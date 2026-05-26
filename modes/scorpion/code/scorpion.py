import random
from mpf.core.delays import DelayManager
from mpf.core.mode import Mode

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
    "points_var": "scorpion_mode_points",
    "completed_var": "scorpion_completed",
"""
class Scorpion(Mode):

    VENOM_READY_HITS = 4
    MAX_TRIES = 3

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)

        self.scorpion_venom_value = 0

        self.venom_hits = 0
        self.tries_used = 0
        self.state = "build"
        self.active_target_side = None
        self.required_target = None

        self.scorpion_stings = 0
        self.scorpion_biggest_jackpot = 0
        self.scorpion_mode_points = 0

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


    def spinner_hit(self, **kwargs):
        if self.state != "build":
            return

        self.venom_hits += 1
        self.machine.events.post("scorpion_spinner_build")

        self.machine.game.player["score"] += 25000
        self.scorpion_venom_value += 50000

        self.scorpion_mode_points += 25000
        self.machine.game.player["scorpion_mode_points"] = self.scorpion_mode_points

        if self.venom_hits >= self.VENOM_READY_HITS:
            self.state = "ready"
            self.machine.events.post("scorpion_sting_ready")

    def right_exit_chosen(self, **kwargs):
        if self.state != "ready":
            return

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
    
    def left_exit_chosen(self, **kwargs):
        if self.state != "ready":
            return

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

    def prepare_left_bank_after_reset(self):
        for i in range(1, 4):
            if i != self.required_target:
                self.machine.coils[f"c_left_bank_drop_{i}"].pulse()

    def prepare_right_bank_after_reset(self):
        for i in range(1, 6):
            if i != self.required_target:
                self.machine.coils[f"c_right_bank_drop_{i}"].pulse()

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
            self.jpval = self.scorpion_venom_value*2
            self.machine.events.post("scorpion_safe_jackpot")
        else:
            self.jpval = self.scorpion_venom_value*4
            self.machine.events.post("scorpion_hard_jackpot")

        self.machine.game.player["score"] += self.jpval
        self.scorpion_mode_points += self.jpval
        self.machine.game.player["scorpion_mode_points"] = self.scorpion_mode_points
        if self.jpval > self.scorpion_biggest_jackpot:
            self.scorpion_biggest_jackpot = self.jpval
        self.machine.game.player["scorpion_biggest_jackpot"] = self.scorpion_biggest_jackpot

        self.machine.events.post("scorpion_sting_success")
        self.reset_for_next_try()

    def award_missed_sting(self):
        self.machine.events.post("scorpion_sting_timer_stop")

        self.machine.game.player["score"] += 50000
        self.scorpion_mode_points += 50000
        self.machine.game.player["scorpion_mode_points"] = self.scorpion_mode_points
        
        self.machine.events.post("scorpion_sting_miss")
        self.reset_for_next_try()

    def sting_timeout(self, **kwargs):
        if self.state != "sting":
            return

        self.machine.events.post("scorpion_sting_failed")
        self.reset_for_next_try()

    def reset_for_next_try(self):
        self.tries_used += 1

        if self.tries_used >= self.MAX_TRIES:
            self.machine.events.post("scorpion_mode_complete")
            return

        self.venom_hits = 0
        self.state = "build"
        self.active_target_side = None

        self.machine.events.post("scorpion_build_phase_started")