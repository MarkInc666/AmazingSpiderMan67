import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class DoctorDumpty(CaseFileMixin, Mode):
    MODE_KEY = "doctor_dumpty"
    DISPLAY_NAME = "Doctor Dumpty"

    DROP_VALUE = 75_000
    BIGGER_DROP_VALUE = 100_000
    GAS_VALUE = 200_000
    BIGGER_GAS_VALUE = 250_000
    UPPER_JP_START = 350_000
    BIGGER_UPPER_JP_START = 500_000
    SPINNER_STEP = 50_000
    ROOF_SECONDS = 16
    MORE_TIME_ROOF_SECONDS = 20

    GAS_AREAS = ("left_sling", "right_sling", "left_pop", "right_pop", "right_bank")
    DROP_REVEAL_COUNTS = (1, 1, 1)
    MORE_JP_REVEAL_COUNTS = (1, 2, 2)

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=2)
        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "gas"
        self.mode_points = 0
        self.balloons_popped = 0
        self.revealed_gas = set()
        self.cleared_gas = set()
        self.used_left_drops = set()
        self.shot_assist_available = self.has_case_file("shot_assist")
        self.more_jackpots = self.has_case_file("more_jackpots")
        self.bigger_jackpots = self.has_case_file("bigger_jackpots")
        self.gas_required = 5 if self.more_jackpots else 3
        self.drop_reveal_counts = self.MORE_JP_REVEAL_COUNTS if self.more_jackpots else self.DROP_REVEAL_COUNTS
        self.drop_value = self.BIGGER_DROP_VALUE if self.bigger_jackpots else self.DROP_VALUE
        self.gas_value = self.BIGGER_GAS_VALUE if self.bigger_jackpots else self.GAS_VALUE
        self.upper_jp = self.BIGGER_UPPER_JP_START if self.bigger_jackpots else self.UPPER_JP_START
        self.roof_seconds = self.MORE_TIME_ROOF_SECONDS if self.has_case_file("more_time") else self.ROOF_SECONDS
        self.seconds_left = 0

        player = self.machine.game.player if self.machine.game else None
        if player:
            player["doctor_dumpty_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "REVEAL AND CLEAR ALL 5 GAS AREAS"),
            ("bigger_jackpots", "BIGGER DROP / GAS / BALLOON JACKPOTS"),
            ("more_time", "20 SECONDS ON THE ROOF"),
            ("safety_net", "BALL SAVE ACTIVE"),
            ("shot_assist", "CLEAR AN EXTRA GAS AREA OR DOUBLE FIRST BALLOON HIT"),
        ])

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        for drop_num in (1, 2, 3):
            self.add_mode_event_handler(f"doctor_dumpty_left_drop_{drop_num}", self._left_drop_hit, drop_num=drop_num)
        for area in self.GAS_AREAS:
            self.add_mode_event_handler(f"doctor_dumpty_gas_{area}", self._gas_hit, area=area)
        self.add_mode_event_handler("doctor_dumpty_upper_entry", self._upper_entry)
        self.add_mode_event_handler("doctor_dumpty_upper_target_hit", self._upper_target_hit)
        self.add_mode_event_handler("doctor_dumpty_upper_spinner_hit", self._upper_spinner_hit)

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("doctor_dumpty_startup_complete")
        self.machine.events.post("doctor_dumpty_gas_phase_started")
        self.machine.events.post("show_mode_message_long", message_mode_title="CLEAR THE LAUGHING GAS", message_mode_subtitle="HIT LEFT DROPS TO FIND IT")
        self._update_status()

    def mode_stop(self, **kwargs):
        self.delay.remove("doctor_dumpty_roof_tick")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("doctor_dumpty_all_lights_off")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _left_drop_hit(self, drop_num=None, **kwargs):
        if self.mode_done or self.phase != "gas" or drop_num in self.used_left_drops:
            return
        self.used_left_drops.add(drop_num)
        self._score(self.drop_value)

        reveal_count = self.drop_reveal_counts[drop_num - 1]
        choices = [area for area in self.GAS_AREAS if area not in self.revealed_gas]
        for area in random.sample(choices, min(reveal_count, len(choices))):
            self.revealed_gas.add(area)
            self.machine.events.post(f"doctor_dumpty_light_gas_{area}")

        self.machine.events.post("show_mode_message", message_mode_title="GAS FOUND", message_mode_subtitle=f"{len(self.revealed_gas)} OF {self.gas_required}")
        self._sync_vars()
        self._update_status()

    def _gas_hit(self, area=None, **kwargs):
        if self.mode_done or self.phase != "gas" or area not in self.revealed_gas or area in self.cleared_gas:
            return

        self._clear_gas_area(area, award=True)

        # Do not consume Shot Assist unless there is a second lit gas area to clear.
        if self.shot_assist_available:
            other_lit = [candidate for candidate in self.revealed_gas if candidate not in self.cleared_gas]
            if other_lit:
                assisted_area = random.choice(other_lit)
                self._clear_gas_area(assisted_area, award=True)
                self.shot_assist_available = False
                self.machine.events.post("doctor_dumpty_shot_assist_used")

        if len(self.cleared_gas) >= self.gas_required:
            self._gas_complete()
        else:
            self._sync_vars()
            self._update_status()

    def _clear_gas_area(self, area, award=True):
        if area in self.cleared_gas:
            return
        self.cleared_gas.add(area)
        if award:
            self._score(self.gas_value)
        self.machine.events.post(f"doctor_dumpty_stop_gas_{area}")
        self.machine.events.post("doctor_dumpty_gas_cleared", area=area, value=self.gas_value)

    def _gas_complete(self):
        self.phase = "get_to_roof"
        self.machine.events.post("doctor_dumpty_gas_phase_complete")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("show_mode_message_long", message_mode_title="GAS CLEARED", message_mode_subtitle="GET TO THE ROOFTOP")
        self._sync_vars()
        self._update_status()

    def _upper_entry(self, **kwargs):
        if self.mode_done or self.phase != "get_to_roof":
            return
        self.phase = "roof"
        self.seconds_left = self.roof_seconds
        self.machine.events.post("doctor_dumpty_roof_phase_started")
        self.machine.events.post("show_mode_countdown", message_mode_title="POP THE BALLOONS", message_mode_subtitle="HIT UPPER TARGETS", message_mode_value=self.upper_jp, message_mode_seconds=self.seconds_left)
        self._sync_vars()
        self._update_status()
        self._schedule_roof_tick()

    def _schedule_roof_tick(self):
        self.delay.remove("doctor_dumpty_roof_tick")
        self.delay.add(name="doctor_dumpty_roof_tick", ms=1000, callback=self._roof_tick)

    def _roof_tick(self, **kwargs):
        if self.mode_done or self.phase != "roof":
            return
        self.seconds_left = max(0, self.seconds_left - 1)
        self._sync_vars()
        self._update_status()
        if self.seconds_left <= 0:
            self._complete_mode()
        else:
            self._schedule_roof_tick()

    def _upper_target_hit(self, **kwargs):
        if self.mode_done or self.phase != "roof":
            return

        hit_count = 1
        if self.shot_assist_available:
            hit_count = 2
            self.shot_assist_available = False
            self.machine.events.post("doctor_dumpty_shot_assist_used")

        award = self.upper_jp * hit_count
        self.balloons_popped += hit_count
        self._score(award)
        # One physical hit = one popping SFX even when Shot Assist counts it twice.
        self.machine.events.post("doctor_dumpty_balloon_popped", value=award, hit_count=hit_count)
        self.machine.events.post("show_mode_jackpot", message_mode_title="BALLOON POPPED", message_mode_subtitle=f"{self.balloons_popped} POPPED", message_mode_value=award)
        self._sync_vars()
        self._update_status()

    def _upper_spinner_hit(self, **kwargs):
        if self.mode_done or self.phase != "roof":
            return
        self.upper_jp += self.SPINNER_STEP
        self.machine.events.post("doctor_dumpty_upper_jp_changed", value=self.upper_jp)
        self._sync_vars()
        self._update_status()

    def _score(self, value):
        player = self.machine.game.player if self.machine.game else None
        if player:
            player["score"] += int(value)
        self.mode_points += int(value)

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("doctor_dumpty_roof_tick")
        self.machine.events.post("doctor_dumpty_all_lights_off")
        self.machine.events.post("rooftop_diverter_close")
        player = self.machine.game.player if self.machine.game else None
        if player:
            player["doctor_dumpty_state"] = 2
        self._sync_vars()
        self.machine.events.post("show_mode_message_long", message_mode_title="DOCTOR DUMPTY DEFEATED", message_mode_subtitle=f"{self.balloons_popped} BALLOONS POPPED")
        self.machine.events.post("doctor_dumpty_mode_complete")

    def _sync_vars(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.balloons_popped
        player["doctor_dumpty_timer_seconds"] = self.seconds_left
        player["doctor_dumpty_next_jackpot"] = self.upper_jp

    def _update_status(self):
        if self.phase == "gas":
            title = "GAS CLEARED"
            value = f"{len(self.cleared_gas)} / {self.gas_required}"
        elif self.phase == "get_to_roof":
            title = "GET TO THE ROOF"
            value = "GATE OPEN"
        elif self.phase == "roof":
            self.machine.events.post(
                "update_mode_timer_status",
                mode_status_title=f"BALLOON JP {self.upper_jp:,}",
                mode_status_value=max(0, self.seconds_left),
            )
            return
        else:
            return
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)
