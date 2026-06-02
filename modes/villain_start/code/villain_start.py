from mpf.core.mode import Mode


class VillainStart(Mode):
    """Saucer decision system.

    Saucer state decides:
    0 = points only
    1 = start default next villain
    2-5 = start carousel/select unless only one valid villain remains

    This mode also routes ready saucers to mini-wizard/final wizard when applicable.
    """

    SAUCERS = ["left", "center", "right"]

    # Keep this list synchronized with villain_progression.py.
    # This copy is used only to count available choices for saucer decisions.
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
        self._add_handlers()

    def mode_stop(self, **kwargs):
        self.villain_start_logic_active = False
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("left_villain_saucer_hit", self._saucer_hit, saucer="left")
        self.add_mode_event_handler("center_villain_saucer_hit", self._saucer_hit, saucer="center")
        self.add_mode_event_handler("right_villain_saucer_hit", self._saucer_hit, saucer="right")

    def _saucer_hit(self, saucer=None, **kwargs):
        if not self.villain_start_logic_active or saucer not in self.SAUCERS:
            return

        state = int(self.player[f"{saucer}_saucer_state"])

        if self._player_var("final_wizard_ready") == 1:
            self.machine.events.post("villain_saucer_start_final_wizard", saucer=saucer)
            self.machine.events.post("start_mode_final_wizard_kingpin")
            return

        if self._player_var("chapter_mini_wizard_ready") == 1:
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
            self.machine.events.post(
                "villain_saucer_start_default",
                saucer=saucer,
                state=state,
                villain_key=available[0],
            )
            self.machine.events.post("villain_progression_start_selected", villain_key=available[0])
            return

        self.machine.events.post(
            "villain_saucer_start_select",
            saucer=saucer,
            state=state,
            max_choices=state,
            villain_keys=",".join(available),
        )

        # Your carousel mode can use this event to build/display only these choices.
        self.machine.events.post(
            "start_mode_villain_select",
            max_choices=state,
            villain_keys=",".join(available),
        )

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
