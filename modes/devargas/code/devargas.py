import random
import time
from functools import partial

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode

from modes.common.case_file_mixin import CaseFileMixin


class DeVargas(CaseFileMixin, Mode):
    """Cloud City of Gold pure score attack.

    Twenty timed gold opportunities are drawn from thirteen repeatable shot
    groups. Opportunities overlap naturally because each lasts ten seconds
    while a new one appears every eight seconds. A successful hit immediately
    replaces only the collected opportunity and restarts the eight-second
    selection clock.
    """

    MODE_KEY = "devargas"
    DISPLAY_NAME = "DeVargas"

    BASE_OPPORTUNITIES = 20
    MORE_JACKPOTS_OPPORTUNITIES = 25
    NEXT_OPPORTUNITY_MS = 8_000

    BASE_PHASE_MS = (4_000, 3_000, 3_000)
    MORE_TIME_PHASE_MS = (5_000, 4_000, 4_000)

    BASE_VALUES = {
        "slow": 150_000,
        "medium": 125_000,
        "fast": 100_000,
    }
    BIGGER_VALUES = {
        "slow": 200_000,
        "medium": 175_000,
        "fast": 150_000,
    }

    SHOTS = (
        "left_web",
        "center_web",
        "left_pop",
        "right_pop",
        "left_bank",
        "right_bank",
        "upper_a",
        "upper_b",
        "middle_a",
        "middle_b",
        "upper_targets",
        "spinner",
        "upper_spinner",
    )
    UPPER_SHOTS = {"upper_targets", "upper_spinner"}

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.machine.game.player["active_mode_stat_2"] = self.machine.game.player["devargas_bonus"]

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.active_opportunities = {}
        self.next_opportunity_id = 1
        self.last_selected_shot = None
        self.opportunities_started = 0
        self.gold_shots = 0
        self.expired_shots = 0
        self.mode_points = 0
        self.gold_banked_this_mode = 0
        self.shot_assist_available = self.has_case_file("shot_assist")
        self.gate_open = False

        self.total_opportunities = (
            self.MORE_JACKPOTS_OPPORTUNITIES
            if self.has_case_file("more_jackpots")
            else self.BASE_OPPORTUNITIES
        )
        self.phase_ms = (
            self.MORE_TIME_PHASE_MS
            if self.has_case_file("more_time")
            else self.BASE_PHASE_MS
        )
        self.values = (
            self.BIGGER_VALUES
            if self.has_case_file("bigger_jackpots")
            else self.BASE_VALUES
        )

        self._register_handlers()
        self._reset_player_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "25 GOLD OPPORTUNITIES"),
            ("bigger_jackpots", "GOLD WORTH 200K / 175K / 150K"),
            ("more_time", "GOLD WINDOWS LAST 5s / 4s / 4s"),
            ("safety_net", "10 SECOND OPENING SAVE"),
            ("shot_assist", "FIRST EXPIRED GOLD AUTO-COLLECTS"),
        ])

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        if self.has_case_file("safety_net"):
            self.machine.events.post("devargas_enable_safety_net")

        self._show_message(
            "CITY OF GOLD",
            "HIT THE PULSING SHOTS",
            reminder=True,
        )
        self._spawn_opportunity()

    def mode_stop(self, **kwargs):
        self.delay.remove("devargas_next_opportunity")
        for opportunity_id in list(self.active_opportunities):
            self._remove_opportunity(opportunity_id)
        self.machine.events.post("devargas_all_shots_off")
        self.machine.events.post("devargas_disable_safety_net")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _register_handlers(self):
        for shot in self.SHOTS:
            self.add_mode_event_handler(
                f"devargas_{shot}_hit",
                self._shot_hit,
                shot=shot,
            )

        self.add_mode_event_handler("ball_ending", self._complete_mode)
        self.add_mode_event_handler(
            "devargas_complete_request", self._complete_mode
        )
        self.add_mode_event_handler(
            "rooftop_diverter_open", self._reject_unneeded_gate_open
        )
        self.add_mode_event_handler(
            "open_rooftop_gate", self._reject_unneeded_gate_open
        )

    def _reset_player_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["active_mode_stat_1"] = 0
        player["devargas_state"] = 1
        self._sync_vars()

    def _spawn_opportunity(self, avoid_shot=None):
        if self.mode_done:
            return

        if self.opportunities_started >= self.total_opportunities:
            self.delay.remove("devargas_next_opportunity")
            self._finish_if_resolved()
            return

        active_shots = {
            opportunity["shot"]
            for opportunity in self.active_opportunities.values()
        }
        excluded = set(active_shots)
        if self.last_selected_shot:
            excluded.add(self.last_selected_shot)
        if avoid_shot:
            excluded.add(avoid_shot)

        choices = [shot for shot in self.SHOTS if shot not in excluded]
        if not choices:
            choices = [shot for shot in self.SHOTS if shot not in active_shots]

        shot = random.choice(choices)
        opportunity_id = self.next_opportunity_id
        self.next_opportunity_id += 1
        self.opportunities_started += 1
        self.last_selected_shot = shot

        self.active_opportunities[opportunity_id] = {
            "shot": shot,
            "phase": "slow",
            "started_at": time.monotonic(),
        }

        slow_ms, medium_ms, fast_ms = self.phase_ms
        self.machine.events.post(
            f"devargas_{shot}_slow",
            opportunity=opportunity_id,
        )
        self.machine.events.post(
            "devargas_opportunity_started",
            opportunity=opportunity_id,
            shot=shot,
            opportunities_started=self.opportunities_started,
            opportunities_total=self.total_opportunities,
        )

        self.delay.add(
            name=self._delay_name(opportunity_id, "medium"),
            ms=slow_ms,
            callback=partial(
                self._change_phase,
                opportunity_id=opportunity_id,
                phase="medium",
            ),
        )
        self.delay.add(
            name=self._delay_name(opportunity_id, "fast"),
            ms=slow_ms + medium_ms,
            callback=partial(
                self._change_phase,
                opportunity_id=opportunity_id,
                phase="fast",
            ),
        )
        self.delay.add(
            name=self._delay_name(opportunity_id, "expire"),
            ms=slow_ms + medium_ms + fast_ms,
            callback=partial(
                self._expire_opportunity,
                opportunity_id=opportunity_id,
            ),
        )

        if self.opportunities_started < self.total_opportunities:
            self.delay.reset(
                name="devargas_next_opportunity",
                ms=self.NEXT_OPPORTUNITY_MS,
                callback=self._spawn_opportunity,
            )
        else:
            self.delay.remove("devargas_next_opportunity")

        self._sync_gate()
        self._sync_vars()

    def _change_phase(self, opportunity_id=None, phase=None):
        opportunity = self.active_opportunities.get(opportunity_id)
        if self.mode_done or not opportunity or phase not in self.values:
            return

        opportunity["phase"] = phase
        self.machine.events.post(
            f"devargas_{opportunity['shot']}_{phase}",
            opportunity=opportunity_id,
        )

    def _shot_hit(self, shot=None, **kwargs):
        if self.mode_done or shot not in self.SHOTS:
            return

        opportunity_id = next(
            (
                candidate_id
                for candidate_id, opportunity in self.active_opportunities.items()
                if opportunity["shot"] == shot
            ),
            None,
        )
        if opportunity_id is None:
            return

        self._collect_opportunity(opportunity_id, assisted=False)

    def _collect_opportunity(self, opportunity_id, assisted=False):
        opportunity = self.active_opportunities.get(opportunity_id)
        if self.mode_done or not opportunity:
            return

        shot = opportunity["shot"]
        phase = "fast" if assisted else self._current_phase(opportunity)
        value = self.values[phase]

        self._remove_opportunity(opportunity_id)
        self.gold_shots += 1
        self._score_and_bank(value)

        self.machine.events.post(
            "devargas_gold_collected",
            shot=shot,
            phase=phase,
            value=value,
            assisted=assisted,
            gold_shots=self.gold_shots,
        )

        if assisted:
            self._show_jackpot(
                "GOLD RECOVERED",
                "SHOT ASSIST",
                value,
            )
        else:
            self._show_jackpot(
                "GOLD COLLECTED",
                phase.upper(),
                value,
            )

        self._sync_gate()
        self._sync_vars()

        if self.opportunities_started < self.total_opportunities:
            self._spawn_opportunity(avoid_shot=shot)
        else:
            self._finish_if_resolved()

    def _expire_opportunity(self, opportunity_id=None):
        opportunity = self.active_opportunities.get(opportunity_id)
        if self.mode_done or not opportunity:
            return

        if self.shot_assist_available:
            self.shot_assist_available = False
            self.machine.events.post(
                "devargas_case_file_shot_assist_used",
                shot=opportunity["shot"],
            )
            self._collect_opportunity(opportunity_id, assisted=True)
            return

        shot = opportunity["shot"]
        self._remove_opportunity(opportunity_id)
        self.expired_shots += 1
        self.machine.events.post(
            "devargas_gold_expired",
            shot=shot,
            expired_shots=self.expired_shots,
        )
        self._show_message("GOLD LOST", self._shot_label(shot))
        self._sync_gate()
        self._sync_vars()
        self._finish_if_resolved()

    def _remove_opportunity(self, opportunity_id):
        opportunity = self.active_opportunities.pop(opportunity_id, None)
        if not opportunity:
            return

        for suffix in ("medium", "fast", "expire"):
            self.delay.remove(self._delay_name(opportunity_id, suffix))
        self.machine.events.post(
            f"devargas_{opportunity['shot']}_off",
            opportunity=opportunity_id,
        )

    def _finish_if_resolved(self):
        if (
            not self.mode_done
            and self.opportunities_started >= self.total_opportunities
            and not self.active_opportunities
        ):
            self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.delay.remove("devargas_next_opportunity")
        for opportunity_id in list(self.active_opportunities):
            self._remove_opportunity(opportunity_id)

        self.machine.game.player["devargas_state"] = 2
        self._sync_vars(update_status=False)
        self.machine.events.post("devargas_all_shots_off")
        self.machine.events.post("devargas_disable_safety_net")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("devargas_mode_complete")

    def _current_phase(self, opportunity):
        elapsed_ms = int(
            max(0.0, time.monotonic() - opportunity["started_at"]) * 1000
        )
        slow_ms, medium_ms, _fast_ms = self.phase_ms
        if elapsed_ms < slow_ms:
            return "slow"
        if elapsed_ms < slow_ms + medium_ms:
            return "medium"
        return "fast"

    def _score_and_bank(self, value):
        player = self.machine.game.player
        player["score"] += value
        player["devargas_bonus"] += value
        player["active_mode_stat_2"] = player["devargas_bonus"]
        self.mode_points += value
        self.gold_banked_this_mode += value

    def _sync_gate(self):
        should_open = any(
            opportunity["shot"] in self.UPPER_SHOTS
            for opportunity in self.active_opportunities.values()
        )
        if should_open == self.gate_open:
            return

        self.gate_open = should_open
        self.machine.events.post(
            "rooftop_diverter_open" if should_open else "rooftop_diverter_close"
        )

    def _reject_unneeded_gate_open(self, **kwargs):
        if self.mode_done:
            return
        if not any(
            opportunity["shot"] in self.UPPER_SHOTS
            for opportunity in self.active_opportunities.values()
        ):
            self.gate_open = False
            self.machine.events.post("rooftop_diverter_close")

    def _sync_vars(self, update_status=True):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.gold_shots
        if update_status and not self.mode_done:
            self._update_status()

    def _update_status(self):
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=f"GOLD {self.gold_banked_this_mode:,}",
            mode_status_value=(
                f"OPPORTUNITIES {self.opportunities_started}/{self.total_opportunities}"
                f"  SHOTS {self.gold_shots}"
            ),
        )

    def _show_message(
        self,
        title,
        subtitle="",
        value="",
        seconds="",
        reminder=False,
    ):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )

    def _show_jackpot(self, title, subtitle, value):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    @staticmethod
    def _delay_name(opportunity_id, suffix):
        return f"devargas_opportunity_{opportunity_id}_{suffix}"

    @staticmethod
    def _shot_label(shot):
        labels = {
            "left_web": "LEFT WEB",
            "center_web": "CENTER WEB",
            "left_pop": "LEFT POP",
            "right_pop": "RIGHT POP",
            "left_bank": "LEFT BANK",
            "right_bank": "RIGHT BANK",
            "upper_a": "A ROLLOVER",
            "upper_b": "B ROLLOVER",
            "middle_a": "MIDDLE A",
            "middle_b": "MIDDLE B",
            "upper_targets": "UPPER TARGETS",
            "spinner": "SPINNER",
            "upper_spinner": "UPPER SPINNER",
        }
        return labels.get(shot, shot.replace("_", " ").upper())
