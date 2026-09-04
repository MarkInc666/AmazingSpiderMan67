from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin
import random


class doc_ock(CaseFileMixin, Mode):
    BREAKOUT_BONUS_PER_JACKPOT = 100_000
    JACKPOTS_BEFORE_TIMED_RELEASE = 2
    DEFAULT_ARM_RELEASE_DELAY_MS = 10_000
    MORE_TIME_ARM_RELEASE_DELAY_MS = 15_000
    TIMED_RELEASE_DELAY_NAME = "doc_ock_timed_release"
    TIMED_RELEASE_WARNING_DELAY_NAME = "doc_ock_timed_release_warning"
    SPINNER_SETTLE_DELAY_NAME = "doc_ock_spinner_settle"
    SPINNER_VALUE_DELAY_NAME = "doc_ock_spinner_value"
    COMPLETION_HOLD_DELAY_NAME = "doc_ock_completion_hold"
    JACKPOT_COLLECT_GUARD_DELAY_NAME = "doc_ock_jackpot_collect_guard"
    JACKPOT_COLLECT_GUARD_MS = 750
    ROOFTOP_GATE_WINDOW_MS = 20_000
    ROOFTOP_GATE_DELAY_NAME = "doc_ock_rooftop_gate_window"
    MAX_BREAKOUT_TARGETS = 6

    def _post_mode_jackpot_sfx_if_needed(
        self,
        guarded_display_event="",
        message_mode_title="",
        message_mode_subtitle="",
    ):
        """Mode-local jackpot SFX hook; replace these events per mode as desired."""
        if guarded_display_event != "base_show_mode_jackpot":
            return
        title = str(message_mode_title or "").upper()
        subtitle = str(message_mode_subtitle or "").upper()
        combined = f"{title} {subtitle}".replace("-", " ")
        words = combined.split()
        if "JACKPOT" not in words:
            return
        if any(marker in title.split() for marker in ("BUILDS", "LIT", "READY", "NEXT")):
            return
        if "SUPER" in words:
            self.machine.events.post("play_mode_super_jackpot")
        else:
            self.machine.events.post("play_mode_jackpot")

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.doc_ock_arm_release_delay_ms = (
            self.MORE_TIME_ARM_RELEASE_DELAY_MS
            if self.has_case_file("more_time")
            else self.DEFAULT_ARM_RELEASE_DELAY_MS
        )
        self.doc_ock_jackpot_base_value = 75_000 if self.has_case_file("bigger_jackpots") else 50_000
        self.doc_ock_jackpot_unlit_value = 25_000
        self.doc_ock_breakout_value = 50_000
        self.doc_ock_rollover_value = 10_000
        self.doc_ock_left_bank_complete_score = 50_000
        self.doc_ock_left_bank_all_locked_score = 100_000

        self.doc_ock_jackpot_spinner_multi = 10 if self.has_case_file("shot_assist") else 1
        self.locked_arms = [False, False, False, False]
        for arm_index in random.sample(range(4), 2):
            self.locked_arms[arm_index] = True

        self.jackpot_lit = True
        self.jackpot_collect_guard = False
        self.timed_release_running = False
        self.mode_finishing = False
        self.jackpots_collected = 0
        self.active_breakouts = set()
        self.doc_ock_max_arms_locked = 2
        self.active_mode_points = 0
        self.safety_net_used = False
        self.rooftop_gate_open = False

        self.publish_case_file_bonus_events("doc_ock")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "2 SAFE JACKPOTS"),
            ("bigger_jackpots", "BIGGER DOC OCK JACKPOTS"),
            ("more_time", "ARM RELEASE DELAYED"),
            ("safety_net", "10 SECOND BALL SAVE"),
            ("shot_assist", "+10X SHOT ASSIST"),
        ])

        self.add_mode_event_handler("doc_ock_spinner_hit", self.doc_ock_spinner)
        self.add_mode_event_handler("doc_ock_start_arms", self.doc_ock_start_arms)
        self.add_mode_event_handler("doc_ock_rotate_left", self.rotate_left)
        self.add_mode_event_handler("doc_ock_rotate_right", self.rotate_right)
        self.add_mode_event_handler("doc_ock_jackpot_request", self.jackpot_request)
        self.add_mode_event_handler("doc_ock_left_bank_complete", self.left_bank_complete)
        self.add_mode_event_handler("doc_ock_right_bank_complete", self.right_bank_complete)
        self.add_mode_event_handler("doc_ock_start_timed_release", self.start_timed_release)
        self.add_mode_event_handler("doc_ock_stop_timed_release", self.stop_timed_release)

        for arm in range(1, 5):
            self.add_mode_event_handler(f"doc_ock_arm_{arm}_hit", self.arm_hit, arm=arm)
        for breakout in range(1, 7):
            self.add_mode_event_handler(
                f"doc_ock_breakout_{breakout}_request", self.breakout_hit, breakout=breakout
            )

        self.update_player_vars()
        self._close_rooftop_gate(restore_available=True)
        self.machine.events.post("doc_ock_startup_complete")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="DOCTOR OCTOPUS",
            message_mode_subtitle="LOCK THE ARMS - COLLECT WEB JACKPOTS",
        )

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        if hasattr(self, "delay"):
            for name in (
                self.TIMED_RELEASE_DELAY_NAME,
                self.TIMED_RELEASE_WARNING_DELAY_NAME,
                self.SPINNER_SETTLE_DELAY_NAME,
                self.SPINNER_VALUE_DELAY_NAME,
                self.COMPLETION_HOLD_DELAY_NAME,
                self.JACKPOT_COLLECT_GUARD_DELAY_NAME,
                self.ROOFTOP_GATE_DELAY_NAME,
            ):
                self.delay.remove(name)
        self.timed_release_running = False
        self.clear_active_case_file_helpers()
        self._close_rooftop_gate(restore_available=False)
        # Catch-all: no delayed villain/wizard callback may survive into bonus.
        self.delay.clear()
        super().mode_stop(**kwargs)

    def _rules_active(self):
        return not self.mode_finishing and not self.machine.game.player["villain_mode_in_summary"]

    def _award_points(self, value):
        value = int(value)
        self.machine.game.player["score"] += value
        self.active_mode_points += value
        self.machine.game.player["active_mode_points"] = self.active_mode_points

    def _cancel_spinner_messages(self):
        self.delay.remove(self.SPINNER_SETTLE_DELAY_NAME)
        self.delay.remove(self.SPINNER_VALUE_DELAY_NAME)

    def _post_high_priority_message(self, title, subtitle=None, value=None, long=False):
        self._cancel_spinner_messages()
        event = "show_mode_message_long" if long else "show_mode_message"
        kwargs = {"message_mode_title": title}
        if subtitle is not None:
            kwargs["message_mode_subtitle"] = subtitle
        if value is not None:
            kwargs["message_mode_value"] = value
        self.machine.events.post(event, **kwargs)

    def doc_ock_start_arms(self, **kwargs):
        self.refresh_lane_lights()
        self._set_jackpot_lit(True)

    def rotate_left(self, **kwargs):
        if not self._rules_active():
            return
        self.locked_arms = self.locked_arms[1:] + self.locked_arms[:1]
        self.refresh_lane_lights()

    def rotate_right(self, **kwargs):
        if not self._rules_active():
            return
        self.locked_arms = self.locked_arms[-1:] + self.locked_arms[:-1]
        self.refresh_lane_lights()

    def refresh_lane_lights(self):
        for arm in range(1, 5):
            state = "solid" if self.locked_arms[arm - 1] else "pulse"
            self.machine.events.post(f"doc_ock_arm_{arm}_{state}")

        if all(self.locked_arms):
            self.machine.events.post("doc_ock_left_bank_not_needed")
        else:
            self.machine.events.post("doc_ock_left_bank_needed")

    def _set_jackpot_lit(self, lit):
        self.jackpot_lit = bool(lit)
        if self.jackpot_lit and sum(self.locked_arms) > 0:
            self.machine.events.post("doc_ock_jackpot_lit")
        self.update_player_vars()

    def arm_hit(self, arm, **kwargs):
        if not self._rules_active():
            return
        self._award_points(self.doc_ock_rollover_value)
        self._set_jackpot_lit(True)

        if self.locked_arms[arm - 1]:
            return

        self._lock_arm_index(arm - 1)
        self.machine.events.post("doc_ock_arm_locked_score")
        self._post_high_priority_message("ARM LOCKED")

    def _lock_arm_index(self, arm_index):
        if self.locked_arms[arm_index]:
            return False
        self.locked_arms[arm_index] = True
        self.doc_ock_max_arms_locked = max(self.doc_ock_max_arms_locked, sum(self.locked_arms))
        self.machine.game.player["active_mode_stat_1"] = self.doc_ock_max_arms_locked
        self.refresh_lane_lights()
        self._set_jackpot_lit(True)
        if self.timed_release_running:
            self.start_timed_release(force_reset=True)
        return True

    def _lock_random_free_arm(self):
        free = [index for index, locked in enumerate(self.locked_arms) if not locked]
        if not free:
            return False
        return self._lock_arm_index(random.choice(free))

    def left_bank_complete(self, **kwargs):
        if not self._rules_active():
            return
        locked_new_arm = self._lock_random_free_arm()
        award = self.doc_ock_left_bank_complete_score if locked_new_arm else self.doc_ock_left_bank_all_locked_score
        self._award_points(award)
        self._set_jackpot_lit(True)
        if locked_new_arm:
            self.machine.events.post("doc_ock_arm_locked_score")
            self._post_high_priority_message("ARM LOCKED")

    def right_bank_complete(self, **kwargs):
        if not self._rules_active():
            return
        self.rooftop_gate_open = True
        self.delay.remove(self.ROOFTOP_GATE_DELAY_NAME)
        self.delay.add(
            name=self.ROOFTOP_GATE_DELAY_NAME,
            ms=self.ROOFTOP_GATE_WINDOW_MS,
            callback=self._rooftop_gate_window_expired,
        )
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("doc_ock_rooftop_gate_open")
        self._post_high_priority_message("ROOFTOP ACCESS OPEN", "20 SECONDS")

    def _rooftop_gate_window_expired(self, **kwargs):
        self._close_rooftop_gate(restore_available=True)

    def _close_rooftop_gate(self, restore_available=False):
        if hasattr(self, "delay"):
            self.delay.remove(self.ROOFTOP_GATE_DELAY_NAME)
        self.rooftop_gate_open = False
        self.machine.events.post("rooftop_diverter_close")
        event = "doc_ock_rooftop_gate_available" if restore_available and self._rules_active() else "doc_ock_rooftop_gate_cleanup"
        self.machine.events.post(event)

    def doc_ock_spinner(self, **kwargs):
        if not self._rules_active():
            return
        self.doc_ock_jackpot_spinner_multi += 1
        self._set_jackpot_lit(True)
        self.machine.events.post(
            "doc_ock_spinner_multiplier_increased", multiplier=self.doc_ock_jackpot_spinner_multi
        )
        self._cancel_spinner_messages()
        self.delay.add(
            name=self.SPINNER_SETTLE_DELAY_NAME,
            ms=1000,
            callback=self._show_spinner_multiplier,
        )

    def _show_spinner_multiplier(self, **kwargs):
        if not self._rules_active():
            return
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=f"MULTIPLIER {self.doc_ock_jackpot_spinner_multi}X",
        )
        self.delay.add(
            name=self.SPINNER_VALUE_DELAY_NAME,
            ms=1000,
            callback=self._show_spinner_jackpot_value,
        )

    def _show_spinner_jackpot_value(self, **kwargs):
        if not self._rules_active():
            return
        value = self.calculate_next_jackpot()
        if value > 0:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="NEXT WEB JACKPOT",
                message_mode_value=value,
            )

    def _clear_jackpot_collect_guard(self, **kwargs):
        self.jackpot_collect_guard = False

    def jackpot_request(self, **kwargs):
        if not self._rules_active() or self.jackpot_collect_guard:
            return
        if not self.jackpot_lit:
            self._award_points(self.doc_ock_jackpot_unlit_value)
            self.machine.events.post("doc_ock_jackpot_not_lit")
            return

        locked = sum(self.locked_arms)
        if locked <= 0:
            return

        collected_multiplier = self.doc_ock_jackpot_spinner_multi
        collected_value = self.doc_ock_jackpot_base_value * (5 - locked) * collected_multiplier

        self.jackpot_collect_guard = True
        self.delay.add(
            name=self.JACKPOT_COLLECT_GUARD_DELAY_NAME,
            ms=self.JACKPOT_COLLECT_GUARD_MS,
            callback=self._clear_jackpot_collect_guard,
        )
        self._cancel_spinner_messages()
        self.jackpot_lit = False
        self._award_points(collected_value)
        self.jackpots_collected += 1
        player = self.machine.game.player
        player["active_mode_stat_2"] = self.jackpots_collected
        player["doc_ock_last_jackpot"] = collected_value
        player["doc_ock_bonus"] += self.BREAKOUT_BONUS_PER_JACKPOT
        self.machine.events.post(
            "doc_ock_breakout_bonus_added",
            value=self.BREAKOUT_BONUS_PER_JACKPOT,
            total=player["doc_ock_bonus"],
        )

        self.machine.events.post("doc_ock_jackpot_award")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="WEB JACKPOT",
            message_mode_value=collected_value,
        )

        self.doc_ock_jackpot_spinner_multi = self.jackpots_collected + 1

        safe_jackpot = self.has_case_file("more_jackpots") and self.jackpots_collected <= 2
        if not safe_jackpot:
            self.spawn_breakout_target()

        if self.jackpots_collected >= self.JACKPOTS_BEFORE_TIMED_RELEASE and not self.timed_release_running:
            self.start_timed_release()
        self.update_player_vars()

    def spawn_breakout_target(self):
        available = [target for target in range(1, 7) if target not in self.active_breakouts]
        if not available:
            return
        target = random.choice(available)
        self.active_breakouts.add(target)
        self.machine.events.post(f"doc_ock_breakout_{target}_lit")
        self.update_player_vars()

    def breakout_hit(self, breakout, **kwargs):
        if not self._rules_active() or breakout not in self.active_breakouts:
            return
        self.active_breakouts.remove(breakout)
        self.machine.events.post(f"doc_ock_breakout_{breakout}_collected")
        self._award_points(self.doc_ock_breakout_value)
        self._release_random_locked_arm()

    def start_timed_release(self, force_reset=False, **kwargs):
        if not self._rules_active() or self.jackpots_collected < self.JACKPOTS_BEFORE_TIMED_RELEASE:
            return
        if sum(self.locked_arms) <= 0:
            return
        if self.timed_release_running and not force_reset:
            return

        self.timed_release_running = True
        self.delay.remove(self.TIMED_RELEASE_DELAY_NAME)
        self.delay.remove(self.TIMED_RELEASE_WARNING_DELAY_NAME)
        self.delay.add(
            name=self.TIMED_RELEASE_WARNING_DELAY_NAME,
            ms=self.doc_ock_arm_release_delay_ms // 2,
            callback=self._timed_release_warning,
        )
        self.delay.add(
            name=self.TIMED_RELEASE_DELAY_NAME,
            ms=self.doc_ock_arm_release_delay_ms,
            callback=self.timed_release,
        )

    def _timed_release_warning(self, **kwargs):
        if self._rules_active() and self.timed_release_running:
            self._post_high_priority_message("DOC OCK IS ABOUT TO BREAK FREE!")

    def stop_timed_release(self, **kwargs):
        self.timed_release_running = False
        if hasattr(self, "delay"):
            self.delay.remove(self.TIMED_RELEASE_DELAY_NAME)
            self.delay.remove(self.TIMED_RELEASE_WARNING_DELAY_NAME)

    def timed_release(self, **kwargs):
        if not self._rules_active() or not self.timed_release_running:
            self.stop_timed_release()
            return
        self._release_random_locked_arm()
        if self._rules_active() and sum(self.locked_arms) > 0:
            self.timed_release_running = False
            self.start_timed_release()

    def _release_random_locked_arm(self):
        locked = [index for index, state in enumerate(self.locked_arms) if state]
        if not locked:
            self._begin_completion()
            return False
        self.locked_arms[random.choice(locked)] = False
        self.refresh_lane_lights()
        self.machine.events.post("doc_ock_breakout_hit")
        self._post_high_priority_message("AN ARM BROKE FREE!")

        if self.has_case_file("safety_net") and not self.safety_net_used:
            self.safety_net_used = True
            self.machine.events.post("start_case_file_ball_save")

        self.update_player_vars()
        if sum(self.locked_arms) <= 0:
            self._begin_completion()
        return True

    def _begin_completion(self):
        if self.mode_finishing:
            return
        self.mode_finishing = True
        self._close_rooftop_gate(restore_available=False)
        self.stop_timed_release()
        self._cancel_spinner_messages()
        self.machine.events.post("hide_mode_status")
        self._post_high_priority_message("DOCTOR OCTOPUS HAS BROKEN FREE!", long=True)
        self.delay.add(
            name=self.COMPLETION_HOLD_DELAY_NAME,
            ms=2000,
            callback=self._complete_mode,
        )

    def _complete_mode(self, **kwargs):
        if not self.mode_finishing:
            return
        self.machine.events.post("doc_ock_mode_complete")

    def update_player_vars(self):
        player = self.machine.game.player
        player["doc_ock_locked_arms"] = sum(self.locked_arms)
        player["doc_ock_spinner_multi"] = self.doc_ock_jackpot_spinner_multi
        player["doc_ock_jackpots_collected"] = self.jackpots_collected
        player["active_mode_stat_2"] = self.jackpots_collected
        player["doc_ock_active_breakouts"] = len(self.active_breakouts)
        player["doc_ock_next_jackpot"] = self.calculate_next_jackpot()
        player["active_mode_points"] = self.active_mode_points
        if not self.mode_finishing:
            self.machine.events.post(
                "update_mode_status",
                mode_status_title="DOCTOR OCTOPUS",
                mode_status_value=f"{sum(self.locked_arms)} ARMS LOCKED",
            )

    def calculate_next_jackpot(self):
        locked = sum(self.locked_arms)
        if locked <= 0 or not self.jackpot_lit:
            return 0
        return self.doc_ock_jackpot_base_value * (5 - locked) * self.doc_ock_jackpot_spinner_multi
