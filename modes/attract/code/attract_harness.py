from time import monotonic

from mpf.modes.attract.code.attract import Attract


class AttractHarness(Attract):
    """Attract mode with a deterministic physical-flipper test backdoor."""

    ENABLE_CODE = ("L", "L", "R", "R", "L", "R", "L", "R")
    DISABLE_CODE = ("R", "R", "L", "L", "R", "L", "R", "L")
    CODE_TIMEOUT = 5.0
    MAX_CODE_LENGTH = 8

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self._test_code_buffer = []
        self._test_code_started_at = 0.0
        self.add_mode_event_handler("s_left_flipper_active", self._test_code_left)
        self.add_mode_event_handler("s_right_flipper_active", self._test_code_right)

    def _test_code_left(self, **kwargs):
        del kwargs
        self._record_test_code_press("L")

    def _test_code_right(self, **kwargs):
        del kwargs
        self._record_test_code_press("R")

    def _record_test_code_press(self, press):
        now = monotonic()

        if (self._test_code_buffer and
                now - self._test_code_started_at > self.CODE_TIMEOUT):
            self._test_code_buffer.clear()

        if not self._test_code_buffer:
            self._test_code_started_at = now

        self._test_code_buffer.append(press)
        self._test_code_buffer = self._test_code_buffer[-self.MAX_CODE_LENGTH:]

        entered = tuple(self._test_code_buffer)
        if entered == self.ENABLE_CODE:
            self._test_code_buffer.clear()
            self.machine.events.post("test_mode_harness_code_hit")
        elif entered == self.DISABLE_CODE:
            self._test_code_buffer.clear()
            self.machine.events.post("test_mode_harness_off_code_hit")

    def result_of_start_request(self, ev_result=True):
        """Show feedback when MPF refuses to start until balls are home."""
        if ev_result is False and self._start_is_waiting_for_balls():
            # Keep the player-facing WAITING FOR BALLS feedback, but also make
            # a targeted attempt to free balls from the four common non-home
            # locations before the next start request. Attract has no current
            # player, so use switch-confirmed coil pulses instead of gameplay
            # events which may depend on current_player variables/modes.
            self.machine.events.post("attract_waiting_for_balls")
            self._recover_visible_loose_balls()

        super().result_of_start_request(ev_result)

    def _recover_visible_loose_balls(self):
        """Eject switch-confirmed loose balls while a start request is blocked.

        The shooter lane, VUK and three saucers are all places where a ball can
        legitimately be left after testing or an interrupted game. Only pulse
        a device when its switch is presently active; MPF's normal ball
        controller remains responsible for deciding when all balls are home.
        """
        recoveries = (
            ("s_plunger", "c_auto_plunger", "plunger"),
            ("s_vuk_switch", "c_vuk_to_upper", "vuk"),
            ("s_saucer_1", "c_saucer_1", "saucer 1"),
            ("s_saucer_2", "c_saucer_2", "saucer 2"),
            ("s_saucer_3", "c_saucer_3", "saucer 3"),
        )

        for switch_name, coil_name, label in recoveries:
            switch = self.machine.switches.get(switch_name)
            coil = self.machine.coils.get(coil_name)
            if switch is None or coil is None or not switch.state:
                continue

            self.info_log(
                "Start blocked waiting for balls: recovering %s via %s",
                label,
                coil_name,
            )
            coil.pulse()

    def _start_is_waiting_for_balls(self):
        """Return whether the ball controller is the likely start blocker."""
        if not hasattr(self.machine, "ball_devices"):
            return False

        ball_controller = self.machine.ball_controller

        # Match MPF 0.80's start check. Unstable trough switches also deny the
        # request, so treat that brief state as waiting for the balls to settle.
        try:
            counted_balls = ball_controller._count_balls()
        except ValueError:
            return True

        if counted_balls < self.machine.config["machine"]["min_balls"]:
            return True

        if self.machine.config["game"]["allow_start_with_loose_balls"]:
            return False

        allowed_positions = ["home", "trough"]
        if self.machine.config["game"]["allow_start_with_ball_in_drain"]:
            allowed_positions.append("drain")

        return not ball_controller.are_balls_collected(allowed_positions)
