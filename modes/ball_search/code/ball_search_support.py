"""Persistent ball-search mode for the custom VUK and saucer ejects."""

from functools import partial
from mpf.core.mode import Mode


class BallSearchSupport(Mode):
    def mode_init(self):
        # Register exactly once: MPF retains these callbacks across mode starts.
        self.search = self.machine.playfield.ball_search
        # Native MPF callbacks share this iterator, so each eject is spaced out
        # by ball_search_interval rather than firing the four coils together.
        self.search.register(1000, self._search_vuk, "ASM67 VUK")
        for number in ("1", "2", "3"):
            self.search.register(
                1000 + int(number), partial(self._search_saucer, number=number),
                f"ASM67 saucer {number}"
            )

        # Last callback bounds attract recovery after the configured final pass.
        self.search.register(1004, self._attract_search_end_of_pass, "ASM67 attract limit")

    def mode_start(self, **kwargs):
        self._cradled = False
        self._attract_search_exhausted = False
        self.add_mode_event_handler("ball_search_started", self._arm_attract_search_timeout)
        self.add_mode_event_handler("mode_attract_started", self._new_attract_search)
        self.add_mode_event_handler("request_to_start_game", self._retry_attract_search, priority=100000)
        self.add_mode_event_handler("game_started", self._new_attract_search)
        self._saucer_attempts = {}
        for number in ("1", "2", "3"):
            self.add_mode_event_handler(
                f"kickout_saucer_{number}", self._kickout_saucer, number=number
            )
            self.add_mode_event_handler(
                f"s_saucer_{number}_inactive", self._clear_saucer_retry, number=number
            )
        self.add_mode_event_handler("cancel_pending_saucer_ejects", self._cancel_saucer_retries)
        self.add_mode_event_handler(
            "villain_summary_hold_saucer_until_done", self._cancel_saucer_retries
        )
        self.add_mode_event_handler("s_plunger_active", self._sync_block, priority=100000)
        self.add_mode_event_handler("s_plunger_inactive", self._sync_block, priority=100000)
        self.add_mode_event_handler("flipper_cradle", self._set_cradle, held=True)
        self.add_mode_event_handler("flipper_cradle_release", self._set_cradle, held=False)
        self.add_mode_event_handler("machine_reset_phase_3", self._reset)
        for phase in (1, 2, 3):
            self.add_mode_event_handler(
                f"ball_search_phase_{phase}", self._stage_changed, phase=phase
            )
        self._sync_block()

    def _shooter_occupied(self):
        return self.machine.switch_controller.is_active(
            self.machine.switches["s_plunger"]
        )

    def _reset(self, **kwargs):
        self._cradled = False
        self._sync_block()

    def _set_cradle(self, held, **kwargs):
        self._cradled = held
        self._sync_block()

    def _sync_block(self, **kwargs):
        if self._shooter_occupied() or self._cradled or self._attract_search_exhausted:
            self.search.block()
        elif self.search.blocked:
            # MPF enables only when a ball is on the playfield; unblocking
            # starts a fresh 20-second inactivity timer.
            self.search.unblock()

    def _stage_changed(self, phase, iteration=1, **kwargs):
        """One listener for every phase/iteration, ready for future actions."""
        self._sync_block()
        if self.search.started:
            self.info_log("Ball search stage %s, iteration %s", phase, iteration)

    def _can_search(self):
        if not self.active:
            return False
        if self._shooter_occupied() or self._cradled or self._attract_search_exhausted:
            self.search.block()
            return False
        return self.search.started

    def _search_vuk(self, phase, iteration):
        if phase < 2 or not self._can_search():
            return False
        # Existing up_kick conditions preserve intentional mode/summary holds
        # and use the configured VUK pulse strength.
        self.machine.events.post("up_kick")
        return True

    def _search_saucer(self, phase, iteration, number):
        if phase < 1 or not self._can_search():
            return False
        progression = self.machine.modes.get("villain_progression")
        if progression and getattr(progression, "active", False):
            if (progression._final_showdown_owns_saucers()
                    or number in progression.summary_held_saucers):
                return False
        # Search must also work when a stuck ball is not registering its switch.
        self.machine.events.post(f"kickout_saucer_{number}")
        return True

    def _kickout_saucer(self, number, **kwargs):
        """Own the raw kickout event; duplicate requests cannot overlap retries."""
        if number in self._saucer_attempts:
            return
        self._saucer_attempts[number] = 0
        self._pulse_saucer(number)

    def _pulse_saucer(self, number):
        coil = self.machine.coils[f"c_saucer_{number}"]
        pulse_ms = coil.get_and_verify_pulse_ms(None)
        # Include MPF's PSU scheduling delay, then check 250ms after pulse end.
        wait_ms = coil.pulse(pulse_ms=pulse_ms)
        self._saucer_attempts[number] += 1
        self.delay.reset(
            name=f"saucer_eject_verify_{number}",
            ms=(wait_ms or 0) + pulse_ms + 250,
            callback=self._verify_saucer, number=number,
        )

    def _verify_saucer(self, number):
        if number not in self._saucer_attempts:
            return
        switch = self.machine.switches[f"s_saucer_{number}"]
        if not self.machine.switch_controller.is_active(switch):
            self._clear_saucer_retry(number)
            return
        if self._saucer_attempts[number] >= 3:
            self.warning_log("Saucer %s still occupied after three eject attempts", number)
            self._clear_saucer_retry(number)
            return
        # Retry only the physical pulse, never scoring/collection events.
        self._pulse_saucer(number)

    def _clear_saucer_retry(self, number, **kwargs):
        self.delay.remove(f"saucer_eject_verify_{number}")
        self._saucer_attempts.pop(number, None)

    def _cancel_saucer_retries(self, saucer_number=None, **kwargs):
        numbers = (str(saucer_number).replace("saucer_", ""),) if saucer_number is not None else ("1", "2", "3")
        for number in numbers:
            self._clear_saucer_retry(number)

    def mode_stop(self, **kwargs):
        self._cancel_saucer_retries()

    def _new_attract_search(self, **kwargs):
        self.delay.remove("attract_search_limit")
        self.delay.remove("attract_search_timeout")
        self._attract_search_exhausted = False
        self._sync_block()

    def _retry_attract_search(self, **kwargs):
        # Do not override MPF's decision about whether enough balls are home.
        if self._attract_search_exhausted:
            self._new_attract_search()

    def _attract_search_end_of_pass(self, phase, iteration):
        if self.machine.game or not self._can_search():
            return False
        final_iterations = 4  # Current ASM67 phase repetition counts: 3 / 3 / 4
        if phase == 3 and iteration >= final_iterations:
            # Let the last saucer pulse and its verification finish first.
            self.delay.reset(name="attract_search_limit", ms=350,
                             callback=self._stop_exhausted_attract_search)
            return True
        return False

    def _stop_exhausted_attract_search(self):
        if self.machine.game:
            return
        self._attract_search_exhausted = True
        self._cancel_saucer_retries()
        self.search.block()
        self.warning_log("Attract ball search finished; waiting for balls or another Start press")

    def _arm_attract_search_timeout(self, **kwargs):
        if not self.machine.game and not self.delay.check("attract_search_timeout"):
            self.delay.add(name="attract_search_timeout", ms=120000,
                           callback=self._stop_exhausted_attract_search)
