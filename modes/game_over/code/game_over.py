from mpf.core.mode import Mode


class GameOver(Mode):
    """Final score presentation after MPF's high-score check."""

    DISPLAY_MS = 5000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self._ending_queue = None
        # High Score's priority-500 queued start runs before this priority-400
        # handler, including its initials and award presentation when earned.
        self.add_mode_event_handler("game_ending", self._game_ending)

    def _game_ending(self, queue, **kwargs):
        game = self.machine.game
        if not game or self._ending_queue is not None:
            return
        players = list(game.player_list)
        if any(int(player["test_mode_exit_requested"] or 0) == 1
               or int(player["test_mode_session"] or 0) == 1 for player in players):
            return
        for index in range(4):
            text = ""
            if index < len(players):
                player = players[index]
                text = f"PLAYER {player.number}   {int(player['score']):,}"
            self.machine.variables.set_machine_var(f"game_over_score_{index + 1}", text)
        queue.wait()
        self._ending_queue = queue
        self.machine.events.post("asm_game_over_show")
        self.delay.add(name="game_over_finish", ms=self.DISPLAY_MS, callback=self._finish)

    def _finish(self):
        self.machine.events.post("asm_game_over_hide")
        queue = self._ending_queue
        self._ending_queue = None
        if queue is not None:
            queue.clear()

    def mode_stop(self, **kwargs):
        self.delay.remove("game_over_finish")
        self._finish()
        super().mode_stop(**kwargs)
