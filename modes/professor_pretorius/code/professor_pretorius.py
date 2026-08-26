import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode

from modes.common.case_file_mixin import CaseFileMixin


class ProfessorPretorius(CaseFileMixin, Mode):
    """Professor Pretorius: finish four reactor stations without overheating."""

    MODE_KEY = "professor_pretorius"
    DISPLAY_NAME = "PROFESSOR PRETORIUS"

    STATION_HITS_REQUIRED = 3
    TOTAL_REACTOR_HITS = 12
    REACTOR_HIT_VALUE = 100_000
    BIGGER_REACTOR_HIT_VALUE = 150_000
    COOLING_VALUE = 50_000
    SUPER_VALUE = 500_000
    SUPER_TIME_MS = 15_000
    MORE_TIME_SUPER_MS = 20_000

    OVERHEAT_TEMPERATURE = 5
    OVERHEAT_GRACE_MS = 4_000
    MORE_TIME_GRACE_MS = 8_000
    SHOT_ASSIST_DELAY_MS = 200

    LEFT_DROP_TARGETS = (1, 2, 3)
    RIGHT_DROP_TARGETS = (1, 2, 3, 4, 5)

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.phase = "reactor"
        self.mode_points = 0
        self.reactor_hits = 0
        self.temperature = 0
        self.cooling_spins = 0
        self.super_jackpots = 0
        self.grace_active = False
        self.overheat_seconds_remaining = 0
        self.super_seconds_remaining = 0
        self.shot_assist_used = False
        self.pop_hits = {"left_pop": 0, "right_pop": 0}
        self.left_drops = set()
        self.right_drops = set()
        self.station_complete = {
            "left_pop": False,
            "right_pop": False,
            "left_bank": False,
            "right_bank": False,
        }

        self.reactor_hit_value = (
            self.BIGGER_REACTOR_HIT_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.REACTOR_HIT_VALUE
        )
        self.overheat_grace_ms = (
            self.MORE_TIME_GRACE_MS
            if self.has_case_file("more_time")
            else self.OVERHEAT_GRACE_MS
        )
        self.super_time_ms = (
            self.MORE_TIME_SUPER_MS
            if self.has_case_file("more_time")
            else self.SUPER_TIME_MS
        )

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "ALL FIVE RIGHT DROPS SCORE"),
            ("bigger_jackpots", "REACTOR HITS WORTH 150K"),
            ("more_time", "OVERHEAT 8s / REACTOR SUPER 20s"),
            ("safety_net", "10 SECOND OPENING BALL SAVE"),
            ("shot_assist", "FIRST LEFT DROP ADDS A RANDOM DROP"),
        ])

        self.add_mode_event_handler("professor_pretorius_left_pop_hit", self._pop_hit, station="left_pop")
        self.add_mode_event_handler("professor_pretorius_right_pop_hit", self._pop_hit, station="right_pop")
        for target in self.LEFT_DROP_TARGETS:
            self.add_mode_event_handler(
                f"professor_pretorius_left_drop_{target}_hit",
                self._left_drop_hit,
                target=target,
            )
        for target in self.RIGHT_DROP_TARGETS:
            self.add_mode_event_handler(
                f"professor_pretorius_right_drop_{target}_hit",
                self._right_drop_hit,
                target=target,
            )
        self.add_mode_event_handler("professor_pretorius_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("professor_pretorius_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("professor_pretorius_complete_request", self._complete_mode)
        self.add_mode_event_handler("professor_pretorius_fail_request", self._fail_mode)

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("reset_drops")
        self.machine.events.post("professor_pretorius_clear_all")
        self.machine.events.post("professor_pretorius_stations_available")
        self._update_temperature_lights()
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")
        self._show_message("PRETORIUS REACTOR", "COMPLETE FOUR EXPERIMENTS", reminder=True)
        self._update_status()

    def mode_stop(self, **kwargs):
        self._clear_delays()
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.machine.events.post("professor_pretorius_clear_all")
        self.machine.events.post("final_vuk_chase_stop")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("reset_drops")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _pop_hit(self, station=None, **kwargs):
        if self.mode_done or self.phase not in ("reactor", "super") or station not in self.pop_hits:
            return
        if self.station_complete[station]:
            return

        self.pop_hits[station] += 1
        self._accept_reactor_hit(station, station.replace("_", " ").upper())

    def _left_drop_hit(self, target=None, **kwargs):
        if self.mode_done or self.phase not in ("reactor", "super") or target not in self.LEFT_DROP_TARGETS:
            return
        if target in self.left_drops or self.station_complete["left_bank"]:
            return

        self.left_drops.add(target)
        self._accept_reactor_hit("left_bank", f"LEFT DROP {target}")

        if self.has_case_file("shot_assist") and not self.shot_assist_used and not self.mode_done:
            self.shot_assist_used = True
            self.delay.reset(
                name="professor_pretorius_shot_assist",
                ms=self.SHOT_ASSIST_DELAY_MS,
                callback=self._apply_shot_assist,
            )

    def _apply_shot_assist(self):
        if self.mode_done or self.station_complete["left_bank"]:
            return
        remaining = [target for target in self.LEFT_DROP_TARGETS if target not in self.left_drops]
        if not remaining:
            return

        target = random.choice(remaining)
        self.left_drops.add(target)
        self.machine.events.post(f"professor_pretorius_drop_left_{target}")
        self.machine.events.post("professor_pretorius_shot_assist_used", target=target)
        self._accept_reactor_hit("left_bank", f"ASSISTED LEFT DROP {target}", assisted=True)

    def _right_drop_hit(self, target=None, **kwargs):
        if self.mode_done or self.phase not in ("reactor", "super") or target not in self.RIGHT_DROP_TARGETS:
            return
        if target in self.right_drops:
            return

        self.right_drops.add(target)
        if not self.station_complete["right_bank"]:
            self._accept_reactor_hit("right_bank", f"RIGHT DROP {target}")
            return

        if self.has_case_file("more_jackpots"):
            self._score(self.reactor_hit_value)
            self.machine.events.post(
                "professor_pretorius_optional_right_drop_scored",
                target=target,
                value=self.reactor_hit_value,
            )
            self._show_message("EXTRA REACTOR JACKPOT", f"RIGHT DROP {target}", value=self.reactor_hit_value)
            self._sync_vars()

    def _accept_reactor_hit(self, station, label, assisted=False):
        if self.mode_done or self.station_complete[station]:
            return

        self.reactor_hits += 1
        self._score(self.reactor_hit_value)
        self.temperature += 1
        self.machine.events.post(
            "professor_pretorius_reactor_hit",
            station=station,
            reactor_hits=self.reactor_hits,
            temperature=self.temperature,
            value=self.reactor_hit_value,
            assisted=assisted,
        )

        if self._station_hits(station) >= self.STATION_HITS_REQUIRED:
            self.station_complete[station] = True
            self.machine.events.post(f"professor_pretorius_{station}_complete")

        self._update_temperature_lights()
        self._update_overheat_grace()

        if self.reactor_hits >= self.TOTAL_REACTOR_HITS and self.phase == "reactor":
            self._qualify_super()
        else:
            self._show_message(
                "REACTOR HIT",
                label,
                value=self.reactor_hit_value,
            )
            self._update_status()
        self._sync_vars()

    def _station_hits(self, station):
        if station in self.pop_hits:
            return self.pop_hits[station]
        if station == "left_bank":
            return len(self.left_drops)
        if station == "right_bank":
            return min(len(self.right_drops), self.STATION_HITS_REQUIRED)
        return 0

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.temperature <= 0:
            return

        self.temperature -= 1
        self.cooling_spins += 1
        self._score(self.COOLING_VALUE)
        self.machine.events.post(
            "professor_pretorius_reactor_cooled",
            temperature=self.temperature,
            value=self.COOLING_VALUE,
        )
        if self.temperature < self.OVERHEAT_TEMPERATURE and self.grace_active:
            self._cancel_overheat_grace()
        self._update_temperature_lights()
        self._show_message("REACTOR COOLED", f"TEMPERATURE {self.temperature}", value=self.COOLING_VALUE)
        self._update_status()
        self._sync_vars()

    def _update_overheat_grace(self):
        if self.temperature < self.OVERHEAT_TEMPERATURE or self.grace_active or self.mode_done:
            return
        self.grace_active = True
        self.overheat_seconds_remaining = self.overheat_grace_ms // 1000
        self.delay.reset(
            name="professor_pretorius_overheat_grace",
            ms=self.overheat_grace_ms,
            callback=self._overheat_grace_expired,
        )
        self.delay.reset(
            name="professor_pretorius_overheat_status_tick",
            ms=1000,
            callback=self._overheat_status_tick,
        )
        self.machine.events.post(
            "professor_pretorius_overheat_started",
            seconds=self.overheat_seconds_remaining,
        )
        self._show_message(
            "REACTOR OVERHEATING",
            f"COOL WITH SPINNER - {self.overheat_seconds_remaining} SECONDS",
            reminder=True,
        )
        self._update_status()

    def _overheat_status_tick(self):
        if self.mode_done or not self.grace_active:
            return
        self.overheat_seconds_remaining = max(0, self.overheat_seconds_remaining - 1)
        if self.overheat_seconds_remaining > 0:
            self._update_status()
            self.delay.reset(
                name="professor_pretorius_overheat_status_tick",
                ms=1000,
                callback=self._overheat_status_tick,
            )

    def _cancel_overheat_grace(self):
        self.grace_active = False
        self.overheat_seconds_remaining = 0
        self.delay.remove("professor_pretorius_overheat_grace")
        self.delay.remove("professor_pretorius_overheat_status_tick")
        self.machine.events.post("professor_pretorius_overheat_cancelled")

    def _overheat_grace_expired(self):
        if self.mode_done:
            return
        self.grace_active = False
        self.overheat_seconds_remaining = 0
        self.delay.remove("professor_pretorius_overheat_status_tick")
        if self.temperature >= self.OVERHEAT_TEMPERATURE:
            self.machine.events.post("professor_pretorius_overheated")
            self._show_message("REACTOR OVERHEATED", "PROFESSOR PRETORIUS ESCAPED")
            self._fail_mode()

    def _qualify_super(self):
        if self.mode_done or self.phase != "reactor":
            return
        self.phase = "super"
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("professor_pretorius_super_ready")
        self.machine.events.post("final_vuk_chase_start")
        self.super_seconds_remaining = self.super_time_ms // 1000
        self.delay.reset(
            name="professor_pretorius_super_tick",
            ms=1000,
            callback=self._super_tick,
        )
        self._update_spinner_insert()
        self._show_message(
            "REACTOR SUPER READY",
            f"SHOOT THE VUK - {self.super_seconds_remaining} SECONDS",
            value=self.SUPER_VALUE,
            reminder=True,
        )
        self._update_status()
        self._sync_vars()

    def _super_tick(self):
        if self.mode_done or self.phase != "super":
            return
        self.super_seconds_remaining = max(0, self.super_seconds_remaining - 1)
        if self.super_seconds_remaining <= 0:
            self.machine.events.post("professor_pretorius_super_expired")
            self._show_message("REACTOR SUPER EXPIRED", "PROFESSOR PRETORIUS ESCAPED")
            self._fail_mode()
            return
        self._update_status()
        self.delay.reset(
            name="professor_pretorius_super_tick",
            ms=1000,
            callback=self._super_tick,
        )

    def _vuk_hit(self, **kwargs):
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        if self.mode_done:
            return
        if self.phase != "super":
            self.machine.events.post("request_vuk_eject")
            return

        self.super_jackpots = 1
        self.machine.events.post("final_vuk_chase_stop")
        self._score(self.SUPER_VALUE)
        self.machine.events.post("professor_pretorius_super_collected", value=self.SUPER_VALUE)
        self._show_jackpot("REACTOR SUPER", self.SUPER_VALUE)
        self.machine.events.post("play_mode_super_jackpot")
        self.machine.events.post("villain_summary_hold_vuk_until_done")
        self._complete_mode()

    def _update_temperature_lights(self):
        level = min(self.temperature, self.OVERHEAT_TEMPERATURE)
        self.machine.events.post("professor_pretorius_stop_temperature_gi")
        self.machine.events.post(f"professor_pretorius_temperature_{level}")
        self._update_spinner_insert()

    def _update_spinner_insert(self):
        self.machine.events.post("professor_pretorius_spinner_off")
        if self.temperature > 0 or self.phase == "super":
            self.machine.events.post("professor_pretorius_spinner_flashing")

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.machine.events.post("final_vuk_chase_stop")
        self.mode_done = True
        self._clear_delays()
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("professor_pretorius_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.machine.events.post("final_vuk_chase_stop")
        self.mode_done = True
        self._clear_delays()
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("professor_pretorius_mode_complete")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.reactor_hits
        player["active_mode_stat_2"] = self.super_jackpots

    def _update_status(self):
        if self.mode_done:
            return
        if self.phase == "super":
            value = f"VUK {self.super_seconds_remaining}s / TEMP {self.temperature}"
            if self.grace_active and self.overheat_seconds_remaining > 0:
                value += f" / OVERHEAT {self.overheat_seconds_remaining}s"
            self.machine.events.post(
                "show_mode_status",
                mode_status_title="REACTOR SUPER READY",
                mode_status_value=value,
            )
            return
        value = (
            f"{min(self.reactor_hits, self.TOTAL_REACTOR_HITS)} / "
            f"{self.TOTAL_REACTOR_HITS} - TEMP {self.temperature}"
        )
        title = "PRETORIUS REACTOR"
        if self.grace_active and self.overheat_seconds_remaining > 0:
            title = "COOL REACTOR"
            value += f" - {self.overheat_seconds_remaining}s"
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _show_message(self, title, subtitle="", value="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
            reminder=reminder,
        )

    def _show_jackpot(self, title, value):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle="PROFESSOR PRETORIUS DEFEATED",
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _clear_delays(self):
        self.delay.remove("professor_pretorius_overheat_grace")
        self.delay.remove("professor_pretorius_overheat_status_tick")
        self.delay.remove("professor_pretorius_super_tick")
        self.delay.remove("professor_pretorius_shot_assist")
