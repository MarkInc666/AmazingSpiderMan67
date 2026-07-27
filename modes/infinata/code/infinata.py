import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Infinata(CaseFileMixin, Mode):
    MODE_KEY = "infinata"
    DISPLAY_NAME = "Infinata"

    AREAS = ("pops", "left_drops", "right_drops", "webs", "upper_targets")
    REQUIRED_AREAS = 3
    MORE_JACKPOTS_AREAS = 4
    POP_HITS_REQUIRED = 2
    AREA_VALUES = (200_000, 300_000, 400_000, 500_000)
    BIGGER_AREA_VALUES = (300_000, 450_000, 600_000, 750_000)
    SUPER_VALUE = 1_000_000
    BIGGER_SUPER_VALUE = 1_500_000
    SUPER_SECONDS = 20
    MORE_TIME_SUPER_SECONDS = 30

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.phase = "areas"
        self.mode_points = 0
        self.completed_areas = 0
        self.super_jackpots = 0
        self.super_seconds_left = 0
        self.shot_assist_used = False
        self.active_area = None
        self.area_progress = set()
        self.roof_gate_requested = False

        self.case_files = self.get_case_file_bonuses()
        area_count = self.MORE_JACKPOTS_AREAS if self.has_case_file("more_jackpots") else self.REQUIRED_AREAS
        self.selected_areas = random.sample(list(self.AREAS), area_count)
        self.area_values = self.BIGGER_AREA_VALUES if self.has_case_file("bigger_jackpots") else self.AREA_VALUES
        self.super_value = self.BIGGER_SUPER_VALUE if self.has_case_file("bigger_jackpots") else self.SUPER_VALUE
        self.super_seconds = self.MORE_TIME_SUPER_SECONDS if self.has_case_file("more_time") else self.SUPER_SECONDS

        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player["infinata_state"] = 1

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "4TH GREEN AREA AVAILABLE DURING SUPER"),
            ("bigger_jackpots", "BIGGER AREA AWARDS AND 1.5M SUPER"),
            ("more_time", "SUPER TIMER EXTENDED TO 30 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST HIT AWARDS TWO AREAS"),
        ])
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        for area in self.AREAS:
            self.add_mode_event_handler(f"infinata_{area}_hit", self._area_hit, area=area)
        self.add_mode_event_handler("infinata_saucer_hit", self._saucer_hit)
        self.add_mode_event_handler("infinata_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("infinata_complete_request", self._complete_mode)
        self.add_mode_event_handler("infinata_fail_request", self._fail_mode)

        self.machine.events.post("infinata_mode_started")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("reset_drops")
        self._light_next_area()

    def mode_stop(self, **kwargs):
        self.delay.remove("infinata_super_tick")
        self.delay.remove("infinata_vuk_eject")
        self._close_roof_gate_if_requested()
        self.machine.events.post("infinata_clear_lights")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("reset_drops")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _light_next_area(self):
        if self.mode_done:
            return
        if self.completed_areas >= len(self.selected_areas):
            return
        self.active_area = self.selected_areas[self.completed_areas]
        self.area_progress = set()
        self.machine.events.post("infinata_clear_area_lights")
        if self.active_area == "upper_targets":
            self._open_roof_gate_for_upper_targets()
        else:
            self._close_roof_gate_if_requested()
        self.machine.events.post(f"infinata_light_{self.active_area}")
        self._show_message("BANISH THE CREATURES", self.active_area.replace("_", " ").upper(), reminder=True)
        self._sync_vars()

    def _area_hit(self, area=None, switch=None, **kwargs):
        if self.mode_done or area != self.active_area:
            return
        if self.phase not in ("areas", "super"):
            return

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            self._complete_active_area(assisted=True)
            if self.completed_areas < self.REQUIRED_AREAS:
                self._complete_active_area(assisted=True)
            return

        if not switch:
            return

        # Multi-shot areas require unique switches. Repeat hits on an already
        # counted pop or web target do not advance progress.
        if switch in self.area_progress:
            return

        self.area_progress.add(switch)

        if area == "pops":
            self.machine.events.post(f"infinata_{switch}_complete")
            needed = self.POP_HITS_REQUIRED
        elif area == "webs":
            self.machine.events.post(f"infinata_{switch}_complete")
            needed = 2
        else:
            # Either drop bank and the three upper targets each act as one
            # grouped shot: any valid switch completes that area.
            needed = 1

        if len(self.area_progress) >= needed:
            self._complete_active_area()
        else:
            self._sync_vars()

    def _complete_active_area(self, assisted=False):
        if self.active_area is None or self.completed_areas >= len(self.selected_areas):
            return
        area = self.active_area
        self.machine.events.post(f"infinata_unlight_{area}")
        if area == "upper_targets":
            self._close_roof_gate_if_requested()
        value = self.area_values[min(self.completed_areas, len(self.area_values) - 1)]
        self.completed_areas += 1
        self._score(value)
        subtitle = f"{self.completed_areas} OF 3 CLEARED"
        if self.completed_areas > 3:
            subtitle = "BONUS AREA CLEARED"
        if assisted:
            subtitle = f"SHOT ASSIST - {subtitle}"
        self._show_jackpot("AREA CLEARED", value, subtitle)
        self.active_area = None
        self.area_progress = set()
        self._sync_vars()

        if self.completed_areas == self.REQUIRED_AREAS:
            self._start_super_phase()
            return
        if self.completed_areas < len(self.selected_areas):
            self._light_next_area()

    def _start_super_phase(self):
        self.phase = "super"
        self.super_seconds_left = self.super_seconds
        self.machine.events.post("infinata_light_saucers")
        if self.completed_areas < len(self.selected_areas):
            self._light_next_area()
        else:
            self._show_countdown()
        self._schedule_super_tick()

    def _schedule_super_tick(self):
        self.delay.reset(name="infinata_super_tick", ms=1000, callback=self._super_tick)

    def _super_tick(self):
        if self.mode_done or self.phase != "super":
            return
        self.super_seconds_left -= 1
        self._sync_vars()
        if self.super_seconds_left <= 0:
            self._fail_mode()
            return
        self._show_countdown()
        self._schedule_super_tick()

    def _show_countdown(self):
        subtitle = "SHOOT ANY SAUCER"
        if self.active_area:
            subtitle = f"OPTIONAL {self.active_area.replace('_', ' ').upper()} - OR SAUCER"
        self.machine.events.post("show_mode_countdown", message_mode_title="INFINATA SUPER", message_mode_subtitle=subtitle, message_mode_value="", message_mode_seconds=self.super_seconds_left)


    def _vuk_hit(self, **kwargs):
        """Kick balls out of the Daily Bugle VUK while Infinata owns the mode.

        Daily Bugle Mystery is disabled during villain play, so Infinata must
        provide the VUK response itself. This is especially important when the
        rooftop gate is open for the upper-target area and the VUK is acting as
        the feed to the upper playfield.
        """
        self.delay.remove("infinata_vuk_eject")
        self.delay.add(
            name="infinata_vuk_eject",
            ms=1000,
            callback=lambda: self.machine.events.post("up_kick"),
        )

    def _saucer_hit(self, **kwargs):
        if self.mode_done or self.phase != "super":
            return
        self.delay.remove("infinata_super_tick")
        self.super_jackpots = 1
        self._score(self.super_value)
        self.machine.events.post("infinata_super_collected", value=self.super_value)
        self._show_jackpot("SUPER JACKPOT", self.super_value, "INFINATA DEFEATED")
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player["infinata_state"] = 2
        self._sync_vars()
        self.machine.events.post("infinata_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player["infinata_state"] = 2
        self._sync_vars()
        self._show_message("INFINATA ESCAPES", "THE FIFTH DIMENSION CLOSES")
        self.machine.events.post("infinata_mode_complete")

    def _score(self, points):
        self.machine.game.player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _open_roof_gate_for_upper_targets(self):
        if self.roof_gate_requested:
            return
        self.roof_gate_requested = True
        self.machine.events.post("rooftop_diverter_open")

    def _close_roof_gate_if_requested(self):
        if not self.roof_gate_requested:
            return
        self.roof_gate_requested = False
        self.machine.events.post("rooftop_diverter_close")

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.completed_areas
        player["active_mode_major_hits"] = self.super_jackpots
        player["infinata_areas_completed"] = self.completed_areas
        player["infinata_super_seconds"] = self.super_seconds_left

    def _show_message(self, title, subtitle="", reminder=False):
        self.machine.events.post("show_mode_message", message_mode_title=title, message_mode_subtitle=subtitle, message_mode_value="", message_mode_seconds="", reminder=reminder)

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post("show_mode_jackpot", message_mode_title=title, message_mode_subtitle=subtitle, message_mode_value=value, message_mode_seconds="")
