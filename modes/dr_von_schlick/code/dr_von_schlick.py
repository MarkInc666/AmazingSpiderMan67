from mpf.core.delays import DelayManager
from mpf.core.mode import Mode

from modes.common.case_file_mixin import CaseFileMixin


class DrVonSchlick(CaseFileMixin, Mode):
    """Dr. Von Schlick: collect moving Oil Pellets, then flood the reactor."""

    MODE_KEY = "dr_von_schlick"
    DISPLAY_NAME = "Dr. Von Schlick"

    SHOT_ORDER = (
        "left_web",
        "left_drops",
        "left_pop",
        "center_web",
        "right_pop",
        "right_drops",
    )

    SHOT_SECONDS = 4
    PELLETS_TO_SUPER = 5
    MORE_JACKPOTS_PELLETS = 7
    BASE_PELLET_VALUE = 100_000
    BIGGER_PELLET_VALUE = 150_000
    SUPER_VALUE = 1_000_000
    SUPER_SECONDS = 20
    MORE_TIME_SUPER_SECONDS = 30
    FLOOD_BANDS = 8

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.phase = "pellets"
        self.mode_points = 0
        self.pellets = 0
        self.super_jackpots = 0
        self.current_index = 0
        self.direction = 1
        self.shot_assist_used = False
        self.super_seconds_left = 0

        self.case_files = self.get_case_file_bonuses()
        self.pellet_value = (
            self.BIGGER_PELLET_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.BASE_PELLET_VALUE
        )
        self.pellet_limit = (
            self.MORE_JACKPOTS_PELLETS
            if self.has_case_file("more_jackpots")
            else self.PELLETS_TO_SUPER
        )
        self.super_seconds = (
            self.MORE_TIME_SUPER_SECONDS
            if self.has_case_file("more_time")
            else self.SUPER_SECONDS
        )

        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player[f"{self.MODE_KEY}_state"] = 1

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "TWO EXTRA OIL PELLETS AVAILABLE"),
            ("bigger_jackpots", "OIL PELLETS WORTH 150K"),
            ("more_time", "SUPER TIMER EXTENDED TO 30 SECONDS"),
            ("safety_net", "BALL SAVE STARTS WITH SUPER"),
            ("shot_assist", "FIRST PELLET COUNTS TWICE"),
        ])

        for shot in self.SHOT_ORDER:
            self.add_mode_event_handler(
                f"dr_von_schlick_{shot}_hit", self._shot_hit, shot=shot
            )
        self.add_mode_event_handler("dr_von_schlick_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("dr_von_schlick_complete_request", self._complete_mode)
        self.add_mode_event_handler("dr_von_schlick_fail_request", self._fail_mode)

        self.machine.events.post("dr_von_schlick_gi_red")
        self.machine.events.post("dr_von_schlick_clear_shot_lights")
        self._light_current_shot()
        self._schedule_move()
        self._show_message("OIL PELLETS", "FOLLOW THE GREEN SHOT", self.pellet_value, reminder=True)
        self._sync_vars()

    def mode_stop(self, **kwargs):
        for name in ("dr_von_schlick_move_shot", "dr_von_schlick_super_tick"):
            self.delay.remove(name)
        for band in range(1, self.FLOOD_BANDS + 1):
            self.delay.remove(f"dr_von_schlick_flood_{band}")
        self.machine.events.post("dr_von_schlick_clear_shot_lights")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _shot_hit(self, shot=None, **kwargs):
        if self.mode_done or self.phase not in ("pellets", "super"):
            return
        if self.pellets >= self.pellet_limit or shot != self.current_shot:
            return

        awards = 1
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            awards = 2

        for _ in range(awards):
            if self.pellets >= self.pellet_limit:
                break
            self.pellets += 1
            self._score(self.pellet_value)

        self.machine.events.post(
            "dr_von_schlick_pellet_collected",
            pellets=self.pellets,
            pellet_limit=self.pellet_limit,
            value=self.pellet_value * awards,
        )
        self._show_message(
            "OIL PELLET",
            f"{self.pellets} / {self.pellet_limit}",
            self.pellet_value * awards,
        )

        if self.pellets >= self.PELLETS_TO_SUPER and self.phase == "pellets":
            self._qualify_super()

        if self.pellets >= self.pellet_limit:
            self.delay.remove("dr_von_schlick_move_shot")
            self.machine.events.post("dr_von_schlick_clear_moving_lights")
        else:
            self._advance_shot()
            self._schedule_move()
        self._sync_vars()

    @property
    def current_shot(self):
        return self.SHOT_ORDER[self.current_index]

    def _schedule_move(self):
        self.delay.remove("dr_von_schlick_move_shot")
        if self.mode_done or self.pellets >= self.pellet_limit:
            return
        self.delay.add(
            name="dr_von_schlick_move_shot",
            ms=self.SHOT_SECONDS * 1000,
            callback=self._move_timeout,
        )

    def _move_timeout(self):
        if self.mode_done or self.phase not in ("pellets", "super"):
            return
        self._advance_shot()
        self._schedule_move()

    def _advance_shot(self):
        next_index = self.current_index + self.direction
        if next_index >= len(self.SHOT_ORDER):
            self.direction = -1
            next_index = len(self.SHOT_ORDER) - 2
        elif next_index < 0:
            self.direction = 1
            next_index = 1
        self.current_index = next_index
        self._light_current_shot()

    def _light_current_shot(self):
        self.machine.events.post("dr_von_schlick_clear_moving_lights")
        if self.pellets < self.pellet_limit:
            self.machine.events.post(f"dr_von_schlick_light_{self.current_shot}")

    def _qualify_super(self):
        self.phase = "super"
        self.super_seconds_left = self.super_seconds
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("dr_von_schlick_light_vuk")
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")
        self._show_message("REACTOR READY", "SHOOT VUK", self.SUPER_VALUE, self.super_seconds_left, reminder=True)
        self.delay.add(name="dr_von_schlick_super_tick", ms=1000, callback=self._super_tick)

    def _super_tick(self):
        if self.mode_done or self.phase != "super":
            return
        self.super_seconds_left -= 1
        if self.super_seconds_left <= 0:
            self._fail_mode()
            return
        self._show_message("REACTOR READY", "SHOOT VUK", self.SUPER_VALUE, self.super_seconds_left, reminder=True)
        self.delay.add(name="dr_von_schlick_super_tick", ms=1000, callback=self._super_tick)

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            return
        if self.phase != "super":
            self.machine.events.post("up_kick")
            return
        self.phase = "flood"
        self.delay.remove("dr_von_schlick_move_shot")
        self.delay.remove("dr_von_schlick_super_tick")
        self.machine.events.post("dr_von_schlick_clear_shot_lights")
        self._show_message("FLOOD THE REACTOR", "WATER RISING", self.SUPER_VALUE)
        for band in range(1, self.FLOOD_BANDS + 1):
            self.delay.add(
                name=f"dr_von_schlick_flood_{band}",
                ms=band * 1000,
                callback=lambda band=band: self._flood_band(band),
            )

    def _flood_band(self, band):
        if self.mode_done or self.phase != "flood":
            return
        self.machine.events.post(f"dr_von_schlick_flood_band_{band}")
        if band >= self.FLOOD_BANDS:
            self._score(self.SUPER_VALUE)
            self.super_jackpots = 1
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="REACTOR FLOODED",
                message_mode_subtitle="SUPER JACKPOT",
                message_mode_value=self.SUPER_VALUE,
            )
            self.machine.events.post("up_kick")
            self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("dr_von_schlick_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("show_mode_message", message_mode_title="REACTOR ESCAPED", message_mode_subtitle="SUPER LOST")
        self.machine.events.post("up_kick")
        self.machine.events.post("dr_von_schlick_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.pellets
        player["active_mode_major_hits"] = self.super_jackpots

    def _show_message(self, title, subtitle="", value="", seconds="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )
