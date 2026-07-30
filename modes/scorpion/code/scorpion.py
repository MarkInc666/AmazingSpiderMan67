import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Scorpion(CaseFileMixin, Mode):
    """Scorpion: build Venom, choose an exit, then hit one staged drop."""
    VENOM_READY_HITS = 2
    BASE_MAX_ATTEMPTS = 3
    BASE_STING_SECONDS = 8
    MORE_TIME_STING_SECONDS = 12
    SPINNER_SCORE = 50_000
    FULL_AWARDS = (250_000, 500_000, 1_000_000, 1_500_000)
    PARTIAL_AWARDS = (200_000, 300_000, 400_000, 500_000)

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()
        self.max_attempts = (
            self.BASE_MAX_ATTEMPTS + 1
            if self.has_case_file("more_jackpots")
            else self.BASE_MAX_ATTEMPTS
        )
        self.sting_seconds = (
            self.MORE_TIME_STING_SECONDS
            if self.has_case_file("more_time")
            else self.BASE_STING_SECONDS
        )
        self.bigger_multiplier = 1.5 if self.has_case_file("bigger_jackpots") else 1.0
        self.shot_assist_available = self.has_case_file("shot_assist")
        self.venom_hits = 0
        self.attempts_used = 0
        self.state = "build"
        self.mode_done = False
        self.scoring_enabled = True
        self.active_target_side = None
        self.required_target = None
        self.seconds_left = 0
        self.rubber_enabled = False

        self.scorpion_stings = 0
        self.scorpion_biggest_jackpot = 0
        self.active_mode_points = 0
        self._sync_player_vars()
        self.publish_case_file_bonus_events("scorpion")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA STING ATTEMPT AVAILABLE"),
            ("bigger_jackpots", "STING AWARDS BOOSTED"),
            ("more_time", "12 SECOND STING WINDOW"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST RUBBER COUNTS AS TARGET"),
        ])
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.add_mode_event_handler("scorpion_spinner_hit", self.spinner_hit)
        self.add_mode_event_handler("scorpion_right_exit_chosen", self.right_exit_chosen)
        self.add_mode_event_handler("scorpion_left_exit_chosen", self.left_exit_chosen)
        for i in range(1, 4):
            self.add_mode_event_handler(
                f"scorpion_left_drop_{i}_hit", self.left_drop_hit, target=i
            )
        for i in range(1, 6):
            self.add_mode_event_handler(
                f"scorpion_right_drop_{i}_hit", self.right_drop_hit, target=i
            )

        self.add_mode_event_handler("s_left_drops_rubber_active", self.sting_rubber_left)
        self.add_mode_event_handler("s_right_drops_rubber_active", self.sting_rubber_right)
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="BUILD VENOM",
            message_mode_subtitle="HIT THE ROOF SPINNER",
            reminder=True,
        )
        self._update_mode_status()

    def mode_stop(self, **kwargs):
        for name in (
            "scorpion_prepare_left_bank_after_reset",
            "scorpion_prepare_right_bank_after_reset",
            "scorpion_enable_rubber",
            "scorpion_sting_tick",
            "scorpion_complete_hold",
        ):
            self.delay.remove(name)
        self.rubber_enabled = False
        self.machine.events.post("scorpion_sting_lights_off")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _sync_player_vars(self):
        player = self.machine.game.player
        player["scorpion_stings"] = self.scorpion_stings
        player["scorpion_biggest_jackpot"] = self.scorpion_biggest_jackpot
        player["active_mode_points"] = self.active_mode_points

    def _add_score(self, value):
        if not self.scoring_enabled or value <= 0:
            return
        player = self.machine.game.player
        player["score"] += value
        self.active_mode_points += value
        player["active_mode_points"] = self.active_mode_points

    def _update_mode_status(self):
        if self.mode_done:
            return
        if self.state == "build":
            title = "VENOM"
            value = f"{self.venom_hits}/{self.VENOM_READY_HITS}"
        elif self.state == "ready":
            title = "STING READY"
            value = "CHOOSE UPPER EXIT"
        elif self.state == "sting":
            title = f"ATTEMPT {self.attempts_used + 1} OF {self.max_attempts}"
            value = f"TIME: {self.seconds_left}"
        else:
            return
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def spinner_hit(self, **kwargs):
        if self.mode_done or not self.scoring_enabled:
            return

        self._add_score(self.SPINNER_SCORE)
        if self.state != "build":
            return
        self.venom_hits = min(self.VENOM_READY_HITS, self.venom_hits + 1)
        self.machine.events.post("scorpion_spinner_build")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="VENOM BUILDS",
            message_mode_subtitle=f"{self.venom_hits}/{self.VENOM_READY_HITS}",
            message_mode_value=self.SPINNER_SCORE,
        )
        if self.venom_hits >= self.VENOM_READY_HITS:
            self.state = "ready"
            self.machine.events.post("scorpion_sting_ready")
            self.machine.events.post(
                "show_mode_message_long",
                message_mode_title="STING READY",
                message_mode_subtitle="CHOOSE LEFT OR RIGHT EXIT",
            )
        self._update_mode_status()

    def right_exit_chosen(self, **kwargs):
        # Right upper exit stages the left drop bank.
        self._start_sting(side="left")

    def left_exit_chosen(self, **kwargs):
        # Left upper exit stages the right drop bank.
        self._start_sting(side="right")

    def _start_sting(self, side):
        if self.mode_done or not self.scoring_enabled or self.state != "ready":
            return
        self.machine.events.post("scorpion_sting_lights_off")
        self.state = "sting"
        self.active_target_side = side
        self.seconds_left = self.sting_seconds

        # Ignore mechanical vibration/bounce while the selected bank resets
        # and the non-required drops are knocked down.
        self.rubber_enabled = False

        if side == "left":
            self.required_target = random.randint(1, 3)
            self.machine.coils["c_left_bank_reset"].pulse()
            self.delay.reset(
                name="scorpion_prepare_left_bank_after_reset",
                ms=400,
                callback=self.prepare_left_bank_after_reset,
            )
            self.machine.events.post("scorpion_safe_sting_started")
        else:
            self.required_target = random.randint(1, 5)
            self.machine.coils["c_right_bank_reset"].pulse()
            self.delay.reset(
                name="scorpion_prepare_right_bank_after_reset",
                ms=400,
                callback=self.prepare_right_bank_after_reset,
            )
            self.machine.events.post("scorpion_hard_sting_started")

        self.delay.reset(
            name="scorpion_enable_rubber",
            ms=1000,
            callback=self._enable_rubber,
        )

        self._update_mode_status()
        self.delay.reset(
            name="scorpion_sting_tick",
            ms=1000,
            callback=self._sting_tick,
        )

    def _enable_rubber(self):
        if self.mode_done or self.state != "sting":
            return
        self.rubber_enabled = True

    def _sting_tick(self):
        if self.mode_done or self.state != "sting":
            return
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self._resolve_attempt(result="timeout")
            return
        self._update_mode_status()
        self.delay.reset(
            name="scorpion_sting_tick",
            ms=1000,
            callback=self._sting_tick,
        )

    def prepare_left_bank_after_reset(self):
        if self.mode_done or self.state != "sting" or self.active_target_side != "left":
            return
        for i in range(1, 4):
            if i != self.required_target:
                self.machine.coils[f"c_left_bank_drop_{i}"].pulse()
        self.machine.events.post("scorpion_left_sting_target_lit")

    def prepare_right_bank_after_reset(self):
        if self.mode_done or self.state != "sting" or self.active_target_side != "right":
            return
        for i in range(1, 6):
            if i != self.required_target:
                self.machine.coils[f"c_right_bank_drop_{i}"].pulse()
        self.machine.events.post(
            f"scorpion_right_sting_target_{self.required_target}_lit"
        )

    def left_drop_hit(self, target, **kwargs):
        if (
            not self.mode_done
            and self.state == "sting"
            and self.active_target_side == "left"
            and target == self.required_target
        ):
            self._resolve_attempt(result="target")

    def right_drop_hit(self, target, **kwargs):
        if (
            not self.mode_done
            and self.state == "sting"
            and self.active_target_side == "right"
            and target == self.required_target
        ):
            self._resolve_attempt(result="target")

    def sting_rubber_left(self, **kwargs):
        if (
            self.rubber_enabled
            and self.state == "sting"
            and self.active_target_side == "left"
        ):
            self._resolve_rubber()

    def sting_rubber_right(self, **kwargs):
        if (
            self.rubber_enabled
            and self.state == "sting"
            and self.active_target_side == "right"
        ):
            self._resolve_rubber()

    def _resolve_rubber(self):
        if self.shot_assist_available and self.attempts_used == 0:
            self.shot_assist_available = False
            self._resolve_attempt(result="target")
        else:
            self._resolve_attempt(result="rubber")

    def _award_for_attempt(self, values):
        index = min(self.attempts_used, len(values) - 1)
        return int(values[index] * self.bigger_multiplier)

    def _resolve_attempt(self, result):
        if self.mode_done or self.state != "sting":
            return

        self.rubber_enabled = False
        self.delay.remove("scorpion_enable_rubber")
        self.state = "awarding"
        self.delay.remove("scorpion_sting_tick")
        self.machine.events.post("scorpion_sting_lights_off")
        if result == "target":
            value = self._award_for_attempt(self.FULL_AWARDS)
            self._add_score(value)
            self.scorpion_stings += 1
            self.scorpion_biggest_jackpot = max(self.scorpion_biggest_jackpot, value)
            self._sync_player_vars()
            self.machine.events.post("scorpion_sting_success")
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="SCORPION STING",
                message_mode_value=value,
            )
        elif result == "rubber":
            value = self._award_for_attempt(self.PARTIAL_AWARDS)
            self._add_score(value)
            self.machine.events.post("scorpion_sting_miss")
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="PARTIAL STING",
                message_mode_value=value,
            )
        else:
            self.machine.events.post("scorpion_sting_failed")
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="STING MISSED",
            )
        self.attempts_used += 1
        self.venom_hits = 0
        self.active_target_side = None
        self.required_target = None
        self.seconds_left = 0

        if self.attempts_used >= self.max_attempts:
            self._begin_completion_hold()
            return
        self.state = "build"
        self.machine.events.post("scorpion_build_phase_started")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="BUILD VENOM",
            message_mode_subtitle="HIT THE ROOF SPINNER",
            reminder=True,
        )
        self._update_mode_status()

    def _begin_completion_hold(self):
        if self.mode_done:
            return
        self.mode_done = True
        self.state = "complete_hold"
        self.scoring_enabled = False
        self.rubber_enabled = False
        self.delay.remove("scorpion_enable_rubber")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("scorpion_sting_lights_off")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="SCORPION DEFEATED!",
        )
        self.delay.reset(
            name="scorpion_complete_hold",
            ms=2000,
            callback=self._finish_completion,
        )

    def _finish_completion(self):
        if not self.mode_done:
            return
        self.machine.events.post("scorpion_mode_complete")
