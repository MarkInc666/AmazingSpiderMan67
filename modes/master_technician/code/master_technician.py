import random

from mpf.core.mode import Mode


class MasterTechnician(Mode):

    DROP_SCORE = 25000
    SPINNER_BASE = 50000
    SPINNER_PER_DROP = 50000
    SPINNER_MAX = 400000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.left_down = set()
        self.right_down = set()
        self.pending_inlane_drop = None

        self.add_mode_event_handler("master_technician_start", self.met_start)
        self.add_mode_event_handler("master_technician_spinner_hit", self.spinner_hit)
        self.add_mode_event_handler("master_technician_saucer_hit", self.saucer_hit)
        self.add_mode_event_handler("master_technician_inlane_hit", self.inlane_hit)

        for target in range(1, 4):
            self.add_mode_event_handler(
                f"master_technician_left_drop_{target}_hit",
                self.left_drop_hit,
                target=target
            )

        for target in range(1, 6):
            self.add_mode_event_handler(
                f"master_technician_right_drop_{target}_hit",
                self.right_drop_hit,
                target=target
            )

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        super().mode_stop(**kwargs)

    def met_start(self, **kwargs):
        self.update_player_vars()
        self._update_saucer_guidance()

    def left_drop_hit(self, target, **kwargs):
        key = f"left_{target}"
        if self.pending_inlane_drop == key:
            self.pending_inlane_drop = None
            self.delay.remove("master_technician_inlane_drop_guard")

        if target in self.left_down:
            return

        self.left_down.add(target)
        self.award_score(self.DROP_SCORE)
        self.machine.events.post("master_technician_drop_scored")
        self.after_drop_hit()

    def right_drop_hit(self, target, **kwargs):
        key = f"right_{target}"
        if self.pending_inlane_drop == key:
            self.pending_inlane_drop = None
            self.delay.remove("master_technician_inlane_drop_guard")

        if target in self.right_down:
            return

        self.right_down.add(target)
        self.award_score(self.DROP_SCORE)
        self.machine.events.post("master_technician_drop_scored")
        self.after_drop_hit()


    def inlane_hit(self, **kwargs):
        """Knock down one random standing target from either bank."""
        if self.pending_inlane_drop is not None:
            return

        standing = [
            *(f"left_{target}" for target in range(1, 4) if target not in self.left_down),
            *(f"right_{target}" for target in range(1, 6) if target not in self.right_down),
        ]
        if not standing:
            return

        target_key = random.choice(standing)
        self.pending_inlane_drop = target_key
        self.delay.reset(
            name="master_technician_inlane_drop_guard",
            ms=1000,
            callback=self._clear_inlane_drop_guard,
        )
        self.machine.drop_targets[f"dt_{target_key}"].knockdown()
        self.machine.events.post("master_technician_inlane_advance")

    def _clear_inlane_drop_guard(self):
        # Allow another inlane attempt if the physical target did not register.
        self.pending_inlane_drop = None

    def saucer_hit(self, **kwargs):
        """Reset only the left three-bank and preserve right-bank progress."""
        if self.left_down:
            self.left_down.clear()
            self.machine.events.post("drop_target_bank_dt_bank_left_reset")
            self.machine.events.post("master_technician_left_bank_reset")
            self.update_player_vars()
            self._update_saucer_guidance()

    def after_drop_hit(self):
        self.update_player_vars()
        self._update_saucer_guidance()

        # All eight physical drops must be down at once to complete the mode.
        if self.total_drops_down() >= 8:
            player = self.machine.game.player
            player["master_technician_state"] = 2
            self.machine.events.post("master_technician_mode_complete")
            return

        # Warn when only one target remains.
        if self.total_drops_down() == 7:
            self.machine.events.post("master_technician_danger_warning")

    def spinner_hit(self, **kwargs):
        value = self.calculate_spinner_value()
        self.award_score(value)

        player = self.machine.game.player
        player["master_technician_last_spinner_score"] = value

        self.machine.events.post("master_technician_spinner_scored")

    def total_drops_down(self):
        return len(self.left_down) + len(self.right_down)

    def calculate_multiplier(self):
        # Retained for the existing player variable/display contract.
        return self.total_drops_down() + 1

    def calculate_spinner_value(self):
        # 50K base plus 50K per down target, capped at 400K.
        return min(
            self.SPINNER_MAX,
            self.SPINNER_BASE + (self.SPINNER_PER_DROP * self.total_drops_down())
        )

    def _update_saucer_guidance(self):
        event = (
            "master_technician_light_saucers"
            if self.left_down
            else "master_technician_clear_saucers"
        )
        self.machine.events.post(event)

    def _update_mode_status(self):
        self.machine.events.post(
            "update_mode_status",
            mode_status_title="DROP TARGETS",
            mode_status_value=(
                f"{self.total_drops_down()}/8 DOWN  "
                f"SPIN {self.calculate_spinner_value():,}"
            ),
        )

    def update_player_vars(self):
        player = self.machine.game.player

        player["master_technician_left_drops_down"] = len(self.left_down)
        player["master_technician_right_drops_down"] = len(self.right_down)
        player["master_technician_multiplier"] = self.calculate_multiplier()
        player["master_technician_spinner_value"] = self.calculate_spinner_value()
        self._update_mode_status()

    def award_score(self, value):
        player = self.machine.game.player
        player["score"] += value
        player["active_mode_points"] = player["active_mode_points"] + value
