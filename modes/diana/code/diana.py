from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
DIANA - ARCHERY VOLLEY

Limited-arrows monster mode.
- Main left/right flipper presses spend 1 arrow.
- Upper spinner earns +1 arrow.
- Upper-right exit earns +5 arrows.
- Upper-left exit starts the next Hunt by holding the ball on the up-post.
- Hunt timer starts when the up-post drops, either by timeout or flipper cancel.
- Hunt 1: right drops 1/3/5 up for 15s; bullseyes score 100K each.
- Hunt 2: right drops 2/4 up for 12s; bullseyes score 150K each.
- Hunt 3: right drop 3 up for 8s; bullseye scores 200K.
- More Time extends timers to 18/16/12.
- Bigger Jackpots raises bullseyes to 150K/250K/350K.
- More Jackpots makes rubber shots 50K instead of 25K.
- Shot Assist: first drop or rubber hit in each Hunt drops one standing staged target.
- Safety Net: first arrow depletion restores 10 arrows.
- Mode completes when the third Hunt timer expires, then awards 25K per remaining arrow.
"""


class Diana(CaseFileMixin, Mode):
    MODE_KEY = "diana"
    DISPLAY_NAME = "Diana"

    STARTING_ARROWS = 20
    SPINNER_ARROW_AWARD = 1
    UPPER_RIGHT_ARROW_AWARD = 5
    SAFETY_NET_ARROWS = 10
    FLIP_BONUS_VALUE = 25_000
    RUBBER_SCORE = 25_000
    MORE_JACKPOTS_RUBBER_SCORE = 50_000
    POST_HOLD_MS = 6000
    STAGE_BANK_DELAY_MS = 500

    HUNTS = {
        1: {
            "targets": (1, 3, 5),
            "seconds": 15,
            "more_time_seconds": 18,
            "value": 100_000,
            "bigger_value": 150_000,
        },
        2: {
            "targets": (2, 4),
            "seconds": 12,
            "more_time_seconds": 16,
            "value": 150_000,
            "bigger_value": 250_000,
        },
        3: {
            "targets": (3,),
            "seconds": 8,
            "more_time_seconds": 12,
            "value": 200_000,
            "bigger_value": 350_000,
        },
    }

    ALL_RIGHT_DROPS = (1, 2, 3, 4, 5)

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "rearm"
        self.current_hunt = 0
        self.hunt_seconds_left = 0
        self.hunt_active = False
        self.post_hold_active = False
        self.safety_net_used = False
        self.mode_points = 0
        self.arrows_remaining = self.STARTING_ARROWS
        self.arrows_used = 0
        self.spinner_hits = 0
        self.upper_right_exits = 0
        self.rubber_hits = 0
        self.bullseyes = 0
        self.end_bonus = 0
        self.shot_assist_used_this_hunt = False
        self.standing_targets = set()
        self.hit_targets = set()

        player = self.machine.game.player
        player["diana_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "RUBBER SHOTS 50K"),
            ("bigger_jackpots", "BULLSEYES BOOSTED"),
            ("more_time", "HUNT TIMERS EXTENDED"),
            ("safety_net", "10 ARROW SAFETY NET"),
            ("shot_assist", "FIRST HIT DROPS A TARGET"),
        ])

        self.add_mode_event_handler("s_left_flipper_active", self._flipper_pressed)
        self.add_mode_event_handler("s_right_flipper_active", self._flipper_pressed)
        self.add_mode_event_handler("diana_upper_spinner_hit", self._upper_spinner_hit)
        self.add_mode_event_handler("diana_upper_right_exit", self._upper_right_exit)
        self.add_mode_event_handler("diana_upper_left_exit", self._upper_left_exit)
        self.add_mode_event_handler("diana_upper_entered", self._upper_entered)
        self.add_mode_event_handler("diana_post_hold_cancel", self._post_hold_cancel)
        self.add_mode_event_handler("diana_complete_request", self._complete_mode)
        self.add_mode_event_handler("diana_fail_request", self._complete_mode)

        for target in self.ALL_RIGHT_DROPS:
            self.add_mode_event_handler(
                f"diana_right_drop_{target}_hit",
                self._right_drop_hit,
                target=target,
            )

        self.add_mode_event_handler("diana_right_rubber_hit", self._right_rubber_hit)

        self.machine.events.post("clear_saucers")
        self.machine.events.post("reset_5bank")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("diana_mode_started")
        self._show_mode_message("DIANA", "GET TO THE ROOF", reminder=True)
        self._sync_vars()

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self._clear_delays()
        if self.post_hold_active:
            self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("diana_clear_all_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        self.machine.events.post("cancel_mode_message_reminder")
        super().mode_stop(**kwargs)


    def _clear_delays(self):
        self.delay.remove("diana_post_hold_release")
        self.delay.remove("diana_stage_right_bank")
        self.delay.remove("diana_hunt_timer_tick")

    def _show_mode_message(self, title, subtitle="", value="", seconds="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )

    def _show_mode_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _show_mode_countdown(self, title, seconds, subtitle=""):
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value="",
            message_mode_seconds=seconds,
        )

    def _flipper_pressed(self, **kwargs):
        if self._done_or_summary():
            return

        self.arrows_remaining -= 1
        self.arrows_used += 1
        self.machine.events.post("diana_arrow_used", arrows_remaining=self.arrows_remaining)

        if self.arrows_remaining <= 0:
            if self.has_case_file("safety_net") and not self.safety_net_used:
                self.safety_net_used = True
                self.arrows_remaining = self.SAFETY_NET_ARROWS
                self.machine.events.post("diana_safety_net_used", arrows_remaining=self.arrows_remaining)
                self._show_mode_message("SAFETY NET", "10 ARROWS RESTORED")
            else:
                self.arrows_remaining = 0
                self._sync_vars()
                self.machine.events.post("diana_goal_missed")
                self._complete_mode()
                return

        if self.arrows_remaining <= 5 or self.arrows_remaining % 5 == 0:
            self._show_mode_message("ARROWS", f"{self.arrows_remaining} REMAINING")
        self._sync_vars()

    def _upper_spinner_hit(self, **kwargs):
        if self._done_or_summary():
            return

        self.spinner_hits += 1
        self.arrows_remaining += self.SPINNER_ARROW_AWARD
        self.machine.events.post("diana_upper_spinner_arrow_awarded", arrows_remaining=self.arrows_remaining)
        self._show_mode_message("+1 ARROW", f"{self.arrows_remaining} ARROWS")
        self._sync_vars()

    def _upper_right_exit(self, **kwargs):
        if self._done_or_summary():
            return

        self.upper_right_exits += 1
        self.arrows_remaining += self.UPPER_RIGHT_ARROW_AWARD
        self.machine.events.post("diana_upper_right_arrows_awarded", arrows_remaining=self.arrows_remaining)
        self._show_mode_message("+5 ARROWS", f"{self.arrows_remaining} ARROWS")
        self._sync_vars()

    def _upper_left_exit(self, **kwargs):
        if self._done_or_summary():
            return

        if self.phase not in ("rearm", "ready"):
            return

        next_hunt = self.current_hunt + 1
        if next_hunt not in self.HUNTS:
            return

        self._prepare_hunt(next_hunt)

    def _upper_entered(self, **kwargs):
        if self._done_or_summary():
            return

        if self.phase == "hunt" and self.current_hunt in (1, 2):
            self._end_hunt_early(reason="upper_rearm")

    def _prepare_hunt(self, hunt_number):
        self.phase = "post_hold"
        self.current_hunt = hunt_number
        self.hunt_active = False
        self.post_hold_active = True
        self.shot_assist_used_this_hunt = False
        self.standing_targets = set(self.HUNTS[hunt_number]["targets"])
        self.hit_targets = set()
        self.machine.events.post("diana_hunt_prepare", hunt=hunt_number)
        self.machine.events.post("enable_up_post_event")
        self._stage_right_bank_for_hunt(hunt_number)
        self._show_mode_message(f"HUNT {hunt_number}", "READY YOUR SHOT")
        self.delay.add(
            name="diana_post_hold_release",
            ms=self.POST_HOLD_MS,
            callback=self._release_post_hold,
        )
        self._sync_vars()

    def _stage_right_bank_for_hunt(self, hunt_number):
        self.machine.events.post("reset_5bank")
        self.delay.add(
            name="diana_stage_right_bank",
            ms=self.STAGE_BANK_DELAY_MS,
            callback=self._drop_non_staged_targets,
        )

    def _drop_non_staged_targets(self):
        if self._done_or_summary() or self.phase not in ("post_hold", "hunt"):
            return

        for target in self.ALL_RIGHT_DROPS:
            if target not in self.standing_targets:
                self._drop_right_target(target)

        self.machine.events.post(f"diana_hunt_{self.current_hunt}_staged")
        self.machine.events.post("diana_hunt_targets_staged", hunt=self.current_hunt)

    def _post_hold_cancel(self, **kwargs):
        if not self.post_hold_active:
            return
        self.delay.remove("diana_post_hold_release")
        self.machine.events.post("diana_post_hold_cancelled")
        self._release_post_hold(reason="flipper_cancel")

    def _release_post_hold(self, reason="timer", **kwargs):
        if self._done_or_summary() or not self.post_hold_active:
            return

        self.post_hold_active = False
        self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("diana_post_hold_released", reason=reason, hunt=self.current_hunt)
        self._start_hunt_timer()

    def _start_hunt_timer(self):
        if self._done_or_summary():
            return

        hunt = self.HUNTS[self.current_hunt]
        self.phase = "hunt"
        self.hunt_active = True
        self.hunt_seconds_left = self._hunt_seconds(self.current_hunt)
        self.machine.events.post(
            "diana_hunt_started",
            hunt=self.current_hunt,
            seconds=self.hunt_seconds_left,
        )
        self._show_mode_message(f"HUNT {self.current_hunt}", "BULLSEYES AND RUBBER")
        self._sync_vars()
        self._schedule_hunt_tick()

    def _schedule_hunt_tick(self):
        if self._done_or_summary() or not self.hunt_active:
            return

        self.delay.add(
            name="diana_hunt_timer_tick",
            ms=1000,
            callback=self._hunt_timer_tick,
        )

    def _hunt_timer_tick(self):
        if self._done_or_summary() or not self.hunt_active:
            return

        self.hunt_seconds_left -= 1
        self.machine.events.post(
            "diana_hunt_timer_changed",
            hunt=self.current_hunt,
            seconds=self.hunt_seconds_left,
        )
        self._sync_vars()

        if self.hunt_seconds_left <= 0:
            self._hunt_timer_expired()
            return

        self._schedule_hunt_tick()

    def _hunt_timer_expired(self):
        if self._done_or_summary() or not self.hunt_active:
            return

        hunt = self.current_hunt
        self.machine.events.post("diana_hunt_timer_expired", hunt=hunt)
        self.hunt_active = False
        self.delay.remove("diana_hunt_timer_tick")
        self._drop_remaining_staged_targets()

        if hunt >= 3:
            self._award_end_bonus()
            self._complete_mode()
            return

        self.phase = "rearm"
        self._show_mode_message("REARM", "GET BACK TO THE ROOF", reminder=True)
        self._sync_vars()

    def _end_hunt_early(self, reason="upper_rearm"):
        if self._done_or_summary() or not self.hunt_active:
            return

        hunt = self.current_hunt
        self.hunt_active = False
        self.delay.remove("diana_hunt_timer_tick")
        self._drop_remaining_staged_targets()
        self.phase = "rearm"
        self.machine.events.post("diana_hunt_ended_early", hunt=hunt, reason=reason)
        self._show_mode_message("HUNT ENDED", "REARM UPSTAIRS")
        self._sync_vars()

    def _right_drop_hit(self, target=None, **kwargs):
        if self._done_or_summary() or not self.hunt_active:
            return

        if target not in self.standing_targets:
            return

        self.standing_targets.discard(target)
        self.hit_targets.add(target)
        value = self._bullseye_value(self.current_hunt)
        self.bullseyes += 1
        self._score(value)
        self.machine.events.post(
            "diana_bullseye_awarded",
            hunt=self.current_hunt,
            target=target,
            value=value,
        )
        self._show_mode_jackpot("BULLSEYE", value, f"HUNT {self.current_hunt}")
        self._use_shot_assist_if_available(source="drop", hit_target=target)
        self._sync_vars()

    def _right_rubber_hit(self, **kwargs):
        if self._done_or_summary() or not self.hunt_active:
            return

        value = self._rubber_value()
        self.rubber_hits += 1
        self._score(value)
        self.machine.events.post(
            "diana_rubber_arrow_awarded",
            hunt=self.current_hunt,
            value=value,
        )
        self._show_mode_message("ARROW SHOT", "RUBBER TARGET", value=value)
        self._use_shot_assist_if_available(source="rubber")
        self._sync_vars()

    def _use_shot_assist_if_available(self, source=None, hit_target=None):
        if not self.has_case_file("shot_assist"):
            return
        if self.shot_assist_used_this_hunt:
            return
        if not self.standing_targets:
            return

        self.shot_assist_used_this_hunt = True
        # Prefer a different target than the one just hit, but any standing target is valid.
        candidates = sorted(target for target in self.standing_targets if target != hit_target)
        if not candidates:
            candidates = sorted(self.standing_targets)
        assist_target = candidates[0]
        self.standing_targets.discard(assist_target)
        self._drop_right_target(assist_target)
        self.machine.events.post(
            "diana_shot_assist_target_dropped",
            hunt=self.current_hunt,
            target=assist_target,
            source=source,
        )
        self._show_mode_message("SHOT ASSIST", f"TARGET {assist_target} DROPPED")

    def _drop_remaining_staged_targets(self):
        for target in sorted(self.standing_targets):
            self._drop_right_target(target)
        self.standing_targets.clear()
        self.machine.events.post("diana_remaining_targets_dropped", hunt=self.current_hunt)

    def _drop_right_target(self, target):
        self.machine.events.post(f"diana_drop_right_target_{target}")

    def _hunt_seconds(self, hunt_number):
        key = "more_time_seconds" if self.has_case_file("more_time") else "seconds"
        return self.HUNTS[hunt_number][key]

    def _bullseye_value(self, hunt_number):
        key = "bigger_value" if self.has_case_file("bigger_jackpots") else "value"
        return self.HUNTS[hunt_number][key]

    def _rubber_value(self):
        if self.has_case_file("more_jackpots"):
            return self.MORE_JACKPOTS_RUBBER_SCORE
        return self.RUBBER_SCORE

    def _award_end_bonus(self):
        self.end_bonus = max(0, self.arrows_remaining) * self.FLIP_BONUS_VALUE
        if self.end_bonus:
            self._score(self.end_bonus)
            self.machine.events.post(
                "diana_end_bonus_awarded",
                arrows_remaining=self.arrows_remaining,
                value=self.end_bonus,
            )
            self._show_mode_jackpot("ARROW BONUS", self.end_bonus, f"{self.arrows_remaining} ARROWS")
        self._sync_vars()

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.hunt_active = False
        self.post_hold_active = False
        self._clear_delays()
        player = self.machine.game.player
        player["diana_state"] = 2
        self.machine.events.post("timer_timer_up_post_hold_complete")
        self._sync_vars()
        self.machine.events.post("diana_mode_complete")

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["diana_arrows_remaining"] = self.arrows_remaining
        player["diana_arrows_used"] = self.arrows_used
        player["diana_current_hunt"] = self.current_hunt
        player["diana_hunt_seconds"] = self.hunt_seconds_left
        player["diana_hunt_active"] = 1 if self.hunt_active else 0
        player["diana_phase"] = self.phase
        player["diana_bullseyes"] = self.bullseyes
        player["diana_rubber_hits"] = self.rubber_hits
        player["diana_spinner_hits"] = self.spinner_hits
        player["diana_upper_right_exits"] = self.upper_right_exits
        player["diana_safety_net_used"] = 1 if self.safety_net_used else 0
        player["diana_end_bonus"] = self.end_bonus
        player["diana_standing_targets"] = len(self.standing_targets)
        player["active_mode_hits"] = self.bullseyes + self.rubber_hits
        player["active_mode_major_hits"] = self.bullseyes
        self._update_mode_status()

    def _update_mode_status(self):
        if self.mode_done:
            return

        if self.hunt_active:
            self.machine.events.post(
                "update_mode_status",
                mode_status_title="ARROWS / TIME",
                mode_status_value=f"{max(0, self.arrows_remaining)} / {max(0, self.hunt_seconds_left)}",
            )
        else:
            self.machine.events.post(
                "update_mode_status",
                mode_status_title="ARROWS LEFT",
                mode_status_value=max(0, self.arrows_remaining),
            )

    def _done_or_summary(self):
        player = self.machine.game.player
        return self.mode_done or player["villain_mode_in_summary"] is True
