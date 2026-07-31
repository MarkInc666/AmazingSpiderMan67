import random
from functools import partial

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class MetalEatingRobot(CaseFileMixin, Mode):
    """Metal-Eating Monster: rescue zones before the monster destroys the city."""

    MODE_KEY = "metal_eating_robot"
    DISPLAY_NAME = "METAL MONSTER"
    ATTACK_INTERVAL_MS = 5_000
    RETALIATION_INTERVAL_MS = 2_000
    BASE_ZONE_TIMER_MS = 12_000
    MORE_TIME_ZONE_TIMER_MS = 16_000
    SHOT_ASSIST_REMAINING_MS = 2_000
    SAVES_TO_WIN = 4
    DESTROYED_TO_LOSE = 3
    BASE_SAVE_VALUE = 250_000
    BIGGER_SAVE_VALUE = 400_000

    ZONES = (
        "left_sling",
        "right_sling",
        "left_web",
        "upper_right",
        "left_bank",
        "right_bank",
        "center",
        "saucers",
    )

    ZONE_LABELS = {
        "left_sling": "LEFT SLING",
        "right_sling": "RIGHT SLING",
        "left_web": "LEFT WEB",
        "upper_right": "UPPER RIGHT",
        "left_bank": "LEFT BANK",
        "right_bank": "RIGHT BANK",
        "center": "CENTER",
        "saucers": "SAUCERS",
    }

    SAUCER_EJECT_EVENTS = {
        1: "delayed_kickout_saucer_1",
        2: "delayed_kickout_saucer_2",
        3: "delayed_kickout_saucer_3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.mode_points = 0
        self.saved_zones = set()
        self.destroyed_zones = set()
        self.attacked_zones = set()
        self.repeat_available = set()
        self.repeat_collected = set()
        self.shot_assist_used = False
        self.zone_timer_ms = (
            self.MORE_TIME_ZONE_TIMER_MS
            if self.has_case_file("more_time")
            else self.BASE_ZONE_TIMER_MS
        )
        self.save_value = (
            self.BIGGER_SAVE_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.BASE_SAVE_VALUE
        )
        self.repeat_value = self.save_value // 2

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", f"SAVED ZONES RELIGHT FOR {self.repeat_value:,}"),
            ("bigger_jackpots", f"ZONE SAVES SCORE {self.save_value:,}"),
            ("more_time", f"ZONE TIMERS LAST {self.zone_timer_ms // 1000} SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "HELP ARRIVES AT 2 SECONDS"),
        ])

        for zone in self.ZONES:
            self.add_mode_event_handler(
                f"metal_zone_{zone}", partial(self._zone_hit, zone=zone)
            )
        for saucer in self.SAUCER_EJECT_EVENTS:
            self.add_mode_event_handler(
                f"metal_saucer_{saucer}_eject",
                partial(self._eject_saucer, saucer=saucer),
            )

        player = self.machine.game.player
        player["metal_eating_robot_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player["metal_zones_saved"] = 0
        player["metal_zones_destroyed"] = 0
        player["metal_zones_under_attack"] = 0
        player["metal_repeat_jackpots"] = 0
        player["metal_zone_timer_seconds"] = self.zone_timer_ms // 1000

        self.machine.events.post("reset_drops")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("rooftop_diverter_close")
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.machine.events.post("metal_all_zones_safe")
        self._show_message("ZONES UNDER ATTACK", "SAVE 4 - LOSE 3")
        self._schedule_next_attack(self.ATTACK_INTERVAL_MS)
        self._sync_vars()

    def mode_stop(self, **kwargs):
        self._clear_delays()
        self.clear_active_case_file_helpers()
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("metal_mode_ended")
        self.machine.events.post("clear_saucers_delayed")
        super().mode_stop(**kwargs)

    def _schedule_next_attack(self, delay_ms):
        self.delay.remove("metal_next_attack")
        if self.mode_done or len(self.saved_zones) >= self.SAVES_TO_WIN:
            return
        if not self._available_zones():
            self._check_end_conditions()
            return
        self.delay.add(name="metal_next_attack", ms=delay_ms, callback=self._start_attack)

    def _start_attack(self):
        if self.mode_done or len(self.saved_zones) >= self.SAVES_TO_WIN:
            self._check_end_conditions()
            return

        choices = self._available_zones()
        if not choices:
            self._check_end_conditions()
            return

        zone = random.choice(choices)
        self.attacked_zones.add(zone)
        self.machine.events.post(f"metal_zone_{zone}_attacked")
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title="ZONE UNDER ATTACK",
            message_mode_subtitle=self.ZONE_LABELS[zone],
            message_mode_value="",
            message_mode_seconds=self.zone_timer_ms // 1000,
            reminder=True,
        )

        urgent_ms = max(1, self.zone_timer_ms - self.SHOT_ASSIST_REMAINING_MS)
        self.delay.add(
            name=self._urgent_delay_name(zone),
            ms=urgent_ms,
            callback=partial(self._zone_urgent, zone=zone),
        )
        self.delay.add(
            name=self._expiry_delay_name(zone),
            ms=self.zone_timer_ms,
            callback=partial(self._destroy_zone, zone=zone),
        )
        self._schedule_next_attack(self.ATTACK_INTERVAL_MS)
        self._sync_vars()

    def _zone_hit(self, zone=None, **kwargs):
        if self.mode_done or zone not in self.ZONES:
            return

        if zone in self.attacked_zones:
            self._save_zone(zone, assisted=False)
            return

        if zone in self.repeat_available:
            self.repeat_available.remove(zone)
            self.repeat_collected.add(zone)
            self._score(self.repeat_value)
            self.machine.events.post(f"metal_zone_{zone}_repeat_collected")
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="SAVED ZONE JACKPOT",
                message_mode_subtitle=self.ZONE_LABELS[zone],
                message_mode_value=self.repeat_value,
            )
            self._sync_vars()

    def _save_zone(self, zone, assisted=False):
        if self.mode_done or zone not in self.attacked_zones:
            return

        self._cancel_zone_delays(zone)
        self.attacked_zones.remove(zone)
        self.saved_zones.add(zone)
        self._score(self.save_value)

        self.machine.events.post(f"metal_zone_{zone}_saved")
        if self.has_case_file("more_jackpots"):
            self.repeat_available.add(zone)
            self.machine.events.post(f"metal_zone_{zone}_repeat_available")

        title = "SPIDER-MAN SAVES THE ZONE!" if assisted else "ZONE SAVED"
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=self.ZONE_LABELS[zone],
            message_mode_value=self.save_value,
        )

        if len(self.saved_zones) >= self.SAVES_TO_WIN:
            self.delay.remove("metal_next_attack")
        else:
            self._schedule_next_attack(self.RETALIATION_INTERVAL_MS)

        self._sync_vars()
        self._check_end_conditions()

    def _zone_urgent(self, zone=None):
        if self.mode_done or zone not in self.attacked_zones:
            return
        self.machine.events.post(f"metal_zone_{zone}_urgent")
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            self._save_zone(zone, assisted=True)

    def _destroy_zone(self, zone=None):
        if self.mode_done or zone not in self.attacked_zones:
            return

        self._cancel_zone_delays(zone)
        self.attacked_zones.remove(zone)
        self.destroyed_zones.add(zone)
        self.machine.events.post(f"metal_zone_{zone}_destroyed")
        self._show_message("ZONE DESTROYED", self.ZONE_LABELS[zone])
        self._sync_vars()
        self._check_end_conditions()

    def _check_end_conditions(self):
        if self.mode_done:
            return
        if len(self.destroyed_zones) >= self.DESTROYED_TO_LOSE:
            self._finish_mode(won=False)
            return
        if len(self.saved_zones) >= self.SAVES_TO_WIN and not self.attacked_zones:
            self._finish_mode(won=True)
            return
        if not self._available_zones() and not self.attacked_zones:
            self._finish_mode(won=len(self.saved_zones) >= self.SAVES_TO_WIN)

    def _finish_mode(self, won):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        player = self.machine.game.player
        player["metal_eating_robot_state"] = 2
        self._sync_vars()

        if won:
            self._show_message("CITY SAVED", f"{len(self.saved_zones)} ZONES SAVED", jackpot=True)
        else:
            self._show_message("CITY DESTROYED", "THREE ZONES LOST")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("metal_eating_robot_mode_complete")

    def _available_zones(self):
        unavailable = self.saved_zones | self.destroyed_zones | self.attacked_zones
        return [zone for zone in self.ZONES if zone not in unavailable]

    def _cancel_zone_delays(self, zone):
        self.delay.remove(self._urgent_delay_name(zone))
        self.delay.remove(self._expiry_delay_name(zone))

    def _clear_delays(self):
        self.delay.remove("metal_next_attack")
        for zone in self.ZONES:
            self._cancel_zone_delays(zone)

    @staticmethod
    def _urgent_delay_name(zone):
        return f"metal_{zone}_urgent"

    @staticmethod
    def _expiry_delay_name(zone):
        return f"metal_{zone}_expire"

    def _eject_saucer(self, saucer=None, **kwargs):
        event = self.SAUCER_EJECT_EVENTS.get(saucer)
        if event:
            self.machine.events.post(event)

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += int(points)
        self.mode_points += int(points)
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = len(self.saved_zones)
        player["active_mode_major_hits"] = len(self.destroyed_zones)
        player["metal_zones_saved"] = len(self.saved_zones)
        player["metal_zones_destroyed"] = len(self.destroyed_zones)
        player["metal_zones_under_attack"] = len(self.attacked_zones)
        player["metal_repeat_jackpots"] = len(self.repeat_collected)

    def _show_message(self, title, subtitle="", jackpot=False):
        self.machine.events.post(
            "show_mode_jackpot" if jackpot else "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=self.mode_points if jackpot else "",
            message_mode_seconds="",
        )
