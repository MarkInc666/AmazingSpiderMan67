"""The Plutonians villain mode.

Current coded rules:
- All six Super-Swami-style playfield areas begin frozen; roof access remains
  open for the mode. A qualifying hit thaws a frozen area at any time.
- While active, the freeze ray fires every 12 seconds and randomly refreezes
  one currently thawed area.
- Any upper-target hit blocks or resets the ray for 20 seconds (25 with More
  Time). When the block expires, a new 12-second firing cycle begins.
- Thaws score 100K (150K with Bigger), upper targets score 50K (75K with
  Bigger), and thawing all six simultaneously awards 1M (1.5M with Bigger).
- More Jackpots awards one Space Warp Jackpot per upper-playfield entrance;
  Shot Assist adds one extra thaw on the first successful thaw; Safety Net
  starts a 10-second ball save.
"""

import random

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Plutonians(CaseFileMixin, Mode):
    """Six-area freeze/thaw control mode for The Plutonians."""

    MODE_KEY = "plutonians"
    DISPLAY_NAME = "The Plutonians"

    FREEZE_CYCLE_SECONDS = 12
    BLOCK_SECONDS = 20
    MORE_TIME_BLOCK_SECONDS = 25
    VICTORY_HOLD_MS = 2000

    THAW_VALUE = 100_000
    BIGGER_THAW_VALUE = 150_000
    TARGET_VALUE = 50_000
    BIGGER_TARGET_VALUE = 75_000
    COMPLETION_VALUE = 1_000_000
    BIGGER_COMPLETION_VALUE = 1_500_000
    MORE_JACKPOTS_VALUE = 500_000
    BIGGER_MORE_JACKPOTS_VALUE = 750_000

    # Reuse the established Super Swami six-area map.
    AREA_SWITCHES = {
        "upper_left": (
            "s_leaf_next_to_1", "s_saucer_1", "s_saucer_2", "s_saucer_3",
            "s_upper_entrance_opto", "s_upper_exit_left_opto", "s_vuk_switch",
        ),
        "upper_right": (
            "s_above_star", "s_inlane_a", "s_inlane_b", "s_star_rollover",
            "s_trispinner_opto", "s_upper_exit_right_opto", "s_upper_target_center",
            "s_upper_target_left", "s_upper_target_right", "s_web_target_mid",
        ),
        "middle_left": (
            "s_above_spinner", "s_inlane_m_l", "s_left_drops_1", "s_left_drops_2",
            "s_left_drops_3", "s_left_drops_rubber", "s_left_drops_top_left_rubber",
            "s_left_drops_top_right_rubber", "s_pop_left", "s_web_spinner",
            "s_web_target_left",
        ),
        "middle_right": (
            "s_inlane_m_r", "s_mid_right_rubber", "s_pop_right", "s_right_drops_1",
            "s_right_drops_2", "s_right_drops_3", "s_right_drops_4",
            "s_right_drops_5", "s_right_drops_rubber", "s_right_drops_top_rubber",
        ),
        "lower_left": ("s_inlane_l", "s_outlane_l", "s_sling_l"),
        "lower_right": ("s_inlane_r", "s_outlane_r", "s_sling_r"),
    }

    AREA_LABELS = {
        "upper_left": "UPPER LEFT",
        "upper_right": "UPPER RIGHT",
        "middle_left": "MID LEFT",
        "middle_right": "MID RIGHT",
        "lower_left": "BOTTOM LEFT",
        "lower_right": "BOTTOM RIGHT",
    }

    UPPER_TARGETS = (
        "s_upper_target_left",
        "s_upper_target_center",
        "s_upper_target_right",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.mode_done = False
        self.thawed = set()
        self.mode_points = 0
        self.total_thaws = 0
        self.freeze_ray_blockers = 0

        self.case_files = self.get_case_file_bonuses()
        self.block_duration = (
            self.MORE_TIME_BLOCK_SECONDS
            if self.has_case_file("more_time")
            else self.BLOCK_SECONDS
        )
        self.thaw_value = (
            self.BIGGER_THAW_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.THAW_VALUE
        )
        self.target_value = (
            self.BIGGER_TARGET_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.TARGET_VALUE
        )
        self.completion_value = (
            self.BIGGER_COMPLETION_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.COMPLETION_VALUE
        )
        self.upper_jackpot_value = (
            self.BIGGER_MORE_JACKPOTS_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.MORE_JACKPOTS_VALUE
        )
        self.shot_assist_available = self.has_case_file("shot_assist")
        self.more_jackpots_enabled = self.has_case_file("more_jackpots")
        self.upper_jackpot_available = False

        self.ray_blocked = False
        self.ray_seconds = self.FREEZE_CYCLE_SECONDS

        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["active_mode_stat_1"] = 0
        player["active_mode_stat_2"] = 0
        player[f"{self.MODE_KEY}_state"] = 1

        # Register target behavior before area behavior because upper targets do both.
        for switch_name in self.UPPER_TARGETS:
            self.add_mode_event_handler(f"{switch_name}_active", self._upper_target_hit)

        self.add_mode_event_handler("s_upper_entrance_opto_active", self._upper_entered)
        self.add_mode_event_handler("s_upper_exit_left_opto_active", self._upper_exited)
        self.add_mode_event_handler("s_upper_exit_right_opto_active", self._upper_exited)

        for area_name, switches in self.AREA_SWITCHES.items():
            for switch_name in switches:
                self.add_mode_event_handler(
                    f"{switch_name}_active",
                    self._area_switch_hit,
                    area=area_name,
                    switch_name=switch_name,
                )

        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._fail_mode)

        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("plutonians_all_areas_frozen")
        self.machine.events.post("plutonians_ray_active")

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.publish_active_case_file_helpers([
            ("more_jackpots", "500K JACKPOT ONCE PER ROOF ENTRY"),
            ("bigger_jackpots", "THAWS 150K - CONTROL 1.5M"),
            ("more_time", "FREEZE BLOCKED FOR 25 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE"),
            ("shot_assist", "FIRST THAW ALSO THAWS ANOTHER AREA"),
        ])

        self.machine.events.post(
            "show_mode_message",
            message_mode_title="THAW ALL 6 AREAS",
            message_mode_subtitle="HIT TARGETS TO BLOCK RAY",
            reminder=True,
        )
        self._update_status()
        self.delay.add(name="plutonians_ray_tick", ms=1000, callback=self._ray_tick)

    def mode_stop(self, **kwargs):
        self.delay.remove("plutonians_ray_tick")
        self.delay.remove("plutonians_victory_hold")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("plutonians_clear_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _area_switch_hit(self, area=None, switch_name=None, **kwargs):
        if self.mode_done or not area or area in self.thawed:
            return

        self._thaw_area(area, announce=True)

        if self.shot_assist_available and len(self.thawed) < len(self.AREA_SWITCHES):
            self.shot_assist_available = False
            remaining = [name for name in self.AREA_SWITCHES if name not in self.thawed]
            assisted = random.choice(remaining)
            self._thaw_area(assisted, announce=False)
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="SHOT ASSIST",
                message_mode_subtitle=f"{self.AREA_LABELS[assisted]} THAWED",
                message_mode_value=self.thaw_value,
            )

        if (
            len(self.thawed) >= len(self.AREA_SWITCHES)
            and str(switch_name).startswith("s_saucer_")
        ):
            self.machine.events.post("villain_summary_hold_saucer_until_done")
        self._check_completion()

    def _thaw_area(self, area, announce=True):
        if area in self.thawed or self.mode_done:
            return

        self.thawed.add(area)
        self.total_thaws += 1
        self._score(self.thaw_value)
        self.machine.events.post(f"plutonians_thaw_{area}")
        self.machine.events.post("reset_mode_message_reminder")
        self._sync_vars()

        if announce:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="AREA THAWED",
                message_mode_subtitle=f"{self.AREA_LABELS[area]} - {len(self.thawed)} OF 6",
                message_mode_value=self.thaw_value,
            )

    def _upper_target_hit(self, **kwargs):
        if self.mode_done:
            return

        self.freeze_ray_blockers += 1
        self._score(self.target_value)
        self.ray_blocked = True
        self.ray_seconds = self.block_duration
        self.machine.events.post("plutonians_ray_blocked")
        self.machine.events.post("reset_mode_message_reminder")

        if self.more_jackpots_enabled and self.upper_jackpot_available:
            self.upper_jackpot_available = False
            self._score(self.upper_jackpot_value)
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="SPACE WARP JACKPOT",
                message_mode_subtitle="UPPER TARGET",
                message_mode_value=self.upper_jackpot_value,
            )
        else:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="FREEZE RAY BLOCKED",
                message_mode_subtitle=f"{self.block_duration} SECONDS",
                message_mode_value=self.target_value,
            )

        self._sync_vars()
        self._update_status()

    def _upper_entered(self, **kwargs):
        if self.mode_done:
            return
        self.upper_jackpot_available = self.more_jackpots_enabled

    def _upper_exited(self, **kwargs):
        self.upper_jackpot_available = False

    def _ray_tick(self, **kwargs):
        if self.mode_done:
            return

        self.ray_seconds -= 1

        if self.ray_seconds <= 0:
            if self.ray_blocked:
                self.ray_blocked = False
                self.ray_seconds = self.FREEZE_CYCLE_SECONDS
                self.machine.events.post("plutonians_ray_active")
            else:
                self._fire_freeze_ray()
                if self.mode_done:
                    return
                self.ray_seconds = self.FREEZE_CYCLE_SECONDS

        self._update_status()
        self.delay.add(name="plutonians_ray_tick", ms=1000, callback=self._ray_tick)

    def _fire_freeze_ray(self):
        if not self.thawed:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="FREEZE RAY FIRED",
                message_mode_subtitle="NO THAWED AREA",
            )
            return

        area = random.choice(tuple(self.thawed))
        self.thawed.remove(area)
        self.machine.events.post(f"plutonians_freeze_{area}")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="AREA REFROZEN",
            message_mode_subtitle=self.AREA_LABELS[area],
        )
        self._sync_vars()

    def _update_status(self):
        if self.mode_done:
            return
        if self.ray_blocked:
            title = "HIT AREAS TO THAW"
            value = f"FREEZE BLOCKED {self.ray_seconds}"
        else:
            title = "HIT TARGETS TO BLOCK RAY"
            value = f"FREEZE IN {self.ray_seconds}"
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _check_completion(self):
        if self.mode_done or len(self.thawed) < len(self.AREA_SWITCHES):
            return

        # Stop the ray immediately; the sixth thaw cannot be undone.
        self.mode_done = True
        self.delay.remove("plutonians_ray_tick")
        self.ray_seconds = 0
        self._score(self.completion_value)
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("plutonians_control_repaired")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SPACE WARP CONTROL",
            message_mode_subtitle="REPAIRED",
            message_mode_value=self.completion_value,
        )
        self.delay.add(
            name="plutonians_victory_hold",
            ms=self.VICTORY_HOLD_MS,
            callback=self._finish_victory,
        )

    def _finish_victory(self, **kwargs):
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("plutonians_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.events.post("plutonians_mode_failed")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.total_thaws
        player["active_mode_stat_2"] = self.freeze_ray_blockers
