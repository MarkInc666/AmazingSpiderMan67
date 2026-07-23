from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class DrMagneto(CaseFileMixin, Mode):
    """Dr. Magneto - magnetic sweep rooftop mode."""

    MODE_KEY = "dr_magneto"
    DISPLAY_NAME = "DR. MAGNETO"

    SPINNER_SCORE = 50_000
    DROP_SCORE = 50_000
    MAIN_SUPER_VALUE = 1_000_000
    BIGGER_MAIN_SUPER_VALUE = 1_500_000
    FLUX_SUPER_VALUE = 500_000
    MAIN_SECONDS = 20
    MORE_TIME_SECONDS = 30
    FLUX_SECONDS = 10
    BANK_SETTLE_MS = 500

    SWEEP_TARGETS = (
        "left_1",
        "left_2",
        "left_3",
        "right_1",
        "right_2",
        "right_3",
        "right_4",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.phase = "waiting_for_roof"
        self.sweep_index = 0
        self.spinner_hits = 0
        self.drops_knocked_down = 0
        self.mode_points = 0
        self.seconds_left = 0
        self.shot_assist_used = False
        self.main_super_collected = False
        self.flux_super_collected = False

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_summary_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "LEFT 1 MAGNETIC FLUX SUPER AFTER MAIN SUPER"),
            ("bigger_jackpots", "MAIN SUPER BOOSTED TO 1.5M"),
            ("more_time", "MAIN SUPER TIMER EXTENDED TO 30s"),
            ("safety_net", "BALL SAVE WHEN MAIN SUPER LIGHTS"),
            ("shot_assist", "FIRST SPIN DROPS TWO TARGETS"),
        ])

        self.add_mode_event_handler("dr_magneto_upper_entered", self._upper_entered)
        self.add_mode_event_handler("dr_magneto_upper_exited", self._upper_exited)
        self.add_mode_event_handler("dr_magneto_upper_spinner_hit", self._upper_spinner_hit)
        self.add_mode_event_handler("dr_magneto_right_drop_5_hit", self._right_drop_5_hit)
        self.add_mode_event_handler("dr_magneto_left_drop_1_hit", self._left_drop_1_hit)
        self.add_mode_event_handler("dr_magneto_complete_request", self._complete_mode)
        self.add_mode_event_handler("dr_magneto_fail_request", self._fail_mode)

        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("dr_magneto_build_gi")
        self._show_message("DR. MAGNETO", "GET TO THE ROOF", reminder=True)

    def mode_stop(self, **kwargs):
        self._clear_delays()
        self.machine.events.post("dr_magneto_stop_gi")
        self.machine.events.post("dr_magneto_clear_drop_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _upper_entered(self, **kwargs):
        if self._done_or_summary():
            return

        # Once a final shot is staged, preserve it even if the ball loops upstairs.
        if self.phase in ("main_ready", "flux_ready"):
            return

        self._clear_timer_delay()
        self.phase = "bank_resetting"
        self.sweep_index = 0
        self.machine.events.post("dr_magneto_reset_banks")
        self.machine.events.post("dr_magneto_clear_drop_lights")
        self.machine.events.post("dr_magneto_build_gi")
        self._show_message("MAGNETIC SWEEP", "SPIN TO DROP THE BANKS")
        self.delay.add(
            name="dr_magneto_bank_settle",
            ms=self.BANK_SETTLE_MS,
            callback=self._begin_sweep,
        )
        self._sync_summary_vars()

    def _begin_sweep(self):
        if self._done_or_summary() or self.phase != "bank_resetting":
            return
        self.phase = "sweep"
        self.machine.events.post("dr_magneto_sweep_started")
        self._sync_summary_vars()

    def _upper_exited(self, **kwargs):
        if self._done_or_summary():
            return

        if self.phase in ("bank_resetting", "sweep"):
            # The right-5 final target was not isolated yet. Reset and require another roof trip.
            self._clear_timer_delay()
            self.phase = "waiting_for_roof"
            self.sweep_index = 0
            self.machine.events.post("dr_magneto_reset_banks")
            self.machine.events.post("dr_magneto_clear_drop_lights")
            self.machine.events.post("dr_magneto_build_gi")
            self._show_message("MAGNETIC SWEEP LOST", "RETURN TO THE ROOF", reminder=True)
            self._sync_summary_vars()

    def _upper_spinner_hit(self, **kwargs):
        if self._done_or_summary() or self.phase != "sweep":
            return

        self.spinner_hits += 1
        self._score(self.SPINNER_SCORE)

        steps = 1
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            steps = 2
            self.machine.events.post("dr_magneto_shot_assist_used")

        for _ in range(steps):
            if self.sweep_index >= len(self.SWEEP_TARGETS):
                break
            target = self.SWEEP_TARGETS[self.sweep_index]
            self.sweep_index += 1
            self.drops_knocked_down += 1
            self._score(self.DROP_SCORE)
            self.machine.events.post(f"dr_magneto_drop_{target}")
            self.machine.events.post(
                "dr_magneto_sweep_advanced",
                sweep_index=self.sweep_index,
                target=target,
            )

        if self.sweep_index >= len(self.SWEEP_TARGETS):
            self._stage_main_super()
        else:
            self._show_message(
                "MAGNETIC SWEEP",
                f"{self.sweep_index} / {len(self.SWEEP_TARGETS)} TARGETS",
                value=self.mode_points,
            )
        self._sync_summary_vars()

    def _stage_main_super(self):
        if self._done_or_summary():
            return
        self.phase = "main_ready"
        self.seconds_left = self.MORE_TIME_SECONDS if self.has_case_file("more_time") else self.MAIN_SECONDS
        self.machine.events.post("dr_magneto_main_super_ready")
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")
        self._show_countdown("MAGNETO SUPER", self.seconds_left, "HIT RIGHT DROP 5")
        self._schedule_timer_tick()
        self._sync_summary_vars()

    def _right_drop_5_hit(self, **kwargs):
        if self._done_or_summary() or self.phase != "main_ready":
            return

        self._clear_timer_delay()
        value = self.BIGGER_MAIN_SUPER_VALUE if self.has_case_file("bigger_jackpots") else self.MAIN_SUPER_VALUE
        self.main_super_collected = True
        self._score(value)
        self.machine.events.post("dr_magneto_main_super_collected", value=value)
        self._show_jackpot("MAGNETO SUPER", value)

        if self.has_case_file("more_jackpots"):
            self._prepare_flux_super()
        else:
            self._complete_mode()

    def _prepare_flux_super(self):
        self.phase = "flux_staging"
        self.seconds_left = 0
        self.machine.events.post("dr_magneto_reset_left_bank")
        self.machine.events.post("dr_magneto_clear_drop_lights")
        self.delay.add(
            name="dr_magneto_flux_stage",
            ms=self.BANK_SETTLE_MS,
            callback=self._stage_flux_super,
        )
        self._sync_summary_vars()

    def _stage_flux_super(self):
        if self._done_or_summary() or self.phase != "flux_staging":
            return
        self.machine.events.post("dr_magneto_drop_left_2")
        self.machine.events.post("dr_magneto_drop_left_3")
        self.phase = "flux_ready"
        self.seconds_left = self.FLUX_SECONDS
        self.machine.events.post("dr_magneto_flux_super_ready")
        self._show_countdown("MAGNETIC FLUX SUPER", self.seconds_left, "HIT LEFT DROP 1")
        self._schedule_timer_tick()
        self._sync_summary_vars()

    def _left_drop_1_hit(self, **kwargs):
        if self._done_or_summary() or self.phase != "flux_ready":
            return

        self._clear_timer_delay()
        self.flux_super_collected = True
        self._score(self.FLUX_SUPER_VALUE)
        self.machine.events.post("dr_magneto_flux_super_collected", value=self.FLUX_SUPER_VALUE)
        self._show_jackpot("MAGNETIC FLUX SUPER", self.FLUX_SUPER_VALUE)
        self._complete_mode()

    def _schedule_timer_tick(self):
        self.delay.add(
            name="dr_magneto_timer_tick",
            ms=1000,
            callback=self._timer_tick,
        )

    def _timer_tick(self):
        if self._done_or_summary() or self.phase not in ("main_ready", "flux_ready"):
            return
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            expired_phase = self.phase
            self.seconds_left = 0
            self.machine.events.post("dr_magneto_final_shot_expired", phase=expired_phase)
            self._show_message("DR. MAGNETO", "SUPER JACKPOT EXPIRED")
            self._fail_mode()
            return

        if self.phase == "main_ready":
            self._show_countdown("MAGNETO SUPER", self.seconds_left, "HIT RIGHT DROP 5")
        else:
            self._show_countdown("MAGNETIC FLUX SUPER", self.seconds_left, "HIT LEFT DROP 1")
        self._schedule_timer_tick()
        self._sync_summary_vars()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("dr_magneto_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("dr_magneto_mode_complete")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_summary_vars()

    def _sync_summary_vars(self):
        """Expose only the shared summary values needed outside this mode.

        Sweep progress, phase, countdown, helper use, and collected-shot flags are
        temporary mode state and intentionally remain Python attributes.
        """
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.spinner_hits
        player["active_mode_major_hits"] = (
            int(self.main_super_collected) + int(self.flux_super_collected)
        )

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

    def _show_jackpot(self, title, value):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle="",
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _clear_timer_delay(self):
        self.delay.remove("dr_magneto_timer_tick")

    def _clear_delays(self):
        self.delay.remove("dr_magneto_bank_settle")
        self.delay.remove("dr_magneto_flux_stage")
        self.delay.remove("dr_magneto_timer_tick")

    def _done_or_summary(self):
        return self.mode_done or not self.machine.game or not self.machine.game.player
