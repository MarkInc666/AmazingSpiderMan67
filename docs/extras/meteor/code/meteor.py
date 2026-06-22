from mpf.core.mode import Mode


class Meteor(Mode):

    DROP_SCORE = 25000
    SPINNER_BASE = 1000
    RIGHT_DROP_VALUE = 10000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.left_down = set()
        self.right_down = set()

        self.add_mode_event_handler("meteor_start", self.met_start)

        self.add_mode_event_handler("meteor_spinner_hit", self.spinner_hit)

        for target in range(1, 4):
            self.add_mode_event_handler(
                f"meteor_left_drop_{target}_hit",
                self.left_drop_hit,
                target=target
            )

        for target in range(1, 6):
            self.add_mode_event_handler(
                f"meteor_right_drop_{target}_hit",
                self.right_drop_hit,
                target=target
            )

    def met_start(self, **kwargs):
        self.update_player_vars()

    def left_drop_hit(self, target, **kwargs):
        if target in self.left_down:
            return

        self.left_down.add(target)
        self.award_score(self.DROP_SCORE)
        self.machine.events.post("meteor_drop_scored")
        self.after_drop_hit()

    def right_drop_hit(self, target, **kwargs):
        if target in self.right_down:
            return

        self.right_down.add(target)
        self.award_score(self.DROP_SCORE)
        self.machine.events.post("meteor_drop_scored")
        self.after_drop_hit()

    def after_drop_hit(self):
        self.update_player_vars()

        # If either bank completes, mode ends.
        if len(self.left_down) >= 3 or len(self.right_down) >= 5:
            player = self.machine.game.player
            player["meteor_completed"] = 1
            self.machine.events.post("meteor_mode_complete")
            return

        # Warning if either bank has only one target left.
        if len(self.left_down) == 2 or len(self.right_down) == 4:
            self.machine.events.post("meteor_danger_warning")

    def spinner_hit(self, **kwargs):
        value = self.calculate_spinner_value()
        self.award_score(value)

        player = self.machine.game.player
        player["meteor_last_spinner_score"] = value

        self.machine.events.post("meteor_spinner_scored")

    def calculate_multiplier(self):
        left_count = len(self.left_down)

        if left_count == 0:
            return 1
        if left_count == 1:
            return 2

        # 2 down = max multiplier.
        # 3 down ends the mode.
        return 5

    def calculate_spinner_value(self):
        multiplier = self.calculate_multiplier()
        right_count = len(self.right_down)

        value = right_count * self.RIGHT_DROP_VALUE * multiplier

        if value < self.SPINNER_BASE:
            return self.SPINNER_BASE

        return value

    def update_player_vars(self):
        player = self.machine.game.player

        player["meteor_left_drops_down"] = len(self.left_down)
        player["meteor_right_drops_down"] = len(self.right_down)
        player["meteor_multiplier"] = self.calculate_multiplier()
        player["meteor_spinner_value"] = self.calculate_spinner_value()

    def award_score(self, value):
        player = self.machine.game.player
        player["score"] += value
        player["meteor_mode_points"] = player["meteor_mode_points"] + value