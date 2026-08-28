from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Vulture(CaseFileMixin, Mode):

    STAGE_VALUES = {
        1: 20000,   # yellow / starting
        2: 50000,   # red / lit
    }
    TARGET_TIMER_SECONDS = 8
    MORE_TIME_TARGET_TIMER_SECONDS = 12

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.machine.game.player["active_mode_stat_2"] = self.machine.game.player["vulture_bonus"]

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
            ("more_jackpots", "ALL-RED SPINNER +100K"),
            ("bigger_jackpots", "SPINNER VALUES DOUBLED"),
            ("more_time", "TARGET LIGHTS EXTENDED TO 12s"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST TARGET LIGHTS ALL"),
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
        self.add_mode_event_handler("vulture_show_targets", self.show_targets)
        self.add_mode_event_handler("timer_vulture_mode_timer_tick", self.timer_tick)

        self.update_player_vars()
        self.show_targets()
        self.machine.events.post("vulture_gi_lower")
        self._show_message("VULTURE", "GET TO THE ROOFTOP", reminder=True)
        self.machine.events.post("show_mode_status", mode_status_title="ROOF ACCESS", mode_status_value="GET TO ROOFTOP")

    def mode_stop(self, **kwargs):
        for target in self.stages:
            self.delay.remove(f"vulture_target_timer_{target}")
        self.machine.events.post("vulture_gi_stop")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        self.machine.events.post("cancel_mode_message_reminder")
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

    def _apply_case_file_bonuses(self):
        self.stage_values = dict(self.STAGE_VALUES)
        self.case_file_extra_aerial_bonus = self.has_case_file("more_jackpots")
        self.target_timer_seconds = (
            self.MORE_TIME_TARGET_TIMER_SECONDS
            if self.has_case_file("more_time")
            else self.TARGET_TIMER_SECONDS
        )
        self.shot_assist_available = self.has_case_file("shot_assist")

        if self.has_case_file("bigger_jackpots"):
            self.stage_values = {stage: value * 2 for stage, value in self.stage_values.items()}

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

    def upper_entered(self, **kwargs):
        self.upper_balls += 1
        self.machine.events.post("vulture_gi_upper")

        if not self.started:
            self.started = True
            self._show_message("SKY ATTACK", "HIT UPPER TARGETS", reminder=True)
            self.machine.events.post("show_mode_status", mode_status_title="SECONDS LEFT", mode_status_value=40)
            self.machine.events.post("vulture_timer_start")

        self.update_upper_multiplier()
        self.update_player_vars()

    def upper_exited(self, **kwargs):
        if self.upper_balls > 0:
            self.upper_balls -= 1

        self.machine.events.post("vulture_gi_lower")
        self.update_upper_multiplier()
        self.update_player_vars()

    def _restart_target_timer(self, target):
        self.delay.reset(
            name=f"vulture_target_timer_{target}",
            ms=self.target_timer_seconds * 1000,
            callback=self.target_timer_expired,
            target=target,
        )

    def timer_tick(self, ticks=None, **kwargs):
        if not self.started:
            return
        remaining = ticks
        if remaining is None:
            try:
                remaining = self.machine.timers["vulture_mode_timer"].ticks
            except Exception:
                remaining = ""
        if int(self.machine.game.player["multiball_autoplunge_active"] or 0) == 1:
            self.machine.events.post(
                "update_mode_status",
                mode_status_title="MB FREE TIME",
                mode_status_value="",
            )
        else:
            self.machine.events.post(
                "update_mode_status",
                mode_status_title="SECONDS LEFT",
                mode_status_value=remaining,
            )

    def update_upper_multiplier(self):
        if self.upper_balls >= 2:
            self.machine.events.post("vulture_two_balls_upper")

    def target_hit(self, target, **kwargs):
        all_red_before_hit = all(stage == 2 for stage in self.stages.values())

        if self.shot_assist_available:
            for name in self.stages:
                self.stages[name] = 2
                self._restart_target_timer(name)
            self.shot_assist_available = False
            self.machine.events.post("vulture_case_file_shot_assist_used")
            self._show_message("SHOT ASSIST", "ALL TARGETS LIT")
        else:
            self.stages[target] = 2
            self._restart_target_timer(target)
            self._show_message("TARGET LIT", f"{target.upper()} TARGET  50K")

        self.award_score(50000)
        self.show_targets()
        if all_red_before_hit:
            self.award_add_a_ball()
        elif all(stage == 2 for stage in self.stages.values()):
            self._show_message("ADD-A-BALL READY", "HIT ANY UPPER TARGET", event="show_mode_jackpot")
            self.machine.events.post("vulture_add_a_ball_ready")
        self.update_player_vars()

    def award_add_a_ball(self):
        if self.add_a_ball_awarded:
            return

        self._show_message("ADD-A-BALL!", "ALL TARGETS RED", event="show_mode_jackpot")
        self.machine.events.post("start_vulture_add_a_ball")
        self.machine.events.post("vulture_add_a_ball")
        self.add_a_ball_awarded = True

    def spinner_hit(self, **kwargs):
        if not self.started:
            return

        total = sum(self.stage_values[stage] for stage in self.stages.values())

        if self.upper_balls >= 2:
            total *= 2

        if self.case_file_extra_aerial_bonus and all(stage == 2 for stage in self.stages.values()):
            total += 100000
            self.machine.events.post("vulture_case_file_extra_aerial_bonus_awarded")

        self.award_score(total)
        self.bank_bonus(total)

        self.vulture_spins += 1
        self.vulture_banked_bonus += total

        player = self.machine.game.player
        player["active_mode_stat_1"] = self.vulture_spins
        player["vulture_banked_bonus"] = self.vulture_banked_bonus
        player["vulture_last_spinner_score"] = total

        self._show_message(
            "VULTURE SPINNER",
            "TOTAL COLLECTED",
            value=self.vulture_banked_bonus,
            event="show_mode_jackpot",
        )

    def bank_bonus(self, value):
        player = self.machine.game.player
        player["vulture_bonus"] = player["vulture_bonus"] + value
        player["active_mode_stat_2"] = player["vulture_bonus"]

    def target_timer_expired(self, target, **kwargs):
        if self.stages.get(target) != 2:
            return

        self.stages[target] = 1
        self.machine.events.post(f"vulture_show_{target}_yellow")
        self._show_message("TARGET DIMMED", f"{target.upper()} TARGET  20K")
        self.update_player_vars()

    def show_targets(self, **kwargs):
        for target, stage in self.stages.items():
            color = self.stage_name(stage)
            self.machine.events.post(f"vulture_show_{target}_{color}")

    @staticmethod
    def stage_name(stage):
        if stage == 1:
            return "yellow"
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
