import random
from mpf.core.mode import Mode


class DailyBugleMystery(Mode):

    """
    Daily Bugle Scoop flow:

    1. Complete A+B.
    2. Rooftop gate opens.
    3. Enter rooftop.
    4. Exit rooftop right.
    5. Gate opens again.
    6. VUK collects Mystery.

    Progression:
    - 1st, 2nd, 3rd awards = placeholder mystery awards
    - 4th award = light Extra Ball
    - 10th award = award Extra Ball
    """

    EXTRA_BALL_LIGHT_AT = 4
    EXTRA_BALL_AWARD_AT = 10

    PLACEHOLDER_AWARDS = [
        "start_mystery_ball_save",
        "daily_bugle_award_placeholder_2",
        "daily_bugle_award_placeholder_3",
        "daily_bugle_award_placeholder_4",
        "daily_bugle_award_placeholder_5",
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.a_hit = False
        self.b_hit = False
        self.ab_ready = False
        self.rooftop_traversal_complete = False
        self.mystery_ready = False
        self.extra_ball_lit = False

        self.add_mode_event_handler("daily_bugle_a_hit", self.a_rollover_hit)
        self.add_mode_event_handler("daily_bugle_b_hit", self.b_rollover_hit)
        self.add_mode_event_handler("daily_bugle_rooftop_right_exit", self.rooftop_right_exit)
        self.add_mode_event_handler("daily_bugle_vuk_collect_request", self.vuk_collect_request)

        self.ensure_player_vars()

    def ensure_player_vars(self):
        player = self.machine.game.player

        if "daily_bugle_mystery_count" not in player:
            player["daily_bugle_mystery_count"] = 0

        if "daily_bugle_extra_balls_awarded" not in player:
            player["daily_bugle_extra_balls_awarded"] = 0

        self.update_player_vars()

    def a_rollover_hit(self, **kwargs):
        if self.a_hit == False:
            self.machine.events.post("daily_bugle_a_complete")
            self.a_hit = True
            self.check_ab_complete()

    def b_rollover_hit(self, **kwargs):
        if self.b_hit == False:
            self.machine.events.post("daily_bugle_b_complete")
            self.b_hit = True
            self.check_ab_complete()

    def check_ab_complete(self):
        if not self.a_hit or not self.b_hit:
            self.update_player_vars()
            return

        if self.ab_ready:
            self.update_player_vars()
            return

        self.ab_ready = True

        self.machine.events.post("daily_bugle_ab_ready")
        self.machine.events.post("rooftop_diverter_open")

        self.update_player_vars()

    def rooftop_right_exit(self, **kwargs):
        if not self.ab_ready:
            return

        self.rooftop_traversal_complete = True
        self.mystery_ready = True

        # Open gate again so player can shoot back toward VUK/mystery collect.
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("daily_bugle_rooftop_traversal_complete")

        self.update_player_vars()

    def vuk_collect_request(self, **kwargs):
        if not self.mystery_ready:
            return

        self.collect_mystery()

    def collect_mystery(self):
        player = self.machine.game.player

        player["daily_bugle_mystery_count"] += 1
        count = player["daily_bugle_mystery_count"]

        self.machine.events.post("daily_bugle_mystery_collected")

        if count == self.EXTRA_BALL_LIGHT_AT:
            self.light_extra_ball()
        elif count == self.EXTRA_BALL_AWARD_AT:
            self.award_extra_ball()
        else:
            self.award_placeholder_mystery()

        self.reset_cycle()
        self.update_player_vars()

    def award_placeholder_mystery(self):
        award_event = random.choice(self.PLACEHOLDER_AWARDS)
        self.machine.events.post(award_event)

    def light_extra_ball(self):
        self.extra_ball_lit = True

        # Hook this event to your real extra ball light/logic later.
        self.machine.events.post("daily_bugle_extra_ball_lit")

    def award_extra_ball(self):
        player = self.machine.game.player
        player["daily_bugle_extra_balls_awarded"] += 1

        # Hook this event to your real extra ball device/award later.
        self.machine.events.post("daily_bugle_extra_ball_awarded")

    def reset_cycle(self):
        self.a_hit = False
        self.b_hit = False
        self.ab_ready = False
        self.rooftop_traversal_complete = False
        self.mystery_ready = False

    def update_player_vars(self):
        player = self.machine.game.player

        player["daily_bugle_a_hit"] = int(self.a_hit)
        player["daily_bugle_b_hit"] = int(self.b_hit)
        player["daily_bugle_ab_ready"] = int(self.ab_ready)
        player["daily_bugle_rooftop_traversal_complete"] = int(self.rooftop_traversal_complete)
        player["daily_bugle_mystery_ready"] = int(self.mystery_ready)
        player["daily_bugle_extra_ball_lit"] = int(self.extra_ball_lit)