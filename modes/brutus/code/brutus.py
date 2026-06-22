from mpf.core.mode import Mode

"""
Brutus placeholder villain mode.

Mode idea:
Brutus covers shots with ink; hit reveal shots to uncover jackpot.

PLACEHOLDER IMPLEMENTATION
- Python owns scoring, mode state, player variables, and completion/failure.
- YAML maps common playfield hits into generic mode events.
- Replace this with real gameplay when the villain is built out.
"""


class Brutus(Mode):
    MODE_KEY = "brutus"
    DISPLAY_NAME = "Brutus"
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
        player[f"{self.MODE_KEY}_mode_points"] = 0
        player[f"{self.MODE_KEY}_hits"] = 0
        player[f"{self.MODE_KEY}_major_hits"] = 0
        player[f"{self.MODE_KEY}_completed"] = 1

        self.add_mode_event_handler(f"{self.MODE_KEY}_shot_hit", self._shot_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_major_hit", self._major_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_complete_request", self._complete_mode)
        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._complete_mode)

        self.machine.events.post(f"{self.MODE_KEY}_placeholder_started")

    def _shot_hit(self, **kwargs):
        if self.mode_done:
            return
        self.hits += 1
        self._score(self.HIT_SCORE)
        self._sync_vars()
        self.machine.events.post(f"{self.MODE_KEY}_progress", hits=self.hits)
        if self.hits >= self.HITS_TO_COMPLETE:
            self._complete_mode()

    def _major_hit(self, **kwargs):
        if self.mode_done:
            return
        self.major_hits += 1
        self._score(self.MAJOR_SCORE)
        self._sync_vars()
        self.machine.events.post(f"{self.MODE_KEY}_major_progress", major_hits=self.major_hits)

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_completed"] = 1
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_completed"] = 1
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_mode_points"] = self.mode_points
        player[f"{self.MODE_KEY}_hits"] = self.hits
        player[f"{self.MODE_KEY}_major_hits"] = self.major_hits
