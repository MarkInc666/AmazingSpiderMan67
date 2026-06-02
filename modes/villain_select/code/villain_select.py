from mpf.core.mode import Mode


class VillainSelect(Mode):
    """Dynamic villain select carousel.

    This mode is intentionally not subclassing MPF's stock Carousel.
    Reason: this game needs a dynamic list of villains based on saucer state,
    chapter, already-played villains, and the event that started selection.

    Expected start event:
        start_mode_villain_select

    Expected kwargs from villain_start.py:
        villain_keys="rhino,vulture,lizard"
        max_choices=3

    Navigation:
        villain_select_next
        villain_select_previous
        villain_select_confirm
        villain_select_cancel

    Output:
        villain_select_highlighted
        villain_select_highlighted_<villain_key>
        villain_select_selected
        villain_progression_start_selected
    """

    VILLAINS = {
        "rhino": {
            "name": "Rhino",
            "display_name": "RHINO",
        },
        "vulture": {
            "name": "Vulture",
            "display_name": "VULTURE",
        },
        "lizard": {
            "name": "Lizard",
            "display_name": "LIZARD",
        },
        "sandman": {
            "name": "Sandman",
            "display_name": "SANDMAN",
        },
        "electro": {
            "name": "Electro",
            "display_name": "ELECTRO",
        },
        "doc_ock": {
            "name": "Doctor Octopus",
            "display_name": "DOC OCK",
        },
        "scorpion": {
            "name": "Scorpion",
            "display_name": "SCORPION",
        },
        "mysterio": {
            "name": "Mysterio",
            "display_name": "MYSTERIO",
        },
        "goblin": {
            "name": "Green Goblin",
            "display_name": "GOBLIN",
        },
        "parafino": {
            "name": "Parafino",
            "display_name": "PARAFINO",
        },
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.villain_select_logic_active = True
        self.valid_villains = []
        self.selected_index = 0
        self.max_choices = 5

        self._add_handlers()
        self._build_valid_list(**kwargs)

        if len(self.valid_villains) == 0:
            self.machine.events.post("villain_select_no_valid_villains")
            self._stop_self()
            return

        # If only one valid villain remains, do not force the player through a carousel.
        if len(self.valid_villains) == 1:
            villain_key = self.valid_villains[0]
            self.machine.events.post(
                "villain_select_only_one_choice",
                villain_key=villain_key,
                villain_name=self._villain_name(villain_key),
                display_name=self._villain_display_name(villain_key),
            )
            self._select_villain(villain_key)
            return

        self._post_status()
        self._highlight_current()

    def mode_stop(self, **kwargs):
        self.villain_select_logic_active = False
        self.machine.events.post("villain_select_stopped")
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("villain_select_next", self._next)
        self.add_mode_event_handler("villain_select_previous", self._previous)
        self.add_mode_event_handler("villain_select_confirm", self._confirm)
        self.add_mode_event_handler("villain_select_cancel", self._cancel)

    def _build_valid_list(self, villain_keys=None, max_choices=5, **kwargs):
        self.max_choices = self._safe_int(max_choices, default=5)

        requested_keys = self._parse_villain_keys(villain_keys)

        if not requested_keys:
            requested_keys = self._fallback_available_villains()

        valid = []
        for key in requested_keys:
            if key not in self.VILLAINS:
                self.machine.events.post("villain_select_ignored_unknown_villain", villain_key=key)
                continue

            if self._player_var(f"{key}_played", 0) == 1:
                self.machine.events.post("villain_select_ignored_played_villain", villain_key=key)
                continue

            if key not in valid:
                valid.append(key)

        self.valid_villains = valid[:self.max_choices]
        self.selected_index = 0

    def _parse_villain_keys(self, villain_keys):
        if not villain_keys:
            return []

        if isinstance(villain_keys, str):
            return [
                item.strip()
                for item in villain_keys.split(",")
                if item.strip()
            ]

        if isinstance(villain_keys, (list, tuple)):
            return [str(item).strip() for item in villain_keys if str(item).strip()]

        return []

    def _fallback_available_villains(self):
        available = []
        for key in self.VILLAINS:
            if self._player_var(f"{key}_played", 0) == 0:
                available.append(key)
        return available

    def _next(self, **kwargs):
        if not self.villain_select_logic_active or not self.valid_villains:
            return

        self.selected_index = (self.selected_index + 1) % len(self.valid_villains)
        self.machine.events.post("villain_select_moved_next")
        self._highlight_current()

    def _previous(self, **kwargs):
        if not self.villain_select_logic_active or not self.valid_villains:
            return

        self.selected_index = (self.selected_index - 1) % len(self.valid_villains)
        self.machine.events.post("villain_select_moved_previous")
        self._highlight_current()

    def _confirm(self, **kwargs):
        if not self.villain_select_logic_active or not self.valid_villains:
            return

        villain_key = self.valid_villains[self.selected_index]
        self._select_villain(villain_key)

    def _cancel(self, **kwargs):
        if not self.villain_select_logic_active:
            return

        self.machine.events.post("villain_select_cancelled")
        self._stop_self()

    def _highlight_current(self):
        villain_key = self.valid_villains[self.selected_index]

        self.machine.events.post(
            "villain_select_highlighted",
            villain_key=villain_key,
            villain_name=self._villain_name(villain_key),
            display_name=self._villain_display_name(villain_key),
            selected_index=self.selected_index + 1,
            available_count=len(self.valid_villains),
            max_choices=self.max_choices,
        )

        self.machine.events.post(f"villain_select_highlighted_{villain_key}")

    def _post_status(self):
        self.machine.events.post(
            "villain_select_started",
            available_count=len(self.valid_villains),
            max_choices=self.max_choices,
            villain_keys=",".join(self.valid_villains),
        )

    def _select_villain(self, villain_key):
        self.machine.events.post(
            "villain_select_selected",
            villain_key=villain_key,
            villain_name=self._villain_name(villain_key),
            display_name=self._villain_display_name(villain_key),
        )

        self.machine.events.post(
            "villain_progression_start_selected",
            villain_key=villain_key,
        )

        self._stop_self()

    def _stop_self(self):
        self.machine.events.post("stop_mode_villain_select")

    def _villain_name(self, key):
        return self.VILLAINS.get(key, {}).get("name", key)

    def _villain_display_name(self, key):
        return self.VILLAINS.get(key, {}).get("display_name", key.upper())

    def _player_var(self, name, default=0):
        try:
            return self.player[name]
        except Exception:
            return default

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
