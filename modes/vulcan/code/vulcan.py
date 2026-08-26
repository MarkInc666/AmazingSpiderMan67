from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin

"""
Vulcan - Volcano Unleashed

Rules:
- Starts 2-ball multiball with a 10-second ball save; mode ends when the
  multiball drops to one ball.
- The rooftop gate remains open for the mode.
- Right-bank drops are Vulcan Jackpots. Base is 100K, or 150K with Bigger
  Jackpots, and the value is capped at 1M.
- Every upper-target hit adds 25K to the current Jackpot value. The hit that
  collects Add-a-Ball also adds 25K.
- Completing a Jackpot bank qualifies one Add-a-Ball. Qualifications do not
  stack. If already at the 3-ball cap, Add-a-Ball stays qualified until an
  upper target is hit while below 3 balls.
- Entering the upper playfield resets any down targets in the active Jackpot
  banks. Banks do not auto-reset when completed.
- More Jackpots makes the left 3-bank a second Jackpot bank under the same
  rules as the right bank.
- Without More Jackpots, each left drop scores the normal 2K drop value and
  the left bank resets immediately when completed.
- Bigger Jackpots raises the starting Jackpot from 100K to 150K.
- More Time extends the upper-left-exit post hold from 8s to 12s.
- Safety Net extends the opening multiball ball save from 10s to 20s. The
  built-in Add-a-Ball save remains 10s.
- Shot Assist: the first right-bank drop hit also drops and awards two more
  standing right-bank targets.
- Every collected Jackpot adds its full scored value to vulcan_bonus.
- Spinners have no Vulcan-specific rule; normal base spinner scoring remains.
"""


