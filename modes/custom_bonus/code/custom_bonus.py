from mpf.core.mode import Mode


class CustomBonus(Mode):

    BONUS_UNIT_VALUE = 1000

    NORMAL_DELAY_MS = 120
    FAST_DELAY_MS = 30

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.queue = None
        self.running = False
        self.speed_level = 0

        self.bonus_count_remaining = 0
        self.base_bonus_total = 0
        self.multiplier_extra_total = 0
        self.vulture_bonus_total = 0
        self.grand_total = 0

        self.add_mode_event_handler("custom_bonus_init", self.init_bonus_vars)
        self.add_mode_event_handler("ball_ending", self.ball_ending)
        self.add_mode_event_handler("custom_bonus_speed_press", self.speed_press)

        self.add_mode_event_handler("custom_bonus_start", self.ball_ending )        

    def init_bonus_vars(self, **kwargs):
        player = self.machine.game.player

        player["bonus_count"] = player.get("bonus_count", 0)
        player["bonus_multiplier"] = player.get("bonus_multiplier", 1)
        player["vulture_bonus"] = player.get("vulture_bonus", 0)

        player["custom_bonus_phase"] = "idle"
        player["custom_bonus_base_awarded"] = 0
        player["custom_bonus_multiplier_awarded"] = 0
        player["custom_bonus_vulture_awarded"] = 0
        player["custom_bonus_total_awarded"] = 0
        player["custom_bonus_count_remaining"] = 0

    def ball_ending(self, queue=None, **kwargs):
        player = self.machine.game.player

        if player.get("tilted", False):
            return

        if self.running:
            return

        self.queue = queue
        if self.queue:
            self.queue.wait()

        self.running = True
        self.speed_level = 0

        bonus_count = player.get("bonus_count", 0)
        bonus_multiplier = player.get("bonus_multiplier", 1)
        vulture_bonus = player.get("vulture_bonus", 0)

        self.bonus_count_remaining = bonus_count
        self.base_bonus_total = bonus_count * self.BONUS_UNIT_VALUE
        self.multiplier_extra_total = self.base_bonus_total * max(0, bonus_multiplier - 1)
        self.vulture_bonus_total = vulture_bonus
        self.grand_total = self.base_bonus_total + self.multiplier_extra_total + self.vulture_bonus_total

        player["custom_bonus_phase"] = "base_bonus"
        player["custom_bonus_count_remaining"] = self.bonus_count_remaining
        player["custom_bonus_base_awarded"] = 0
        player["custom_bonus_multiplier_awarded"] = 0
        player["custom_bonus_vulture_awarded"] = 0
        player["custom_bonus_total_awarded"] = 0

        self.machine.events.post("custom_bonus_base_started")
        self.count_base_bonus()

    def speed_press(self, **kwargs):
        if not self.running:
            return

        self.speed_level += 1

        if self.speed_level == 1:
            self.machine.events.post("custom_bonus_speed_fast")
        else:
            self.machine.events.post("custom_bonus_skip_requested")

    def current_delay(self):
        if self.speed_level >= 1:
            return self.FAST_DELAY_MS
        return self.NORMAL_DELAY_MS

    def count_base_bonus(self):
        player = self.machine.game.player

        if self.speed_level >= 2:
            remaining_value = self.bonus_count_remaining * self.BONUS_UNIT_VALUE
            player["score"] += remaining_value
            player["custom_bonus_base_awarded"] += remaining_value
            self.bonus_count_remaining = 0
            player["custom_bonus_count_remaining"] = 0

        if self.bonus_count_remaining <= 0:
            self.machine.events.post("custom_bonus_base_complete")
            self.award_multiplier_bonus()
            return

        self.bonus_count_remaining -= 1

        player["score"] += self.BONUS_UNIT_VALUE
        player["custom_bonus_base_awarded"] += self.BONUS_UNIT_VALUE
        player["custom_bonus_count_remaining"] = self.bonus_count_remaining
        player["custom_bonus_total_awarded"] += self.BONUS_UNIT_VALUE

        self.machine.events.post("custom_bonus_base_tick")

        self.delay.add(
            name="custom_bonus_base_tick",
            ms=self.current_delay(),
            callback=self.count_base_bonus
        )

    def award_multiplier_bonus(self):
        player = self.machine.game.player
        player["custom_bonus_phase"] = "multiplier"

        self.machine.events.post("custom_bonus_multiplier_started")

        if self.multiplier_extra_total > 0:
            player["score"] += self.multiplier_extra_total
            player["custom_bonus_multiplier_awarded"] = self.multiplier_extra_total
            player["custom_bonus_total_awarded"] += self.multiplier_extra_total

        self.delay.add(
            name="custom_bonus_multiplier_done",
            ms=self.current_delay() * 6,
            callback=self.award_vulture_bonus
        )

    def award_vulture_bonus(self):
        player = self.machine.game.player
        player["custom_bonus_phase"] = "vulture_bonus"

        self.machine.events.post("custom_bonus_vulture_started")

        if self.vulture_bonus_total > 0:
            player["score"] += self.vulture_bonus_total
            player["custom_bonus_vulture_awarded"] = self.vulture_bonus_total
            player["custom_bonus_total_awarded"] += self.vulture_bonus_total

        self.delay.add(
            name="custom_bonus_vulture_done",
            ms=self.current_delay() * 6,
            callback=self.show_total_bonus
        )

    def show_total_bonus(self):
        player = self.machine.game.player
        player["custom_bonus_phase"] = "total"
        player["custom_bonus_total_awarded"] = self.grand_total

        self.machine.events.post("custom_bonus_total_started")

        self.delay.add(
            name="custom_bonus_total_done",
            ms=self.current_delay() * 10,
            callback=self.finish_bonus
        )

    def finish_bonus(self):
        player = self.machine.game.player

        player["custom_bonus_phase"] = "complete"

        self.machine.events.post("custom_bonus_complete")

        self.running = False
        self.speed_level = 0

        if self.queue:
            self.queue.clear()
            self.queue = None
            