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

    # Mystery Awards Ideas
    + light extra ball (at 3)
    + extra ball (at 10)
    + ball save (20s)
    + super spinners 20s
    + collect bonus
    + bonus X
    + hold bonus
    + villain qualify  ?
    + mystery multiball  ?

    """

    EXTRA_BALL_LIGHT_AT = 4
    EXTRA_BALL_AWARD_AT = 10

    PLACEHOLDER_AWARDS = [
#        "mystery_award_ball_save",
        "mystery_award_start_super_spinner",
#        "mystery_award_advance_bonus_multiplier",
#        "mystery_award_collect_bonus",
#        "mystery_award_hold_bonus",
        "mystery_award_start_super_pops",
 #       "mystery_award_million_points",        
 #       "mystery_award_villain_start_ready",
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.a_hit = False
        self.b_hit = False
        self.machine.game.player["mystery_ab_ready"] = False
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

        if self.machine.game.player["mystery_ab_ready"]:
            self.update_player_vars()
            return

        self.machine.game.player["mystery_ab_ready"] = True

        self.machine.events.post("rooftop_diverter_open")

        self.update_player_vars()

    def rooftop_right_exit(self, **kwargs):
        if not self.machine.game.player["mystery_ab_ready"]:
            return

        self.rooftop_traversal_complete = True
        self.mystery_ready = True

        # Open gate again so player can shoot back toward VUK/mystery collect.
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("daily_bugle_rooftop_traversal_complete")

        self.update_player_vars()

    def vuk_collect_request(self, **kwargs):

        if not self.mystery_ready:
            # kick up for all others
            self.delay.add(
                name=f"vuk_delay_eject",
                ms=500,
                callback=self.fire_VUK
            )
            return
        
        #second time, collect and wait 
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
            self.award_psuedo_random_mystery()

        self.reset_cycle()
        self.update_player_vars()

    def award_psuedo_random_mystery(self):
        valid = False

        while not valid:
            award_event = random.choice(self.PLACEHOLDER_AWARDS)
            if award_event == "mystery_award_villain_start_ready":
                if (
                    self.machine.game.player.villain_mode_running == 0
                    and self.machine.game.player.villain_start_ready == 0
                ):
                    valid = True
            elif award_event == "mystery_award_hold_bonus":
                if self.machine.game.player.hold_bonus == 0:
                    valid = True
            else:
                valid = True

        self.machine.events.post(award_event)
        self.delay.add(
            name=f"vuk_delay_eject",
            ms=8000,
            callback=self.fire_VUK
        )

    def fire_VUK(self):
        self.machine.events.post("up_kick")

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
        self.machine.game.player["mystery_ab_ready"] = False
        self.rooftop_traversal_complete = False
        self.mystery_ready = False

    def update_player_vars(self):
        player = self.machine.game.player

        player["daily_bugle_a_hit"] = int(self.a_hit)
        player["daily_bugle_b_hit"] = int(self.b_hit)
        player["daily_bugle_rooftop_traversal_complete"] = int(self.rooftop_traversal_complete)
        player["daily_bugle_mystery_ready"] = int(self.mystery_ready)
        player["daily_bugle_extra_ball_lit"] = int(self.extra_ball_lit)