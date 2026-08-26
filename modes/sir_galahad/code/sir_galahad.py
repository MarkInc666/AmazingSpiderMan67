from mpf.core.delays import DelayManager
from mpf.core.mode import Mode

from modes.common.case_file_mixin import CaseFileMixin


class SirGalahad(CaseFileMixin, Mode):
    """Knight Must Fall: three rooftop-triggered drop-bank accuracy rounds."""

    MODE_KEY = "sir_galahad"
    DISPLAY_NAME = "Sir Galahad"

    BASE_ROUNDS = 3
    MORE_JACKPOTS_ROUNDS = 4
    BASE_WINDOW_SECONDS = 8
    MORE_TIME_WINDOW_SECONDS = 12
    EXIT_SCORE = 100_000
    COLLAPSE_STEP_MS = 30
    VUK_EJECT_MS = 750
    COMPLETION_HOLD_MS = 2_000

    LEFT_VALUES = {1: 100_000, 2: 500_000, 3: 100_000}
    LEFT_BIGGER_VALUES = {1: 150_000, 2: 750_000, 3: 150_000}
    RIGHT_VALUES = {
        1: 50_000,
        2: 100_000,
        3: 500_000,
        4: 100_000,
        5: 50_000,
    }
    RIGHT_BIGGER_VALUES = {
        1: 100_000,
        2: 250_000,
        3: 750_000,
        4: 250_000,
        5: 100_000,
    }

    # Rapid center-outward collapse order after a joust target is collected.
    # Already-down targets are skipped; each remaining target falls 30 ms after
    # the previous one rather than dropping in simultaneous groups.
    COLLAPSE_ORDER = {
        "left": (2, 1, 3),
        "right": (3, 2, 4, 1, 5),
    }
    CENTER_TARGET = {"left": 2, "right": 3}

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()
        self.max_rounds = (
            self.MORE_JACKPOTS_ROUNDS
            if self.has_case_file("more_jackpots")
            else self.BASE_ROUNDS
        )
        self.window_seconds = (
            self.MORE_TIME_WINDOW_SECONDS
            if self.has_case_file("more_time")
            else self.BASE_WINDOW_SECONDS
        )

        self.mode_done = False
        self.phase = "roof_ready"
        self.round_number = 0
        self.rounds_resolved = 0
        self.active_bank = None
        self.seconds_left = 0
        self.post_hold_active = False
        self.programmatic_drops = set()
        self.drops_down = set()
        self.shot_assist_available = self.has_case_file("shot_assist")
        self.mode_points = 0
        self.target_hits = 0
        self.bullseyes = 0

        player = self.machine.game.player
        player["sir_galahad_state"] = 1
        self._sync_summary_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "FOURTH JOUST ROUND ADDED"),
            ("bigger_jackpots", "JOUST JACKPOTS BOOSTED"),
            ("more_time", "12 SECOND JOUST WINDOWS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST DROP SCORES CENTER VALUE"),
        ])

        self.add_mode_event_handler("sir_galahad_upper_left_exit", self._upper_left_exit)
        self.add_mode_event_handler("sir_galahad_upper_right_exit", self._upper_right_exit)
        self.add_mode_event_handler("sir_galahad_right_inlane_hit", self._right_inlane_hit)
        self.add_mode_event_handler(
            "timer_timer_up_post_hold_complete", self._post_hold_dropped
        )
        self.add_mode_event_handler("sir_galahad_post_hold_cancel", self._cancel_post_hold)
        self.add_mode_event_handler("sir_galahad_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("sir_galahad_complete_request", self._complete_mode)

        for target in range(1, 4):
            self.add_mode_event_handler(
                f"sir_galahad_left_drop_{target}_hit",
                self._drop_hit,
                bank="left",
                target=target,
            )
        for target in range(1, 6):
            self.add_mode_event_handler(
                f"sir_galahad_right_drop_{target}_hit",
                self._drop_hit,
                bank="right",
                target=target,
            )

        self.machine.events.post("sir_galahad_setup")
        self.machine.events.post("rooftop_diverter_open")
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.machine.events.post("sir_galahad_roof_ready")
        self._show_message("KNIGHT MUST FALL", "ENTER THE ROOFTOP", reminder=True)
        self._update_status()

    def mode_stop(self, **kwargs):
        self.mode_done = True
        self.phase = "stopping"
        self._clear_delays()
        if self.post_hold_active:
            self.post_hold_active = False
            self.machine.events.post("drop_the_up_post")
            self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("sir_galahad_clear_all_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.clear_active_case_file_helpers()
        # Catch-all: no delayed villain/wizard callback may survive into bonus.
        self.delay.clear()
        super().mode_stop(**kwargs)

    def _clear_delays(self):
        for name in (
            "sir_galahad_window_tick",
            "sir_galahad_collapse_next",
            "sir_galahad_complete_hold",
        ):
            self.delay.remove(name)

    def _upper_left_exit(self, **kwargs):
        self._begin_round(bank="right", exit_name="LEFT")

    def _upper_right_exit(self, **kwargs):
        self._begin_round(bank="left", exit_name="RIGHT")

    def _begin_round(self, bank, exit_name):
        if self.mode_done or self.phase != "roof_ready":
            return

        self.round_number += 1
        self.active_bank = bank
        self.seconds_left = 0
        self.programmatic_drops.clear()
        self.drops_down.clear()
        self._score(self.EXIT_SCORE)

        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("sir_galahad_roof_not_ready")
        self.machine.events.post(f"drop_target_bank_dt_bank_{bank}_reset")
        self.machine.events.post(f"sir_galahad_{bank}_bank_ready")
        self.machine.events.post(
            "sir_galahad_exit_scored",
            exit_name=exit_name,
            bank=bank,
            value=self.EXIT_SCORE,
            round=self.round_number,
        )

        bank_label = "RIGHT FIVE-BANK" if bank == "right" else "LEFT THREE-BANK"
        self._show_message(
            f"{exit_name} EXIT",
            f"AIM FOR {bank_label} CENTER",
            value=self.EXIT_SCORE,
        )

        if bank == "right":
            self.phase = "waiting_post"
            self.post_hold_active = True
            self.machine.events.post("enable_up_post_event")
        else:
            self.phase = "waiting_inlane"
        self._update_status()

    def _post_hold_dropped(self, **kwargs):
        if self.mode_done or self.phase != "waiting_post" or self.active_bank != "right":
            return
        self.post_hold_active = False
        self._start_window()

    def _cancel_post_hold(self, **kwargs):
        if self.mode_done or not self.post_hold_active or self.phase != "waiting_post":
            return
        self.post_hold_active = False
        self.machine.events.post("drop_the_up_post")
        self.machine.events.post("timer_timer_up_post_hold_complete")

    def _right_inlane_hit(self, **kwargs):
        if self.mode_done or self.phase != "waiting_inlane" or self.active_bank != "left":
            return
        self._start_window()

    def _start_window(self):
        if self.mode_done or self.phase not in ("waiting_post", "waiting_inlane"):
            return

        self.phase = "window"
        self.seconds_left = self.window_seconds
        self.machine.events.post(
            "sir_galahad_joust_window_started",
            bank=self.active_bank,
            round=self.round_number,
            seconds=self.seconds_left,
        )
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=f"{self.active_bank.upper()} BANK",
            message_mode_subtitle="AIM FOR CENTER",
            message_mode_value="",
            message_mode_seconds=self.seconds_left,
        )
        self._update_status()
        self._schedule_window_tick()

    def _schedule_window_tick(self):
        if self.mode_done or self.phase != "window":
            return
        self.delay.reset(
            name="sir_galahad_window_tick",
            ms=1000,
            callback=self._window_tick,
        )

    def _window_tick(self):
        if self.mode_done or self.phase != "window":
            return
        self.seconds_left -= 1
        self.machine.events.post(
            "sir_galahad_joust_timer_changed",
            bank=self.active_bank,
            seconds=max(0, self.seconds_left),
        )
        self._update_status()
        if self.seconds_left <= 0:
            self._resolve_round(result="timeout")
            return
        self._schedule_window_tick()

    def _drop_hit(self, bank, target, **kwargs):
        key = (bank, target)
        if key in self.programmatic_drops:
            self.programmatic_drops.discard(key)
            return
        if (
            self.mode_done
            or self.phase != "window"
            or bank != self.active_bank
            or target in self.drops_down
        ):
            return

        self.drops_down.add(target)
        values = self._values_for_bank(bank)
        value = values[target]
        assisted = False
        if self.shot_assist_available:
            self.shot_assist_available = False
            value = values[self.CENTER_TARGET[bank]]
            assisted = target != self.CENTER_TARGET[bank]

        self._score(value)
        self.target_hits += 1
        if target == self.CENTER_TARGET[bank] or assisted:
            self.bullseyes += 1
        self._sync_summary_vars()

        subtitle = f"{bank.upper()} TARGET {target}"
        if assisted:
            subtitle = "SHOT ASSIST — CENTER VALUE"
        self.machine.events.post(
            "sir_galahad_target_collected",
            bank=bank,
            target=target,
            value=value,
            assisted=assisted,
            round=self.round_number,
        )
        self._show_jackpot("JOUST JACKPOT", value, subtitle)
        self._resolve_round(result="target")

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            return

        final_vuk_round = (
            self.phase == "window"
            and self.rounds_resolved + 1 >= self.max_rounds
        )
        if final_vuk_round:
            self.machine.events.post("villain_summary_hold_vuk_until_done")
        else:
            self.machine.events.post("request_vuk_eject", delay_ms=self.VUK_EJECT_MS)

        if self.phase != "window":
            return
        self._resolve_round(result="vuk")

    def _resolve_round(self, result):
        if self.mode_done or self.phase != "window":
            return

        self.phase = "collapse"
        self.seconds_left = 0
        self.delay.remove("sir_galahad_window_tick")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("sir_galahad_bank_window_off")

        if result == "timeout":
            self._show_message("GALAHAD CHARGES", "TIME EXPIRED")
        elif result == "vuk":
            self._show_message("GALAHAD CHARGES", "VUK ENDS THE JOUST")

        self.machine.events.post(
            "sir_galahad_round_resolving",
            bank=self.active_bank,
            result=result,
            round=self.round_number,
        )
        self._collapse_stage(0)

    def _collapse_stage(self, stage):
        if self.mode_done or self.phase != "collapse" or self.active_bank is None:
            return

        order = self.COLLAPSE_ORDER[self.active_bank]

        # Skip targets that are already down (including the shot the player just
        # made) so every remaining physical knockdown is separated by 30 ms.
        while stage < len(order) and order[stage] in self.drops_down:
            stage += 1

        if stage >= len(order):
            self._finish_round()
            return

        target = order[stage]
        self.drops_down.add(target)
        self.programmatic_drops.add((self.active_bank, target))
        self.machine.drop_targets[f"dt_{self.active_bank}_{target}"].knockdown()

        self.machine.events.post(
            "sir_galahad_collapse_step",
            bank=self.active_bank,
            targets=str(target),
            stage=stage + 1,
            round=self.round_number,
        )
        self.delay.reset(
            name="sir_galahad_collapse_next",
            ms=self.COLLAPSE_STEP_MS,
            callback=lambda: self._collapse_stage(stage + 1),
        )

    def _finish_round(self):
        if self.mode_done or self.phase != "collapse":
            return

        self.rounds_resolved += 1
        completed_round = self.round_number
        self.active_bank = None
        self.drops_down.clear()
        self.seconds_left = 0
        self.machine.events.post(
            "sir_galahad_round_complete",
            round=completed_round,
            rounds_remaining=max(0, self.max_rounds - self.rounds_resolved),
        )

        if self.rounds_resolved >= self.max_rounds:
            self._complete_mode()
            return

        self.phase = "roof_ready"
        self.machine.events.post("sir_galahad_roof_ready")
        remaining = self.max_rounds - self.rounds_resolved
        self._show_message(
            f"ROUND {completed_round} COMPLETE",
            f"ENTER ROOFTOP — {remaining} JOUSTS LEFT",
            reminder=True,
        )
        self._update_status()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.phase = "complete_hold"
        self._clear_delays()
        self.machine.game.player["sir_galahad_state"] = 2
        self._sync_summary_vars()
        self.machine.events.post("sir_galahad_clear_all_lights")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="KNIGHT MUST FALL",
            message_mode_subtitle="JOUST SCORE",
            message_mode_value=self.mode_points,
        )
        self.delay.reset(
            name="sir_galahad_complete_hold",
            ms=self.COMPLETION_HOLD_MS,
            callback=lambda: self.machine.events.post("sir_galahad_mode_complete"),
        )

    def _values_for_bank(self, bank):
        if bank == "left":
            return (
                self.LEFT_BIGGER_VALUES
                if self.has_case_file("bigger_jackpots")
                else self.LEFT_VALUES
            )
        return (
            self.RIGHT_BIGGER_VALUES
            if self.has_case_file("bigger_jackpots")
            else self.RIGHT_VALUES
        )

    def _score(self, points):
        if self.mode_done or points <= 0:
            return
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_summary_vars()

    def _sync_summary_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.target_hits
        player["active_mode_stat_2"] = self.bullseyes

    def _update_status(self):
        if self.mode_done:
            return
        if self.phase == "roof_ready":
            title = "JOUSTS LEFT"
            value = self.max_rounds - self.rounds_resolved
        elif self.phase == "waiting_post":
            title = f"ROUND {self.round_number} OF {self.max_rounds}"
            value = "RIGHT BANK — WAIT FOR POST"
        elif self.phase == "waiting_inlane":
            title = f"ROUND {self.round_number} OF {self.max_rounds}"
            value = "LEFT BANK — RIGHT INLANE"
        elif self.phase == "window":
            title = f"{self.active_bank.upper()} BANK — AIM CENTER"
            value = self.seconds_left
        else:
            return
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _show_message(self, title, subtitle="", value="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
            reminder=reminder,
        )

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )
