from mpf.core.mode import Mode


class WhoIsTheRealVillain(Mode):
    """Placeholder chapter mini-wizard.

    Temporary flow mode:
    - Bookend intro starts this mode.
    - Start a 2-ball multiball.
    - Score simple hits while multiball runs.
    - When multiball ends, complete the mini-wizard.
    - Villain progression shows the summary and advances the chapter.
    """

    MODE_KEY = "who_is_the_real_villain"
    DISPLAY_NAME = "Who Is the Real Villain?"
    BASE_JACKPOT = 50_000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.hits = 0
        self.mode_points = 0

        player = self.machine.game.player
        self.case_file_bonus = player["mini_wizard_case_file_bonus"]
        self.jackpot_value = self.BASE_JACKPOT + self.case_file_bonus
        player["mini_wizard_current_key"] = self.MODE_KEY
        player[f"{self.MODE_KEY}_state"] = 1
        player[f"{self.MODE_KEY}_mode_points"] = 0
        player[f"{self.MODE_KEY}_hits"] = 0
        player[f"{self.MODE_KEY}_case_file_bonus"] = self.case_file_bonus
        player[f"{self.MODE_KEY}_jackpot_value"] = self.jackpot_value

        self.add_mode_event_handler(f"{self.MODE_KEY}_shot_hit", self._shot_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_complete_request", self._complete_mode)
        self.add_mode_event_handler(f"{self.MODE_KEY}_failed", self._fail_mode)
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
        self._score(self.jackpot_value)
        self._sync_vars()
        self.machine.events.post(
            f"{self.MODE_KEY}_progress",
            hits=self.hits,
            points=self.mode_points,
            jackpot_value=self.jackpot_value,
            case_file_bonus=self.case_file_bonus,
        )

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_mode_points"] = self.mode_points
        player[f"{self.MODE_KEY}_hits"] = self.hits
        player[f"{self.MODE_KEY}_case_file_bonus"] = self.case_file_bonus
        player[f"{self.MODE_KEY}_jackpot_value"] = self.jackpot_value
