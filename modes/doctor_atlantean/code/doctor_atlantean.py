from mpf.core.mode import Mode

from modes.common.case_file_mixin import CaseFileMixin


class DoctorAtlantean(CaseFileMixin, Mode):
    """Raise Manhattan by operating Doctor Atlantean's rooftop control panel."""

    MODE_KEY = "doctor_atlantean"
    DISPLAY_NAME = "Doctor Atlantean"

    MAX_WATER_LEVEL = 8
    STARTING_WATER_LEVEL = 6
    SINKING_ANIMATION_MS = 4_000
    NORMAL_TIMER_SECONDS = 20
    MORE_TIME_SECONDS = 30

    LIT_TARGET_SCORE = 100_000
    BIGGER_TARGET_SCORE = 125_000
    UNLIT_TARGET_SCORE = 25_000
    SPINNER_SCORE = 10_000
    MORE_JACKPOTS_SPINNER_SCORE = 100_000
    EXIT_SCORE = 25_000

    TARGETS = ("left", "center", "right")

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

        self.mode_done = False
        self.phase = "sinking"
        self.water_level = self.STARTING_WATER_LEVEL
        self.seconds_left = 0
        self.available_targets = set(self.TARGETS)
        self.control_panel_jackpots = 0
        self.spinner_spins = 0
        self.mode_points = 0
        self.spinner_jackpot_ready = False
        self.shot_assist_available = False

        self.case_files = self.get_case_file_bonuses()
        self.target_score = (
            self.BIGGER_TARGET_SCORE
            if self.has_case_file("bigger_jackpots")
            else self.LIT_TARGET_SCORE
        )
        self.timer_seconds = (
            self.MORE_TIME_SECONDS
            if self.has_case_file("more_time")
            else self.NORMAL_TIMER_SECONDS
        )
        self.shot_assist_available = self.has_case_file("shot_assist")

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars(update_status=False)

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "THREE TARGETS LIGHT A 100K SPINNER JACKPOT"),
            ("bigger_jackpots", "CONTROL PANEL JACKPOTS WORTH 125K"),
            ("more_time", "WATER TIMERS EXTENDED TO 30 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST UNLIT TARGET COUNTS AS LIT"),
        ])

        for target in self.TARGETS:
            self.add_mode_event_handler(
                f"doctor_atlantean_target_{target}_hit",
                self._target_hit,
                target=target,
            )
        self.add_mode_event_handler(
            "doctor_atlantean_upper_spinner_hit", self._spinner_hit
        )
        self.add_mode_event_handler(
            "doctor_atlantean_upper_exit_hit", self._upper_exit_hit
        )
        self.add_mode_event_handler(
            "doctor_atlantean_complete_request", self._complete_mode
        )
        self.add_mode_event_handler(
            "doctor_atlantean_fail_request", self._fail_mode
        )

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.machine.events.post("doctor_atlantean_water_base_orange")
        self.machine.events.post("doctor_atlantean_all_targets_off")
        self._show_message(
            "MANHATTAN SINKS",
            "WATER RISING",
            seconds="4",
            reminder=True,
        )
        self._start_sinking_animation()

    def mode_stop(self, **kwargs):
        self.delay.remove("doctor_atlantean_water_tick")
        for band in range(1, self.STARTING_WATER_LEVEL + 1):
            self.delay.remove(f"doctor_atlantean_sink_band_{band}")
        self.machine.events.post("doctor_atlantean_all_targets_off")
        self.machine.events.post("doctor_atlantean_water_restore")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _start_sinking_animation(self):
        interval = self.SINKING_ANIMATION_MS / self.STARTING_WATER_LEVEL
        for band in range(1, self.STARTING_WATER_LEVEL + 1):
            self.delay.add(
                name=f"doctor_atlantean_sink_band_{band}",
                ms=round(interval * band),
                callback=lambda band=band: self._sink_animation_band(band),
            )

    def _sink_animation_band(self, band):
        if self.mode_done or self.phase != "sinking":
            return
        self.machine.events.post(f"doctor_atlantean_water_band_{band}_blue")
        if band == self.STARTING_WATER_LEVEL:
            self._begin_play()

    def _begin_play(self):
        if self.mode_done or self.phase != "sinking":
            return
        self.phase = "active"
        self._light_all_targets()
        self._reset_water_timer()
        self._sync_vars()
        self._show_message(
            "OPERATE THE CONTROL PANEL",
            "PULSING GREEN TARGETS",
            reminder=True,
        )

    def _target_hit(self, target, **kwargs):
        if self.mode_done or self.phase != "active":
            return

        is_lit = target in self.available_targets
        assisted = False
        if not is_lit and self.shot_assist_available:
            self.shot_assist_available = False
            is_lit = True
            assisted = True
            self.machine.events.post(
                "doctor_atlantean_case_file_shot_assist_used", target=target
            )

        if is_lit:
            self._score(self.target_score)
            self.control_panel_jackpots += 1
            if not assisted:
                self.available_targets.remove(target)
                self.machine.events.post(
                    f"doctor_atlantean_target_{target}_collected"
                )

            self.machine.events.post(
                "doctor_atlantean_control_panel_jackpot",
                target=target,
                value=self.target_score,
                assisted=int(assisted),
            )
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="CONTROL PANEL JACKPOT",
                message_mode_subtitle="SHOT ASSIST" if assisted else "",
                message_mode_value=self.target_score,
                message_mode_seconds="",
            )
            self._set_water_level(self.water_level - 1)
            if self.mode_done:
                return

            if not self.available_targets:
                if self.has_case_file("more_jackpots"):
                    self.spinner_jackpot_ready = True
                    self.machine.events.post(
                        "doctor_atlantean_spinner_jackpot_ready"
                    )
                self._light_all_targets()
        else:
            self._score(self.UNLIT_TARGET_SCORE)
            self.machine.events.post(
                "doctor_atlantean_unlit_target_scored",
                target=target,
                value=self.UNLIT_TARGET_SCORE,
            )
            self._show_message(
                "CONTROL PANEL",
                "TARGET ALREADY USED",
                value=self.UNLIT_TARGET_SCORE,
            )

        self._reset_water_timer()
        self._sync_vars()

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.phase != "active":
            return

        self.spinner_spins += 1
        if self.spinner_jackpot_ready:
            value = self.MORE_JACKPOTS_SPINNER_SCORE
            self.spinner_jackpot_ready = False
            self._score(value)
            self.machine.events.post(
                "doctor_atlantean_spinner_jackpot_collected", value=value
            )
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="SPINNER JACKPOT",
                message_mode_subtitle="CONTROL PANEL COMPLETE",
                message_mode_value=value,
                message_mode_seconds="",
            )
        else:
            value = self.SPINNER_SCORE
            self._score(value)
            self.machine.events.post(
                "doctor_atlantean_spinner_scored", value=value
            )

        self._reset_water_timer()
        self._sync_vars()

    def _upper_exit_hit(self, **kwargs):
        if self.mode_done or self.phase != "active":
            return

        self._score(self.EXIT_SCORE)
        old_level = self.water_level
        self._set_water_level(self.water_level + 1)
        self.machine.events.post(
            "doctor_atlantean_upper_exit_scored",
            value=self.EXIT_SCORE,
            water_level=self.water_level,
        )

        # Entering maximum danger always starts a fresh full countdown. Other
        # exits do not count as the target/spinner activity that resets it.
        if old_level < self.MAX_WATER_LEVEL <= self.water_level:
            self._reset_water_timer()
        else:
            self._sync_vars()

    def _reset_water_timer(self):
        if self.mode_done or self.phase != "active":
            return
        self.seconds_left = self.timer_seconds
        self.delay.reset(
            name="doctor_atlantean_water_tick",
            ms=1000,
            callback=self._water_timer_tick,
        )
        self._update_status()

    def _water_timer_tick(self):
        if self.mode_done or self.phase != "active":
            return

        self.seconds_left -= 1
        if self.seconds_left <= 0:
            if self.water_level >= self.MAX_WATER_LEVEL:
                self._fail_mode()
                return
            self._set_water_level(self.water_level + 1)
            if self.mode_done:
                return
            self.seconds_left = self.timer_seconds

        self._update_status()
        self.delay.reset(
            name="doctor_atlantean_water_tick",
            ms=1000,
            callback=self._water_timer_tick,
        )

    def _set_water_level(self, level):
        level = max(0, min(self.MAX_WATER_LEVEL, int(level)))
        old_level = self.water_level
        if level == old_level:
            return

        if level > old_level:
            for band in range(old_level + 1, level + 1):
                self.machine.events.post(
                    f"doctor_atlantean_water_band_{band}_blue"
                )
        else:
            for band in range(old_level, level, -1):
                self.machine.events.post(
                    f"doctor_atlantean_water_band_{band}_orange"
                )

        self.water_level = level
        self.machine.events.post(
            "doctor_atlantean_water_level_changed",
            old_level=old_level,
            water_level=self.water_level,
        )
        self._sync_vars()

        if self.water_level <= 0:
            self._complete_mode()

    def _light_all_targets(self):
        self.available_targets = set(self.TARGETS)
        self.machine.events.post("doctor_atlantean_all_targets_off")
        for target in self.TARGETS:
            self.machine.events.post(f"doctor_atlantean_target_{target}_available")

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.phase = "done"
        self.delay.remove("doctor_atlantean_water_tick")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars(update_status=False)
        self.machine.events.post("doctor_atlantean_all_targets_off")
        self.machine.events.post("hide_mode_status")
        self._show_message("MANHATTAN RISES!", "DOCTOR ATLANTEAN DEFEATED")
        self.machine.events.post("doctor_atlantean_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.phase = "done"
        self.delay.remove("doctor_atlantean_water_tick")
        self._sync_vars(update_status=False)
        self.machine.events.post("doctor_atlantean_all_targets_off")
        self.machine.events.post("hide_mode_status")
        self._show_message("MANHATTAN IS LOST!", "CITY FULLY SUBMERGED")
        self.machine.events.post("doctor_atlantean_mode_complete")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _sync_vars(self, update_status=True):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.control_panel_jackpots
        player["active_mode_stat_2"] = self.spinner_spins
        player["doctor_atlantean_water_level"] = self.water_level
        if update_status and not self.mode_done and self.phase == "active":
            self._update_status()

    def _update_status(self):
        if self.mode_done or self.phase != "active":
            return
        if self.water_level >= self.MAX_WATER_LEVEL:
            title = "MANHATTAN SUBMERGED"
        else:
            title = f"WATER LEVEL {self.water_level} / {self.MAX_WATER_LEVEL}"
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=title,
            mode_status_value=f"TIME {self.seconds_left}",
        )

    def _show_message(
        self,
        title,
        subtitle="",
        value="",
        seconds="",
        reminder=False,
    ):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )
