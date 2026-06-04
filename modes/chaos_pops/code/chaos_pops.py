from mpf.core.mode import Mode


class ChaosPops(Mode):
    """Chaos Pops background scoring mode.

    Design notes:
    - Tracks pop bumper hits during the ball.
    - Every 5 pop hits advances one Chaos Level.
    - Max Chaos Level is 20.
    - Each Chaos Level adds +100 points to the normal/default scoring events.

    Example:
        base pop value = 1100
        Chaos Level 20 bonus = 20 * 100 = 2000
        effective pop value = 1100 + 2000 = 3100

    This mode does not replace the normal base scoring in base.yaml.
    It listens for the same generic default scoring events and adds only the
    Chaos bonus on top:
        pops_hit
        drop_hit_no_mode
        secondary_switch_hit
        default_spinner_hit

    Later we can add lights/widgets/sounds from the posted events:
        chaos_pops_level_changed
        chaos_pops_max_level
        chaos_pops_bonus_scored
    """

    HITS_PER_LEVEL = 5
    MAX_LEVEL = 20
    BONUS_PER_LEVEL = 100

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.pop_hits = 0
        self.chaos_level = 0
        self.chaos_points = 0

        self._sync_vars()

        self.add_mode_event_handler("pops_hit", self._pop_hit)
        self.add_mode_event_handler("drop_hit_no_mode", self._default_score_hit)
        self.add_mode_event_handler("secondary_switch_hit", self._default_score_hit)
        self.add_mode_event_handler("default_spinner_hit", self._default_score_hit)

        self.machine.events.post("chaos_pops_started")

    def mode_stop(self, **kwargs):
        self.machine.events.post("chaos_pops_stopped")
        super().mode_stop(**kwargs)

    def _pop_hit(self, **kwargs):
        """Pop hits build the Chaos Level and also receive the current bonus."""
        old_level = self.chaos_level
        self.pop_hits += 1
        self.chaos_level = min(self.MAX_LEVEL, self.pop_hits // self.HITS_PER_LEVEL)

        if self.chaos_level != old_level:
            self.machine.events.post(
                "chaos_pops_level_changed",
                level=self.chaos_level,
                pop_hits=self.pop_hits,
                bonus=self._current_bonus(),
            )

            if self.chaos_level >= self.MAX_LEVEL:
                self.machine.events.post("chaos_pops_max_level")

        self._score_current_bonus(source="pops")
        self._sync_vars()

    def _default_score_hit(self, **kwargs):
        """Drops, secondary switches, and default spinner receive the chaos bonus."""
        self._score_current_bonus(source="default")
        self._sync_vars()

    def _score_current_bonus(self, source="default"):
        bonus = self._current_bonus()

        if bonus <= 0:
            return

        player = self.machine.game.player if self.machine.game else None
        if not player:
            return

        player["score"] += bonus
        self.chaos_points += bonus

        self.machine.events.post(
            "chaos_pops_bonus_scored",
            source=source,
            level=self.chaos_level,
            bonus=bonus,
            chaos_points=self.chaos_points,
        )

    def _current_bonus(self):
        return self.chaos_level * self.BONUS_PER_LEVEL

    def _sync_vars(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return

        player["chaos_pops_hits"] = self.pop_hits
        player["chaos_pops_level"] = self.chaos_level
        player["chaos_pops_bonus"] = self._current_bonus()
        player["chaos_pops_points"] = self.chaos_points
        player["chaos_pops_next_level_hits"] = min(
            self.MAX_LEVEL * self.HITS_PER_LEVEL,
            (self.chaos_level + 1) * self.HITS_PER_LEVEL,
        )
