class CaseFileMixin:
    """Shared helper for villain modes that want to read global Case File bonuses."""

    CASE_FILE_KEYS = (
        "more_jackpots",
        "bigger_jackpots",
        "more_time",
        "safety_net",
        "shot_assist",
    )

    def get_case_file_bonuses(self):
        """Return the 5 global case file states as booleans."""
        player = self.machine.game.player if self.machine.game else None

        bonuses = {
            "more_jackpots": False,
            "bigger_jackpots": False,
            "more_time": False,
            "safety_net": False,
            "shot_assist": False,
        }

        if not player:
            return bonuses

        for key in self.CASE_FILE_KEYS:
            bonuses[key] = self._player_var(
                f"case_file_{key}_collected",
                0
            ) == 1

        return bonuses

    def has_case_file(self, key):
        """Convenience check for one case file."""
        if not hasattr(self, "case_files"):
            self.case_files = self.get_case_file_bonuses()

        return bool(self.case_files.get(key, False))

    def publish_case_file_bonus_events(self, prefix):
        """
        Post events when a case file bonus is active.

        Example with prefix='rhino':
          rhino_case_file_more_time_active
          rhino_case_file_safety_net_active
          rhino_case_files_applied
        """
        if not hasattr(self, "case_files"):
            self.case_files = self.get_case_file_bonuses()

        active = []

        for key, enabled in self.case_files.items():
            if enabled:
                active.append(key)
                self.machine.events.post(f"{prefix}_case_file_{key}_active")

        self.machine.events.post(
            f"{prefix}_case_files_applied",
            active_case_files=",".join(active),
            active_count=len(active),
        )

    def _player_var(self, name, default=0):
        """Read an MPF player variable safely without using player.get()."""
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return default

        try:
            value = player[name]
        except KeyError:
            return default

        return self._safe_int(value, default)

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default