import random
from functools import partial

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Fiddler(CaseFileMixin, Mode):
    """Fiddler: saucer-started Simon Says with persistent failure limit."""

    MODE_KEY = "fiddler"
    DISPLAY_NAME = "FIDDLER"

    MAX_PATTERN_LENGTH = 5
    BASE_FAILURE_LIMIT = 3
    MORE_JACKPOTS_FAILURE_LIMIT = 4
    BASE_NOTE_VALUE = 250_000
    BIGGER_NOTE_VALUE = 300_000

    NOTE_FLASH_ON_MS = 200
    NOTE_FLASH_OFF_MS = 50
    NOTE_FLASH_TOTAL_MS = 1_000
    NOTE_GAP_MS = 500
    PATTERN_REPEAT_PAUSE_MS = 2_000
    PATTERN_REPEATS = 2
    FEEDBACK_FLASH_MS = 1_000

    SHOTS = ("left_web", "left_bank", "right_pop", "right_bank")
    SHOT_LABELS = {
        "left_web": "LEFT WEB",
        "left_bank": "LEFT BANK",
        "right_pop": "RIGHT POP",
        "right_bank": "RIGHT BANK",
    }
    NOTE_EVENTS = {
        "left_web": "play_note_1",
        "left_bank": "play_note_2",
        "right_pop": "play_note_3",
        "right_bank": "play_note_4",
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
        self.pattern_length = 1
        self.sequence = []
        self.expected_index = 0
        self.rounds_completed = 0
        self.notes_hit = 0
        self.failures = 0
        self.failure_limit = (
            self.MORE_JACKPOTS_FAILURE_LIMIT
            if self.has_case_file("more_jackpots")
            else self.BASE_FAILURE_LIMIT
        )
        self.note_value = (
            self.BIGGER_NOTE_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.BASE_NOTE_VALUE
        )
        self.shot_assist_used = False
        self.defeated = False
        self.round_failed = False
        self.waiting_for_saucer = True
        self.demonstrating = False
        self.feedback_active = False
        self.held_saucer = None
        self._watch_notes = []
        self._watch_repeat = 0
        self._watch_note_index = 0

        for shot in self.SHOTS:
            self.add_mode_event_handler(
                f"fiddler_{shot}_hit", partial(self._shot_hit, shot=shot)
            )
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(
                f"fiddler_saucer_{saucer}_hit",
                partial(self._saucer_hit, saucer=saucer),
            )

        player = self.machine.game.player
        player["fiddler_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_stat_1"] = 0
        player["active_mode_stat_2"] = 0
        player["active_mode_completed"] = 0
        player["fiddler_note"] = 0
        player["fiddler_notes_completed"] = 0
        player["fiddler_notes_required"] = self.pattern_length
        player["fiddler_shot_assist_used"] = 0

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "FOURTH FAILED ROUND ALLOWED"),
            ("bigger_jackpots", "CORRECT NOTES WORTH 300,000"),
            ("more_time", "25 SECOND BALL SAVE ACTIVE"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST WRONG NOTE IS FORGIVEN"),
        ])

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")
        if self.has_case_file("more_time"):
            self.machine.events.post("start_fiddler_more_time_ball_save")

        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("fiddler_all_notes_off")
        self._force_drop_banks_down()
        self._show_waiting_for_saucer("SHOOT A SAUCER", "WATCH THE PATTERN")
        self._sync_vars()

    def mode_stop(self, **kwargs):
        self.mode_done = True
        self._clear_delays()
        self.clear_active_case_file_helpers()
        self.machine.events.post("fiddler_all_notes_off")
        self.machine.events.post("fiddler_saucers_not_ready")
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

    def _new_pattern(self):
        # Five-note patterns intentionally allow repeated shots because Fiddler
        # has four physical note shots.
        self.sequence = [random.choice(self.SHOTS) for _ in range(self.pattern_length)]
        self.expected_index = 0
        self.round_failed = False

    def _saucer_hit(self, saucer=None, **kwargs):
        if self.mode_done or saucer not in (1, 2, 3):
            return
        if self.demonstrating or self.feedback_active:
            return

        self.held_saucer = saucer
        self.machine.events.post("fiddler_saucers_not_ready")

        if self.round_failed or not self.sequence:
            self._new_pattern()

        # A clean saucer return is a voluntary reminder: replay the same full
        # pattern and preserve progress already made in that pattern.
        self.waiting_for_saucer = False
        self._begin_watch_phase()

    def _begin_watch_phase(self):
        if self.mode_done or not self.sequence:
            return
        self._clear_watch_delays()
        self.demonstrating = True
        self.feedback_active = False
        self.machine.events.post("fiddler_all_notes_off")
        self._watch_notes = list(self.sequence)
        self._watch_repeat = 0
        self._watch_note_index = 0
        self._show_message(
            "WATCH",
            f"{len(self.sequence)} NOTE" + ("S" if len(self.sequence) != 1 else ""),
        )
        self._watch_play_next_note()

    def _watch_play_next_note(self):
        if self.mode_done or not self.demonstrating:
            return

        if self._watch_note_index >= len(self._watch_notes):
            self._watch_repeat += 1
            if self._watch_repeat >= self.PATTERN_REPEATS:
                self._finish_watch_phase()
                return
            self._watch_note_index = 0
            self.machine.events.post("fiddler_all_notes_off")
            self.delay.reset(
                name="fiddler_watch_repeat_pause",
                ms=self.PATTERN_REPEAT_PAUSE_MS,
                callback=self._watch_play_next_note,
            )
            return

        shot = self._watch_notes[self._watch_note_index]
        self.machine.events.post(self.NOTE_EVENTS[shot])
        self._start_note_flash(
            shot,
            done_callback=self._watch_note_flash_done,
            delay_name="fiddler_watch_flash",
        )

    def _watch_note_flash_done(self):
        if self.mode_done or not self.demonstrating:
            return
        self._watch_note_index += 1
        if self._watch_note_index >= len(self._watch_notes):
            self._watch_play_next_note()
            return
        self.delay.reset(
            name="fiddler_watch_note_gap",
            ms=self.NOTE_GAP_MS,
            callback=self._watch_play_next_note,
        )

    def _finish_watch_phase(self):
        if self.mode_done:
            return
        self.demonstrating = False
        self.machine.events.post("fiddler_all_notes_off")
        self._show_message(
            "YOUR TURN",
            f"NOTE {self.expected_index + 1} OF {len(self.sequence)}",
            reminder=True,
        )
        self._eject_held_saucer()
        self._sync_vars()

    def _eject_held_saucer(self):
        if self.held_saucer not in (1, 2, 3):
            return
        saucer = self.held_saucer
        self.held_saucer = None
        self.machine.events.post(
            "request_saucer_eject",
            saucer_number=saucer,
            delay_ms=0,
        )

    def _shot_hit(self, shot=None, **kwargs):
        if self.mode_done or shot not in self.SHOTS:
            return
        if self.demonstrating or self.feedback_active:
            return

        # Once a round has failed, note shots are deliberately "dead wrong"
        # until the player returns to a saucer. They provide feedback but do
        # not consume additional failures.
        if self.round_failed:
            self.machine.events.post("play_bad_note")
            self.feedback_active = True
            self._start_note_flash(
                shot,
                done_callback=self._failed_round_feedback_done,
                delay_name="fiddler_failed_round_flash",
            )
            return

        if self.waiting_for_saucer or not self.sequence:
            return
        if self.expected_index >= len(self.sequence):
            return

        expected = self.sequence[self.expected_index]
        if shot == expected:
            self._correct_note_hit(expected)
            return

        self.machine.events.post("play_bad_note")
        self.feedback_active = True
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            self.machine.game.player["fiddler_shot_assist_used"] = 1
            self._show_message("SHOT ASSIST", f"TRY {self.SHOT_LABELS[expected]}")
            self._start_note_flash(
                expected,
                done_callback=self._shot_assist_feedback_done,
                delay_name="fiddler_shot_assist_flash",
            )
            return

        self.failures += 1
        self.round_failed = True
        self._show_message(
            "WRONG NOTE",
            f"{self.failures} OF {self.failure_limit} FAILURES",
        )
        self._start_note_flash(
            expected,
            done_callback=self._wrong_note_feedback_done,
            delay_name="fiddler_wrong_note_flash",
        )
        self._sync_vars()

    def _correct_note_hit(self, shot):
        self.machine.events.post(self.NOTE_EVENTS[shot])
        self._score(self.note_value)
        self.notes_hit += 1
        self.feedback_active = True
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="CORRECT NOTE",
            message_mode_subtitle=self.SHOT_LABELS[shot],
            message_mode_value=self.note_value,
        )
        self._start_note_flash(
            shot,
            done_callback=self._correct_note_feedback_done,
            delay_name="fiddler_correct_note_flash",
        )
        self._sync_vars()

    def _correct_note_feedback_done(self):
        if self.mode_done:
            return
        self.feedback_active = False
        self.expected_index += 1
        if self.expected_index >= len(self.sequence):
            self._complete_pattern()
            return
        self._show_message(
            "YOUR TURN",
            f"NOTE {self.expected_index + 1} OF {len(self.sequence)}",
            reminder=True,
        )
        self._sync_vars()

    def _shot_assist_feedback_done(self):
        if self.mode_done:
            return
        self.feedback_active = False
        self._show_message(
            "YOUR TURN",
            f"NOTE {self.expected_index + 1} OF {len(self.sequence)}",
            reminder=True,
        )
        self._sync_vars()

    def _wrong_note_feedback_done(self):
        if self.mode_done:
            return
        self.feedback_active = False
        if self.failures >= self.failure_limit:
            self._finish_mode_after_failures()
            return
        self.waiting_for_saucer = True
        self.machine.events.post("fiddler_all_notes_off")
        self.machine.events.post("fiddler_saucers_ready")
        self._show_message("ROUND FAILED", "SHOOT A SAUCER")
        self._sync_vars()

    def _failed_round_feedback_done(self):
        if self.mode_done:
            return
        self.feedback_active = False
        self.machine.events.post("fiddler_all_notes_off")
        self.machine.events.post("fiddler_saucers_ready")
        self._show_message("ROUND FAILED", "SHOOT A SAUCER")

    def _complete_pattern(self):
        if self.mode_done:
            return
        self.feedback_active = False
        self.rounds_completed += 1
        if not self.defeated:
            self.defeated = True
            player = self.machine.game.player
            player["fiddler_state"] = 2
            player["active_mode_completed"] = 1

        self.pattern_length = min(self.MAX_PATTERN_LENGTH, self.pattern_length + 1)
        self.sequence = []
        self.expected_index = 0
        self.round_failed = False
        self.waiting_for_saucer = True
        self.machine.events.post("fiddler_all_notes_off")
        self.machine.events.post("fiddler_saucers_ready")
        self._show_message(
            "PATTERN COMPLETE",
            f"NEXT: {self.pattern_length} NOTE" + ("S" if self.pattern_length != 1 else ""),
        )
        self._sync_vars()

    def _finish_mode_after_failures(self):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        self.machine.events.post("fiddler_all_notes_off")
        self.machine.events.post("fiddler_saucers_not_ready")
        player = self.machine.game.player
        player["active_mode_completed"] = 1 if self.defeated else 0
        if self.defeated:
            player["fiddler_state"] = 2
            self._show_message("FIDDLER SILENCED", f"{self.mode_points:,} POINTS", jackpot=True)
            self.machine.events.post("fiddler_mode_complete")
        else:
            self._show_message("FIDDLER ESCAPES", "NO PATTERN COMPLETED")
            self.machine.events.post("fiddler_mode_failed")

    def _start_note_flash(self, shot, done_callback, delay_name):
        self.machine.events.post(f"fiddler_{shot}_solid")
        self._note_flash_tick(
            shot=shot,
            elapsed_ms=0,
            light_on=True,
            done_callback=done_callback,
            delay_name=delay_name,
        )

    def _note_flash_tick(self, shot, elapsed_ms, light_on, done_callback, delay_name):
        if self.mode_done:
            return
        interval = self.NOTE_FLASH_ON_MS if light_on else self.NOTE_FLASH_OFF_MS
        next_elapsed = elapsed_ms + interval
        if next_elapsed >= self.NOTE_FLASH_TOTAL_MS:
            remaining = self.NOTE_FLASH_TOTAL_MS - elapsed_ms
            self.delay.reset(
                name=delay_name,
                ms=max(1, remaining),
                callback=partial(self._note_flash_done, shot, done_callback),
            )
            return

        self.delay.reset(
            name=delay_name,
            ms=interval,
            callback=partial(
                self._note_flash_toggle,
                shot,
                next_elapsed,
                not light_on,
                done_callback,
                delay_name,
            ),
        )

    def _note_flash_toggle(self, shot, elapsed_ms, light_on, done_callback, delay_name):
        if self.mode_done:
            return
        self.machine.events.post(f"fiddler_{shot}_{'solid' if light_on else 'off'}")
        self._note_flash_tick(
            shot=shot,
            elapsed_ms=elapsed_ms,
            light_on=light_on,
            done_callback=done_callback,
            delay_name=delay_name,
        )

    def _note_flash_done(self, shot, done_callback):
        if self.mode_done:
            return
        self.machine.events.post(f"fiddler_{shot}_off")
        done_callback()

    def _show_waiting_for_saucer(self, title, subtitle):
        self.waiting_for_saucer = True
        self.machine.events.post("fiddler_saucers_ready")
        self._show_message(title, subtitle)

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.rounds_completed
        player["active_mode_stat_2"] = self.notes_hit
        player["fiddler_note"] = (
            min(self.expected_index + 1, len(self.sequence)) if self.sequence else 0
        )
        player["fiddler_notes_completed"] = self.expected_index
        player["fiddler_notes_required"] = len(self.sequence) if self.sequence else self.pattern_length
        self.machine.events.post("fiddler_status_changed")

    def _clear_watch_delays(self):
        for name in (
            "fiddler_watch_flash",
            "fiddler_watch_note_gap",
            "fiddler_watch_repeat_pause",
        ):
            self.delay.remove(name)

    def _clear_delays(self):
        self._clear_watch_delays()
        for name in (
            "fiddler_correct_note_flash",
            "fiddler_wrong_note_flash",
            "fiddler_shot_assist_flash",
            "fiddler_failed_round_flash",
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
