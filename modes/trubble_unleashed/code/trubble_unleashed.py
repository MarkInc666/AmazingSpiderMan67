from mpf.core.delays import DelayManager
from mpf.core.mode import Mode

import random

"""
Trubble Unleashed - Chapter 3 wizard.

Design notes:
- No active case-file powers in wizard modes.
- Chapter case files only affect values via mini_wizard_case_file_bonus.
- Starts as 2-ball multiball and ends when the main multiball ends/down to 1 ball.
- Left bank opens the roof. Upper exits close the roof gate.
- Upper targets light matching saucer jackpots.
- Upper-right exit starts a Diana-style post release, then a 6s staged right-bank shot.
- Successful staged right-bank hits increase saucer jackpot values and qualify Add-a-Ball at VUK.
"""


class TrubbleUnleashed(Mode):
    MODE_KEY = "trubble_unleashed"
    DISPLAY_NAME = "Trubble Unleashed"

    BASIC_DROP_SCORE = 25_000
    UPPER_TARGET_SCORE = 50_000
    UNLIT_SAUCER_SCORE = 25_000
    BASE_SAUCER_JACKPOT = 250_000
    STAGED_HIT_SCORE = 150_000
    STAGED_JACKPOT_STEP = 100_000
    VUK_UNLIT_SCORE = 25_000
    POST_HOLD_MS = 6000
    STAGE_BANK_DELAY_MS = 500
    STAGED_SECONDS = 6
    MAX_BALLS = 3

    ALL_RIGHT_DROPS = (1, 2, 3, 4, 5)
    SAUCER_BY_TARGET = {
        "left": 1,
        "center": 2,
        "right": 3,
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.mode_exiting = False
        self.mode_points = 0
        self.left_drop_hits = 0
        self.right_drop_hits = 0
        self.upper_target_hits = 0
        self.saucer_jackpots = 0
        self.staged_successes = 0
        self.add_a_balls_awarded = 0
        self.add_a_ball_qualified = False
        self.staged_active = False
        self.post_hold_active = False
        self.staged_seconds_left = 0
        self.staged_targets = set()
        self.ignored_auto_drop_targets = set()
        self.lit_saucers = set()
        self.case_file_bonus = self._get("mini_wizard_case_file_bonus", 0)
        self.saucer_jackpot_value = self.BASE_SAUCER_JACKPOT + self.case_file_bonus

        self._set("trubble_unleashed_state", 1)
        self._sync_vars()

        self.add_mode_event_handler("trubble_unleashed_left_drop_hit", self._left_drop_hit)
        self.add_mode_event_handler("trubble_unleashed_left_bank_complete", self._left_bank_complete)
        self.add_mode_event_handler("trubble_unleashed_right_bank_complete", self._right_bank_complete)
        self.add_mode_event_handler("trubble_unleashed_upper_exit_left", self._upper_exit_left)
        self.add_mode_event_handler("trubble_unleashed_upper_exit_right", self._upper_exit_right)
        self.add_mode_event_handler("trubble_unleashed_post_hold_cancel", self._post_hold_cancel)
        self.add_mode_event_handler("trubble_unleashed_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("trubble_unleashed_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler("trubble_unleashed_complete_request", self._complete_mode)

        for target in self.ALL_RIGHT_DROPS:
            self.add_mode_event_handler(
                f"trubble_unleashed_right_drop_{target}_hit",
                self._right_drop_hit,
                target=target,
            )

        for name in self.SAUCER_BY_TARGET:
            self.add_mode_event_handler(
                f"trubble_unleashed_upper_target_{name}_hit",
                self._upper_target_hit,
                target_name=name,
            )

        for saucer in (1, 2, 3):
            self.add_mode_event_handler(
                f"trubble_unleashed_saucer_{saucer}_hit",
                self._saucer_hit,
                saucer=saucer,
            )

        self.machine.events.post("trubble_unleashed_setup")
        self.machine.events.post("trubble_unleashed_start_multiball")
        self._show_message("TRUBBLE UNLEASHED", "OPEN THE ROOF", reminder=True)
        self._update_saucer_lights()
        self._update_add_a_ball_light()

    def mode_stop(self, **kwargs):
        self.mode_exiting = True
        self._clear_delays()
        if self.post_hold_active:
            self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("trubble_unleashed_clear_all_lights")
        self.machine.events.post("trubble_unleashed_close_gate")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("cancel_mode_message_reminder")
        super().mode_stop(**kwargs)

    def _left_drop_hit(self, **kwargs):
        if self._inactive():
            return
        self.left_drop_hits += 1
        self._score(self.BASIC_DROP_SCORE)
        self.machine.events.post("trubble_unleashed_left_drop_scored", value=self.BASIC_DROP_SCORE)
        self._sync_vars()

    def _left_bank_complete(self, **kwargs):
        if self._inactive():
            return
        self.machine.events.post("trubble_unleashed_left_bank_complete_show")
        self.machine.events.post("trubble_unleashed_open_gate")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self._show_message("ROOF OPEN", "GET TO THE TOP", reminder=True)

    def _right_bank_complete(self, **kwargs):
        if self._inactive():
            return
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

    def _upper_target_hit(self, target_name=None, **kwargs):
        if self._inactive():
            return
        saucer = self.SAUCER_BY_TARGET[target_name]
        self.upper_target_hits += 1
        self.lit_saucers.add(saucer)
        self._score(self.UPPER_TARGET_SCORE)
        self.machine.events.post("trubble_unleashed_saucer_lit", saucer=saucer, value=self.saucer_jackpot_value)
        self.machine.events.post(f"trubble_unleashed_saucer_{saucer}_lit")
        self._show_message("SAUCER LIT", f"SAUCER {saucer}", value=self.saucer_jackpot_value)
        self._sync_vars()
        self._update_saucer_lights()

    def _saucer_hit(self, saucer=None, **kwargs):
        if self._inactive():
            self._kick_saucer(saucer)
            return

        if saucer in self.lit_saucers:
            value = self.saucer_jackpot_value
            self.lit_saucers.discard(saucer)
            self.saucer_jackpots += 1
            self._score(value)
            self.machine.events.post("trubble_unleashed_saucer_jackpot_collected", saucer=saucer, value=value)
            self._show_jackpot("MONSTER JACKPOT", value, f"SAUCER {saucer}")
        else:
            self._score(self.UNLIT_SAUCER_SCORE)
            self.machine.events.post("trubble_unleashed_unlit_saucer", saucer=saucer)

        self._sync_vars()
        self._update_saucer_lights()
        self._kick_saucer(saucer)

    def _upper_exit_left(self, **kwargs):
        if self._inactive():
            return
        self.machine.events.post("trubble_unleashed_close_gate")
        self._show_message("GATE CLOSED", "REOPEN WITH LEFT BANK", reminder=True)

    def _upper_exit_right(self, **kwargs):
        if self._inactive():
            return
        if self.staged_active or self.post_hold_active:
            return

        self.machine.events.post("trubble_unleashed_close_gate")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self._prepare_staged_shot()

    def _prepare_staged_shot(self):
        self.post_hold_active = True
        self.staged_active = False
        self.staged_seconds_left = self.STAGED_SECONDS
        self.staged_targets = set(self._targets_for_next_stage())
        self.ignored_auto_drop_targets.clear()

        self.machine.events.post("trubble_unleashed_staged_prepare", stage=self.staged_successes + 1)
        self.machine.events.post("reset_5bank")
        self.machine.events.post("enable_up_post_event")
        self._show_message("TRUBBLE TRAP", "READY THE STAGED DROP")

        self.delay.remove("trubble_stage_right_bank")
        self.delay.add(
            name="trubble_stage_right_bank",
            ms=self.STAGE_BANK_DELAY_MS,
            callback=self._drop_non_staged_targets,
        )

        self.delay.remove("trubble_post_hold_release")
        self.delay.add(
            name="trubble_post_hold_release",
            ms=self.POST_HOLD_MS,
            callback=self._release_post_hold,
        )
        self._sync_vars()

    def _drop_non_staged_targets(self):
        if self._inactive() or not self.post_hold_active:
            return
        for target in self.ALL_RIGHT_DROPS:
            if target not in self.staged_targets:
                self._auto_drop_right_target(target)
        self.machine.events.post("trubble_unleashed_staged_targets_lit", stage=self.staged_successes + 1)
        self._update_staged_lights()

    def _post_hold_cancel(self, **kwargs):
        if not self.post_hold_active:
            return
        self.delay.remove("trubble_post_hold_release")
        self.machine.events.post("trubble_unleashed_post_hold_cancelled")
        self._release_post_hold(reason="flipper_cancel")

    def _release_post_hold(self, reason="timer", **kwargs):
        if self._inactive() or not self.post_hold_active:
            return
        self.post_hold_active = False
        self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("trubble_unleashed_post_hold_released", reason=reason)
        self._start_staged_timer()

    def _start_staged_timer(self):
        if self._inactive() or not self.staged_targets:
            return
        self.staged_active = True
        self.staged_seconds_left = self.STAGED_SECONDS
        self.machine.events.post("trubble_unleashed_staged_timer_started", seconds=self.staged_seconds_left)
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title="STAGED DROP",
            message_mode_subtitle="HIT TRUBBLE'S TARGET",
            message_mode_value="",
            message_mode_seconds=self.staged_seconds_left,
        )
        self._sync_vars()
        self._schedule_staged_tick()

    def _schedule_staged_tick(self):
        if self._inactive() or not self.staged_active:
            return
        self.delay.add(
            name="trubble_staged_timer_tick",
            ms=1000,
            callback=self._staged_timer_tick,
        )

    def _staged_timer_tick(self):
        if self._inactive() or not self.staged_active:
            return
        self.staged_seconds_left -= 1
        self.machine.events.post("update_mode_status", mode_status_title="SECONDS LEFT", mode_status_value=max(0, self.staged_seconds_left))
        self._sync_vars()
        if self.staged_seconds_left <= 0:
            self._staged_timer_expired()
            return
        self._schedule_staged_tick()

    def _staged_timer_expired(self):
        if self._inactive() or not self.staged_active:
            return
        self.machine.events.post("trubble_unleashed_staged_timer_expired")
        self._end_staged_window(success=False)
        self._show_message("TRAP MISSED", "NO ADD-A-BALL")

    def _right_drop_hit(self, target=None, **kwargs):
        if self._inactive():
            return
        if target in self.ignored_auto_drop_targets:
            self.ignored_auto_drop_targets.discard(target)
            return

        self.right_drop_hits += 1

        if self.staged_active and target in self.staged_targets:
            self._collect_staged_drop(target)
            return

        self._score(self.BASIC_DROP_SCORE)
        self.machine.events.post("trubble_unleashed_right_drop_basic", target=target, value=self.BASIC_DROP_SCORE)
        self._sync_vars()

    def _collect_staged_drop(self, target):
        if self._inactive() or not self.staged_active:
            return
        value = self.STAGED_HIT_SCORE + (self.staged_successes * 25_000)
        self.staged_successes += 1
        self.add_a_ball_qualified = True
        self.saucer_jackpot_value += self.STAGED_JACKPOT_STEP
        self._score(value)
        self.machine.events.post(
            "trubble_unleashed_staged_drop_collected",
            target=target,
            value=value,
            saucer_jackpot=self.saucer_jackpot_value,
            stage=self.staged_successes,
        )
        self._show_jackpot("STAGED HIT", value, f"SAUCERS +{self.STAGED_JACKPOT_STEP}")
        self._end_staged_window(success=True)
        self._update_add_a_ball_light()
        self._sync_vars()

    def _end_staged_window(self, success=False):
        self.staged_active = False
        self.post_hold_active = False
        self.delay.remove("trubble_staged_timer_tick")
        self.delay.remove("trubble_post_hold_release")
        self.delay.remove("trubble_stage_right_bank")
        self.machine.events.post("hide_mode_status")
        for target in sorted(self.staged_targets):
            self._auto_drop_right_target(target)
        self.staged_targets.clear()
        self.machine.events.post("trubble_unleashed_staged_window_ended", success=success)
        self.machine.events.post("trubble_unleashed_clear_staged_lights")
        self.delay.add(
            name="trubble_reset_right_bank_after_stage",
            ms=500,
            callback=lambda: self.machine.events.post("drop_target_bank_dt_bank_right_reset"),
        )
        self._sync_vars()

    def _vuk_hit(self, **kwargs):
        if self._inactive():
            return
        self.delay.add(
            name="trubble_vuk_eject",
            ms=1500,
            callback=lambda: self.machine.events.post("up_kick"),
        )
        if self.add_a_ball_qualified and self._balls_in_play() < self.MAX_BALLS:
            self.add_a_ball_qualified = False
            self.add_a_balls_awarded += 1
            self.machine.events.post("trubble_unleashed_add_a_ball")
            self.machine.events.post("trubble_unleashed_add_a_ball_awarded")
            self._show_jackpot("ADD-A-BALL", 0, "VUK")
            self._update_add_a_ball_light()
        else:
            self._score(self.VUK_UNLIT_SCORE)
        self._sync_vars()

    def _multiball_ended(self, **kwargs):
        if self.mode_done:
            return
        self.machine.events.post("trubble_unleashed_multiball_done")
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.mode_exiting = True
        self._set("trubble_unleashed_state", 2)
        self._clear_delays()
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("trubble_unleashed_clear_all_lights")
        self._sync_vars()
        self.machine.events.post("trubble_unleashed_mode_complete")

    def _targets_for_next_stage(self):
        stage = self.staged_successes + 1
        if stage == 1:
            return (1, 2, 3, 4, 5)
        if stage == 2:
            return (1, 2, 4, 5)
        if stage == 3:
            return (1, 3, 5)
        if stage == 4:
            return (2, 4)
        if stage == 5:
            return (3,)
        return (random.choice(self.ALL_RIGHT_DROPS),)

    def _auto_drop_right_target(self, target):
        self.ignored_auto_drop_targets.add(target)
        self.machine.events.post(f"trubble_unleashed_drop_right_target_{target}")

    def _kick_saucer(self, saucer):
        event = {
            1: "delayed_kickout_saucer_1",
            2: "delayed_kickout_saucer_2",
            3: "delayed_kickout_saucer_3",
        }.get(saucer)
        if event:
            self.machine.events.post(event)
        else:
            self.machine.events.post("clear_saucers")

    def _update_saucer_lights(self):
        self.machine.events.post("trubble_unleashed_clear_saucer_lights")
        for saucer in sorted(self.lit_saucers):
            self.machine.events.post(f"trubble_unleashed_saucer_{saucer}_lit")

    def _update_staged_lights(self):
        self.machine.events.post("trubble_unleashed_clear_staged_lights")
        for target in sorted(self.staged_targets):
            self.machine.events.post(f"trubble_unleashed_right_drop_{target}_staged")

    def _update_add_a_ball_light(self):
        if self.add_a_ball_qualified:
            self.machine.events.post("trubble_unleashed_add_a_ball_lit")
        else:
            self.machine.events.post("trubble_unleashed_add_a_ball_unlit")

    def _clear_delays(self):
        for name in (
            "trubble_stage_right_bank",
            "trubble_post_hold_release",
            "trubble_staged_timer_tick",
            "trubble_reset_right_bank_after_stage",
            "trubble_vuk_eject",
        ):
            self.delay.remove(name)

    def _score(self, points):
        if not points:
            return
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _show_message(self, title, subtitle="", value="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _sync_vars(self):
        self._set("active_mode_points", self.mode_points)
        self._set("active_mode_hits", self.left_drop_hits + self.right_drop_hits + self.upper_target_hits)
        self._set("active_mode_major_hits", self.saucer_jackpots + self.staged_successes + self.add_a_balls_awarded)
        self._set("trubble_unleashed_saucer_jackpot", self.saucer_jackpot_value)
        self._set("trubble_unleashed_saucer_jackpots", self.saucer_jackpots)
        self._set("trubble_unleashed_staged_successes", self.staged_successes)
        self._set("trubble_unleashed_staged_seconds", self.staged_seconds_left)
        self._set("trubble_unleashed_staged_targets", len(self.staged_targets))
        self._set("trubble_unleashed_add_a_ball_qualified", 1 if self.add_a_ball_qualified else 0)
        self._set("trubble_unleashed_add_a_balls", self.add_a_balls_awarded)
        self._set("trubble_unleashed_lit_saucers", len(self.lit_saucers))
        self._set("trubble_unleashed_case_file_bonus", self.case_file_bonus)

    def _inactive(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return True
        return self.mode_done or player["villain_mode_in_summary"] is True

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return self.machine.game.balls_in_play

    def _get(self, name, default=0):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return default
        try:
            return player[name]
        except KeyError:
            return default

    def _set(self, name, value):
        player = self.machine.game.player if self.machine.game else None
        if player is not None:
            player[name] = value
