import random
import time
from functools import partial

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Fiddler(CaseFileMixin, Mode):
    """Fiddler: saucer-started Simon Says with persistent failure limit."""

    MODE_KEY = "fiddler"
    DISPLAY_NAME = "FIDDLER"

    MAX_PATTERN_LENGTH = 4
    BASE_FAILURE_LIMIT = 3
    MORE_JACKPOTS_FAILURE_LIMIT = 4
    BASE_NOTE_VALUE = 250_000
    BIGGER_NOTE_VALUE = 300_000

    NOTE_FLASH_ON_MS = 200
    NOTE_FLASH_OFF_MS = 50
    NOTE_FLASH_TOTAL_MS = 1_000
    WATCH_NOTE_TOTAL_MS = 900
    WATCH_STROBE_ON_MS = 200
    WATCH_STROBE_OFF_MS = 100
    NOTE_GAP_MS = 200
    PATTERN_REPEAT_PAUSE_MS = 750
    FRESH_PATTERN_REPEATS = 2
    REMINDER_PATTERN_REPEATS = 1
    REMINDER_REENTRY_LOCKOUT_SECONDS = 4.0
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

    def mode_start(self, starting_saucer=None, starting_vuk=False, **kwargs):
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
        self.held_vuk = False
        self.daily_bugle_claimed = False
        self._watch_notes = []
        self._watch_repeat = 0
        self._watch_note_index = 0
        self._watch_repeats_target = self.FRESH_PATTERN_REPEATS
        self._watch_note_elapsed_ms = 0
        self._watch_strobe_on = False
        self._last_saucer_eject_time = None

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
        player["fiddler_saucer_hold"] = 0

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
        self.machine.events.post("fiddler_all_notes_off")
        self._force_drop_banks_down()
        starting_saucer = self._normalize_saucer_number(starting_saucer)
        if starting_vuk:
            self._start_from_vuk()
        elif starting_saucer:
            self._saucer_hit(saucer=starting_saucer)
        else:
            self._show_waiting_for_saucer("SHOOT A SAUCER", "WATCH THE PATTERN")
        self._sync_vars()

    @staticmethod
    def _normalize_saucer_number(saucer):
        try:
            number = int(str(saucer).replace("saucer_", ""))
        except (TypeError, ValueError):
            return None
        return number if number in (1, 2, 3) else None

    def mode_stop(self, **kwargs):
        self.mode_done = True
        self._clear_delays()
        self.clear_active_case_file_helpers()
        self.machine.events.post("fiddler_all_notes_off")
        self.machine.events.post("fiddler_saucers_not_ready")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        if self.machine.game:
            self.machine.game.player["fiddler_saucer_hold"] = 0
        if self.held_vuk:
            self.held_vuk = False
            self.machine.events.post("request_vuk_eject", delay_ms=0)
        if self.daily_bugle_claimed:
            self.daily_bugle_claimed = False
            self.machine.events.post("enable_daily_bugle_mystery")
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
        # Patterns may repeat shots; the four-note cap is a gameplay limit,
        # not a uniqueness requirement.
        self.sequence = [random.choice(self.SHOTS) for _ in range(self.pattern_length)]
        self.expected_index = 0
        self.round_failed = False

    def _saucer_hit(self, saucer=None, **kwargs):
        if self.mode_done or saucer not in (1, 2, 3):
            return
        if self.demonstrating or self.feedback_active:
            return

        self.held_saucer = saucer
        self.machine.game.player["fiddler_saucer_hold"] = 1
        self.machine.events.post("fiddler_saucers_not_ready")

        fresh_pattern = self.round_failed or not self.sequence
        if fresh_pattern:
            self._new_pattern()
        else:
            # A clean saucer return is only a reminder if the ball has been
            # back in play for at least four seconds. A ricochet straight back
            # into a saucer is ejected immediately without replaying WATCH.
            if self._last_saucer_eject_time is not None:
                elapsed = time.monotonic() - self._last_saucer_eject_time
                if elapsed < self.REMINDER_REENTRY_LOCKOUT_SECONDS:
                    # A quick ricochet is not a reminder and must not extend
                    # the original four-second reminder lockout. Use the
                    # shared standard saucer-eject delay for this path.
                    self._eject_held_saucer(
                        delay_ms=None,
                        restart_reminder_lockout=False,
                    )
                    return

        # A clean saucer return is a voluntary reminder: replay the same full
        # pattern once and preserve progress already made. Fresh attempts get
        # the normal two-play WATCH presentation.
        self.waiting_for_saucer = False
        self._begin_watch_phase(
            repeats=(
                self.FRESH_PATTERN_REPEATS
                if fresh_pattern
                else self.REMINDER_PATTERN_REPEATS
            )
        )

    def _start_from_vuk(self):
        """Claim a Mystery-start ball in the VUK for the first WATCH phase."""
        if self.mode_done:
            return
        self.held_vuk = True
        self.daily_bugle_claimed = True
        self.machine.game.player["fiddler_saucer_hold"] = 1
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.machine.events.post("cancel_vuk_eject_request")
        self.machine.events.post("fiddler_saucers_not_ready")
        self._new_pattern()
        self.waiting_for_saucer = False
        self._begin_watch_phase(repeats=self.FRESH_PATTERN_REPEATS)

    def _begin_watch_phase(self, repeats=None):
        if self.mode_done or not self.sequence:
            return
        self._clear_watch_delays()
        self._clear_correct_note_flashes()
        self.demonstrating = True
        self.feedback_active = False
        self.machine.events.post("fiddler_all_notes_off")
        self._watch_notes = list(self.sequence)
        self._watch_repeat = 0
        self._watch_note_index = 0
        self._watch_repeats_target = max(1, int(repeats or self.FRESH_PATTERN_REPEATS))
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
            if self._watch_repeat >= self._watch_repeats_target:
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
        self._watch_note_elapsed_ms = 0
        self._watch_strobe_on = False
        self._watch_strobe_step(shot)

    def _watch_strobe_step(self, shot):
        if self.mode_done or not self.demonstrating:
            return

        if self._watch_note_elapsed_ms >= self.WATCH_NOTE_TOTAL_MS:
            self.machine.events.post(f"fiddler_{shot}_off")
            self._watch_note_flash_done()
            return

        self._watch_strobe_on = not self._watch_strobe_on
        if self._watch_strobe_on:
            self.machine.events.post(f"fiddler_{shot}_solid")
            step_ms = self.WATCH_STROBE_ON_MS
        else:
            self.machine.events.post(f"fiddler_{shot}_dim")
            step_ms = self.WATCH_STROBE_OFF_MS

        remaining_ms = self.WATCH_NOTE_TOTAL_MS - self._watch_note_elapsed_ms
        step_ms = min(step_ms, remaining_ms)
        self._watch_note_elapsed_ms += step_ms
        self.delay.reset(
            name="fiddler_watch_flash",
            ms=step_ms,
            callback=partial(self._watch_strobe_step, shot),
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
        self._eject_held_ball()
        self._sync_vars()

    def _eject_held_ball(self):
        if self.held_vuk:
            self.held_vuk = False
            self.machine.game.player["fiddler_saucer_hold"] = 0
            self._last_saucer_eject_time = time.monotonic()
            self.machine.events.post("request_vuk_eject", delay_ms=0)
            return
        self._eject_held_saucer()

    def _eject_held_saucer(self, delay_ms=0, restart_reminder_lockout=True):
        if self.held_saucer not in (1, 2, 3):
            return
        saucer = self.held_saucer
        self.held_saucer = None
        self.machine.game.player["fiddler_saucer_hold"] = 0
        if restart_reminder_lockout:
            self._last_saucer_eject_time = time.monotonic()
        self.machine.events.post(
            "request_saucer_eject",
            saucer_number=saucer,
            delay_ms=delay_ms,
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
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="CORRECT NOTE",
            message_mode_subtitle=self.SHOT_LABELS[shot],
            message_mode_value=self.note_value,
        )
        self._start_note_flash(
            shot,
            done_callback=self._correct_note_feedback_done,
            delay_name=f"fiddler_correct_note_flash_{shot}",
        )
        # Correct-note feedback is visual only. Advance immediately so an
        # ordered pattern can be completed as quickly as switches register.
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

    def _correct_note_feedback_done(self):
        """Correct-note lighting never gates the next gameplay input."""

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
            "fiddler_wrong_note_flash",
            "fiddler_shot_assist_flash",
            "fiddler_failed_round_flash",
        ):
            self.delay.remove(name)
        self._clear_correct_note_flashes()
        for target_name in self.DROP_TARGETS:
            self.delay.remove(f"fiddler_knockdown_{target_name}")

    def _clear_correct_note_flashes(self):
        for shot in self.SHOTS:
            self.delay.remove(f"fiddler_correct_note_flash_{shot}")

    def _show_message(self, title, subtitle="", jackpot=False, reminder=False):
        self.machine.events.post(
            "show_mode_jackpot" if jackpot else "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=self.mode_points if jackpot else "",
            message_mode_seconds="",
            reminder=reminder,
        )
