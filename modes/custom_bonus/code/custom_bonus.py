from mpf.core.mode import Mode


class CustomBonus(Mode):

    BONUS_UNIT_VALUE = 1000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.add_mode_event_handler("custom_bonus_collect_bonus", self.collect_bonus)


    def collect_bonus(self, queue=None, **kwargs):
        player = self.machine.game.player

        bonus_count = player["bonus_count"], 0
        bonus_multiplier = player["bonus_multiplier"]
        vulture_bonus = player["vulture_bonus"]

        self.base_bonus_total = bonus_count * self.BONUS_UNIT_VALUE
        self.multiplier_extra_total = self.base_bonus_total * max(0, bonus_multiplier - 1)
        self.vulture_bonus_total = vulture_bonus
              
        self.grand_total = self.base_bonus_total + self.multiplier_extra_total + self.vulture_bonus_total

        player["score"] += self.grand_total
        
        self.delay.add(
            name="custom_bonus_delay",
            ms=4000,
            callback=self.finish_bonus
        )


    def finish_bonus(self):
        self.machine.events.post("custom_bonus_complete")