class Vulcan(CaseFileMixin, Mode):
    MODE_KEY = "vulcan"
    DISPLAY_NAME = "Vulcan"

    BASE_JACKPOT = 100_000
    BIGGER_BASE_JACKPOT = 150_000
    UPPER_TARGET_BUILD = 25_000
    MAX_JACKPOT = 1_000_000
    POST_HOLD_MS = 8_000
    MORE_TIME_POST_HOLD_MS = 12_000
    MAX_BALLS = 3

    RIGHT_DROPS = (1, 2, 3, 4, 5)
    LEFT_DROPS = (1, 2, 3)
    UPPER_TARGETS = ("left", "center", "right")

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.machine.game.player["active_mode_stat_2"] = self.machine.game.player["vulcan_bonus"]

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.mode_points = 0
        self.jackpot_value = (
            self.BIGGER_BASE_JACKPOT
            if self.has_case_file("bigger_jackpots")
            else self.BASE_JACKPOT
        )
        self.post_hold_ms = (
            self.MORE_TIME_POST_HOLD_MS
            if self.has_case_file("more_time")
            else self.POST_HOLD_MS
        )

        self.right_drops_down = set()
        self.left_drops_down = set()
        self.jackpots_collected = 0
        self.add_a_ball_qualified = False
        self.add_a_balls_awarded = 0
        self.shot_assist_used = False
        self.post_hold_active = False

        self._sync_vars()
        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "LEFT 3-BANK ADDS JACKPOTS"),
            ("bigger_jackpots", "JACKPOTS START AT 150K"),
            ("more_time", "UPPER-LEFT POST HOLDS 12s"),
            ("safety_net", "20 SECOND MULTIBALL BALL SAVE"),
            ("shot_assist", "FIRST RIGHT DROP ADDS TWO DROPS"),
        ])

        self.add_mode_event_handler(
            "vulcan_upper_playfield_entered", self._upper_playfield_entered
        )
        self.add_mode_event_handler("vulcan_upper_left_exit", self._upper_left_exit)
        self.add_mode_event_handler("vulcan_post_hold_cancel", self._post_hold_cancel)
        self.add_mode_event_handler("vulcan_multiball_ended", self._complete_mode)
        self.add_mode_event_handler("vulcan_complete_request", self._complete_mode)
        self.add_mode_event_handler("vulcan_fail_request", self._complete_mode)
        self.add_mode_event_handler(
            "drop_target_bank_dt_bank_left_down", self._left_bank_completed
        )

        for number in self.RIGHT_DROPS:
            self.add_mode_event_handler(
                f"vulcan_right_drop_{number}_hit",
                self._right_drop_hit,
                number=number,
            )

        for number in self.LEFT_DROPS:
            self.add_mode_event_handler(
                f"vulcan_left_drop_{number}_hit",
                self._left_drop_hit,
                number=number,
            )

        for target in self.UPPER_TARGETS:
            self.add_mode_event_handler(
                f"vulcan_upper_target_{target}_hit",
                self._upper_target_hit,
                target=target,
            )

        self.machine.events.post("vulcan_setup")
        if self.has_case_file("more_jackpots"):
            self.machine.events.post("vulcan_left_bank_reloaded")
        else:
            self.machine.events.post("vulcan_left_bank_disabled")
        self.machine.events.post("vulcan_start_multiball")
        self.machine.events.post("vulcan_mode_intro")
        self._show_mode_message("VOLCANO UNLEASHED", "DROPS SCORE - UPPER TARGETS BUILD")

    def mode_stop(self, **kwargs):
        self.delay.remove("vulcan_post_hold_release")
        if self.post_hold_active:
            self.machine.events.post("timer_timer_up_post_hold_complete")
            self.post_hold_active = False
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("vulcan_clear_all_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        # Catch-all: no delayed villain/wizard callback may survive into bonus.
        self.delay.clear()
        super().mode_stop(**kwargs)

    def _right_drop_hit(self, number=None, **kwargs):
        if self._done() or number is None or number in self.right_drops_down:
            return

        self._collect_drop("right", number)

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            for _ in range(2):
                extra = self._first_available_right_drop()
                if extra is None:
                    break
                # Mark and score before the physical knockdown switch arrives,
                # so its eventual switch event cannot double-award the Jackpot.
                self.machine.events.post(f"vulcan_shot_assist_drop_{extra}")
                self._collect_drop("right", extra)

        self._check_bank_completion("right")
        self._sync_vars()

    def _left_drop_hit(self, number=None, **kwargs):
        if self._done() or number is None:
            return

        if not self.has_case_file("more_jackpots"):
            self.machine.events.post("drop_hit_no_mode")
            return

        if number in self.left_drops_down:
            return

        self._collect_drop("left", number)
        self._check_bank_completion("left")
        self._sync_vars()

    def _left_bank_completed(self, **kwargs):
        if self._done() or self.has_case_file("more_jackpots"):
            return

        self.machine.events.post("drop_target_bank_dt_bank_left_reset")

    def _collect_drop(self, bank, number):
        drops_down = self.right_drops_down if bank == "right" else self.left_drops_down
        drops_down.add(number)

        value = self.jackpot_value
        self.jackpots_collected += 1
        self._score(value)
        self._bank_vulcan_bonus(value)
        self.machine.events.post(
            "vulcan_drop_jackpot_collected", bank=bank, number=number, value=value
        )
        self.machine.events.post(f"vulcan_{bank}_drop_{number}_collected")
        self._show_mode_jackpot("VULCAN JACKPOT", value, f"{bank.upper()} DROP {number}")

    def _check_bank_completion(self, bank):
        if bank == "right":
            complete = len(self.right_drops_down) >= len(self.RIGHT_DROPS)
        else:
            complete = len(self.left_drops_down) >= len(self.LEFT_DROPS)

        if not complete:
            return

        self.machine.events.post(f"vulcan_{bank}_bank_down")
        if not self.add_a_ball_qualified:
            self.add_a_ball_qualified = True
            self.machine.events.post("vulcan_add_a_ball_qualified")
            self._show_mode_message("ADD-A-BALL READY", "HIT ANY UPPER TARGET")

    def _upper_playfield_entered(self, **kwargs):
        if self._done():
            return

        if self.right_drops_down:
            self.right_drops_down.clear()
            self.machine.events.post("drop_target_bank_dt_bank_right_reset")
            self.machine.events.post("vulcan_right_bank_reloaded")

        if self.has_case_file("more_jackpots") and self.left_drops_down:
            self.left_drops_down.clear()
            self.machine.events.post("drop_target_bank_dt_bank_left_reset")
            self.machine.events.post("vulcan_left_bank_reloaded")

        self._sync_vars()

    def _upper_target_hit(self, target=None, **kwargs):
        if self._done() or target not in self.UPPER_TARGETS:
            return

        old_value = self.jackpot_value
        self.jackpot_value = min(
            self.MAX_JACKPOT, self.jackpot_value + self.UPPER_TARGET_BUILD
        )
        self.machine.events.post(
            "vulcan_jackpot_built",
            target=target,
            value=self.jackpot_value,
            increase=self.jackpot_value - old_value,
        )

        if self.add_a_ball_qualified and self._balls_in_play() < self.MAX_BALLS:
            self.add_a_ball_qualified = False
            self.add_a_balls_awarded += 1
            self.machine.events.post("vulcan_add_a_ball")
            self.machine.events.post("vulcan_add_a_ball_awarded")
            self.machine.events.post("vulcan_add_a_ball_unqualified")
            self._show_mode_message("ADD-A-BALL", "VULCAN ERUPTS AGAIN")

        self._sync_vars()

    def _upper_left_exit(self, **kwargs):
        if self._done():
            return

        self.delay.remove("vulcan_post_hold_release")
        self.post_hold_active = True
        self.machine.events.post("enable_up_post_event")
        self.machine.events.post(
            "vulcan_post_hold_started", seconds=int(self.post_hold_ms / 1000)
        )
        self.delay.add(
            name="vulcan_post_hold_release",
            ms=self.post_hold_ms,
            callback=self._release_post_hold,
        )
        self._sync_vars()

    def _post_hold_cancel(self, **kwargs):
        if not self.post_hold_active:
            return
        self._release_post_hold(cancel_delay=True)

    def _release_post_hold(self, cancel_delay=False):
        if cancel_delay:
            self.delay.remove("vulcan_post_hold_release")
        if not self.post_hold_active:
            return

        self.post_hold_active = False
        self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("vulcan_post_hold_released")
        self._sync_vars()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.delay.remove("vulcan_post_hold_release")
        if self.post_hold_active:
            self.machine.events.post("timer_timer_up_post_hold_complete")
            self.post_hold_active = False
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")

    def _first_available_right_drop(self):
        for number in self.RIGHT_DROPS:
            if number not in self.right_drops_down:
                return number
        return None

    def _bank_vulcan_bonus(self, value):
        self.machine.game.player["vulcan_bonus"] += value

    def _score(self, points):
        self.machine.game.player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.jackpots_collected
        player["active_mode_stat_2"] = player["vulcan_bonus"]

    def _show_mode_message(self, title, subtitle="", value="", seconds="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )

    def _show_mode_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return self.machine.game.balls_in_play

    def _done(self):
        return self.mode_done
