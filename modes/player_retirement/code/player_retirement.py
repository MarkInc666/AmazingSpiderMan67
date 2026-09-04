from mpf.core.mode import Mode


class PlayerRetirement(Mode):
    """Retire only the player who completes ASM67's Final Wizard.

    Final Showdown completion marks the player retired. The victory summary is
    still shown, then flippers are disabled so the remaining ball drains and
    MPF runs its normal ball-ending / bonus flow. After bonus, this controller
    adjusts only the turn rotation needed to keep retired players out while
    preserving MPF's normal game-ending and high-score path.
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
        if not self._is_retired(player):
            player[self.RETIRED_VAR] = 1

        # Final Wizard completion ends this player's game. Extra balls must not
        # run after the normal end-of-ball bonus. Mark this player at the normal
        # terminal ball immediately; the stock loop will still run this ball's
        # bonus, and _prepare_stock_game_end temporarily backs off a terminal
        # last-numbered player only when earlier active players still have turns.
        player["extra_balls"] = 0
        balls_per_game = self._safe_int(game.balls_per_game, 0)
        if balls_per_game > 0:
            player["ball"] = max(self._safe_int(player["ball"], 0), balls_per_game)
        self.machine.events.post(
            "player_game_completed_final_wizard",
            player=player.number,
        )

    def _final_summary_finished(self, **kwargs):
        del kwargs
        game = self.machine.game
        if not game or not game.player or not self._is_retired(game.player):
            return

        # Do not jump directly to game_ending here. The remaining physical ball
        # must drain so MPF executes the existing ball_ending -> bonus flow.
        # Qualification is separately blocked for retired players. Reassert the
        # terminal ball number here in case any mode bookkeeping touched it while
        # the Final Showdown summary was on screen.
        balls_per_game = self._safe_int(game.balls_per_game, 0)
        if balls_per_game > 0:
            game.player["ball"] = max(self._safe_int(game.player["ball"], 0), balls_per_game)
        self.machine.events.post("cmd_flippers_disable")
        self.machine.events.post("cmd_autofire_coils_disable")
        self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("clear_villain_saucer_lights")
        self.machine.events.post("case_files_clear_lights")
        self.machine.events.post("rooftop_diverter_close")
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

        balls_per_game = self._safe_int(game.balls_per_game, 0)
        for offset in range(1, len(players) + 1):
            candidate = players[(current_index + offset) % len(players)]
            if (
                not self._is_retired(candidate)
                and (balls_per_game <= 0 or self._safe_int(candidate["ball"], 0) < balls_per_game)
            ):
                skipped_number = game.player.number
                game.player = candidate
                self.machine.events.post(
                    "retired_player_turn_skipped",
                    skipped_player=skipped_number,
                    next_player=candidate.number,
                )
                return

        # Normally unreachable because _prepare_stock_game_end makes MPF end
        # once no eligible player has another turn. If this fires, do not choose
        # a player who has already exhausted their normal balls.
        self.warning_log("No eligible player remains but MPF requested another turn.")

    def _restore_player_count_for_game_end(self, **kwargs):
        del kwargs
        game = self.machine.game
        if not game or self._original_num_players is None:
            return
        # Restore the real count before high-score / game-ended processing.
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

        # Retired players never receive an extra ball after their Final Wizard.
        if self._is_retired(current):
            current["extra_balls"] = 0

        # Look only for another non-retired player who still has a normal ball
        # remaining. The retired current player never counts as future work.
        future_player_exists = any(
            candidate is not current
            and not self._is_retired(candidate)
            and self._safe_int(candidate["ball"], 0) < balls_per_game
            for candidate in game.player_list
        )

        # A non-retired current player can itself have another future ball.
        if (
            not self._is_retired(current)
            and self._safe_int(current["ball"], 0) < balls_per_game
        ):
            future_player_exists = True

        if future_player_exists:
            # MPF normally ends immediately when the terminal-numbered player
            # finishes balls_per_game. If that player retired on their nominal
            # last ball while earlier players still have turns, keep this value
            # just below the terminal threshold. The player is still skipped by
            # _skip_retired_player, so no additional ball is ever served to them.
            if (
                self._is_retired(current)
                and current.number == game.num_players
                and self._safe_int(current["ball"], 0) >= balls_per_game
            ):
                current["ball"] = max(0, balls_per_game - 1)
            return

        # No active player has another turn. Arrange the values MPF's stock game
        # loop checks after player_turn_will_end so it follows _end_game(), which
        # preserves game_will_end -> high score -> game_ended -> attract.
        if self._is_retired(current):
            current["ball"] = balls_per_game

        game.num_players = current.number
        self.machine.events.post(
            "all_active_players_finished",
            final_player=current.number,
        )
