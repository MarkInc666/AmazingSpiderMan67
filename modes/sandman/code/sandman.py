from mpf.core.mode import Mode
from mpf.core.delays import DelayManager


class Sandman(Mode):

    BANK_TARGETS = [1, 2, 3, 4, 5]
    MAX_BANKS = 3
    MOVE_INTERVAL_MS = 3000
    RESET_SETTLE_MS = 500

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)

        self.current_flash = 1
        self.down_targets = set()
        self.flash_hits = 0
        self.banks_completed = 0
        self.hit_order = []

        for target in self.BANK_TARGETS:
            self.add_mode_event_handler(
                f"sandman_drop_{target}_hit",
                self.drop_hit,
                target=target
            )

        self.add_mode_event_handler("sandman_start_bank", self.start_bank)
        self.machine.coils["c_right_bank_reset"].pulse()

    def start_bank(self, **kwargs):
        self.down_targets = set()
        self.hit_order = []
        self.current_flash = 1

        self.machine.coils["c_right_bank_reset"].pulse()

        self.delay.add(
            ms=self.RESET_SETTLE_MS,
            callback=self.after_bank_reset
        )

    def after_bank_reset(self):
        self.light_current_flash()
        self.schedule_next_shift()

    def schedule_next_shift(self):
        self.delay.remove("sandman_shift")
        self.delay.add(
            name="sandman_shift",
            ms=self.MOVE_INTERVAL_MS,
            callback=self.shift_flash
        )

    def shift_flash(self):
        self.down_targets.add(self.current_flash)
        self.machine.coils["c_right_bank_drop_{self.current_flash}"].pulse()

        next_target = self.find_next_standing_target(self.current_flash)

        if next_target is None:
            self.complete_bank()
            return

        self.current_flash = next_target
        self.light_current_flash()
        self.schedule_next_shift()

    def find_next_standing_target(self, current):
        ordered = self.BANK_TARGETS[current:] # no wrap  + self.BANK_TARGETS[:current]

        for target in ordered:
            if target not in self.down_targets:
                return target

        return None

    def drop_hit(self, target, **kwargs):
        if target in self.down_targets:
            return

        self.down_targets.add(target)
        self.hit_order.append(target)

        if target == self.current_flash:
            self.flash_hits += 1
            self.machine.events.post("sandman_flashing_hit")
        else:
            self.machine.events.post("sandman_regular_hit")

        if len(self.down_targets) >= 5:
            self.complete_bank()
            return

        if target == self.current_flash:
            next_target = self.find_next_standing_target(self.current_flash)
            if next_target is not None:
                self.current_flash = next_target
                self.light_current_flash()
                self.schedule_next_shift()

    def complete_bank(self):
        self.delay.remove("sandman_shift")

        self.banks_completed += 1
        self.machine.events.post("sandman_bank_complete")

        if self.flash_hits >= 5:
            self.machine.events.post("sandman_five_flashing_jackpot")
            self.flash_hits = 0

        if self.hit_order == [1, 2, 3, 4, 5]:
            self.machine.events.post("sandman_left_to_right_jackpot")

        if self.banks_completed >= self.MAX_BANKS:
            self.machine.events.post("sandman_mode_complete")
            self.machine.events.post("reset_5bank")
            return

        self.delay.add(
            ms=750,
            callback=self.start_bank
        )

    def light_current_flash(self):
        self.machine.events.post(f"sandman_flash_{self.current_flash}")