from mpf.core.mode import Mode


class VillainStart(Mode):
    """Saucer decision system for the four-chapter campaign.

    Saucer state:
    0 = points only
    1 = start one available villain directly
    2-5 = start carousel/select unless only one valid villain remains

    Chapter groups:
    1 Classic Rogues: Rhino, Vulture, Lizard, Sandman, Electro
    2 Masterminds: Doc Ock, Mysterio, Goblin, Scorpion, Parafino
    3 Monsters: Centaur, Cerberus, Cyclops, Reptilla, Mole Man
    4 Crime Wave: Enforcers, Ox, Fifth Avenue Phantom, Frederick Foswell, Blackwell
    """

    SAUCERS = ["saucer_1", "saucer_2", "saucer_3"]
    CHAPTER_VILLAINS = {
        1: ['rhino', 'vulture', 'lizard', 'sandman', 'electro'],
        2: ['doc_ock', 'mysterio', 'goblin', 'scorpion', 'parafino'],
        3: ['centaur', 'cerberus', 'cyclops', 'reptilla', 'mole_man'],
        4: ['enforcers', 'ox', 'fifth_avenue_phantom', 'frederick_foswell', 'blackwell']
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.villain_start_logic_active = True
        self._ensure_player_vars()
        self._add_handlers()

    def mode_stop(self, **kwargs):
        self.villain_start_logic_active = False
        super().mode_stop(**kwargs)

    def _ensure_player_vars(self):
        defaults = {
            "villain_mode_running": 0,
            "villain_current_name": "",
            "villain_mode_running_name": "",
            "villain_chapter": 1,
            "chapter_mini_wizard_ready": 0,
            "final_wizard_ready": 0,
        }
        for name, value in defaults.items():
            if name not in self.player:
                self.player[name] = value

    def _add_handlers(self):
        self.add_mode_event_handler("saucer_1_hit", self._saucer_hit, saucer="saucer_1")
        self.add_mode_event_handler("saucer_2_hit", self._saucer_hit, saucer="saucer_2")
        self.add_mode_event_handler("saucer_3_hit", self._saucer_hit, saucer="saucer_3")
        self.add_mode_event_handler("villain_started_set", self._villain_started)
        self.add_mode_event_handler("villain_mode_started", self._villain_started)
        self.add_mode_event_handler("villain_mode_ended", self._villain_mode_ended)
        self.add_mode_event_handler("chapter_mini_wizard_completed", self._villain_mode_ended)

    def _villain_started(self, villain_key=None, villain_name=None, villain=None, **kwargs):
        key = villain_key or villain or villain_name or self._player_var("villain_current_name", "")
        self.villain_start_logic_active = False
        self.player["villain_mode_running"] = 1
        self.player["villain_current_name"] = key
        self.player["villain_mode_running_name"] = key
        self.machine.events.post("clear_villain_saucer_lights")
        self.machine.events.post("clear_saucers")

    def _villain_mode_ended(self, **kwargs):
        self.villain_start_logic_active = True
        self.player["villain_mode_running"] = 0
        self.player["villain_current_name"] = ""
        self.player["villain_mode_running_name"] = ""

    def _saucer_hit(self, saucer=None, **kwargs):
        if saucer not in self.SAUCERS:
            return
        if self._player_var("villain_mode_running") == 1:
            self.machine.events.post("villain_saucer_ignored_mode_running", saucer=saucer)
            return
        if not self.villain_start_logic_active:
            self.machine.events.post("villain_saucer_ignored_start_locked", saucer=saucer)
            return

        state = int(self._player_var(f"{saucer}_state", 0))

        if self._player_var("final_wizard_ready") == 1:
            self._lock_saucers_for_start("kingpin")
            self.machine.events.post("villain_saucer_start_final_wizard", saucer=saucer)
            self.machine.events.post("villain_progression_start_final_wizard")
            return

        if self._player_var("chapter_mini_wizard_ready") == 1:
            self._lock_saucers_for_start()
            self.machine.events.post("villain_saucer_lights_daily_bugle_for_mini_wizard", saucer=saucer)
            self.machine.events.post("mini_wizard_start_ready_at_daily_bugle")
            return

        if state <= 0:
            self.machine.events.post("villain_saucer_points_only", saucer=saucer)
            return

        available = self._get_available_villains(limit=state)
        if len(available) == 0:
            self.machine.events.post("villain_saucer_no_valid_villains", saucer=saucer, state=state)
            return

        if len(available) == 1:
            self._lock_saucers_for_start(villain_key=available[0])
            self.machine.events.post("villain_saucer_start_default", saucer=saucer, state=state, villain_key=available[0])
            self.machine.events.post("villain_progression_start_selected", villain_key=available[0])
            return

        self._lock_saucers_for_start()
        self.machine.events.post(
            "villain_saucer_start_select",
            saucer=saucer,
            state=state,
            max_choices=state,
            villain_keys=",".join(available),
        )
        self.machine.events.post(
            "start_mode_villain_select",
            max_choices=state,
            villain_keys=",".join(available),
        )

    def _lock_saucers_for_start(self, villain_key=""):
        self.villain_start_logic_active = False

        # Also block qualify/drop advancement while the select, mini-wizard,
        # or final-wizard launch pipeline is active. This gets cleared by
        # villain_mode_ended or chapter_mini_wizard_completed.
        lock_name = villain_key or "villain_select"
        self.player["villain_mode_running"] = 1
        self.player["villain_current_name"] = lock_name
        self.player["villain_mode_running_name"] = lock_name

        self.machine.events.post("clear_villain_saucer_lights")
        self.machine.events.post("clear_saucers")

    def _get_available_villains(self, limit=None):
        chapter = int(self._player_var("villain_chapter", 1))
        available = []
        for key in self.CHAPTER_VILLAINS.get(chapter, []):
            if self._player_var(f"{key}_played") == 1:
                continue
            available.append(key)
        if limit is not None:
            return available[:int(limit)]
        return available

    def _player_var(self, name, default=0):
        try:
            return self.player[name]
        except Exception:
            return default
