from mpf.core.mode import Mode


class VillainProgression(Mode):
    """Generic chapter/villain progression engine."""

    CHAPTERS = [
        {
            "key": "chapter_1",
            "name": "Daily Bugle Panic",
            "villain_count_required": 5,
            "mini_wizard_event": "start_mode_mini_wizard_bugle",
        },
        {
            "key": "chapter_2",
            "name": "Sinister Syndicate",
            "villain_count_required": 5,
            "mini_wizard_event": "start_mode_mini_wizard_syndicate",
        },
    ]

    VILLAINS = {
        "rhino": {"name": "Rhino", "tier": 1, "start_event": "start_mode_rhino"},
        "vulture": {"name": "Vulture", "tier": 1, "start_event": "start_mode_vulture"},
        "lizard": {"name": "Lizard", "tier": 1, "start_event": "start_mode_lizard"},
        "sandman": {"name": "Sandman", "tier": 1, "start_event": "start_mode_sandman"},
        "electro": {"name": "Electro", "tier": 1, "start_event": "start_mode_electro"},
        "doc_ock": {"name": "Doctor Octopus", "tier": 2, "start_event": "start_mode_doc_ock"},
        "scorpion": {"name": "Scorpion", "tier": 2, "start_event": "start_mode_scorpion"},
        "mysterio": {"name": "Mysterio", "tier": 2, "start_event": "start_mode_mysterio"},
        "goblin": {"name": "Green Goblin", "tier": 2, "start_event": "start_mode_goblin"},
        "parafino": {"name": "Parafino", "tier": 2, "start_event": "start_mode_parafino"},
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.villain_progression_logic_active = True
        self._ensure_player_vars()
        self._add_handlers()
        self._restore_state()

    def mode_stop(self, **kwargs):
        self.villain_progression_logic_active = False
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("villain_played", self._villain_played)
        self.add_mode_event_handler("chapter_mini_wizard_completed", self._mini_wizard_completed)
        self.add_mode_event_handler("villain_progression_restore_state", self._restore_state)
        self.add_mode_event_handler("villain_progression_start_default", self._start_default_villain)
        self.add_mode_event_handler("villain_progression_start_selected", self._start_selected_villain)
        self.add_mode_event_handler("villain_progression_request_choices", self._post_available_choices)

    def _ensure_player_vars(self):
        defaults = {
            "villain_chapter": 1,
            "villains_played_this_chapter": 0,
            "villains_played_total": 0,
            "chapter_mini_wizard_ready": 0,
            "final_wizard_ready": 0,
            "villain_current_key": "",
        }

        for name, value in defaults.items():
            if name not in self.player:
                self.player[name] = value

        for key in self.VILLAINS:
            var_name = f"{key}_played"
            if var_name not in self.player:
                self.player[var_name] = 0

    def _get_current_chapter(self):
        chapter_num = int(self.player["villain_chapter"])
        index = max(0, chapter_num - 1)
        if index >= len(self.CHAPTERS):
            return None
        return self.CHAPTERS[index]

    def _get_available_villains(self, limit=None):
        chapter_num = int(self.player["villain_chapter"])
        available = []

        for key, info in self.VILLAINS.items():
            if int(info.get("tier", 1)) > chapter_num:
                continue
            if self.player[f"{key}_played"] == 1:
                continue
            available.append(key)

        if limit is not None:
            return available[:int(limit)]
        return available

    def _post_available_choices(self, max_choices=5, **kwargs):
        available = self._get_available_villains(limit=max_choices)
        self.machine.events.post(
            "villain_progression_choices_ready",
            max_choices=max_choices,
            available_count=len(available),
            villain_keys=",".join(available),
        )

    def _start_default_villain(self, **kwargs):
        available = self._get_available_villains(limit=1)
        if not available:
            self.machine.events.post("no_villains_available")
            return
        self._start_villain(available[0])

    def _start_selected_villain(self, villain_key=None, **kwargs):
        if not villain_key:
            self.machine.events.post("villain_selection_missing")
            return
        if villain_key not in self.VILLAINS:
            self.machine.events.post("villain_selection_invalid", villain_key=villain_key)
            return
        if self.player[f"{villain_key}_played"] == 1:
            self.machine.events.post("villain_selection_already_played", villain_key=villain_key)
            return
        self._start_villain(villain_key)

    def _start_villain(self, villain_key):
        info = self.VILLAINS[villain_key]
        self.player["villain_current_key"] = villain_key

        self.machine.events.post(
            "villain_about_to_start",
            villain_key=villain_key,
            villain_name=info["name"],
        )

        self.machine.events.post(info["start_event"])

        self.machine.events.post(
            "villain_mode_started",
            villain_key=villain_key,
            villain_name=info["name"],
        )

    def _villain_played(self, villain_key=None, **kwargs):
        if not villain_key:
            villain_key = self.player["villain_current_key"]

        if not villain_key or villain_key not in self.VILLAINS:
            self.machine.events.post("villain_played_invalid", villain_key=villain_key)
            return

        if self.player[f"{villain_key}_played"] == 0:
            self.player[f"{villain_key}_played"] = 1
            self.player["villains_played_this_chapter"] += 1
            self.player["villains_played_total"] += 1

        self.machine.events.post(
            "villain_marked_played",
            villain_key=villain_key,
            villain_name=self.VILLAINS[villain_key]["name"],
            villains_played_this_chapter=self.player["villains_played_this_chapter"],
        )

        self._check_chapter_complete()
        self._restore_state()

    def _check_chapter_complete(self):
        chapter = self._get_current_chapter()
        if chapter is None:
            self.player["final_wizard_ready"] = 1
            self.machine.events.post("final_wizard_ready")
            return

        required = int(chapter["villain_count_required"])
        if self.player["villains_played_this_chapter"] >= required:
            self.player["chapter_mini_wizard_ready"] = 1
            self.machine.events.post(
                "chapter_mini_wizard_ready",
                chapter=chapter["key"],
                chapter_name=chapter["name"],
                mini_wizard_event=chapter["mini_wizard_event"],
            )

    def _mini_wizard_completed(self, **kwargs):
        self.player["chapter_mini_wizard_ready"] = 0
        self.player["villains_played_this_chapter"] = 0
        self.player["villain_chapter"] += 1

        if self._get_current_chapter() is None:
            self.player["final_wizard_ready"] = 1
            self.machine.events.post("final_wizard_ready")
        else:
            chapter = self._get_current_chapter()
            self.machine.events.post(
                "villain_chapter_started",
                chapter=chapter["key"],
                chapter_name=chapter["name"],
                chapter_number=self.player["villain_chapter"],
            )

        self._restore_state()

    def _restore_state(self, **kwargs):
        available = self._get_available_villains()
        chapter = self._get_current_chapter()

        self.machine.events.post(
            "villain_progression_status",
            chapter_number=self.player["villain_chapter"],
            chapter_name=chapter["name"] if chapter else "Final Wizard",
            villains_played_this_chapter=self.player["villains_played_this_chapter"],
            available_count=len(available),
            mini_wizard_ready=self.player["chapter_mini_wizard_ready"],
            final_wizard_ready=self.player["final_wizard_ready"],
        )
