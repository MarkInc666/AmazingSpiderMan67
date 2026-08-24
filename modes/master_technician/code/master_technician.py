import random

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class MasterTechnician(CaseFileMixin, Mode):
    """Timed spinner/drop-target score attack."""

    MODE_KEY = "master_technician"

    BASE_SECONDS = 60
    MORE_TIME_SECONDS = 75
    TIME_PENALTY = 10

    DROP_SCORE = 25_000
    UNLIT_SPINNER_SCORE = 10_000
    SPINNER_PER_DROP = 50_000
    BIGGER_SPINNER_PER_DROP = 75_000
    WEB_JACKPOT_SCORE = 50_000

    INLANE_DROP_GUARD_MS = 1_500
    SHOT_ASSIST_STEP_MS = 250

    TARGETS = (
        "left_1", "left_2", "left_3",
        "right_1", "right_2", "right_3", "right_4", "right_5",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.started = False
        self.seconds_left = (
            self.MORE_TIME_SECONDS
            if self.has_case_file("more_time")
            else self.BASE_SECONDS
        )
        self.spinner_per_drop = (
            self.BIGGER_SPINNER_PER_DROP
            if self.has_case_file("bigger_jackpots")
            else self.SPINNER_PER_DROP
        )

        self.left_down = set()
        self.right_down = set()
        self.pending_inlane_drops = set()
        self.shot_assist_used = False
        self.safety_net_used = False
        self.spinner_hits = 0
        self.short_circuits = 0

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_stat_1"] = 0
        player["active_mode_stat_2"] = 0

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "WEB TARGETS SCORE 50K WHILE SPINNER IS LIT"),
            ("bigger_jackpots", "SPINNER BUILDS 75K PER DOWN TARGET"),
            ("more_time", "MODE TIMER EXTENDED TO 75s"),
            ("safety_net", "FIRST SHORT CIRCUIT HAS NO TIME PENALTY"),
            ("shot_assist", "FIRST INLANE CAN DROP TWO SAFE TARGETS"),
        ])

        self.add_mode_event_handler("master_technician_start", self._start_mode)
        self.add_mode_event_handler("master_technician_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("master_technician_web_hit", self._web_hit)
        self.add_mode_event_handler("master_technician_inlane_hit", self._inlane_hit)

        for target in range(1, 4):
            self.add_mode_event_handler(
                f"master_technician_left_drop_{target}_hit",
                self._left_drop_hit,
                target=target,
            )

        for target in range(1, 6):
            self.add_mode_event_handler(
                f"master_technician_right_drop_{target}_hit",
                self._right_drop_hit,
                target=target,
            )

        # Do not rely on mode_master_technician_started to post the gameplay
        # start event. Announce readiness only after every Python handler above
        # is registered, then let the mode config perform its ordered startup.
        self.machine.events.post("master_technician_startup_complete")

    def mode_stop(self, **kwargs):
        self.delay.remove("master_technician_timer_tick")
        self.delay.remove("master_technician_shot_assist_second_drop")
        for target in self.TARGETS:
            self.delay.remove(f"master_technician_inlane_guard_{target}")
        self.machine.events.post("master_technician_clear_lights")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _start_mode(self, **kwargs):
        if self.started or self.mode_done:
            return
        self.started = True
        self.machine.events.post("master_technician_level_0")
        self.machine.events.post("master_technician_clear_webs")
        self._show_message(
            "BUILD THE SPINNER",
            "STOP AT SEVEN - ALL EIGHT COSTS 10s",
            reminder=True,
        )
        self._update_mode_status()
        self._schedule_timer_tick()

    def _schedule_timer_tick(self):
        self.delay.reset(
            name="master_technician_timer_tick",
            ms=1_000,
            callback=self._timer_tick,
        )

    def _timer_tick(self, **kwargs):
        if self.mode_done or not self.started:
            return
        self.seconds_left = max(0, self.seconds_left - 1)
        self.machine.events.post(
            "master_technician_timer_changed",
            seconds=self.seconds_left,
        )
        self._update_mode_status()
        if self.seconds_left <= 0:
            self._finish_mode()
            return
        self._schedule_timer_tick()

    def _left_drop_hit(self, target, **kwargs):
        self._drop_hit("left", target)

    def _right_drop_hit(self, target, **kwargs):
        self._drop_hit("right", target)

    def _drop_hit(self, bank, target):
        if self.mode_done or not self.started:
            return

        key = f"{bank}_{target}"
        if key in self.pending_inlane_drops:
            self.pending_inlane_drops.discard(key)
            self.delay.remove(f"master_technician_inlane_guard_{key}")

        down_set = self.left_down if bank == "left" else self.right_down
        if target in down_set:
            return

        down_set.add(target)
        self._award_score(self.DROP_SCORE)
        self.machine.events.post(
            "master_technician_drop_scored",
            value=self.DROP_SCORE,
            drops_down=self.total_drops_down(),
        )

        if self.total_drops_down() >= len(self.TARGETS):
            self._short_circuit()
            return

        self._update_level_lights()
        self._update_mode_status()

    def _short_circuit(self):
        self.short_circuits += 1
        self.machine.game.player["active_mode_stat_2"] = self.short_circuits

        if self.has_case_file("safety_net") and not self.safety_net_used:
            self.safety_net_used = True
            self.machine.events.post("master_technician_safety_net_used")
            self._show_message(
                "SAFETY NET",
                "TIME PENALTY CANCELLED",
                value=f"{self.seconds_left} SECONDS",
            )
        else:
            self.seconds_left = max(0, self.seconds_left - self.TIME_PENALTY)
            self.machine.events.post(
                "master_technician_time_penalty",
                seconds=self.seconds_left,
                penalty=self.TIME_PENALTY,
            )
            self._show_message(
                "SHORT CIRCUIT",
                "ALL TARGETS DOWN",
                value=f"-{self.TIME_PENALTY} SECONDS",
            )

        self.left_down.clear()
        self.right_down.clear()
        self.pending_inlane_drops.clear()
        self.delay.remove("master_technician_shot_assist_second_drop")
        self.machine.events.post("master_technician_reset_banks")
        self.machine.events.post("master_technician_level_0")
        self.machine.events.post("master_technician_clear_webs")
        self._update_mode_status()

        if self.seconds_left <= 0:
            self._finish_mode()

    def _spinner_hit(self, **kwargs):
        if self.mode_done or not self.started:
            return
        value = self.spinner_value()
        self.spinner_hits += 1
        self.machine.game.player["active_mode_stat_1"] = self.spinner_hits
        self._award_score(value)
        self.machine.events.post(
            "master_technician_spinner_scored",
            value=value,
            drops_down=self.total_drops_down(),
        )
        self._update_mode_status()

    def _web_hit(self, **kwargs):
        if (
            self.mode_done
            or not self.started
            or not self.has_case_file("more_jackpots")
            or not 1 <= self.total_drops_down() <= 7
        ):
            return
        self._award_score(self.WEB_JACKPOT_SCORE)
        self.machine.events.post(
            "master_technician_web_jackpot_scored",
            value=self.WEB_JACKPOT_SCORE,
        )
        self._show_jackpot("WEB JACKPOT", self.WEB_JACKPOT_SCORE)

    def _inlane_hit(self, **kwargs):
        if self.mode_done or not self.started or self.pending_inlane_drops:
            return

        standing = [target for target in self.TARGETS if not self._target_is_down(target)]
        if not standing:
            return

        drop_count = 1
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            drop_count = min(2, max(0, 7 - self.total_drops_down()))
            self.machine.events.post("master_technician_shot_assist_used")
            if drop_count == 0:
                self._show_message("SHOT ASSIST", "FINAL TARGET HELD")
                return

        selected = random.sample(standing, min(drop_count, len(standing)))
        self._knockdown_from_inlane(selected[0])
        if len(selected) > 1:
            self.delay.reset(
                name="master_technician_shot_assist_second_drop",
                ms=self.SHOT_ASSIST_STEP_MS,
                callback=self._knockdown_from_inlane,
                target=selected[1],
            )

    def _knockdown_from_inlane(self, target, **kwargs):
        if self.mode_done or self._target_is_down(target):
            return
        self.pending_inlane_drops.add(target)
        self.delay.reset(
            name=f"master_technician_inlane_guard_{target}",
            ms=self.INLANE_DROP_GUARD_MS,
            callback=self._clear_inlane_drop_guard,
            target=target,
        )
        self.machine.drop_targets[f"dt_{target}"].knockdown()
        self.machine.events.post("master_technician_inlane_advance", target=target)

    def _clear_inlane_drop_guard(self, target, **kwargs):
        self.pending_inlane_drops.discard(target)

    def _target_is_down(self, target):
        bank, number = target.split("_")
        down_set = self.left_down if bank == "left" else self.right_down
        return int(number) in down_set

    def total_drops_down(self):
        return len(self.left_down) + len(self.right_down)

    def spinner_value(self):
        drops_down = self.total_drops_down()
        if drops_down <= 0:
            return self.UNLIT_SPINNER_SCORE
        return self.spinner_per_drop * min(7, drops_down)

    def _update_level_lights(self):
        level = min(7, self.total_drops_down())
        self.machine.events.post(f"master_technician_level_{level}")
        self.machine.events.post(
            "master_technician_light_webs"
            if self.has_case_file("more_jackpots") and level > 0
            else "master_technician_clear_webs"
        )

    def _update_mode_status(self):
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=f"{max(0, self.seconds_left)}s  {self.total_drops_down()}/8 DOWN",
            mode_status_value=f"SPINNER {self.spinner_value():,}",
        )

    def _finish_mode(self):
        if self.mode_done:
            return
        self.mode_done = True
        self.seconds_left = 0
        self.delay.remove("master_technician_timer_tick")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("master_technician_time_expired")
        self.machine.events.post("master_technician_mode_complete")

    def _show_message(self, title, subtitle="", value="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            reminder=reminder,
        )

    def _show_jackpot(self, title, value):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle="MASTER TECHNICIAN",
            message_mode_value=value,
        )

    def _award_score(self, value):
        player = self.machine.game.player
        player["score"] += value
        player["active_mode_points"] += value
