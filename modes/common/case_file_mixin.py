class CaseFileMixin:
    """Shared helper for villain modes that want to read global Case File bonuses."""

    VILLAIN_START_BASE = 100_000
    VILLAIN_START_PER_CASE_FILE = 50_000
    OPENING_RELEASE_SWITCHES = (
        "s_saucer_1", "s_saucer_2", "s_saucer_3", "s_vuk_switch", "s_plunger",
    )

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

    def reset_active_mode_summary(self, stat_count=3):
        """Start a villain attempt and seed its summary with the start award.

        Called once by each villain's mode_start, after the bookend intro.
        Wizard modes do not use this helper. Local score accumulators must
        start at villain_start_bonus so later summary updates retain it.
        """
        self.villain_start_bonus = 0
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return

        case_file_count = sum(self.get_case_file_bonuses().values())
        self.villain_start_bonus = (
            self.VILLAIN_START_BASE
            + self.VILLAIN_START_PER_CASE_FILE * case_file_count
        )
        player["score"] += self.villain_start_bonus
        player["active_mode_stat_count"] = int(stat_count)
        player["active_mode_completed"] = 0
        player["active_mode_points"] = self.villain_start_bonus
        player["active_mode_stat_1"] = 0
        player["active_mode_stat_2"] = 0
        self._prepare_opening_ball_save()

    def _prepare_opening_ball_save(self):
        """Every villain gets 20s; Safety Net extends the opening to 30s."""
        self.machine.game.player["villain_opening_save_seconds"] = (
            30 if self.get_case_file_bonuses()["safety_net"] else 20
        )
        self._opening_save_enabled = False
        self._opening_save_waiting_for_release = False
        self.add_mode_event_handler(
            f"mode_{self.name}_started", self._enable_opening_ball_save,
        )
        for switch in self.OPENING_RELEASE_SWITCHES:
            self.add_mode_event_handler(
                f"{switch}_inactive", self._start_opening_ball_save_timer,
            )

    def _enable_opening_ball_save(self, **kwargs):
        if self._opening_save_enabled:
            return
        self._opening_save_enabled = True
        self._opening_save_waiting_for_release = True
        self.machine.events.post("villain_opening_ball_save_enable")
        # Selection and bookend intros finish before mode_start. If the mode
        # still holds a starting ball, arm protection but wait to count time.
        held = any(
            self.machine.switches.get(name) is not None
            and self.machine.switches[name].state == 1
            for name in self.OPENING_RELEASE_SWITCHES
        )
        if not held:
            self._start_opening_ball_save_timer()

    def _start_opening_ball_save_timer(self, **kwargs):
        if not self._opening_save_waiting_for_release:
            return
        self._opening_save_waiting_for_release = False
        self.machine.events.post("villain_opening_ball_save_timer_start")

    def mode_stop(self, **kwargs):
        self._opening_save_waiting_for_release = False
        self.machine.events.post("villain_opening_ball_save_disable")
        super().mode_stop(**kwargs)

    def publish_active_mode_summary(self, points, stat_1=0, stat_2=0, stat_count=None):
        """Publish local mode totals into the shared summary/display slots."""
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return

        if stat_count is not None:
            player["active_mode_stat_count"] = int(stat_count)
        player["active_mode_points"] = points
        player["active_mode_stat_1"] = stat_1
        player["active_mode_stat_2"] = stat_2

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
