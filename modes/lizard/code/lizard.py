from mpf.core.mode import Mode

"""
    "title": "THE LIZARD MAN",
    "intro_1": "Create the antidote at the star rollover.",
    "intro_2": "Get it to Lizard Man at the lit web targets.",
    "intro_3": "Move fast before the value drains.",
    "summary_title_complete": "LIZARD MAN CURED",
    "summary_title_failed": "LIZARD MAN ESCAPED",
    "stat_1_label": "DELIVERIES",
    "stat_1_var": "lizard_deliveries",
    "stat_2_label": "BEST VALUE",
    "stat_2_var": "lizard_best_delivery_value",
    "points_var": "lizard_mode_points",
    "completed_var": "lizard_completed",
"""
class Lizard(Mode):

    DELIVERY_SEQUENCE = [
        "left",
        "center",
#        "left",
#        "center",
    ]

    TARGET_LIGHT_EVENTS = {
        "left": "lizard_light_left_web",
        "center": "lizard_light_center_web",
    }

    START_DELIVERY_VALUE = 1000000
    SERUM_COLLECT_SCORE = 100000
    DELIVERY_TICK_VALUE = 100000
    AB_BONUS_VALUE = 500000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self._init_player_vars()

        # Switch/event handlers.
        self.add_mode_event_handler("s_star_rollover_active", self.serum_collect_request)
        self.add_mode_event_handler("s_web_target_left_active", self.delivery_request, target="left")
        self.add_mode_event_handler("s_web_target_top_active", self.delivery_request, target="center")

        # A rollovers.
        self.add_mode_event_handler("s_inlane_a_active", self.a_rollover)
        self.add_mode_event_handler("s_inlane_m_r_active", self.a_rollover)

        # B rollovers.
        self.add_mode_event_handler("s_inlane_b_active", self.b_rollover)
        self.add_mode_event_handler("s_inlane_m_l_active", self.b_rollover)

        # Timer/control events.
        self.add_mode_event_handler("timer_lizard_delivery_timer_tick", self.delivery_timer_tick)
        self.add_mode_event_handler("timer_lizard_delivery_timer_complete", self.serum_expired)
        self.add_mode_event_handler("lizard_light_delivery_target", self.light_next_target)

        # Startup actions formerly handled by event_player/variable_player.
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("lizard_light_serum_location")
        self.machine.events.post("clear_saucers")
