from mpf.core.mode import Mode


class CaseFiles(Mode):
    """Lower spinner + right 5-bank Case File system.

    - Lower spinner cycles the selected/flashing Case File target every 3 spins.
    - Any right 5-bank drop hit flashes l_gi_5bank_lower and l_gi_5bank_upper.
    - Only the currently selected/flashing target awards a Case File.
    - Awarded Case Files stay solid until the next villain starts.
    - Completing all five Case Files adds Wizard Prep for the chapter.
    """

    CASE_FILES = [
        "extra_jackpot",
        "more_time",
        "multiplier",
        "safety",
        "super_boost",
    ]

    CASE_FILE_LABELS = {
        "extra_jackpot": "Extra Jackpot",
        "more_time": "More Time",
        "multiplier": "Multiplier Boost",
        "safety": "Safety / Retry",
        "super_boost": "Super Jackpot Boost",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.case_files_logic_active = True
        self._ensure_player_vars()
        self._add_handlers()
        self._restore_state()

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

        self.add_mode_event_handler("villain_mode_started", self._consume_case_files)
        self.add_mode_event_handler("chapter_mini_wizard_started", self._clear_wizard_prep)
        self.add_mode_event_handler("case_files_restore_state", self._restore_state)

    def _ensure_player_vars(self):
        defaults = {
            "case_file_selected_index": 0,
            "case_file_spinner_count": 0,

            "case_file_extra_jackpot": 0,
            "case_file_more_time": 0,
            "case_file_multiplier": 0,
            "case_file_safety": 0,
            "case_file_super_boost": 0,

            "case_files_collected_count": 0,
            "case_files_complete_ready": 0,
            "wizard_prep_this_chapter": 0,
        }

        for name, value in defaults.items():
            if name not in self.player:
                self.player[name] = value

    def _spinner_hit(self, **kwargs):
        if not self.case_files_logic_active:
            return

        self.player["case_file_spinner_count"] += 1

        # Every 3 lower-spinner spins advances the selected Case File.
        if self.player["case_file_spinner_count"] % 3 != 0:
            self.machine.events.post(
                "case_file_spinner_progress",
                spins=self.player["case_file_spinner_count"],
            )
            return

        self._advance_selected_case_file()

    def _advance_selected_case_file(self):
        start_index = int(self.player["case_file_selected_index"])

        for step in range(1, len(self.CASE_FILES) + 1):
            next_index = (start_index + step) % len(self.CASE_FILES)
            key = self.CASE_FILES[next_index]

            if self.player[f"case_file_{key}"] == 0:
                self.player["case_file_selected_index"] = next_index
                self._restore_selected_case_file()
                return

        self.machine.events.post("case_files_all_collected_already")

    def _case_file_drop_hit(self, index=None, **kwargs):
        if not self.case_files_logic_active:
            return

        # Any right 5-bank drop hit flashes the local GI.
        self.machine.events.post("case_file_any_drop_hit", hit_index=index + 1)

        selected_index = int(self.player["case_file_selected_index"])

        # Wrong target: feedback only, no Case File.
        if index != selected_index:
            self.machine.events.post(
                "case_file_wrong_drop_hit",
                hit_index=index + 1,
                selected_index=selected_index + 1,
            )
            return

        key = self.CASE_FILES[selected_index]
        var_name = f"case_file_{key}"

        if self.player[var_name] == 1:
            self.machine.events.post("case_file_already_collected", case_file=key)
            self._advance_selected_case_file()
            return

        # Stop selected flashing show before making the target solid.
        self.machine.events.post("case_file_selected_stop")

        self.player[var_name] = 1
        self.player["case_files_collected_count"] += 1

        self.machine.events.post(
            "case_file_collected",
            case_file=key,
            label=self.CASE_FILE_LABELS[key],
            count=self.player["case_files_collected_count"],
        )
        self.machine.events.post(f"case_file_collected_{key}")

        if self.player["case_files_collected_count"] >= len(self.CASE_FILES):
            self._complete_case_file_set()
        else:
            self._advance_selected_case_file()

        self._restore_state()

    def _complete_case_file_set(self):
        if self.player["case_files_complete_ready"] == 1:
            return

        self.player["case_files_complete_ready"] = 1
        self.player["wizard_prep_this_chapter"] += 1

        self.machine.events.post(
            "case_files_complete",
            wizard_prep=self.player["wizard_prep_this_chapter"],
        )
        self.machine.events.post(
            "wizard_prep_added",
            wizard_prep=self.player["wizard_prep_this_chapter"],
        )

    def _consume_case_files(self, **kwargs):
        self.machine.events.post(
            "case_files_consumed",
            extra_jackpot=self.player["case_file_extra_jackpot"],
            more_time=self.player["case_file_more_time"],
            multiplier=self.player["case_file_multiplier"],
            safety=self.player["case_file_safety"],
            super_boost=self.player["case_file_super_boost"],
        )

        for key in self.CASE_FILES:
            self.player[f"case_file_{key}"] = 0

        self.player["case_files_collected_count"] = 0
        self.player["case_files_complete_ready"] = 0
        self.player["case_file_selected_index"] = 0
        self.player["case_file_spinner_count"] = 0

        self.machine.events.post("case_files_cleared")
        self._restore_state()

    def _clear_wizard_prep(self, **kwargs):
        self.player["wizard_prep_this_chapter"] = 0
        self.machine.events.post("wizard_prep_cleared")

    def _restore_state(self, **kwargs):
        if not self.case_files_logic_active:
            return

        for index, key in enumerate(self.CASE_FILES):
            collected = self.player[f"case_file_{key}"] == 1
            self.machine.events.post(
                f"case_file_{index + 1}_{'collected' if collected else 'uncollected'}",
                case_file=key,
                label=self.CASE_FILE_LABELS[key],
            )

        self._restore_selected_case_file()

        self.machine.events.post(
            "case_files_status",
            selected_index=int(self.player["case_file_selected_index"]) + 1,
            collected_count=self.player["case_files_collected_count"],
            wizard_prep=self.player["wizard_prep_this_chapter"],
        )

    def _restore_selected_case_file(self):
        selected_index = int(self.player["case_file_selected_index"])
        key = self.CASE_FILES[selected_index]

        # If selected target is already collected, move to the next uncollected one.
        if self.player[f"case_file_{key}"] == 1:
            self._advance_selected_case_file()
            return

        self.machine.events.post(
            "case_file_selected",
            selected_index=selected_index + 1,
            case_file=key,
            label=self.CASE_FILE_LABELS[key],
        )
        self.machine.events.post(f"case_file_selected_{key}")
