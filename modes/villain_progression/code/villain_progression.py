from mpf.core.mode import Mode


class VillainProgression(Mode):
    """Single source of truth for villain chapters, states, and launches.

    Other modes should not keep their own villain lists or start villain modes
    directly. The intended flow is:

        villain_start.py decides that a physical shot is allowed to request a start
        villain_progression.py decides what that request means
        villain_select.py only shows/returns a selected key when choices are needed
        villain_progression.py starts the selected/default villain through bookends

    State wording is also prepared for a future Godot chapter widget:
        NOT PLAYED, PLAYING, COMPLETED
    """

    NOT_PLAYED = "NOT PLAYED"
    PLAYING = "PLAYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    READY = "READY"
    LIT = "LIT"

    CHAPTERS = [
        {
            "key": "classic_rogues",
            "name": "Classic Rogues",
            "villains": ["rhino", "vulture", "lizard", "sandman", "electro"],
            "mini_wizard_key": "sinister_surge",
            "mini_wizard_name": "Sinister Surge",
            "mini_wizard_event": "start_mode_sinister_surge",
        },
        {
            "key": "masterminds",
            "name": "Masterminds",
            "villains": ["doc_ock", "mysterio", "goblin", "scorpion", "parafino"],
            "mini_wizard_key": "master_plan",
            "mini_wizard_name": "Master Plan",
            "mini_wizard_event": "start_mode_master_plan",
        },
        {
            "key": "monsters",
            "name": "Monsters",
            "villains": ["centaur", "cerberus", "cyclops", "reptilla", "mole_man"],
            "mini_wizard_key": "monster_island",
            "mini_wizard_name": "Monster Island",
            "mini_wizard_event": "start_mode_monster_island",
        },
        {
            "key": "crime_wave",
            "name": "Crime Wave",
            "villains": ["enforcers", "ox", "fifth_avenue_phantom", "frederick_foswell", "blackwell"],
            "mini_wizard_key": "crime_wave_mini",
            "mini_wizard_name": "Crime Wave",
            "mini_wizard_event": "start_mode_crime_wave_mini",
        },
    ]

    VILLAINS = {
        "rhino": {"name": "Rhino", "chapter": 1, "start_event": "start_mode_rhino_bash"},
        "vulture": {"name": "Vulture", "chapter": 1, "start_event": "start_mode_vulture"},
        "lizard": {"name": "Lizard", "chapter": 1, "start_event": "start_mode_lizard"},
        "sandman": {"name": "Sandman", "chapter": 1, "start_event": "start_mode_sandman"},
        "electro": {"name": "Electro", "chapter": 1, "start_event": "start_mode_electro"},
        "doc_ock": {"name": "Doctor Octopus", "chapter": 2, "start_event": "start_mode_doc_ock"},
        "mysterio": {"name": "Mysterio", "chapter": 2, "start_event": "start_mode_mysterio"},
        "goblin": {"name": "Green Goblin", "chapter": 2, "start_event": "start_mode_goblin"},
        "scorpion": {"name": "Scorpion", "chapter": 2, "start_event": "start_mode_scorpion"},
        "parafino": {"name": "Parafino", "chapter": 2, "start_event": "start_mode_parafino"},
        "centaur": {"name": "Centaur", "chapter": 3, "start_event": "start_mode_centaur"},
        "cerberus": {"name": "Cerberus", "chapter": 3, "start_event": "start_mode_cerberus"},
        "cyclops": {"name": "Cyclops", "chapter": 3, "start_event": "start_mode_cyclops"},
        "reptilla": {"name": "Reptilla", "chapter": 3, "start_event": "start_mode_reptilla"},
        "mole_man": {"name": "Mole Man", "chapter": 3, "start_event": "start_mode_mole_man"},
        "enforcers": {"name": "Enforcers", "chapter": 4, "start_event": "start_mode_enforcers"},
        "ox": {"name": "Ox", "chapter": 4, "start_event": "start_mode_ox"},
        "fifth_avenue_phantom": {"name": "Fifth Avenue Phantom", "chapter": 4, "start_event": "start_mode_fifth_avenue_phantom"},
        "frederick_foswell": {"name": "Frederick Foswell", "chapter": 4, "start_event": "start_mode_frederick_foswell"},
        "blackwell": {"name": "Blackwell", "chapter": 4, "start_event": "start_mode_blackwell"},
    }

    FINAL_WIZARD_KEY = "kingpin"
    FINAL_WIZARD_NAME = "Kingpin"
    FINAL_WIZARD_EVENT = "start_mode_kingpin"

    # These are the events posted by the individual villain modes when their
    # gameplay is finished. Progression owns the next step: mark state, stop the
    # gameplay mode, then ask villain_bookends to show the summary.
    COMPLETION_EVENTS = {
        "rhino_bash_complete": ("rhino", True),
        "rhino_mode_complete": ("rhino", True),
        "sandman_mode_complete": ("sandman", True),
        "vulture_mode_complete": ("vulture", True),
        "lizard_mode_complete": ("lizard", True),
        "lizard_mode_failed": ("lizard", False),
        "electro_mode_complete": ("electro", True),
        "electro_mode_failed": ("electro", False),
        "doc_ock_mode_complete": ("doc_ock", True),
        "mysterio_mode_complete": ("mysterio", True),
        "goblin_mode_complete": ("goblin", True),
        "goblin_mode_failed": ("goblin", False),
        "scorpion_mode_complete": ("scorpion", True),
        "parafino_mode_complete": ("parafino", True),
        "parafino_mode_failed": ("parafino", False),
        "centaur_mode_complete": ("centaur", True),
        "centaur_mode_failed": ("centaur", False),
        "cerberus_mode_complete": ("cerberus", True),
        "cerberus_mode_failed": ("cerberus", False),
        "cyclops_mode_complete": ("cyclops", True),
        "cyclops_mode_failed": ("cyclops", False),
        "reptilla_mode_complete": ("reptilla", True),
        "reptilla_mode_failed": ("reptilla", False),
        "mole_man_mode_complete": ("mole_man", True),
        "mole_man_mode_failed": ("mole_man", False),
        "enforcers_mode_complete": ("enforcers", True),
        "enforcers_mode_failed": ("enforcers", False),
        "ox_mode_complete": ("ox", True),
        "ox_mode_failed": ("ox", False),
        "fifth_avenue_phantom_mode_complete": ("fifth_avenue_phantom", True),
        "fifth_avenue_phantom_mode_failed": ("fifth_avenue_phantom", False),
        "frederick_foswell_mode_complete": ("frederick_foswell", True),
        "frederick_foswell_mode_failed": ("frederick_foswell", False),
        "blackwell_mode_complete": ("blackwell", True),
        "blackwell_mode_failed": ("blackwell", False),
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
        # Public API for the rest of the game.
        self.add_mode_event_handler("villain_progression_request_start", self._request_start)
        self.add_mode_event_handler("villain_progression_request_choices", self._post_available_choices)
        self.add_mode_event_handler("villain_progression_start_default", self._start_default_villain)
        self.add_mode_event_handler("villain_progression_start_selected", self._start_selected_villain)
        self.add_mode_event_handler("villain_select_choice_made", self._start_selected_villain)
        self.add_mode_event_handler("villain_progression_start_final_wizard", self._start_final_wizard)
        self.add_mode_event_handler("villain_progression_restore_state", self._restore_state)

        # Completion / wizard flow.
        for event_name, finish_info in self.COMPLETION_EVENTS.items():
            villain_key, completed = finish_info
            self.add_mode_event_handler(
                event_name,
                self._villain_mode_finished,
                villain_key=villain_key,
                completed=completed,
            )

        # Legacy manual completion hook. Prefer the concrete events above for
        # real gameplay modes.
        self.add_mode_event_handler("villain_played", self._villain_completed)
        self.add_mode_event_handler("villain_bookend_summary_done", self._summary_done)
        self.add_mode_event_handler("chapter_mini_wizard_completed", self._mini_wizard_completed)
        self.add_mode_event_handler("mini_wizard_start_ready_at_daily_bugle", self._mini_wizard_ready_at_daily_bugle)
        self.add_mode_event_handler("s_vuk_switch_active", self._daily_bugle_hit)

    def _ensure_player_vars(self):
        defaults = {
            "villain_chapter": 1,
            "villains_played_this_chapter": 0,
            "villains_played_total": 0,
            "chapter_mini_wizard_ready": 0,
            "mini_wizard_daily_bugle_ready": 0,
            "final_wizard_ready": 0,
            "villain_current_key": "",
            "villain_current_name": "",
            "villain_mode_running": 0,
            "villain_mode_running_name": "",
            "villain_mode_in_summary": 0,
            "mini_wizard_current_key": "",
            "mini_wizards_completed": 0,
            "final_wizard_state": self.NOT_PLAYED,
        }
        for name, value in defaults.items():
            if name not in self.machine.game.player:
                self.machine.game.player[name] = value

        for key in self.VILLAINS:
            if f"{key}_played" not in self.machine.game.player:
                self.machine.game.player[f"{key}_played"] = 0
            if f"{key}_completed" not in self.machine.game.player:
                self.machine.game.player[f"{key}_completed"] = 0
            if f"{key}_state" not in self.machine.game.player:
                self.machine.game.player[f"{key}_state"] = self.NOT_PLAYED

        for chapter in self.CHAPTERS:
            mini_key = chapter["mini_wizard_key"]
            if f"{mini_key}_completed" not in self.machine.game.player:
                self.machine.game.player[f"{mini_key}_completed"] = 0
            if f"{mini_key}_state" not in self.machine.game.player:
                self.machine.game.player[f"{mini_key}_state"] = self.NOT_PLAYED

    def _request_start(self, saucer=None, state=0, max_choices=None, source="", **kwargs):
        """Handle a villain start request from a physical shot.

        villain_start.py should call this instead of deciding chapter contents or
        starting villains itself.
        """
        state = self._safe_int(state, 0)
        if max_choices is None:
            max_choices = state
        max_choices = self._safe_int(max_choices, state)

        if self._safe_int(self.machine.game.player["final_wizard_ready"], 0) == 1:
            self.machine.events.post("villain_saucer_start_final_wizard", saucer=saucer, source=source)
            self._start_final_wizard()
            return

        if self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) == 1:
            self.machine.events.post("villain_saucer_lights_daily_bugle_for_mini_wizard", saucer=saucer, source=source)
            self._mini_wizard_ready_at_daily_bugle()
            return

        if state <= 0:
            self.machine.events.post("villain_saucer_points_only", saucer=saucer, source=source)
            return

        available = self._get_available_villains(limit=max_choices)
        if not available:
            self.machine.events.post("villain_saucer_no_valid_villains", saucer=saucer, state=state, source=source)
            self.machine.events.post("villain_start_request_failed", saucer=saucer, reason="no_valid_villains")
            self._check_chapter_complete()
            return

        if len(available) == 1:
            villain_key = available[0]
            self.machine.events.post(
                "villain_saucer_start_default",
                saucer=saucer,
                state=state,
                villain_key=villain_key,
                source=source,
            )
            self._start_villain(villain_key)
            return

        self.machine.events.post(
            "villain_saucer_start_select",
            saucer=saucer,
            state=state,
            max_choices=max_choices,
            villain_keys=",".join(available),
            source=source,
        )
        self.machine.events.post(
            "start_mode_villain_select",
            max_choices=max_choices,
            villain_keys=",".join(available),
        )

    def _get_current_chapter(self):
        chapter_num = self._safe_int(self.machine.game.player["villain_chapter"], 1)
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
            if self._villain_state(key) == self.NOT_PLAYED:
                available.append(key)

        if limit is not None:
            return available[:self._safe_int(limit, len(available))]
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
            self.machine.events.post("villain_start_request_failed", reason="no_villains_available")
            return
        self._start_villain(available[0])

    def _start_selected_villain(self, villain_key=None, item=None, **kwargs):
        villain_key = villain_key or item
        if not villain_key:
            self.machine.events.post("villain_selection_missing")
            self.machine.events.post("villain_start_request_failed", reason="missing_villain_key")
            return
        if villain_key not in self.VILLAINS:
            self.machine.events.post("villain_selection_invalid", villain_key=villain_key)
            self.machine.events.post("villain_start_request_failed", reason="invalid_villain_key")
            return
        if villain_key not in self._get_available_villains():
            self.machine.events.post("villain_selection_already_played", villain_key=villain_key)
            self.machine.events.post("villain_start_request_failed", reason="already_played", villain_key=villain_key)
            return
        self._start_villain(villain_key)

    def _start_villain(self, villain_key):
        info = self.VILLAINS[villain_key]

        # Set both the new state vars and the older *_played vars. The played
        # bit means "do not offer this villain again." Completion is tracked
        # separately with *_completed and *_state == COMPLETED.
        self.machine.game.player[f"{villain_key}_played"] = 1
        self.machine.game.player[f"{villain_key}_state"] = self.PLAYING
        self.machine.game.player["villain_current_key"] = villain_key
        self.machine.game.player["villain_current_name"] = villain_key
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_mode_running_name"] = villain_key

        self.info_log("VILLAIN START: %s state=%s played=%s", villain_key, self.machine.game.player[f"{villain_key}_state"], self.machine.game.player[f"{villain_key}_played"])

        self.machine.events.post("clear_villain_saucer_lights")
        self.machine.events.post("clear_saucers")
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
        self._restore_state()

    def _villain_mode_finished(self, villain_key=None, completed=True, **kwargs):
        """Finish gameplay immediately, then show the bookend summary.

        The old flow let each villain mode keep running until its summary was
        dismissed. This method makes the summary a separate bookend step:
        complete/fail event -> stop gameplay mode -> show summary -> cleanup.
        """
        if not villain_key:
            villain_key = self.machine.game.player["villain_current_key"]
        if not villain_key or villain_key not in self.VILLAINS:
            self.machine.events.post("villain_finish_invalid", villain_key=villain_key)
            return

        completed = bool(completed)
        finish_state = self.COMPLETED if completed else self.FAILED

        self.machine.game.player[f"{villain_key}_completed"] = 1 if completed else 0
        self.machine.game.player[f"{villain_key}_played"] = 1
        self.machine.game.player[f"{villain_key}_state"] = finish_state

        # Keep villain_mode_running locked through the summary. The gameplay
        # mode itself is stopping now, but saucer starts / qualify drops should
        # stay blocked until villain_bookends finishes the summary.
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_mode_in_summary"] = 1
        self.machine.game.player["villain_current_key"] = villain_key
        self.machine.game.player["villain_current_name"] = villain_key
        self.machine.game.player["villain_mode_running_name"] = villain_key

        self.machine.events.post(
            "villain_gameplay_finished",
            villain_key=villain_key,
            villain_name=self.VILLAINS[villain_key]["name"],
            completed=1 if completed else 0,
            state=finish_state,
        )

        # Ask MPF to stop the active gameplay mode now. The mode YAML also has
        # the concrete complete/fail events in stop_events, but this keeps the
        # behavior explicit from the single progression pipeline.
        self.machine.events.post(f"stop_mode_{villain_key}")

        # Let mode_stop/widget/show cleanup happen before the summary widget is
        # displayed. This prevents gameplay lights/shows from overlapping the
        # bookend summary.
        self.delay.add(
            name=f"{villain_key}_summary_after_mode_stop",
            ms=100,
            callback=lambda: self._request_summary(villain_key),
        )

        self._check_chapter_complete()
        self._restore_state()

    def _request_summary(self, villain_key):
        self.machine.events.post(
            "villain_bookend_summary_request",
            villain=villain_key,
            done_event=f"{villain_key}_mode_completed_summary",
        )

    def _summary_done(self, villain=None, **kwargs):
        """Release the villain lock after the bookend summary is finished.

        Gameplay modes are already stopped before the summary is shown. This is
        the one official point where case files, saucers, drops, and qualify
        state are reset and the saucer/start system is unlocked again.
        """
        player = self.machine.game.player if self.machine.game else None

        if player:
            player["villain_mode_running"] = 0
            player["villain_mode_in_summary"] = 0
            player["villain_current_key"] = ""
            player["villain_current_name"] = ""
            player["villain_mode_running_name"] = ""

        self.machine.events.post("villain_full_cleanup", villain_key=villain, villain=villain)
        self.machine.events.post("villain_summary_cleanup_complete", villain_key=villain, villain=villain)
        self.machine.events.post("villain_mode_ended", villain_key=villain, villain=villain)
        self._restore_state()

    def _villain_completed(self, villain_key=None, **kwargs):
        # Compatibility hook for anything that still posts villain_played.
        self._villain_mode_finished(villain_key=villain_key, completed=True, **kwargs)

    def _check_chapter_complete(self):
        chapter = self._get_current_chapter()
        if chapter is None:
            self.machine.game.player["final_wizard_ready"] = 1
            self.machine.game.player["final_wizard_state"] = self.READY
            self.machine.events.post("final_wizard_ready")
            return

        resolved_count = 0
        for key in chapter["villains"]:
            if self._villain_state(key) in (self.COMPLETED, self.FAILED):
                resolved_count += 1

        self.machine.game.player["villains_played_this_chapter"] = resolved_count
        required = len(chapter["villains"])
        if resolved_count >= required:
            mini_key = chapter["mini_wizard_key"]
            if self._safe_int(self.machine.game.player[f"{mini_key}_completed"], 0) == 0:
                self.machine.game.player["chapter_mini_wizard_ready"] = 1
                self.machine.game.player["mini_wizard_daily_bugle_ready"] = 0
                self.machine.game.player[f"{mini_key}_state"] = self.READY
                self.machine.events.post(
                    "chapter_mini_wizard_ready",
                    chapter=chapter["key"],
                    chapter_name=chapter["name"],
                    mini_wizard_key=mini_key,
                    mini_wizard_name=chapter["mini_wizard_name"],
                    mini_wizard_event=chapter["mini_wizard_event"],
                )

    def _mini_wizard_ready_at_daily_bugle(self, **kwargs):
        if self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) != 1:
            return
        chapter = self._get_current_chapter()
        if not chapter:
            return
        mini_key = chapter["mini_wizard_key"]
        self.machine.game.player["mini_wizard_daily_bugle_ready"] = 1
        self.machine.game.player[f"{mini_key}_state"] = self.LIT
        self.machine.events.post(
            "chapter_mini_wizard_lit_at_daily_bugle",
            chapter=chapter["key"],
            chapter_name=chapter["name"],
            mini_wizard_key=mini_key,
            mini_wizard_name=chapter["mini_wizard_name"],
        )
        self._restore_state()

    def _daily_bugle_hit(self, **kwargs):
        if self._safe_int(self.machine.game.player["mini_wizard_daily_bugle_ready"], 0) != 1:
            return
        chapter = self._get_current_chapter()
        if not chapter:
            return
        mini_key = chapter["mini_wizard_key"]
        self.machine.game.player["mini_wizard_daily_bugle_ready"] = 0
        self.machine.game.player["mini_wizard_current_key"] = mini_key
        self.machine.game.player[f"{mini_key}_state"] = self.PLAYING
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_current_name"] = mini_key
        self.machine.game.player["villain_mode_running_name"] = mini_key
        self.machine.events.post(
            "chapter_mini_wizard_starting",
            chapter=chapter["key"],
            chapter_name=chapter["name"],
            mini_wizard_key=mini_key,
            mini_wizard_name=chapter["mini_wizard_name"],
        )
        self.machine.events.post(chapter["mini_wizard_event"])
        self._restore_state()

    def _mini_wizard_completed(self, mini_wizard=None, **kwargs):
        chapter = self._get_current_chapter()
        if not chapter:
            return

        mini_key = chapter["mini_wizard_key"]
        self.machine.game.player[f"{mini_key}_completed"] = 1
        self.machine.game.player[f"{mini_key}_state"] = self.COMPLETED
        self.machine.game.player["mini_wizards_completed"] += 1
        self.machine.game.player["chapter_mini_wizard_ready"] = 0
        self.machine.game.player["mini_wizard_daily_bugle_ready"] = 0
        self.machine.game.player["mini_wizard_current_key"] = ""
        self.machine.game.player["villain_mode_running"] = 0
        self.machine.game.player["villain_current_name"] = ""
        self.machine.game.player["villain_mode_running_name"] = ""
        self.machine.game.player["villains_played_this_chapter"] = 0
        self.machine.game.player["villain_chapter"] += 1

        if self._get_current_chapter() is None:
            self.machine.game.player["final_wizard_ready"] = 1
            self.machine.game.player["final_wizard_state"] = self.READY
            self.machine.events.post("final_wizard_ready")
        else:
            next_chapter = self._get_current_chapter()
            self.machine.events.post(
                "villain_chapter_started",
                chapter=next_chapter["key"],
                chapter_name=next_chapter["name"],
                chapter_number=self.machine.game.player["villain_chapter"],
            )
        self._restore_state()

    def _start_final_wizard(self, **kwargs):
        if self._safe_int(self.machine.game.player["final_wizard_ready"], 0) != 1:
            return
        self.machine.game.player["final_wizard_state"] = self.PLAYING
        self.machine.game.player["villain_current_key"] = self.FINAL_WIZARD_KEY
        self.machine.game.player["villain_current_name"] = self.FINAL_WIZARD_KEY
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_mode_running_name"] = self.FINAL_WIZARD_KEY
        self.machine.events.post("villain_started_set", villain_key=self.FINAL_WIZARD_KEY, villain=self.FINAL_WIZARD_KEY)
        self.machine.events.post(
            "villain_bookend_intro_request",
            villain=self.FINAL_WIZARD_KEY,
            start_event=self.FINAL_WIZARD_EVENT,
        )
        self._restore_state()

    def _restore_state(self, **kwargs):
        self._check_chapter_widget_vars()
        available = self._get_available_villains()
        chapter = self._get_current_chapter()
        self.machine.events.post(
            "villain_progression_status",
            chapter_number=self.machine.game.player["villain_chapter"],
            chapter_key=chapter["key"] if chapter else "final_wizard",
            chapter_name=chapter["name"] if chapter else "Final Wizard",
            villains_played_this_chapter=self.machine.game.player["villains_played_this_chapter"],
            available_count=len(available),
            villain_keys=",".join(available),
            mini_wizard_ready=self.machine.game.player["chapter_mini_wizard_ready"],
            mini_wizard_daily_bugle_ready=self.machine.game.player["mini_wizard_daily_bugle_ready"],
            final_wizard_ready=self.machine.game.player["final_wizard_ready"],
        )
        self.machine.events.post("villain_chapter_status_changed")

    def _check_chapter_widget_vars(self):
        chapter = self._get_current_chapter()
        if not chapter:
            self.machine.game.player["chapter_current_key"] = "final_wizard"
            self.machine.game.player["chapter_current_name"] = "Final Wizard"
            self.machine.game.player["chapter_mini_wizard_key"] = self.FINAL_WIZARD_KEY
            self.machine.game.player["chapter_mini_wizard_name"] = self.FINAL_WIZARD_NAME
            self.machine.game.player["chapter_mini_wizard_state"] = self.machine.game.player["final_wizard_state"]
            for index in range(1, 6):
                self.machine.game.player[f"chapter_villain_{index}_key"] = ""
                self.machine.game.player[f"chapter_villain_{index}_name"] = ""
                self.machine.game.player[f"chapter_villain_{index}_state"] = ""
            return

        self.machine.game.player["chapter_current_key"] = chapter["key"]
        self.machine.game.player["chapter_current_name"] = chapter["name"]
        self.machine.game.player["chapter_mini_wizard_key"] = chapter["mini_wizard_key"]
        self.machine.game.player["chapter_mini_wizard_name"] = chapter["mini_wizard_name"]
        self.machine.game.player["chapter_mini_wizard_state"] = self.machine.game.player[f"{chapter['mini_wizard_key']}_state"]

        for index, villain_key in enumerate(chapter["villains"], start=1):
            self.machine.game.player[f"chapter_villain_{index}_key"] = villain_key
            self.machine.game.player[f"chapter_villain_{index}_name"] = self.VILLAINS[villain_key]["name"]
            self.machine.game.player[f"chapter_villain_{index}_state"] = self._villain_state(villain_key)

    def _villain_state(self, villain_key):
        state = self._get_player_var(f"{villain_key}_state") 
        if state == None:   
            state = self.NOT_PLAYED        
        if state in (self.PLAYING, self.COMPLETED, self.FAILED):
            return state
        if self._safe_int(self._get_player_var(f"{villain_key}_completed", 0), 0) == 1:
            return self.COMPLETED
        if self._safe_int(self._get_player_var(f"{villain_key}_played", 0), 0) == 1:
            return self.FAILED
        return self.NOT_PLAYED

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _player(self):
        if not self.machine.game:
            return None
        return self.machine.game.player

    def _get_player_var(self, name, default=0):
        player = self._player()
        if not player:
            return default

        try:
            return player[name]
        except (KeyError, TypeError):
            return getattr(player, name, default)

    def _set_player_var(self, name, value):
        player = self._player()
        if not player:
            return

        try:
            player[name] = value
        except TypeError:
            setattr(player, name, value)

    def _add_player_var(self, name, amount):
        self._set_player_var(name, self._get_player_var(name, 0) + amount)