#        self.machine.events.post("play_song_4")

    def _player(self):
        if not self.machine.game:
            return None
        return self.machine.game.player

    def _get_player_var(self, name, default=0):
        player = self._player()
        if not player:
            return default
        try:
            return player[name]
        except KeyError:
            return default

    def _set_player_var(self, name, value):
        player = self._player()
        if not player:
            return
        player[name] = value

    def _add_player_var(self, name, value):
        self._set_player_var(name, self._get_player_var(name, 0) + value)

    def _award_points(self, points):
        points = int(points)
        self._add_player_var("score", points)
        self._add_player_var("lizard_mode_points", points)

    def _init_player_vars(self):
        self._set_player_var("lizard_serum_ready", 0)
        self._set_player_var("lizard_deliveries", 0)
        self._set_player_var("lizard_delivery_value", self.START_DELIVERY_VALUE)
        self._set_player_var("lizard_a_hit", 0)
        self._set_player_var("lizard_b_hit", 0)
        self._set_player_var("lizard_ab_ready", 0)

        # Vars used by the generic villain summary/bookend screen.
        self._set_player_var("lizard_mode_points", 0)
        self._set_player_var("lizard_best_delivery_value", 0)
        self._set_player_var("lizard_deliveries_made", 0)
        self._set_player_var("lizard_completed", 0)

    def current_target(self):
        deliveries = self._get_player_var("lizard_deliveries", 0)

        if deliveries >= len(self.DELIVERY_SEQUENCE):
            return None

        return self.DELIVERY_SEQUENCE[deliveries]

    def a_rollover(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return

        self._set_player_var("lizard_a_hit", 1)
        self.machine.events.post("lizard_a_complete")

        if self._get_player_var("lizard_b_hit", 0) == 1:
            self._ab_complete()

    def b_rollover(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return

        self._set_player_var("lizard_b_hit", 1)
        self.machine.events.post("lizard_b_complete")

        if self._get_player_var("lizard_a_hit", 0) == 1:
            self._ab_complete()

    def _ab_complete(self):
        """Completing A+B gives the player a short helper/reset during Lizard."""
        self._set_player_var("lizard_ab_ready", 1)
        self.machine.events.post("lizard_ab_complete")

        # Existing YAML comment said A+B should reset the delivery timer.
        self.machine.events.post("lizard_delivery_timer_start")

        # Keep this bonus in Python now. It was present in YAML as lizard_apply_ab_bonus.
        self._add_player_var("lizard_delivery_value", self.AB_BONUS_VALUE)

        # Reset A/B state so the combo can be earned again.
        self._set_player_var("lizard_a_hit", 0)
        self._set_player_var("lizard_b_hit", 0)
        self._set_player_var("lizard_ab_ready", 0)
        self.machine.events.post("lizard_clear_ab")

    def serum_collect_request(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return

        if self._get_player_var("lizard_serum_ready", 0) == 1:
            return

        self._award_points(self.SERUM_COLLECT_SCORE)
        self._set_player_var("lizard_serum_ready", 1)

        self.machine.events.post("lizard_serum_collected")
        self.machine.events.post("lizard_light_delivery_target")
        self.machine.events.post("lizard_delivery_timer_start")

    def delivery_timer_tick(self, ticks=None, **kwargs):
        """Drain value only during the original 10-to-3 tick window."""
        if ticks is None:
            # Some MPF timer events may not pass ticks; fall back to the device.
            try:
                ticks = self.machine.timers["lizard_delivery_timer"].ticks
            except Exception:
                return

        if 3 <= int(ticks) <= 10:
            current_value = self._get_player_var("lizard_delivery_value", self.START_DELIVERY_VALUE)
            self._set_player_var(
                "lizard_delivery_value",
                max(0, current_value - self.DELIVERY_TICK_VALUE),
            )
            self.machine.events.post("lizard_delivery_tick")


    def serum_expired(self, **kwargs):
        # Public event for shows/widgets/sounds.
        self.machine.events.post("lizard_serum_expired")

        # Stop the active delivery timer and delivery-target lights.
        self.machine.events.post("lizard_delivery_timer_stop")
        self.machine.events.post("lizard_serum_expired_show")

        # This delivery attempt is now spent, even though no points were awarded.
        self._add_player_var("lizard_deliveries", 1)

        # Reset serum state for the next attempt.
        self._set_player_var("lizard_serum_ready", 0)
        self._set_player_var("lizard_delivery_value", self.START_DELIVERY_VALUE)

        # If all attempts are used, end the mode.
        if self._get_player_var("lizard_deliveries", 0) >= len(self.DELIVERY_SEQUENCE):
            self.machine.events.post("lizard_mode_failed")
            return

        # Otherwise light the star again for the next serum collect.
        self.machine.events.post("lizard_light_serum_location")

    def delivery_request(self, target=None, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return

        if self._get_player_var("lizard_serum_ready", 0) == 0:
            return

        required_target = self.current_target()

        if required_target != target:
            return

        delivery_value = self._get_player_var("lizard_delivery_value", self.START_DELIVERY_VALUE)
        self._award_points(delivery_value)

        if delivery_value > self._get_player_var("lizard_best_delivery_value", 0):
            self._set_player_var("lizard_best_delivery_value", delivery_value)

        self._add_player_var("lizard_deliveries", 1)
        self._add_player_var("lizard_deliveries_made", 1)
        #successful if just one delivery made
        self._set_player_var("lizard_completed", 1) 
        self._set_player_var("lizard_serum_ready", 0)
        self._set_player_var("lizard_delivery_value", self.START_DELIVERY_VALUE)

        self.machine.events.post("lizard_serum_delivered")
        self.machine.events.post("lizard_delivery_timer_stop")

        if self._get_player_var("lizard_deliveries", 0) >= len(self.DELIVERY_SEQUENCE):
            self.machine.events.post("lizard_mode_complete")
            return

        self.machine.events.post("lizard_light_serum_location")

    def light_next_target(self, **kwargs):
        target = self.current_target()

        if not target:
            return

        event = self.TARGET_LIGHT_EVENTS.get(target)

        if event:
            self.machine.events.post(event)
