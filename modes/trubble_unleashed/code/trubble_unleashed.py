from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin

import random

"""
    "title": "TRUBBLE UNLEASHED",
    "intro_1": "Three shots look the same.",
    "intro_2": "Spinner reveals the good shot.",
    "intro_3": "Seven wrong choices and she escapes.",
    "summary_title_complete": "TRUBBLE UNLEASHED DEFEATED",
    "summary_title_failed": "TRUBBLE UNLEASHED ESCAPED",
    "stat_1_label": "GOOD SHOTS",
    "stat_1_var": "trubble_unleashed_correct_shots",
    "stat_2_label": "WRONG SHOTS",
    "stat_2_var": "trubble_unleashed_incorrect_shots",
    "points_var": "trubble_unleashed_mode_points",
    "completed_var": "trubble_unleashed_completed",
"""


class TrubbleUnleashed(CaseFileMixin, Mode):
    BASE_ROUNDS = 7
    EXTRA_ROUNDS = 2
    MAX_INCORRECT_SHOTS = 7

    BASE_JACKPOT_VALUE = 100_000
    JACKPOT_STEP = 50_000
    BIGGER_BASE_JACKPOT_VALUE = 150_000
    BIGGER_JACKPOT_STEP = 75_000
    BAD_SHOT_SCORE = 10_000

    NORMAL_REVEAL_MS = 750
    MORE_TIME_REVEAL_MS = 2_000

    SHOT_GROUPS = [
        "left_web",
        "center_web",
        "upper_spinner",
        "upper_target_left",
        "upper_target_center",
        "upper_target_right",
        "left_drops",
        "right_drops",
        "pops",
    ]

    UPPER_GROUPS = {
        "upper_spinner",
        "upper_target_left",
        "upper_target_center",
        "upper_target_right",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.round_number = 0
        self.rounds_to_play = self.BASE_ROUNDS
        self.correct_shots = 0
        self.incorrect_shots = 0
        self.mode_points = 0
        self.current_groups = []
        self.correct_group = None
        self.first_round_all_good = False
        self.reveal_ms = self.NORMAL_REVEAL_MS
        self.jackpot_value = self.BASE_JACKPOT_VALUE
        self.jackpot_step = self.JACKPOT_STEP

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("trubble_unleashed")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "TWO EXTRA TRUBBLE ROUNDS"),
            ("bigger_jackpots", "BIGGER TRUBBLE JACKPOTS"),
            ("more_time", "LONGER SPINNER REVEAL"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST ROUND ALL GOOD"),
        ])

        for group in self.SHOT_GROUPS:
            self.add_mode_event_handler(f"trubble_unleashed_{group}_hit", self._shot_hit, group=group)

        self.add_mode_event_handler("trubble_unleashed_spinner_reveal", self._reveal_current_round)
        self.add_mode_event_handler("trubble_unleashed_spinner_switch", self._spinner_switch)
        self.add_mode_event_handler("trubble_unleashed_complete_request", self._complete_mode)
        self.add_mode_event_handler("trubble_unleashed_fail_request", self._complete_mode)

        self._sync_player_vars()
        self.machine.events.post("trubble_unleashed_startup_complete")
        self.machine.events.post("show_mode_message_long", message_mode_title="TRUBBLE UNLEASHED", message_mode_subtitle="FIND THE CORRECT SHOT")
        self._start_next_round()

    def mode_stop(self, **kwargs):
        self.delay.remove("trubble_unleashed_hide_reveal")
        self.machine.events.post("trubble_unleashed_all_lights_off")
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        if self.has_case_file("more_jackpots"):
            self.rounds_to_play += self.EXTRA_ROUNDS

        if self.has_case_file("bigger_jackpots"):
            self.jackpot_value = self.BIGGER_BASE_JACKPOT_VALUE
            self.jackpot_step = self.BIGGER_JACKPOT_STEP

        if self.has_case_file("more_time"):
            self.reveal_ms = self.MORE_TIME_REVEAL_MS

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.first_round_all_good = True

    def _spinner_switch(self, **kwargs):
        if self._inactive():
            return

        self._reveal_current_round()

        # The upper spinner may also be one of the three hidden choices.
        self._shot_hit(group="upper_spinner")

    def _start_next_round(self):
        if self._inactive():
            return

        self.delay.remove("trubble_unleashed_hide_reveal")

        if self.round_number >= self.rounds_to_play:
            self._complete_mode()
            return

        self.round_number += 1
        self.current_groups = random.sample(self.SHOT_GROUPS, 3)
        self.correct_group = random.choice(self.current_groups)

        self._sync_player_vars()
        self.machine.events.post(
            "trubble_unleashed_round_started",
            round=self.round_number,
            total_rounds=self.rounds_to_play,
            jackpot=self.jackpot_value,
            incorrect=self.incorrect_shots,
        )
        self.machine.events.post("show_mode_message", message_mode_title="TROUBLE ROUND", message_mode_subtitle=f"{self.round_number} OF {self.rounds_to_play}", message_mode_value=self.jackpot_value)
        self._show_hidden_round()
        self._update_rooftop_diverter()

    def _shot_hit(self, group=None, **kwargs):
        if self._inactive() or group not in self.current_groups:
            return

        all_good = self.first_round_all_good and self.round_number == 1
        is_correct = all_good or group == self.correct_group

        self.delay.remove("trubble_unleashed_hide_reveal")

        if is_correct:
            self._collect_jackpot(group)
        else:
            self._collect_bad_shot(group)

        if self.mode_done:
            return

        self.machine.events.post("trubble_unleashed_all_lights_off")
        self._start_next_round()

    def _collect_jackpot(self, group):
        self._score(self.jackpot_value)
        self.correct_shots += 1
        self.machine.events.post(
            "trubble_unleashed_correct_shot",
            group=group,
            value=self.jackpot_value,
            correct_shots=self.correct_shots,
        )
        self.machine.events.post(f"trubble_unleashed_correct_{group}")
        self.machine.events.post("show_mode_jackpot", message_mode_title="CORRECT SHOT", message_mode_subtitle=group.replace("_", " ").upper(), message_mode_value=self.jackpot_value)
        self.jackpot_value += self.jackpot_step
        self._sync_player_vars()

    def _collect_bad_shot(self, group):
        self._score(self.BAD_SHOT_SCORE)
        self.incorrect_shots += 1
        self.machine.events.post(
            "trubble_unleashed_incorrect_shot",
            group=group,
            incorrect_shots=self.incorrect_shots,
            max_incorrect=self.MAX_INCORRECT_SHOTS,
        )
        self.machine.events.post(f"trubble_unleashed_incorrect_{group}")
        self.machine.events.post("show_mode_message", message_mode_title="WRONG SHOT", message_mode_subtitle=f"TROUBLE {self.incorrect_shots} / {self.MAX_INCORRECT_SHOTS}")
        self._sync_player_vars()

        if self.incorrect_shots >= self.MAX_INCORRECT_SHOTS:
            self._fail_mode()

    def _reveal_current_round(self, **kwargs):
        if self._inactive() or not self.current_groups:
            return

        self.machine.events.post("trubble_unleashed_all_lights_off")
        self.machine.events.post("show_mode_message", message_mode_title="SPINNER REVEAL", message_mode_subtitle="WATCH CLOSELY")

        all_good = self.first_round_all_good and self.round_number == 1
        for group in self.current_groups:
            if all_good or group == self.correct_group:
                self.machine.events.post(f"trubble_unleashed_reveal_good_{group}")
            else:
                self.machine.events.post(f"trubble_unleashed_reveal_bad_{group}")

        self.delay.remove("trubble_unleashed_hide_reveal")
        self.delay.add(
            name="trubble_unleashed_hide_reveal",
            ms=self.reveal_ms,
            callback=self._show_hidden_round,
        )

    def _show_hidden_round(self, **kwargs):
        if self._inactive() or not self.current_groups:
            return

        self.machine.events.post("trubble_unleashed_all_lights_off")
        for group in self.current_groups:
            self.machine.events.post(f"trubble_unleashed_hidden_{group}")

    def _update_rooftop_diverter(self):
        if any(group in self.UPPER_GROUPS for group in self.current_groups):
            self.machine.events.post("rooftop_diverter_open")
        else:
            self.machine.events.post("rooftop_diverter_close")

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player if self.machine.game else None
        if player:
            player["trubble_unleashed_completed"] = 1
        self.machine.events.post("trubble_unleashed_all_lights_off")
        self.machine.events.post("show_mode_message_long", message_mode_title="TRUBBLE UNLEASHED DEFEATED", message_mode_subtitle="SEQUENCE COMPLETE")
        self.machine.events.post("trubble_unleashed_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player if self.machine.game else None
        if player:
            player["trubble_unleashed_completed"] = 1
        self.machine.events.post("trubble_unleashed_all_lights_off")
        self.machine.events.post("show_mode_message_long", message_mode_title="TRUBBLE UNLEASHED ESCAPES", message_mode_subtitle="TOO MUCH TROUBLE")
        self.machine.events.post("trubble_unleashed_mode_complete")

    def _score(self, points):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return
        player["score"] += points
        self.mode_points += points
        self._sync_player_vars()

    def _sync_player_vars(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return
        player["trubble_unleashed_mode_points"] = self.mode_points
        player["trubble_unleashed_round"] = self.round_number
        player["trubble_unleashed_total_rounds"] = self.rounds_to_play
        player["trubble_unleashed_correct_shots"] = self.correct_shots
        player["trubble_unleashed_incorrect_shots"] = self.incorrect_shots
        player["trubble_unleashed_next_jackpot"] = self.jackpot_value

    def _inactive(self):
        if self.mode_done:
            return True
        if self.machine.game.player["villain_mode_in_summary"] is True:
            return True
        return False
