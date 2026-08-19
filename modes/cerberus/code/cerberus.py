from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin

"""
Cerberus - Three Heads

- Upper targets light saucer jackpots.
- Any upper target lights regular jackpot status for all three saucers.
- The specific upper target also lights the matching saucer for 3X.
- Additional upper-target hits can make multiple or all saucers 3X.
- Any lit saucer collects a jackpot at its current multiplier.
- After a collect, the gate opens and all remaining lit saucers return to 1X.
- More Jackpots lets each saucer remain lit once after its first collect, at
  the same multiplier it had for that collect.
- Upper spinner builds jackpot value and resets the timer once it is running.
- After the first saucer jackpot, a 16s timer starts.
- Upper-target, spinner, and all saucer hits reset the running timer.
- The third jackpot displays CERBERUS DEFEATED for 2 seconds but does not end
  the mode; defeat is presentation only.
- Mode continues until the ball ends or the timer expires.
"""


class Cerberus(CaseFileMixin, Mode):
    MODE_KEY = "cerberus"

    BASE_JACKPOT_VALUE = 100_000
    SPINNER_ADD_VALUE = 10_000
    MAX_JACKPOT_VALUE = 500_000
    TARGET_SCORE = 25_000
    UNLIT_SAUCER_SCORE = 10_000
    BASE_TIMER_SECONDS = 16
    MORE_TIME_TIMER_SECONDS = 20

    TARGET_TO_SAUCER = {
        1: 1,
        2: 2,
        3: 3,
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.delay = DelayManager(self.machine)
        self.mode_done = False

        self.case_files = self.get_case_file_bonuses()
        self.base_jackpot_value = self.BASE_JACKPOT_VALUE
        self.spinner_add_value = self.SPINNER_ADD_VALUE
        self.max_jackpot_value = self.MAX_JACKPOT_VALUE
        self.base_timer_seconds = self.BASE_TIMER_SECONDS
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("cerberus")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EACH SAUCER STAYS LIT ONCE"),
            ("bigger_jackpots", "BIGGER CERBERUS JACKPOTS"),
            ("more_time", "CERBERUS TIMER EXTENDED"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "BEST JACKPOT FROM ANY SAUCER"),
        ])

        self.saucer_jackpot_lit = {1: False, 2: False, 3: False}
        self.saucer_triple_lit = {1: False, 2: False, 3: False}
        self.more_jackpots_active = self.has_case_file("more_jackpots")
        self.more_jackpots_repeat_available = {
            saucer: self.more_jackpots_active for saucer in [1, 2, 3]
        }
        self.shot_assist_available = self.has_case_file("shot_assist")

        self.jackpot_value = self.base_jackpot_value
        self.jackpots_collected = 0
        self.targets_hit = 0
        self.spinner_spins = 0
        self.best_jackpot = 0
        self.mode_points = 0
        self.timer_running = False
        self.timer_seconds = self.base_timer_seconds
        self.gate_open_after_collect = False

        self._sync_vars()

        for target in [1, 2, 3]:
            self.add_mode_event_handler(
                f"cerberus_upper_target_{target}_hit",
                self._upper_target_hit,
                target=target,
            )

        for saucer in [1, 2, 3]:
            self.add_mode_event_handler(
                f"cerberus_saucer_{saucer}_hit",
                self._saucer_hit,
                saucer=saucer,
            )

        self.add_mode_event_handler("cerberus_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("cerberus_fail_request", self._fail_mode)

        self._update_gate_state()
        self.machine.events.post("cerberus_startup_complete")
        self.machine.events.post("show_mode_message_long", message_mode_title="THREE HEADS", message_mode_subtitle="HIT UPPER TARGETS")
        self._refresh_lights()

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.delay.remove("cerberus_mode_timer")
        self.clear_active_case_file_helpers()
        self.machine.events.post("cerberus_clear_all_lights")
        self.machine.events.post("rooftop_diverter_close")
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        if self.has_case_file("bigger_jackpots"):
            self.base_jackpot_value = 150_000
            self.spinner_add_value = 15_000
            self.max_jackpot_value = 750_000

        if self.has_case_file("more_time"):
            self.base_timer_seconds = self.MORE_TIME_TIMER_SECONDS

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

    def _upper_target_hit(self, target=None, **kwargs):
        if self._in_summary_or_done():
            return

        self.targets_hit += 1
        self._score(self.TARGET_SCORE)

        # Any target lights/re-lights the regular jackpot state for all saucers.
        for saucer in [1, 2, 3]:
            self.saucer_jackpot_lit[saucer] = True

        # The matching target upgrades that saucer to 3X. Other previously
        # upgraded saucers remain at 3X, so all three can be built before a collect.
        matching_saucer = self.TARGET_TO_SAUCER.get(target)
        if matching_saucer:
            self.saucer_triple_lit[matching_saucer] = True

        self.gate_open_after_collect = False
        self._reset_timer_if_running()
        self._sync_vars()
        self._refresh_lights()
        self._update_gate_state()
        self.machine.events.post("cerberus_target_hit", target=target)
        self.machine.events.post("show_mode_message", message_mode_title="HEAD STUNNED", message_mode_subtitle=f"SAUCER {target} 3X")

    def _spinner_hit(self, **kwargs):
        if self._in_summary_or_done():
            return

        self.spinner_spins += 1
        self.jackpot_value = min(
            self.max_jackpot_value,
            self.jackpot_value + self.spinner_add_value,
        )
        self._reset_timer_if_running()
        self._sync_vars()
        self.machine.events.post(
            "cerberus_jackpot_value_changed",
            value=self.jackpot_value,
            spins=self.spinner_spins,
        )
        self.machine.events.post("show_mode_message", message_mode_title="JACKPOT BUILDS", message_mode_subtitle="UPPER SPINNER", message_mode_value=self.jackpot_value)

    def _saucer_hit(self, saucer=None, **kwargs):
        if self._in_summary_or_done():
            return

        self._reset_timer_if_running()

        if self.shot_assist_available:
            self.shot_assist_available = False
            collect_saucer, multiplier = self._best_available_saucer_or_default(saucer)
            self.machine.events.post(
                "cerberus_case_file_shot_assist_used",
                entered_saucer=saucer,
                collected_saucer=collect_saucer,
                multiplier=multiplier,
            )
        elif not self.saucer_jackpot_lit.get(saucer, False):
            self._score(self.UNLIT_SAUCER_SCORE)
            self._sync_vars()
            self._update_gate_state()
            self.machine.events.post("cerberus_unlit_saucer_hit", saucer=saucer)
            self.machine.events.post("show_mode_message", message_mode_title="SAUCER UNLIT", message_mode_subtitle="HIT UPPER TARGETS")
            return
        else:
            collect_saucer = saucer
            multiplier = 3 if self.saucer_triple_lit.get(saucer, False) else 1

        award = self.jackpot_value * multiplier

        self._score(award)
        self.jackpots_collected += 1
        self.best_jackpot = max(self.best_jackpot, award)

        # More Jackpots gives each saucer one retained first collection. The
        # retained shot stays exactly as it was, including 3X when applicable.
        # Shot Assist reaches this same path, so it consumes only one collection
        # state from the saucer it actually awards.
        keep_collected_saucer_lit = self.more_jackpots_repeat_available.get(
            collect_saucer,
            False,
        )
        if keep_collected_saucer_lit:
            self.more_jackpots_repeat_available[collect_saucer] = False

        self.saucer_jackpot_lit[collect_saucer] = keep_collected_saucer_lit
        for candidate in [1, 2, 3]:
            if candidate != collect_saucer or not keep_collected_saucer_lit:
                self.saucer_triple_lit[candidate] = False

        self.gate_open_after_collect = True

        if not self.timer_running:
            self._restart_timer()

        self._sync_vars()
        self._refresh_lights()
        self._update_gate_state()
        self.machine.events.post(
            "cerberus_jackpot_collected",
            saucer=collect_saucer,
            entered_saucer=saucer,
            value=award,
            multiplier=multiplier,
            jackpots=self.jackpots_collected,
        )
        self.machine.events.post("show_mode_jackpot", message_mode_title="CERBERUS JACKPOT", message_mode_subtitle=f"SAUCER {collect_saucer} - {multiplier}X", message_mode_value=award)

        if self.jackpots_collected == 3:
            # Presentation only: show_mode_message expires after 2 seconds in
            # the shared base mode and play continues normally.
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="CERBERUS DEFEATED",
                message_mode_subtitle="KEEP PLAYING",
            )

    def _best_available_saucer_or_default(self, default_saucer):
        # Prefer the best lit jackpot on the playfield, even if the entered saucer is unlit.
        for saucer in [1, 2, 3]:
            if self.saucer_jackpot_lit.get(saucer, False) and self.saucer_triple_lit.get(saucer, False):
                return saucer, 3

        for saucer in [1, 2, 3]:
            if self.saucer_jackpot_lit.get(saucer, False):
                return saucer, 1

        # Nothing is lit. The assist still awards the entered saucer as a 1X jackpot.
        return default_saucer, 1

    def _restart_timer(self):
        if self.mode_done:
            return

        self.timer_running = True
        self.timer_seconds = self.base_timer_seconds
        self._sync_vars()
        self.machine.events.post("cerberus_timer_started", seconds=self.timer_seconds)
        self.machine.events.post("show_mode_countdown", message_mode_title="CERBERUS TIMER", message_mode_subtitle="KEEP ATTACKING", message_mode_seconds=self.timer_seconds)

        self.delay.remove("cerberus_mode_timer")
        self.delay.add(
            name="cerberus_mode_timer",
            ms=self.timer_seconds * 1000,
            callback=self._timer_expired,
        )

    def _reset_timer_if_running(self):
        if self.timer_running and not self.mode_done:
            self._restart_timer()

    def _timer_expired(self, **kwargs):
        if self.mode_done:
            return
        self.machine.events.post("cerberus_timer_expired")
        self.machine.events.post("show_mode_message", message_mode_title="CERBERUS ESCAPED", message_mode_subtitle="TIME EXPIRED")
        self._fail_mode()

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("cerberus_mode_timer")
        self._sync_vars()
        self.machine.events.post("cerberus_mode_complete")

    def _score(self, points):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return
        player["score"] += points
        self.mode_points += points

    def _update_gate_state(self):
        """Keep the rooftop gate aligned with the Cerberus scoring loop.

        Upper-target activity lights the saucers and closes the gate. A saucer
        jackpot collect opens the gate even when other saucers remain lit, so
        the player can return upstairs to rebuild 3X values. The next upper
        target hit closes the gate again.
        """
        if self._in_summary_or_done():
            return

        if self.gate_open_after_collect:
            self.machine.events.post("rooftop_diverter_open")
            self.machine.events.post("cerberus_gate_open_after_collect")
        elif any(self.saucer_jackpot_lit.get(saucer, False) for saucer in [1, 2, 3]):
            self.machine.events.post("rooftop_diverter_close")
            self.machine.events.post("cerberus_gate_closed_for_saucers")
        else:
            self.machine.events.post("rooftop_diverter_open")
            self.machine.events.post("cerberus_gate_open_for_upper")

    def _refresh_lights(self):
        # Upper targets remain valid upgrade shots while the ball is on the roof.
        self.machine.events.post("cerberus_lite_upper_targets")

        for saucer in [1, 2, 3]:
            if self.saucer_jackpot_lit[saucer]:
                self.machine.events.post(f"cerberus_saucer_{saucer}_jackpot_lit")
            else:
                self.machine.events.post(f"cerberus_saucer_{saucer}_jackpot_off")

            if self.saucer_triple_lit[saucer]:
                self.machine.events.post(f"cerberus_saucer_{saucer}_triple_lit")
            else:
                self.machine.events.post(f"cerberus_saucer_{saucer}_triple_off")

    def _sync_vars(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return

        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.targets_hit
        player["cerberus_spinner_spins"] = self.spinner_spins
        player["active_mode_stat_2"] = self.jackpots_collected
        player["cerberus_best_jackpot"] = self.best_jackpot
        player["cerberus_jackpot_value"] = self.jackpot_value
        player["cerberus_timer_seconds"] = self.timer_seconds if self.timer_running else 0
        player["cerberus_more_jackpots_available"] = int(getattr(self, "more_jackpots_active", False))
        player["cerberus_shot_assist_available"] = int(getattr(self, "shot_assist_available", False))

        self._update_mode_status()

        for saucer in [1, 2, 3]:
            player[f"cerberus_saucer_{saucer}_jackpot_lit"] = int(self.saucer_jackpot_lit[saucer])
            player[f"cerberus_saucer_{saucer}_triple_lit"] = int(self.saucer_triple_lit[saucer])

    def _update_mode_status(self):
        lit = sum(1 for saucer in [1, 2, 3] if self.saucer_jackpot_lit[saucer])
        triples = sum(1 for saucer in [1, 2, 3] if self.saucer_triple_lit[saucer])
        if lit:
            title = "SAUCERS LIT / 3X"
            value = f"{lit} LIT / {triples} AT 3X"
        else:
            title = "HIT UPPER TARGETS"
            value = f"JACKPOTS {self.jackpots_collected}"
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)

    def _in_summary_or_done(self):
        if self.mode_done:
            return True
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return False
        try:
            return player["villain_mode_in_summary"] == True
        except KeyError:
            return False
