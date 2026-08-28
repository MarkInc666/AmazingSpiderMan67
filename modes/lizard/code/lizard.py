from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
    "title": "THE LIZARD MAN",
    "intro_1": "Hit both pop bumpers to build the serum.",
    "intro_2": "Deliver it to Lizard Man at the left web target.",
    "intro_3": "Hit the red star during delivery to arm 10X.",
    "summary_title_complete": "LIZARD MAN CURED",
    "summary_title_failed": "LIZARD MAN ESCAPED",
    "stat_1_label": "DELIVERIES",
    "stat_1_var": "lizard_deliveries",
    "stat_2_label": "BEST VALUE",
    "stat_2_var": "active_mode_stat_2",
    "points_var": "active_mode_points",
    "state_var": "lizard_state",
"""


class Lizard(CaseFileMixin, Mode):

    BASE_DELIVERY_ATTEMPTS = 2
    MORE_JACKPOTS_DELIVERY_ATTEMPTS = 3

    TARGET_LIGHT_EVENTS = {
        "left": "lizard_light_left_web",
    }

    START_DELIVERY_VALUE = 1_000_000
    BIGGER_DELIVERY_VALUE = 1_500_000
    MINIMUM_DELIVERY_VALUE = 100_000
    SERUM_COLLECT_SCORE = 100_000
    DELIVERY_TICK_VALUE = 100_000
    MORE_TIME_TICK_VALUE = 50_000
    DELIVERY_SECONDS = 16
    MORE_TIME_SECONDS = 20
    AB_BONUS_VALUE = 500_000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self._init_player_vars()
        self.mode_done = False

        # Build each serum by hitting both pop bumpers once.
        self.add_mode_event_handler("s_pop_left_active", self.pop_hit, side="left")
        self.add_mode_event_handler("s_pop_right_active", self.pop_hit, side="right")

        # During delivery the red star is an optional 10X multiplier.
        self.add_mode_event_handler("s_star_rollover_active", self.star_multiplier_request)
        self.add_mode_event_handler("s_web_target_left_active", self.delivery_request, target="left")

        # A rollovers.
        self.add_mode_event_handler("s_inlane_a_active", self.a_rollover)
        self.add_mode_event_handler("s_inlane_m_r_active", self.a_rollover)

        # B rollovers. The left B can also substitute for the web with Shot Assist.
        self.add_mode_event_handler("s_inlane_b_active", self.b_rollover)
        self.add_mode_event_handler("s_inlane_m_l_active", self.b_rollover)
        self.add_mode_event_handler("s_inlane_m_l_active", self.delivery_request, target="shot_assist")

        # Main-playfield spinner only. The upper trispinner is intentionally excluded.
        self.add_mode_event_handler("s_web_spinner_active", self.delivery_request, target="shot_assist")

        # Both possible delivery timers feed the same logic.
        self.add_mode_event_handler("timer_lizard_delivery_timer_tick", self.delivery_timer_tick)
        self.add_mode_event_handler("timer_lizard_delivery_timer_complete", self.serum_expired)
        self.add_mode_event_handler("timer_lizard_delivery_timer_more_time_tick", self.delivery_timer_tick)
        self.add_mode_event_handler("timer_lizard_delivery_timer_more_time_complete", self.serum_expired)
        self.add_mode_event_handler("lizard_light_delivery_target", self.light_next_target)

        self.publish_case_file_bonus_events("lizard")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "THIRD SERUM DELIVERY ATTEMPT"),
            ("bigger_jackpots", "SERUM STARTS AT 1.5 MILLION"),
            ("more_time", "20 SECONDS AND SLOWER VALUE DECAY"),
            ("safety_net", "FIRST EXPIRED SERUM IS SAVED"),
            ("shot_assist", "MAIN SPINNER OR LEFT B DELIVERS SERUM"),
        ])

        # Lizard owns the gate for the full mode so the star remains reachable.
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("lizard_clear_ab")
        self._reset_serum_build_lights()
        self.machine.events.post("clear_saucers")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="BUILD THE SERUM",
            message_mode_subtitle="HIT BOTH POP BUMPERS",
        )
        self._update_status()

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self._stop_delivery_timers()
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        self.delivery_attempts = (
            self.MORE_JACKPOTS_DELIVERY_ATTEMPTS
            if self.has_case_file("more_jackpots")
            else self.BASE_DELIVERY_ATTEMPTS
        )
        self.start_delivery_value = (
            self.BIGGER_DELIVERY_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.START_DELIVERY_VALUE
        )
        self.delivery_tick_value = (
            self.MORE_TIME_TICK_VALUE
            if self.has_case_file("more_time")
            else self.DELIVERY_TICK_VALUE
        )
        self.delivery_seconds = (
            self.MORE_TIME_SECONDS
            if self.has_case_file("more_time")
            else self.DELIVERY_SECONDS
        )

    def _init_player_vars(self):
        player = self.machine.game.player
        player["lizard_serum_ready"] = 0
        player["lizard_deliveries"] = 0
        player["lizard_delivery_value"] = self.start_delivery_value
        player["lizard_a_hit"] = 0
        player["lizard_b_hit"] = 0
        player["lizard_ab_ready"] = 0
        self.best_delivery_value = 0
        self.deliveries_made = 0
        player["active_mode_stat_1"] = self.deliveries_made
        player["active_mode_stat_2"] = self.best_delivery_value

        self._safety_net_used = False
        self._delivery_completes_mode = False
        self._serum_expiration_pending = False
        self._delivery_success_pending = False
        self._left_pop_hit = False
        self._right_pop_hit = False
        self._star_10x_armed = False

        player["active_mode_points"] = 0
        player["lizard_state"] = 1

    def _award_points(self, points):
        player = self.machine.game.player
        points = int(points)
        player["score"] += points
        player["active_mode_points"] += points

    def _update_status(self):
        if self.mode_done:
            return
        player = self.machine.game.player
        if player["lizard_serum_ready"] == 1:
            title = f"DELIVERY {int(player['lizard_delivery_value']):,}"
            value = "10X ARMED" if self._star_10x_armed else "STAR 10X READY"
        else:
            title = "BUILD THE SERUM"
            if self._left_pop_hit and not self._right_pop_hit:
                value = "RIGHT POP NEEDED"
            elif self._right_pop_hit and not self._left_pop_hit:
                value = "LEFT POP NEEDED"
            else:
                value = "HIT BOTH POP BUMPERS"
        self.machine.events.post("show_mode_status", mode_status_title=title, mode_status_value=value)

    def current_target(self):
        deliveries = self.machine.game.player["lizard_deliveries"]
        if deliveries >= self.delivery_attempts:
            return None
        return "left"

    def a_rollover(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] is True:
            return
        self.machine.game.player["lizard_a_hit"] = 1
        self.machine.events.post("lizard_a_complete")
        if self.machine.game.player["lizard_b_hit"] == 1:
            self._ab_complete()

    def b_rollover(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] is True:
            return
        self.machine.game.player["lizard_b_hit"] = 1
        self.machine.events.post("lizard_b_complete")
        if self.machine.game.player["lizard_a_hit"] == 1:
            self._ab_complete()

    def _ab_complete(self):
        """Permanently boost this mode's current and future serum values."""
        player = self.machine.game.player
        player["lizard_ab_ready"] = 1
        self.start_delivery_value += self.AB_BONUS_VALUE
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="A+B BOOST!",
            message_mode_subtitle="ALL SERUM VALUES UP",
            message_mode_value=self.AB_BONUS_VALUE,
        )
        self.machine.events.post("lizard_ab_complete")

        if player["lizard_serum_ready"] == 1:
            player["lizard_delivery_value"] += self.AB_BONUS_VALUE
            self._start_delivery_timer()
            self.machine.events.post("lizard_ab_timer_restarted")
        else:
            player["lizard_delivery_value"] = self.start_delivery_value

        player["lizard_a_hit"] = 0
        player["lizard_b_hit"] = 0
        player["lizard_ab_ready"] = 0
        self.machine.events.post("lizard_clear_ab")

    def _reset_serum_build_lights(self):
        self._left_pop_hit = False
        self._right_pop_hit = False
        self._star_10x_armed = False
        self.machine.events.post("lizard_pop_left_available")
        self.machine.events.post("lizard_pop_right_available")
        self.machine.events.post("lizard_star_10x_stop")
        self.machine.events.post("lizard_light_serum_location")

    def pop_hit(self, side=None, **kwargs):
        if self.mode_done or self.machine.game.player["villain_mode_in_summary"] is True:
            return
        if self._serum_expiration_pending or self._delivery_success_pending:
            return

        player = self.machine.game.player
        if player["lizard_serum_ready"] == 1:
            return
        if player["lizard_deliveries"] >= self.delivery_attempts:
            return

        if side == "left":
            if self._left_pop_hit:
                return
            self._left_pop_hit = True
            self.machine.events.post("lizard_pop_left_collected")
        elif side == "right":
            if self._right_pop_hit:
                return
            self._right_pop_hit = True
            self.machine.events.post("lizard_pop_right_collected")
        else:
            return

        if not (self._left_pop_hit and self._right_pop_hit):
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="SERUM COMPONENT FOUND",
                message_mode_subtitle="HIT THE OTHER POP",
            )
            self._update_status()
            return

        self._serum_ready_from_pops()

    def _serum_ready_from_pops(self):
        player = self.machine.game.player
        player["lizard_delivery_value"] = self.start_delivery_value
        self._award_points(self.SERUM_COLLECT_SCORE)
        player["lizard_serum_ready"] = 1
        self._star_10x_armed = False

        subtitle = "LEFT WEB / SPINNER / LEFT B" if self.has_case_file("shot_assist") else "DELIVER TO LEFT WEB"
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title="SERUM READY",
            message_mode_subtitle=subtitle,
            message_mode_value=player["lizard_delivery_value"],
            message_mode_seconds=self.delivery_seconds,
        )
        self.machine.events.post("lizard_serum_collected")
        self.machine.events.post("lizard_light_delivery_target")
        self.machine.events.post("lizard_star_10x_available")
        self._start_delivery_timer()
        self._update_status()

    def star_multiplier_request(self, **kwargs):
        if self.mode_done or self.machine.game.player["villain_mode_in_summary"] is True:
            return
        if self.machine.game.player["lizard_serum_ready"] == 0 or self._star_10x_armed:
            return
        self._star_10x_armed = True
        self.machine.events.post("lizard_star_10x_armed")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="10X DELIVERY ARMED",
            message_mode_subtitle="DELIVER TO LEFT WEB",
        )
        self._update_status()

    def _start_delivery_timer(self):
        self._stop_delivery_timers()
        event = (
            "lizard_delivery_timer_more_time_start"
            if self.has_case_file("more_time")
            else "lizard_delivery_timer_start"
        )
        self.machine.events.post(event)

    def _stop_delivery_timers(self):
        self.machine.events.post("lizard_delivery_timer_stop")
        self.machine.events.post("lizard_delivery_timer_more_time_stop")

    def delivery_timer_tick(self, ticks=None, **kwargs):
        if self.mode_done or self.machine.game.player["lizard_serum_ready"] == 0:
            return
        if ticks is None:
            return

        player = self.machine.game.player
        player["lizard_delivery_value"] = max(
            self.MINIMUM_DELIVERY_VALUE,
            player["lizard_delivery_value"] - self.delivery_tick_value,
        )
        multiplier_status = "10X ARMED" if self._star_10x_armed else "STAR 10X READY"
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=f"DELIVERY {int(player['lizard_delivery_value']):,}",
            mode_status_value=f"{multiplier_status} - {int(ticks)}s",
        )
        self.machine.events.post("lizard_delivery_tick")

    def serum_expired(self, **kwargs):
        if self.mode_done:
            return

        player = self.machine.game.player
        self._stop_delivery_timers()
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("lizard_serum_expired_show")
        self._serum_expiration_pending = True
        player["lizard_serum_ready"] = 0
        player["lizard_delivery_value"] = self.start_delivery_value
        self._star_10x_armed = False
        self.machine.events.post("lizard_star_10x_stop")

        if self.has_case_file("safety_net") and not self._safety_net_used:
            self._safety_net_used = True
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="SAFETY NET",
                message_mode_subtitle="SERUM SAVED - TRY AGAIN",
            )
            self.machine.events.post("lizard_safety_net_used")
            self._schedule_serum_expiration_resolution(complete_mode=False)
            return

        self.machine.events.post(
            "show_mode_message",
            message_mode_title="SERUM EXPIRED",
            message_mode_subtitle="DELIVERY ATTEMPT LOST",
        )
        self.machine.events.post("lizard_serum_expired")

        player["lizard_deliveries"] += 1
        self._schedule_serum_expiration_resolution(
            complete_mode=player["lizard_deliveries"] >= self.delivery_attempts
        )

    def _schedule_serum_expiration_resolution(self, complete_mode):
        """Let the expired-serum GI fade finish before advancing the mode."""
        self.delay.remove("lizard_serum_expire_resolve")
        self.delay.add(
            name="lizard_serum_expire_resolve",
            ms=2000,
            callback=self._finish_serum_expiration,
            complete_mode=complete_mode,
        )

    def _finish_serum_expiration(self, complete_mode=False, **kwargs):
        if self.mode_done:
            return
        self._serum_expiration_pending = False
        if complete_mode:
            self._complete_mode()
            return
        self._reset_serum_build_lights()
        self._update_status()

    def delivery_request(self, target=None, **kwargs):
        if self.mode_done or self.machine.game.player["villain_mode_in_summary"] is True:
            return

        player = self.machine.game.player
        if player["lizard_serum_ready"] == 0:
            return

        used_shot_assist = target == "shot_assist"
        if used_shot_assist and not self.has_case_file("shot_assist"):
            return
        if not used_shot_assist and target != "left":
            return

        player["lizard_serum_ready"] = 0
        base_delivery_value = max(self.MINIMUM_DELIVERY_VALUE, player["lizard_delivery_value"])
        delivery_value = base_delivery_value * (10 if self._star_10x_armed else 1)
        self._award_points(delivery_value)
        self.machine.events.post("lizard_star_10x_stop")

        self.best_delivery_value = max(self.best_delivery_value, delivery_value)
        self.deliveries_made += 1
        player["active_mode_stat_1"] = self.deliveries_made
        player["active_mode_stat_2"] = self.best_delivery_value

        player["lizard_deliveries"] += 1
        player["lizard_state"] = 2
        player["lizard_delivery_value"] = self.start_delivery_value
        used_10x = self._star_10x_armed
        self._star_10x_armed = False

        subtitle = "SHOT ASSIST" if used_shot_assist else "LEFT WEB"
        if used_10x:
            subtitle = f"{subtitle} - 10X"
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SERUM DELIVERED",
            message_mode_subtitle=subtitle,
            message_mode_value=delivery_value,
        )
        self.machine.events.post("lizard_serum_delivered")
        self.machine.events.post("play_mode_jackpot")
        self._stop_delivery_timers()
        self.machine.events.post("hide_mode_status")

        self._delivery_completes_mode = player["lizard_deliveries"] >= self.delivery_attempts
        self._delivery_success_pending = True
        self.delay.remove("lizard_delivery_success_resolve")
        self.delay.add(
            name="lizard_delivery_success_resolve",
            ms=2000,
            callback=self._finish_delivery_success,
            delivery_value=delivery_value,
        )

    def _finish_delivery_success(self, delivery_value=0, **kwargs):
        if self.mode_done:
            return
        self._delivery_success_pending = False
        if self._delivery_completes_mode:
            self._complete_mode()
            return
        self._reset_serum_build_lights()
        self._update_status()
        self._prompt_next_serum()

    def _prompt_next_serum(self):
        player = self.machine.game.player
        if (
            self.mode_done
            or player["villain_mode_in_summary"] is True
            or player["lizard_deliveries"] >= self.delivery_attempts
        ):
            return
        self.machine.events.post("lizard_more_serum_needed")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="BUILD ANOTHER SERUM",
            message_mode_subtitle="HIT BOTH POP BUMPERS",
            reminder=True,
        )

    def _complete_mode(self):
        self.mode_done = True
        self._stop_delivery_timers()
        self.machine.events.post("lizard_star_10x_stop")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="LIZARD CURED",
            message_mode_subtitle="MODE COMPLETE",
        )
        self.machine.events.post("lizard_mode_complete")

    def light_next_target(self, **kwargs):
        if self.current_target():
            self._light_target("left")

    def _light_target(self, target):
        event = self.TARGET_LIGHT_EVENTS.get(target)
        if event:
            self.machine.events.post(event)
