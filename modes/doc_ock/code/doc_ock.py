from mpf.core.mode import Mode
import random


class DocOck(Mode):

    ARMS = [1, 2, 3, 4]
    MAX_BREAKOUT_TARGETS = 3

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        # False = free, True = locked
        self.locked_arms = {
            1: False,
            2: False,
            3: False,
            4: False,
        }

        # Start with one arm already disabled/locked.
        self.locked_arms[1] = True

        self.selected_arm = 2
        self.jackpots_collected = 0
        self.active_breakouts = set()

        self.add_mode_event_handler("doc_ock_start", self.start)
        self.add_mode_event_handler("doc_ock_rotate_left", self.rotate_left)
        self.add_mode_event_handler("doc_ock_rotate_right", self.rotate_right)
        self.add_mode_event_handler("doc_ock_jackpot_request", self.jackpot_request)
        self.add_mode_event_handler("doc_ock_timed_release_complete", self.timed_release)

        for arm in self.ARMS:
            self.add_mode_event_handler(
                f"doc_ock_arm_{arm}_hit",
                self.arm_hit,
                arm=arm
            )

        for breakout in [1, 2, 3]:
            self.add_mode_event_handler(
                f"doc_ock_breakout_{breakout}_request",
                self.breakout_hit,
                breakout=breakout
            )

    def start(self, **kwargs):
        self.machine.events.post("doc_ock_refresh_locks")
        self.light_selected_arm()
        self.check_jackpot_lit()

    def rotate_left(self, **kwargs):
        self.selected_arm -= 1
        if self.selected_arm < 1:
            self.selected_arm = 4
        self.light_selected_arm()

    def rotate_right(self, **kwargs):
        self.selected_arm += 1
        if self.selected_arm > 4:
            self.selected_arm = 1
        self.light_selected_arm()

    def light_selected_arm(self):
        self.machine.events.post(f"doc_ock_arm_{self.selected_arm}_selected")

    def arm_hit(self, arm, **kwargs):
        # Only the currently selected/free arm can be locked.
        if arm != self.selected_arm:
            return

        if self.locked_arms[arm]:
            return

        self.locked_arms[arm] = True
        self.machine.events.post("doc_ock_arm_locked_score")
        self.machine.events.post("doc_ock_refresh_locks")
        self.check_jackpot_lit()

    def locked_count(self):
        return sum(1 for locked in self.locked_arms.values() if locked)

    def free_count(self):
        return 4 - self.locked_count()

    def check_jackpot_lit(self):
        if self.locked_count() > 0:
            self.machine.events.post("doc_ock_jackpot_lit")

    def jackpot_request(self, **kwargs):
        locked = self.locked_count()

        if locked <= 0:
            return

        # Award base JP through variable_player.
        self.machine.events.post("doc_ock_jackpot_award")
        self.machine.events.post("doc_ock_jackpot_collected")

        self.jackpots_collected += 1

        self.spawn_breakout_target()

        if self.jackpots_collected >= 2:
            self.machine.events.post("doc_ock_start_timed_release")

        self.check_mode_over()

    def spawn_breakout_target(self):
        if len(self.active_breakouts) >= self.MAX_BREAKOUT_TARGETS:
            return

        available = [1, 2, 3]
        random.shuffle(available)

        for target in available:
            if target not in self.active_breakouts:
                self.active_breakouts.add(target)
                self.machine.events.post(f"doc_ock_breakout_{target}_lit")
                return

    def breakout_hit(self, breakout, **kwargs):
        if breakout not in self.active_breakouts:
            return

        self.active_breakouts.remove(breakout)
        self.release_random_locked_arm()
        self.machine.events.post("doc_ock_breakout_hit")
        self.check_mode_over()

    def timed_release(self, **kwargs):
        if self.jackpots_collected < 2:
            return

        self.release_random_locked_arm()
        self.machine.events.post("doc_ock_breakout_hit")

        if self.check_mode_over():
            return

        self.machine.events.post("doc_ock_start_timed_release")

    def release_random_locked_arm(self):
        locked = [arm for arm, is_locked in self.locked_arms.items() if is_locked]

        if not locked:
            return

        arm = random.choice(locked)
        self.locked_arms[arm] = False
        self.machine.events.post("doc_ock_refresh_locks")

    def check_mode_over(self):
        if self.locked_count() <= 0:
            self.machine.events.post("doc_ock_mode_complete")
            return True
        return False