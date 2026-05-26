from mpf.core.mode import Mode

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
    "points_var": "vulture_mode_points",
    "completed_var": "vulture_completed",

"""
class Vulture(Mode):

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
        self.vulture_mode_points = 0

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

        self.update_player_vars()
        self.show_targets()

    def upper_entered(self, **kwargs):
        self.upper_balls += 1

        if not self.started:
            self.started = True
            self.machine.events.post("vulture_timer_start")

        self.update_upper_multiplier()
        self.update_player_vars()

    def upper_exited(self, **kwargs):
        if self.upper_balls > 0:
            self.upper_balls -= 1

        self.update_upper_multiplier()
        self.update_player_vars()

    def update_upper_multiplier(self):
        if self.upper_balls >= 2:
            self.machine.events.post("vulture_two_balls_upper")

    def target_hit(self, target, **kwargs):
        if self.stages[target] < 3:
            self.stages[target] += 1

        self.award_score(20000)
        self.show_targets()
        self.check_add_a_ball()
        self.update_player_vars()

    def check_add_a_ball(self):
        if self.add_a_ball_awarded:
            return

        if self.stages["left"] == 3 and self.stages["center"] == 3 and self.stages["right"] == 3:
            self.machine.events.post("start_vulture_add_a_ball")
            self.add_a_ball_awarded = True

    def spinner_hit(self, **kwargs):
        total = 0

        for stage in self.stages.values():
            total += self.STAGE_VALUES[stage]

        if self.upper_balls >= 2:
            total *= 2

        self.award_score(total)
        self.bank_bonus(total)
        
        self.vulture_spins += 1 
        self.vulture_banked_bonus += total

        self.machine.game.player["vulture_spins"] = self.vulture_spins        
        self.machine.game.player["vulture_banked_bonus"] = self.vulture_banked_bonus  

        self.machine.game.player["vulture_last_spinner_score"] = total        

    def bank_bonus(self, value):
        player = self.machine.game.player
        player["vulture_bonus"] = player["vulture_bonus"] + value                


    def idle_decay(self, **kwargs):
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
        self.vulture_mode_points += value
        self.machine.game.player["vulture_mode_points"] = self.vulture_mode_points 