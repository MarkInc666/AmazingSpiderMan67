import random
from mpf.core.mode import Mode


class DailyBugleMystery(Mode):
    """Daily Bugle Mystery / Scoop mode.

    Flow:
      1. Complete A+B.
      2. Rooftop gate opens.
      3. Enter rooftop.
      4. Exit rooftop right.
      5. Gate opens again.
      6. VUK collects Mystery.

    Important change from the older version:
      A/B/mystery progress is restored from player vars when the mode starts,
      so the state can survive ball drains.
    """

    AB_DAILY_POINTS = 10000
    AB_DAILY_POINTS_UNLIT = 2000

    EXTRA_BALL_LIGHT_AT = 3
    EXTRA_BALL_AWARD_AT = 7
    EXTRA_BALL_RIGHT_LIGHT_AT = 10

    PLACEHOLDER_AWARDS = [
        "mystery_award_ball_save",
        "mystery_award_start_super_spinner",
        "mystery_award_advance_bonus_multiplier",
        "mystery_award_collect_bonus",
        "mystery_award_hold_bonus",
        "mystery_award_start_super_pops",
        "mystery_award_million_points",
        "mystery_award_villain_start_ready",
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.daily_bugle_enabled = True

        self._ensure_player_vars()
        self._restore_runtime_state_from_player()
        self._add_handlers()
        self._restore_lights_and_widgets()

    def mode_stop(self, **kwargs):
        self.daily_bugle_enabled = False
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("daily_bugle_a_hit", self.a_rollover_hit)
        self.add_mode_event_handler("daily_bugle_b_hit", self.b_rollover_hit)
        self.add_mode_event_handler("daily_bugle_rooftop_right_exit", self.rooftop_right_exit)
        self.add_mode_event_handler("daily_bugle_vuk_collect_request", self.vuk_collect_request)

        self.add_mode_event_handler("disable_daily_bugle_mystery", self.disable_db)
        self.add_mode_event_handler("enable_daily_bugle_mystery", self.enable_db)
        self.add_mode_event_handler("reset_daily_bugle_state", self.reset_cycle)
        self.add_mode_event_handler("daily_bugle_restore_state", self._restore_lights_and_widgets)

    def _ensure_player_vars(self):
        player = self.machine.game.player

        defaults = {
            "daily_bugle_mystery_count": 0,
            "daily_bugle_extra_balls_awarded": 0,

            # These are the persistent A/B/mystery state vars.
            "daily_bugle_a_hit": 0,
            "daily_bugle_b_hit": 0,
            "daily_bugle_ab_ready": 0,
            "daily_bugle_mystery_ready": 0,
        }

        for name, value in defaults.items():
            if name not in player:
                player[name] = value

    def _restore_runtime_state_from_player(self):
        player = self.machine.game.player

        self.a_hit = bool(player["daily_bugle_a_hit"])
        self.b_hit = bool(player["daily_bugle_b_hit"])
        self.mystery_ab_ready = bool(player["daily_bugle_ab_ready"])
        self.mystery_ready = bool(player["daily_bugle_mystery_ready"])

    def disable_db(self, **kwargs):
        self.daily_bugle_enabled = False
        self.reset_cycle(post_restore=False)
        self.machine.events.post("daily_bugle_mystery_stop_all")
        self.update_player_vars()
        self._restore_lights_and_widgets()

    def enable_db(self, **kwargs):
        self.daily_bugle_enabled = True
        self._restore_lights_and_widgets()

    def a_rollover_hit(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        player = self.machine.game.player

        if not self.a_hit:
            player["score"] += self.AB_DAILY_POINTS
            self.a_hit = True
            self.update_player_vars(post_widget_update=False)
            self.machine.events.post("daily_bugle_a_complete")
            self.check_ab_complete()
        else:
            player["score"] += self.AB_DAILY_POINTS_UNLIT
            self.machine.events.post("ab_rolledover_sfx")
            self.update_player_vars()

    def b_rollover_hit(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        player = self.machine.game.player

        if not self.b_hit:
            player["score"] += self.AB_DAILY_POINTS
            self.b_hit = True
            self.update_player_vars(post_widget_update=False)
            self.machine.events.post("daily_bugle_b_complete")
            self.check_ab_complete()
        else:
            player["score"] += self.AB_DAILY_POINTS_UNLIT
            self.machine.events.post("ab_rolledover_sfx")
            self.update_player_vars()

    def check_ab_complete(self):
        if not self.a_hit or not self.b_hit:
            self.update_player_vars()
            return

        if self.mystery_ab_ready:
            self.update_player_vars()
            return

        self.mystery_ab_ready = True
        self.update_player_vars(post_widget_update=False)

        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("daily_bugle_ab_complete")
        self.machine.events.post("daily_bugle_widget_update")

    def rooftop_right_exit(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        if not self.mystery_ab_ready:
            return

        if not self.mystery_ready:
            self.mystery_ready = True
            self.update_player_vars(post_widget_update=False)
            self.machine.events.post("daily_bugle_mystery_ready")
        else:
            self.update_player_vars(post_widget_update=False)

        # Open gate again so player can shoot back toward VUK/mystery collect.
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("daily_bugle_widget_update")

    def vuk_collect_request(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        if not self.mystery_ready:
            # VUK was hit but mystery is not ready. Kick up quickly for other uses.
            self.delay.add(
                name="daily_bugle_vuk_delay_eject",
                ms=500,
                callback=self.fire_vuk,
            )
            return

        # Mystery is ready. Hold briefly, award, then eject.
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
        elif count == self.EXTRA_BALL_RIGHT_LIGHT_AT:
            self.light_right_extra_ball()
        else:
            self.award_pseudo_random_mystery()

        self.reset_cycle(post_restore=False)
        self.update_player_vars()

        self.delay.add(
            name="daily_bugle_vuk_delay_eject",
            ms=5000,
            callback=self.fire_vuk,
        )
        self.machine.events.post("rooftop_diverter_close")


    def award_pseudo_random_mystery(self):
        player = self.machine.game.player
        valid_awards = list(self.PLACEHOLDER_AWARDS)

        # Try a handful of times to avoid awards that are not currently useful.
        for _ in range(20):
            award_event = random.choice(valid_awards)

            if award_event == "mystery_award_villain_start_ready":
                villain_mode_running = player["villain_mode_running"]
                villain_start_ready = player["villain_start_ready"]
                if villain_mode_running == 0 and villain_start_ready == 0:
                    self.machine.events.post(award_event)
                    return

            elif award_event == "mystery_award_hold_bonus":
                hold_bonus = player["hold_bonus"]
                if hold_bonus == 0:
                    self.machine.events.post(award_event)
                    return

            else:
                self.machine.events.post(award_event)
                return

        # Safe fallback if every random choice was filtered out.
        self.machine.events.post("mystery_award_million_points")

    def fire_vuk(self):
        self.machine.events.post("up_kick")

    def light_extra_ball(self):
        self.machine.events.post("mystery_award_light_extra_ball")

    def light_right_extra_ball(self):
        self.machine.events.post("mystery_award_light_right_extra_ball")

    def award_extra_ball(self):
        self.machine.events.post("mystery_award_award_extra_ball")

    def reset_cycle(self, post_restore=True, **kwargs):
        self.a_hit = False
        self.b_hit = False
        self.mystery_ab_ready = False
        self.mystery_ready = False
        self.update_player_vars()

        if post_restore:
            self._restore_lights_and_widgets()

    def update_player_vars(self, post_widget_update=True):
        player = self.machine.game.player

        player["daily_bugle_a_hit"] = int(self.a_hit)
        player["daily_bugle_b_hit"] = int(self.b_hit)
        player["daily_bugle_ab_ready"] = int(self.mystery_ab_ready)
        player["daily_bugle_mystery_ready"] = int(self.mystery_ready)

        if post_widget_update:
            self.machine.events.post("daily_bugle_widget_update")

    def _restore_lights_and_widgets(self, **kwargs):
        """Restore visuals from state without replaying hit animations."""

        self.machine.events.post("daily_bugle_mystery_stop_all")

        if self.mystery_ready:
            self.machine.events.post("daily_bugle_restore_mystery_ready")
        elif self.mystery_ab_ready:
            self.machine.events.post("daily_bugle_restore_ab_ready")
        else:
            if self.a_hit:
                self.machine.events.post("daily_bugle_a_restore_complete")
            else:
                self.machine.events.post("daily_bugle_a_restore_incomplete")

            if self.b_hit:
                self.machine.events.post("daily_bugle_b_restore_complete")
            else:
                self.machine.events.post("daily_bugle_b_restore_incomplete")

        self.machine.events.post("daily_bugle_widget_update")
