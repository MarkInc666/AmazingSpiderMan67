from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
    "title": "THE LIZARD MAN",
    "intro_1": "Collect the antidote at the red star rollover.",
    "intro_2": "Deliver it to Lizard Man at the left web target.",
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

    DELIVERY_SEQUENCE = ["left", "left"]

    TARGET_LIGHT_EVENTS = {
        "left": "lizard_light_left_web",
        "center": "lizard_light_center_web",
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
    FOLLOWUP_SECONDS = 10

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self._init_player_vars()
        self.mode_done = False

        self.add_mode_event_handler("s_star_rollover_active", self.serum_collect_request)
        self.add_mode_event_handler("s_web_target_left_active", self.delivery_request, target="left")
        self.add_mode_event_handler("s_web_target_mid_active", self.delivery_request, target="center")

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
        self.add_mode_event_handler("timer_lizard_followup_timer_complete", self.followup_expired)
        self.add_mode_event_handler("lizard_light_delivery_target", self.light_next_target)

        self.publish_case_file_bonus_events("lizard")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "CENTER WEB FOLLOW-UP JACKPOT"),
            ("bigger_jackpots", "SERUM STARTS AT 1.5 MILLION"),
            ("more_time", "20 SECONDS AND SLOWER VALUE DECAY"),
            ("safety_net", "FIRST EXPIRED SERUM IS SAVED"),
            ("shot_assist", "MAIN SPINNER OR LEFT B DELIVERS SERUM"),
        ])

        # Lizard owns the gate for the full mode so the star remains reachable.
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("lizard_light_serum_location")
        self.machine.events.post("clear_saucers")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="COLLECT SERUM",
            message_mode_subtitle="HIT THE STAR ROLLOVER",
        )
        self._update_status()

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self._stop_delivery_timers()
        self.machine.events.post("lizard_followup_timer_stop")
        self.machine.events.post("lizard_followup_cleanup")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
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
        player["lizard_followup_ready"] = 0

        self._safety_net_used = False
        self._followup_target = None
        self._followup_value = 0
        self._pending_completion_after_followup = False

        player["active_mode_points"] = 0
        player["lizard_best_delivery_value"] = 0
        player["lizard_deliveries_made"] = 0
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
        deliveries = player["lizard_deliveries"]
        if player["lizard_followup_ready"] == 1:
            title = "EXTRA JACKPOT"
            value = "CENTER WEB"
        elif player["lizard_serum_ready"] == 1:
            title = "DELIVER SERUM"
            value = "LEFT WEB"
        else:
            title = "COLLECT SERUM"
            value = f"STAR  {deliveries} OF {len(self.DELIVERY_SEQUENCE)}"
        self.machine.events.post("show_mode_status", mode_status_title=title, mode_status_value=value)

    def current_target(self):
        deliveries = self.machine.game.player["lizard_deliveries"]
        if deliveries >= len(self.DELIVERY_SEQUENCE):
            return None
        return self.DELIVERY_SEQUENCE[deliveries]

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
        """Completing A+B boosts the active serum and restarts its timer."""
        player = self.machine.game.player
        player["lizard_ab_ready"] = 1
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="A+B BOOST!",
            message_mode_subtitle="SERUM VALUE UP",
            message_mode_value=self.AB_BONUS_VALUE,
        )
        self.machine.events.post("lizard_ab_complete")

        if player["lizard_serum_ready"] == 1:
            player["lizard_delivery_value"] += self.AB_BONUS_VALUE
            self._start_delivery_timer()

        player["lizard_a_hit"] = 0
        player["lizard_b_hit"] = 0
        player["lizard_ab_ready"] = 0
        self.machine.events.post("lizard_clear_ab")

    def serum_collect_request(self, **kwargs):
        if self.mode_done or self.machine.game.player["villain_mode_in_summary"] is True:
            return

        player = self.machine.game.player
        if player["lizard_serum_ready"] == 1:
            return
        if player["lizard_deliveries"] >= len(self.DELIVERY_SEQUENCE):
            return

        # Starting the next serum early cancels the optional center-web jackpot.
        if player["lizard_followup_ready"] == 1:
            self._cancel_followup_for_serum()

        player["lizard_delivery_value"] = self.start_delivery_value
        self._award_points(self.SERUM_COLLECT_SCORE)
        player["lizard_serum_ready"] = 1

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
        self._start_delivery_timer()
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
        self.machine.events.post(
            "update_mode_status",
            mode_status_title="SECONDS LEFT",
            mode_status_value=int(ticks),
        )
        self.machine.events.post("lizard_delivery_tick")

    def serum_expired(self, **kwargs):
        if self.mode_done:
            return

        player = self.machine.game.player
        self._stop_delivery_timers()
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("lizard_serum_expired_show")

        if self.has_case_file("safety_net") and not self._safety_net_used:
            self._safety_net_used = True
            player["lizard_serum_ready"] = 0
            player["lizard_delivery_value"] = self.start_delivery_value
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="SAFETY NET",
                message_mode_subtitle="SERUM SAVED - TRY AGAIN",
            )
            self.machine.events.post("lizard_safety_net_used")
            self.machine.events.post("lizard_light_serum_location")
            self._update_status()
            return

        self.machine.events.post(
            "show_mode_message",
            message_mode_title="SERUM EXPIRED",
            message_mode_subtitle="DELIVERY ATTEMPT LOST",
        )
        self.machine.events.post("lizard_serum_expired")

        player["lizard_deliveries"] += 1
        player["lizard_serum_ready"] = 0
        player["lizard_delivery_value"] = self.start_delivery_value

        if player["lizard_deliveries"] >= len(self.DELIVERY_SEQUENCE):
            self._complete_mode()
            return

        self.machine.events.post("lizard_light_serum_location")
        self._update_status()

    def delivery_request(self, target=None, **kwargs):
        if self.mode_done or self.machine.game.player["villain_mode_in_summary"] is True:
            return

        player = self.machine.game.player
        if player["lizard_followup_ready"] == 1:
            self._followup_request(target)
            return
        if player["lizard_serum_ready"] == 0:
            return

        used_shot_assist = target == "shot_assist"
        if used_shot_assist and not self.has_case_file("shot_assist"):
            return
        if not used_shot_assist and target != "left":
            return

        player["lizard_serum_ready"] = 0
        delivery_value = max(self.MINIMUM_DELIVERY_VALUE, player["lizard_delivery_value"])
        self._award_points(delivery_value)

        if delivery_value > player["lizard_best_delivery_value"]:
            player["lizard_best_delivery_value"] = delivery_value

        player["lizard_deliveries"] += 1
        player["lizard_deliveries_made"] += 1
        player["lizard_state"] = 2
        player["lizard_delivery_value"] = self.start_delivery_value

        subtitle = "SHOT ASSIST" if used_shot_assist else "LEFT WEB"
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SERUM DELIVERED",
            message_mode_subtitle=subtitle,
            message_mode_value=delivery_value,
        )
        self.delay.remove("lizard_next_serum_prompt")
        self.delay.add(name="lizard_next_serum_prompt", ms=2000, callback=self._prompt_next_serum)
        self.machine.events.post("lizard_serum_delivered")
        self._stop_delivery_timers()

        self._pending_completion_after_followup = player["lizard_deliveries"] >= len(self.DELIVERY_SEQUENCE)

        if self.has_case_file("more_jackpots"):
            self._start_followup_jackpot(delivery_value)
            return
        if self._pending_completion_after_followup:
            self._complete_mode()
            return

        self.machine.events.post("lizard_light_serum_location")
        self._update_status()

    def _prompt_next_serum(self):
        player = self.machine.game.player
        if (
            self.mode_done
            or player["villain_mode_in_summary"] is True
            or player["lizard_followup_ready"] == 1
            or player["lizard_deliveries"] >= len(self.DELIVERY_SEQUENCE)
        ):
            return
        self.machine.events.post("lizard_more_serum_needed")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="COLLECT MORE SERUM",
            message_mode_subtitle="HIT THE STAR ROLLOVER",
            reminder=True,
        )

    def _start_followup_jackpot(self, delivery_value):
        self._followup_target = "center"
        self._followup_value = int(delivery_value / 2)
        self.machine.game.player["lizard_followup_ready"] = 1

        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title="EXTRA JACKPOT",
            message_mode_subtitle="HIT CENTER WEB",
            message_mode_value=self._followup_value,
            message_mode_seconds=self.FOLLOWUP_SECONDS,
        )
        self.machine.events.post("lizard_followup_started")
        self._light_target("center")
        self.machine.events.post("lizard_followup_timer_start")
        self._update_status()

    def _followup_request(self, target):
        if target != "center":
            return

        self.machine.game.player["lizard_followup_ready"] = 0
        self.machine.events.post("lizard_followup_timer_stop")
        self.machine.events.post("lizard_followup_collected")
        self.machine.events.post("hide_mode_status")
        self._award_points(self._followup_value)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="EXTRA JACKPOT",
            message_mode_subtitle="CENTER WEB",
            message_mode_value=self._followup_value,
        )
        self._finish_followup()

    def _cancel_followup_for_serum(self):
        self.machine.game.player["lizard_followup_ready"] = 0
        self.machine.events.post("lizard_followup_timer_stop")
        self.machine.events.post("lizard_followup_cleanup")
        self._followup_target = None
        self._followup_value = 0
        self._pending_completion_after_followup = False

    def followup_expired(self, **kwargs):
        if self.mode_done or self.machine.game.player["lizard_followup_ready"] == 0:
            return

        self.machine.game.player["lizard_followup_ready"] = 0
        self.machine.events.post("lizard_followup_expired")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="EXTRA JACKPOT MISSED",
            message_mode_subtitle="COLLECT SERUM",
        )
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
        self._stop_delivery_timers()
        self.machine.events.post("lizard_followup_timer_stop")
        self.machine.events.post("lizard_followup_cleanup")
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
