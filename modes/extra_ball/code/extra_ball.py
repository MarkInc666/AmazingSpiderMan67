from mpf.core.mode import Mode


class ExtraBall(Mode):
    """Shared extra-ball presentation plus Daily Bugle VUK ownership."""

    DAILY_BUGLE_NEWSPAPER_REVEAL_MS = 3000
    EXTRA_BALL_PRESENTATION_MS = 6000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        if self.machine.game:
            self.machine.game.player["extra_ball_vuk_hold_active"] = 0
        self._active_ball_saves = set()
        self._hurry_ball_saves = set()
        self._shoot_again_state = "off"
        self._register_standard_ball_save_handlers()
        self._register_multiball_ball_save_handlers()
        self.add_mode_event_handler(
            "mystery_extra_ball_award", self._maybe_claim_daily_bugle_vuk
        )
        self.add_mode_event_handler(
            "mystery_extra_ball_direct_award", self._maybe_claim_daily_bugle_vuk
        )

    def mode_stop(self, **kwargs):
        self.delay.remove("daily_bugle_extra_ball_takeover")
        self.delay.remove("daily_bugle_extra_ball_finish")
        if self.machine.game:
            self.machine.game.player["extra_ball_vuk_hold_active"] = 0
        super().mode_stop(**kwargs)


    def _register_standard_ball_save_handlers(self):
        """Track the three shared non-multiball ball-save devices."""
        for name in ("default_ball_save", "mystery_ball_save", "case_file_ball_save"):
            self.add_mode_event_handler(
                f"ball_save_{name}_enabled",
                self._ball_save_started,
                save_name=name,
            )
            self.add_mode_event_handler(
                f"ball_save_{name}_hurry_up",
                self._ball_save_hurry_up,
                save_name=name,
            )
            self.add_mode_event_handler(
                f"ball_save_{name}_disabled",
                self._ball_save_ended,
                save_name=name,
            )

    def _ball_save_started(self, save_name="", **kwargs):
        name = str(save_name or "")
        if not name:
            return
        self._active_ball_saves.add(name)
        self._hurry_ball_saves.discard(name)
        self._refresh_shoot_again_state()

    def _ball_save_hurry_up(self, save_name="", **kwargs):
        name = str(save_name or "")
        if not name:
            return
        self._active_ball_saves.add(name)
        self._hurry_ball_saves.add(name)
        self._refresh_shoot_again_state()

    def _ball_save_ended(self, save_name="", **kwargs):
        name = str(save_name or "")
        if name:
            self._active_ball_saves.discard(name)
            self._hurry_ball_saves.discard(name)
        self._refresh_shoot_again_state()

    def _refresh_shoot_again_state(self):
        if self._hurry_ball_saves:
            state = "fast"
        elif self._active_ball_saves:
            state = "flash"
        else:
            state = "off"

        if state == self._shoot_again_state:
            return
        self._shoot_again_state = state
        if state == "fast":
            self.machine.events.post("shared_shoot_again_fast")
        elif state == "flash":
            self.machine.events.post("shared_shoot_again_flash")
        else:
            self.machine.events.post("shared_shoot_again_off")

    def _register_multiball_ball_save_handlers(self):
        """Normalize every configured multiball shoot-again window."""
        multiballs = getattr(self.machine, "multiballs", {})
        for multiball in multiballs.values():
            name = multiball.name
            # MPF starts the multiball ball-save timer when multiball begins,
            # but does not post multiball_<name>_shoot_again until a ball is
            # actually saved.  Listen to the timer-start event so SHOOT AGAIN
            # flashes for the entire active save window from multiball start.
            self.add_mode_event_handler(
                f"ball_save_{name}_timer_start",
                self._multiball_ball_save_started,
                multiball_name=name,
            )
            # Add-a-ball restarts/extends the same protection window using a
            # separate MPF ball-save timer-start event.
            self.add_mode_event_handler(
                f"ball_save_{name}_add_a_ball_timer_start",
                self._multiball_ball_save_started,
                multiball_name=name,
            )
            self.add_mode_event_handler(
                f"multiball_{name}_shoot_again",
                self._multiball_ball_save_started,
                multiball_name=name,
            )
            self.add_mode_event_handler(
                f"multiball_{name}_hurry_up",
                self._multiball_ball_save_hurry_up,
                multiball_name=name,
            )
            self.add_mode_event_handler(
                f"multiball_{name}_shoot_again_ended",
                self._multiball_ball_save_ended,
                multiball_name=name,
            )
            # Defensive cleanup if a multiball is explicitly stopped before its
            # shoot-again timer posts the normal ended event.
            self.add_mode_event_handler(
                f"multiball_{name}_ended",
                self._multiball_ball_save_ended,
                multiball_name=name,
            )

    def _multiball_ball_save_started(self, multiball_name="", **kwargs):
        name = str(multiball_name or "")
        if not name:
            return
        self._ball_save_started(save_name=f"multiball:{name}")

    def _multiball_ball_save_hurry_up(self, multiball_name="", **kwargs):
        name = str(multiball_name or "")
        if not name:
            return
        self._ball_save_hurry_up(save_name=f"multiball:{name}")

    def _multiball_ball_save_ended(self, multiball_name="", **kwargs):
        name = str(multiball_name or "")
        if not name:
            return
        self._ball_save_ended(save_name=f"multiball:{name}")

    def _maybe_claim_daily_bugle_vuk(self, **kwargs):
        if not self.machine.game:
            return
        player = self.machine.game.player
        if int(player["daily_bugle_vuk_hold_active"] or 0) != 1:
            return

        # The extra-ball award fires/reveals at 3s. Claim the parked VUK ball
        # immediately, but let the newspaper remain visible for another 3s.
        player["extra_ball_vuk_hold_active"] = 1
        self.machine.events.post("extra_ball_vuk_ownership_claimed")
        self.delay.reset(
            name="daily_bugle_extra_ball_takeover",
            ms=self.DAILY_BUGLE_NEWSPAPER_REVEAL_MS,
            callback=self._start_daily_bugle_extra_ball_presentation,
        )

    def _start_daily_bugle_extra_ball_presentation(self):
        if not self.machine.game:
            return
        player = self.machine.game.player
        if int(player["extra_ball_vuk_hold_active"] or 0) != 1:
            return
        self.machine.events.post("daily_bugle_extra_ball_presentation_start")
        self.delay.reset(
            name="daily_bugle_extra_ball_finish",
            ms=self.EXTRA_BALL_PRESENTATION_MS,
            callback=self._finish_daily_bugle_extra_ball_presentation,
        )

    def _finish_daily_bugle_extra_ball_presentation(self):
        if not self.machine.game:
            return
        player = self.machine.game.player
        if int(player["extra_ball_vuk_hold_active"] or 0) != 1:
            return
        player["extra_ball_vuk_hold_active"] = 0
        self.machine.events.post("daily_bugle_extra_ball_presentation_complete")
        self.machine.events.post("request_vuk_eject")
