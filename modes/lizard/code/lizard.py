from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

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
    "points_var": "active_mode_points",
    "state_var": "lizard_state",
"""
class Lizard(CaseFileMixin, Mode):

    DELIVERY_SEQUENCE = [
        "left",
        "center",
    ]

    TARGET_LIGHT_EVENTS = {
        "left": "lizard_light_left_web",
        "center": "lizard_light_center_web",
    }

    OPPOSITE_TARGET = {
        "left": "center",
        "center": "left",
    }

    START_DELIVERY_VALUE = 1000000
    SERUM_COLLECT_SCORE = 100000
    DELIVERY_TICK_VALUE = 100000
    AB_BONUS_VALUE = 500000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self._init_player_vars()
        self.mode_done = False

        # Switch/event handlers.
        self.add_mode_event_handler("s_star_rollover_active", self.serum_collect_request)
        self.add_mode_event_handler("s_web_target_left_active", self.delivery_request, target="left")
        self.add_mode_event_handler("s_web_target_mid_active", self.delivery_request, target="center")

        # A rollovers.
        self.add_mode_event_handler("s_inlane_a_active", self.a_rollover)
        self.add_mode_event_handler("s_inlane_m_r_active", self.a_rollover)

        # B rollovers.
        self.add_mode_event_handler("s_inlane_b_active", self.b_rollover)
        self.add_mode_event_handler("s_inlane_m_l_active", self.b_rollover)

        # Timer/control events.
        self.add_mode_event_handler("timer_lizard_delivery_timer_tick", self.delivery_timer_tick)
        self.add_mode_event_handler("timer_lizard_delivery_timer_complete", self.serum_expired)
        self.add_mode_event_handler("timer_lizard_followup_timer_complete", self.followup_expired)
        self.add_mode_event_handler("lizard_light_delivery_target", self.light_next_target)

        self.publish_case_file_bonus_events("lizard")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "FOLLOW-UP JACKPOTS AFTER DELIVERIES"),
            ("bigger_jackpots", "SERUM VALUE BOOSTED"),
            ("more_time", "SERUM VALUE DECAY SLOWED"),
            ("safety_net", "FIRST EXPIRED SERUM IS SAVED"),
            ("shot_assist", "FIRST DELIVERY CAN HIT EITHER WEB"),
        ])

        # Startup actions formerly handled by event_player/variable_player.
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("lizard_light_serum_location")
        self.machine.events.post("clear_saucers")
        self._show_message("COLLECT SERUM", "HIT THE STAR ROLLOVER")
        self._update_status()
#        self.machine.events.post("play_song_4")

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("lizard_delivery_timer_stop")
        self.machine.events.post("lizard_followup_timer_stop")
        self.machine.events.post("lizard_followup_cleanup")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _show_message(self, title, subtitle="", value="", seconds="", event="show_mode_message"):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
        )

    def _update_status(self):
        if self.mode_done:
            return
        player = self.machine.game.player
        deliveries = player["lizard_deliveries"]
        if player["lizard_followup_ready"] == 1:
            title = "FOLLOW-UP WEB"
            value = (self._followup_target or "WEB").upper()
        elif player["lizard_serum_ready"] == 1:
            title = "DELIVER SERUM"
            value = (self.current_target() or "WEB").upper()
        else:
            title = "COLLECT SERUM"
            value = f"STAR  {deliveries} OF {len(self.DELIVERY_SEQUENCE)}"
        self.machine.events.post("show_mode_status", mode_status_title=title, mode_status_value=value)

    def _apply_case_file_bonuses(self):
        self.START_DELIVERY_VALUE = type(self).START_DELIVERY_VALUE
        self.DELIVERY_TICK_VALUE = type(self).DELIVERY_TICK_VALUE

        if self.has_case_file("bigger_jackpots"):
            self.START_DELIVERY_VALUE += 250000

        if self.has_case_file("more_time"):
            self.DELIVERY_TICK_VALUE = max(25000, int(self.DELIVERY_TICK_VALUE / 2))

        # More Jackpots, Safety Net, and Shot Assist are handled in the
        # delivery/expiration flow so they enhance the mode instead of
        # skipping or lengthening the core serum loop.

    def _award_points(self, points):
        player = self.machine.game.player
        points = int(points)
        player["score"] += points
        player["active_mode_points"] += points

    def _init_player_vars(self):
        player = self.machine.game.player
        player["lizard_serum_ready"] = 0
        player["lizard_deliveries"] = 0
        player["lizard_delivery_value"] = self.START_DELIVERY_VALUE
        player["lizard_a_hit"] = 0
        player["lizard_b_hit"] = 0
        player["lizard_ab_ready"] = 0
        player["lizard_followup_ready"] = 0

        self._safety_net_used = False
        self._shot_assist_used = False
        self._followup_target = None
        self._followup_value = 0
        self._pending_completion_after_followup = False

        # Vars used by the generic villain summary/bookend screen.
        player["active_mode_points"] = 0
        player["lizard_best_delivery_value"] = 0
        player["lizard_deliveries_made"] = 0
        player["lizard_state"] = 1

    def current_target(self):
        deliveries = self.machine.game.player["lizard_deliveries"]

        if deliveries >= len(self.DELIVERY_SEQUENCE):
            return None

        return self.DELIVERY_SEQUENCE[deliveries]

    def a_rollover(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return

        self.machine.game.player["lizard_a_hit"] = 1
        self.machine.events.post("lizard_a_complete")

        if self.machine.game.player["lizard_b_hit"] == 1:
            self._ab_complete()

    def b_rollover(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return

        self.machine.game.player["lizard_b_hit"] = 1
        self.machine.events.post("lizard_b_complete")

        if self.machine.game.player["lizard_a_hit"] == 1:
            self._ab_complete()

    def _ab_complete(self):
        """Completing A+B gives the player a short helper/reset during Lizard."""
        self.machine.game.player["lizard_ab_ready"] = 1
        self._show_message("A+B BOOST!", "SERUM VALUE UP", value=self.AB_BONUS_VALUE)
        self.machine.events.post("lizard_ab_complete")

        # Existing YAML comment said A+B should reset the delivery timer.
        self.machine.events.post("lizard_delivery_timer_start")

        # Keep this bonus in Python now. It was present in YAML as lizard_apply_ab_bonus.
        self.machine.game.player["lizard_delivery_value"] += self.AB_BONUS_VALUE

        # Reset A/B state so the combo can be earned again.
        self.machine.game.player["lizard_a_hit"] = 0
        self.machine.game.player["lizard_b_hit"] = 0
        self.machine.game.player["lizard_ab_ready"] = 0
        self.machine.events.post("lizard_clear_ab")

    def serum_collect_request(self, **kwargs):
        if self.mode_done:
            return

        if self.machine.game.player["villain_mode_in_summary"] == True: return

        if self.machine.game.player["lizard_serum_ready"] == 1:
            return

        self._award_points(self.SERUM_COLLECT_SCORE)
        self.machine.game.player["lizard_serum_ready"] = 1

        target = self.current_target() or "web"
        if self.has_case_file("shot_assist") and not self._shot_assist_used:
            subtitle = "DELIVER TO EITHER WEB"
        else:
            subtitle = f"DELIVER TO {target.upper()} WEB"
        self._show_message("SERUM READY", subtitle, value=self.machine.game.player["lizard_delivery_value"], seconds=10, event="show_mode_countdown")
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
            current_value = self.machine.game.player["lizard_delivery_value"]
            self.machine.game.player["lizard_delivery_value"] = max(0, current_value - self.DELIVERY_TICK_VALUE)
            self.machine.events.post("update_mode_status", mode_status_title="SECONDS LEFT", mode_status_value=int(ticks))
            self.machine.events.post("lizard_delivery_tick")


    def serum_expired(self, **kwargs):
        if self.mode_done:
            return

        # Public event for shows/widgets/sounds.
        self.machine.events.post("lizard_delivery_timer_stop")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("lizard_serum_expired_show")

        if self.has_case_file("safety_net") and not self._safety_net_used:
            self._safety_net_used = True
            self.machine.game.player["lizard_serum_ready"] = 0
            self.machine.game.player["lizard_delivery_value"] = self.START_DELIVERY_VALUE
            self._show_message("SAFETY NET", "SERUM SAVED - TRY AGAIN")
            self.machine.events.post("lizard_safety_net_used")
            self.machine.events.post("lizard_light_serum_location")
            self._update_status()
            return

        self._show_message("SERUM EXPIRED", "COLLECT ANOTHER SERUM")
        self.machine.events.post("lizard_serum_expired")

        # This delivery attempt is now spent, even though no points were awarded.
        self.machine.game.player["lizard_deliveries"] += 1

        # Reset serum state for the next attempt.
        self.machine.game.player["lizard_serum_ready"] = 0
        self.machine.game.player["lizard_delivery_value"] = self.START_DELIVERY_VALUE

        # If all attempts are used, end the mode.
        if self.machine.game.player["lizard_deliveries"] >= len(self.DELIVERY_SEQUENCE):
            self.mode_done = True
            self.machine.events.post("lizard_mode_complete")
            return

        # Otherwise light the star again for the next serum collect.
        self.machine.events.post("lizard_light_serum_location")
        self._update_status()

    def delivery_request(self, target=None, **kwargs):
        if self.mode_done:
            return

        if self.machine.game.player["villain_mode_in_summary"] == True: return

        if self.machine.game.player["lizard_followup_ready"] == 1:
            self._followup_request(target)
            return

        if self.machine.game.player["lizard_serum_ready"] == 0:
            return

        required_target = self.current_target()
        used_shot_assist = False

        if required_target != target:
            if self.has_case_file("shot_assist") and not self._shot_assist_used:
                used_shot_assist = True
                self._shot_assist_used = True
            else:
                return

        if self.has_case_file("shot_assist") and not self._shot_assist_used:
            self._shot_assist_used = True

        self.machine.game.player["lizard_serum_ready"] = 0
        delivery_value = self.machine.game.player["lizard_delivery_value"]
        self._award_points(delivery_value)

        if delivery_value > self.machine.game.player["lizard_best_delivery_value"]:
            self.machine.game.player["lizard_best_delivery_value"] = delivery_value

        self.machine.game.player["lizard_deliveries"] += 1
        self.machine.game.player["lizard_deliveries_made"] += 1
        # successful if just one delivery made
        self.machine.game.player["lizard_state"] = 2
        self.machine.game.player["lizard_delivery_value"] = self.START_DELIVERY_VALUE

        subtitle = "ANY WEB ACCEPTED" if used_shot_assist else target.upper()
        self._show_message("SERUM DELIVERED", subtitle, value=delivery_value, event="show_mode_jackpot")
        self.delay.remove("lizard_next_serum_prompt")
        self.delay.add(name="lizard_next_serum_prompt", ms=2000, callback=self._prompt_next_serum)
        self.machine.events.post("lizard_serum_delivered")
        self.machine.events.post("lizard_delivery_timer_stop")

        self._pending_completion_after_followup = self.machine.game.player["lizard_deliveries"] >= len(self.DELIVERY_SEQUENCE)

        if self.has_case_file("more_jackpots"):
            self._start_followup_jackpot(target, delivery_value)
            return

        if self._pending_completion_after_followup:
            self._complete_mode()
            return

        self.machine.events.post("lizard_light_serum_location")
        self._update_status()


    def _prompt_next_serum(self):
        if self.mode_done or self.machine.game.player["villain_mode_in_summary"] is True:
            return
        self.machine.events.post("lizard_more_serum_needed")
        self._show_message("COLLECT MORE SERUM", "HIT THE STAR ROLLOVER", reminder=True)

    def _start_followup_jackpot(self, delivered_target, delivery_value):
        self._followup_target = self.OPPOSITE_TARGET.get(delivered_target, self.current_target() or "center")
        self._followup_value = int(delivery_value / 2)
        self.machine.game.player["lizard_followup_ready"] = 1

        self._show_message(
            "FOLLOW-UP JACKPOT",
            "HIT {} WEB".format(self._followup_target.upper()),
            value=self._followup_value,
            seconds=5,
            event="show_mode_countdown",
        )
        self.machine.events.post("lizard_followup_started")
        self._light_target(self._followup_target)
        self.machine.events.post("lizard_followup_timer_start")

    def _followup_request(self, target):
        if target != self._followup_target:
            return

        self.machine.game.player["lizard_followup_ready"] = 0
        self.machine.events.post("lizard_followup_timer_stop")
        self.machine.events.post("lizard_followup_collected")
        self.machine.events.post("hide_mode_status")
        self._award_points(self._followup_value)
        self._show_message("FOLLOW-UP JACKPOT", target.upper(), value=self._followup_value, event="show_mode_jackpot")
        self._finish_followup()

    def followup_expired(self, **kwargs):
        if self.mode_done or self.machine.game.player["lizard_followup_ready"] == 0:
            return

        self.machine.game.player["lizard_followup_ready"] = 0
        self.machine.events.post("lizard_followup_expired")
        self.machine.events.post("hide_mode_status")
        self._show_message("FOLLOW-UP MISSED", "COLLECT SERUM")
        self._finish_followup()

    def _finish_followup(self):
        self._followup_target = None
        self._followup_value = 0

        if self._pending_completion_after_followup:
            self._complete_mode()
            return

        self.machine.events.post("lizard_light_serum_location")
        self._update_status()

    def _complete_mode(self):
        self.mode_done = True
        self.machine.events.post("lizard_followup_timer_stop")
        self.machine.events.post("lizard_followup_cleanup")
        self._show_message("LIZARD CURED", "MODE COMPLETE", event="show_mode_jackpot")
        self.machine.events.post("lizard_mode_complete")

    def light_next_target(self, **kwargs):
        target = self.current_target()

        if not target:
            return

        if self.has_case_file("shot_assist") and not self._shot_assist_used:
            self.machine.events.post("lizard_light_both_webs")
            return

        self._light_target(target)

    def _light_target(self, target):
        event = self.TARGET_LIGHT_EVENTS.get(target)

        if event:
            self.machine.events.post(event)
