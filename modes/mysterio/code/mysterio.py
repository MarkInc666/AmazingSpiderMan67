from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin
from modes.common.shot_registry import Shot
import random

"""
    "title": "MYSTERIO",
    "intro_1": "Find the real Mysterio.",
    "intro_2": "Shoot lit illusions to reveal him.",
    "intro_3": "Choose carefully for Jackpot.",
    "summary_title_complete": "MYSTERIO DEFEATED",
    "summary_title_failed": "MYSTERIO ESCAPED",
    "stat_1_label": "REVEALS USED",
    "stat_1_var": "mysterio_illusions_cleared",
    "stat_2_label": "JACKPOT",
    "stat_2_var": "mysterio_jackpot_value",
    "points_var": "mysterio_mode_points",
    "state_var": "mysterio_state",
"""
class Mysterio(CaseFileMixin, Mode):

    STARTING_SUPER = 1000000
    SUPER_FLOOR = 300000
    WRONG_DEDUCT = 100000
    CLUE_DEDUCT = 10000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.super_value = self.STARTING_SUPER
        self.mysterio_illusions_cleared = 0
        self.mysterio_jackpot_value = 0
        self.mysterio_mode_points = 0

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("mysterio")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA ILLUSION CHANCE AVAILABLE"),
            ("bigger_jackpots", "SUPER JACKPOT BOOSTED"),
            ("more_time", "ILLUSION VALUE PROTECTED"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FALSE SHOT REVEALED"),
        ])

        self.shots = [
            Shot("left_web", 10, 70, "mysterio_left_web_hit", group="left"),
            Shot("spinner", 20, 50, "mysterio_spinner_hit", group="center"),
            Shot("left_drops", 40, 60, "mysterio_left_drops_hit", group="left"),
            Shot("saucers", 50, 30, "mysterio_saucers_hit", group="left"),
            Shot("center_web", 60, 30, "mysterio_center_web_hit", group="center"),
            Shot("upper_spinner", 90, 30, "mysterio_upper_spinner_hit", group="upper"),
            Shot("upper_targets", 95, 20, "mysterio_upper_targets_hit", group="upper"),
            Shot("right_drops", 100, 80, "mysterio_right_drops_hit", group="right"),
        ]

        self.shots_by_name = {shot.name: shot for shot in self.shots}

        for shot in self.shots:
            self.add_mode_event_handler(shot.event, self.shot_hit, shot_name=shot.name)

        self.start_trial()

    def mode_stop(self, **kwargs):
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        self.case_file_extra_chance_available = False
        self.case_file_reveal_false_shot = False

        if self.has_case_file("more_jackpots"):
            self.case_file_extra_chance_available = True

        if self.has_case_file("bigger_jackpots"):
            self.STARTING_SUPER += 250000
            self.super_value = self.STARTING_SUPER

        if self.has_case_file("more_time"):
            self.WRONG_DEDUCT = max(25000, int(self.WRONG_DEDUCT / 2))
            self.CLUE_DEDUCT = max(5000, int(self.CLUE_DEDUCT / 2))

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.case_file_reveal_false_shot = True

    def start_trial(self):
        for shot in self.shots:
            shot.is_lit = True
            shot.is_clue = False
            shot.is_jackpot = False
            shot.disabled = False
            shot.hint = None

        jackpot = random.choice(self.shots)
        jackpot.is_jackpot = True

        clue_shots = random.sample(
            [s for s in self.shots if not s.is_jackpot],
            5
        )

        for clue in clue_shots:
            clue.is_clue = True
            clue.hint = self.build_hint(jackpot)

        if getattr(self, "case_file_reveal_false_shot", False):
            false_shots = [s for s in self.shots if not s.is_jackpot and not s.is_clue]
            if false_shots:
                revealed = random.choice(false_shots)
                revealed.disabled = True
                revealed.is_lit = False
                self.machine.events.post(f"mysterio_stop_{revealed.name}")
                self.machine.events.post("mysterio_case_file_false_shot_revealed", shot=revealed.name)
                self.machine.events.post("show_mode_message", message_mode_title="FALSE SHOT REMOVED", message_mode_subtitle=revealed.name.replace("_", " ").upper())

        self.machine.game.player["mysterio_super_value"] = self.super_value
        self.machine.events.post("mysterio_startup_complete")
        self.machine.events.post("mysterio_all_shots_lit")
        self.machine.events.post("show_mode_message_long", message_mode_title="ILLUSION TRIAL", message_mode_subtitle="FIND THE REAL SHOT", message_mode_value=self.super_value)

    def build_hint(self, jackpot_shot):
        if jackpot_shot.group == "upper":
            return "upper"
        if jackpot_shot.group == "center":
            return "center"
        if jackpot_shot.x < 60:
            return "left"
        return "right"     

    def shot_hit(self, shot_name=None, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return

        if not shot_name:
            return

        shot = self.shots_by_name.get(shot_name)
        if not shot or shot.disabled:
            return

        self.mysterio_illusions_cleared += 1
        self.machine.game.player["mysterio_illusions_cleared"] = self.mysterio_illusions_cleared

        if shot.is_jackpot:
            self.collect_super(shot)
            return

        if shot.is_clue:
            self.handle_clue_shot(shot)
        else:
            self.handle_wrong_shot(shot)

        self.check_gate_status()


    def check_gate_status(self):
        upper_lit = False
        for shot in self.shots:
            if shot.disabled == False and shot.hint == "upper":
                upper_lit = True
        if upper_lit:
            self.machine.events.post("rooftop_diverter_open")
        else:
            self.machine.events.post("rooftop_diverter_close")


    def handle_wrong_shot(self, shot):
        if getattr(self, "case_file_extra_chance_available", False):
            self.case_file_extra_chance_available = False
            self.machine.events.post("mysterio_case_file_extra_chance_used", shot=shot.name)
            self.machine.events.post("show_mode_message", message_mode_title="EXTRA CHANCE", message_mode_subtitle="BAD SHOT IGNORED")
            shot.disabled = True
            shot.is_lit = False
            self.machine.events.post(f"mysterio_stop_{shot.name}")
            return

        self.machine.events.post("mysterio_wrong_shot")
        self.machine.events.post("show_mode_message", message_mode_title="WRONG SHOT", message_mode_subtitle="SUPER VALUE REDUCED", message_mode_value=self.super_value)
        self.machine.events.post("mysterio_score_wrong_shot")
        
        self.mysterio_mode_points += 10000
        self.machine.game.player["mysterio_mode_points"] = self.mysterio_mode_points
        self.machine.game.player["score"] += 10000

        self.reduce_super(self.WRONG_DEDUCT)

        shot.disabled = True
        shot.is_lit = False
        self.machine.events.post(f"mysterio_stop_{shot.name}")

    def handle_clue_shot(self, shot):
        self.machine.events.post("mysterio_clue_shot")
        self.machine.events.post("show_mode_message", message_mode_title="CLUE FOUND", message_mode_subtitle=f"SPIDEY SENSE: {shot.hint.upper()}")
        self.machine.events.post("mysterio_score_wrong_shot")

        self.mysterio_mode_points += 5000
        self.machine.game.player["mysterio_mode_points"] = self.mysterio_mode_points
        self.machine.game.player["score"] += 5000

        self.reduce_super(self.CLUE_DEDUCT)

        if shot.hint == "left":
            self.machine.events.post("mysterio_spidey_sense_left")
        elif shot.hint == "right":
            self.machine.events.post("mysterio_spidey_sense_right")
        elif shot.hint == "upper":
            self.machine.events.post("mysterio_spidey_sense_upper")
        else:
            self.machine.events.post("mysterio_spidey_sense_center")

        shot.disabled = True
        shot.is_lit = False
        self.machine.events.post(f"mysterio_stop_{shot.name}")

    def reduce_super(self, amount):
        self.super_value = max(self.SUPER_FLOOR, self.super_value - amount)
        self.machine.game.player["mysterio_super_value"] = self.super_value
        self.machine.events.post("mysterio_super_changed")
        self.machine.events.post("show_mode_message", message_mode_title="SUPER VALUE", message_mode_subtitle="MYSTERIO JACKPOT", message_mode_value=self.super_value)

    def collect_super(self, shot):
        self.machine.game.player["mysterio_jackpot_value"] = self.super_value
        self.mysterio_mode_points += self.super_value

        self.machine.game.player["mysterio_mode_points"] = self.mysterio_mode_points
        self.machine.game.player["score"] += self.super_value

        self.machine.events.post("mysterio_super_collected")
        self.machine.events.post("show_mode_jackpot", message_mode_title="MYSTERIO JACKPOT", message_mode_subtitle=shot.name.replace("_", " ").upper(), message_mode_value=self.super_value)
        self.machine.events.post("mysterio_mode_complete")