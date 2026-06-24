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

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        for event in self.MESSAGE_EVENTS:
            self.add_mode_event_handler(event, self._sync_mode_message_vars, priority=10000)
        self.add_mode_event_handler("show_mode_countdown", self._sync_mode_countdown_vars, priority=10000)
        self.add_mode_event_handler("hide_mode_message", self._hide_mode_message, priority=10000)

        self.add_mode_event_handler("show_mode_status", self._sync_mode_status_vars, priority=10000)
        self.add_mode_event_handler("update_mode_status", self._sync_mode_status_vars, priority=10000)
        self.add_mode_event_handler("hide_mode_status", self._hide_mode_status, priority=10000)

        self._clear_mode_message_vars()
        self._clear_mode_status_vars()

    def _sync_mode_message_vars(
        self,
        message_mode_title="",
        message_mode_subtitle="",
        message_mode_value="",
        message_mode_seconds="",
        **kwargs,
    ):
        self._cancel_countdown()
        self._set_mode_message_vars(
            message_mode_title=message_mode_title,
            message_mode_subtitle=message_mode_subtitle,
            message_mode_value=message_mode_value,
            message_mode_seconds=message_mode_seconds,
        )

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
            message_mode_seconds=message_mode_seconds,
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
        player["message_mode_seconds"] = display_remaining
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

    def _hide_mode_message(self, **kwargs):
        self._cancel_countdown()
        self._clear_mode_message_vars()

    def _hide_mode_status(self, **kwargs):
        self._clear_mode_status_vars()

    def _cancel_countdown(self):
        self.delay.remove(self.COUNTDOWN_DELAY_NAME)
        self._message_countdown_remaining = 0

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
        if value is None or value == "":
            return " "
        return str(value)
