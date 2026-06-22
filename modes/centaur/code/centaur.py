from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin

"""
Centaur - Charge Trap

Rules:
- Hit drop targets to build the charge.
- Each unique drop scores 25K and adds 100K to the Centaur Jackpot.
- Both drop banks stay down during the build phase; they do not reset when complete.
- Drop-bank rubbers score 25K during the build phase.
- After 4 total drops are down, the rooftop gate opens.
- Exit the upper playfield left to raise the pop-up post and stage the right bank.
- Post holds for 6 seconds, or releases early by flipper/cradle cancel.
- During the hold, the right bank is reset and targets 2, 3, and 4 are knocked down.
- When the post releases, a final-shot timer starts: 6s normally, 12s with More Time.
- Right-bank rubber awards the Centaur Jackpot.
- Right-bank target 1 or 5 awards 50K consolation, unless Shot Assist is active.
- Shot Assist makes right-bank target 1 or 5 award the Centaur Jackpot instead.
- More Jackpots lights the left-bank rubber for a secret half-jackpot.
- Without More Jackpots, a right-bank hit/rubber ends the mode immediately.
- With More Jackpots, right-bank hits do not end the mode; the mode ends when the timer expires.
"""


class Centaur(CaseFileMixin, Mode):
    MODE_KEY = "centaur"
    DISPLAY_NAME = "Centaur"

    DROP_SCORE = 25_000
    RUBBER_SCORE = 25_000
    DROP_JACKPOT_ADD = 100_000
    CONSOLATION_SCORE = 50_000
    DROPS_TO_OPEN_GATE = 4
    POST_HOLD_MS = 6000
    FINAL_TIMER_SECONDS = 6
    MORE_TIME_FINAL_TIMER_SECONDS = 12

    LEFT_DROPS = ("left_1", "left_2", "left_3")
    RIGHT_DROPS = ("right_1", "right_2", "right_3", "right_4", "right_5")
    ALL_DROPS = LEFT_DROPS + RIGHT_DROPS
    FINAL_RIGHT_DROPS = {"right_1", "right_5"}

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "build"
        self.drops_down = set()
        self.mode_points = 0
        self.jackpot_base_value = 0
        self.best_jackpot = 0
        self.jackpots_collected = 0
        self.secret_jackpots_collected = 0
        self.consolation_awarded = 0
        self.gate_open = False
        self.post_hold_active = False
        self.final_active = False
        self.final_seconds = self.FINAL_TIMER_SECONDS
        self.final_seconds_left = 0
        self.right_result_collected = False
        self.right_full_jackpot_collected = False
        self.left_secret_collected = False

        self._apply_case_file_bonuses()
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "LEFT RUBBER SECRET 1/2 JACKPOT"),
            ("bigger_jackpots", "CENTAUR JACKPOT 2X"),
            ("more_time", "FINAL TIMER EXTENDED TO 12s"),
            ("safety_net", "10 SECOND BALL SAVE ON FINAL SHOT"),
            ("shot_assist", "RIGHT DROPS SCORE JACKPOT"),
        ])

        for target in self.ALL_DROPS:
            self.add_mode_event_handler(
                f"centaur_drop_{target}_hit",
                self._drop_hit,
                target=target,
            )

        self.add_mode_event_handler("centaur_left_rubber_hit", self._left_rubber_hit)
        self.add_mode_event_handler("centaur_right_rubber_hit", self._right_rubber_hit)
        self.add_mode_event_handler("centaur_bank_rubber_hit", self._bank_rubber_hit)
        self.add_mode_event_handler("centaur_upper_left_exit", self._upper_left_exit)
        self.add_mode_event_handler("centaur_post_hold_cancel", self._post_hold_cancel)
        self.add_mode_event_handler("centaur_complete_request", self._complete_mode)
        self.add_mode_event_handler("centaur_fail_request", self._fail_mode)

        self.machine.events.post("clear_saucers")
        self.machine.events.post("reset_drops")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("centaur_startup_complete")
        self.machine.events.post("centaur_build_phase_started")
        self._show_mode_message("BUILD THE CHARGE", "4 DROPS OPENS THE GATE")

    def mode_stop(self, **kwargs):
        self.delay.remove("centaur_post_hold_release")
        self.delay.remove("centaur_stage_right_bank")
        self.delay.remove("centaur_final_timer_tick")
        if self.post_hold_active:
            self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("centaur_clear_all_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)


    def _show_mode_message(self, title, subtitle="", value="", seconds=""):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
        )

    def _show_mode_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _show_mode_countdown(self, title, seconds, subtitle=""):
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value="",
            message_mode_seconds=seconds,
        )

    def _apply_case_file_bonuses(self):
        if self.has_case_file("more_time"):
            self.final_seconds = self.MORE_TIME_FINAL_TIMER_SECONDS
        else:
            self.final_seconds = self.FINAL_TIMER_SECONDS

    def _drop_hit(self, target=None, **kwargs):
        if self._done_or_summary():
            return

        if self.phase in ("build", "roof_ready"):
            self._build_drop_hit(target)
            return

        if self.phase == "final" and target in self.FINAL_RIGHT_DROPS:
            self._right_drop_final_hit(target)
            return

    def _build_drop_hit(self, target):
        if target in self.drops_down:
            return

        self.drops_down.add(target)
        self.jackpot_base_value += self.DROP_JACKPOT_ADD
        self._score(self.DROP_SCORE)
        self._sync_vars()

        self.machine.events.post(
            "centaur_drop_build_hit",
            target=target,
            drops_down=len(self.drops_down),
            jackpot=self._current_jackpot_value(),
        )
        self._show_mode_jackpot(
            "JACKPOT BUILDS",
            self._current_jackpot_value(),
            f"{len(self.drops_down)} DROPS DOWN",
        )

        if not self.gate_open and len(self.drops_down) >= self.DROPS_TO_OPEN_GATE:
            self.gate_open = True
            self.phase = "roof_ready"
            self.machine.events.post("rooftop_diverter_open")
            self.machine.events.post("centaur_gate_open")
            self._show_mode_message("GATE OPEN", "GET TO THE ROOF")
            self._sync_vars()

    def _bank_rubber_hit(self, **kwargs):
        if self._done_or_summary():
            return

        if self.phase in ("build", "roof_ready"):
            self._score(self.RUBBER_SCORE)
            self.machine.events.post("centaur_bank_rubber_score", value=self.RUBBER_SCORE)
            self._sync_vars()

    def _left_rubber_hit(self, **kwargs):
        if self._done_or_summary():
            return

        if self.phase == "final" and self.has_case_file("more_jackpots"):
            if self.left_secret_collected:
                return
            self.left_secret_collected = True
            secret_value = self._secret_jackpot_value()
            self.secret_jackpots_collected += 1
            self._score(secret_value)
            self.machine.events.post("centaur_secret_half_jackpot_awarded", value=secret_value)
            self._show_mode_jackpot("SECRET HALF JACKPOT", secret_value)
            self._sync_vars()
            return

        self._bank_rubber_hit()

    def _right_rubber_hit(self, **kwargs):
        if self._done_or_summary():
            return

        if self.phase == "final":
            self._award_right_full_jackpot(source="right_rubber")
            return

        self._bank_rubber_hit()

    def _upper_left_exit(self, **kwargs):
        if self._done_or_summary():
            return

        if self.phase != "roof_ready":
            return

        self.phase = "post_hold"
        self.post_hold_active = True
        self.machine.events.post("centaur_post_hold_started")
        self._show_mode_message("POST HOLD", "RIGHT BANK IS STAGING")
        self.machine.events.post("enable_up_post_event")
        self._stage_right_bank()

        self.delay.add(
            name="centaur_post_hold_release",
            ms=self.POST_HOLD_MS,
            callback=self._release_post_hold,
        )
        self._sync_vars()

    def _stage_right_bank(self):
        self.machine.events.post("centaur_stage_right_bank_started")
        self.machine.events.post("reset_5bank")
        self.delay.add(
            name="centaur_stage_right_bank",
            ms=500,
            callback=self._drop_staged_right_targets,
        )

    def _drop_staged_right_targets(self):
        if self._done_or_summary():
            return
        self.machine.events.post("centaur_stage_right_bank_drops")
        self.machine.events.post("centaur_final_shot_staged")

    def _post_hold_cancel(self, **kwargs):
        if not self.post_hold_active:
            return
        self.machine.events.post("centaur_post_hold_cancelled")
        self._release_post_hold(cancel_delay=True, reason="flipper_cancel")

    def _release_post_hold(self, cancel_delay=False, reason="timer"):
        if cancel_delay:
            self.delay.remove("centaur_post_hold_release")

        if not self.post_hold_active:
            return

        self.post_hold_active = False
        self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("centaur_post_hold_released", reason=reason)
        self._start_final_phase()

    def _start_final_phase(self):
        if self._done_or_summary():
            return

        self.phase = "final"
        self.final_active = True
        self.final_seconds_left = self.final_seconds
        self.right_result_collected = False
        self.right_full_jackpot_collected = False
        self.left_secret_collected = False

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.machine.events.post(
            "centaur_final_timer_started",
            seconds=self.final_seconds_left,
            jackpot=self._current_jackpot_value(),
        )
        self._show_mode_countdown("HIT RIGHT RUBBER", self.final_seconds_left, "CENTAUR JACKPOT")
        self._sync_vars()
        self._schedule_final_tick()

    def _schedule_final_tick(self):
        if self._done_or_summary() or not self.final_active:
            return

        self.delay.add(
            name="centaur_final_timer_tick",
            ms=1000,
            callback=self._final_timer_tick,
        )

    def _final_timer_tick(self):
        if self._done_or_summary() or not self.final_active:
            return

        self.final_seconds_left -= 1
        self._sync_vars()
        self.machine.events.post("centaur_final_timer_changed", seconds=self.final_seconds_left)
        self._show_mode_countdown("HIT RIGHT RUBBER", self.final_seconds_left, "CENTAUR JACKPOT")

        if self.final_seconds_left <= 0:
            self._final_timer_expired()
            return

        self._schedule_final_tick()

    def _final_timer_expired(self):
        if self._done_or_summary():
            return

        self.final_active = False
        self.machine.events.post("centaur_final_timer_expired")
        self._show_mode_message("CENTAUR ESCAPED", "FINAL TIMER EXPIRED")

        if self.right_full_jackpot_collected:
            self._complete_mode()
        else:
            self._fail_mode()

    def _right_drop_final_hit(self, target):
        if self.right_result_collected:
            return

        if self.has_case_file("shot_assist"):
            self._award_right_full_jackpot(source=target, shot_assist=True)
        else:
            self._award_consolation(source=target)

    def _award_right_full_jackpot(self, source="right_rubber", shot_assist=False):
        if self.right_result_collected:
            return

        self.right_result_collected = True
        self.right_full_jackpot_collected = True
        jackpot_value = self._current_jackpot_value()
        self.jackpots_collected += 1
        self.best_jackpot = max(self.best_jackpot, jackpot_value)
        self._score(jackpot_value)
        self.machine.events.post(
            "centaur_jackpot_awarded",
            value=jackpot_value,
            source=source,
            shot_assist=shot_assist,
        )
        self._show_mode_jackpot("CENTAUR JACKPOT", jackpot_value)
        self._sync_vars()

        if not self.has_case_file("more_jackpots"):
            self._complete_mode()

    def _award_consolation(self, source=None):
        if self.right_result_collected:
            return

        self.right_result_collected = True
        self.consolation_awarded = 1
        self._score(self.CONSOLATION_SCORE)
        self.machine.events.post("centaur_consolation_awarded", value=self.CONSOLATION_SCORE, source=source)
        self._show_mode_jackpot("CONSOLATION", self.CONSOLATION_SCORE)
        self._sync_vars()

        if not self.has_case_file("more_jackpots"):
            self._fail_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.final_active = False
        self.delay.remove("centaur_final_timer_tick")
        player = self.machine.game.player
        player["centaur_state"] = 2
        self._sync_vars()
        self.machine.events.post("centaur_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.final_active = False
        self.delay.remove("centaur_final_timer_tick")
        player = self.machine.game.player
        player["centaur_state"] = 1
        self._sync_vars()
        self.machine.events.post("centaur_mode_complete")

    def _current_jackpot_value(self):
        jackpot = self.jackpot_base_value
        if self.has_case_file("bigger_jackpots"):
            jackpot *= 2
        return jackpot

    def _secret_jackpot_value(self):
        return self._current_jackpot_value() // 2

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["centaur_mode_points"] = self.mode_points
        player["centaur_drops_down"] = len(self.drops_down)
        player["centaur_jackpot_value"] = self._current_jackpot_value()
        player["centaur_best_jackpot"] = self.best_jackpot
        player["centaur_jackpots"] = self.jackpots_collected
        player["centaur_secret_jackpots"] = self.secret_jackpots_collected
        player["centaur_consolation_awarded"] = self.consolation_awarded
        player["centaur_final_seconds"] = self.final_seconds_left
        player["centaur_phase"] = self.phase
        player["centaur_gate_open"] = 1 if self.gate_open else 0
        player["centaur_final_active"] = 1 if self.final_active else 0

    def _done_or_summary(self):
        player = self.machine.game.player
        return self.mode_done or player["villain_mode_in_summary"] is True
