import random
from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
    "title": "SCORPION",
    "intro_1": "Build Venom with the upper spinner.",
    "intro_2": "Exit left or right to set up your attack.",
    "intro_3": "Hit the single drop target for Jackpot.",
    "summary_title_complete": "SCORPION DEFEATED",
    "summary_title_failed": "SCORPION ESCAPED",
    "stat_1_label": "STINGS",
    "stat_1_var": "scorpion_stings",
    "stat_2_label": "BIGGEST JACKPOT",
    "stat_2_var": "scorpion_biggest_jackpot",
    "points_var": "active_mode_points",
    "state_var": "scorpion_state",
"""
class Scorpion(CaseFileMixin, Mode):

    VENOM_READY_HITS = 2
    MAX_TRIES = 3

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("scorpion")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA STING ATTEMPT AVAILABLE"),
            ("bigger_jackpots", "STING JACKPOTS BOOSTED"),
            ("more_time", "STING WINDOW EXTENDED"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "STING TARGET SPOTTED"),
        ])


        self.scorpion_venom_value = 0

        self.venom_hits = 0
        self.tries_used = 0
        self.state = "build"
        self.active_target_side = None
        self.required_target = None

        self.scorpion_stings = 0
        self.scorpion_biggest_jackpot = 0
        self.active_mode_points = 0

        self.add_mode_event_handler("scorpion_spinner_hit", self.spinner_hit)
        self.add_mode_event_handler("scorpion_right_exit_chosen", self.right_exit_chosen)
        self.add_mode_event_handler("scorpion_left_exit_chosen", self.left_exit_chosen)
        self.add_mode_event_handler("scorpion_sting_timeout", self.sting_timeout)

        for i in range(1, 4):
            self.add_mode_event_handler(f"scorpion_left_drop_{i}_hit", self.left_drop_hit, target=i)

        for i in range(1, 6):
            self.add_mode_event_handler(f"scorpion_right_drop_{i}_hit", self.right_drop_hit, target=i)

        self.add_mode_event_handler("s_left_drops_rubber_active", self.sting_miss_left)
        self.add_mode_event_handler("s_right_drops_rubber_active", self.sting_miss_right)
        self.machine.events.post("show_mode_message", message_mode_title="BUILD VENOM", message_mode_subtitle="HIT THE SPINNER")


    def mode_stop(self, **kwargs):
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        self.case_file_sting_multiplier_bonus = 0

        if self.has_case_file("more_jackpots"):
            self.MAX_TRIES += 1

        if self.has_case_file("bigger_jackpots"):
            self.case_file_sting_multiplier_bonus = 1

        if self.has_case_file("more_time"):
            self.machine.events.post("scorpion_case_file_sting_window_extended")

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.machine.events.post("scorpion_case_file_target_spotted")

    def spinner_hit(self, **kwargs):
        self.machine.game.player["score"] += 25000
        self.scorpion_venom_value += 50000

        self.active_mode_points += 25000
        self.machine.game.player["active_mode_points"] = self.active_mode_points

        if self.state != "build":
            return

        self.venom_hits += 1
        self.machine.events.post("scorpion_spinner_build")
        self.machine.events.post("show_mode_message", message_mode_title="VENOM BUILDS", message_mode_subtitle="SPINNER VALUE UP", message_mode_value=self.scorpion_venom_value)

        if self.venom_hits >= self.VENOM_READY_HITS:
            self.state = "ready"
            self.machine.events.post("scorpion_sting_ready")
            self.machine.events.post("show_mode_message_long", message_mode_title="STING READY", message_mode_subtitle="CHOOSE LEFT OR RIGHT EXIT")

    def right_exit_chosen(self, **kwargs):
        if self.state != "ready":
            return

        self.machine.events.post("scorpion_sting_lights_off")
        self.state = "sting"
        self.active_target_side = "left"

        self.required_target = random.randint(1, 3)

        # reset bank first
        self.machine.coils["c_left_bank_reset"].pulse()

        # delay so targets rise fully
        self.delay.add(
            ms=400,
            callback=self.prepare_left_bank_after_reset
        )

        self.machine.events.post("scorpion_safe_sting_started")
        self.machine.events.post("scorpion_sting_timer_start")
        self.machine.events.post("show_mode_countdown", message_mode_title="LEFT EXIT", message_mode_subtitle="LEFT BANK STING SHOT", message_mode_seconds=5)
    
    def left_exit_chosen(self, **kwargs):
        if self.state != "ready":
            return

        self.machine.events.post("scorpion_sting_lights_off")
        self.state = "sting"
        self.active_target_side = "right"

        self.required_target = random.randint(1, 5)

        self.machine.coils["c_right_bank_reset"].pulse()

        self.delay.add(
            ms=400,
            callback=self.prepare_right_bank_after_reset
        )

        self.machine.events.post("scorpion_hard_sting_started")
        self.machine.events.post("scorpion_sting_timer_start")
        self.machine.events.post("show_mode_countdown", message_mode_title="RIGHT EXIT", message_mode_subtitle="RIGHT BANK STING SHOT", message_mode_seconds=5)

    def prepare_left_bank_after_reset(self):
        for i in range(1, 4):
            if i != self.required_target:
                self.machine.coils[f"c_left_bank_drop_{i}"].pulse()

        self.machine.events.post("scorpion_left_sting_target_lit")
        self.machine.events.post("show_mode_message", message_mode_title="STING SHOT", message_mode_subtitle=f"LEFT TARGET {self.required_target}")

    def prepare_right_bank_after_reset(self):
        for i in range(1, 6):
            if i != self.required_target:
                self.machine.coils[f"c_right_bank_drop_{i}"].pulse()

        self.machine.events.post(f"scorpion_right_sting_target_{self.required_target}_lit")
        self.machine.events.post("show_mode_message", message_mode_title="STING SHOT", message_mode_subtitle=f"RIGHT TARGET {self.required_target}")

    def left_drop_hit(self, target, **kwargs):
        if self.state == "sting" and self.active_target_side == "left":
            if target == self.required_target:
                self.award_sting(safe=True)

    def sting_miss_left(self, **kwargs):
        if self.state == "sting" and self.active_target_side == "left":
            self.award_missed_sting()

    def right_drop_hit(self, target, **kwargs):
        if self.state == "sting" and self.active_target_side == "right":
            if target == self.required_target:
                self.award_sting(safe=False)

    def sting_miss_right(self, **kwargs):
        if self.state == "sting" and self.active_target_side == "right":
            self.award_missed_sting()

    def award_sting(self, safe):
        self.machine.events.post("scorpion_sting_timer_stop")

        self.scorpion_stings += 1
        self.machine.game.player["scorpion_stings"] = self.scorpion_stings

        if safe:
            self.jpval = self.scorpion_venom_value * (2 + self.case_file_sting_multiplier_bonus)
            self.machine.events.post("scorpion_safe_jackpot")
        else:
            self.jpval = self.scorpion_venom_value * (4 + self.case_file_sting_multiplier_bonus)
            self.machine.events.post("scorpion_hard_jackpot")

        self.machine.game.player["score"] += self.jpval
        self.active_mode_points += self.jpval
        self.machine.game.player["active_mode_points"] = self.active_mode_points
        if self.jpval > self.scorpion_biggest_jackpot:
            self.scorpion_biggest_jackpot = self.jpval
        self.machine.game.player["scorpion_biggest_jackpot"] = self.scorpion_biggest_jackpot

        self.machine.events.post("scorpion_sting_success")
        self.machine.events.post("show_mode_jackpot", message_mode_title="SCORPION JACKPOT", message_mode_subtitle="STING SEQUENCE", message_mode_value=self.jpval)
        self.reset_for_next_try()

    def award_missed_sting(self):
        self.machine.events.post("scorpion_sting_timer_stop")

        self.machine.game.player["score"] += 50000
        self.active_mode_points += 50000
        self.machine.game.player["active_mode_points"] = self.active_mode_points
        
        self.machine.events.post("scorpion_sting_miss")
        self.machine.events.post("show_mode_message", message_mode_title="STING FAILED", message_mode_subtitle="50K CONSOLATION", message_mode_value=50000)
        self.reset_for_next_try()

    def sting_timeout(self, **kwargs):
        if self.state != "sting":
            return

        self.machine.events.post("scorpion_sting_failed")
        self.machine.events.post("show_mode_message", message_mode_title="STING FAILED", message_mode_subtitle="OUT OF TIME")
        self.reset_for_next_try()

    def reset_for_next_try(self):
        self.machine.events.post("scorpion_sting_lights_off")
        self.tries_used += 1

        if self.tries_used >= self.MAX_TRIES:
            self.machine.events.post("scorpion_mode_complete")
            return

        self.venom_hits = 0
        self.state = "build"
        self.active_target_side = None

        self.machine.events.post("scorpion_build_phase_started")
        self.machine.events.post("show_mode_message", message_mode_title="BUILD VENOM", message_mode_subtitle="HIT THE SPINNER")
