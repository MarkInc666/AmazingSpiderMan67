from mpf.modes.carousel.code.carousel import Carousel


class VillainSelect(Carousel):
    """Villain carousel UI only.

    This mode does not own villain start events or chapter lists. It displays the
    choices handed to it by villain_progression and reports the selected key back
    to villain_progression.
    """

    def mode_start(self, **kwargs):
        self.info_log("Villain select start kwargs: %s", kwargs)
        self.current_item = None
        self.selection_made = False

        self.valid_villains = self._build_valid_list(
            villain_keys=kwargs.get("villain_keys", ""),
            max_choices=kwargs.get("max_choices", 5),
        )

        if not self.valid_villains:
            self.machine.events.post("villain_select_no_valid_villains")
            self.machine.events.post("villain_start_request_failed", reason="select_no_valid_villains")
            self.machine.events.post("stop_mode_villain_select")
            return

        self._all_items = list(self.valid_villains)
        self.config["mode_settings"]["selectable_items"] = list(self.valid_villains)

        super().mode_start(**kwargs)

        self.info_log("Carousel items: %s", self._all_items)

        self.add_mode_event_handler("carousel_item_highlighted", self.my_carousel_item_highlighted)
        self.add_mode_event_handler("flipper_cancel", self.my_carousel_item_selected)

        self.machine.events.post(
            "villain_select_started",
            available_count=len(self.valid_villains),
            max_choices=self._safe_int(kwargs.get("max_choices", len(self.valid_villains)), len(self.valid_villains)),
            villain_keys=",".join(self.valid_villains),
        )

        if len(self.valid_villains) == 1:
            self.delay.add(name="villain_select_only_one_choice", ms=250, callback=self._select_only_choice)

    def mode_stop(self, **kwargs):
        self.machine.events.post("villain_select_stopped")
        if not getattr(self, "selection_made", False):
            self.machine.events.post("villain_select_cancelled")
        super().mode_stop(**kwargs)

    def _select_only_choice(self):
        if not self.valid_villains:
            return
        villain = self.valid_villains[0]
        self.machine.events.post(
            "villain_select_only_one_choice",
            villain_key=villain,
            display_name=self._display_name(villain),
        )
        self._select_villain(villain)

    def my_carousel_item_highlighted(self, item=None, **kwargs):
        if not item:
            return

        self.current_item = item
        self.machine.events.post(f"carousel_{item}_highlighted")
        self.machine.events.post(f"villain_select_highlighted_{item}")
        self.machine.events.post(
            "villain_select_highlighted",
            villain_key=item,
            display_name=self._display_name(item),
            selected_index=self._current_index(item),
            available_count=len(self.valid_villains),
            villain_keys=",".join(self.valid_villains),
        )

        if self._is_unavailable(item):
            self.machine.events.post(f"villain_select_{item}_played")
        else:
            self.machine.events.post(f"villain_select_{item}_available")

    def my_carousel_item_selected(self, **kwargs):
        if not self.current_item:
            return
        if self._is_unavailable(self.current_item):
            self.machine.events.post("villain_select_already_played", villain_key=self.current_item)
            return
        self._select_villain(self.current_item)

    def _select_villain(self, villain_key):
        self.selection_made = True
        self.machine.events.post(
            "villain_select_selected",
            villain_key=villain_key,
            display_name=self._display_name(villain_key),
        )
        self.machine.events.post("villain_select_choice_made", villain_key=villain_key)
        self.machine.events.post("villain_carousel_accept_selection")
        self.machine.events.post("stop_mode_villain_select")
        self.machine.events.post("stop_carousel_select")

    def _build_valid_list(self, villain_keys=None, max_choices=5, **kwargs):
        requested_keys = self._parse_villain_keys(villain_keys)
        if not requested_keys:
            requested_keys = list(self.config.get("mode_settings", {}).get("selectable_items", []))

        valid = []
        for key in requested_keys:
            if self._is_unavailable(key):
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
            return [item.strip() for item in villain_keys.split(",") if item.strip()]
        if isinstance(villain_keys, (list, tuple)):
            return [str(item).strip() for item in villain_keys if str(item).strip()]
        return []

    def _is_unavailable(self, villain_key):
        state = self._player_var(f"{villain_key}_state", 0)
        try:
            return int(state) != 0
        except Exception:
            state_text = str(state).strip().upper().replace(" ", "_")
            return state_text in ("PLAYING", "COMPLETED")

    def _display_name(self, villain_key):
        return str(villain_key).replace("_", " ").upper()

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
