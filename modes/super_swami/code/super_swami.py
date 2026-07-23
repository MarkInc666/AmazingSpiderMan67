from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class SuperSwami(CaseFileMixin, Mode):
    MODE_KEY = "super_swami"
    DISPLAY_NAME = "Super Swami"
    BASE_TIME = 40
    MORE_TIME_TIME = 50
    BASE_VALUE = 100_000
    BIGGER_BASE_VALUE = 200_000
    VALUE_STEP = 50_000
    MORE_JACKPOTS_VALUE = 500_000

    AREA_SWITCHES = {
        "upper_left": ['s_leaf_next_to_1', 's_saucer_1', 's_saucer_2', 's_saucer_3', 's_upper_entrance_opto', 's_upper_exit_left_opto', 's_vuk_switch'],
        "upper_right": ['s_above_star', 's_inlane_a', 's_inlane_b', 's_star_rollover', 's_trispinner_opto', 's_upper_exit_right_opto', 's_upper_target_center', 's_upper_target_left', 's_upper_target_right', 's_web_target_mid', 's_web_target_top'],
        "middle_left": ['s_above_spinner', 's_inlane_m_l', 's_left_drops_1', 's_left_drops_2', 's_left_drops_3', 's_left_drops_rubber', 's_left_drops_top_left_rubber', 's_left_drops_top_right_rubber', 's_pop_left', 's_web_spinner', 's_web_target_left'],
        "middle_right": ['s_inlane_m_r', 's_mid_right_rubber', 's_pop_right', 's_right_drops_1', 's_right_drops_2', 's_right_drops_3', 's_right_drops_4', 's_right_drops_5', 's_right_drops_rubber', 's_right_drops_top_rubber'],
        "lower_left": ['s_inlane_l', 's_outlane_l', 's_sling_l'],
        "lower_right": ['s_inlane_r', 's_outlane_r', 's_sling_r'],
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
        self.restored = set()
        self.mode_points = 0
        self.case_files = self.get_case_file_bonuses()
        self.seconds_left = self.MORE_TIME_TIME if self.has_case_file("more_time") else self.BASE_TIME
        self.base_value = self.BIGGER_BASE_VALUE if self.has_case_file("bigger_jackpots") else self.BASE_VALUE
        self.shot_assist_available = self.has_case_file("shot_assist")
        self.final_jackpot_lit = False

        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player[f"{self.MODE_KEY}_state"] = 1

        for area_name, switches in self.AREA_SWITCHES.items():
            for switch_name in switches:
                self.add_mode_event_handler(f"{switch_name}_active", self._area_switch_hit, area=area_name)

        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._fail_mode)

        self.machine.events.post("super_swami_dim_city")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.publish_active_case_file_helpers([
            ("more_jackpots", "BLACKOUT JACKPOT AT VUK"),
            ("bigger_jackpots", "RESTORE VALUES START AT 200K"),
            ("more_time", "50 SECOND CITY TIMER"),
            ("safety_net", "BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST AREA SPOTS ANOTHER"),
        ])
        self.machine.events.post("show_mode_message", message_mode_title="RESTORE NEW YORK", message_mode_subtitle=f"6 AREAS - {self.seconds_left} SECONDS", reminder=True)
        self.delay.add(name="super_swami_tick", ms=1000, callback=self._timer_tick)

    def mode_stop(self, **kwargs):
        self.delay.remove("super_swami_tick")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("super_swami_restore_all_lights")
        self.machine.events.post("close_gate")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _area_switch_hit(self, area=None, **kwargs):
        if self.mode_done or self.final_jackpot_lit or not area or area in self.restored:
            return
        self._restore_area(area, scored=True)
        if self.shot_assist_available and len(self.restored) < 6:
            self.shot_assist_available = False
            other = next(name for name in self.AREA_SWITCHES if name not in self.restored)
            self._restore_area(other, scored=False)
            self.machine.events.post("show_mode_message", message_mode_title="SHOT ASSIST", message_mode_subtitle=f"{self.AREA_LABELS[other]} RESTORED")
        self._check_completion()

    def _restore_area(self, area, scored):
        if area in self.restored:
            return
        value = self.base_value + self.VALUE_STEP * len(self.restored)
        self.restored.add(area)
        if scored:
            self._score(value)
        player = self.machine.game.player
        player["active_mode_hits"] = len(self.restored)
        self.machine.events.post(f"super_swami_restore_{area}")
        self.machine.events.post("reset_mode_message_reminder")
        self.machine.events.post("show_mode_message", message_mode_title=f"{self.AREA_LABELS[area]} RESTORED", message_mode_subtitle=f"{value // 1000}K - {len(self.restored)} OF 6")

    def _check_completion(self):
        if len(self.restored) < 6:
            return
        if self.has_case_file("more_jackpots"):
            self.final_jackpot_lit = True
            self.machine.events.post("open_gate")
            self.machine.events.post("super_swami_light_vuk")
            self.machine.events.post("show_mode_message", message_mode_title="BLACKOUT JACKPOT", message_mode_subtitle="SHOOT THE VUK", reminder=True)
        else:
            self._complete_mode()

    def _vuk_hit(self, **kwargs):
        if not self.final_jackpot_lit or self.mode_done:
            return
        self._score(self.MORE_JACKPOTS_VALUE)
        self.machine.events.post("show_mode_message", message_mode_title="BLACKOUT JACKPOT", message_mode_subtitle="500K")
        self.machine.events.post("clear_vuk")
        self._complete_mode()

    def _timer_tick(self, **kwargs):
        if self.mode_done:
            return
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self._fail_mode()
            return
        self.machine.events.post("super_swami_timer_changed", seconds=self.seconds_left)
        self.delay.add(name="super_swami_tick", ms=1000, callback=self._timer_tick)

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("super_swami_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.events.post("show_mode_message", message_mode_title="NEW YORK STAYS DARK", message_mode_subtitle=f"{len(self.restored)} OF 6 RESTORED")
        self.machine.events.post("super_swami_mode_failed")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points
        player["super_swami_bonus"] += points
