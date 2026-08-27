from dataclasses import dataclass
from functools import partial
import random

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


@dataclass(frozen=True)
class GoblinShot:
    name: str
    event: str


class Goblin(CaseFileMixin, Mode):
    """Green Goblin two-ball risk/reward multiball."""

    CHAOS_START = 500_000
    CHAOS_MIN = 100_000
    UNSAFE_SCORE = 20_000
    UNSAFE_LOSS = 100_000
    EXTRA_SAUCER_SCORE = 50_000
    EXTRA_SAUCER_EJECT_DELAY_MS = 750
    HELD_RELEASE_CHECK_MS = 650
    HELD_RELEASE_MAX_ATTEMPTS = 2
    MULTIBALL_START_CHECK_MS = 1_200

    SAFE_TIME_SECONDS = 10
    MORE_TIME_SECONDS = 15
    SAFE_IMMEDIATE_SCORE = 100_000
    MORE_JACKPOTS_SCORE = 150_000
    SAFE_CHAOS_ADD = 100_000
    BIGGER_SAFE_CHAOS_ADD = 150_000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.case_files = self.get_case_file_bonuses()
        self.more_jackpots = self.has_case_file("more_jackpots")
        self.bigger_jackpots = self.has_case_file("bigger_jackpots")
        self.more_time = self.has_case_file("more_time")
        self.safety_net_available = self.has_case_file("safety_net")
        self.shot_assist_available = self.has_case_file("shot_assist")
        self.safety_net_used = False
        self.shot_assist_used = False

        self.publish_case_file_bonus_events("goblin")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SAFE SHOTS SCORE 150K"),
            ("bigger_jackpots", "SAFE SHOTS ADD 150K TO CHAOS"),
            ("more_time", "15 SECOND SAFE PHASE"),
            ("safety_net", "BALL SAVE AFTER FIRST RELEASE"),
            ("shot_assist", "FIRST SAFE HIT AWARDS ANOTHER"),
        ])

        self.shots = [
            GoblinShot("left_web", "goblin_left_web_hit"),
            GoblinShot("right_web", "goblin_right_web_hit"),
            GoblinShot("left_pop", "goblin_left_pop_hit"),
            GoblinShot("right_pop", "goblin_right_pop_hit"),
            GoblinShot("left_drops", "gob_left_drops_hit"),
            GoblinShot("right_drops", "gob_right_drops_hit"),
        ]

        self.active_shots = set()
        self.current_flashing = set()
        self.current_solid = set()
        self.hold_active = False
        self.held_saucer = None
        self.release_pending = False
        self.ejecting_saucers = set()
        self.mode_finishing = False
        self.attack_total = 0
        self.chaos_scored = 0
        self.safe_hit_count = 0
        self.safe_seconds_remaining = 0
        self.held_release_attempts = 0
        self.multiball_start_pending = False

        for shot in self.shots:
            self.add_mode_event_handler(shot.event, self.shot_hit, shot_name=shot.name)

        self.add_mode_event_handler("goblin_saucer_1_hit", partial(self.saucer_hit, saucer=1))
        self.add_mode_event_handler("goblin_saucer_2_hit", partial(self.saucer_hit, saucer=2))
        self.add_mode_event_handler("goblin_saucer_3_hit", partial(self.saucer_hit, saucer=3))
        self.add_mode_event_handler("s_saucer_1_inactive", partial(self.saucer_cleared, saucer=1))
        self.add_mode_event_handler("s_saucer_2_inactive", partial(self.saucer_cleared, saucer=2))
        self.add_mode_event_handler("s_saucer_3_inactive", partial(self.saucer_cleared, saucer=3))
        self.add_mode_event_handler("multiball_goblin_chaos_multiball_started", self.multiball_started)
        self.add_mode_event_handler("multiball_goblin_chaos_multiball_ended", self.multiball_ended)

        # Goblin owns the rooftop gate for the entire mode. Reject both the
        # modern diverter-open event and the legacy open request if another
        # subsystem tries to reopen it during Chaos/Safe play.
        self.add_mode_event_handler("rooftop_diverter_open", self._force_gate_closed)
        self.add_mode_event_handler("open_rooftop_gate", self._force_gate_closed)

        self.machine.events.post("rooftop_diverter_close")
        self.begin_mode()

    def begin_mode(self):
        player = self.machine.game.player
        player["goblin_chaos_bonus"] = self.CHAOS_START
        self.chaos_scored = 0
        player["active_mode_stat_2"] = self.chaos_scored
        player["goblin_chaos_lock"] = 0
        player["goblin_hold_count"] = 0
        player["goblin_hold_active"] = 0
        self.attack_total = 0
        player["active_mode_stat_1"] = self.attack_total
        player["active_mode_points"] = 0
        player["goblin_state"] = 1
        player["goblin_jackpot_value"] = (
            self.MORE_JACKPOTS_SCORE if self.more_jackpots else self.SAFE_IMMEDIATE_SCORE
        )

        self.machine.events.post("reset_drops")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("goblin_lite_saucers")
        self.multiball_start_pending = True
        self.delay.reset(
            name="goblin_start_multiball_when_clear",
            ms=self.MULTIBALL_START_CHECK_MS,
            callback=self._try_start_multiball,
        )
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="CHAOS MULTIBALL",
            message_mode_subtitle="HIT SAUCER TO BANK BONUS",
        )
        self.start_unsafe_phase()

    def _try_start_multiball(self, **kwargs):
        """Serve Ball 2 only after the intro-held saucer has cleared."""
        if self.mode_finishing or not self.multiball_start_pending:
            return

        occupied = [
            saucer
            for saucer in (1, 2, 3)
            if self.machine.switch_controller.is_active(
                self.machine.switches[f"s_saucer_{saucer}"]
            )
        ]
        if occupied:
            self.machine.events.post("clear_saucers")
            self.delay.reset(
                name="goblin_start_multiball_when_clear",
                ms=1_000,
                callback=self._try_start_multiball,
            )
            return

        self.multiball_start_pending = False
        self.machine.events.post("goblin_start_multiball")

    # ------------------------------------------------------------------
    # Phase control
    # ------------------------------------------------------------------

    def start_unsafe_phase(self, **kwargs):
        if self.mode_finishing:
            return
        self.hold_active = False
        self.release_pending = False
        self.machine.game.player["goblin_hold_active"] = 0
        self.safe_seconds_remaining = 0
        self.safe_hit_count = 0
        self.clear_shot_shows()
        self.active_shots = {shot.name for shot in self.shots}
        self.current_solid = set(self.active_shots)
        self.current_flashing.clear()
        for shot_name in self.current_solid:
            self.machine.events.post(f"goblin_solid_{shot_name}")
        self.machine.events.post("goblin_gi_unsafe")
        self.machine.events.post("goblin_lite_saucers")
        self._update_mode_status()

    def start_safe_phase(self, saucer):
        self.hold_active = True
        self.release_pending = False
        self.held_saucer = saucer
        player = self.machine.game.player
        player["goblin_hold_active"] = 1
        player["goblin_hold_count"] += 1
        self.safe_hit_count = 0
        self.safe_seconds_remaining = self.MORE_TIME_SECONDS if self.more_time else self.SAFE_TIME_SECONDS
        self.clear_shot_shows()
        self.active_shots = {shot.name for shot in self.shots}
        self.current_flashing = set(self.active_shots)
        self.current_solid.clear()
        for shot_name in self.current_flashing:
            self.machine.events.post(f"goblin_lite_{shot_name}")
        self.machine.events.post("goblin_gi_safe")
        self.machine.events.post("goblin_lite_saucers")
        self.machine.events.post("goblin_hold_started", saucer=saucer)
        self._update_mode_status()
        self.delay.remove("goblin_safe_tick")
        self.delay.add(name="goblin_safe_tick", ms=1000, callback=self.safe_tick)
        self.delay.reset(
            name="goblin_safe_prompt",
            ms=2_000,
            callback=self._show_temp,
            title="SAFE JACKPOTS",
            subtitle="HIT ALL 6",
        )

    def safe_tick(self, **kwargs):
        if self.mode_finishing or not self.hold_active:
            return
        self.safe_seconds_remaining = max(0, self.safe_seconds_remaining - 1)
        self._update_mode_status()
        if self.safe_seconds_remaining <= 0:
            self.end_safe_phase(reason="timeout")
            return
        self.delay.add(name="goblin_safe_tick", ms=1000, callback=self.safe_tick)

    def end_safe_phase(self, reason="complete", **kwargs):
        if self.mode_finishing or not self.hold_active or self.release_pending:
            return
        self.delay.remove("goblin_safe_tick")
        saucer = self.held_saucer
        self.release_pending = True
        self._update_mode_status()
        self.delay.remove("goblin_temp_followup")
        self.delay.remove("goblin_safe_prompt")
        self._show_temp("MORE CHAOS!")
        if saucer is not None:
            self.held_release_attempts = 0
            self._request_held_saucer_release()
        else:
            self._complete_saucer_release(saucer=None, reason=reason)

    # ------------------------------------------------------------------
    # Shots and scoring
    # ------------------------------------------------------------------

    def shot_hit(self, shot_name=None, **kwargs):
        if self.mode_finishing or not shot_name or shot_name not in self.active_shots:
            return
        if self.machine.game.player["villain_mode_in_summary"] is True:
            return
        if self.hold_active:
            self.collect_safe_shot(shot_name)
        else:
            self.collect_unsafe_shot(shot_name)

    def collect_unsafe_shot(self, shot_name):
        self._award_points(self.UNSAFE_SCORE)
        player = self.machine.game.player
        self.attack_total += self.UNSAFE_SCORE
        player["active_mode_stat_1"] = self.attack_total
        player["goblin_chaos_bonus"] = max(
            self.CHAOS_MIN,
            int(player["goblin_chaos_bonus"]) - self.UNSAFE_LOSS,
        )
        self.machine.events.post("goblin_solid_shot_score", shot=shot_name)
        self._show_temp("CHAOS HIT - 20K", "CHAOS VALUE -100K")
        self._update_mode_status()

    def collect_safe_shot(self, shot_name, assisted=False):
        if shot_name not in self.active_shots:
            return
        immediate = self.MORE_JACKPOTS_SCORE if self.more_jackpots else self.SAFE_IMMEDIATE_SCORE
        add_value = self.BIGGER_SAFE_CHAOS_ADD if self.bigger_jackpots else self.SAFE_CHAOS_ADD

        self._award_points(immediate)
        player = self.machine.game.player
        self.attack_total += immediate
        player["active_mode_stat_1"] = self.attack_total
        player["goblin_chaos_bonus"] = int(player["goblin_chaos_bonus"]) + add_value
        self.safe_hit_count += 1
        self.deactivate_safe_shot(shot_name)
        self.machine.events.post("goblin_flashing_shot_score", shot=shot_name, assisted=assisted)
        self._queue_safe_messages(immediate, player["goblin_chaos_bonus"])

        trigger_assist = (
            not assisted
            and self.shot_assist_available
            and not self.shot_assist_used
        )
        if trigger_assist:
            self.shot_assist_used = True
            candidates = list(self.active_shots)
            if candidates:
                self.collect_safe_shot(random.choice(candidates), assisted=True)

        self._update_mode_status()
        # Six unique logical Safe shots complete the phase. Use the explicit
        # collected-shot count as the authoritative release trigger instead
        # of relying only on active_shots becoming empty; a stale shot-group
        # entry must never leave the held saucer waiting for the Safe timer.
        if self.safe_hit_count >= len(self.shots):
            self.active_shots.clear()
            self.current_flashing.clear()
            self.end_safe_phase(reason="all_six")

    def deactivate_safe_shot(self, shot_name):
        self.active_shots.discard(shot_name)
        self.current_flashing.discard(shot_name)
        self.machine.events.post(f"goblin_stop_{shot_name}")

    # ------------------------------------------------------------------
    # Saucers
    # ------------------------------------------------------------------

    def saucer_hit(self, saucer=None, **kwargs):
        if self.mode_finishing or saucer is None:
            return
        if self.multiball_start_pending:
            self.machine.events.post("goblin_starting_saucer_retrigger_ignored", saucer=saucer)
            return
        # Do not rescore or change state if a saucer switch chatters while its
        # kickout is in progress. The inactive edge clears this guard.
        if saucer in self.ejecting_saucers:
            return
        if self.hold_active:
            if saucer == self.held_saucer:
                self.machine.events.post("goblin_held_saucer_retrigger_ignored", saucer=saucer)
                return
            self._award_points(self.EXTRA_SAUCER_SCORE)
            self.attack_total += self.EXTRA_SAUCER_SCORE
            self.machine.game.player["active_mode_stat_1"] = self.attack_total
            self._show_temp("NO NO NO")
            self.ejecting_saucers.add(saucer)
            self.delay.add(
                name=f"goblin_extra_saucer_eject_{saucer}",
                ms=self.EXTRA_SAUCER_EJECT_DELAY_MS,
                callback=self.eject_saucer,
                saucer=saucer,
            )
            return

        player = self.machine.game.player
        bank_value = int(player["goblin_chaos_bonus"])
        self._award_points(bank_value)
        self.chaos_scored += bank_value
        player["active_mode_stat_2"] = self.chaos_scored
        player["goblin_chaos_lock"] = self.chaos_scored
        self.machine.events.post(
            "goblin_chaos_bonus_scored",
            value=bank_value,
            total=self.chaos_scored,
        )
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="CHAOS BONUS SCORED",
            message_mode_subtitle="SAFE PHASE STARTED",
            message_mode_value=bank_value,
        )
        self.start_safe_phase(saucer)

    def saucer_cleared(self, saucer=None, **kwargs):
        """Use the physical switch opening as confirmation of a kickout."""
        if saucer is None:
            return
        self.ejecting_saucers.discard(saucer)
        if self.multiball_start_pending:
            self.delay.reset(
                name="goblin_start_multiball_when_clear",
                ms=100,
                callback=self._try_start_multiball,
            )
        if self.release_pending and saucer == self.held_saucer:
            self.delay.remove("goblin_held_saucer_release_check")
            self._complete_saucer_release(saucer=saucer, reason="switch_inactive")
        elif self.hold_active and saucer == self.held_saucer:
            self.delay.remove("goblin_safe_tick")
            self.delay.remove("goblin_safe_prompt")
            self.held_saucer = None
            self.hold_active = False
            self.machine.game.player["goblin_hold_active"] = 0
            self.machine.events.post(
                "goblin_hold_ended",
                saucer=saucer,
                reason="unexpected_switch_inactive",
            )
            self.start_unsafe_phase()

    def eject_saucer(self, saucer=None, **kwargs):
        """Request an occupancy-checked saucer eject."""
        if saucer is not None:
            self.ejecting_saucers.add(saucer)
            self.machine.events.post(
                "request_saucer_eject",
                saucer_number=saucer,
                delay_ms=0,
            )

    def _request_held_saucer_release(self):
        if not self.release_pending or self.held_saucer is None:
            return
        self.held_release_attempts += 1
        self.eject_saucer(saucer=self.held_saucer)
        self.delay.reset(
            name="goblin_held_saucer_release_check",
            ms=self.HELD_RELEASE_CHECK_MS,
            callback=self._check_held_saucer_release,
        )

    def _check_held_saucer_release(self, **kwargs):
        if not self.release_pending or self.held_saucer is None:
            return
        saucer = self.held_saucer
        active = self.machine.switch_controller.is_active(
            self.machine.switches[f"s_saucer_{saucer}"]
        )
        if not active:
            self._complete_saucer_release(saucer=saucer, reason="release_check_inactive")
            return
        if self.held_release_attempts < self.HELD_RELEASE_MAX_ATTEMPTS:
            self.machine.events.post(
                "goblin_held_saucer_release_retry",
                saucer=saucer,
                attempt=self.held_release_attempts + 1,
            )
            self._request_held_saucer_release()
            return
        self.machine.events.post(
            "goblin_held_saucer_release_failed",
            saucer=saucer,
            attempts=self.held_release_attempts,
        )

    def _complete_saucer_release(self, saucer=None, reason=None):
        """Leave the safe phase only after the held ball has physically left."""
        self.delay.remove("goblin_held_saucer_release_check")
        self.held_saucer = None
        self.hold_active = False
        self.release_pending = False
        self.machine.game.player["goblin_hold_active"] = 0
        self.machine.events.post("goblin_hold_ended", saucer=saucer, reason=reason)
        if self.safety_net_available and not self.safety_net_used:
            self.safety_net_used = True
            self.machine.events.post("start_case_file_ball_save")
        self.start_unsafe_phase()

    def eject_held_saucer(self, reason=None):
        saucer = self.held_saucer
        if saucer is None:
            return
        self.delay.remove("goblin_safe_tick")
        if saucer not in self.ejecting_saucers:
            self.eject_saucer(saucer=saucer)
        self.held_saucer = None
        self.hold_active = False
        self.release_pending = False
        self.machine.game.player["goblin_hold_active"] = 0
        self.machine.events.post("goblin_hold_ended", saucer=saucer, reason=reason)

    # ------------------------------------------------------------------
    # Messages / status
    # ------------------------------------------------------------------

    def _show_temp(self, title, subtitle="", value=""):
        self.machine.events.post(
            "goblin_show_temp_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
        )

    def _force_gate_closed(self, **kwargs):
        if not self.mode_finishing:
            self.machine.events.post("rooftop_diverter_close")

    def _queue_safe_messages(self, immediate, chaos_bonus):
        self.delay.remove("goblin_temp_followup")
        self._show_temp(f"SAFE JACKPOT - {immediate // 1000}K")
        self.delay.reset(
            name="goblin_temp_followup",
            ms=1_000,
            callback=self._show_temp,
            title="CHAOS VALUE NOW",
            value=chaos_bonus,
        )

    def _update_mode_status(self):
        if self.release_pending:
            title = "RELEASING BALL"
            value = "MORE CHAOS!"
        elif self.hold_active:
            title = "SAFE JACKPOTS"
            value = f"TIME: {self.safe_seconds_remaining}"
        else:
            title = "CHAOS VALUE"
            value = f"{int(self.machine.game.player['goblin_chaos_bonus']):,}"
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    # ------------------------------------------------------------------
    # Multiball / ending
    # ------------------------------------------------------------------

    def multiball_started(self, **kwargs):
        self.machine.game.player["multiball_autoplunge_active"] = 1

    def multiball_ended(self, **kwargs):
        self.machine.game.player["multiball_autoplunge_active"] = 0
        if self.held_saucer is not None:
            self.eject_held_saucer(reason="multiball_ended")
        if not self.mode_finishing:
            self.finish_mode(completed=False)

    def finish_mode(self, completed=False):
        if self.mode_finishing:
            return
        self.mode_finishing = True
        self.multiball_start_pending = False
        if self.held_saucer is not None:
            self.eject_held_saucer(reason="mode_finish")
        self.clear_all_delays()
        self.clear_shot_shows()
        self.machine.events.post("goblin_gi_stop")
        self.machine.events.post("goblin_mode_ended")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.game.player["goblin_state"] = 2
        self.machine.events.post("goblin_mode_complete")

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        self.clear_all_delays()
        self.clear_shot_shows()
        self.machine.events.post("goblin_gi_stop")
        self.machine.events.post("goblin_mode_ended")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.game.player["multiball_autoplunge_active"] = 0
        super().mode_stop(**kwargs)

    def clear_all_delays(self):
        for name in (
            "goblin_safe_tick",
            "goblin_safe_prompt",
            "goblin_temp_followup",
            "goblin_start_multiball_when_clear",
            "goblin_held_saucer_release_check",
            "goblin_extra_saucer_eject_1",
            "goblin_extra_saucer_eject_2",
            "goblin_extra_saucer_eject_3",
        ):
            self.delay.remove(name)

    def clear_shot_shows(self):
        for shot_name in set(self.current_flashing) | set(self.current_solid):
            self.machine.events.post(f"goblin_stop_{shot_name}")
        self.current_flashing.clear()
        self.current_solid.clear()

    def _award_points(self, points):
        self.machine.game.player["score"] += points
        self.machine.game.player["active_mode_points"] += points
