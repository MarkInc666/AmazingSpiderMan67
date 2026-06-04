from mpf.core.mode import Mode


class VillainProgression(Mode):
    """Four-chapter villain progression engine.

    Campaign structure:
    1. Classic Rogues: Rhino, Vulture, Lizard, Sandman, Electro
       Mini-wizard: Sinister Surge
    2. Masterminds: Doctor Octopus, Mysterio, Green Goblin, Scorpion, Parafino
       Mini-wizard: Master Plan
    3. Monsters: Centaur, Cerberus, Cyclops, Reptilla, Mole Man
       Mini-wizard: Monster Island
    4. Crime Wave: Enforcers, Ox, Fifth Avenue Phantom, Frederick Foswell, Blackwell
       Mini-wizard: Crime Wave

    After the four mini-wizards are completed, Kingpin is ready as the final wizard.
    """

    CHAPTERS = [{'key': 'classic_rogues', 'name': 'Classic Rogues', 'villains': ['rhino', 'vulture', 'lizard', 'sandman', 'electro'], 'mini_wizard_key': 'sinister_surge', 'mini_wizard_event': 'start_mode_sinister_surge'},
        {'key': 'masterminds', 'name': 'Masterminds', 'villains': ['doc_ock', 'mysterio', 'goblin', 'scorpion', 'parafino'], 'mini_wizard_key': 'master_plan', 'mini_wizard_event': 'start_mode_master_plan'},
        {'key': 'monsters', 'name': 'Monsters', 'villains': ['centaur', 'cerberus', 'cyclops', 'reptilla', 'mole_man'], 'mini_wizard_key': 'monster_island', 'mini_wizard_event': 'start_mode_monster_island'},
        {'key': 'crime_wave', 'name': 'Crime Wave', 'villains': ['enforcers', 'ox', 'fifth_avenue_phantom', 'frederick_foswell', 'blackwell'], 'mini_wizard_key': 'crime_wave_mini', 'mini_wizard_event': 'start_mode_crime_wave_mini'}]

    VILLAINS = {
        'rhino': {'name': 'Rhino', 'chapter': 1, 'start_event': 'start_mode_rhino_bash'},
        'vulture': {'name': 'Vulture', 'chapter': 1, 'start_event': 'start_mode_vulture'},
        'lizard': {'name': 'Lizard', 'chapter': 1, 'start_event': 'start_mode_lizard'},
        'sandman': {'name': 'Sandman', 'chapter': 1, 'start_event': 'start_mode_sandman'},
        'electro': {'name': 'Electro', 'chapter': 1, 'start_event': 'start_mode_electro'},
        'doc_ock': {'name': 'Doctor Octopus', 'chapter': 2, 'start_event': 'start_mode_doc_ock'},
        'mysterio': {'name': 'Mysterio', 'chapter': 2, 'start_event': 'start_mode_mysterio'},
        'goblin': {'name': 'Green Goblin', 'chapter': 2, 'start_event': 'start_mode_goblin'},
        'scorpion': {'name': 'Scorpion', 'chapter': 2, 'start_event': 'start_mode_scorpion'},
        'parafino': {'name': 'Parafino', 'chapter': 2, 'start_event': 'start_mode_parafino'},
        'centaur': {'name': 'Centaur', 'chapter': 3, 'start_event': 'start_mode_centaur'},
        'cerberus': {'name': 'Cerberus', 'chapter': 3, 'start_event': 'start_mode_cerberus'},
        'cyclops': {'name': 'Cyclops', 'chapter': 3, 'start_event': 'start_mode_cyclops'},
        'reptilla': {'name': 'Reptilla', 'chapter': 3, 'start_event': 'start_mode_reptilla'},
        'mole_man': {'name': 'Mole Man', 'chapter': 3, 'start_event': 'start_mode_mole_man'},
        'enforcers': {'name': 'Enforcers', 'chapter': 4, 'start_event': 'start_mode_enforcers'},
        'ox': {'name': 'Ox', 'chapter': 4, 'start_event': 'start_mode_ox'},
        'fifth_avenue_phantom': {'name': 'Fifth Avenue Phantom', 'chapter': 4, 'start_event': 'start_mode_fifth_avenue_phantom'},
        'frederick_foswell': {'name': 'Frederick Foswell', 'chapter': 4, 'start_event': 'start_mode_frederick_foswell'},
        'blackwell': {'name': 'Blackwell', 'chapter': 4, 'start_event': 'start_mode_blackwell'}
    }

    FINAL_WIZARD_KEY = "kingpin"
    FINAL_WIZARD_EVENT = "start_mode_kingpin"

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
        self.add_mode_event_handler("villain_mode_ended", self._villain_mode_ended)
        self.add_mode_event_handler("chapter_mini_wizard_completed", self._mini_wizard_completed)
        self.add_mode_event_handler("villain_progression_restore_state", self._restore_state)
        self.add_mode_event_handler("villain_progression_start_default", self._start_default_villain)
        self.add_mode_event_handler("villain_progression_start_selected", self._start_selected_villain)
        self.add_mode_event_handler("villain_progression_request_choices", self._post_available_choices)
        self.add_mode_event_handler("mini_wizard_start_ready_at_daily_bugle", self._mini_wizard_ready_at_daily_bugle)
        self.add_mode_event_handler("s_vuk_switch_active", self._daily_bugle_hit)
        self.add_mode_event_handler("villain_progression_start_final_wizard", self._start_final_wizard)

    def _ensure_player_vars(self):
        defaults = {
            "villain_chapter": 1,
            "villains_played_this_chapter": 0,
            "villains_played_total": 0,
            "chapter_mini_wizard_ready": 0,
            "mini_wizard_daily_bugle_ready": 0,
            "final_wizard_ready": 0,
            "villain_current_key": "",
            "mini_wizard_current_key": "",
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
        index = chapter_num - 1
        if index < 0 or index >= len(self.CHAPTERS):
            return None
        return self.CHAPTERS[index]

    def _get_available_villains(self, limit=None):
        chapter = self._get_current_chapter()
        if not chapter:
            return []
        available = []
        for key in chapter["villains"]:
            if self.player[f"{key}_played"] == 0:
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
        self.player["villain_current_name"] = villain_key
        self.player["villain_mode_running"] = 1
        self.player["villain_mode_running_name"] = villain_key

        self.machine.events.post("villain_started_set", villain_key=villain_key, villain=villain_key)
        self.machine.events.post(
            "villain_mode_started",
            villain_key=villain_key,
            villain_name=info["name"],
        )
        self.machine.events.post(
            "villain_bookend_intro_request",
            villain=villain_key,
            start_event=info["start_event"],
        )

    def _villain_mode_ended(self, villain_key=None, **kwargs):
        # The bookend summary posts villain_mode_ended after each villain summary.
        self._villain_played(villain_key=villain_key)

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
        required = len(chapter["villains"])
        if self.player["villains_played_this_chapter"] >= required:
            self.player["chapter_mini_wizard_ready"] = 1
            self.player["mini_wizard_daily_bugle_ready"] = 0
            self.machine.events.post(
                "chapter_mini_wizard_ready",
                chapter=chapter["key"],
                chapter_name=chapter["name"],
                mini_wizard_key=chapter["mini_wizard_key"],
                mini_wizard_event=chapter["mini_wizard_event"],
            )

    def _mini_wizard_ready_at_daily_bugle(self, **kwargs):
        if self.player["chapter_mini_wizard_ready"] != 1:
            return
        chapter = self._get_current_chapter()
        if not chapter:
            return
        self.player["mini_wizard_daily_bugle_ready"] = 1
        self.machine.events.post(
            "chapter_mini_wizard_lit_at_daily_bugle",
            chapter=chapter["key"],
            chapter_name=chapter["name"],
            mini_wizard_key=chapter["mini_wizard_key"],
        )

    def _daily_bugle_hit(self, **kwargs):
        if self.player["mini_wizard_daily_bugle_ready"] != 1:
            return
        chapter = self._get_current_chapter()
        if not chapter:
            return
        self.player["mini_wizard_daily_bugle_ready"] = 0
        self.player["mini_wizard_current_key"] = chapter["mini_wizard_key"]
        self.machine.events.post(
            "chapter_mini_wizard_starting",
            chapter=chapter["key"],
            chapter_name=chapter["name"],
            mini_wizard_key=chapter["mini_wizard_key"],
        )
        self.machine.events.post(chapter["mini_wizard_event"])

    def _mini_wizard_completed(self, mini_wizard=None, **kwargs):
        chapter = self._get_current_chapter()
        if not chapter:
            return
        self.player[f"{chapter['mini_wizard_key']}_completed"] = 1
        self.player["chapter_mini_wizard_ready"] = 0
        self.player["mini_wizard_daily_bugle_ready"] = 0
        self.player["mini_wizard_current_key"] = ""
        self.player["villains_played_this_chapter"] = 0
        self.player["villain_chapter"] += 1
        if self._get_current_chapter() is None:
            self.player["final_wizard_ready"] = 1
            self.machine.events.post("final_wizard_ready")
        else:
            next_chapter = self._get_current_chapter()
            self.machine.events.post(
                "villain_chapter_started",
                chapter=next_chapter["key"],
                chapter_name=next_chapter["name"],
                chapter_number=self.player["villain_chapter"],
            )
        self._restore_state()

    def _start_final_wizard(self, **kwargs):
        if self.player["final_wizard_ready"] != 1:
            return
        self.player["villain_current_key"] = self.FINAL_WIZARD_KEY
        self.player["villain_current_name"] = self.FINAL_WIZARD_KEY
        self.player["villain_mode_running"] = 1
        self.player["villain_mode_running_name"] = self.FINAL_WIZARD_KEY
        self.machine.events.post("villain_started_set", villain_key=self.FINAL_WIZARD_KEY)
        self.machine.events.post(
            "villain_bookend_intro_request",
            villain=self.FINAL_WIZARD_KEY,
            start_event=self.FINAL_WIZARD_EVENT,
        )

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
            mini_wizard_daily_bugle_ready=self.player["mini_wizard_daily_bugle_ready"],
            final_wizard_ready=self.player["final_wizard_ready"],
        )
