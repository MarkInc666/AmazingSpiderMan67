import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
Fifth Avenue Phantom — Vanish and Reveal

Rules:
- The right drop bank reveals the Phantom's current hiding place.
- Each right drop hit lights the hidden location for a longer window:
  1st = 6s, 2nd = 8s, 3rd = 10s, 4th = 12s, 5th = 14s.
- Phantom can only be collected while the location is lit.
- Jackpot value is based on how many reveals were needed:
  1st = 1M, 2nd = 800K, 3rd = 600K, 4th = 400K, 5th = 200K.
- If collected, the right bank resets and a new round begins.
- If the final reveal expires, the mode ends.

Case Files:
- Safety Net: 10s ball save during mode.
- Bigger Jackpot: values become 1M/900K/800K/700K/600K.
- More Time: +2 seconds to reveal timers.
- Shot Assist: once only, final reveal timeout awards the jackpot anyway.
- More Jackpots: after a Phantom Jackpot, relight same location for a 5s Escape Jackpot worth 50%.
"""


class FifthAvenuePhantom(CaseFileMixin, Mode):
    MODE_KEY = "fifth_avenue_phantom"
    DISPLAY_NAME = "Fifth Avenue Phantom"

    REVEAL_SECONDS = (6, 8, 10, 12, 14)
    BASE_JACKPOTS = (1_000_000, 800_000, 600_000, 400_000, 200_000)
    BIGGER_JACKPOTS = (1_000_000, 900_000, 800_000, 700_000, 600_000)
    MORE_TIME_BONUS_SECONDS = 2
    ESCAPE_SECONDS = 5

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
        self.escape_jackpots_collected = 0
        self.best_jackpot = 0
        self.shot_assist_used = 0

        self._init_player_vars()
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "ESCAPE JACKPOT AFTER PHANTOM"),
            ("bigger_jackpots", "PHANTOM VALUES IMPROVED"),
            ("more_time", "REVEALS EXTENDED 2s"),
            ("safety_net", "PHANTOM BALL SAVE ACTIVE"),
            ("shot_assist", "FINAL MISS AWARDS ONCE"),
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
        self.add_mode_event_handler("fifth_avenue_phantom_fail_request", self._fail_mode)

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("fifth_avenue_phantom_started")
        self.machine.events.post("show_mode_message_long", message_mode_title="REVEAL THE PHANTOM", message_mode_subtitle="HIT RIGHT DROPS")
        self._start_new_round()

    def mode_stop(self, **kwargs):
        self.delay.remove("fifth_avenue_phantom_timer_tick")
        self._clear_lit_location()
        self.clear_active_case_file_helpers()
        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        super().mode_stop(**kwargs)

    def _init_player_vars(self):
        player = self.machine.game.player
        player["fifth_avenue_phantom_state"] = 1
        player["fifth_avenue_phantom_mode_points"] = 0
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

        self.delay.remove("fifth_avenue_phantom_timer_tick")
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
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        self.machine.events.post("show_mode_message", message_mode_title="PHANTOM HIDES", message_mode_subtitle="RIGHT DROPS REVEAL HIM")
        self._sync_vars()

    def _right_drop_hit(self, target=None, **kwargs):
        if self._in_summary_or_done() or not target:
            return

        if self.phase == "escape":
            return

        if target in self.right_drops_hit:
            return

        self.right_drops_hit.add(target)
        self.reveal_number = len(self.right_drops_hit)
        self.current_jackpot = self._jackpot_for_reveal(self.reveal_number)

        self._start_reveal_timer()

    def _start_reveal_timer(self):
        self.phase = "reveal"
        self.reveal_seconds_left = self._seconds_for_reveal(self.reveal_number)

        self._clear_lit_location()
        self._light_location(self.current_location)

        self.machine.events.post(
            "fifth_avenue_phantom_revealed",
            reveal_number=self.reveal_number,
            seconds=self.reveal_seconds_left,
            jackpot=self.current_jackpot,
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        self.machine.events.post("show_mode_countdown", message_mode_title="PHANTOM REVEALED", message_mode_subtitle=self.LOCATION_LABELS[self.current_location], message_mode_value=self.current_jackpot, message_mode_seconds=self.reveal_seconds_left)
        self._sync_vars()
        self._schedule_timer_tick()

    def _saucer_hit(self, **kwargs):
        self._location_hit(location="saucers", **kwargs)
        self.machine.events.post("clear_saucers")

    def _location_hit(self, location=None, **kwargs):
        if self._in_summary_or_done() or not location:
            return

        if location != self.current_location:
            return

        if self.phase == "reveal":
            self._award_phantom_jackpot(source=location)
            return

        if self.phase == "escape":
            self._award_escape_jackpot(source=location)

    def _award_phantom_jackpot(self, source="shot"):
        if self.mode_done:
            return

        self.delay.remove("fifth_avenue_phantom_timer_tick")
        jackpot = self.current_jackpot
        self.last_jackpot_awarded = jackpot
        self.jackpots_collected += 1
        self.best_jackpot = max(self.best_jackpot, jackpot)
        self._score(jackpot)
        self.machine.events.post(
            "fifth_avenue_phantom_jackpot_awarded",
            source=source,
            jackpot=jackpot,
            reveal_number=self.reveal_number,
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        self.machine.events.post("show_mode_jackpot", message_mode_title="PHANTOM JACKPOT", message_mode_subtitle=self.LOCATION_LABELS[self.current_location], message_mode_value=jackpot)
        self._sync_vars()

        if self.has_case_file("more_jackpots"):
            self._start_escape_jackpot()
        else:
            self._start_new_round()

    def _start_escape_jackpot(self):
        self.phase = "escape"
        self.reveal_seconds_left = self.ESCAPE_SECONDS
        if self.has_case_file("more_time"):
            self.reveal_seconds_left += self.MORE_TIME_BONUS_SECONDS

        self._clear_lit_location()
        self._light_location(self.current_location)
        self.machine.events.post(
            "fifth_avenue_phantom_escape_jackpot_lit",
            seconds=self.reveal_seconds_left,
            jackpot=self._escape_jackpot_value(),
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        self.machine.events.post("show_mode_countdown", message_mode_title="ESCAPE BONUS LIT", message_mode_subtitle=self.LOCATION_LABELS[self.current_location], message_mode_value=self._escape_jackpot_value(), message_mode_seconds=self.reveal_seconds_left)
        self._sync_vars()
        self._schedule_timer_tick()

    def _award_escape_jackpot(self, source="shot"):
        if self.mode_done:
            return

        self.delay.remove("fifth_avenue_phantom_timer_tick")
        jackpot = self._escape_jackpot_value()
        self.escape_jackpots_collected += 1
        self._score(jackpot)
        self.machine.events.post(
            "fifth_avenue_phantom_escape_jackpot_awarded",
            source=source,
            jackpot=jackpot,
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        self.machine.events.post("show_mode_jackpot", message_mode_title="ESCAPE BONUS", message_mode_subtitle=self.LOCATION_LABELS[self.current_location], message_mode_value=jackpot)
        self._sync_vars()
        self._start_new_round()

    def _schedule_timer_tick(self):
        self.delay.remove("fifth_avenue_phantom_timer_tick")
        self.delay.add(
            name="fifth_avenue_phantom_timer_tick",
            ms=1000,
            callback=self._timer_tick,
        )

    def _timer_tick(self, **kwargs):
        if self._in_summary_or_done() or self.phase not in ("reveal", "escape"):
            return

        self.reveal_seconds_left -= 1
        self.machine.events.post(
            "fifth_avenue_phantom_timer_tick",
            phase=self.phase,
            seconds=self.reveal_seconds_left,
            jackpot=self.current_jackpot if self.phase == "reveal" else self._escape_jackpot_value(),
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        if self.reveal_seconds_left <= 5:
            self.machine.events.post("show_mode_countdown", message_mode_title="VANISHING", message_mode_subtitle=self.LOCATION_LABELS[self.current_location], message_mode_seconds=self.reveal_seconds_left)
        self._sync_vars()

        if self.reveal_seconds_left <= 0:
            self._timer_expired()
            return

        self._schedule_timer_tick()

    def _timer_expired(self):
        if self.mode_done:
            return

        if self.phase == "escape":
            self.machine.events.post("fifth_avenue_phantom_escape_jackpot_missed")
            self.machine.events.post("show_mode_message", message_mode_title="ESCAPE BONUS MISSED", message_mode_subtitle="PHANTOM VANISHES")
            self._start_new_round()
            return

        if self.phase != "reveal":
            return

        if self.reveal_number >= 5:
            if self.has_case_file("shot_assist") and not self.shot_assist_used:
                self.shot_assist_used = 1
                self.machine.events.post(
                    "fifth_avenue_phantom_shot_assist_used",
                    jackpot=self.current_jackpot,
                    location=self.current_location,
                    location_label=self.LOCATION_LABELS[self.current_location],
                )
                self._award_phantom_jackpot(source="shot_assist_timeout")
                return

            self.machine.events.post("fifth_avenue_phantom_final_reveal_expired")
            self.machine.events.post("show_mode_message", message_mode_title="PHANTOM VANISHED", message_mode_subtitle="FINAL REVEAL EXPIRED")
            if self.jackpots_collected > 0:
                self._complete_mode()
            else:
                self._fail_mode()
            return

        self._clear_lit_location()
        self.phase = "build"
        self.reveal_seconds_left = 0
        self.machine.events.post(
            "fifth_avenue_phantom_reveal_expired",
            reveal_number=self.reveal_number,
            location=self.current_location,
            location_label=self.LOCATION_LABELS[self.current_location],
        )
        self.machine.events.post("show_mode_message", message_mode_title="PHANTOM VANISHED", message_mode_subtitle="HIT MORE RIGHT DROPS")
        self._sync_vars()

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

    def _escape_jackpot_value(self):
        return int(self.last_jackpot_awarded * 0.5)

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.delay.remove("fifth_avenue_phantom_timer_tick")
        self._clear_lit_location()
        player = self.machine.game.player
        player["fifth_avenue_phantom_state"] = 2
        player["fifth_avenue_phantom_phase"] = "complete"
        self.machine.events.post("fifth_avenue_phantom_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.delay.remove("fifth_avenue_phantom_timer_tick")
        self._clear_lit_location()
        player = self.machine.game.player
        player["fifth_avenue_phantom_state"] = 1
        player["fifth_avenue_phantom_phase"] = "failed"
        self.machine.events.post("fifth_avenue_phantom_mode_complete")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["fifth_avenue_phantom_mode_points"] = self.mode_points
        player["fifth_avenue_phantom_jackpots"] = self.jackpots_collected
        player["fifth_avenue_phantom_escape_jackpots"] = self.escape_jackpots_collected
        player["fifth_avenue_phantom_best_jackpot"] = self.best_jackpot
        player["fifth_avenue_phantom_rounds"] = self.rounds_started
        player["fifth_avenue_phantom_reveals_used"] = self.reveal_number
        player["fifth_avenue_phantom_current_jackpot"] = self.current_jackpot
        player["fifth_avenue_phantom_timer"] = self.reveal_seconds_left
        player["fifth_avenue_phantom_location"] = self.LOCATION_LABELS[self.current_location] if self.current_location else ""
        player["fifth_avenue_phantom_phase"] = self.phase
        player["fifth_avenue_phantom_shot_assist_used"] = self.shot_assist_used

    def _in_summary_or_done(self):
        if self.mode_done:
            return True

        player = self.machine.game.player
        return player["villain_mode_in_summary"] is True
