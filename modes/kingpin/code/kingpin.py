from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Kingpin(Mode, CaseFileMixin):
    """KINGPIN: THE FIX IS IN

    60 second right-bank completion mode.
    Complete all five right-bank target lights before time expires.

    Round 1 allows one right-bank hit before Kingpin sweeps the bank.
    Round 2 allows two hits, Round 3 allows three hits, and so on.
    After the allowed hits are used, remaining drops are auto-dropped and
    the bank resets after a short delay.

    Completing the left 3-bank adds 10 seconds and resets the left bank.
    The mode does not control the Daily Bugle A/B gate.
    """

    MODE_KEY = "kingpin"
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
        self.more_jackpots_extra_round = False
        self.extra_round_active = False
        self.shot_assist_used = False

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self._reset_player_vars()
        self._add_handlers()

        self.machine.events.post("kingpin_started")
        self.machine.events.post("kingpin_clear_lights")
        self.machine.events.post("kingpin_reset_banks")
        self.machine.events.post("kingpin_round_started", round=self.round_number, allowed=self._hits_allowed())
        self._sync_vars()
        self._show_message(
            "KINGPIN",
            f"ROUND {self.round_number}: {self._hits_allowed()} HIT",
            value=f"{self._completed_count()}/5 TARGETS",
            seconds=self.remaining_seconds,
            event="show_mode_countdown",
        )
        self._start_timer()

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.delay.remove("kingpin_timer_tick")
        self.delay.remove("kingpin_reset_right_bank")
        self.clear_active_case_file_helpers()
        self.machine.events.post("kingpin_clear_lights")
        self.machine.events.post("kingpin_reset_banks")
        super().mode_stop(**kwargs)

    def _show_message(self, title, subtitle="", value="", seconds="", event="show_mode_message"):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
        )

    def _format_score(self, value):
        return f"{int(value):,}"

    def _apply_case_file_bonuses(self):
        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA KINGPIN ROUND"),
            ("bigger_jackpots", "250K NEW TARGETS"),
            ("more_time", "70 SECOND TIMER"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "ROUND 2 SPOTS EXTRA TARGET"),
        ])

        if self.has_case_file("more_time"):
            self.remaining_seconds = self.MORE_TIME_SECONDS

        if self.has_case_file("bigger_jackpots"):
            self.new_target_value = self.BIGGER_NEW_TARGET_VALUE
            self.duplicate_target_value = self.BIGGER_DUPLICATE_TARGET_VALUE

        if self.has_case_file("more_jackpots"):
            self.more_jackpots_extra_round = True

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

    def _reset_player_vars(self):
        player = self.machine.game.player
        player["kingpin_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player["kingpin_timer"] = self.remaining_seconds
        player["kingpin_round"] = self.round_number
        player["kingpin_round_hits"] = 0
        player["kingpin_round_hits_allowed"] = self._hits_allowed()
        player["kingpin_completed_count"] = 0
        player["kingpin_extra_round_active"] = 0
        for target in self.TARGETS:
            player[f"kingpin_target_{target}_complete"] = 0

    def _add_handlers(self):
        for target in self.TARGETS:
            self.add_mode_event_handler(
                f"kingpin_right_drop_{target}_hit",
                self._right_drop_hit,
                target=target,
            )

        self.add_mode_event_handler("kingpin_left_bank_complete", self._left_bank_complete)
        self.add_mode_event_handler("kingpin_timer_expired", self._timer_expired)

    def _start_timer(self):
        self.delay.remove("kingpin_timer_tick")
        self.delay.add(name="kingpin_timer_tick", ms=1000, callback=self._timer_tick)

    def _timer_tick(self):
        if self.mode_done:
            return

        self.remaining_seconds -= 1
        self._sync_vars()
        self.machine.events.post("kingpin_timer_tick", seconds=self.remaining_seconds)
        self.machine.events.post("update_mode_status", mode_status_title="SECONDS LEFT", mode_status_value=max(0, self.remaining_seconds))

        if self.remaining_seconds <= 0:
            self.machine.events.post("kingpin_timer_expired")
            return

        self._start_timer()

    def _timer_expired(self, **kwargs):
        if self.mode_done:
            return

        self.machine.events.post("kingpin_goal_missed")
        self._show_message("TIME UP", "KINGPIN ESCAPES", event="show_mode_jackpot")
        self._complete_mode()

    def _left_bank_complete(self, **kwargs):
        if self.mode_done:
            return

        self.remaining_seconds += self.LEFT_BANK_TIME_ADD
        self._sync_vars()
        self.machine.events.post("kingpin_time_added", seconds=self.LEFT_BANK_TIME_ADD)
        self._show_message(
            "TIME ADDED",
            "LEFT BANK COMPLETE",
            value=f"+{self.LEFT_BANK_TIME_ADD}s",
        )
        self.machine.events.post("update_mode_status", mode_status_title="SECONDS LEFT", mode_status_value=max(0, self.remaining_seconds))
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")

    def _right_drop_hit(self, target, **kwargs):
        if self.mode_done or self.bank_sweeping:
            return

        if self.extra_round_active:
            self._collect_extra_jackpot(target)
            return

        self.round_hits += 1
        self._add_hit_vars(major=True)

        if self.completed[target]:
            self._score(self.duplicate_target_value)
            self.machine.events.post("kingpin_duplicate_target_hit", target=target, value=self.duplicate_target_value)
            self._show_message(
                "TARGET AGAIN",
                f"DROP {target}",
                value=self._format_score(self.duplicate_target_value),
                event="show_mode_message",
            )
        else:
            self._complete_target(target, self.new_target_value)

        if self._should_use_shot_assist():
            self._use_shot_assist(excluding=target)

        if self._all_targets_completed():
            self._all_targets_lit()
            return

        if self.round_hits >= self._hits_allowed():
            self._sweep_and_reset_bank()
        else:
            self._sync_vars()

    def _complete_target(self, target, value):
        self.completed[target] = True
        self._score(value)
        self.machine.events.post(f"kingpin_target_{target}_complete")
        self.machine.events.post("kingpin_new_target_complete", target=target, value=value)
        self._sync_vars()
        self._show_message(
            "TARGET LOCKED",
            f"DROP {target}",
            value=self._format_score(value),
            event="show_mode_jackpot",
        )

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
                self.machine.events.post("kingpin_shot_assist_spotted", target=target)
                self._show_message("SHOT ASSIST", f"DROP {target} SPOTTED", event="show_mode_jackpot")
                return

    def _all_targets_lit(self):
        self.machine.events.post("kingpin_all_targets_lit")
        self._show_message("ALL TARGETS", "KINGPIN CORNERED", event="show_mode_jackpot")

        if self.more_jackpots_extra_round and not self.extra_round_active:
            self.extra_round_active = True
            self.round_hits = 0
            self.bank_sweeping = True
            self.machine.events.post("kingpin_extra_round_started")
            self._show_message(
                "EXTRA ROUND",
                "MORE JACKPOTS",
                value=self._format_score(self.EXTRA_JACKPOT_VALUE),
                event="show_mode_jackpot",
            )
            self._drop_unhit_targets_this_cycle(excluding=None)
            self.delay.remove("kingpin_reset_right_bank")
            self.delay.add(name="kingpin_reset_right_bank", ms=self.BANK_RESET_DELAY_MS, callback=self._reset_for_extra_round)
            self._sync_vars()
            return

        self._complete_mode()

    def _reset_for_extra_round(self):
        if self.mode_done:
            return
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.bank_sweeping = False
        self._sync_vars()

    def _collect_extra_jackpot(self, target):
        self._score(self.EXTRA_JACKPOT_VALUE)
        self._add_hit_vars(major=True)
        self.machine.events.post("kingpin_extra_jackpot_collected", target=target, value=self.EXTRA_JACKPOT_VALUE)
        self._show_message(
            "EXTRA JACKPOT",
            f"DROP {target}",
            value=self._format_score(self.EXTRA_JACKPOT_VALUE),
            event="show_mode_jackpot",
        )
        self._drop_unhit_targets_this_cycle(excluding=target)
        self._complete_mode()

    def _sweep_and_reset_bank(self):
        self.bank_sweeping = True
        self.machine.events.post("kingpin_bank_sweep_started", round=self.round_number)
        self._show_message("KINGPIN SWEEPS", "BANK RESETTING", event="show_mode_message")
        self._drop_unhit_targets_this_cycle(excluding=None)
        self.delay.remove("kingpin_reset_right_bank")
        self.delay.add(name="kingpin_reset_right_bank", ms=self.BANK_RESET_DELAY_MS, callback=self._next_round)
        self._sync_vars()

    def _next_round(self):
        if self.mode_done:
            return

        self.round_number += 1
        self.round_hits = 0
        self.bank_sweeping = False
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("kingpin_round_started", round=self.round_number, allowed=self._hits_allowed())
        self._sync_vars()
        self._show_message(
            "KINGPIN",
            f"ROUND {self.round_number}: {self._hits_allowed()} HITS",
            value=f"{self._completed_count()}/5 TARGETS",
            seconds=self.remaining_seconds,
            event="show_mode_countdown",
        )

    def _drop_unhit_targets_this_cycle(self, excluding=None):
        for target in self.TARGETS:
            if target == excluding:
                continue
            self._pulse_drop(target)

    def _pulse_drop(self, target):
        try:
            self.machine.coils[f"c_right_bank_drop_{target}"].pulse()
        except KeyError:
            self.warning_log("Missing right-bank drop coil for Kingpin target %s", target)

    def _hits_allowed(self):
        return min(self.round_number, len(self.TARGETS))

    def _all_targets_completed(self):
        return all(self.completed.values())

    def _completed_count(self):
        return sum(1 for target in self.TARGETS if self.completed[target])

    def _add_hit_vars(self, major=False):
        player = self.machine.game.player
        player["active_mode_hits"] += 1
        if major:
            player["active_mode_major_hits"] += 1

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points

    def _complete_mode(self):
        if self.mode_done:
            return

        self.mode_done = True
        self.delay.remove("kingpin_timer_tick")
        self.delay.remove("kingpin_reset_right_bank")
        player = self.machine.game.player
        player["kingpin_state"] = 2
        self._sync_vars()
        self._show_message("KINGPIN DEFEATED", "MODE COMPLETE", event="show_mode_jackpot")
        self.machine.events.post("kingpin_mode_complete")

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["kingpin_timer"] = max(0, self.remaining_seconds)
        player["kingpin_round"] = self.round_number
        player["kingpin_round_hits"] = self.round_hits
        player["kingpin_round_hits_allowed"] = self._hits_allowed()
        player["kingpin_completed_count"] = self._completed_count()
        player["kingpin_extra_round_active"] = 1 if self.extra_round_active else 0
        for target in self.TARGETS:
            player[f"kingpin_target_{target}_complete"] = 1 if self.completed[target] else 0
