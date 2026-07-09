from mpf.core.mode import Mode


class ChapterSelect(Mode):
    """Comic-book chapter carousel shown at controlled shooter-lane stops."""

    CHAPTERS = [
        (1, "CLASSIC ROGUES"),
        (2, "MASKED MASTERMINDS"),
        (3, "TRUBBLE'S MONSTERS"),
        (4, "CRIME WAVE"),
        (5, "MYSTIC MENACE"),
        (6, "MAD SCIENCE"),
        (7, "ELEMENTAL CHAOS"),
        (8, "LOST WORLDS"),
        (9, "SAVAGE ODDITIES"),
        (10, "DIMENSIONAL FINALE"),
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        player = self.machine.game.player
        player["chapter_select_active"] = 1
        self.selection_made = False
        self.flipper_select_enabled = False
        self.left_flipper_active = self._switch_active("s_left_flipper")
        self.right_flipper_active = self._switch_active("s_right_flipper")
        # A both-flipper select must be intentional inside Chapter Select:
        # both released first, then both held, then either released.
        self.flipper_chord_armed = False
        self.flipper_chord_was_held = False
        requested = self._safe_int(kwargs.get("chapter", 0), 0)
        if requested < 1 or requested > len(self.CHAPTERS):
            requested = self._safe_int(player["selected_chapter"], 1)
        self.current_index = max(0, min(len(self.CHAPTERS) - 1, requested - 1))
        self.add_mode_event_handler("chapter_carousel_next", self.move_next)
        self.add_mode_event_handler("chapter_carousel_previous", self.move_previous)
        self.add_mode_event_handler("chapter_carousel_select", self.select_current)
        self.add_mode_event_handler("chapter_select_left_flipper_active", self._left_flipper_active)
        self.add_mode_event_handler("chapter_select_left_flipper_inactive", self._left_flipper_inactive)
        self.add_mode_event_handler("chapter_select_right_flipper_active", self._right_flipper_active)
        self.add_mode_event_handler("chapter_select_right_flipper_inactive", self._right_flipper_inactive)
        self.machine.events.post("case_files_clear_lights")
        self.delay.add(
            name="chapter_select_enable_flipper_select",
            ms=3000,
            callback=self._enable_flipper_select,
        )
        self.machine.events.post("chapter_select_flipper_select_locked")
        self._publish_view()

    def mode_stop(self, **kwargs):
        if self.machine.game:
            self.machine.game.player["chapter_select_active"] = 0
        self.machine.events.post("chapter_select_stopped")
        super().mode_stop(**kwargs)

    def _enable_flipper_select(self):
        self.flipper_select_enabled = True
        self._arm_flipper_chord_if_released()
        self.machine.events.post("chapter_select_flipper_select_ready")

    def _left_flipper_active(self, **kwargs):
        self.left_flipper_active = True
        self._note_flipper_chord_held()

    def _right_flipper_active(self, **kwargs):
        self.right_flipper_active = True
        self._note_flipper_chord_held()

    def _left_flipper_inactive(self, **kwargs):
        was_both_held = self.left_flipper_active and self.right_flipper_active
        self.left_flipper_active = False
        if self._select_on_clean_chord_release(was_both_held):
            return
        self._arm_flipper_chord_if_released()
        if not self.right_flipper_active:
            self.move_previous(**kwargs)

    def _right_flipper_inactive(self, **kwargs):
        was_both_held = self.left_flipper_active and self.right_flipper_active
        self.right_flipper_active = False
        if self._select_on_clean_chord_release(was_both_held):
            return
        self._arm_flipper_chord_if_released()
        if not self.left_flipper_active:
            self.move_next(**kwargs)

    def _note_flipper_chord_held(self):
        if (
            self.flipper_select_enabled
            and self.flipper_chord_armed
            and self.left_flipper_active
            and self.right_flipper_active
        ):
            self.flipper_chord_was_held = True

    def _select_on_clean_chord_release(self, was_both_held):
        if not self.flipper_select_enabled:
            if was_both_held:
                self.machine.events.post("chapter_select_flipper_select_not_ready")
            return False
        if self.flipper_chord_armed and self.flipper_chord_was_held and was_both_held:
            self.flipper_chord_armed = False
            self.flipper_chord_was_held = False
            self.select_current()
            return True
        return False

    def _arm_flipper_chord_if_released(self):
        if self.flipper_select_enabled and not self.left_flipper_active and not self.right_flipper_active:
            self.flipper_chord_armed = True
            self.flipper_chord_was_held = False

    def _switch_active(self, switch_name):
        try:
            return bool(self.machine.switch_controller.is_active(switch_name))
        except Exception:
            try:
                return bool(self.machine.switches[switch_name].state)
            except Exception:
                return False

    def move_next(self, **kwargs):
        if self.current_index >= len(self.CHAPTERS) - 1:
            self.machine.events.post("chapter_select_edge")
            return
        self.current_index += 1
        self.machine.events.post("chapter_select_moved", direction="right")
        self._publish_view()

    def move_previous(self, **kwargs):
        if self.current_index <= 0:
            self.machine.events.post("chapter_select_edge")
            return
        self.current_index -= 1
        self.machine.events.post("chapter_select_moved", direction="left")
        self._publish_view()

    def select_current(self, **kwargs):
        if self.selection_made:
            return
        selected_index = self._selected_or_next_available_index()
        if selected_index is None:
            chapter_number, chapter_name = self.CHAPTERS[self.current_index]
            self.machine.events.post(
                "chapter_select_no_available_chapters",
                chapter_number=chapter_number,
                chapter_name=chapter_name,
                status=self._chapter_status(chapter_number),
            )
            return

        if selected_index != self.current_index:
            old_number, old_name = self.CHAPTERS[self.current_index]
            new_number, new_name = self.CHAPTERS[selected_index]
            self.current_index = selected_index
            self._publish_view()
            self.machine.events.post(
                "chapter_select_defaulted_to_next_available",
                old_chapter_number=old_number,
                old_chapter_name=old_name,
                new_chapter_number=new_number,
                new_chapter_name=new_name,
            )

        chapter_number, chapter_name = self.CHAPTERS[self.current_index]
        self.selection_made = True
        self.machine.events.post(
            "chapter_select_selected",
            chapter_number=chapter_number,
            chapter_name=chapter_name,
        )
        self.machine.events.post("chapter_carousel_accept_selection")
        self.machine.events.post("stop_mode_chapter_select")

    def _selected_or_next_available_index(self):
        chapter_number, _ = self.CHAPTERS[self.current_index]
        if self._chapter_status(chapter_number) == "AVAILABLE":
            return self.current_index

        total = len(self.CHAPTERS)
        for offset in range(1, total + 1):
            index = (self.current_index + offset) % total
            test_number, _ = self.CHAPTERS[index]
            if self._chapter_status(test_number) == "AVAILABLE":
                return index
        return None

    def _publish_view(self):
        self._publish_slot("left", self.current_index - 1)
        self._publish_slot("center", self.current_index)
        self._publish_slot("right", self.current_index + 1)

        center_number, center_name = self.CHAPTERS[self.current_index]
        center_status = self._chapter_status(center_number)
        self.machine.events.post(
            "chapter_select_highlighted",
            chapter_number=center_number,
            chapter_name=center_name,
            chapter_status=center_status,
            selected_index=self.current_index + 1,
            total_chapters=len(self.CHAPTERS),
        )
        self.machine.events.post("chapter_select_view_changed")

    def _publish_slot(self, slot, index):
        player = self.machine.game.player
        prefix = f"chapter_select_{slot}"
        if index < 0 or index >= len(self.CHAPTERS):
            player[f"{prefix}_visible"] = 0
            player[f"{prefix}_number"] = ""
            player[f"{prefix}_title"] = ""
            player[f"{prefix}_status"] = ""
            player[f"{prefix}_selectable"] = 0
            return

        chapter_number, chapter_name = self.CHAPTERS[index]
        status = self._chapter_status(chapter_number)
        player[f"{prefix}_visible"] = 1
        player[f"{prefix}_number"] = f"CHAPTER {chapter_number}"
        player[f"{prefix}_title"] = chapter_name
        player[f"{prefix}_status"] = status
        player[f"{prefix}_selectable"] = 1 if status == "AVAILABLE" else 0

    def _chapter_status(self, chapter_number):
        player = self.machine.game.player
        if self._safe_int(player[f"chapter_{chapter_number}_collected"], 0) == 1:
            return "COLLECTED"
        if self._safe_int(player[f"chapter_{chapter_number}_unlocked"], 0) == 1:
            return "AVAILABLE"
        return "LOCKED"

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
