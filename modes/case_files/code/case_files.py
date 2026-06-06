from mpf.core.mode import Mode


class CaseFiles(Mode):
    """Global Daily Bugle Case File system.

    Case Files are global player-level modifiers. They are available before a
    villain starts, then reset after the villain summary cleanup. Case file
    switch handling is locked out during villain/mini-wizard/final-wizard flow.

    Current Case Files:
      - more_jackpots
      - more_time
      - bigger_jackpots
      - safety_net
      - shot_assist

    Lower spinner cycles the selected/flashing right 5-bank Case File target.
    The currently selected/flashing target awards that Case File when hit.
    """

    CASE_FILES = [
        "more_jackpots",
        "more_time",
        "bigger_jackpots",
        "safety_net",
        "shot_assist",
    ]

    CASE_FILE_LABELS = {
        "more_jackpots": "More Jackpots",
        "more_time": "More Time",
        "bigger_jackpots": "Bigger Jackpots",
        "safety_net": "Safety Net",
        "shot_assist": "Shot Assist",
    }

    CASE_FILE_BENEFITS = {
        "more_jackpots": "Adds extra jackpot chances in villain modes",
        "more_time": "Adds time or slows timers in villain modes",
        "bigger_jackpots": "Boosts jackpot values in villain modes",
        "safety_net": "Adds ball save, retry, grace, or protection",
        "shot_assist": "Spots progress or makes objectives easier",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.case_files_logic_active = True
        self._ensure_player_vars()
        self._add_handlers()
        self._restore_state()
        self._publish_widget_vars()

    def mode_stop(self, **kwargs):
        self.case_files_logic_active = False
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("case_file_spinner_hit", self._spinner_hit)

        self.add_mode_event_handler("case_file_drop_1_hit", self._case_file_drop_hit, index=0)
        self.add_mode_event_handler("case_file_drop_2_hit", self._case_file_drop_hit, index=1)
        self.add_mode_event_handler("case_file_drop_3_hit", self._case_file_drop_hit, index=2)
        self.add_mode_event_handler("case_file_drop_4_hit", self._case_file_drop_hit, index=3)
        self.add_mode_event_handler("case_file_drop_5_hit", self._case_file_drop_hit, index=4)

        # Villain modes can listen for this event, or just read player vars at
        # their own mode_start. We publish current values when a villain starts.
        self.add_mode_event_handler("villain_mode_started", self._publish_case_file_bonuses)

        self.add_mode_event_handler("chapter_mini_wizard_started", self._clear_wizard_prep)
        self.add_mode_event_handler("case_files_restore_state", self._restore_state)
        self.add_mode_event_handler("case_files_reset_all", self._reset_all_case_files)
        self.add_mode_event_handler("case_files_clear_lights", self._clear_lights)

    def _ensure_player_vars(self):
        defaults = {
            "case_file_selected_index": 0,

            "case_files_collected_count": 0,
            "case_files_complete_ready": 0,
            "wizard_prep_this_chapter": 0,
            "wizard_prep_level": 0,
            "wizard_prep_summary": "No Case Files collected",
            "wizard_prep_next_award": "Collect More Jackpots",
        }

        for key in self.CASE_FILES:
            defaults[f"case_file_{key}"] = 0
            defaults[f"case_file_{key}_collected"] = 0
            defaults[f"case_file_{key}_state"] = "NOT COLLECTED"

        for name, value in defaults.items():
            if name not in self.machine.game.player:
                self.machine.game.player[name] = value

        self._refresh_counts()
        self._publish_widget_vars()

    def _spinner_hit(self, **kwargs):
        if not self.case_files_logic_active or self._case_files_locked():
            return

        self.machine.events.post("case_file_spinner_progress")
        self._advance_selected_case_file()

    def _advance_selected_case_file(self):
        start_index = int(self.machine.game.player["case_file_selected_index"])

        for step in range(1, len(self.CASE_FILES) + 1):
            next_index = (start_index + step) % len(self.CASE_FILES)
            key = self.CASE_FILES[next_index]

            if self._case_file_value(key) == 0:
                self.machine.game.player["case_file_selected_index"] = next_index
                self._restore_selected_case_file()
                return

        self.machine.events.post("case_files_all_collected_already")

    def _case_file_drop_hit(self, index=None, **kwargs):
        if not self.case_files_logic_active or self._case_files_locked():
            return

        self.machine.events.post("case_file_any_drop_hit", hit_index=index + 1)

        selected_index = int(self.machine.game.player["case_file_selected_index"])

        if index != selected_index:
            self.machine.events.post(
                "case_file_wrong_drop_hit",
                hit_index=index + 1,
                selected_index=selected_index + 1,
            )
            return

        key = self.CASE_FILES[selected_index]

        if self._case_file_value(key) == 1:
            self.machine.events.post("case_file_already_collected", case_file=key)
            self._advance_selected_case_file()
            return

        self.machine.events.post("case_file_selected_stop")

        self._set_case_file_collected(key, 1)
        self._refresh_counts()
        self._publish_widget_vars()

        self.machine.events.post(
            "case_file_collected",
            case_file=key,
            label=self.CASE_FILE_LABELS[key],
            benefit=self.CASE_FILE_BENEFITS[key],
            count=self.machine.game.player["case_files_collected_count"],
        )
        self.machine.events.post(f"case_file_collected_{key}")

        if self.machine.game.player["case_files_collected_count"] >= len(self.CASE_FILES):
            self._complete_case_file_set()
        else:
            self._advance_selected_case_file()

        self._restore_state()

    def _complete_case_file_set(self):
        self.machine.game.player = self.machine.game.player
        if self.machine.game.player["case_files_complete_ready"] == 1:
            return

        self.machine.game.player["case_files_complete_ready"] = 1
        self.machine.game.player["wizard_prep_this_chapter"] += 1
        self.machine.game.player["wizard_prep_level"] = int(self.machine.game.player["case_files_collected_count"])
        self.machine.game.player["wizard_prep_summary"] = "All Case Files collected"
        self.machine.game.player["wizard_prep_next_award"] = "Wizard Prep complete"

        self.machine.events.post(
            "case_files_complete",
            wizard_prep=self.machine.game.player["wizard_prep_this_chapter"],
        )
        self.machine.events.post(
            "wizard_prep_added",
            wizard_prep=self.machine.game.player["wizard_prep_this_chapter"],
        )

    def _publish_case_file_bonuses(self, **kwargs):
        """Publish the global Case File state for the mode that just started."""
        self._refresh_counts()
        self._publish_widget_vars()

        payload = {
            "collected_count": self.machine.game.player["case_files_collected_count"],
            "complete": self.machine.game.player["case_files_complete_ready"],
            "wizard_prep_level": self.machine.game.player["wizard_prep_level"],
        }

        for key in self.CASE_FILES:
            payload[key] = self._case_file_value(key)
            payload[f"{key}_collected"] = self._case_file_value(key)

        self.machine.events.post("case_files_available_for_villain", **payload)

    def _clear_wizard_prep(self, **kwargs):
        self.machine.game.player["wizard_prep_this_chapter"] = 0
        self.machine.events.post("wizard_prep_cleared")
        self._publish_widget_vars()

    def _reset_all_case_files(self, **kwargs):
        """Manual reset hook. Case Files are not cleared by villain starts."""
        self.machine.events.post("case_file_selected_stop")

        for key in self.CASE_FILES:
            self._set_case_file_collected(key, 0)

        self.machine.game.player["case_file_selected_index"] = 0
        self.machine.game.player["case_files_complete_ready"] = 0
        self.machine.game.player["wizard_prep_this_chapter"] = 0
        self._refresh_counts()
        self._publish_widget_vars()
        self.machine.events.post("case_files_cleared")
        self._restore_state()

    def _restore_state(self, **kwargs):
        if not self.case_files_logic_active:
            return

        if self._case_files_locked():
            self.machine.events.post("case_files_clear_lights")
            self._publish_widget_vars()
            return

        self._refresh_counts()
        self._publish_widget_vars()

        for index, key in enumerate(self.CASE_FILES):
            collected = self._case_file_value(key) == 1
            self.machine.events.post(
                f"case_file_{index + 1}_{'collected' if collected else 'uncollected'}",
                case_file=key,
                label=self.CASE_FILE_LABELS[key],
                benefit=self.CASE_FILE_BENEFITS[key],
            )

        self._restore_selected_case_file()

        self.machine.events.post(
            "case_files_status",
            selected_index=int(self.machine.game.player["case_file_selected_index"]) + 1,
            collected_count=self.machine.game.player["case_files_collected_count"],
            wizard_prep=self.machine.game.player["wizard_prep_this_chapter"],
            wizard_prep_level=self.machine.game.player["wizard_prep_level"],
            wizard_prep_summary=self.machine.game.player["wizard_prep_summary"],
            wizard_prep_next_award=self.machine.game.player["wizard_prep_next_award"],
        )

    def _restore_selected_case_file(self):
        selected_index = int(self.machine.game.player["case_file_selected_index"])
        key = self.CASE_FILES[selected_index]

        if self._case_file_value(key) == 1:
            self._advance_selected_case_file()
            return

        self.machine.events.post(
            "case_file_selected",
            selected_index=selected_index + 1,
            case_file=key,
            label=self.CASE_FILE_LABELS[key],
            benefit=self.CASE_FILE_BENEFITS[key],
        )
        self.machine.events.post(f"case_file_selected_{key}")

    def _case_file_value(self, key):
        collected = self._player_var(f"case_file_{key}_collected", None)

        if collected is None:
            collected = self._player_var(f"case_file_{key}", 0)

        return self._safe_int(collected)

    def _player_var(self, name, default=0):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return default
        try:
            return player[name]
        except Exception:
            return default

    def _set_case_file_collected(self, key, value):
        value = 1 if self._safe_int(value) == 1 else 0
        self.machine.game.player[f"case_file_{key}"] = value
        self.machine.game.player[f"case_file_{key}_collected"] = value
        self.machine.game.player[f"case_file_{key}_state"] = "COLLECTED" if value else "NOT COLLECTED"

    def _refresh_counts(self):
        collected_count = sum(self._case_file_value(key) for key in self.CASE_FILES)
        self.machine.game.player["case_files_collected_count"] = collected_count
        self.machine.game.player["case_files_complete_ready"] = 1 if collected_count >= len(self.CASE_FILES) else 0
        self.machine.game.player["wizard_prep_level"] = collected_count

        if collected_count >= len(self.CASE_FILES):
            self.machine.game.player["wizard_prep_summary"] = "All Case Files collected"
            self.machine.game.player["wizard_prep_next_award"] = "Wizard Prep complete"
        else:
            next_key = self._next_missing_case_file()
            if next_key:
                self.machine.game.player["wizard_prep_summary"] = f"{collected_count} / {len(self.CASE_FILES)} Case Files collected"
                self.machine.game.player["wizard_prep_next_award"] = f"Collect {self.CASE_FILE_LABELS[next_key]}"
            else:
                self.machine.game.player["wizard_prep_summary"] = "Case Files ready"
                self.machine.game.player["wizard_prep_next_award"] = "Wizard Prep complete"

    def _next_missing_case_file(self):
        for key in self.CASE_FILES:
            if self._case_file_value(key) == 0:
                return key
        return None

    def _publish_widget_vars(self):
        for index, key in enumerate(self.CASE_FILES, start=1):
            collected = self._case_file_value(key)
            self.machine.game.player[f"case_file_{index}_key"] = key
            self.machine.game.player[f"case_file_{index}_name"] = self.CASE_FILE_LABELS[key]
            self.machine.game.player[f"case_file_{index}_state"] = "COLLECTED" if collected else "NOT COLLECTED"
            self.machine.game.player[f"case_file_{index}_benefit"] = self.CASE_FILE_BENEFITS[key]

        self.machine.events.post("case_files_status_changed")

    def _clear_lights(self, **kwargs):
        """Public event hook for clearing all case file lights/shows.

        The actual show stops live in case_files.yaml on the case_files_clear_lights
        event. This method exists so Python callers can use the same event safely
        without changing case-file data.
        """
        self.machine.events.post("case_files_cleared")

    def _case_files_locked(self):
        """Return True when case-file switch logic should be ignored.

        Case files should not advance, collect, or relight during villain modes,
        mini-wizard flow, or final-wizard flow. Reset/clear events still work.
        """
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return True

        lock_vars = (
            "villain_mode_running",
            "villain_mode_in_summary",
            "chapter_mini_wizard_ready",
            "mini_wizard_daily_bugle_ready",
            "final_wizard_ready",
        )

        for var_name in lock_vars:
            try:
                if self._safe_int(player[var_name], 0) == 1:
                    return True
            except Exception:
                pass

        return False

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
