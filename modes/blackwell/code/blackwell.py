from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin

"""
Blackwell - Prediction Panic

Rules:
- 6-shot timed sequence.
- One shot is active at a time.
- Timers start at 12 seconds and drop by 1 second per shot.
- Spinner adds +1 second to the current shot timer.
- Lit shot awards the current jackpot and advances to the next shot.
- Timeout advances to the next shot with no award.
- Jackpot starts at 100K and increases by 100K per collected jackpot.

Case File helpers:
- More Jackpots: adds a 7th shot. Either pop hit awards it.
- Bigger Jackpots: jackpot starts at 150K and increases by 150K per collect.
- More Time: timers start at 16 seconds instead of 12.
- Safety Net: starts a 10 second ball save.
- Shot Assist: first timeout awards the jackpot anyway.
"""


class Blackwell(CaseFileMixin, Mode):
    MODE_KEY = "blackwell"
    DISPLAY_NAME = "Blackwell"

    BASE_SHOT_COUNT = 6
    BASE_START_TIME = 12
    MORE_TIME_START_TIME = 16
    BASE_JACKPOT = 100_000
    BASE_JACKPOT_STEP = 100_000
    BIGGER_JACKPOT = 150_000
    BIGGER_JACKPOT_STEP = 150_000
    SPINNER_TIME_ADD = 1

    BASE_SHOTS = [
        "left_web",
        "center_web",
        "upper_spinner",
        "upper_target_left",
        "upper_target_center",
        "upper_target_right",
    ]

    CASE_FILE_EXTRA_SHOT = "pops"
    UPPER_SHOTS = {"upper_spinner", "upper_target_left", "upper_target_center", "upper_target_right"}

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.current_index = -1
        self.current_shot = None
        self.seconds_left = 0
        self.mode_points = 0
        self.jackpots_collected = 0
        self.missed_shots = 0
        self.best_jackpot = 0

        self.start_time = self.BASE_START_TIME
        self.jackpot_base = self.BASE_JACKPOT
        self.jackpot_step = self.BASE_JACKPOT_STEP
        self.shot_assist_available = False

        self.shot_sequence = list(self.BASE_SHOTS)
        self._apply_case_file_bonuses()
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA BLACKWELL SHOT AVAILABLE"),
            ("bigger_jackpots", "BIGGER PREDICTION JACKPOTS"),
            ("more_time", "PREDICTION TIMERS EXTENDED"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST TIMEOUT AWARDS JACKPOT"),
        ])

        self.add_mode_event_handler("blackwell_left_web_hit", self._shot_hit, shot_name="left_web")
        self.add_mode_event_handler("blackwell_center_web_hit", self._shot_hit, shot_name="center_web")
        self.add_mode_event_handler("blackwell_upper_spinner_hit", self._shot_hit, shot_name="upper_spinner")
        self.add_mode_event_handler("blackwell_upper_target_left_hit", self._shot_hit, shot_name="upper_target_left")
        self.add_mode_event_handler("blackwell_upper_target_center_hit", self._shot_hit, shot_name="upper_target_center")
        self.add_mode_event_handler("blackwell_upper_target_right_hit", self._shot_hit, shot_name="upper_target_right")
        self.add_mode_event_handler("blackwell_pops_hit", self._shot_hit, shot_name="pops")
        self.add_mode_event_handler("blackwell_spinner_time_add", self._spinner_time_add)
        self.add_mode_event_handler("blackwell_complete_request", self._complete_mode)
        self.add_mode_event_handler("blackwell_fail_request", self._fail_mode)

        self.machine.events.post("blackwell_startup_complete")
        self.machine.events.post("show_mode_message_long", title="PREDICTION PANIC", subtitle="HIT EACH LIT SHOT")
        self._next_shot()

    def mode_stop(self, **kwargs):
        self.delay.remove("blackwell_timer_tick")
        self.delay.remove("blackwell_next_shot_delay")
        self._stop_current_shot_light()
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        if self.has_case_file("more_jackpots"):
            self.shot_sequence.append(self.CASE_FILE_EXTRA_SHOT)

        if self.has_case_file("bigger_jackpots"):
            self.jackpot_base = self.BIGGER_JACKPOT
            self.jackpot_step = self.BIGGER_JACKPOT_STEP

        if self.has_case_file("more_time"):
            self.start_time = self.MORE_TIME_START_TIME

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.shot_assist_available = True

    def _next_shot(self, **kwargs):
        if self.mode_done:
            return

        self.delay.remove("blackwell_timer_tick")
        self._stop_current_shot_light()

        self.current_index += 1

        if self.current_index >= len(self.shot_sequence):
            self._complete_mode()
            return

        self.current_shot = self.shot_sequence[self.current_index]
        self._update_rooftop_diverter()
        self.seconds_left = max(1, self.start_time - self.current_index)
        self._sync_vars()

        self.machine.events.post("blackwell_shot_started", shot=self.current_shot, shot_number=self.current_index + 1, total_shots=len(self.shot_sequence), seconds=self.seconds_left, jackpot=self._current_jackpot_value())
        self.machine.events.post("show_mode_countdown", title="BLACKWELL PREDICTS", subtitle=self.current_shot.replace("_", " ").upper(), value=self._current_jackpot_value(), seconds=self.seconds_left)
        self.machine.events.post(f"blackwell_lite_{self.current_shot}")
        self._schedule_tick()

    def _schedule_tick(self):
        self.delay.remove("blackwell_timer_tick")
        self.delay.add(
            name="blackwell_timer_tick",
            ms=1000,
            callback=self._timer_tick,
        )

    def _timer_tick(self, **kwargs):
        if self.mode_done or not self.current_shot:
            return

        self.seconds_left -= 1
        self._sync_vars()
        self.machine.events.post("blackwell_timer_changed", seconds=self.seconds_left)
        if self.seconds_left <= 5:
            self.machine.events.post("show_mode_countdown", title="TIME RUNNING OUT", subtitle=self.current_shot.replace("_", " ").upper(), seconds=self.seconds_left)

        if self.seconds_left <= 0:
            self._timeout_current_shot()
            return

        self._schedule_tick()

    def _spinner_time_add(self, **kwargs):
        if self.mode_done or not self.current_shot:
            return

        self.seconds_left += self.SPINNER_TIME_ADD
        self._sync_vars()
        self.machine.events.post("blackwell_time_added", seconds=self.seconds_left)
        self.machine.events.post("show_mode_message", title="TIME ADDED", subtitle="SPINNER HIT", seconds=self.seconds_left)

    def _shot_hit(self, shot_name=None, **kwargs):
        if self.mode_done or self._in_summary():
            return

        if not shot_name or shot_name != self.current_shot:
            return

        self._award_current_jackpot(shot_assist=False)

    def _timeout_current_shot(self):
        if self.mode_done:
            return

        if self.shot_assist_available:
            self.shot_assist_available = False
            self.machine.events.post("blackwell_shot_assist_used")
            self.machine.events.post("show_mode_message", title="SHOT ASSIST", subtitle="TIMEOUT AWARDS JACKPOT")
            self._award_current_jackpot(shot_assist=True)
            return

        self.missed_shots += 1
        self._sync_vars()
        self.machine.events.post("blackwell_shot_missed", shot=self.current_shot)
        self.machine.events.post("show_mode_message", title="MISSED SHOT", subtitle=self.current_shot.replace("_", " ").upper())
        self._advance_after_delay()

    def _award_current_jackpot(self, shot_assist=False):
        jackpot_value = self._current_jackpot_value()
        player = self.machine.game.player if self.machine.game else None

        if player:
            player["score"] += jackpot_value

        self.mode_points += jackpot_value
        self.jackpots_collected += 1
        self.best_jackpot = max(self.best_jackpot, jackpot_value)
        self._sync_vars()

        self.machine.events.post("blackwell_jackpot_collected", shot=self.current_shot, value=jackpot_value, shot_assist=shot_assist)
        self.machine.events.post("show_mode_jackpot", title="PREDICTION HIT", subtitle=self.current_shot.replace("_", " ").upper(), value=jackpot_value)
        self._advance_after_delay()

    def _advance_after_delay(self):
        self.delay.remove("blackwell_timer_tick")
        self._stop_current_shot_light()
        self.delay.remove("blackwell_next_shot_delay")
        self.delay.add(
            name="blackwell_next_shot_delay",
            ms=500,
            callback=self._next_shot,
        )

    def _current_jackpot_value(self):
        return self.jackpot_base + (self.jackpot_step * self.jackpots_collected)

    def _update_rooftop_diverter(self):
        if self.current_shot in self.UPPER_SHOTS:
            self.machine.events.post("rooftop_diverter_open")
        else:
            self.machine.events.post("rooftop_diverter_close")

    def _stop_current_shot_light(self):
        if self.current_shot:
            self.machine.events.post(f"blackwell_stop_{self.current_shot}")

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("blackwell_timer_tick")
        self.delay.remove("blackwell_next_shot_delay")
        self._stop_current_shot_light()
        self.machine.events.post("rooftop_diverter_close")
        player = self.machine.game.player if self.machine.game else None
        if player:
            player["blackwell_completed"] = 1
        self._sync_vars()
        self.machine.events.post("show_mode_message_long", title="BLACKWELL BEATEN", subtitle="SEQUENCE COMPLETE")
        self.machine.events.post("blackwell_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("blackwell_timer_tick")
        self.delay.remove("blackwell_next_shot_delay")
        self._stop_current_shot_light()
        self.machine.events.post("rooftop_diverter_close")
        player = self.machine.game.player if self.machine.game else None
        if player:
            player["blackwell_completed"] = 0
        self._sync_vars()
        self.machine.events.post("show_mode_message_long", title="BLACKWELL ESCAPES", subtitle="OUT OF TIME")
        self.machine.events.post("blackwell_mode_failed")

    def _sync_vars(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return

        player["blackwell_mode_points"] = self.mode_points
        player["blackwell_hits"] = self.jackpots_collected
        player["blackwell_major_hits"] = len(self.shot_sequence)
        player["blackwell_jackpots"] = self.jackpots_collected
        player["blackwell_missed_shots"] = self.missed_shots
        player["blackwell_best_jackpot"] = self.best_jackpot
        player["blackwell_current_shot"] = self.current_shot or ""
        player["blackwell_current_shot_number"] = self.current_index + 1 if self.current_index >= 0 else 0
        player["blackwell_total_shots"] = len(self.shot_sequence)
        player["blackwell_timer_seconds"] = self.seconds_left
        player["blackwell_next_jackpot"] = self._current_jackpot_value()

    def _in_summary(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return False

        try:
            return bool(player["villain_mode_in_summary"])
        except KeyError:
            return False
