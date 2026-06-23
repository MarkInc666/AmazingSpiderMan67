from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin
from modes.common.shot_registry import Shot
from mpf.core.delays import DelayManager

import random

"""
    "title": "ELECTRO",
    "intro_1": "Follow the moving spark.",
    "intro_2": "Hit each charged shot before time runs out.",
    "intro_3": "The eighth spark awards Super Jackpot.",
    "summary_title_complete": "ELECTRO DEFEATED",
    "summary_title_failed": "ELECTRO ESCAPED",
    "stat_1_label": "BEST SPARK",
    "stat_1_var": "electro_best_spark",
    "stat_2_label": "SUPER JACKPOT",
    "stat_2_var": "electro_super_jackpot",
    "points_var": "active_mode_points",
    "state_var": "electro_state",
"""

class Electro(CaseFileMixin, Mode):

    NORMAL_JACKPOT_VALUE = 250000
    SUPER_JACKPOT_VALUE = 1000000    

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("electro")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA SPARK JACKPOT AVAILABLE"),
            ("bigger_jackpots", "SPARK JACKPOTS BOOSTED"),
            ("more_time", "SPARK VALUE DRAINS SLOWER"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "NEXT SPARK HELD LONGER"),
        ])
        self._show_message("POWER SURGE", "HIT THE LIT SPARK")


        self.value_deduct = 0

        self.super_active = False
        self.current_shot = None

        self.electro_super_jackpot = 0
        self.electro_best_spark = 0
        self.active_mode_points = 0

        self.shots = [
            Shot("left_web", 10, 70, "electro_left_web_hit", group="left"),
            Shot("spinner", 20, 50, "electro_spinner_hit", group="center"),
            Shot("left_drops", 40, 60, "electro_left_drops_hit", group="left"),
            Shot("saucers", 50, 30, "electro_saucers_hit", group="left"),
            Shot("right_web", 80, 30, "electro_right_web_hit", group="right"),
            Shot("upper_spinner", 90, 30, "electro_upper_spinner_hit", group="upper"),
            Shot("upper_targets", 95, 20, "electro_upper_target_hit", group="upper"),
            Shot("right_drops", 100, 80, "electro_right_drops_hit", group="right"),
        ]

        self.shots_by_name = {shot.name: shot for shot in self.shots}

        for shot in self.shots:
            self.add_mode_event_handler(shot.event, self.shot_hit, shot_name=shot.name)

        self.add_mode_event_handler("electro_lit_shot_timeout", self.lit_shot_timeout)
        self.add_mode_event_handler("electro_super_timeout", self.super_timeout)
        self.add_mode_event_handler("timer_electro_value_timer_tick", self.value_tick)

        self.begin_power_surge()


    def mode_stop(self, **kwargs):
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _show_message(self, title, subtitle="", value="", seconds="", event="show_mode_message"):
        self.machine.events.post(
            event,
            title=title,
            subtitle=subtitle,
            value=value,
            seconds=seconds,
        )

    def _shot_label(self, shot):
        labels = {
            "left_web": "LEFT WEB",
            "spinner": "SPINNER",
            "left_drops": "LEFT DROPS",
            "saucers": "SAUCERS",
            "right_web": "CENTER WEB",
            "upper_spinner": "UPPER SPINNER",
            "upper_targets": "UPPER TARGETS",
            "right_drops": "RIGHT DROPS",
        }
        return labels.get(shot.name, shot.name.upper())

    def _apply_case_file_bonuses(self):
        self.case_file_extra_spark_available = False
        self.case_file_slow_value_drain = False
        self.case_file_value_tick_toggle = False

        if self.has_case_file("more_jackpots"):
            self.case_file_extra_spark_available = True

        if self.has_case_file("bigger_jackpots"):
            self.NORMAL_JACKPOT_VALUE += 50000
            self.SUPER_JACKPOT_VALUE += 250000

        if self.has_case_file("more_time"):
            self.case_file_slow_value_drain = True

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.machine.events.post("electro_case_file_next_spark_held")

    def begin_power_surge(self):
        self.super_active = False
        self.current_shot = None

        for shot in self.shots:
            shot.is_lit = False
            shot.disabled = False
            shot.is_jackpot = False

        self.machine.events.post("electro_startup_complete")
        self.pick_next_lit_shot()

    def value_tick(self, **kwargs):
        #250,000 - 20 X 10,000 = 50,000 base
        if getattr(self, "case_file_slow_value_drain", False):
            self.case_file_value_tick_toggle = not self.case_file_value_tick_toggle
            if self.case_file_value_tick_toggle:
                return

        if self.value_deduct < 20:
            self.value_deduct += 1 

    def active_shots(self):
        return [shot for shot in self.shots if not shot.disabled]

    def pick_next_lit_shot(self):
        self.stop_current_lit_shot()

        active = self.active_shots()

        if len(active) <= 0:
            self.machine.events.post("electro_mode_complete")
            return

        if len(active) == 1:
            self.start_super_jackpot(active[0])
            return
        if self.current_shot:
            previous_location = self.current_shot.group
        else:
            previous_location = "lower"
        
        self.current_shot = random.choice(active)
        self.current_shot.is_lit = True

        self._show_message("HIT THE SPARK", self._shot_label(self.current_shot), seconds=5, event="show_mode_countdown")
        self.machine.events.post("electro_lit_shot_changed")
        self.machine.events.post(f"electro_lite_{self.current_shot.name}")
        self.machine.events.post("electro_shot_timer_start")
        
        if previous_location == "upper" and self.current_shot.group != "upper":
            self.machine.events.post("rooftop_diverter_close")
        if previous_location != "upper" and self.current_shot.group == "upper":
            self.machine.events.post("rooftop_diverter_open")

        self.machine.events.post("electro_value_timer_start")

    def _set_gate_for_shot(self, shot):
        if shot and shot.group == "upper":
            self.machine.events.post("rooftop_diverter_open")
        else:
            self.machine.events.post("rooftop_diverter_close")

    def stop_current_lit_shot(self):
        if self.current_shot:
            self.current_shot.is_lit = False
            self.machine.events.post(f"electro_stop_{self.current_shot.name}")

        self.machine.events.post("electro_shot_timer_stop")

    def lit_shot_timeout(self, **kwargs):
        if self.super_active:
            return

        # Timeout means the shot remains active, but the spark moves elsewhere.
        self._show_message("SPARK MOVED", "FIND THE NEW SHOT")
        self.pick_next_lit_shot()

    def shot_hit(self, shot_name=None, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return
       
        if not shot_name:
            return
        
        shot = self.shots_by_name.get(shot_name)

        if not shot or shot.disabled:
            return

        self.machine.events.post("electro_value_timer_stop")

        if self.super_active:
            if shot == self.current_shot:
                self.collect_super()
            return

        if shot != self.current_shot:
            return

        self.collect_normal_jackpot(shot)

    def collect_normal_jackpot(self, shot):
        jackpot_value = self.NORMAL_JACKPOT_VALUE - 10000 * self.value_deduct
        self.machine.game.player["score"] += jackpot_value
        self.active_mode_points += jackpot_value
        self.machine.game.player["active_mode_points"] = self.active_mode_points

        if jackpot_value > self.electro_best_spark:
            self.electro_best_spark = jackpot_value
        self.machine.game.player["electro_best_spark"] = self.electro_best_spark

        self._show_message("ELECTRO JACKPOT", self._shot_label(shot), value=jackpot_value, event="show_mode_jackpot")
        self.machine.events.post("electro_jackpot_collected")
        self.value_deduct = 0

        if getattr(self, "case_file_extra_spark_available", False):
            self.case_file_extra_spark_available = False
            self.machine.events.post("electro_case_file_extra_spark_used")
        else:
            shot.disabled = True
        shot.is_lit = False

        self.machine.events.post(f"electro_stop_{shot.name}")
        self.machine.events.post(f"electro_deactivate_{shot.name}")

        self.delay.remove("next_shot_delay")
        self.delay.add(
            name="next_shot_delay",
            ms=1000,
            callback=self.delayed_next_shot
        )

    def delayed_next_shot(self, **kwargs):
        self.machine.events.post("electro_shot_timer_stop")
        self.pick_next_lit_shot()

    def start_super_jackpot(self, shot):
        self.stop_current_lit_shot()

        self.super_active = True
        self.current_shot = shot
        self.current_shot.is_lit = True
        self.current_shot.is_jackpot = True

        #for the "GET THE SUPER JACKPOT FOR XXXX" widget
        self.machine.game.player["electro_super_jackpot_value"] = self.SUPER_JACKPOT_VALUE

        self._set_gate_for_shot(shot)

        self._show_message("SUPER SURGE LIT", self._shot_label(shot), value=self.SUPER_JACKPOT_VALUE, seconds=10, event="show_mode_countdown")
        self.machine.events.post("electro_super_lit")
        self.machine.events.post(f"electro_super_lite_{shot.name}")
        self.machine.events.post("electro_super_timer_start")

    def collect_super(self):
        self.electro_super_jackpot = self.machine.game.player["electro_super_jackpot_value"]
        self.active_mode_points += self.electro_super_jackpot

        self.machine.game.player["electro_super_jackpot"] = self.electro_super_jackpot
        self.machine.game.player["active_mode_points"] = self.active_mode_points

        self.machine.game.player["score"] += self.electro_super_jackpot

        self.current_shot.is_lit = False
        self.current_shot.is_jackpot = False

        self._show_message("ELECTRO SUPER", "SUPER JACKPOT", value=self.electro_super_jackpot, event="show_mode_jackpot")
        self.machine.events.post("electro_super_collected")
        self.machine.events.post("electro_super_timer_stop")
        self.machine.events.post("electro_mode_almost_complete")

    def super_timeout(self, **kwargs):
        self._show_message("SUPER MISSED", "ELECTRO ESCAPES")
        self.machine.events.post("electro_super_missed")
        self.machine.events.post("electro_mode_complete")        
