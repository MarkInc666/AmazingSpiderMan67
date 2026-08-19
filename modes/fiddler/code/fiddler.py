import random
from functools import partial

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Fiddler(CaseFileMixin, Mode):
    """Fiddler: repeat increasingly long light-and-violin patterns."""

    MODE_KEY = "fiddler"
    DISPLAY_NAME = "FIDDLER"
    DEMO_NOTE_MS = 2_000
    STAGE_DELAY_MS = 2_000
    BASE_REMINDER_MS = 14_000
    MORE_TIME_REMINDER_MS = 8_000

    SHOTS = ("left_web", "left_bank", "center_web", "right_bank")
    SHOT_LABELS = {
        "left_web": "LEFT WEB",
        "left_bank": "LEFT BANK",
        "center_web": "CENTER WEB",
        "right_bank": "RIGHT BANK",
    }
    NOTE_EVENTS = {
        "left_web": "play_note_1",
        "left_bank": "play_note_2",
        "center_web": "play_note_3",
        "right_bank": "play_note_4",
    }
    ROUND_VALUES = {
        1: (100_000,),
        2: (200_000, 300_000),
        3: (400_000, 500_000, 600_000),
        4: (700_000, 800_000, 900_000, 1_000_000),
    }

    DROP_TARGETS = (
        "dt_left_1", "dt_left_2", "dt_left_3",
        "dt_right_1", "dt_right_2", "dt_right_3", "dt_right_4", "dt_right_5",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.mode_points = 0
        self.round_number = 0
        self.sequence = []
        self.expected_index = 0
        self.demonstrating = False
        self.shot_assist_used = False
        self.max_round = 4 if self.has_case_file("more_jackpots") else 3
        self.reminder_ms = (
            self.MORE_TIME_REMINDER_MS
            if self.has_case_file("more_time")
            else self.BASE_REMINDER_MS
        )
        self.bigger_increment = 100_000 if self.has_case_file("bigger_jackpots") else 0

        for shot in self.SHOTS:
            self.add_mode_event_handler(
                f"fiddler_{shot}_hit", partial(self._shot_hit, shot=shot)
            )

        player = self.machine.game.player
        player["fiddler_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_stat_2"] = 0
        player["active_mode_stat_1"] = 0
        player["fiddler_note"] = 0
        player["fiddler_notes_completed"] = 0
        player["fiddler_notes_required"] = 0
        player["fiddler_shot_assist_used"] = 0

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "FOUR-NOTE ENCORE ROUND ADDED"),
            ("bigger_jackpots", "+100,000 PER CORRECT NOTE"),
            ("more_time", "PATTERN REPEATS EVERY 8 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST WRONG SHOT PLAYS CORRECT NOTE"),
        ])

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("fiddler_all_notes_off")
        self._force_drop_banks_down()
        self._show_message("SIMON SAYS", "WATCH THE NOTES")
        self.delay.add(name="fiddler_first_round", ms=750, callback=self._start_next_round)
        self._sync_vars()

    def mode_stop(self, **kwargs):
        self._clear_delays()
        self.clear_active_case_file_helpers()
        self.machine.events.post("fiddler_all_notes_off")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        super().mode_stop(**kwargs)

    def _force_drop_banks_down(self):
        for index, target_name in enumerate(self.DROP_TARGETS):
            self.delay.add(
                name=f"fiddler_knockdown_{target_name}",
                ms=100 + (index * 100),
                callback=partial(self._knockdown_target, target_name=target_name),
            )

    def _knockdown_target(self, target_name=None):
        if self.mode_done or not target_name:
            return
        try:
            target = self.machine.drop_targets[target_name]
        except (KeyError, TypeError):
            return
        target.knockdown()

    def _start_next_round(self):
        if self.mode_done:
            return
        self.round_number += 1
        if self.round_number > self.max_round:
            self._finish_mode(won=True)
            return

        self.sequence = random.sample(list(self.SHOTS), self.round_number)
        self.expected_index = 0
        self.machine.events.post("fiddler_all_notes_off")
        self._show_message(
            f"ROUND {self.round_number}",
            f"REMEMBER {self.round_number} NOTE" + ("S" if self.round_number != 1 else ""),
        )
        self._sync_vars()
        self.delay.add(
            name="fiddler_round_demo_start",
            ms=750,
            callback=self._begin_demonstration,
        )

    def _begin_demonstration(self):
        if self.mode_done:
            return
        self._cancel_reminder()
        self.demonstrating = True
        self.machine.events.post("fiddler_all_notes_off")
        remaining = self.sequence[self.expected_index:]
        if not remaining:
            self.demonstrating = False
            self._complete_round()
            return
        self._demonstrate_note(remaining, 0)

    def _demonstrate_note(self, notes, index):
        if self.mode_done:
            return
        if index >= len(notes):
            self.demonstrating = False
            self._begin_response_phase()
            return

        shot = notes[index]
        self.machine.events.post(f"fiddler_{shot}_flash")
        self.machine.events.post(self.NOTE_EVENTS[shot])
        self.delay.add(
            name="fiddler_demo_step",
            ms=self.DEMO_NOTE_MS,
            callback=partial(self._finish_demo_note, notes=notes, index=index, shot=shot),
        )

    def _finish_demo_note(self, notes, index, shot):
        if self.mode_done:
            return
        self.machine.events.post(f"fiddler_{shot}_solid")
        self._demonstrate_note(notes, index + 1)

    def _begin_response_phase(self):
        if self.mode_done:
            return
        self._show_message(
            "PLAY THE PATTERN",
            f"NOTE {self.expected_index + 1} OF {len(self.sequence)}",
            reminder=True,
        )
        self._schedule_reminder()
        self._sync_vars()

    def _schedule_reminder(self):
        self._cancel_reminder()
        if self.mode_done or self.demonstrating or self.expected_index >= len(self.sequence):
            return
        self.delay.add(
            name="fiddler_pattern_reminder",
            ms=self.reminder_ms,
            callback=self._begin_demonstration,
        )

    def _cancel_reminder(self):
        self.delay.remove("fiddler_pattern_reminder")

    def _shot_hit(self, shot=None, **kwargs):
        if self.mode_done or self.demonstrating or shot not in self.SHOTS:
            return
        if self.expected_index >= len(self.sequence):
            return

        expected = self.sequence[self.expected_index]
        if shot == expected:
            self._award_expected_note(assisted=False)
            return

        self.machine.events.post("play_bad_note")
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            self.machine.game.player["fiddler_shot_assist_used"] = 1
            self._show_message("SHOT ASSIST", f"{self.SHOT_LABELS[expected]} AWARDED")
            self._award_expected_note(assisted=True)
            return

        self._finish_mode(won=False)

    def _award_expected_note(self, assisted=False):
        if self.mode_done or self.expected_index >= len(self.sequence):
            return

        self._cancel_reminder()
        shot = self.sequence[self.expected_index]
        value = self.ROUND_VALUES[self.round_number][self.expected_index] + self.bigger_increment
        self.machine.events.post(self.NOTE_EVENTS[shot])
        self.machine.events.post(f"fiddler_{shot}_off")
        self._score(value)
        self.expected_index += 1
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="CORRECT NOTE" if not assisted else "ASSISTED NOTE",
            message_mode_subtitle=self.SHOT_LABELS[shot],
            message_mode_value=value,
        )
        self._sync_vars()

        if self.expected_index >= len(self.sequence):
            self._complete_round()
        else:
            self._begin_response_phase()

    def _complete_round(self):
        if self.mode_done:
            return
        self._cancel_reminder()
        self.machine.events.post("fiddler_all_notes_off")
        if self.round_number >= self.max_round:
            self._finish_mode(won=True)
            return
        self._show_message(f"ROUND {self.round_number} COMPLETE", "NEXT PATTERN")
        self.delay.add(
            name="fiddler_next_round",
            ms=self.STAGE_DELAY_MS,
            callback=self._start_next_round,
        )

    def _finish_mode(self, won):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        self.machine.events.post("fiddler_all_notes_off")
        player = self.machine.game.player
        player["fiddler_state"] = 2
        self._sync_vars()

        if won:
            self._show_message("FIDDLER SILENCED", f"{self.mode_points:,} POINTS", jackpot=True)
        else:
            self._show_message("WRONG NOTE", "FIDDLER ESCAPES")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("fiddler_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_2"] = sum(len(self.ROUND_VALUES[r]) for r in range(1, self.round_number)) + self.expected_index
        player["active_mode_stat_1"] = self.round_number
        player["fiddler_note"] = min(self.expected_index + 1, len(self.sequence)) if self.sequence else 0
        player["fiddler_notes_completed"] = self.expected_index
        player["fiddler_notes_required"] = len(self.sequence)
        self.machine.events.post("fiddler_status_changed")

    def _clear_delays(self):
        for name in (
            "fiddler_first_round",
            "fiddler_round_demo_start",
            "fiddler_demo_step",
            "fiddler_pattern_reminder",
            "fiddler_next_round",
        ):
            self.delay.remove(name)
        for target_name in self.DROP_TARGETS:
            self.delay.remove(f"fiddler_knockdown_{target_name}")

    def _show_message(self, title, subtitle="", jackpot=False, reminder=False):
        self.machine.events.post(
            "show_mode_jackpot" if jackpot else "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=self.mode_points if jackpot else "",
            message_mode_seconds="",
            reminder=reminder,
        )
