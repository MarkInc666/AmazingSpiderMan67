import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
Fifth Avenue Phantom — Vanish and Reveal

Rules:
- Mode is 5 rounds. More Jackpots adds a 6th round.
- Each round begins with the Phantom hiding at one random shot/location.
- Hit any right-bank drop target to reveal the jackpot shot and start the timer.
- Additional right-bank drops in the same round add more time, but reduce the jackpot value.
- Hit the revealed jackpot shot to collect and advance to the next round.
- If the timer expires, that round is missed and the mode advances to the next round.
- After the final round is collected or missed, the mode completes.

Case Files:
- Safety Net: 10s ball save during mode.
- Bigger Jackpots: values become 1M/900K/800K/700K/600K.
- More Time: +2 seconds to each reveal/drop timer add.
- Shot Assist: once only, the first expired revealed jackpot is awarded anyway.
- More Jackpots: adds a 6th round.
"""


class FifthAvenuePhantom(CaseFileMixin, Mode):
    MODE_KEY = "fifth_avenue_phantom"
    DISPLAY_NAME = "Fifth Avenue Phantom"

    TOTAL_ROUNDS = 5
    MORE_JACKPOTS_TOTAL_ROUNDS = 6
    REVEAL_SECONDS = (6, 8, 10, 12, 14)
    BASE_JACKPOTS = (1_000_000, 800_000, 600_000, 400_000, 200_000)
    BIGGER_JACKPOTS = (1_000_000, 900_000, 800_000, 700_000, 600_000)
    MORE_TIME_BONUS_SECONDS = 2

    RIGHT_DROP_TARGETS = ("right_1", "right_2", "right_3", "right_4", "right_5")

    LOCATIONS = (
        "left_web",
        "center_web",
        "star",
        "left_drops",
        "upper_targets",
        "saucers",
    )

    LOCATION_LABELS = {
        "left_web": "LEFT WEB",
        "center_web": "CENTER WEB",
        "star": "STAR ROLLOVER",
        "left_drops": "LEFT DROPS",
        "upper_targets": "UPPER TARGETS",
        "saucers": "SAUCERS",
    }

    LOCATION_LIGHT_EVENTS = {
        "left_web": "fifth_avenue_phantom_light_left_web",
        "center_web": "fifth_avenue_phantom_light_center_web",
        "star": "fifth_avenue_phantom_light_star",
        "left_drops": "fifth_avenue_phantom_light_left_drops",
        "upper_targets": "fifth_avenue_phantom_light_upper_targets",
        "saucers": "fifth_avenue_phantom_light_saucers",
    }

    LOCATION_STOP_EVENTS = {
        "left_web": "fifth_avenue_phantom_stop_left_web",
        "center_web": "fifth_avenue_phantom_stop_center_web",
        "star": "fifth_avenue_phantom_stop_star",
        "left_drops": "fifth_avenue_phantom_stop_left_drops",
        "upper_targets": "fifth_avenue_phantom_stop_upper_targets",
        "saucers": "fifth_avenue_phantom_stop_saucers",
    }

    RIGHT_DROP_LIGHT_EVENTS = {
        "right_1": "fifth_avenue_phantom_light_right_1",
        "right_2": "fifth_avenue_phantom_light_right_2",
        "right_3": "fifth_avenue_phantom_light_right_3",
        "right_4": "fifth_avenue_phantom_light_right_4",
        "right_5": "fifth_avenue_phantom_light_right_5",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "build"
        self.current_location = None
        self.right_drops_hit = set()
        self.reveal_number = 0
        self.reveal_seconds_left = 0
        self.current_jackpot = 0
        self.last_jackpot_awarded = 0
        self.mode_points = 0
        self.rounds_started = 0
        self.jackpots_collected = 0
        self.rounds_missed = 0
        self.best_jackpot = 0
        self.shot_assist_used = 0
        self.total_rounds = self.MORE_JACKPOTS_TOTAL_ROUNDS if self.has_case_file("more_jackpots") else self.TOTAL_ROUNDS

        self._init_player_vars()
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "6TH PHANTOM ROUND"),
            ("bigger_jackpots", "PHANTOM VALUES IMPROVED"),
            ("more_time", "REVEALS EXTENDED 2s"),
            ("safety_net", "PHANTOM BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST EXPIRED REVEAL AWARDED"),
        ])

        self.add_mode_event_handler("s_right_drops_1_active", self._right_drop_hit, target="right_1")
        self.add_mode_event_handler("s_right_drops_2_active", self._right_drop_hit, target="right_2")
        self.add_mode_event_handler("s_right_drops_3_active", self._right_drop_hit, target="right_3")
        self.add_mode_event_handler("s_right_drops_4_active", self._right_drop_hit, target="right_4")
        self.add_mode_event_handler("s_right_drops_5_active", self._right_drop_hit, target="right_5")

        self.add_mode_event_handler("s_web_target_left_active", self._location_hit, location="left_web")
        self.add_mode_event_handler("s_web_target_mid_active", self._location_hit, location="center_web")
        self.add_mode_event_handler("s_star_rollover_active", self._location_hit, location="star")

        self.add_mode_event_handler("s_left_drops_1_active", self._location_hit, location="left_drops")
        self.add_mode_event_handler("s_left_drops_2_active", self._location_hit, location="left_drops")
        self.add_mode_event_handler("s_left_drops_3_active", self._location_hit, location="left_drops")

        self.add_mode_event_handler("s_upper_target_left_active", self._location_hit, location="upper_targets")
        self.add_mode_event_handler("s_upper_target_center_active", self._location_hit, location="upper_targets")
        self.add_mode_event_handler("s_upper_target_right_active", self._location_hit, location="upper_targets")

        self.add_mode_event_handler("s_saucer_1_active", self._saucer_hit)
        self.add_mode_event_handler("s_saucer_2_active", self._saucer_hit)
        self.add_mode_event_handler("s_saucer_3_active", self._saucer_hit)

        self.add_mode_event_handler("fifth_avenue_phantom_complete_request", self._complete_mode)
        self.add_mode_event_handler("fifth_avenue_phantom_fail_request", self._complete_mode)

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("fifth_avenue_phantom_started")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="REVEAL THE PHANTOM",
            message_mode_subtitle=f"{self.total_rounds} ROUNDS - HIT RIGHT DROPS",
        )
        self._start_new_round()

    def mode_stop(self, **kwargs):
        self.delay.remove("fifth_avenue_phantom_timer_tick")
        self.delay.remove("fifth_avenue_phantom_next_round")
        self._clear_lit_location()
        self.clear_active_case_file_helpers()
        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        super().mode_stop(**kwargs)

    def _init_player_vars(self):
        player = self.machine.game.player
        player["fifth_avenue_phantom_state"] = 1
        player["active_mode_points"] = 0
        player["fifth_avenue_phantom_jackpots"] = 0
        player["fifth_avenue_phantom_escape_jackpots"] = 0
        player["fifth_avenue_phantom_best_jackpot"] = 0
        player["fifth_avenue_phantom_rounds"] = 0
        player["fifth_avenue_phantom_reveals_used"] = 0
        player["fifth_avenue_phantom_current_jackpot"] = 0
        player["fifth_avenue_phantom_timer"] = 0
        player["fifth_avenue_phantom_location"] = ""
        player["fifth_avenue_phantom_phase"] = self.phase
        player["fifth_avenue_phantom_shot_assist_used"] = 0

    def _start_new_round(self):
        if self._in_summary_or_done():
            return

        if self.rounds_started >= self.total_rounds:
            self._complete_mode()
            return

        self.delay.remove("fifth_avenue_phantom_timer_tick")
        self.delay.remove("fifth_avenue_phantom_next_round")
        self._clear_lit_location()
        self.phase = "build"
        self.current_location = random.choice(list(self.LOCATIONS))
        self.right_drops_hit.clear()
        self.reveal_number = 0
        self.reveal_seconds_left = 0
        self.current_jackpot = 0
        self.rounds_started += 1

        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post(
            "fifth_avenue_phantom_round_started",
            round=self.rounds_started,
            total_rounds=self.total_rounds,
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=f"ROUND {self.rounds_started} / {self.total_rounds}",
            message_mode_subtitle="RIGHT DROPS REVEAL PHANTOM",
        )
        self._sync_vars()

    def _right_drop_hit(self, target=None, **kwargs):
        if self._in_summary_or_done() or not target:
            return

        if self.phase not in ("build", "reveal"):
            return

        if target in self.right_drops_hit:
            return

        self.right_drops_hit.add(target)
        self.reveal_number = len(self.right_drops_hit)
        self.current_jackpot = self._jackpot_for_reveal(self.reveal_number)
        self.reveal_seconds_left += self._seconds_for_reveal(self.reveal_number)

        light_event = self.RIGHT_DROP_LIGHT_EVENTS.get(target)
        if light_event:
            self.machine.events.post(light_event)

        if self.phase == "build":
            self.phase = "reveal"
            self._clear_lit_location()
            self._light_location(self.current_location)
            self.machine.events.post(
                "fifth_avenue_phantom_revealed",
                round=self.rounds_started,
                total_rounds=self.total_rounds,
                reveal_number=self.reveal_number,
                seconds=self.reveal_seconds_left,
                jackpot=self.current_jackpot,
                location=self.current_location,
                location_label=self.LOCATION_LABELS[self.current_location],
            )
        else:
            self.machine.events.post(
                "fifth_avenue_phantom_reveal_extended",
                round=self.rounds_started,
                total_rounds=self.total_rounds,
                reveal_number=self.reveal_number,
                seconds=self.reveal_seconds_left,
                jackpot=self.current_jackpot,
                location=self.current_location,
                location_label=self.LOCATION_LABELS[self.current_location],
            )

        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=f"ROUND {self.rounds_started}: PHANTOM REVEALED",
            message_mode_subtitle=self.LOCATION_LABELS[self.current_location],
            message_mode_value=self.current_jackpot,
            message_mode_seconds=self.reveal_seconds_left,
        )
        self._sync_vars()
        self._schedule_timer_tick()

    def _saucer_hit(self, **kwargs):
        self._location_hit(location="saucers", **kwargs)
        self.machine.events.post("clear_saucers")

    def _location_hit(self, location=None, **kwargs):
        if self._in_summary_or_done() or not location:
            return

        if self.phase != "reveal":
            return

        if location != self.current_location:
            return

        self._award_phantom_jackpot(source=location)

    def _award_phantom_jackpot(self, source="shot"):
        if self.mode_done or self.phase != "reveal":
            return

        self.phase = "awarding"
        self.delay.remove("fifth_avenue_phantom_timer_tick")
        jackpot = self.current_jackpot
        self.last_jackpot_awarded = jackpot
        self.jackpots_collected += 1
        self.best_jackpot = max(self.best_jackpot, jackpot)
        self._score(jackpot)
        self._clear_lit_location()
        self.machine.events.post(
            "fifth_avenue_phantom_jackpot_awarded",
            source=source,
            jackpot=jackpot,
            round=self.rounds_started,
            total_rounds=self.total_rounds,
            reveal_number=self.reveal_number,
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        title = "SHOT ASSIST JACKPOT" if source == "shot_assist_timeout" else "PHANTOM JACKPOT"
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=f"ROUND {self.rounds_started} / {self.total_rounds}",
            message_mode_value=jackpot,
        )
        self._sync_vars()
        self._queue_next_round_or_complete()

    def _miss_round(self):
        if self.mode_done or self.phase != "reveal":
            return

        self.phase = "round_missed"
        self.delay.remove("fifth_avenue_phantom_timer_tick")
        self.rounds_missed += 1
        self._clear_lit_location()
        self.machine.events.post(
            "fifth_avenue_phantom_round_missed",
            round=self.rounds_started,
            total_rounds=self.total_rounds,
            reveal_number=self.reveal_number,
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="PHANTOM VANISHED",
            message_mode_subtitle=f"ROUND {self.rounds_started} MISSED",
        )
        self._sync_vars()
        self._queue_next_round_or_complete()

    def _queue_next_round_or_complete(self):
        self.delay.remove("fifth_avenue_phantom_next_round")
        if self.rounds_started >= self.total_rounds:
            self.phase = "complete_pending"
            self._sync_vars()
            self.delay.add(
                name="fifth_avenue_phantom_next_round",
                ms=1500,
                callback=self._complete_mode,
            )
            return

        self.delay.add(
            name="fifth_avenue_phantom_next_round",
            ms=1200,
            callback=self._start_new_round,
        )

    def _schedule_timer_tick(self):
        self.delay.remove("fifth_avenue_phantom_timer_tick")
        self.delay.add(
            name="fifth_avenue_phantom_timer_tick",
            ms=1000,
            callback=self._timer_tick,
        )

    def _timer_tick(self, **kwargs):
        if self._in_summary_or_done() or self.phase != "reveal":
            return

        self.reveal_seconds_left -= 1
        self.machine.events.post(
            "fifth_avenue_phantom_timer_tick",
            round=self.rounds_started,
            total_rounds=self.total_rounds,
            seconds=self.reveal_seconds_left,
            jackpot=self.current_jackpot,
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=f"ROUND {self.rounds_started}: VANISHING",
            message_mode_subtitle=self.LOCATION_LABELS[self.current_location],
            message_mode_value=self.current_jackpot,
            message_mode_seconds=max(0, self.reveal_seconds_left),
        )
        self._sync_vars()

        if self.reveal_seconds_left <= 0:
            self._timer_expired()
            return

        self._schedule_timer_tick()

    def _timer_expired(self):
        if self.mode_done or self.phase != "reveal":
            return

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = 1
            self.machine.events.post(
                "fifth_avenue_phantom_shot_assist_used",
                jackpot=self.current_jackpot,
                round=self.rounds_started,
                total_rounds=self.total_rounds,
                location=self.current_location,
                location_label=self.LOCATION_LABELS[self.current_location],
            )
            self._award_phantom_jackpot(source="shot_assist_timeout")
            return

        self.machine.events.post("fifth_avenue_phantom_reveal_expired")
        self._miss_round()

    def _light_location(self, location):
        event = self.LOCATION_LIGHT_EVENTS.get(location)
        if event:
            self.machine.events.post(event)

    def _clear_lit_location(self):
        self.machine.events.post("fifth_avenue_phantom_clear_lights")
        for event in self.LOCATION_STOP_EVENTS.values():
            self.machine.events.post(event)

    def _seconds_for_reveal(self, reveal_number):
        index = max(1, min(5, reveal_number)) - 1
        seconds = self.REVEAL_SECONDS[index]
        if self.has_case_file("more_time"):
            seconds += self.MORE_TIME_BONUS_SECONDS
        return seconds

    def _jackpot_for_reveal(self, reveal_number):
        index = max(1, min(5, reveal_number)) - 1
        values = self.BIGGER_JACKPOTS if self.has_case_file("bigger_jackpots") else self.BASE_JACKPOTS
        return values[index]

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.phase = "complete"
        self.delay.remove("fifth_avenue_phantom_timer_tick")
        self.delay.remove("fifth_avenue_phantom_next_round")
        self._clear_lit_location()
        player = self.machine.game.player
        player["fifth_avenue_phantom_state"] = 2
        player["fifth_avenue_phantom_phase"] = "complete"
        self.machine.events.post("show_mode_message", message_mode_title="PHANTOM CASE CLOSED", message_mode_subtitle="MODE COMPLETE")
        self.machine.events.post("fifth_avenue_phantom_mode_complete")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["fifth_avenue_phantom_jackpots"] = self.jackpots_collected
        player["fifth_avenue_phantom_escape_jackpots"] = 0
        player["fifth_avenue_phantom_best_jackpot"] = self.best_jackpot
        player["fifth_avenue_phantom_rounds"] = self.rounds_started
        player["fifth_avenue_phantom_reveals_used"] = self.reveal_number
        player["fifth_avenue_phantom_current_jackpot"] = self.current_jackpot
        player["fifth_avenue_phantom_timer"] = max(0, self.reveal_seconds_left)
        player["fifth_avenue_phantom_location"] = self.LOCATION_LABELS[self.current_location] if self.current_location else ""
        player["fifth_avenue_phantom_phase"] = self.phase
        player["fifth_avenue_phantom_shot_assist_used"] = self.shot_assist_used

    def _in_summary_or_done(self):
        if self.mode_done:
            return True

        player = self.machine.game.player
        return player["villain_mode_in_summary"] is True
