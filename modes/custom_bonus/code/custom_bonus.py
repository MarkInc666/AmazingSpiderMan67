from mpf.core.mode import Mode


class CustomBonus(Mode):

    BONUS_UNIT_VALUE = 1000

    BANKED_BONUS_VARS = [
        "vulture_bonus",
        "goblin_bonus",
        "vulcan_bonus",
        "diamond_bonus",
        "super_swami_bonus",
        "dumpty_bonus",
        "radiation_bonus",
        "plutonians_bonus",
        "swamp_bonus",
        "technician_bonus",
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.add_mode_event_handler("custom_bonus_collect_bonus", self.collect_bonus)

    def collect_bonus(self, queue=None, **kwargs):
        player = self.machine.game.player

        bonus_count = player["bonus_count"]
        bonus_multiplier = player["bonus_multiplier"]

        self.base_bonus_total = bonus_count * self.BONUS_UNIT_VALUE
        self.multiplier_extra_total = self.base_bonus_total * max(0, bonus_multiplier - 1)
        self.banked_bonus_total = sum(player[var_name] for var_name in self.BANKED_BONUS_VARS)

        # Keep the old attribute for anything that may still reference it.
        self.vulture_bonus_total = player["vulture_bonus"]

        self.grand_total = (
            self.base_bonus_total
            + self.multiplier_extra_total
            + self.banked_bonus_total
        )

        player["score"] += self.grand_total

        for var_name in self.BANKED_BONUS_VARS:
            player[var_name] = 0

        if not player["hold_bonus"]:
            player["bonus_count"] = 0
            player["bonus_multiplier"] = 1

        self.delay.add(
            name="custom_bonus_delay",
            ms=4000,
            callback=self.finish_bonus
        )

    def finish_bonus(self):
        self.machine.events.post("custom_bonus_complete")
