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
