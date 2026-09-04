from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Skymaster(CaseFileMixin, Mode):
    """Skymaster - force the eight lower drops down in order."""

    MODE_KEY = "skymaster"
    DISPLAY_NAME = "SKYMASTER"

    DROP_SCORE = 100_000
    BIGGER_DROP_SCORE = 150_000
    SUPER_VALUE = 500_000
    BIGGER_SUPER_VALUE = 750_000
    SUPER_SECONDS = 20
    MORE_TIME_SUPER_SECONDS = 25

    # Drop-bank reset events have a 100ms device delay in config/devices.yaml.
    # Waiting 300ms here leaves approximately 200ms after the physical reset
    # pulse before the first restored target is knocked down.
    RESET_SETTLE_MS = 300
    REDROP_STEP_MS = 200
    SPINNER_DROP_STEP_MS = 200
    PROGRAMMATIC_DROP_GUARD_MS = 1_500

    TARGETS = (
        "left_1", "left_2", "left_3",
        "right_1", "right_2", "right_3", "right_4", "right_5",
    )

    TARGET_LABELS = {
        "left_1": "LEFT 1", "left_2": "LEFT 2", "left_3": "LEFT 3",
        "right_1": "RIGHT 1", "right_2": "RIGHT 2", "right_3": "RIGHT 3",
        "right_4": "RIGHT 4", "right_5": "RIGHT 5",
    }

    TARGET_COILS = {
        "left_1": "c_left_bank_drop_1",
        "left_2": "c_left_bank_drop_2",
        "left_3": "c_left_bank_drop_3",
        "right_1": "c_right_bank_drop_1",
        "right_2": "c_right_bank_drop_2",
        "right_3": "c_right_bank_drop_3",
        "right_4": "c_right_bank_drop_4",
        "right_5": "c_right_bank_drop_5",
    }

    TARGET_BANKS = {
        "left_1": "left", "left_2": "left", "left_3": "left",
        "right_1": "right", "right_2": "right", "right_3": "right",
        "right_4": "right", "right_5": "right",
    }

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
        self.mode_done = False
        self.phase = "starting_reset"
        self.progress = 0
        self.mode_points = 0
        self.seconds_left = 0
        self.spinner_hits = 0
        self.spinner_steps_pending = 0
        self.shot_assist_used = False
        self.programmatic_drops_pending = set()
        self.restage_targets = []
        self.web_jackpots_collected = set()
        self.skymaster_defeated = False

        self.drop_score = (
            self.BIGGER_DROP_SCORE
            if self.has_case_file("bigger_jackpots")
            else self.DROP_SCORE
        )
        self.super_value = (
            self.BIGGER_SUPER_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.SUPER_VALUE
        )
        self.super_seconds = (
            self.MORE_TIME_SUPER_SECONDS
            if self.has_case_file("more_time")
            else self.SUPER_SECONDS
        )

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        player["skymaster_defeated"] = 0
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "LEFT WEB ADDS A SECOND SUPER"),
            ("bigger_jackpots", "DROPS 150K - WEB SUPERS 750K"),
            ("more_time", "WEB SUPER WINDOW EXTENDED TO 25s"),
            ("safety_net", "10 SECOND OPENING BALL SAVE"),
            ("shot_assist", "FIRST UPPER SPIN DROPS TWO TARGETS"),
        ])

        self.add_mode_event_handler("skymaster_upper_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("skymaster_drop_hit", self._drop_target_hit)
        self.add_mode_event_handler("skymaster_center_web_hit", self._center_web_hit)
        self.add_mode_event_handler("skymaster_left_web_hit", self._left_web_hit)
        self.add_mode_event_handler("skymaster_complete_request", self._complete_mode)
        self.add_mode_event_handler("skymaster_fail_request", self._fail_mode)

        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("skymaster_reset_left_bank")
        self.machine.events.post("skymaster_reset_right_bank")
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self._show_message(
            "DROP TARGETS IN ORDER",
            "UPPER SPINNER OR CORRECT TARGET",
            value="0 / 8",
            reminder=True,
        )
        self.delay.add(
            name="skymaster_starting_reset",
            ms=self.RESET_SETTLE_MS,
            callback=self._finish_starting_reset,
        )

    def mode_stop(self, **kwargs):
        self._clear_delays()
        self.machine.events.post("skymaster_clear_lights")
        self.machine.events.post("skymaster_reset_left_bank")
        self.machine.events.post("skymaster_reset_right_bank")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _finish_starting_reset(self, **kwargs):
        if self._done_or_summary() or self.phase != "starting_reset":
            return
        self.phase = "sequence"
        # The upper spinner can advance every ordered target, so rooftop access
        # remains open for the complete sequence phase.
        self.machine.events.post("skymaster_sequence_started")
        self._light_expected_target()

    def _spinner_hit(self, **kwargs):
        if self._done_or_summary() or self.phase not in ("sequence", "spinner_drop"):
            return

        self.spinner_hits += 1
        steps = 1
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            steps = 2
            self.machine.events.post("skymaster_shot_assist_used")

        self.spinner_steps_pending += steps
        self._process_spinner_steps()

    def _process_spinner_steps(self, **kwargs):
        if self._done_or_summary() or self.phase != "sequence":
            return
        if self.spinner_steps_pending <= 0 or self.progress >= len(self.TARGETS):
            return

        self.phase = "spinner_drop"
        self.spinner_steps_pending -= 1
        self._advance_sequence(source="spinner", programmatic=True)

        if self.phase == "super" or self.mode_done:
            self.spinner_steps_pending = 0
            return

        self.delay.reset(
            name="skymaster_spinner_drop_step",
            ms=self.SPINNER_DROP_STEP_MS,
            callback=self._finish_spinner_step,
        )

    def _finish_spinner_step(self, **kwargs):
        if self._done_or_summary() or self.phase != "spinner_drop":
            return
        self.phase = "sequence"
        self._process_spinner_steps()

    def _drop_target_hit(self, target=None, **kwargs):
        if self._done_or_summary() or target not in self.TARGETS:
            return

        if target in self.programmatic_drops_pending:
            self.programmatic_drops_pending.discard(target)
            self.delay.remove(f"skymaster_programmatic_drop_{target}")
            self.machine.events.post("skymaster_programmatic_drop_ignored", target=target)
            return

        if self.phase not in ("sequence", "spinner_drop"):
            return

        if target == self._expected_target():
            self._advance_sequence(source="direct", programmatic=False)
            return

        self._handle_wrong_target(target)

    def _advance_sequence(self, source, programmatic=False):
        target = self._expected_target()
        if not target:
            return

        self.progress += 1
        self._score(self.drop_score)
        if programmatic:
            self._drop_programmatically(target)

        self.machine.events.post(
            "skymaster_correct_drop",
            target=target,
            target_label=self.TARGET_LABELS[target],
            progress=self.progress,
            source=source,
            value=self.drop_score,
        )
        self._sync_vars()

        if self.progress >= len(self.TARGETS):
            self._start_super_round()
            return

        self._show_message(
            "TARGET IN ORDER",
            f"NEXT: {self.TARGET_LABELS[self._expected_target()]}",
            value=f"{self.progress} / {len(self.TARGETS)}",
        )
        self._light_expected_target()

    def _handle_wrong_target(self, target):
        bank = self.TARGET_BANKS[target]
        self.phase = "bank_resetting"
        self.restage_targets = [
            completed
            for completed in self.TARGETS[:self.progress]
            if self.TARGET_BANKS[completed] == bank
        ]
        self.delay.remove("skymaster_spinner_drop_step")
        self.machine.events.post("skymaster_wrong_drop", target=target, bank=bank)
        self.machine.events.post("skymaster_clear_target_lights")
        self.machine.events.post(f"skymaster_reset_{bank}_bank")
        self._show_message(
            "WRONG TARGET",
            f"RESETTING {bank.upper()} BANK",
            value=f"{self.progress} / {len(self.TARGETS)}",
        )
        self.delay.reset(
            name="skymaster_bank_reset_settle",
            ms=self.RESET_SETTLE_MS,
            callback=self._redrop_next_completed_target,
        )

    def _redrop_next_completed_target(self, **kwargs):
        if self._done_or_summary() or self.phase not in ("bank_resetting", "bank_restaging"):
            return

        if not self.restage_targets:
            self.phase = "sequence"
            self._light_expected_target()
            self._show_message(
                "ORDER RESTORED",
                f"NEXT: {self.TARGET_LABELS[self._expected_target()]}",
                value=f"{self.progress} / {len(self.TARGETS)}",
            )
            self._process_spinner_steps()
            return

        self.phase = "bank_restaging"
        target = self.restage_targets.pop(0)
        self._drop_programmatically(target)
        self.machine.events.post("skymaster_completed_target_restaged", target=target)
        self.delay.reset(
            name="skymaster_bank_redrop_step",
            ms=self.REDROP_STEP_MS,
            callback=self._redrop_next_completed_target,
        )

    def _drop_programmatically(self, target):
        self.programmatic_drops_pending.add(target)
        self.delay.reset(
            name=f"skymaster_programmatic_drop_{target}",
            ms=self.PROGRAMMATIC_DROP_GUARD_MS,
            callback=self._clear_programmatic_drop_pending,
            target=target,
        )
        self.machine.coils[self.TARGET_COILS[target]].pulse()

    def _clear_programmatic_drop_pending(self, target=None, **kwargs):
        if target:
            self.programmatic_drops_pending.discard(target)

    def _start_super_round(self):
        self.phase = "super"
        self.spinner_steps_pending = 0
        self.seconds_left = self.super_seconds
        self.machine.events.post(
            "skymaster_super_ready", seconds=self.seconds_left, value=self.super_value
        )
        if self.has_case_file("more_jackpots"):
            self.machine.events.post("skymaster_left_super_ready")
        self._show_super_status()
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="SECONDS LEFT",
            mode_status_value=self.seconds_left,
        )
        self._schedule_super_tick()

    def _center_web_hit(self, **kwargs):
        self._collect_web_jackpot("center")

    def _left_web_hit(self, **kwargs):
        if self.has_case_file("more_jackpots"):
            self._collect_web_jackpot("left")

    def _collect_web_jackpot(self, web):
        if self._done_or_summary() or self.phase != "super":
            return
        if web in self.web_jackpots_collected:
            return

        self.web_jackpots_collected.add(web)
        if web == "center":
            self.skymaster_defeated = True
            self.machine.game.player["skymaster_defeated"] = 1

        self._score(self.super_value)
        self.machine.events.post(
            f"skymaster_{web}_super_collected", web=web, value=self.super_value
        )
        self._show_jackpot("SKYMASTER SUPER", self.super_value, f"{web.upper()} WEB")
        self.machine.events.post("play_mode_super_jackpot")
        self._sync_vars()

        required = {"center"}
        if self.has_case_file("more_jackpots"):
            required.add("left")
        if required.issubset(self.web_jackpots_collected):
            self._complete_mode()
        else:
            self._show_super_status()

    def _show_super_status(self):
        if self.skymaster_defeated and "left" not in self.web_jackpots_collected:
            subtitle = "LEFT WEB EXTRA SUPER"
        elif "left" in self.web_jackpots_collected:
            subtitle = "CENTER WEB DEFEATS SKYMASTER"
        elif self.has_case_file("more_jackpots"):
            subtitle = "CENTER + LEFT WEB"
        else:
            subtitle = "CENTER WEB"
        self._show_countdown("SUPER JACKPOT", self.seconds_left, subtitle)

    def _schedule_super_tick(self):
        self.delay.reset(
            name="skymaster_super_tick", ms=1000, callback=self._super_tick
        )

    def _super_tick(self, **kwargs):
        if self._done_or_summary() or self.phase != "super":
            return
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self.seconds_left = 0
            self.machine.events.post("skymaster_super_expired")
            if self.skymaster_defeated:
                self._complete_mode()
            else:
                self._fail_mode()
            return
        self.machine.events.post(
            "update_mode_status",
            mode_status_title="SECONDS LEFT",
            mode_status_value=self.seconds_left,
        )
        self._schedule_super_tick()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.game.player["skymaster_defeated"] = 1
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("skymaster_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        self.machine.game.player["skymaster_defeated"] = 0
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("skymaster_mode_complete")

    def _expected_target(self):
        if self.progress >= len(self.TARGETS):
            return None
        return self.TARGETS[self.progress]

    def _light_expected_target(self):
        target = self._expected_target()
        self.machine.events.post("skymaster_clear_target_lights")
        if target:
            self.machine.events.post(f"skymaster_expected_{target}")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.progress
        player["active_mode_stat_2"] = len(self.web_jackpots_collected)

    def _done_or_summary(self):
        player = self.machine.game.player if self.machine.game else None
        return self.mode_done or bool(player and player["villain_mode_in_summary"])

    def _clear_delays(self):
        for name in (
            "skymaster_starting_reset",
            "skymaster_spinner_drop_step",
            "skymaster_bank_reset_settle",
            "skymaster_bank_redrop_step",
            "skymaster_super_tick",
        ):
            self.delay.remove(name)
        for target in self.TARGETS:
            self.delay.remove(f"skymaster_programmatic_drop_{target}")

    def _show_message(self, title, subtitle="", value="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
            reminder=reminder,
        )

    def _show_countdown(self, title, seconds, subtitle=""):
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value="",
            message_mode_seconds=seconds,
        )

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )
