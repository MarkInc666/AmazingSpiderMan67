from mpf.core.mode import Mode


class Base(Mode):
    """Base-mode helpers for display messages.

    The mode message widget reads player variables. Many gameplay modes post
    show_mode_* events with message fields as event kwargs. This handler copies
    those kwargs into player vars before the widget is played, so repeated
    countdown/spinner updates refresh the on-screen labels reliably and stale
    values are cleared when omitted.
    """

    MESSAGE_EVENTS = (
        "show_mode_message",
        "show_mode_message_long",
        "show_mode_jackpot",
        "show_mode_countdown",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        for event in self.MESSAGE_EVENTS:
            self.add_mode_event_handler(event, self._sync_mode_message_vars, priority=10000)
        self._clear_mode_message_vars()

    def _sync_mode_message_vars(
        self,
        message_mode_title="",
        message_mode_subtitle="",
        message_mode_value="",
        message_mode_seconds="",
        **kwargs,
    ):
        player = self.machine.game.player
        player["message_mode_title"] = self._display_text(message_mode_title)
        player["message_mode_subtitle"] = self._display_text(message_mode_subtitle)
        player["message_mode_value"] = self._display_text(message_mode_value)
        player["message_mode_seconds"] = self._display_text(message_mode_seconds)

    def _clear_mode_message_vars(self):
        player = self.machine.game.player
        player["message_mode_title"] = " "
        player["message_mode_subtitle"] = " "
        player["message_mode_value"] = " "
        player["message_mode_seconds"] = " "

    @staticmethod
    def _display_text(value):
        if value is None or value == "":
            return " "
        return str(value)
