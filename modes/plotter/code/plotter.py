import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Plotter(CaseFileMixin, Mode):
    """The Plotter villain mode: build rumors, expose three schemes, collect the VUK Super."""

    MODE_KEY = "plotter"
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
    BIGGER_JACKPOTS_MULTIPLIER = 2

    def _post_mode_jackpot_sfx_if_needed(
        self,
        guarded_display_event="",
        message_mode_title="",
        message_mode_subtitle="",
    ):
        """Mode-local jackpot SFX hook; replace these events per mode as desired."""
        if guarded_display_event != "base_show_mode_jackpot":
            return
        title = str(message_mode_title or "").upper()
        subtitle = str(message_mode_subtitle or "").upper()
        combined = f"{title} {subtitle}".replace("-", " ")
        words = combined.split()
        if "JACKPOT" not in words:
            return
        if any(marker in title.split() for marker in ("BUILDS", "LIT", "READY", "NEXT")):
            return
        if "SUPER" in words:
            self.machine.events.post("play_mode_super_jackpot")
        else:
            self.machine.events.post("play_mode_jackpot")

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.rumors = 0
        self.rumor_hits = 0
        self.lit_saucers = set()
        self.schemes = 0
        self.mode_points = 0
        self.vuk_lit = False
        self.vuk_collected = False
        self.back_page_lit = False
        self.seconds_left = 0
        self.shot_assist_used = False
        self.lighting_phase = None

        self.case_files = self.get_case_file_bonuses()
        self.vuk_seconds = self.MORE_TIME_VUK_SECONDS if self.has_case_file("more_time") else self.VUK_SECONDS
        self.build_score_multiplier = (
            self.BIGGER_JACKPOTS_MULTIPLIER
            if self.has_case_file("bigger_jackpots")
            else 1
        )

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_stat_1"] = 0
        player["active_mode_stat_2"] = 0

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "BACK PAGE SHOT AFTER VUK"),
            ("bigger_jackpots", "POPS, SPINNER AND SCHEMES SCORE 2X"),
            ("more_time", "VUK TIMER EXTENDED TO 30 SECONDS"),
            ("safety_net", "BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST UNLIT SAUCER COLLECTS A LIT SAUCER"),
        ])
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.add_mode_event_handler("plotter_pop_hit", self._pop_hit)
        self.add_mode_event_handler("plotter_spinner_hit", self._spinner_hit)
        for saucer in self.SAUCERS:
            self.add_mode_event_handler(f"plotter_saucer_{saucer}_hit", self._saucer_hit, saucer=saucer)
        self.add_mode_event_handler("plotter_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("plotter_back_page_hit", self._back_page_hit)
        self.add_mode_event_handler("plotter_complete_request", self._complete_mode)
        self.add_mode_event_handler("plotter_fail_request", self._fail_mode)
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
        self.machine.events.post("plotter_clear_lights")
        self.machine.events.post("plotter_vuk_chase_stop")
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        # Catch-all: no delayed villain/wizard callback may survive into bonus.
        self.delay.clear()
        super().mode_stop(**kwargs)

    def _ball_ending(self, **kwargs):
        self.mode_done = True
        self._cleanup_mode_display_and_delays()

    def _cleanup_mode_display_and_delays(self):
        if hasattr(self, "delay"):
            self.delay.remove("plotter_vuk_timer_tick")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")

    def _pop_hit(self, **kwargs):
        if self.mode_done:
            return
        spinner_was_ready = self.rumors >= self.RUMORS_TO_LIGHT_SAUCER
        self.rumors += 1
        self.rumor_hits += 1
        self.machine.game.player["active_mode_stat_1"] = self.rumor_hits
        self._score(self._boosted_value(self.POP_VALUE))
        if not spinner_was_ready and self.rumors >= self.RUMORS_TO_LIGHT_SAUCER:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="SPINNER READY",
                message_mode_subtitle="SHOOT THE YELLOW LOWER SPINNER",
            )
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
        self._score(self._boosted_value(self.SPINNER_VALUE))
        self._light_random_saucer(available)

        self.machine.events.post(
            "show_mode_message",
            message_mode_title="SAUCER LIT",
            message_mode_subtitle="COLLECT THE RED SAUCER",
        )
        self._update_status()

    def _light_random_saucer(self, available):
        saucer = random.choice(available)
        self.lit_saucers.add(saucer)
        self.machine.events.post(f"plotter_saucer_{saucer}_lit")

    def _saucer_hit(self, saucer, **kwargs):
        self.machine.events.post(f"delayed_kickout_saucer_{saucer}")
        if self.mode_done or self.vuk_lit or not self.lit_saucers:
            return

        assisted = False
        collected_saucer = saucer
        if saucer not in self.lit_saucers:
            if not self.has_case_file("shot_assist") or self.shot_assist_used:
                return
            self.shot_assist_used = True
            assisted = True
            collected_saucer = random.choice(sorted(self.lit_saucers))

        self.lit_saucers.remove(collected_saucer)
        self.machine.events.post(f"plotter_saucer_{collected_saucer}_collected")
        self.schemes += 1
        scheme_value = self._boosted_value(self.SCHEME_VALUE)
        self._score(scheme_value)
        player = self.machine.game.player
        player["active_mode_stat_2"] = self.schemes

        if self.schemes >= 3:
            self._start_vuk_timer()
        else:
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="SHOT ASSIST" if assisted else "SCHEME STOPPED",
                message_mode_subtitle=(
                    f"SAUCER {collected_saucer} COLLECTED — {self.schemes} OF 3"
                    if assisted
                    else f"{self.schemes} OF 3"
                ),
                message_mode_value=scheme_value,
            )
        self._update_status()

    def _start_vuk_timer(self):
        if self.vuk_lit or self.mode_done:
            return

        # Shot Assist can leave another saucer lit when the third scheme is
        # collected. Once the VUK phase begins, no surplus scheme remains live.
        for saucer in tuple(self.lit_saucers):
            self.machine.events.post(f"plotter_saucer_{saucer}_collected")
        self.lit_saucers.clear()

        self.vuk_lit = True
        self.machine.events.post("plotter_vuk_chase_start")
        self.seconds_left = self.vuk_seconds
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="THE PLOTTER EXPOSED",
            message_mode_subtitle=f"SHOOT DAILY BUGLE VUK - {self.seconds_left}s",
            message_mode_value=self.SUPER_VALUE,
        )
        self._refresh_objective_lighting()
        self._schedule_vuk_tick()

    def _schedule_vuk_tick(self):
        self.delay.remove("plotter_vuk_timer_tick")
        if not self.mode_done and self.vuk_lit and self.seconds_left > 0:
            self.delay.add(
                name="plotter_vuk_timer_tick",
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
        if self.mode_done or not self.vuk_lit or self.vuk_collected:
            self.machine.events.post("request_vuk_eject")
            return

        self.vuk_collected = True
        self.machine.events.post("plotter_vuk_chase_stop")
        self._score(self.SUPER_VALUE)

        if self.has_case_file("more_jackpots"):
            self.back_page_lit = True
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="THE PLOTTER SUPER",
                message_mode_subtitle=f"BACK PAGE LIT - {self.seconds_left}s",
                message_mode_value=self.SUPER_VALUE,
            )
            self._update_status()
            self.machine.events.post("request_vuk_eject")
            return

        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="THE PLOTTER SUPER",
            message_mode_subtitle="THE PLOTTER DEFEATED",
            message_mode_value=self.SUPER_VALUE,
        )
        self.machine.events.post("villain_summary_hold_vuk_until_done")
        self._complete_mode()

    def _back_page_hit(self, **kwargs):
        if self.mode_done or not self.back_page_lit:
            return
        self._score(self.BACK_PAGE_VALUE)
        self.machine.events.post("plotter_back_page_collected")
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
        self.machine.events.post("plotter_vuk_chase_stop")
        self.mode_done = True
        self.delay.remove("plotter_vuk_timer_tick")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("plotter_mode_complete")
        self.machine.events.post("plotter_clear_lights")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.machine.events.post("plotter_vuk_chase_stop")
        self.mode_done = True
        self.delay.remove("plotter_vuk_timer_tick")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 0
        self.machine.events.post("plotter_mode_complete")
        self.machine.events.post("plotter_clear_lights")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points

    def _boosted_value(self, base_value):
        return base_value * self.build_score_multiplier

    def _refresh_objective_lighting(self):
        if self.mode_done:
            return

        if self.back_page_lit:
            phase = "back_page"
        elif self.vuk_lit:
            phase = "vuk"
        elif len(self.lit_saucers) >= len(self.SAUCERS):
            phase = "saucers_only"
        elif self.rumors >= self.RUMORS_TO_LIGHT_SAUCER:
            phase = "spinner"
        else:
            phase = "pops"

        if phase == self.lighting_phase:
            return

        self.lighting_phase = phase
        self.machine.events.post("plotter_clear_guidance_lights")
        if phase != "saucers_only":
            self.machine.events.post(f"plotter_{phase}_lights")

    def _update_status(self):
        if self.mode_done:
            return
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
        self._refresh_objective_lighting()
