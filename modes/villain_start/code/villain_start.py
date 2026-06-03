from mpf.core.mode import Mode


class VillainStart(Mode):
    """Saucer decision system.

    saucer state:
    0 = points only
    1 = start one available villain directly
    2-5 = start carousel/select unless only one valid villain remains
    """

    SAUCERS = ["saucer_1", "saucer_2", "saucer_3"]

    VILLAIN_KEYS = [
        "rhino",
        "vulture",
        "lizard",
        "sandman",
        "electro",
        "doc_ock",
        "scorpion",
        "mysterio",
        "goblin",
        "parafino",
    ]

    VILLAIN_TIERS = {
        "rhino": 1,
        "vulture": 1,
        "lizard": 1,
        "sandman": 1,
        "electro": 1,
        "doc_ock": 2,
        "scorpion": 2,
        "mysterio": 2,
        "goblin": 2,
        "parafino": 2,
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
        }

        for name, value in defaults.items():
            if name not in self.player:
                self.player[name] = value

    def _add_handlers(self):
        self.add_mode_event_handler("saucer_1_hit", self._saucer_hit, saucer="saucer_1")
        self.add_mode_event_handler("saucer_2_hit", self._saucer_hit, saucer="saucer_2")
        self.add_mode_event_handler("saucer_3_hit", self._saucer_hit, saucer="saucer_3")

        # Either of these means saucers must stop accepting villain starts.
        self.add_mode_event_handler("villain_started_set", self._villain_started)
        self.add_mode_event_handler("villain_mode_started", self._villain_started)

        # Villain modes must post this when the mode is actually finished.
        self.add_mode_event_handler("villain_mode_ended", self._villain_mode_ended)

    def _villain_started(self, villain_key=None, villain_name=None, villain=None, **kwargs):
        key = villain_key or villain or villain_name or self.player.get("villain_current_name", "")

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

        # Hard block while a villain is active or while the start/select pipeline
        # has locked out saucer starts.
        if self._player_var("villain_mode_running") == 1:
            self.machine.events.post("villain_saucer_ignored_mode_running", saucer=saucer)
            return

        if not self.villain_start_logic_active:
            self.machine.events.post("villain_saucer_ignored_start_locked", saucer=saucer)
            return

        state = int(self.player[f"{saucer}_state"])

        if self._player_var("final_wizard_ready") == 1:
            self._lock_saucers_for_start()
            self.machine.events.post("villain_saucer_start_final_wizard", saucer=saucer)
            self.machine.events.post("start_mode_final_wizard_kingpin")
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

            self.machine.events.post(
                "villain_saucer_start_default",
                saucer=saucer,
                state=state,
                villain_key=available[0],
            )
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

        if villain_key:
            self.player["villain_mode_running"] = 1
            self.player["villain_current_name"] = villain_key
            self.player["villain_mode_running_name"] = villain_key

        self.machine.events.post("clear_villain_saucer_lights")
        self.machine.events.post("clear_saucers")

    def _get_available_villains(self, limit=None):
        chapter = self._player_var("villain_chapter", default=1)
        available = []

        for key in self.VILLAIN_KEYS:
            if self.VILLAIN_TIERS.get(key, 1) > chapter:
                continue
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
