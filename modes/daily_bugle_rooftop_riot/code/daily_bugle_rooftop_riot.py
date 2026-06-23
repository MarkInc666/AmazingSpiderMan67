from mpf.core.mode import Mode

"""
Daily Bugle Rooftop Riot placeholder mini-wizard.

Mode idea:
Timed 2-ball or single-ball challenge: complete one objective from each classic villain, then cash Daily Bugle jackpot.
"""


class DailyBugleRooftopRiot(Mode):
    MODE_KEY = "daily_bugle_rooftop_riot"
    DISPLAY_NAME = "Daily Bugle Rooftop Riot"
    HIT_SCORE = 50_000
    JACKPOT_SCORE = 500_000
    HITS_TO_LIGHT_JACKPOT = 12

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.jackpot_lit = False
        self.hits = 0
        self.mode_points = 0

        player = self.machine.game.player
        player["mini_wizard_current_key"] = self.MODE_KEY
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0

        self.add_mode_event_handler(f"{self.MODE_KEY}_shot_hit", self._shot_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_jackpot_hit", self._jackpot_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_complete_request", self._complete_mode)
        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._fail_mode)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post(f"{self.MODE_KEY}_start_multiball")

    def mode_stop(self, **kwargs):
        player = self.machine.game.player
        if player["mini_wizard_current_key"] == self.MODE_KEY:
            player["mini_wizard_current_key"] = ""
        super().mode_stop(**kwargs)

    def _shot_hit(self, **kwargs):
        if self.mode_done:
            return
        self.hits += 1
        self._score(self.HIT_SCORE)
        self._sync_vars()
        if self.hits >= self.HITS_TO_LIGHT_JACKPOT:
            self.jackpot_lit = True
            self.machine.events.post(f"{self.MODE_KEY}_jackpot_lit")

    def _jackpot_hit(self, **kwargs):
        if self.mode_done:
            return
        if not self.jackpot_lit:
            self.machine.events.post(f"{self.MODE_KEY}_jackpot_not_lit")
            return
        self._score(self.JACKPOT_SCORE)
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")
        self.machine.events.post("chapter_mini_wizard_completed", mini_wizard=self.MODE_KEY)
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")
        self.machine.events.post("chapter_mini_wizard_completed", mini_wizard=self.MODE_KEY)
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.hits
