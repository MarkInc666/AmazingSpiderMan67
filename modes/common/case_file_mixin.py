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
            bonuses[key] = self._safe_int(player[f"case_file_{key}_collected"], 0) == 1

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


    def publish_active_case_file_helpers(self, helpers, empty_text="NO CASE FILE HELP ACTIVE"):
        """Publish player-facing active helper lines for the Case Files widget.

        helpers should be an ordered list of (case_file_key, message) tuples.
        Only messages for collected case files are shown.

        Example:
            self.publish_active_case_file_helpers([
                ("more_jackpots", "EXTRA RHINO JACKPOT AVAILABLE"),
                ("more_time", "RAGE TIMER EXTENDED 5s"),
            ])
        """
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return

        active_lines = []

        for key, message in helpers:
            if self.has_case_file(key) and message:
                active_lines.append(str(message))

        if not active_lines and empty_text:
            active_lines.append(str(empty_text))

        for index in range(5):
            var_name = f"active_case_file_helper_{index + 1}"
            if index < len(active_lines):
                player[var_name] = active_lines[index]
            else:
                player[var_name] = ""

        player["active_case_file_helper_count"] = len(active_lines)

        self.machine.events.post(
            "case_files_active_helpers_changed",
            helper_count=len(active_lines),
        )

    def clear_active_case_file_helpers(self):
        """Clear active helper lines when a villain mode ends."""
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return

        for index in range(5):
            player[f"active_case_file_helper_{index + 1}"] = ""

        player["active_case_file_helper_count"] = 0
        self.machine.events.post("case_files_active_helpers_changed", helper_count=0)

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default