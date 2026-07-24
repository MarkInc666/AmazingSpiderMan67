import random
from mpf.core.mode import Mode


class MasterPlan(Mode):
    """The Plotter villain mode: build information, expose three schemes, collect Super."""

    MODE_KEY = "master_plan"
    DISPLAY_NAME = "The Plotter"
    SAUCERS = (1, 2, 3)
    POP_VALUE = 25_000
    SPINNER_VALUE = 50_000
    SCHEME_VALUE = 250_000
    SUPER_VALUE = 1_000_000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.information = 0
        self.lit_saucer = None
        self.schemes = 0
        self.mode_points = 0

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0

        self.add_mode_event_handler("master_plan_pop_hit", self._pop_hit)
        self.add_mode_event_handler("master_plan_spinner_hit", self._spinner_hit)
        for saucer in self.SAUCERS:
            self.add_mode_event_handler(f"master_plan_saucer_{saucer}_hit", self._saucer_hit, saucer=saucer)
        self.add_mode_event_handler("master_plan_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("master_plan_complete_request", self._complete_mode)
        self.add_mode_event_handler("master_plan_fail_request", self._complete_mode)

        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="THE PLOTTER",
            message_mode_subtitle="POPS BUILD INFORMATION",
            reminder=True,
        )
        self._update_status()

    def mode_stop(self, **kwargs):
        self.machine.events.post("master_plan_clear_lights")
        self.machine.events.post("rooftop_diverter_close")
        super().mode_stop(**kwargs)

    def _pop_hit(self, **kwargs):
        if self.mode_done:
            return
        self.information += 1
        self._score(self.POP_VALUE)
        self._update_status()

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.lit_saucer is not None or self.schemes >= 3:
            return
        if self.information < 2:
            self.machine.events.post("show_mode_message", message_mode_title="NEED INFORMATION", message_mode_subtitle="HIT POPS")
            return
        self.information -= 2
        self.lit_saucer = random.choice(self.SAUCERS)
        self._score(self.SPINNER_VALUE)
        self.machine.events.post(f"master_plan_headline_lit", saucer=self.lit_saucer, headlines_lit=1)
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="SCHEME EXPOSED",
            message_mode_subtitle=f"SHOOT SAUCER {self.lit_saucer}",
        )
        self._update_status()

    def _saucer_hit(self, saucer, **kwargs):
        self.machine.events.post(f"delayed_kickout_saucer_{saucer}")
        if self.mode_done or saucer != self.lit_saucer:
            return
        self.lit_saucer = None
        self.schemes += 1
        self._score(self.SCHEME_VALUE)
        self.machine.game.player["active_mode_major_hits"] = self.schemes
        if self.schemes >= 3:
            self.machine.events.post("rooftop_diverter_open")
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="MASTER PLAN EXPOSED",
                message_mode_subtitle="SHOOT DAILY BUGLE VUK",
                message_mode_value=self.SUPER_VALUE,
            )
        else:
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="SCHEME STOPPED",
                message_mode_subtitle=f"{self.schemes} OF 3",
                message_mode_value=self.SCHEME_VALUE,
            )
        self._update_status()

    def _vuk_hit(self, **kwargs):
        self.machine.events.post("up_kick")
        if self.mode_done or self.schemes < 3:
            return
        self._score(self.SUPER_VALUE)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="MASTER PLAN SUPER",
            message_mode_subtitle="THE PLOTTER DEFEATED",
            message_mode_value=self.SUPER_VALUE,
        )
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("master_plan_mode_complete")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points

    def _update_status(self):
        self.machine.game.player["active_mode_hits"] = self.information
        objective = f"SAUCER {self.lit_saucer}" if self.lit_saucer else ("VUK SUPER" if self.schemes >= 3 else "POPS THEN SPINNER")
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="INFO / SCHEMES",
            mode_status_value=f"{self.information} / {self.schemes}   {objective}",
        )
