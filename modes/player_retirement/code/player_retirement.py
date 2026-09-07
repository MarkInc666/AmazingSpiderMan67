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
            "mode_bonus_stopping",
            self._consume_retired_player_extra_balls,
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

        # Snapshot every ball this player would otherwise still receive before
        # retirement consumes anything. The current physical ball is not part of
        # this count: only unused normal balls plus queued earned extra balls.
        balls_per_game = self._safe_int(game.balls_per_game, 0)
        current_ball = self._safe_int(player["ball"], 0)
        normal_balls_remaining = max(0, balls_per_game - current_ball)
        earned_extra_balls = max(0, self._safe_int(player["extra_balls"], 0))
        remaining_balls = normal_balls_remaining + earned_extra_balls

        player["final_wizard_remaining_balls"] = remaining_balls
        player["final_wizard_remaining_ball_bonus"] = remaining_balls * 10000000
        player[self.RETIRED_VAR] = 1

        self.machine.events.post(
            "player_game_completed_final_wizard",
            player=player.number,
            remaining_balls=remaining_balls,
            remaining_ball_bonus=remaining_balls * 10000000,
        )

    def _final_summary_finished(self, **kwargs):
        del kwargs
        game = self.machine.game
        if not game or not game.player or not self._is_retired(game.player):
            return

        # Do not jump directly to game ending here. The remaining physical ball
        # must drain so MPF executes the existing ball_ending -> bonus flow.
        # The retiring player's future normal/extra balls were snapshotted when
        # Final Showdown completed and are paid during Bonus.
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
        game.num_players = self._original_num_players

    def _consume_retired_player_extra_balls(self, **kwargs):
        """Consume queued extra balls only after the retiring player's bonus ran."""
        del kwargs
        game = self.machine.game
        if not game or not game.player or not self._is_retired(game.player):
            return
        game.player["extra_balls"] = 0

    def _eligible_future_players(self, current):
        game = self.machine.game
        if not game:
            return []
        balls_per_game = self._safe_int(game.balls_per_game, 0)
        eligible = []
        for candidate in game.player_list:
            if candidate is current or self._is_retired(candidate):
                continue
            if balls_per_game <= 0 or self._safe_int(candidate["ball"], 0) < balls_per_game:
                eligible.append(candidate)
        return eligible

    def _prepare_stock_game_end(self, player=None, number=None, **kwargs):
        del player, number, kwargs
        game = self.machine.game
        if not game or not game.player:
            return

        current = game.player
        if not self._is_retired(current):
            return

        # Bonus has completed by the time MPF reaches player_turn_will_end.
        # Never allow a queued extra ball to be served after Final Showdown.
        current["extra_balls"] = 0

        future_players = self._eligible_future_players(current)
        if future_players:
            # MPF's stock loop normally ends the game when the last-numbered
            # player finishes their nominal last ball. If that player retired
            # while an earlier active player still has future balls, keep the
            # retired player's ball just below the terminal threshold so MPF
            # rotates instead. _skip_retired_player then selects the next
            # actually eligible player before a new ball starts.
            balls_per_game = self._safe_int(game.balls_per_game, 0)
            if (
                balls_per_game > 0
                and current.number == game.num_players
                and self._safe_int(current["ball"], 0) >= balls_per_game
            ):
                current["ball"] = max(0, balls_per_game - 1)
            self.machine.events.post(
                "retired_player_has_next_active_player",
                retired_player=current.number,
                next_player=future_players[0].number,
            )
            return

        # No player has another legitimate turn. Use MPF 0.80's supported
        # explicit game-end API instead of manipulating num_players and hoping
        # the stock terminal-ball test happens to fire. This preserves the
        # normal game_will_end -> game_ending -> game_ended/high-score path.
        # Prevent MPF's current game-loop iteration from rotating to a different
        # player after end_game() is requested. Temporarily make the retiring
        # player look like the terminal numbered player; game_will_end restores
        # the real player count before high-score / game-ended processing.
        balls_per_game = self._safe_int(game.balls_per_game, 0)
        if balls_per_game > 0:
            current["ball"] = max(self._safe_int(current["ball"], 0), balls_per_game)
        game.num_players = current.number
        self.machine.events.post(
            "all_active_players_finished",
            final_player=current.number,
        )
        game.end_game()
