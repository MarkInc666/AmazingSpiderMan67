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
        requested = self._safe_int(kwargs.get("chapter", 0), 0)
        if requested < 1 or requested > len(self.CHAPTERS):
            requested = self._safe_int(player["selected_chapter"], 1)
        self.current_index = max(0, min(len(self.CHAPTERS) - 1, requested - 1))

        # Flipper input is handled here instead of by YAML combo_switches. A held-over
        # both-flipper press from the previous wizard/summary cannot select. The
        # player must release both, then hold both, then release either flipper.
        self.left_flipper_active = self._switch_active("s_left_flipper")
        self.right_flipper_active = self._switch_active("s_right_flipper")
        self.clean_flipper_release_seen = not self.left_flipper_active and not self.right_flipper_active
        self.both_flippers_armed = False

        self.add_mode_event_handler("chapter_carousel_next", self.move_next)
        self.add_mode_event_handler("chapter_carousel_previous", self.move_previous)
        self.add_mode_event_handler("chapter_carousel_select", self.select_current)
        self.add_mode_event_handler("s_left_flipper_active", self._left_flipper_active)
        self.add_mode_event_handler("s_left_flipper_inactive", self._left_flipper_inactive)
        self.add_mode_event_handler("s_right_flipper_active", self._right_flipper_active)
        self.add_mode_event_handler("s_right_flipper_inactive", self._right_flipper_inactive)
        self.machine.events.post("case_files_clear_lights")
        if self.clean_flipper_release_seen:
            self.machine.events.post("chapter_select_flipper_select_ready")
        else:
            self.machine.events.post("chapter_select_flipper_select_locked")
        self._publish_view()

    def mode_stop(self, **kwargs):
        if self.machine.game:
            self.machine.game.player["chapter_select_active"] = 0
        self.machine.events.post("chapter_select_stopped")
        super().mode_stop(**kwargs)

    def _left_flipper_active(self, **kwargs):
        self.left_flipper_active = True
        self._arm_both_flipper_select_if_ready()

    def _right_flipper_active(self, **kwargs):
        self.right_flipper_active = True
        self._arm_both_flipper_select_if_ready()

    def _left_flipper_inactive(self, **kwargs):
        should_select = self.both_flippers_armed
        self.left_flipper_active = False
        self._handle_flipper_release(should_select=should_select, direction="left")

    def _right_flipper_inactive(self, **kwargs):
        should_select = self.both_flippers_armed
        self.right_flipper_active = False
        self._handle_flipper_release(should_select=should_select, direction="right")

    def _handle_flipper_release(self, should_select=False, direction=""):
        if self.selection_made:
            return

        if should_select:
            self.both_flippers_armed = False
            self.select_current(source="flippers")
            return

        # Once both are released, the next intentional both-flipper chord can select.
        if not self.left_flipper_active and not self.right_flipper_active:
            if not self.clean_flipper_release_seen:
                self.clean_flipper_release_seen = True
                self.machine.events.post("chapter_select_flipper_select_ready")
            self.both_flippers_armed = False

        # Normal chapter navigation: release right for next, release left for previous,
        # but only when the opposite flipper is not being held.
        if direction == "right" and not self.left_flipper_active:
            self.move_next()
        elif direction == "left" and not self.right_flipper_active:
            self.move_previous()

    def _arm_both_flipper_select_if_ready(self):
        if self.clean_flipper_release_seen and self.left_flipper_active and self.right_flipper_active:
            self.both_flippers_armed = True

    def move_next(self, **kwargs):
        if self.selection_made:
            return
        if self.current_index >= len(self.CHAPTERS) - 1:
            self.machine.events.post("chapter_select_edge")
            return
        self.current_index += 1
        self.machine.events.post("chapter_select_moved", direction="right")
        self._publish_view()

    def move_previous(self, **kwargs):
        if self.selection_made:
            return
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

    def _switch_active(self, switch_name):
        switch = self.machine.switches.get(switch_name)
        if not switch:
            return False
        return switch.state == 1

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
