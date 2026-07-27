from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Desperado(Mode, CaseFileMixin):
    """Timed right-bank pursuit repurposed from the former Kingpin rules.

    Complete all five unique right-bank targets before time expires.
    Round 1 allows one bank hit before Desperado escapes and resets the bank;
    each later round allows one additional hit. Completing the left bank adds
    time. Temporary round and target state remains in Python.
    """

    MODE_KEY = "desperado"
    TARGETS = (1, 2, 3, 4, 5)

    BASE_SECONDS = 60
    MORE_TIME_SECONDS = 70
    LEFT_BANK_TIME_ADD = 10
    BANK_RESET_DELAY_MS = 2000

    NEW_TARGET_VALUE = 200_000
    DUPLICATE_TARGET_VALUE = 50_000
    BIGGER_NEW_TARGET_VALUE = 250_000
    BIGGER_DUPLICATE_TARGET_VALUE = 75_000
    EXTRA_JACKPOT_VALUE = 500_000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.bank_sweeping = False
        self.completed = {target: False for target in self.TARGETS}
        self.round_number = 1
        self.round_hits = 0
        self.remaining_seconds = self.BASE_SECONDS
        self.mode_points = 0
        self.new_target_value = self.NEW_TARGET_VALUE
        self.duplicate_target_value = self.DUPLICATE_TARGET_VALUE
        self.extra_round_qualified = False
        self.extra_round_active = False
        self.shot_assist_used = False

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self._reset_shared_vars()
        self._add_handlers()

        self.machine.events.post("desperado_started")
        self.machine.events.post("desperado_clear_lights")
        self.machine.events.post("desperado_reset_banks")
        self._start_round()
        self._start_timer()

    def mode_stop(self, **kwargs):
        self.delay.remove("desperado_timer_tick")
        self.delay.remove("desperado_reset_right_bank")
        self.clear_active_case_file_helpers()
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("desperado_clear_lights")
        self.machine.events.post("desperado_reset_banks")
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA SHOWDOWN JACKPOT"),
            ("bigger_jackpots", "250K NEW TARGETS"),
            ("more_time", "70 SECOND PURSUIT"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "ROUND 2 SPOTS EXTRA TARGET"),
        ])
        if self.has_case_file("more_time"):
            self.remaining_seconds = self.MORE_TIME_SECONDS
        if self.has_case_file("bigger_jackpots"):
            self.new_target_value = self.BIGGER_NEW_TARGET_VALUE
            self.duplicate_target_value = self.BIGGER_DUPLICATE_TARGET_VALUE
        if self.has_case_file("more_jackpots"):
            self.extra_round_qualified = True
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

    def _reset_shared_vars(self):
        player = self.machine.game.player
        player["desperado_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0

    def _add_handlers(self):
        for target in self.TARGETS:
            self.add_mode_event_handler(
                f"desperado_right_drop_{target}_hit", self._right_drop_hit, target=target
            )
        self.add_mode_event_handler("desperado_left_bank_complete", self._left_bank_complete)
        self.add_mode_event_handler("desperado_timer_expired", self._timer_expired)

    def _start_timer(self):
        # Desperado owns one countdown. Resetting the same named delay keeps
        # round changes and time awards from creating parallel timer chains.
        self.delay.reset(name="desperado_timer_tick", ms=1000, callback=self._timer_tick)

    def _timer_tick(self):
        if self.mode_done:
            return
        self.remaining_seconds -= 1
        self._show_timer_status()
        if self.remaining_seconds <= 0:
            self.machine.events.post("desperado_timer_expired")
            return
        self._start_timer()

    def _timer_expired(self, **kwargs):
        if self.mode_done:
            return
        self._show_message("TIME UP", "DESPERADO ESCAPES", event="show_mode_jackpot")
        self.machine.events.post("desperado_goal_missed")
        self._finish_mode(defeated=False)

    def _left_bank_complete(self, **kwargs):
        if self.mode_done:
            return
        self.remaining_seconds += self.LEFT_BANK_TIME_ADD
        self.machine.events.post("desperado_time_added", seconds=self.LEFT_BANK_TIME_ADD)
        self._show_message("PURSUIT EXTENDED", "LEFT BANK COMPLETE", value=f"+{self.LEFT_BANK_TIME_ADD}s")
        self._show_timer_status()
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")

    def _right_drop_hit(self, target, **kwargs):
        if self.mode_done or self.bank_sweeping:
            return
        if self.extra_round_active:
            self._collect_extra_jackpot(target)
            return

        self.round_hits += 1
        self._add_hit_vars()
        if self.completed[target]:
            self._score(self.duplicate_target_value)
            self.machine.events.post("desperado_duplicate_target_hit", target=target)
            self._show_message("TRAIL REVISITED", f"DROP {target}", value=self._format_score(self.duplicate_target_value))
        else:
            self._complete_target(target, self.new_target_value)

        if self._should_use_shot_assist():
            self._use_shot_assist(excluding=target)

        if self._all_targets_completed():
            self._all_targets_lit()
        elif self.round_hits >= self._hits_allowed():
            self._sweep_and_reset_bank()
        else:
            self._show_status()

    def _complete_target(self, target, value):
        self.completed[target] = True
        self._score(value)
        self.machine.game.player["active_mode_major_hits"] += 1
        self.machine.events.post(f"desperado_target_{target}_complete")
        self.machine.events.post("desperado_new_target_complete", target=target, value=value)
        self._show_message("OUTLAW SPOTTED", f"DROP {target}", value=self._format_score(value), event="show_mode_jackpot")

    def _should_use_shot_assist(self):
        return (
            self.has_case_file("shot_assist")
            and not self.shot_assist_used
            and self.round_number == 2
            and any(not self.completed[target] for target in self.TARGETS)
        )

    def _use_shot_assist(self, excluding):
        for target in self.TARGETS:
            if target != excluding and not self.completed[target]:
                self.shot_assist_used = True
                self._complete_target(target, self.new_target_value)
                self._pulse_drop(target)
                self._show_message("SHOT ASSIST", f"DROP {target} SPOTTED", event="show_mode_jackpot")
                return

    def _all_targets_lit(self):
        self.machine.events.post("desperado_all_targets_lit")
        if self.extra_round_qualified:
            self.extra_round_qualified = False
            self.extra_round_active = True
            self.bank_sweeping = True
            self.machine.events.post("desperado_extra_round_started")
            self._show_message("FINAL SHOWDOWN", "HIT ANY RIGHT DROP", value=self._format_score(self.EXTRA_JACKPOT_VALUE), event="show_mode_jackpot")
            self._drop_targets(excluding=None)
            self.delay.add(name="desperado_reset_right_bank", ms=self.BANK_RESET_DELAY_MS, callback=self._reset_for_extra_round)
            return
        self._finish_mode(defeated=True)

    def _reset_for_extra_round(self):
        if self.mode_done:
            return
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.bank_sweeping = False

    def _collect_extra_jackpot(self, target):
        self._score(self.EXTRA_JACKPOT_VALUE)
        self._add_hit_vars()
        self.machine.events.post("desperado_extra_jackpot_collected", target=target, value=self.EXTRA_JACKPOT_VALUE)
        self._show_message("SHOWDOWN JACKPOT", f"DROP {target}", value=self._format_score(self.EXTRA_JACKPOT_VALUE), event="show_mode_jackpot")
        self._finish_mode(defeated=True)

    def _sweep_and_reset_bank(self):
        self.bank_sweeping = True
        self.machine.events.post("desperado_escape_started", round=self.round_number)
        self._show_message("DESPERADO ESCAPES", "BANK RESETTING")
        self._drop_targets(excluding=None)
        self.delay.remove("desperado_reset_right_bank")
        self.delay.add(name="desperado_reset_right_bank", ms=self.BANK_RESET_DELAY_MS, callback=self._next_round)

    def _next_round(self):
        if self.mode_done:
            return
        self.round_number += 1
        self.round_hits = 0
        self.bank_sweeping = False
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self._start_round()

    def _start_round(self):
        allowed = self._hits_allowed()
        self.machine.events.post("desperado_round_started", round=self.round_number, allowed=allowed)
        # Do not use show_mode_countdown here. That shared display event owns
        # its own one-second countdown, which used to run alongside this mode's
        # Python timer and become stale when the left bank added time.
        self._show_message(
            "DESPERADO", f"ROUND {self.round_number}: {allowed} SHOT{'S' if allowed != 1 else ''}",
            value=f"{self._completed_count()}/5 OUTLAWS", reminder=True,
        )
        self._show_status()

    def _show_status(self):
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=f"ROUND {self.round_number}",
            mode_status_value=f"{self._completed_count()}/5  {self.round_hits}/{self._hits_allowed()}",
        )

    def _show_timer_status(self):
        self.machine.events.post(
            "update_mode_status",
            mode_status_title="SECONDS LEFT",
            mode_status_value=max(0, self.remaining_seconds),
        )

    def _drop_targets(self, excluding=None):
        for target in self.TARGETS:
            if target != excluding:
                self._pulse_drop(target)

    def _pulse_drop(self, target):
        try:
            self.machine.coils[f"c_right_bank_drop_{target}"].pulse()
        except KeyError:
            self.warning_log("Missing right-bank drop coil for Desperado target %s", target)

    def _hits_allowed(self):
        return min(self.round_number, len(self.TARGETS))

    def _all_targets_completed(self):
        return all(self.completed.values())

    def _completed_count(self):
        return sum(1 for completed in self.completed.values() if completed)

    def _add_hit_vars(self):
        self.machine.game.player["active_mode_hits"] += 1

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points

    def _finish_mode(self, defeated):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("desperado_timer_tick")
        self.delay.remove("desperado_reset_right_bank")
        self.machine.game.player["desperado_state"] = 2 if defeated else 1
        if defeated:
            self._show_message("DESPERADO CAPTURED", "MODE COMPLETE", event="show_mode_jackpot")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("desperado_mode_complete")

    def _show_message(self, title, subtitle="", value="", seconds="", event="show_mode_message", reminder=False):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )

    @staticmethod
    def _format_score(value):
        return f"{int(value):,}"
