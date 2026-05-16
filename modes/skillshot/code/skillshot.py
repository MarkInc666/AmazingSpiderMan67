from mpf.core.mode import Mode
import random

class SkillShot(Mode):

    """
    Skill shot mode.

    One shot is lit/flashing.
    Left/right flipper presses move the lit shot.
    First skill shot switch hit ends the mode.
    If the hit switch is the lit one, award:
        Ball 1 = 100,000
        Ball 2 = 200,000
        Ball 3 = 300,000
        etc.
    """

    SHOTS = [
        {
            "key": "saucer_left",
            "switch": "s_saucer_1",
            "lit_event": "skillshot_lit_saucer_left",
        },
        {
            "key": "saucer_center",
            "switch": "s_saucer_2",
            "lit_event": "skillshot_lit_saucer_center",
        },
        {
            "key": "saucer_right",
            "switch": "s_saucer_3",
            "lit_event": "skillshot_lit_saucer_right",
        },
        {
            "key": "star",
            "switch": "s_star_rollover",
            "lit_event": "skillshot_lit_star",
        },
        {
            "key": "upper_a",
            "switch": "s_inlane_a",
            "lit_event": "skillshot_lit_upper_a",
        },
        {
            "key": "upper_b",
            "switch": "s_inlane_b",
            "lit_event": "skillshot_lit_upper_b",
        },
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.skillshot_active = True
        self.skillshot_moved = False
        self.current_index = random.randint(0, len(self.SHOTS) - 1)
        
        # Flipper navigation.
        self.add_mode_event_handler("s_left_flipper_active", self.move_left)
        self.add_mode_event_handler("s_right_flipper_active", self.move_right)

        # Skill shot switches.
        for shot in self.SHOTS:
            self.add_mode_event_handler(
                f"{shot['switch']}_active",
                self.skillshot_switch_hit,
                shot_key=shot["key"]
            )

        self.light_current_shot()

    def move_left(self, **kwargs):
        if not self.skillshot_active:
            return

        self.skillshot_moved = True
        self.current_index -= 1

        if self.current_index < 0:
            self.current_index = len(self.SHOTS) - 1

        self.light_current_shot()

    def move_right(self, **kwargs):
        if not self.skillshot_active:
            return

        self.skillshot_moved = True
        self.current_index += 1

        if self.current_index >= len(self.SHOTS):
            self.current_index = 0

        self.light_current_shot()

    def light_current_shot(self):
        if not self.skillshot_active:
            return

        self.machine.events.post("skillshot_clear_lit_shot")

        lit_event = self.SHOTS[self.current_index]["lit_event"]
        self.machine.events.post(lit_event)
    
    def skillshot_switch_hit(self, shot_key=None, **kwargs):
        if not self.skillshot_active:
            return

        self.skillshot_active = False

        lit_key = self.SHOTS[self.current_index]["key"]

        if shot_key == lit_key:
            self.award_skillshot()
        else:
            self.machine.events.post(
                "skillshot_missed",
                hit=shot_key,
                lit=lit_key
            )

    def award_skillshot(self):
        
        self.machine.game.player["skillshots_awarded"] +=1
        
        award = self.machine.game.player["skillshots_awarded"] * 100000

        if self.skillshot_moved == False:
            award = award * 2

        self.player.score += award

        self.machine.events.post(
            "skillshot_awarded",
            points=award,
            skillshot_number=self.machine.game.player["skillshots_awarded"],
            shot=self.SHOTS[self.current_index]["key"]
        )

