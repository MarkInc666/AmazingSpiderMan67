from mpf.core.mode import Mode

"""
Trubble Unleashed mini-wizard placeholder.

Mode idea:
Monsters mini-wizard. 2-ball MB. Centaur, Cerberus, Cyclops, Vulcan, and Miss Trubble completed lights the chapter wizard. Miss Trubble unleashes the monsters for the wizard battle.

PLACEHOLDER IMPLEMENTATION
- MPF launches the multiball from YAML.
- Python tracks generic progress, scoring, and completion.
- Later we can replace the generic hit counter with the real five-objective rules.
"""


class MonsterIsland(Mode):
    MODE_KEY = "monster_island"
    DISPLAY_NAME = "Trubble Unleashed"
    HIT_SCORE = 50_000
    JACKPOT_SCORE = 500_000
    HITS_TO_COMPLETE = 15

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.hits = 0
        self.mode_points = 0
        player = self.machine.game.player if self.machine.game else None
        if player:
            player["mini_wizard_current_key"] = self.MODE_KEY
            player[f"{self.MODE_KEY}_completed"] = 0
            player[f"{self.MODE_KEY}_mode_points"] = 0
            player[f"{self.MODE_KEY}_hits"] = 0

        self.add_mode_event_handler(f"{self.MODE_KEY}_shot_hit", self._shot_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_jackpot_hit", self._jackpot_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_complete_request", self._complete_mode)
        self.add_mode_event_handler(f"{self.MODE_KEY}_failed", self._fail_mode)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post(f"{self.MODE_KEY}_start_multiball")

    def mode_stop(self, **kwargs):
        player = self.machine.game.player if self.machine.game else None
        if player:
            try:
                current_key = player["mini_wizard_current_key"]
            except KeyError:
                current_key = ""
            if current_key == self.MODE_KEY:
                player["mini_wizard_current_key"] = ""
        super().mode_stop(**kwargs)

    def _shot_hit(self, **kwargs):
        if self.mode_done:
            return
        self.hits += 1
        self._score(self.HIT_SCORE)
        self._sync_vars()
        self.machine.events.post(f"{self.MODE_KEY}_progress", hits=self.hits)
        if self.hits >= self.HITS_TO_COMPLETE:
            self._complete_mode()

    def _jackpot_hit(self, **kwargs):
        if self.mode_done:
            return
        self._score(self.JACKPOT_SCORE)
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player if self.machine.game else None
        if player:
            player[f"{self.MODE_KEY}_completed"] = 1
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")
        self.machine.events.post("chapter_mini_wizard_completed", mini_wizard=self.MODE_KEY)
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.events.post(f"{self.MODE_KEY}_mode_failed")
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _score(self, points):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return
        player[f"{self.MODE_KEY}_mode_points"] = self.mode_points
        player[f"{self.MODE_KEY}_hits"] = self.hits
