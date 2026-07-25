import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class MasterPlan(CaseFileMixin, Mode):
    """The Plotter villain mode: build rumors, expose three schemes, collect the VUK Super."""

    MODE_KEY = "master_plan"
    DISPLAY_NAME = "The Plotter"
    SAUCERS = (1, 2, 3)
    POP_VALUE = 25_000
    SPINNER_VALUE = 50_000
    SCHEME_VALUE = 250_000
    SUPER_VALUE = 1_000_000
    BACK_PAGE_VALUE = 500_000
    VUK_SECONDS = 20
    MORE_TIME_VUK_SECONDS = 30
    RUMORS_TO_LIGHT_SAUCER = 2

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.rumors = 0
        self.lit_saucers = set()
        self.schemes = 0
        self.mode_points = 0
        self.vuk_lit = False
        self.vuk_collected = False
        self.back_page_lit = False
        self.seconds_left = 0
        self.shot_assist_used = False

        self.case_files = self.get_case_file_bonuses()
        self.vuk_seconds = self.MORE_TIME_VUK_SECONDS if self.has_case_file("more_time") else self.VUK_SECONDS

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player["master_plan_headlines_collected"] = 0
        player["master_plan_super_collected"] = 0

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "BACK PAGE SHOT AFTER VUK"),
            ("more_time", "VUK TIMER EXTENDED TO 30 SECONDS"),
            ("safety_net", "BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST SPIN LIGHTS TWO SAUCERS"),
        ])
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.add_mode_event_handler("master_plan_pop_hit", self._pop_hit)
        self.add_mode_event_handler("master_plan_spinner_hit", self._spinner_hit)
        for saucer in self.SAUCERS:
            self.add_mode_event_handler(f"master_plan_saucer_{saucer}_hit", self._saucer_hit, saucer=saucer)
        self.add_mode_event_handler("master_plan_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("master_plan_back_page_hit", self._back_page_hit)
        self.add_mode_event_handler("master_plan_complete_request", self._complete_mode)
        self.add_mode_event_handler("master_plan_fail_request", self._fail_mode)
        self.add_mode_event_handler("ball_will_end", self._ball_ending)
        self.add_mode_event_handler("ball_ending", self._ball_ending)

        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="THE PLOTTER",
            message_mode_subtitle="POPS BUILD RUMORS",
            reminder=True,
        )
        self._update_status()

    def mode_stop(self, **kwargs):
        self._cleanup_mode_display_and_delays()
        self.machine.events.post("master_plan_clear_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _ball_ending(self, **kwargs):
        self.mode_done = True
        self._cleanup_mode_display_and_delays()

    def _cleanup_mode_display_and_delays(self):
        if hasattr(self, "delay"):
            self.delay.remove("master_plan_vuk_timer_tick")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")

    def _pop_hit(self, **kwargs):
        if self.mode_done:
            return
        self.rumors += 1
        self._score(self.POP_VALUE)
        self._update_status()

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.vuk_lit:
            return
        if self.rumors < self.RUMORS_TO_LIGHT_SAUCER:
            self.machine.events.post("show_mode_message", message_mode_title="NEED RUMORS", message_mode_subtitle="HIT POPS")
            return

        available = [saucer for saucer in self.SAUCERS if saucer not in self.lit_saucers]
        if not available:
            self.machine.events.post("show_mode_message", message_mode_title="SAUCERS READY", message_mode_subtitle="COLLECT LIT SAUCERS")
            return

        self.rumors -= self.RUMORS_TO_LIGHT_SAUCER
        self._score(self.SPINNER_VALUE)
        self._light_random_saucer(available)

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            available = [saucer for saucer in self.SAUCERS if saucer not in self.lit_saucers]
            if available:
                self._light_random_saucer(available, assisted=True)

        self.machine.events.post(
            "show_mode_message",
            message_mode_title="SAUCER LIT",
            message_mode_subtitle="COLLECT ANY LIT SAUCER",
        )
        self._update_status()

    def _light_random_saucer(self, available, assisted=False):
        saucer = random.choice(available)
        self.lit_saucers.add(saucer)
        self.machine.events.post(f"master_plan_saucer_{saucer}_lit")
        if assisted:
            self.machine.events.post("show_mode_message", message_mode_title="SHOT ASSIST", message_mode_subtitle=f"SAUCER {saucer} ALSO LIT")

    def _saucer_hit(self, saucer, **kwargs):
        self.machine.events.post(f"delayed_kickout_saucer_{saucer}")
        if self.mode_done or saucer not in self.lit_saucers:
            return

        self.lit_saucers.remove(saucer)
        self.machine.events.post(f"master_plan_saucer_{saucer}_collected")
        self.schemes += 1
        self._score(self.SCHEME_VALUE)
        player = self.machine.game.player
        player["active_mode_major_hits"] = self.schemes
        player["master_plan_headlines_collected"] = self.schemes

        if self.schemes >= 3:
            self._start_vuk_timer()
        else:
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="SCHEME STOPPED",
                message_mode_subtitle=f"{self.schemes} OF 3",
                message_mode_value=self.SCHEME_VALUE,
            )
        self._update_status()

    def _start_vuk_timer(self):
        if self.vuk_lit or self.mode_done:
            return
        self.vuk_lit = True
        self.seconds_left = self.vuk_seconds
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("master_plan_super_lit_show")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="MASTER PLAN EXPOSED",
            message_mode_subtitle=f"SHOOT DAILY BUGLE VUK - {self.seconds_left}s",
            message_mode_value=self.SUPER_VALUE,
        )
        self._schedule_vuk_tick()

    def _schedule_vuk_tick(self):
        self.delay.remove("master_plan_vuk_timer_tick")
        if not self.mode_done and self.vuk_lit and self.seconds_left > 0:
            self.delay.add(
                name="master_plan_vuk_timer_tick",
                ms=1000,
                callback=self._vuk_timer_tick,
            )

    def _vuk_timer_tick(self, **kwargs):
        if self.mode_done or not self.vuk_lit:
            return
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            if self.vuk_collected:
                self.machine.events.post("show_mode_message", message_mode_title="BACK PAGE MISSED", message_mode_subtitle="PLOTTER EXPOSED")
                self._complete_mode()
            else:
                self.machine.events.post("show_mode_message", message_mode_title="VUK TIMER EXPIRED", message_mode_subtitle="PLOTTER ESCAPED")
                self._fail_mode()
            return
        self._update_status()
        self._schedule_vuk_tick()

    def _vuk_hit(self, **kwargs):
        self.machine.events.post("up_kick")
        if self.mode_done or not self.vuk_lit or self.vuk_collected:
            return

        self.vuk_collected = True
        self.machine.game.player["master_plan_super_collected"] = 1
        self._score(self.SUPER_VALUE)
        self.machine.events.post("master_plan_super_collected")

        if self.has_case_file("more_jackpots"):
            self.back_page_lit = True
            self.machine.events.post("master_plan_back_page_lit_show")
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="MASTER PLAN SUPER",
                message_mode_subtitle=f"BACK PAGE LIT - {self.seconds_left}s",
                message_mode_value=self.SUPER_VALUE,
            )
            self._update_status()
            return

        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="MASTER PLAN SUPER",
            message_mode_subtitle="THE PLOTTER DEFEATED",
            message_mode_value=self.SUPER_VALUE,
        )
        self._complete_mode()

    def _back_page_hit(self, **kwargs):
        if self.mode_done or not self.back_page_lit:
            return
        self._score(self.BACK_PAGE_VALUE)
        self.machine.events.post("master_plan_back_page_collected")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="BACK PAGE BONUS",
            message_mode_subtitle="THE PLOTTER DEFEATED",
            message_mode_value=self.BACK_PAGE_VALUE,
        )
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("master_plan_vuk_timer_tick")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("master_plan_mode_complete")
        self.machine.events.post("master_plan_clear_lights")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("master_plan_vuk_timer_tick")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 0
        self.machine.events.post("master_plan_mode_complete")
        self.machine.events.post("master_plan_clear_lights")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points

    def _update_status(self):
        if self.mode_done:
            return
        self.machine.game.player["active_mode_hits"] = self.rumors
        if self.back_page_lit:
            objective = f"BACK PAGE {self.seconds_left}s"
        elif self.vuk_lit:
            objective = f"VUK {self.seconds_left}s"
        elif self.lit_saucers:
            lit = ",".join(str(saucer) for saucer in sorted(self.lit_saucers))
            objective = f"SAUCERS {lit}"
        else:
            objective = "POPS THEN SPINNER"
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="RUMORS / SCHEMES",
            mode_status_value=f"{self.rumors} / {self.schemes}   {objective}",
        )
