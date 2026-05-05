from mpf.core.mode import Mode
from modes.common.shot_registry import Shot
import random


class Mysterio(Mode):

    STARTING_SUPER = 1000000
    SUPER_FLOOR = 300000
    WRONG_DEDUCT = 100000
    CLUE_DEDUCT = 25000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.super_value = self.STARTING_SUPER

        self.shots = [
            Shot("left_web", 10, 70, "mysterio_left_web_hit", group="left"),
            Shot("spinner", 20, 50, "mysterio_spinner_hit", group="center"),
            Shot("left_drops", 40, 60, "mysterio_left_drops_hit", group="left"),
            Shot("saucers", 50, 30, "mysterio_saucers_hit", group="left"),
            Shot("right_web", 80, 30, "mysterio_right_web_hit", group="right"),
            Shot("upper_spinner", 90, 30, "mysterio_upper_spinner_hit", group="upper"),
            Shot("upper_targets", 95, 20, "mysterio_upper_target_hit", group="upper"),
            Shot("right_drops", 100, 80, "mysterio_right_drops_hit", group="right"),
        ]

        self.shots_by_name = {shot.name: shot for shot in self.shots}

        for shot in self.shots:
            self.add_mode_event_handler(shot.event, self.shot_hit, shot_name=shot.name)

        self.start_trial()

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
            3
        )

        for clue in clue_shots:
            clue.is_clue = True
            clue.hint = self.build_hint(jackpot)

        self.machine.game.player["mysterio_super_value"] = self.super_value
        self.machine.events.post("mysterio_trial_started")
        self.machine.events.post("mysterio_all_shots_lit")

    def build_hint(self, jackpot_shot):
        if jackpot_shot.x < 60:
            return "left"
        if jackpot_shot.x >= 60:
            return "right"
        if jackpot_shot.group == "upper":
            return "upper"
        return "center"

    def shot_hit(self, shot_name=None, **kwargs):
        if not shot_name:
            return

        shot = self.shots_by_name.get(shot_name)
        if not shot or shot.disabled:
            return

        if shot.is_jackpot:
            self.collect_super(shot)
            return

        if shot.is_clue:
            self.handle_clue_shot(shot)
        else:
            self.handle_wrong_shot(shot)

    def handle_wrong_shot(self, shot):
        self.machine.events.post("mysterio_wrong_shot")
        self.machine.events.post("mysterio_score_wrong_shot")

        self.reduce_super(self.WRONG_DEDUCT)

        shot.disabled = True
        shot.is_lit = False
        self.machine.events.post(f"mysterio_stop_{shot.name}")

    def handle_clue_shot(self, shot):
        self.machine.events.post("mysterio_clue_shot")
        self.machine.events.post("mysterio_score_wrong_shot")

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

    def collect_super(self, shot):
        self.machine.game.player["mysterio_award_value"] = self.super_value
        self.machine.events.post("mysterio_super_collected")
        self.machine.events.post(f"mysterio_{shot.name}_super_collected")
        self.machine.events.post("mysterio_mode_complete")