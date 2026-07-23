from mpf.core.mode import Mode


class Base(Mode):
    """Base-mode helpers for temporary messages and persistent mode status.

    Temporary mode messages use message_mode_* player vars and are meant for
    short callouts. Persistent mode status uses mode_status_* player vars and
    stays visible while a mode needs a live counter, such as remaining flips or
    seconds left.
    """

    MESSAGE_EVENTS = (
        "show_mode_message",
        "show_mode_message_long",
        "show_mode_jackpot",
    )

    COUNTDOWN_DELAY_NAME = "mode_message_countdown_tick"
    REMINDER_DELAY_NAME = "mode_message_reminder"
    REMINDER_INTERVAL_MS = 9000

    MODE_DISPLAY_CLEAR_EVENTS = (
        "mode_antarcticans_stopping",
        "mode_brutus_stopping",
        "mode_centaur_stopping",
        "mode_cerberus_stopping",
        "mode_chapter_select_stopping",
        "mode_charles_cameo_stopping",
        "mode_cyclops_stopping",
        "mode_diamond_smugglers_stopping",
        "mode_diana_stopping",
        "mode_doc_ock_stopping",
        "mode_doctor_atlantean_stopping",
        "mode_doctor_cool_stopping",
        "mode_doctor_dumpty_stopping",
        "mode_dr_magneto_stopping",
        "mode_dr_manta_stopping",
        "mode_dr_von_schlick_stopping",
        "mode_dr_zap_stopping",
        "mode_eigor_stopping",
        "mode_electro_stopping",
        "mode_enforcers_stopping",
        "mode_fakir_stopping",
        "mode_fifth_avenue_phantom_stopping",
        "mode_fifth_dimension_curse_stopping",
        "mode_final_showdown_stopping",
        "mode_goblin_stopping",
        "mode_grand_emperor_stopping",
        "mode_human_flies_stopping",
        "mode_ice_monster_stopping",
        "mode_infinata_stopping",
        "mode_invasion_from_everywhere_stopping",
        "mode_kingpin_stopping",
        "mode_lizard_stopping",
        "mode_mad_science_meltdown_stopping",
        "mode_master_plan_stopping",
        "mode_master_technician_stopping",
        "mode_master_vine_stopping",
        "mode_mastermind_trap_stopping",
        "mode_micro_men_stopping",
        "mode_monster_island_breakout_stopping",
        "mode_mysterio_stopping",
        "mode_nature_strikes_back_stopping",
        "mode_noah_boddy_stopping",
        "mode_parafino_stopping",
        "mode_pardo_stopping",
        "mode_phantom_from_depths_of_time_stopping",
        "mode_plutonians_stopping",
        "mode_pod_stopping",
        "mode_professor_pretoris_stopping",
        "mode_radiation_specialist_stopping",
        "mode_rhino_stopping",
        "mode_sandman_stopping",
        "mode_scarlet_sorcerer_stopping",
        "mode_scorpion_stopping",
        "mode_sinister_surge_stopping",
        "mode_sky_master_stopping",
        "mode_snowman_stopping",
        "mode_super_swami_stopping",
        "mode_swamp_reptiles_stopping",
        "mode_the_fly_stopping",
        "mode_time_tossed_showdown_stopping",
        "mode_trubble_unleashed_stopping",
        "mode_vulcan_stopping",
        "mode_vulture_stopping",
        "mode_who_is_the_real_villain_stopping",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        for event in self.MESSAGE_EVENTS:
            self.add_mode_event_handler(event, self._sync_mode_message_vars, priority=10000)
        self.add_mode_event_handler("show_mode_countdown", self._sync_mode_countdown_vars, priority=10000)
        self.add_mode_event_handler("hide_mode_message", self._hide_mode_message, priority=10000)
        self.add_mode_event_handler("reset_mode_message_reminder", self._reset_mode_message_reminder, priority=10000)
        self.add_mode_event_handler("cancel_mode_message_reminder", self._cancel_mode_message_reminder, priority=10000)

        self.add_mode_event_handler("show_mode_status", self._sync_mode_status_vars, priority=10000)
        self.add_mode_event_handler("update_mode_status", self._sync_mode_status_vars, priority=10000)
        self.add_mode_event_handler("hide_mode_status", self._hide_mode_status, priority=10000)
        self.add_mode_event_handler("clear_mode_display_context", self._clear_mode_display_context, priority=10000)

        for stop_event in self.MODE_DISPLAY_CLEAR_EVENTS:
            self.add_mode_event_handler(stop_event, self._clear_mode_display_context, priority=10000)

        self._clear_mode_message_vars()
        self._clear_mode_status_vars()

    def _sync_mode_message_vars(
        self,
        message_mode_title="",
        message_mode_subtitle="",
        message_mode_value="",
        message_mode_seconds="",
        reminder=False,
        **kwargs,
    ):
        self._set_mode_message_vars(
            message_mode_title=message_mode_title,
            message_mode_subtitle=message_mode_subtitle,
            message_mode_value=message_mode_value,
            message_mode_seconds=message_mode_seconds,
        )
        if reminder:
            self._reminder_payload = dict(
                message_mode_title=message_mode_title,
                message_mode_subtitle=message_mode_subtitle,
                message_mode_value=message_mode_value,
                message_mode_seconds=message_mode_seconds,
            )
            self._schedule_mode_message_reminder()
        elif getattr(self, "_reminder_payload", None):
            # A temporary jackpot/completion message pauses the objective reminder.
            # Restart the inactivity interval so the objective returns after the
            # temporary message has had time to be read.
            self._schedule_mode_message_reminder()
        else:
            self.delay.remove(self.REMINDER_DELAY_NAME)

    def _sync_mode_countdown_vars(
        self,
        message_mode_title="",
        message_mode_subtitle="",
        message_mode_value="",
        message_mode_seconds="",
        mode_status_title="SECONDS LEFT",
        mode_status_value="",
        **kwargs,
    ):
        self._set_mode_message_vars(
            message_mode_title=message_mode_title,
            message_mode_subtitle=message_mode_subtitle,
            message_mode_value=message_mode_value,
            message_mode_seconds="",
        )

        seconds = self._parse_seconds(message_mode_seconds)
        if seconds is None or seconds <= 0:
            self._cancel_countdown()
            return

        self._message_countdown_remaining = seconds
        self._message_countdown_status_title = self._display_text(mode_status_title or "SECONDS LEFT")
        status_value = mode_status_value if mode_status_value not in (None, "") else seconds
        self._set_mode_status_vars(
            mode_status_title=self._message_countdown_status_title,
            mode_status_value=status_value,
        )
        self.machine.events.post("show_mode_status")
        self._schedule_countdown_tick()

    def _set_mode_message_vars(
        self,
        message_mode_title="",
        message_mode_subtitle="",
        message_mode_value="",
        message_mode_seconds="",
    ):
        player = self.machine.game.player
        player["message_mode_title"] = self._display_text(message_mode_title)
        player["message_mode_subtitle"] = self._display_text(message_mode_subtitle)
        player["message_mode_value"] = self._display_text(message_mode_value)
        player["message_mode_seconds"] = self._display_text(message_mode_seconds)

    def _sync_mode_status_vars(
        self,
        mode_status_title="",
        mode_status_value="",
        **kwargs,
    ):
        self._set_mode_status_vars(
            mode_status_title=mode_status_title,
            mode_status_value=mode_status_value,
        )

    def _set_mode_status_vars(
        self,
        mode_status_title="",
        mode_status_value="",
    ):
        player = self.machine.game.player
        player["mode_status_title"] = self._display_text(mode_status_title)
        player["mode_status_value"] = self._display_text(mode_status_value)

    def _schedule_countdown_tick(self):
        self.delay.remove(self.COUNTDOWN_DELAY_NAME)
        self.delay.add(
            name=self.COUNTDOWN_DELAY_NAME,
            ms=1000,
            callback=self._mode_message_countdown_tick,
        )

    def _mode_message_countdown_tick(self):
        remaining = getattr(self, "_message_countdown_remaining", 0)
        remaining = max(0, int(remaining) - 1)
        self._message_countdown_remaining = remaining

        player = self.machine.game.player
        display_remaining = self._display_text(remaining)
        player["mode_status_title"] = getattr(self, "_message_countdown_status_title", "SECONDS LEFT")
        player["mode_status_value"] = display_remaining

        if remaining > 0:
            self._schedule_countdown_tick()
        else:
            # Let the player see 0 briefly before the widgets are removed.
            self.delay.add(
                name=self.COUNTDOWN_DELAY_NAME,
                ms=500,
                callback=self._hide_countdown_widgets,
            )

    def _hide_countdown_widgets(self):
        self.machine.events.post("hide_mode_message")
        self.machine.events.post("hide_mode_status")

    def _clear_mode_display_context(self, **kwargs):
        """Cancel stale temporary display work when a gameplay mode stops.

        Reminder/countdown callbacks live in base mode, not in the villain mode
        that requested them. If a villain mode stops while a reminder/countdown
        is pending, the callback can fire later against a removed/replaced GMC
        widget. Clearing the context here keeps stopped modes from updating the
        shared message/status widgets.
        """
        self._cancel_countdown()
        self.delay.remove(self.REMINDER_DELAY_NAME)
        self._reminder_payload = None
        self._clear_mode_message_vars()
        self._clear_mode_status_vars()
        self.machine.events.post("mode_display_context_cleared")

    def _hide_mode_message(self, **kwargs):
        self._cancel_countdown()
        self._clear_mode_message_vars()

    def _schedule_mode_message_reminder(self):
        self.delay.remove(self.REMINDER_DELAY_NAME)
        self.delay.add(name=self.REMINDER_DELAY_NAME, ms=self.REMINDER_INTERVAL_MS, callback=self._show_mode_message_reminder)

    def _show_mode_message_reminder(self):
        payload = getattr(self, "_reminder_payload", None)
        if not payload:
            return
        self.machine.events.post("show_mode_message", reminder=True, **payload)

    def _reset_mode_message_reminder(self, **kwargs):
        if getattr(self, "_reminder_payload", None):
            self._schedule_mode_message_reminder()

    def _cancel_mode_message_reminder(self, **kwargs):
        self.delay.remove(self.REMINDER_DELAY_NAME)
        self._reminder_payload = None

    def _hide_mode_status(self, **kwargs):
        self._cancel_countdown()
        self._clear_mode_status_vars()

    def _cancel_countdown(self):
        self.delay.remove(self.COUNTDOWN_DELAY_NAME)
        self._message_countdown_remaining = 0

    def mode_stop(self, **kwargs):
        self._cancel_countdown()
        self.delay.remove(self.REMINDER_DELAY_NAME)
        self._reminder_payload = None
        super().mode_stop(**kwargs)

    def _clear_mode_message_vars(self):
        self._set_mode_message_vars(
            message_mode_title=" ",
            message_mode_subtitle=" ",
            message_mode_value=" ",
            message_mode_seconds=" ",
        )

    def _clear_mode_status_vars(self):
        self._set_mode_status_vars(
            mode_status_title=" ",
            mode_status_value=" ",
        )

    @staticmethod
    def _parse_seconds(value):
        try:
            if value is None or value == "":
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _display_text(value):
        """Return display-safe text, comma-formatting score/jackpot numbers."""
        if value is None or value == "":
            return " "

        # Display-only helper: these vars are used by GMC text widgets.
        # Format integer scores/jackpots like 250,000, while leaving
        # mixed strings such as "3 / 12", "SURVIVE", or "+50K" alone.
        if isinstance(value, bool):
            return str(value)

        if isinstance(value, int):
            return f"{value:,}"

        if isinstance(value, float):
            if value.is_integer():
                return f"{int(value):,}"
            return str(value)

        text = str(value)
        stripped = text.strip()
        if stripped:
            sign = ""
            digits = stripped
            if digits[0] in "+-":
                sign = digits[0]
                digits = digits[1:]
            if digits.isdigit():
                return f"{sign}{int(digits):,}"

        return text
