from mpf.core.mode import Mode


class Skymaster(Mode):
    """Temporary Skymaster placeholder pending a distinct non-rooftop redesign."""

    MODE_KEY = "skymaster"
    DISPLAY_NAME = "SKYMASTER"
    HIT_SCORE = 25_000
    MAJOR_SCORE = 75_000
    HITS_TO_COMPLETE = 10

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.hits = 0
        self.major_hits = 0
        self.mode_points = 0
        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player[f"{self.MODE_KEY}_state"] = 1
        self.add_mode_event_handler(f"{self.MODE_KEY}_shot_hit", self._shot_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_major_hit", self._major_hit)
        self._show_message(self.DISPLAY_NAME, f"HIT {self.HITS_TO_COMPLETE} SHOTS", reminder=True)

    def mode_stop(self, **kwargs):
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        super().mode_stop(**kwargs)

    def _shot_hit(self, **kwargs):
        if self.mode_done:
            return
        self.hits += 1
        self._score(self.HIT_SCORE)
        self._sync_vars()
        self._show_message("SHOT HIT", f"{self.hits} / {self.HITS_TO_COMPLETE}")
        if self.hits >= self.HITS_TO_COMPLETE:
            self._complete_mode()

    def _major_hit(self, **kwargs):
        if self.mode_done:
            return
        self.major_hits += 1
        self._score(self.MAJOR_SCORE)
        self._sync_vars()
        self._show_message("MAJOR HIT", f"{self.major_hits} MAJOR", event="show_mode_jackpot")

    def _complete_mode(self):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("skymaster_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.hits
        player["active_mode_major_hits"] = self.major_hits

    def _show_message(self, title, subtitle="", value="", event="show_mode_message", reminder=False):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            reminder=reminder,
        )
