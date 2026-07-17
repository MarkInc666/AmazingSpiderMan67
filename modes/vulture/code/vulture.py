from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
    "title": "VULTURE",
    "intro_1": "Get to the rooftop.",
    "intro_2": "Hit targets to raise spinner value.",
    "intro_3": "Spin fast before the targets decay.",
    "summary_title_complete": "VULTURE DEFEATED",
    "summary_title_failed": "VULTURE ESCAPED",
    "stat_1_label": "SPINS",
    "stat_1_var": "vulture_spins",
    "stat_2_label": "BONUS BANKED",
    "stat_2_var": "vulture_banked_bonus",
    "points_var": "active_mode_points",
    "state_var": "vulture_state",

"""
class Vulture(CaseFileMixin, Mode):

    STAGE_VALUES = {
        1: 5000,    # yellow
        2: 10000,   # orange
        3: 25000,   # red
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.started = False
        self.upper_balls = 0
        self.add_a_ball_awarded = False

        self.vulture_spins = 0 
        self.vulture_banked_bonus = 0
        self.active_mode_points = 0

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("vulture")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA AERIAL BONUS AVAILABLE"),
            ("bigger_jackpots", "SPINNER VALUE BOOSTED"),
            ("more_time", "TARGET DECAY SLOWED"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "TARGET COLOR SPOTTED"),
        ])

        self.stages = {
            "left": 1,
            "center": 1,
            "right": 1,
        }

        self.add_mode_event_handler("vulture_upper_entered", self.upper_entered)
        self.add_mode_event_handler("vulture_upper_exited", self.upper_exited)

        self.add_mode_event_handler("vulture_left_target_hit", self.target_hit, target="left")
        self.add_mode_event_handler("vulture_center_target_hit", self.target_hit, target="center")
        self.add_mode_event_handler("vulture_right_target_hit", self.target_hit, target="right")

        self.add_mode_event_handler("vulture_spinner_hit", self.spinner_hit)
        self.add_mode_event_handler("vulture_idle_decay", self.idle_decay)
        self.add_mode_event_handler("vulture_show_targets", self.show_targets)
        self.add_mode_event_handler("timer_vulture_mode_timer_tick", self.timer_tick)

        self.update_player_vars()
        self.show_targets()
        self._show_message("VULTURE", "GET TO THE ROOFTOP")
        self.machine.events.post("show_mode_status", mode_status_title="ROOF ACCESS", mode_status_value="GET TO ROOFTOP")

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _show_message(self, title, subtitle="", value="", seconds="", event="show_mode_message"):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
        )

    def _apply_case_file_bonuses(self):
        self.stage_values = dict(self.STAGE_VALUES)
        self.case_file_extra_aerial_bonus = False
        self.case_file_decay_skip_available = False

        if self.has_case_file("more_jackpots"):
            self.case_file_extra_aerial_bonus = True

        if self.has_case_file("bigger_jackpots"):
            self.stage_values = {stage: value + 5000 for stage, value in self.stage_values.items()}

        if self.has_case_file("more_time"):
            self.case_file_decay_skip_available = True

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.machine.events.post("vulture_case_file_target_color_spotted")

    def upper_entered(self, **kwargs):
        self.upper_balls += 1

        if not self.started:
            self.started = True
            self._show_message("SKY ATTACK", "HIT UPPER TARGETS")
            self.machine.events.post("show_mode_status", mode_status_title="SECONDS LEFT", mode_status_value=40)
            self.machine.events.post("vulture_timer_start")

        self.update_upper_multiplier()
        self.update_player_vars()

    def upper_exited(self, **kwargs):
        if self.upper_balls > 0:
            self.upper_balls -= 1

        self.update_upper_multiplier()
        self.update_player_vars()

    def timer_tick(self, ticks=None, **kwargs):
        if not self.started:
            return
        remaining = ticks
        if remaining is None:
            try:
                remaining = self.machine.timers["vulture_mode_timer"].ticks
            except Exception:
                remaining = ""
        self.machine.events.post("update_mode_status", mode_status_title="SECONDS LEFT", mode_status_value=remaining)

    def update_upper_multiplier(self):
        if self.upper_balls >= 2:
            self.machine.events.post("vulture_two_balls_upper")

    def target_hit(self, target, **kwargs):
        if self.stages[target] < 3:
            self.stages[target] += 1

        self.award_score(20000)
        self._show_message("TARGET VALUE UP", f"{target.upper()} TARGET STAGE {self.stages[target]}")
        self.show_targets()
        self.check_add_a_ball()
        self.update_player_vars()

    def check_add_a_ball(self):
        if self.add_a_ball_awarded:
            return

        if self.stages["left"] == 3 and self.stages["center"] == 3 and self.stages["right"] == 3:
            self._show_message("ADD-A-BALL!", "ALL TARGETS AT RED", event="show_mode_jackpot")
            self.machine.events.post("start_vulture_add_a_ball")
            self.add_a_ball_awarded = True

    def spinner_hit(self, **kwargs):
        total = 0

        for stage in self.stages.values():
            total += self.stage_values[stage]

        if self.upper_balls >= 2:
            total *= 2

        if getattr(self, "case_file_extra_aerial_bonus", False) and all(stage == 3 for stage in self.stages.values()):
            total += 100000
            self.machine.events.post("vulture_case_file_extra_aerial_bonus_awarded")

        self.award_score(total)
        self.bank_bonus(total)
        
        self.vulture_spins += 1 
        self.vulture_banked_bonus += total

        self.machine.game.player["vulture_spins"] = self.vulture_spins        
        self.machine.game.player["vulture_banked_bonus"] = self.vulture_banked_bonus  

        self.machine.game.player["vulture_last_spinner_score"] = total
        self._show_message("VULTURE SPINNER", "AERIAL BONUS", value=total, event="show_mode_jackpot")

    def bank_bonus(self, value):
        player = self.machine.game.player
        player["vulture_bonus"] = player["vulture_bonus"] + value                


    def idle_decay(self, **kwargs):
        if getattr(self, "case_file_decay_skip_available", False):
            self.case_file_decay_skip_available = False
            self._show_message("TARGETS HELD", "CASE FILE SAVED THE VALUE")
            self.machine.events.post("vulture_case_file_decay_skipped")
            self.machine.events.post("vulture_restart_idle_timer")
            return

        for target in self.stages:
            if self.stages[target] > 1:
                self.stages[target] -= 1

        self.show_targets()
        self.update_player_vars()
        self.machine.events.post("vulture_restart_idle_timer")

    def show_targets(self, **kwargs):
        for target, stage in self.stages.items():
            color = self.stage_name(stage)
            self.machine.events.post(f"vulture_show_{target}_{color}")

    def stage_name(self, stage):
        if stage == 1:
            return "yellow"
        if stage == 2:
            return "orange"
        return "red"

    def update_player_vars(self):
        player = self.machine.game.player

        player["vulture_started"] = int(self.started)
        player["vulture_left_stage"] = self.stages["left"]
        player["vulture_center_stage"] = self.stages["center"]
        player["vulture_right_stage"] = self.stages["right"]
        player["vulture_balls_on_upper"] = self.upper_balls
        player["vulture_add_a_ball_awarded"] = int(self.add_a_ball_awarded)

    def award_score(self, value):
        self.machine.game.player["score"] += value
        self.active_mode_points += value
        self.machine.game.player["active_mode_points"] = self.active_mode_points 