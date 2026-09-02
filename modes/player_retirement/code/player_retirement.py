from mpf.core.mode import Mode


class PlayerRetirement(Mode):
    """Skip players whose ASM67 game ended by defeating Kingpin.

    MPF's stock game loop assumes every player remains in rotation through
    balls_per_game. ASM67 allows a player to finish early by completing the
    Final Wizard, so this game-long controller skips those players before MPF
    increments/serves their next ball while leaving the other players intact.
    """

    RETIRED_VAR = "final_wizard_completed"

    def mode_start(self, **kwargs):
        del kwargs
        self._original_num_players = self.machine.game.num_players if self.machine.game else None
        self.add_mode_event_handler(
            "final_showdown_mode_complete",
            self._retire_current_player,
            priority=10000,
        )
        self.add_mode_event_handler(
            "final_showdown_mode_completed_summary",
            self._final_summary_finished,
            priority=10000,
        )
        self.add_mode_event_handler(
            "final_showdown_mode_done",
            self._final_summary_finished,
            priority=10000,
        )
        self.add_mode_event_handler(
            "player_turn_will_start",
            self._skip_retired_player,
            priority=100000,
        )
        self.add_mode_event_handler(
            "player_turn_will_end",
            self._prepare_stock_game_end,
            priority=100000,
        )
        self.add_mode_event_handler(
            "game_will_end",
            self._restore_player_count_for_game_end,
            priority=100000,
        )

    @staticmethod
    def _safe_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _is_retired(self, player):
        try:
            return self._safe_int(player[self.RETIRED_VAR], 0) == 1
        except (KeyError, TypeError):
            return False

    def _retire_current_player(self, **kwargs):
        del kwargs
        game = self.machine.game
        if not game or not game.player:
            return

        player = game.player
        if self._is_retired(player):
            return

        player[self.RETIRED_VAR] = 1
        # A completed ASM67 game cannot be extended by queued extra balls.
        player["extra_balls"] = 0
        self.machine.events.post(
            "player_game_completed_final_wizard",
            player=player.number,
        )

    def _final_summary_finished(self, **kwargs):
        del kwargs
        game = self.machine.game
        if not game or not game.player or not self._is_retired(game.player):
            return

        # The final summary is the end of this player's playable game. Leave
        # the physical ball to drain normally so MPF's normal ball/bonus flow
        # remains authoritative and no extra ball is artificially served.
        self.machine.events.post("cmd_flippers_disable")
        self.machine.events.post("cmd_autofire_coils_disable")
        self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post(
            "player_game_completed_waiting_for_drain",
            player=game.player.number,
        )

    def _skip_retired_player(self, player=None, number=None, **kwargs):
        del player, number, kwargs
        game = self.machine.game
        if not game or not game.player or not self._is_retired(game.player):
            return

        players = list(game.player_list)
        if not players:
            return

        try:
            current_index = players.index(game.player)
        except ValueError:
            return

        for offset in range(1, len(players) + 1):
            candidate = players[(current_index + offset) % len(players)]
            if not self._is_retired(candidate):
                skipped_number = game.player.number
                game.player = candidate
                self.machine.events.post(
                    "retired_player_turn_skipped",
                    skipped_player=skipped_number,
                    next_player=candidate.number,
                )
                return

        # Defensive fallback. The previous player's player_turn_will_end
        # handler normally makes the stock game loop end before this state can
        # be reached.
        self.warning_log("All players are retired but MPF requested another turn.")


    def _restore_player_count_for_game_end(self, **kwargs):
        del kwargs
        game = self.machine.game
        if not game or self._original_num_players is None:
            return
        game.num_players = self._original_num_players

    def _prepare_stock_game_end(self, player=None, number=None, **kwargs):
        del player, number, kwargs
        game = self.machine.game
        if not game or not game.player:
            return

        current = game.player
        balls_per_game = self._safe_int(game.balls_per_game, 0)
        if balls_per_game <= 0:
            return

        # Is there any non-retired player who should receive another normal
        # turn after the current turn finishes?
        future_player_exists = False
        for candidate in game.player_list:
            if self._is_retired(candidate):
                continue
            if candidate is current:
                if self._safe_int(candidate["ball"], 0) < balls_per_game:
                    future_player_exists = True
                    break
            elif self._safe_int(candidate["ball"], 0) < balls_per_game:
                future_player_exists = True
                break

        if future_player_exists:
            return

        # MPF ends a game when the current player is on the last configured
        # ball and current_player.number == game.num_players. If higher-numbered
        # players retired early, temporarily make this player the terminal
        # player so MPF's normal end-game path runs without serving a fake ball.
        if self._is_retired(current) and self._safe_int(current["ball"], 0) < balls_per_game:
            current["ball"] = balls_per_game

        game.num_players = current.number
        self.machine.events.post(
            "all_active_players_finished",
            final_player=current.number,
        )
