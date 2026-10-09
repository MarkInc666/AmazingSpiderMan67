"""Use the existing GMC service utilities with three cabinet buttons."""
from mpf.modes.service.code.service import Service
from mpf.core.utility_functions import Util


class CabinetService(Service):
    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self._chord = False
        self._entry_release = False
        self._ignore_start_release = False
        self.add_mode_event_handler("service_mode_entered", self._entered)
        for side in ("left", "right"):
            self.add_mode_event_handler(f"s_{side}_flipper_active", self._pressed)
            self.add_mode_event_handler(
                f"s_{side}_flipper_inactive", self._released, side=side)
        self.add_mode_event_handler("s_startbutton_inactive", self._select)

    def _entered(self, **kwargs):
        # Ignore all releases belonging to the entry gesture.
        self._entry_release = True
        self._ignore_start_release = True
        self._chord = True

    def _both(self):
        return all(self.machine.switches[name].state for name in
                   ("s_left_flipper", "s_right_flipper"))

    def _pressed(self, **kwargs):
        if not self.machine.service.is_in_service() or self._entry_release:
            return
        if self._both():
            self._chord = True
            self.delay.reset(ms=1000, callback=self._back, name="service_back")

    def _back(self):
        if self.machine.service.is_in_service() and self._both():
            self.machine.events.post("asm_service_back")

    def _released(self, side, **kwargs):
        self.delay.remove("service_back")
        if not self.machine.service.is_in_service():
            return
        if self._entry_release or self._chord:
            if not any(self.machine.switches[name].state for name in
                       ("s_left_flipper", "s_right_flipper")):
                self._chord = False
                self._entry_release = False
            return
        self.machine.events.post(
            "asm_service_left" if side == "left" else "asm_service_right")

    def _select(self, **kwargs):
        if self._ignore_start_release:
            self._ignore_start_release = False
            return
        if self.machine.service.is_in_service() and not self._entry_release:
            self.machine.events.post("asm_service_select")

    async def _get_key(self):
        # Replace the stock flipper/start listeners to avoid duplicate keys.
        futures = {
            self.machine.events.wait_for_any_event([event]): key
            for event, key in (
                ("asm_service_enter", "ENTER"),
                ("asm_service_left", "DOWN"),
                ("asm_service_right", "UP"),
                ("asm_service_select", "ENTER"),
                ("asm_service_back", "ESC"),
                ("service_trigger", "TRIGGER"),
            )
        }
        key = await Util.race(futures)
        if key == "TRIGGER":
            await self._service_trigger()
            return None
        return key
