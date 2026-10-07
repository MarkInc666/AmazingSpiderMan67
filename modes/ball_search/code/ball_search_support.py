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

    def mode_start(self, **kwargs):
        self._cradled = False
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
        if self._shooter_occupied() or self._cradled:
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
        if self._shooter_occupied() or self._cradled:
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
        if phase < 3 or not self._can_search():
            return False
        progression = self.machine.modes.get("villain_progression")
        if progression and getattr(progression, "active", False):
            if (progression._final_showdown_owns_saucers()
                    or number in progression.summary_held_saucers):
                return False
        # Search must also work when a stuck ball is not registering its switch.
        self.machine.events.post(f"kickout_saucer_{number}")
        return True
