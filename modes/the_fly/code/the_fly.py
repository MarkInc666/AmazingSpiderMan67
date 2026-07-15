from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class TheFly(CaseFileMixin, Mode):
    """The Fly: Rooftop Swarm.

    Saucer opens the roof gate. Upper entrance starts a 10-flip roof
    attempt. The first two unique upper targets are jackpots; the third
    unique target is a Super whose value is boosted by remaining flips.
    """

    MODE_KEY = "the_fly"
    DISPLAY_NAME = "THE FLY"

    BASE_FLIPS = 10
    MORE_TIME_FLIPS = 15
    FLIP_DISABLE_MS = 4000

    TARGET_VALUES = (100_000, 200_000)
    SUPER_BASE_VALUE = 300_000
    FLIP_BONUS_VALUE = 100_000

    BIGGER_TARGET_VALUES = (150_000, 300_000)
    BIGGER_SUPER_BASE_VALUE = 450_000
    BIGGER_FLIP_BONUS_VALUE = 150_000

    REPEAT_TARGET_VALUE = 50_000
    MORE_JACKPOTS_REPEAT_VALUE = 250_000
    ROOFTOP_JACKPOTS_TO_COMPLETE = 3

    TARGETS = {
        "left": {
            "switch": "s_upper_target_left_active",
            "needed": "the_fly_target_left_needed",
            "solid": "the_fly_target_left_solid",
            "off": "the_fly_target_left_off",
        },
        "center": {
            "switch": "s_upper_target_center_active",
            "needed": "the_fly_target_center_needed",
            "solid": "the_fly_target_center_solid",
            "off": "the_fly_target_center_off",
        },
        "right": {
            "switch": "s_upper_target_right_active",
            "needed": "the_fly_target_right_needed",
            "solid": "the_fly_target_right_solid",
            "off": "the_fly_target_right_off",
        },
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.case_files = self.get_case_file_bonuses()
        self._configure_values()

        self.mode_done = False
        self.gate_open = False
        self.roof_attempt_active = False
        self.flips_remaining = 0
        self.targets_hit = set()
        self.rooftop_jackpots = 0
        self.jackpot_hits = 0
        self.mode_points = 0
        self.shot_assist_used = False

        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player[f"{self.MODE_KEY}_state"] = 1

        self.add_mode_event_handler("s_saucer_1_active", self._saucer_hit)
        self.add_mode_event_handler("s_saucer_2_active", self._saucer_hit)
        self.add_mode_event_handler("s_saucer_3_active", self._saucer_hit)
        self.add_mode_event_handler("s_upper_entrance_opto_active", self._upper_entrance)
        self.add_mode_event_handler("s_right_flipper_upper_active", self._upper_flipper_pressed)
        self.add_mode_event_handler("s_upper_exit_left_opto_active", self._upper_exit)
        self.add_mode_event_handler("s_upper_exit_right_opto_active", self._upper_exit)
        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)

        for target_name, target_config in self.TARGETS.items():
            self.add_mode_event_handler(target_config["switch"], self._upper_target_hit, target=target_name)

        self.publish_case_file_bonus_events("the_fly")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "REPEAT ROOF TARGETS SCORE 250K"),
            ("bigger_jackpots", "ROOF JACKPOTS BOOSTED"),
            ("more_time", "15 ROOF FLIPS"),
            ("safety_net", "BALL SAVE AT MODE START"),
            ("shot_assist", "FIRST JP ALSO SPOTS ANOTHER"),
        ])

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("the_fly_all_lights_off")
        self.machine.events.post("the_fly_saucers_needed")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self._show_message("SAUCERS OPEN GATE", "HIT ANY SAUCER")

    def mode_stop(self, **kwargs):
        self.delay.remove("the_fly_reenable_upper_flippers")
        self.delay.remove("the_fly_reset_for_next_attempt")
        self.machine.events.post("cmd_upper_flippers_enable")
        self.machine.events.post("the_fly_all_lights_off")
        self.machine.events.post("the_fly_stop_all_shows")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _configure_values(self):
        if self.has_case_file("bigger_jackpots"):
            self.target_values = self.BIGGER_TARGET_VALUES
            self.super_base_value = self.BIGGER_SUPER_BASE_VALUE
            self.flip_bonus_value = self.BIGGER_FLIP_BONUS_VALUE
        else:
            self.target_values = self.TARGET_VALUES
            self.super_base_value = self.SUPER_BASE_VALUE
            self.flip_bonus_value = self.FLIP_BONUS_VALUE

        self.flips_per_attempt = self.MORE_TIME_FLIPS if self.has_case_file("more_time") else self.BASE_FLIPS
        self.repeat_target_value = (
            self.MORE_JACKPOTS_REPEAT_VALUE if self.has_case_file("more_jackpots") else self.REPEAT_TARGET_VALUE
        )

    def _saucer_hit(self, **kwargs):
        if self.mode_done or self.roof_attempt_active:
            self.machine.events.post("clear_saucers")
            return

        self.gate_open = True
        self.machine.events.post("the_fly_saucers_off")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("clear_saucers")
        self._show_message("GATE OPEN", "GET TO THE ROOF")

    def _upper_entrance(self, **kwargs):
        if self.mode_done or self.roof_attempt_active or not self.gate_open:
            return

        self.gate_open = False
        self.roof_attempt_active = True
        self.flips_remaining = self.flips_per_attempt
        self.targets_hit = set()
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("the_fly_saucers_off")
        self.machine.events.post("the_fly_roof_attempt_started", flips=self.flips_remaining)
        self._light_targets_for_attempt()
        self._show_message("ROOF SWARM", f"{self.flips_remaining} FLIPS")

    def _upper_flipper_pressed(self, **kwargs):
        if self.mode_done or not self.roof_attempt_active:
            return

        self.flips_remaining = max(0, self.flips_remaining - 1)
        self.machine.events.post("the_fly_flips_changed", flips=self.flips_remaining)

        if self.flips_remaining <= 0 and len(self.targets_hit) < 3:
            self._fail_roof_attempt()

    def _upper_target_hit(self, target, **kwargs):
        if self.mode_done or not self.roof_attempt_active:
            return

        if target in self.targets_hit:
            self._award_jackpot_points(self.repeat_target_value)
            self._show_message("REPEAT TARGET", self._format_score(self.repeat_target_value))
            return

        self._collect_unique_target(target, assisted=False)

        if (
            self.has_case_file("shot_assist")
            and not self.shot_assist_used
            and self.roof_attempt_active
            and len(self.targets_hit) < 3
        ):
            self.shot_assist_used = True
            assist_target = self._first_unhit_target()
            if assist_target:
                self._collect_unique_target(assist_target, assisted=True)

    def _collect_unique_target(self, target, assisted=False):
        if target in self.targets_hit:
            return

        target_number = len(self.targets_hit) + 1
        self.targets_hit.add(target)

        if target_number < 3:
            points = self.target_values[target_number - 1]
            title = "ASSIST JP" if assisted else "JACKPOT"
        else:
            points = self.super_base_value + (self.flips_remaining * self.flip_bonus_value)
            title = "ASSIST SUPER" if assisted else "SUPER JACKPOT"

        self._award_jackpot_points(points)
        self.machine.events.post(self.TARGETS[target]["solid"])
        self.machine.events.post("the_fly_jackpot_collected", target=target, number=target_number, value=points)
        self._show_message(title, self._format_score(points), value=self.mode_points, event="show_mode_jackpot")

        if len(self.targets_hit) >= 3:
            self._complete_roof_attempt()

    def _complete_roof_attempt(self):
        if not self.roof_attempt_active:
            return

        self.roof_attempt_active = False
        self.rooftop_jackpots += 1
        self.machine.game.player["active_mode_major_hits"] = self.rooftop_jackpots
        self.machine.events.post("the_fly_roof_attempt_complete", count=self.rooftop_jackpots)

        if self.rooftop_jackpots >= self.ROOFTOP_JACKPOTS_TO_COMPLETE:
            self._complete_mode()
            return

        self._show_message("ROOF CLEARED", f"{self.rooftop_jackpots} / {self.ROOFTOP_JACKPOTS_TO_COMPLETE}")
        self.delay.add(name="the_fly_reset_for_next_attempt", ms=750, callback=self._reset_for_next_attempt)

    def _fail_roof_attempt(self):
        if not self.roof_attempt_active:
            return

        self.roof_attempt_active = False
        self.machine.events.post("the_fly_roof_attempt_failed")
        self.machine.events.post("cmd_upper_flippers_disable")
        self._show_message("OUT OF FLIPS", "UPPER FLIPPER DISABLED", seconds="4")
        self.delay.add(name="the_fly_reenable_upper_flippers", ms=self.FLIP_DISABLE_MS, callback=self._reenable_after_failed_attempt)

    def _reenable_after_failed_attempt(self):
        if self.mode_done:
            return
        self.machine.events.post("cmd_upper_flippers_enable")
        self._reset_for_next_attempt()

    def _reset_for_next_attempt(self):
        if self.mode_done:
            return
        self.gate_open = False
        self.roof_attempt_active = False
        self.flips_remaining = 0
        self.targets_hit = set()
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("the_fly_targets_off")
        self.machine.events.post("the_fly_saucers_needed")
        self._show_message("SAUCERS OPEN GATE", "HIT ANY SAUCER")

    def _upper_exit(self, **kwargs):
        # The mode does not depend on exits for normal flow, but this is a
        # harmless recovery path if the ball leaves the upper playfield after
        # flips have expired.
        if not self.roof_attempt_active and not self.mode_done:
            self.machine.events.post("cmd_upper_flippers_enable")

    def _vuk_hit(self, **kwargs):
        self.delay.add(name="the_fly_vuk_kick", ms=1500, callback=lambda: self.machine.events.post("up_kick"))

    def _light_targets_for_attempt(self):
        for target_name, target_config in self.TARGETS.items():
            if target_name in self.targets_hit:
                self.machine.events.post(target_config["solid"])
            else:
                self.machine.events.post(target_config["needed"])

    def _first_unhit_target(self):
        for target_name in ("left", "center", "right"):
            if target_name not in self.targets_hit:
                return target_name
        return None

    def _award_jackpot_points(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self.jackpot_hits += 1
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.jackpot_hits

    def _complete_mode(self):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("the_fly_targets_off")
        self.machine.events.post("the_fly_saucers_off")
        self._show_message("THE FLY", "MODE COMPLETE", value=self.mode_points, event="show_mode_jackpot")
        self.machine.events.post("the_fly_mode_complete")

    def _show_message(self, title, subtitle="", value="", seconds="", event="show_mode_message"):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
        )

    def _format_score(self, points):
        return "{:,}".format(int(points))
