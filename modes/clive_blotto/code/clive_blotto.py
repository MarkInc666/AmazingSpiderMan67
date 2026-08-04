import random

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class CliveBlotto(CaseFileMixin, Mode):
    """Spirit-Scope Containment.

    Drain the rising Blotto Meter with either spinner while clearing infected
    playfield areas. Clive is defeated when the meter is empty and no area is
    infected. If all six areas become infected at once, Blotto overruns the city.
    """

    MODE_KEY = "clive_blotto"
    DISPLAY_NAME = "Clive and Blotto"

    METER_MAX = 4
    METER_START = 3
    BASE_GROWTH_MS = 2_000
    MORE_TIME_GROWTH_MS = 3_000
    SPINNER_PAUSE_MS = 2_000

    BASE_SPINNER_SCORE = 25_000
    BIGGER_SPINNER_SCORE = 40_000
    BASE_CLEAR_SCORE = 150_000
    BIGGER_CLEAR_SCORE = 225_000
    BASE_COMPLETION_SCORE = 1_000_000
    BIGGER_COMPLETION_SCORE = 1_500_000
    BASE_EXTRA_JACKPOT = 250_000
    BIGGER_EXTRA_JACKPOT = 375_000

    AREA_SWITCHES = {
        "upper_left": [
            "s_leaf_next_to_1", "s_saucer_1", "s_saucer_2", "s_saucer_3",
            "s_upper_entrance_opto", "s_upper_exit_left_opto", "s_vuk_switch",
        ],
        "upper_right": [
            "s_above_star", "s_inlane_a", "s_inlane_b", "s_star_rollover",
            "s_trispinner_opto", "s_upper_exit_right_opto", "s_upper_target_center",
            "s_upper_target_left", "s_upper_target_right", "s_web_target_mid",
        ],
        "middle_left": [
            "s_above_spinner", "s_inlane_m_l", "s_left_drops_1", "s_left_drops_2",
            "s_left_drops_3", "s_left_drops_rubber", "s_left_drops_top_left_rubber",
            "s_left_drops_top_right_rubber", "s_pop_left", "s_web_spinner",
            "s_web_target_left",
        ],
        "middle_right": [
            "s_inlane_m_r", "s_mid_right_rubber", "s_pop_right", "s_right_drops_1",
            "s_right_drops_2", "s_right_drops_3", "s_right_drops_4",
            "s_right_drops_5", "s_right_drops_rubber", "s_right_drops_top_rubber",
        ],
        "lower_left": ["s_inlane_l", "s_outlane_l", "s_sling_l"],
        "lower_right": ["s_inlane_r", "s_outlane_r", "s_sling_r"],
    }

    AREA_LABELS = {
        "upper_left": "UPPER LEFT",
        "upper_right": "UPPER RIGHT",
        "middle_left": "MIDDLE LEFT",
        "middle_right": "MIDDLE RIGHT",
        "lower_left": "LOWER LEFT",
        "lower_right": "LOWER RIGHT",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.meter = self.METER_START
        self.infected = set()
        self.cleared_count = 0
        self.attack_count = 0
        self.mode_points = 0
        self.more_jackpots_collected = set()
        self.case_files = self.get_case_file_bonuses()
        self.shot_assist_available = self.has_case_file("shot_assist")

        self.growth_ms = (
            self.MORE_TIME_GROWTH_MS
            if self.has_case_file("more_time")
            else self.BASE_GROWTH_MS
        )
        self.spinner_score = (
            self.BIGGER_SPINNER_SCORE
            if self.has_case_file("bigger_jackpots")
            else self.BASE_SPINNER_SCORE
        )
        self.clear_score = (
            self.BIGGER_CLEAR_SCORE
            if self.has_case_file("bigger_jackpots")
            else self.BASE_CLEAR_SCORE
        )
        self.completion_score = (
            self.BIGGER_COMPLETION_SCORE
            if self.has_case_file("bigger_jackpots")
            else self.BASE_COMPLETION_SCORE
        )
        self.extra_jackpot = (
            self.BIGGER_EXTRA_JACKPOT
            if self.has_case_file("bigger_jackpots")
            else self.BASE_EXTRA_JACKPOT
        )

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0

        for area_name, switches in self.AREA_SWITCHES.items():
            for switch_name in switches:
                # Spinners get their meter action first; an infected spinner area
                # may also be cleared by the same physical hit.
                self.add_mode_event_handler(
                    f"{switch_name}_active", self._area_switch_hit, area=area_name
                )

        self.add_mode_event_handler("s_web_spinner_active", self._spinner_hit)
        self.add_mode_event_handler("s_trispinner_opto_active", self._spinner_hit)
        self.add_mode_event_handler("clive_blotto_complete_request", self._complete_mode)
        self.add_mode_event_handler("clive_blotto_fail_request", self._fail_mode)

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.publish_active_case_file_helpers([
            ("more_jackpots", "FIRST CLEAR IN EACH AREA AWARDS BLOTTO JACKPOT"),
            ("bigger_jackpots", "BIGGER SPINNER, CLEAR, AND FINAL VALUES"),
            ("more_time", "METER RISES EVERY 3 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST CLEAR WITH 2+ INFECTED CLEARS ANOTHER"),
        ])

        self.machine.events.post("clive_blotto_mode_lighting_start")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self._publish_status()
        self._publish_meter_lighting()
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="SPIRIT-SCOPE CONTAINMENT",
            message_mode_subtitle="DRAIN METER - CLEAR BLOTTO",
            message_mode_value="75%",
            reminder=True,
        )
        self._schedule_growth()

    def mode_stop(self, **kwargs):
        self.delay.remove("clive_blotto_growth")
        self.delay.remove("clive_blotto_completion_hold")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("clive_blotto_restore_all_lights")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _schedule_growth(self):
        if self.mode_done:
            return
        self.delay.add(
            name="clive_blotto_growth",
            ms=self.growth_ms,
            callback=self._meter_growth_tick,
        )

    def _meter_growth_tick(self, **kwargs):
        if self.mode_done:
            return
        self.meter = min(self.METER_MAX, self.meter + 1)
        if self.meter >= self.METER_MAX:
            self._infect_random_area()
            self.meter = 0
        self._publish_status()
        self._publish_meter_lighting()
        if not self.mode_done:
            self._schedule_growth()

    def _spinner_hit(self, **kwargs):
        if self.mode_done:
            return
        self.delay.remove("clive_blotto_growth")
        self.meter = max(0, self.meter - 1)
        self._score(self.spinner_score)
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="METER DOWN",
            message_mode_subtitle=f"{self._meter_percent()}%",
            message_mode_value=f"{self.spinner_score:,}",
        )
        self.machine.events.post("reset_mode_message_reminder")
        self._publish_status()
        self._publish_meter_lighting()
        if self._check_completion():
            return
        self.delay.add(
            name="clive_blotto_growth",
            ms=self.SPINNER_PAUSE_MS,
            callback=self._meter_growth_tick,
        )

    def _infect_random_area(self):
        clean = [area for area in self.AREA_SWITCHES if area not in self.infected]
        if not clean:
            self._fail_mode(reason="BLOTTO OVERRUN")
            return
        area = random.choice(clean)
        self.infected.add(area)
        self.attack_count += 1
        player = self.machine.game.player
        player["active_mode_major_hits"] = self.attack_count
        self.machine.events.post("clive_blotto_meter_full_flash")
        self.machine.events.post(f"clive_blotto_infect_{area}")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="BLOTTO SPREADS",
            message_mode_subtitle=self.AREA_LABELS[area],
        )
        self.machine.events.post("reset_mode_message_reminder")
        self._publish_status()
        if len(self.infected) >= len(self.AREA_SWITCHES):
            self._fail_mode(reason="BLOTTO OVERRUN")

    def _area_switch_hit(self, area=None, **kwargs):
        if self.mode_done or not area or area not in self.infected:
            return
        self._clear_area(area, assisted=False)

        if self.shot_assist_available and len(self.infected) >= 1:
            # The assist only triggers if there were at least two infected areas
            # before the successful hit. After clearing the hit area, at least one
            # infected area remaining proves that condition was met.
            self.shot_assist_available = False
            assisted_area = random.choice(list(self.infected))
            self._clear_area(assisted_area, assisted=True)
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="SHOT ASSIST",
                message_mode_subtitle=f"{self.AREA_LABELS[assisted_area]} CLEARED",
            )

        self._check_completion()

    def _clear_area(self, area, assisted=False):
        if area not in self.infected:
            return
        self.infected.remove(area)
        self.cleared_count += 1
        self._score(self.clear_score)

        player = self.machine.game.player
        player["active_mode_hits"] = self.cleared_count
        self.machine.events.post(f"clive_blotto_clear_{area}")
        self.machine.events.post("clive_blotto_area_clear_flash")
        self.machine.events.post("reset_mode_message_reminder")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="AREA CLEARED",
            message_mode_subtitle=self.AREA_LABELS[area],
            message_mode_value=f"{self.clear_score:,}",
        )

        if self.has_case_file("more_jackpots") and area not in self.more_jackpots_collected:
            self.more_jackpots_collected.add(area)
            self._score(self.extra_jackpot)
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="BLOTTO JACKPOT",
                message_mode_subtitle=self.AREA_LABELS[area],
                message_mode_value=f"{self.extra_jackpot:,}",
            )

        self._publish_status()

    def _check_completion(self):
        if self.mode_done or self.meter != 0 or self.infected:
            return False
        self._score(self.completion_score)
        self.mode_done = True
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("clive_blotto_completion_lights")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SPIRIT-SCOPE RESTORED",
            message_mode_subtitle="BLOTTO CONTAINED",
            message_mode_value=f"{self.completion_score:,}",
        )
        self.delay.add(
            name="clive_blotto_completion_hold",
            ms=2_000,
            callback=self._post_completion,
        )
        return True

    def _post_completion(self, **kwargs):
        self.machine.events.post("clive_blotto_mode_complete")

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.meter = 0
        self.infected.clear()
        self._check_completion()

    def _fail_mode(self, reason="BLOTTO OVERRUN", **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=reason,
            message_mode_subtitle=f"{len(self.infected)} OF 6 INFECTED",
        )
        self.machine.events.post("clive_blotto_mode_failed")

    def _publish_status(self):
        player = self.machine.game.player
        player["active_mode_hits"] = self.cleared_count
        player["active_mode_major_hits"] = self.attack_count
        self.machine.events.post(
            "set_mode_status",
            title=f"BLOTTO METER {self._meter_percent()}%",
            value=f"INFECTED {len(self.infected)}/6",
        )

    def _publish_meter_lighting(self):
        percent = self._meter_percent()
        if percent < 50:
            event = "clive_blotto_meter_low"
        elif percent < 75:
            event = "clive_blotto_meter_medium"
        else:
            event = "clive_blotto_meter_high"
        self.machine.events.post(event)

    def _meter_percent(self):
        return int((self.meter / self.METER_MAX) * 100)

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        player["blotto_bonus"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points
