import random

from mpf.core.mode import Mode

from modes.common.case_file_mixin import CaseFileMixin


class SpiderMen(CaseFileMixin, Mode):
    """Align the six-point homeworld ray before the proton test fires."""

    MODE_KEY = "spider_men"
    DISPLAY_NAME = "The Spider-Men"

    NORMAL_TIMER_SECONDS = 40
    MORE_TIME_SECONDS = 60
    SUPER_SECONDS = 10

    ALIGNMENT_VALUE = 100_000
    BIGGER_ALIGNMENT_VALUE = 150_000
    FINE_ADJUSTMENT_VALUE = 25_000
    SUPER_VALUE = 500_000
    FINAL_MESSAGE_MS = 2_000

    SHOTS = (
        {"key": "saucer_1", "switch": "s_saucer_1"},
        {"key": "saucer_2", "switch": "s_saucer_2"},
        {"key": "saucer_3", "switch": "s_saucer_3"},
        {"key": "star", "switch": "s_star_rollover"},
        {"key": "upper_a", "switch": "s_inlane_a"},
        {"key": "upper_b", "switch": "s_inlane_b"},
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_done = False
        self.phase = "alignment"
        self.aligned = [False] * len(self.SHOTS)
        self.seconds_left = 0
        self.jackpots = 0
        self.fine_adjustments = 0
        self.mode_points = 0
        self.super_collected = False

        self.case_files = self.get_case_file_bonuses()
        self.timer_seconds = (
            self.MORE_TIME_SECONDS
            if self.has_case_file("more_time")
            else self.NORMAL_TIMER_SECONDS
        )
        self.alignment_value = (
            self.BIGGER_ALIGNMENT_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.ALIGNMENT_VALUE
        )
        self.shot_assist_available = self.has_case_file("shot_assist")

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars(update_status=False)

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SIX JACKPOTS LIGHT 500K CENTER WEB SUPER"),
            ("bigger_jackpots", "ALIGNMENT JACKPOTS WORTH 150K"),
            ("more_time", "PROTON TIMER EXTENDED TO 60 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST JACKPOT ALIGNS AN EXTRA POSITION"),
        ])

        self.add_mode_event_handler("s_left_flipper_active", self._rotate_left)
        self.add_mode_event_handler("s_right_flipper_active", self._rotate_right)
        for index, shot in enumerate(self.SHOTS):
            self.add_mode_event_handler(
                f"{shot['switch']}_active",
                self._shot_hit,
                index=index,
            )

        self.add_mode_event_handler(
            "s_web_target_mid_active", self._center_web_hit
        )
        # The alignment uses only main-playfield shots. Keep the rooftop closed
        # if another active subsystem asks to open it during this mode.
        self.add_mode_event_handler(
            "rooftop_diverter_open", self._force_gate_closed
        )
        self.add_mode_event_handler("open_rooftop_gate", self._force_gate_closed)
        self.add_mode_event_handler(
            "spider_men_complete_request", self._begin_success
        )
        self.add_mode_event_handler(
            "spider_men_fail_request", self._begin_failure
        )

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.machine.events.post("spider_men_startup_complete")
        self._refresh_lights()
        self._update_status()
        self._show_message(
            "ALIGN THE HOMEWORLD RAY",
            "FLIPPERS ROTATE THE LIGHTS",
            reminder=True,
        )

    def mode_stop(self, **kwargs):
        self.delay.remove("spider_men_proton_tick")
        self.delay.remove("spider_men_super_tick")
        self.delay.remove("spider_men_final_message")
        self.machine.events.post("spider_men_clear_lights")
        self.machine.events.post("spider_men_gi_restore")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _rotate_left(self, **kwargs):
        if self.mode_done or self.phase != "alignment":
            return
        self.aligned = self.aligned[1:] + self.aligned[:1]
        self._refresh_lights()

    def _rotate_right(self, **kwargs):
        if self.mode_done or self.phase != "alignment":
            return
        self.aligned = self.aligned[-1:] + self.aligned[:-1]
        self._refresh_lights()

    def _shot_hit(self, index, **kwargs):
        if self.mode_done or self.phase != "alignment":
            return

        if self.aligned[index]:
            self._score(self.FINE_ADJUSTMENT_VALUE)
            self.fine_adjustments += 1
            self._sync_vars()
            self.machine.events.post(
                "spider_men_fine_adjustment",
                shot=self.SHOTS[index]["key"],
                value=self.FINE_ADJUSTMENT_VALUE,
                fine_adjustments=self.fine_adjustments,
            )
            self._show_message(
                "FINE ADJUSTMENT",
                "POSITION ALREADY ALIGNED",
                value=self.FINE_ADJUSTMENT_VALUE,
            )
            return

        first_jackpot = self.jackpots == 0
        self._award_alignment(index)

        if first_jackpot:
            self._start_proton_timer()

        if self.shot_assist_available and not self.mode_done:
            self.shot_assist_available = False
            unaligned = [
                position
                for position, completed in enumerate(self.aligned)
                if not completed
            ]
            if unaligned:
                assisted_index = random.choice(unaligned)
                assisted_value = self._award_alignment(
                    assisted_index,
                    assisted=True,
                )
                self.machine.events.post(
                    "spider_men_case_file_shot_assist_used",
                    shot=self.SHOTS[assisted_index]["key"],
                    value=assisted_value,
                )
                self._show_message(
                    "SHOT ASSIST",
                    "EXTRA POSITION ALIGNED",
                    value=assisted_value,
                )

        self._refresh_lights()
        self._sync_vars()

        if all(self.aligned):
            self._alignment_complete()

    def _award_alignment(self, index, assisted=False):
        self.aligned[index] = True
        self.jackpots += 1
        value = self.alignment_value
        if self.jackpots == len(self.SHOTS):
            value *= 2

        self._score(value)
        self.machine.events.post(
            "spider_men_alignment_jackpot",
            shot=self.SHOTS[index]["key"],
            value=value,
            jackpots=self.jackpots,
            assisted=int(assisted),
        )
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="RAY ALIGNED",
            message_mode_subtitle=(
                "SHOT ASSIST"
                if assisted
                else f"{self.jackpots} OF {len(self.SHOTS)}"
            ),
            message_mode_value=value,
            message_mode_seconds="",
        )
        return value

    def _start_proton_timer(self):
        self.seconds_left = self.timer_seconds
        self.machine.events.post(
            "spider_men_proton_timer_started", seconds=self.seconds_left
        )
        self.delay.reset(
            name="spider_men_proton_tick",
            ms=1000,
            callback=self._proton_tick,
        )

    def _proton_tick(self):
        if self.mode_done or self.phase != "alignment":
            return

        self.seconds_left -= 1
        self.machine.events.post(
            "spider_men_proton_timer_changed", seconds=max(0, self.seconds_left)
        )
        self._update_status()

        if self.seconds_left <= 0:
            self._begin_failure()
            return

        self.delay.reset(
            name="spider_men_proton_tick",
            ms=1000,
            callback=self._proton_tick,
        )

    def _alignment_complete(self):
        self.delay.remove("spider_men_proton_tick")
        self.seconds_left = 0
        self.machine.events.post("spider_men_homeworld_ray_aligned")

        if self.has_case_file("more_jackpots"):
            self.phase = "super"
            self.seconds_left = self.SUPER_SECONDS
            self.machine.events.post(
                "spider_men_super_ready",
                value=self.SUPER_VALUE,
                seconds=self.seconds_left,
            )
            self._show_countdown(
                "SUPER JACKPOT LIT",
                "CENTER WEB",
                self.seconds_left,
                value=self.SUPER_VALUE,
                reminder=True,
            )
            self._update_status()
            self.delay.reset(
                name="spider_men_super_tick",
                ms=1000,
                callback=self._super_tick,
            )
            return

        self._begin_success()

    def _center_web_hit(self, **kwargs):
        if self.mode_done or self.phase != "super":
            return

        self.delay.remove("spider_men_super_tick")
        self.super_collected = True
        self._score(self.SUPER_VALUE)
        self._sync_vars(update_status=False)
        self.machine.events.post(
            "spider_men_super_collected", value=self.SUPER_VALUE
        )
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="HOMEWORLD SUPER",
            message_mode_subtitle="CENTER WEB",
            message_mode_value=self.SUPER_VALUE,
            message_mode_seconds="",
        )
        self._begin_success(show_final_message=False)

    def _super_tick(self):
        if self.mode_done or self.phase != "super":
            return

        self.seconds_left -= 1
        self.machine.events.post(
            "spider_men_super_timer_changed", seconds=max(0, self.seconds_left)
        )
        self._update_status()

        if self.seconds_left <= 0:
            self._begin_success()
            return

        self._show_countdown(
            "SUPER JACKPOT LIT",
            "CENTER WEB",
            self.seconds_left,
            value=self.SUPER_VALUE,
            reminder=True,
        )
        self.delay.reset(
            name="spider_men_super_tick",
            ms=1000,
            callback=self._super_tick,
        )

    def _begin_success(self, show_final_message=True, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.phase = "complete"
        self.delay.remove("spider_men_proton_tick")
        self.delay.remove("spider_men_super_tick")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("spider_men_clear_lights")
        self.machine.events.post("hide_mode_status")
        self._sync_vars(update_status=False)

        if show_final_message:
            self._show_message("THE SPIDER-MEN", "RETURN HOME", seconds="2")

        self.delay.reset(
            name="spider_men_final_message",
            ms=self.FINAL_MESSAGE_MS,
            callback=self._finish_success,
        )

    def _finish_success(self):
        self.machine.events.post("spider_men_mode_complete")

    def _begin_failure(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.phase = "failed"
        self.delay.remove("spider_men_proton_tick")
        self.delay.remove("spider_men_super_tick")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("spider_men_clear_lights")
        self.machine.events.post("hide_mode_status")
        self._sync_vars(update_status=False)
        self._show_message(
            "PROTON TEST ACTIVATED",
            "ALIGNMENT FAILED",
            seconds="2",
        )
        self.delay.reset(
            name="spider_men_final_message",
            ms=self.FINAL_MESSAGE_MS,
            callback=self._finish_failure,
        )

    def _finish_failure(self):
        self.machine.events.post("spider_men_mode_failed")

    def _force_gate_closed(self, **kwargs):
        if not self.mode_done:
            self.machine.events.post("rooftop_diverter_close")

    def _refresh_lights(self):
        self.machine.events.post("spider_men_alignment_lights_off")
        for index, completed in enumerate(self.aligned):
            state = "solid" if completed else "pulse"
            self.machine.events.post(
                f"spider_men_{self.SHOTS[index]['key']}_{state}"
            )
        self.machine.events.post(f"spider_men_gi_{sum(self.aligned)}")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _sync_vars(self, update_status=True):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.jackpots
        player["active_mode_major_hits"] = self.fine_adjustments
        if update_status and not self.mode_done:
            self._update_status()

    def _update_status(self):
        if self.phase == "super":
            title = "SUPER JACKPOT"
            value = f"CENTER WEB {max(0, self.seconds_left)}"
        elif self.seconds_left > 0:
            title = f"PROTON TEST {self.seconds_left}"
            value = f"{self.jackpots} / {len(self.SHOTS)} ALIGNED"
        else:
            title = "HOMEWORLD RAY"
            value = f"{self.jackpots} / {len(self.SHOTS)} ALIGNED"

        self.machine.events.post(
            "show_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _show_message(
        self,
        title,
        subtitle="",
        value="",
        seconds="",
        reminder=False,
    ):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )

    def _show_countdown(
        self,
        title,
        subtitle,
        seconds,
        value="",
        reminder=False,
    ):
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )
