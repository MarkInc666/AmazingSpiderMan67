from mpf.modes.carousel.code.carousel import Carousel


class VillainSelect(Carousel):
    """Dynamic villain select carousel.

    This version follows the same working pattern as qualify_villain_select:

    - subclass MPF's stock Carousel so GMC MPFCarousel receives the normal
      carousel_item_highlighted events
    - keep the currently highlighted item in Python
    - use flipper_cancel / both-flippers-held as the confirm event
    - start the selected villain through the bookend intro
    - stop the carousel after a valid selection

    Expected start event:
        start_mode_villain_select

    Optional kwargs from villain_start.py:
        villain_keys="rhino,vulture,lizard"
        max_choices=3
    """

    VILLAINS = {
        "lizard": "start_mode_lizard",
        "rhino": "start_mode_rhino_bash",
        "sandman": "start_mode_sandman",
        "vulture": "start_mode_vulture",
        "electro": "start_mode_electro",
        "goblin": "start_mode_goblin",
        "mysterio": "start_mode_mysterio",
        "scorpion": "start_mode_scorpion",
        "doc_ock": "start_mode_doc_ock",
        "parafino": "start_mode_parafino",
    }

    DISPLAY_NAMES = {
        "lizard": "LIZARD",
        "rhino": "RHINO",
        "sandman": "SANDMAN",
        "vulture": "VULTURE",
        "electro": "ELECTRO",
        "goblin": "GOBLIN",
        "mysterio": "MYSTERIO",
        "scorpion": "SCORPION",
        "doc_ock": "DOC OCK",
        "parafino": "PARAFINO",
    }

    def mode_start(self, **kwargs):
        self.info_log("Villain select start kwargs: %s", kwargs)

        self.current_item = None

        self.valid_villains = self._build_valid_list(
            villain_keys=kwargs.get("villain_keys", ""),
            max_choices=kwargs.get("max_choices", 5)
        )

        if not self.valid_villains:
            self.machine.events.post("villain_select_no_valid_villains")
            self.machine.events.post("stop_mode_villain_select")
            return

        self._all_items = list(self.valid_villains)
        self.config["mode_settings"]["selectable_items"] = list(self.valid_villains)

        super().mode_start(**kwargs)

        self.info_log("Carousel items: %s", self._all_items)

        self.add_mode_event_handler(
            "carousel_item_highlighted",
            self.my_carousel_item_highlighted
        )

        self.add_mode_event_handler(
            "flipper_cancel",
            self.my_carousel_item_selected
        )

        self.machine.events.post(
            "villain_select_started",
            available_count=len(self.valid_villains),
            max_choices=self._safe_int(
                kwargs.get("max_choices", len(self.valid_villains)),
                len(self.valid_villains)
            ),
            villain_keys=",".join(self.valid_villains),
        )

        if len(self.valid_villains) == 1:
            self.delay.add(
                name="villain_select_only_one_choice",
                ms=250,
                callback=self._select_only_choice
            )

    def mode_stop(self, **kwargs):
        self.machine.events.post("villain_select_stopped")
        super().mode_stop(**kwargs)

    def _select_only_choice(self):
        if not self.valid_villains:
            return

        villain = self.valid_villains[0]
        self.machine.events.post(
            "villain_select_only_one_choice",
            villain_key=villain,
            display_name=self.DISPLAY_NAMES.get(villain, villain.upper())
        )
        self.start_villain(villain)

    def my_carousel_item_highlighted(self, item=None, **kwargs):
        if not item:
            return

        self.current_item = item

        # GMC MPFCarousel uses the stock carousel_item_highlighted event.
        # These extra events are for your lights/sounds/widgets.
        self.machine.events.post(f"carousel_{item}_highlighted")
        self.machine.events.post(f"villain_select_highlighted_{item}")

        self.machine.events.post(
            "villain_select_highlighted",
            villain_key=item,
            display_name=self.DISPLAY_NAMES.get(item, item.upper()),
            selected_index=self._current_index(item),
            available_count=len(self.valid_villains),
            villain_keys=",".join(self.valid_villains),
        )

        played_state = self._player_var(f"{item}_played", 0)

        if played_state == 1:
            self.machine.events.post(f"villain_select_{item}_played")
        else:
            self.machine.events.post(f"villain_select_{item}_available")

    def my_carousel_item_selected(self, **kwargs):
        if not self.current_item:
            return

        played_state = self._player_var(f"{self.current_item}_played", 0)

        self.info_log("current villain: %s", self.current_item)
        self.info_log("current villain played state: %s", played_state)

        if played_state == 1:
            self.machine.events.post("villain_select_already_played")
            return

        self.start_villain(self.current_item)


    def start_villain(self, item):
        if item not in self.VILLAINS:
            self.warning_log("Unknown villain selected: %s", item)
            self.machine.events.post("villain_select_unknown_villain", villain_key=item)
            return

        player = self.machine.game.player if self.machine.game else None

        if not player:
            return

        player[f"{item}_played"] = 1
        player["villain_current_name"] = item
        player["villain_mode_running"] = 1
        player["villain_mode_running_name"] = item

        player["villain_start_ready"] = 0
        player["villain_locate_spins"] = 0
        player["saucer_1_select_ready"] = 0
        player["saucer_2_select_ready"] = 0
        player["saucer_3_select_ready"] = 0

        # Shut down qualify/start visuals and saucers first.
        self.machine.events.post("clear_villain_saucer_lights")
        self.machine.events.post("clear_saucers")

        # Tell the qualify/start system that a villain is now active.
        self.machine.events.post(
            "villain_mode_started",
            villain_key=item,
            villain_name=self.DISPLAY_NAMES.get(item, item.upper())
        )

        self.machine.events.post("villain_started_set", villain=item, villain_key=item)

        self.machine.events.post(
            "villain_select_selected",
            villain_key=item,
            display_name=self.DISPLAY_NAMES.get(item, item.upper())
        )

        start_event = self.VILLAINS[item]

        self.machine.events.post(
            "villain_bookend_intro_request",
            villain=item,
            start_event=start_event
        )

        self.machine.events.post("villain_carousel_accept_selection")
        self.machine.events.post("stop_mode_villain_select")
        self.machine.events.post("stop_carousel_select")

    def _build_valid_list(self, villain_keys=None, max_choices=5, **kwargs):
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

        max_choices = self._safe_int(max_choices, default=len(valid))

        if max_choices > 0:
            valid = valid[:max_choices]

        return valid

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
            return [
                str(item).strip()
                for item in villain_keys
                if str(item).strip()
            ]

        return []

    def _fallback_available_villains(self):
        available = []

        for key in self.VILLAINS:
            if self._player_var(f"{key}_played", 0) == 0:
                available.append(key)

        return available

    def _current_index(self, item):
        try:
            return self.valid_villains.index(item) + 1
        except ValueError:
            return 0

    def _player_var(self, name, default=0):
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return default

        try:
            return player[name]
        except Exception:
            return default

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
