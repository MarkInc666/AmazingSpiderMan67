from mpf.core.mode import Mode


class CustomBonus(Mode):

    BONUS_UNIT_VALUE = 1000
    DAILY_BUGLE_NEWSPAPER_REVEAL_MS = 3000
    CUSTOM_BONUS_PRESENTATION_MS = 4000

    BANKED_BONUS_VARS = [
        "vulture_bonus",
        "doc_ock_bonus",
        "vulcan_bonus",
        "diamond_bonus",
        "harley_bonus",
        "super_swami_bonus",
        "noah_boddy_bonus",
        "blotto_bonus",
        "devargas_bonus",
        "swamp_bonus",
        "technician_bonus",
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        player = self.machine.game.player
        player["custom_bonus_vuk_hold_active"] = 1
        self.machine.events.post("custom_bonus_vuk_ownership_claimed")

        # The award is revealed at the three-second Daily Bugle mark. Keep the
        # newspaper visible for another three seconds, then let Custom Bonus
        # take over the display and award the bonus.
        self.delay.reset(
            name="custom_bonus_takeover",
            ms=self.DAILY_BUGLE_NEWSPAPER_REVEAL_MS,
            callback=self.collect_bonus,
        )

    def mode_stop(self, **kwargs):
        self.delay.remove("custom_bonus_takeover")
        self.delay.remove("custom_bonus_delay")
        self.delay.remove("custom_bonus_display_update")
        if self.machine.game:
            self.machine.game.player["custom_bonus_vuk_hold_active"] = 0
        self.machine.events.post("custom_bonus_slide_hide")
        super().mode_stop(**kwargs)

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

        # Mode bonuses are persistent player achievements. Collect Bonus may
        # award their current values immediately, but must not consume them;
        # they are awarded again during every later end-of-ball bonus count.
        if not player["hold_bonus"]:
            player["bonus_count"] = 0
            player["bonus_multiplier"] = 1

        self.machine.events.post("custom_bonus_slide_show")
        self.delay.reset(
            name="custom_bonus_display_update",
            ms=1,
            callback=self._show_bonus_total,
        )
        self.delay.reset(
            name="custom_bonus_delay",
            ms=self.CUSTOM_BONUS_PRESENTATION_MS,
            callback=self.finish_bonus,
        )

    def _show_bonus_total(self):
        if not self.machine.game:
            return
        self.machine.events.post(
            "bonus_entry",
            entry="final_score_hold",
            text="BONUS TOTAL",
            score=self.grand_total,
            running_total=self.grand_total,
            total_state="hidden",
            player_number=self.machine.game.player.number,
        )

    def finish_bonus(self):
        if not self.machine.game:
            return
        self.machine.game.player["custom_bonus_vuk_hold_active"] = 0
        self.machine.events.post("custom_bonus_slide_hide")
        self.machine.events.post("custom_bonus_complete")
        self.machine.events.post("request_vuk_eject")
