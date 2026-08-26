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
    "stat_1_var": "active_mode_stat_1",
    "stat_2_label": "SUPER JACKPOT",
    "stat_2_var": "active_mode_stat_2",
    "points_var": "active_mode_points",
    "state_var": "electro_state",
"""


class Electro(CaseFileMixin, Mode):

    BASE_NORMAL_JACKPOT_VALUE = 250000
    BASE_SUPER_JACKPOT_VALUE = 1000000
    MIN_NORMAL_JACKPOT_VALUE = 50000
    NORMAL_VALUE_DECAY = 10000
    NORMAL_SHOT_SECONDS = 5
    SHOT_ASSIST_SECONDS = 8
    UPPER_NORMAL_SHOT_SECONDS = 10
    UPPER_SHOT_ASSIST_SECONDS = 13
    LOWER_SUPER_SECONDS = 10
    UPPER_SUPER_SECONDS = 15

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        # Instance values prevent Case File bonuses from leaking across starts.
        self.normal_jackpot_value = self.BASE_NORMAL_JACKPOT_VALUE
        self.super_jackpot_value = self.BASE_SUPER_JACKPOT_VALUE

        self.case_file_extra_spark_available = False
        self.case_file_slow_value_drain = False
        self.case_file_shot_assist_available = False
        self._apply_case_file_bonuses()

        self.publish_case_file_bonus_events("electro")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA SPARK JACKPOT AVAILABLE"),
            ("bigger_jackpots", "SPARK JACKPOTS BOOSTED"),
            ("more_time", "SPARK VALUE DRAINS SLOWER"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST SPARK HELD LONGER"),
        ])
        self._show_message("POWER SURGE", "HIT THE LIT SPARK", reminder=True)

        self.value_deduct = 0
        self.value_tick_count = 0
        self.super_active = False
        self.current_shot = None
        self.mode_done = False
        self.awaiting_next_shot = False
        self.collected_jackpot_shots = set()

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
        self.machine.events.post("electro_shot_timer_stop")
        self.machine.events.post("electro_shot_assist_timer_stop")
        self.machine.events.post("electro_upper_shot_timer_stop")
        self.machine.events.post("electro_upper_shot_assist_timer_stop")
        self.machine.events.post("electro_value_timer_stop")
        self.machine.events.post("electro_super_timer_stop")
        self.machine.events.post("electro_upper_super_timer_stop")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        self.machine.events.post("cancel_mode_message_reminder")
        # Catch-all: no delayed villain/wizard callback may survive into bonus.
        self.delay.clear()
        super().mode_stop(**kwargs)

    def _show_message(self, title, subtitle="", value="", seconds="", event="show_mode_message", reminder=False):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )

    def _update_status(self):
        if self.mode_done:
            return
        remaining = len(self.active_shots())
        title = "SUPER SPARK" if self.super_active else "SPARKS LEFT"
        value = self._shot_label(self.current_shot) if self.super_active and self.current_shot else remaining
        self.machine.events.post("show_mode_status", mode_status_title=title, mode_status_value=value)

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
        if self.has_case_file("more_jackpots"):
            self.case_file_extra_spark_available = True

        if self.has_case_file("bigger_jackpots"):
            self.normal_jackpot_value += 50000
            self.super_jackpot_value += 250000

        if self.has_case_file("more_time"):
            self.case_file_slow_value_drain = True

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.case_file_shot_assist_available = True

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
        if self.super_active or not self.current_shot or not self.current_shot.is_lit:
            return

        self.value_tick_count += 1
        decay_interval = 2 if self.current_shot.group == "upper" else 1
        if self.case_file_slow_value_drain:
            decay_interval *= 2

        if self.value_tick_count % decay_interval:
            return

        current_value = self._current_normal_jackpot_value()
        if current_value > self.MIN_NORMAL_JACKPOT_VALUE:
            self.value_deduct += 1

    def _current_normal_jackpot_value(self):
        return max(
            self.MIN_NORMAL_JACKPOT_VALUE,
            self.normal_jackpot_value - self.NORMAL_VALUE_DECAY * self.value_deduct,
        )

    def active_shots(self):
        return [shot for shot in self.shots if not shot.disabled]

    def pick_next_lit_shot(self):
        if self.mode_done:
            return

        self.awaiting_next_shot = False
        previous_location = self.current_shot.group if self.current_shot else "lower"
        self.stop_current_lit_shot()

        active = self.active_shots()

        if not active:
            self._complete_mode()
            return

        if len(active) == 1:
            self.start_super_jackpot(active[0])
            return

        self.current_shot = random.choice(active)
        self.current_shot.is_lit = True

        # Every newly selected or moved spark starts again at maximum value.
        self.value_deduct = 0
        self.value_tick_count = 0

        is_upper_shot = self.current_shot.group == "upper"
        shot_seconds = self.UPPER_NORMAL_SHOT_SECONDS if is_upper_shot else self.NORMAL_SHOT_SECONDS
        if self.case_file_shot_assist_available:
            shot_seconds = self.UPPER_SHOT_ASSIST_SECONDS if is_upper_shot else self.SHOT_ASSIST_SECONDS
            self.case_file_shot_assist_available = False
            self.machine.events.post("electro_case_file_next_spark_held")
            timer_event = (
                "electro_upper_shot_assist_timer_start"
                if is_upper_shot
                else "electro_shot_assist_timer_start"
            )
        else:
            timer_event = "electro_upper_shot_timer_start" if is_upper_shot else "electro_shot_timer_start"

        self.machine.events.post(timer_event)

        self._show_message(
            "HIT THE SPARK",
            self._shot_label(self.current_shot),
            value=self._current_normal_jackpot_value(),
            seconds=shot_seconds,
            event="show_mode_countdown",
        )
        self.machine.events.post("electro_lit_shot_changed")
        self.machine.events.post(f"electro_lite_{self.current_shot.name}")

        if previous_location == "upper" and self.current_shot.group != "upper":
            self.machine.events.post("rooftop_diverter_close")
        if previous_location != "upper" and self.current_shot.group == "upper":
            self.machine.events.post("rooftop_diverter_open")

        self.machine.events.post("electro_value_timer_start")
        self._update_status()

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
        self.machine.events.post("electro_shot_assist_timer_stop")
        self.machine.events.post("electro_upper_shot_timer_stop")
        self.machine.events.post("electro_upper_shot_assist_timer_stop")
        self.machine.events.post("electro_value_timer_stop")

    def lit_shot_timeout(self, **kwargs):
        if self.mode_done or self.super_active:
            return

        if self.awaiting_next_shot or not self.current_shot or not self.current_shot.is_lit:
            return

        # The uncollected shot stays in the pool; the spark moves and resets to max.
        self._show_message("SPARK MOVED", "FIND THE NEW SHOT")
        self.pick_next_lit_shot()

    def shot_hit(self, shot_name=None, **kwargs):
        if self.mode_done:
            return

        if self.machine.game.player["villain_mode_in_summary"] is True:
            return

        if not shot_name:
            return

        shot = self.shots_by_name.get(shot_name)
        if not shot:
            return

        is_saucer_shot = shot.name == "saucers"

        if shot.disabled:
            if is_saucer_shot:
                self._release_saucers()
            return

        if self.super_active:
            if shot == self.current_shot:
                self.machine.events.post("electro_super_timer_stop")
                self.machine.events.post("electro_upper_super_timer_stop")
                self.collect_super()
            elif is_saucer_shot:
                self._release_saucers()
            return

        # Unlit shots do not pause or stop the active spark's value decay.
        if shot != self.current_shot:
            if is_saucer_shot:
                self._release_saucers()
            return

        self.machine.events.post("electro_value_timer_stop")
        self.collect_normal_jackpot(shot)
        if is_saucer_shot:
            self._release_saucers()

    def _release_saucers(self):
        self.machine.events.post("clear_saucers_delayed")

    def collect_normal_jackpot(self, shot):
        if self.mode_done:
            return

        self.machine.events.post("electro_shot_timer_stop")
        self.machine.events.post("electro_shot_assist_timer_stop")
        self.machine.events.post("electro_upper_shot_timer_stop")
        self.machine.events.post("electro_upper_shot_assist_timer_stop")
        self.awaiting_next_shot = True

        jackpot_value = self._current_normal_jackpot_value()
        self.machine.game.player["score"] += jackpot_value
        self.active_mode_points += jackpot_value
        self.machine.game.player["active_mode_points"] = self.active_mode_points

        if jackpot_value > self.electro_best_spark:
            self.electro_best_spark = jackpot_value
        self.machine.game.player["active_mode_stat_1"] = self.electro_best_spark

        self._show_message("ELECTRO JACKPOT", self._shot_label(shot), value=jackpot_value, event="show_mode_jackpot")
        self.machine.events.post("electro_jackpot_collected")

        if self.case_file_extra_spark_available:
            # More Jackpots grants one extra normal collect by returning this shot
            # to the available pool instead of permanently disabling it.
            self.case_file_extra_spark_available = False
            shot.disabled = False
            self.machine.events.post("electro_case_file_extra_spark_used")
        else:
            shot.disabled = True
            self.collected_jackpot_shots.add(shot.name)
            self.machine.events.post(f"electro_deactivate_{shot.name}")

        shot.is_lit = False
        self.machine.events.post(f"electro_stop_{shot.name}")
        self.value_deduct = 0
        self._update_status()

        self.delay.remove("next_shot_delay")
        self.delay.add(name="next_shot_delay", ms=1000, callback=self.delayed_next_shot)

    def delayed_next_shot(self, **kwargs):
        self.awaiting_next_shot = False
        self.pick_next_lit_shot()

    def start_super_jackpot(self, shot):
        self.stop_current_lit_shot()

        self.super_active = True
        self.current_shot = shot
        self.current_shot.is_lit = True
        self.current_shot.is_jackpot = True

        self.machine.game.player["electro_super_jackpot_value"] = self.super_jackpot_value
        self._set_gate_for_shot(shot)

        is_upper_shot = shot.group == "upper"
        super_seconds = self.UPPER_SUPER_SECONDS if is_upper_shot else self.LOWER_SUPER_SECONDS

        self._show_message(
            "SUPER SURGE LIT",
            self._shot_label(shot),
            value=self.super_jackpot_value,
            seconds=super_seconds,
            event="show_mode_countdown",
        )
        self.machine.events.post("electro_super_lit")
        self.machine.events.post(f"electro_super_lite_{shot.name}")
        super_timer_event = "electro_upper_super_timer_start" if is_upper_shot else "electro_super_timer_start"
        self.machine.events.post(super_timer_event)
        self._update_status()

    def collect_super(self):
        if self.mode_done:
            return
        self.mode_done = True

        self.electro_super_jackpot = self.machine.game.player["electro_super_jackpot_value"]
        self.active_mode_points += self.electro_super_jackpot

        self.machine.game.player["active_mode_stat_2"] = self.electro_super_jackpot
        self.machine.game.player["active_mode_points"] = self.active_mode_points
        self.machine.game.player["score"] += self.electro_super_jackpot

        self.current_shot.is_lit = False
        self.current_shot.is_jackpot = False

        if self.current_shot.name == "saucers":
            self.machine.events.post("villain_summary_hold_saucer_until_done")
        self._show_message("ELECTRO SUPER", "SUPER JACKPOT", value=self.electro_super_jackpot, event="show_mode_jackpot")
        self.machine.events.post("electro_super_collected")
        self.machine.events.post("electro_super_timer_stop")
        self.machine.events.post("electro_upper_super_timer_stop")
        self.machine.events.post("electro_mode_almost_complete")

    def super_timeout(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._show_message("SUPER MISSED", "ELECTRO ESCAPES")
        self.machine.events.post("electro_super_missed")
        self.machine.events.post("electro_mode_complete")

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.events.post("electro_mode_complete")
