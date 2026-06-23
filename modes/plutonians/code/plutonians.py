from mpf.core.mode import Mode

"""
Jesse James Robot placeholder villain mode.

Mode idea:
Lit target appears briefly; hit before it moves to win quickdraw jackpots.

PLACEHOLDER IMPLEMENTATION
- Python owns scoring, mode state, player variables, and completion/failure.
- YAML maps common playfield hits into generic mode events.
- Replace this with real gameplay when the villain is built out.
"""


class Plutonians(Mode):
    MODE_KEY = "plutonians"
    DISPLAY_NAME = "Jesse James Robot"
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
        self.add_mode_event_handler(f"{self.MODE_KEY}_complete_request", self._complete_mode)
        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._fail_mode)

        self.machine.events.post(f"{self.MODE_KEY}_placeholder_started")
        self._show_placeholder_message(self.DISPLAY_NAME.upper(), f"HIT {self.HITS_TO_COMPLETE} SHOTS", value=self.mode_points)

    def _shot_hit(self, **kwargs):
        if self.mode_done:
            return
        self.hits += 1
        self._score(self.HIT_SCORE)
        self._sync_vars()
        self.machine.events.post(f"{self.MODE_KEY}_progress", hits=self.hits)
        self._show_placeholder_message("SHOT HIT", f"{self.hits} / {self.HITS_TO_COMPLETE}", value=self.mode_points)
        if self.hits >= self.HITS_TO_COMPLETE:
            self._complete_mode()

    def _major_hit(self, **kwargs):
        if self.mode_done:
            return
        self.major_hits += 1
        self._score(self.MAJOR_SCORE)
        self._sync_vars()
        self.machine.events.post(f"{self.MODE_KEY}_major_progress", major_hits=self.major_hits)
        self._show_placeholder_message("MAJOR HIT", f"{self.major_hits} MAJOR", value=self.mode_points, event="show_mode_jackpot")

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._show_placeholder_message(self.DISPLAY_NAME.upper(), "MODE COMPLETE", value=self.mode_points, event="show_mode_jackpot")
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._show_placeholder_message(self.DISPLAY_NAME.upper(), "MODE COMPLETE", value=self.mode_points, event="show_mode_jackpot")
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")


    def _show_placeholder_message(self, title, subtitle="", value="", seconds="", event="show_mode_message"):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
        )

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.hits
        player["active_mode_major_hits"] = self.major_hits
