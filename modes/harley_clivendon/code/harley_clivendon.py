import random
from functools import partial

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class HarleyClivendon(CaseFileMixin, Mode):
    MODE_KEY = "harley_clivendon"
    AREA_SCORE = 50_000
    SAUCER_SCORE = 50_000
    BASE_JACKPOT_PER_AREA = 100_000
    BIGGER_JACKPOT_PER_AREA = 150_000
    MIN_JACKPOT_AREAS = 4
    SAFETY_NET_SECONDS = 10
    SAUCER_EJECT_EVENTS = {
        1: "delayed_kickout_saucer_1",
        2: "delayed_kickout_saucer_2",
        3: "delayed_kickout_saucer_3",
    }
    AREAS = (
        "left_sling", "right_sling", "left_pop", "right_pop",
        "left_bank", "right_bank", "left_web", "center_web",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.held_saucer = None
        self.lock_accepting = True
        self.lit_areas = set()
        self.jackpots = 0
        self.biggest_jackpot = 0
        self.safety_net_used = False
        self.shot_assist_used = False
        self.jackpot_per_area = self.BIGGER_JACKPOT_PER_AREA if self.has_case_file("bigger_jackpots") else self.BASE_JACKPOT_PER_AREA
        self.opening_save_seconds = 25 if self.has_case_file("more_time") else 15

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "TWO AREAS STAY LIT"),
            ("bigger_jackpots", "150K PER AREA"),
            ("more_time", "25 SECOND OPENING SAVE"),
            ("safety_net", "BALL SAVE AFTER FIRST JACKPOT"),
            ("shot_assist", "FIRST AREA SPOTS ANOTHER"),
        ])

        for area in self.AREAS:
            self.add_mode_event_handler(f"harley_area_{area}", self._area_hit, area=area)
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(f"harley_saucer_{saucer}", partial(self._saucer_hit, saucer=saucer))
        self.add_mode_event_handler("harley_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("multiball_harley_multiball_ended", self._multiball_ended)

        p = self.machine.game.player
        p["harley_clivendon_state"] = 1
        p["active_mode_points"] = 0
        p["harley_vuk_jackpots"] = 0
        p["harley_biggest_jackpot"] = 0
        p["harley_areas_lit"] = 0
        p["harley_jackpot_value"] = 0
        p["harley_opening_save_seconds"] = self.opening_save_seconds

        self.machine.events.post("reset_drops")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("harley_start_multiball")
        self.machine.events.post("harley_round_reset")
        self.machine.events.post("show_mode_message_long", message_mode_title="HYPNOTIC HOLD", message_mode_subtitle="LOCK A BALL - LIGHT 4 AREAS")
        self._sync()

    def _area_hit(self, area=None, **kwargs):
        if self.mode_done or self.held_saucer is None or area in self.lit_areas:
            return
        self.lit_areas.add(area)
        self._score(self.AREA_SCORE)
        self.machine.events.post(f"harley_area_{area}_lit")
        self.machine.events.post("show_mode_message", message_mode_title="AREA LIT", message_mode_subtitle=area.replace("_", " ").upper(), message_mode_value=self.AREA_SCORE)

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            choices = [x for x in self.AREAS if x not in self.lit_areas]
            if choices:
                assisted = random.choice(choices)
                self.lit_areas.add(assisted)
                self.machine.events.post(f"harley_area_{assisted}_lit")
                self.machine.events.post("show_mode_message", message_mode_title="SHOT ASSIST", message_mode_subtitle=assisted.replace("_", " ").upper())
            self.shot_assist_used = True
        self._sync()

    def _saucer_hit(self, saucer=None, **kwargs):
        if self.mode_done or saucer not in self.SAUCER_EJECT_EVENTS:
            return
        if self.held_saucer is not None or not self.lock_accepting:
            self._eject_saucer(saucer, 750)
            return
        self.held_saucer = saucer
        self.lock_accepting = False
        self._score(self.SAUCER_SCORE)
        self.machine.events.post("harley_saucers_unavailable")
        self.machine.events.post(f"harley_saucer_{saucer}_held")
        self.machine.events.post("show_mode_message_long", message_mode_title="BALL CAPTURED", message_mode_subtitle="LIGHT PLAYFIELD AREAS", message_mode_value=self.SAUCER_SCORE)
        self._sync()

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            self._eject_vuk()
            return
        if self.held_saucer is None or len(self.lit_areas) < self.MIN_JACKPOT_AREAS:
            self._eject_vuk()
            return
        value = len(self.lit_areas) * self.jackpot_per_area
        self._score(value)
        self.jackpots += 1
        self.biggest_jackpot = max(self.biggest_jackpot, value)
        self.machine.events.post("show_mode_jackpot", message_mode_title="HARLEY JACKPOT", message_mode_subtitle=f"{len(self.lit_areas)} AREAS", message_mode_value=value)

        keep = set()
        if self.has_case_file("more_jackpots"):
            keep = set(random.sample(list(self.lit_areas), min(2, len(self.lit_areas))))
        self.lit_areas = keep
        self.machine.events.post("harley_round_reset")
        for area in keep:
            self.machine.events.post(f"harley_area_{area}_lit")

        held = self.held_saucer
        self.held_saucer = None
        self._eject_saucer(held, 1000)
        self._eject_vuk(1000)
        self.delay.reset(name="harley_accept_next_lock", ms=2200, callback=self._enable_next_lock)

        if self.has_case_file("safety_net") and not self.safety_net_used:
            self.safety_net_used = True
            self.machine.events.post("start_case_file_ball_save")
            self.machine.events.post("harley_safety_net_started")
        self._sync()

    def _enable_next_lock(self):
        if self.mode_done:
            return
        self.lock_accepting = True
        self.machine.events.post("harley_saucers_available")
        self._sync()

    def _eject_saucer(self, saucer, delay_ms=0):
        event = self.SAUCER_EJECT_EVENTS.get(saucer)
        if event:
            self.delay.reset(name=f"harley_eject_saucer_{saucer}", ms=delay_ms, callback=self.machine.events.post, event=event)

    def _eject_vuk(self, delay_ms=750):
        self.delay.reset(name="harley_vuk_eject", ms=delay_ms, callback=self.machine.events.post, event="up_kick")

    def _multiball_ended(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        if self.held_saucer is not None:
            self._eject_saucer(self.held_saucer)
        self.machine.game.player["harley_clivendon_state"] = 2
        self.machine.events.post("harley_clivendon_mode_complete")

    def _score(self, points):
        p = self.machine.game.player
        p["score"] += points
        p["active_mode_points"] += points

    def _sync(self):
        p = self.machine.game.player
        value = len(self.lit_areas) * self.jackpot_per_area
        p["harley_areas_lit"] = len(self.lit_areas)
        p["harley_jackpot_value"] = value
        p["harley_vuk_jackpots"] = self.jackpots
        p["harley_biggest_jackpot"] = self.biggest_jackpot
        title = f"AREAS {len(self.lit_areas)}/8"
        status = "LOCK A BALL"
        if self.held_saucer is not None:
            status = f"VUK JACKPOT {value:,}" if len(self.lit_areas) >= 4 else "LIGHT 4 AREAS"
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=status)
        self.machine.events.post("harley_vuk_ready" if self.held_saucer is not None and len(self.lit_areas) >= 4 else "harley_vuk_not_ready")

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("harley_mode_ended")
        self.clear_active_case_file_helpers()
        if self.held_saucer is not None:
            self._eject_saucer(self.held_saucer)
        self._eject_vuk(0)
        super().mode_stop(**kwargs)
