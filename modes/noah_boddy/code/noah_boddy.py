import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
Find the Noah Boddy

Rules:
- Get to the upper playfield to start the search.
- Both drop target banks reset and one lower drop target is secretly chosen.
- Upper target hits knock down non-secret lower drop targets.
- Upper spinner builds the Noah Boddy Jackpot.
- When only the secret target remains standing, a hurry-up starts.
- The player has 16s, or 24s with More Time, to return lower and hit the secret target.
- If the hurry-up expires, the secret target drops and the mode fails.
- If the player exits upper left/right before reveal, all remaining drops fall and the player must return upper.
- If a lower drop is hit before reveal, all remaining drops fall and the player must return upper.

Case Files:
- More Jackpots: upper target reveal hits score more points.
- Bigger Jackpot: Noah Boddy Jackpot is worth 2x.
- More Time: hurry-up is 24s instead of 16s.
- Safety Net: starts case-file ball save when the secret target is revealed.
- Shot Assist: rubber hit on the secret target bank collects the jackpot after reveal.
"""


class NoahBoddy(Mode):
    MODE_KEY = "noah_boddy"
    DISPLAY_NAME = "Noah Boddy"

    BASE_JACKPOT = 250_000
    SPINNER_ADD_VALUE = 25_000
    UPPER_TARGET_SCORE = 25_000
    MORE_JACKPOTS_UPPER_TARGET_SCORE = 75_000
    HURRYUP_SECONDS = 16
    MORE_TIME_HURRYUP_SECONDS = 24

    TARGETS = (
        "left_1",
        "left_2",
        "left_3",
        "right_1",
        "right_2",
        "right_3",
        "right_4",
        "right_5",
    )

    TARGET_LABELS = {
        "left_1": "LEFT 1",
        "left_2": "LEFT 2",
        "left_3": "LEFT 3",
        "right_1": "RIGHT 1",
        "right_2": "RIGHT 2",
        "right_3": "RIGHT 3",
        "right_4": "RIGHT 4",
        "right_5": "RIGHT 5",
    }

    TARGET_COILS = {
        "left_1": "c_left_bank_drop_1",
        "left_2": "c_left_bank_drop_2",
        "left_3": "c_left_bank_drop_3",
        "right_1": "c_right_bank_drop_1",
        "right_2": "c_right_bank_drop_2",
        "right_3": "c_right_bank_drop_3",
        "right_4": "c_right_bank_drop_4",
        "right_5": "c_right_bank_drop_5",
    }

    TARGET_BANKS = {
        "left_1": "left",
        "left_2": "left",
        "left_3": "left",
        "right_1": "right",
        "right_2": "right",
        "right_3": "right",
        "right_4": "right",
        "right_5": "right",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "get_to_upper"
        self.secret_target = None
        self.standing_targets = set()
        self.programmatic_drops_pending = set()
        self.jackpot_value = self.BASE_JACKPOT
        self.jackpot_multiplier = 1
        self.hurryup_seconds = self.HURRYUP_SECONDS
        self.hurryup_seconds_left = 0
        self.upper_target_score = self.UPPER_TARGET_SCORE
        self.mode_points = 0
        self.upper_target_hits = 0
        self.spinner_hits = 0
        self.jackpots_collected = 0
        self.best_jackpot = 0

        self._apply_case_file_bonuses()
        self._init_player_vars()
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "UPPER REVEALS SCORE MORE"),
            ("bigger_jackpots", "NOAH BODDY JACKPOT 2X"),
            ("more_time", "HURRY-UP EXTENDED TO 24s"),
            ("safety_net", "SECRET TARGET BALL SAVE"),
            ("shot_assist", "BANK RUBBER SCORES SECRET TARGET"),
        ])

        self.add_mode_event_handler("s_upper_entrance_opto_active", self._upper_entry)
        self.add_mode_event_handler("s_upper_exit_left_opto_active", self._upper_exit)
        self.add_mode_event_handler("s_upper_exit_right_opto_active", self._upper_exit)

        self.add_mode_event_handler("s_upper_target_left_active", self._upper_target_hit)
        self.add_mode_event_handler("s_upper_target_center_active", self._upper_target_hit)
        self.add_mode_event_handler("s_upper_target_right_active", self._upper_target_hit)
        self.add_mode_event_handler("s_trispinner_opto_active", self._spinner_hit)

        self.add_mode_event_handler("s_left_drops_1_active", self._drop_target_hit, target="left_1")
        self.add_mode_event_handler("s_left_drops_2_active", self._drop_target_hit, target="left_2")
        self.add_mode_event_handler("s_left_drops_3_active", self._drop_target_hit, target="left_3")
        self.add_mode_event_handler("s_right_drops_1_active", self._drop_target_hit, target="right_1")
        self.add_mode_event_handler("s_right_drops_2_active", self._drop_target_hit, target="right_2")
        self.add_mode_event_handler("s_right_drops_3_active", self._drop_target_hit, target="right_3")
        self.add_mode_event_handler("s_right_drops_4_active", self._drop_target_hit, target="right_4")
        self.add_mode_event_handler("s_right_drops_5_active", self._drop_target_hit, target="right_5")

        self.add_mode_event_handler("s_left_drops_rubber_active", self._bank_rubber_hit, bank="left")
        self.add_mode_event_handler("s_left_drops_top_left_rubber_active", self._bank_rubber_hit, bank="left")
        self.add_mode_event_handler("s_left_drops_top_right_rubber_active", self._bank_rubber_hit, bank="left")
        self.add_mode_event_handler("s_right_drops_rubber_active", self._bank_rubber_hit, bank="right")
        self.add_mode_event_handler("s_right_drops_top_rubber_active", self._bank_rubber_hit, bank="right")

        self.add_mode_event_handler("noah_boddy_complete_request", self._complete_mode)
        self.add_mode_event_handler("noah_boddy_fail_request", self._complete_mode)

        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("noah_boddy_find_started")
        self.machine.events.post("noah_boddy_get_to_upper")
        self._show_mode_message("FIND THE NOAH BODDY", "GET TO THE ROOF")


    def _show_mode_message(self, title, subtitle="", value="", seconds=""):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
        )

    def _show_mode_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _show_mode_countdown(self, title, seconds, subtitle=""):
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value="",
            message_mode_seconds=seconds,
        )

    def mode_stop(self, **kwargs):
        self.delay.remove("noah_boddy_hurryup_tick")
        self.clear_active_case_file_helpers()
        self.machine.events.post("rooftop_diverter_close")
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        if self.has_case_file("more_jackpots"):
            self.upper_target_score = self.MORE_JACKPOTS_UPPER_TARGET_SCORE

        if self.has_case_file("bigger_jackpots"):
            self.jackpot_multiplier = 2

        if self.has_case_file("more_time"):
            self.hurryup_seconds = self.MORE_TIME_HURRYUP_SECONDS

    def _init_player_vars(self):
        player = self.machine.game.player
        player["noah_boddy_state"] = 2
        player["active_mode_points"] = 0
        player["noah_boddy_upper_target_hits"] = 0
        player["noah_boddy_spinner_hits"] = 0
        player["noah_boddy_jackpots"] = 0
        player["noah_boddy_best_jackpot"] = 0
        player["noah_boddy_jackpot_value"] = self._current_jackpot_value()
        player["noah_boddy_hurryup_seconds"] = 0
        player["noah_boddy_secret_target"] = ""
        player["noah_boddy_phase"] = self.phase
        player["noah_boddy_remaining_targets"] = 0
        player["noah_boddy_secret_revealed"] = 0

    def _upper_entry(self, **kwargs):
        if self._in_summary_or_done():
            return

        self._start_search_cycle()

    def _start_search_cycle(self):
        self.delay.remove("noah_boddy_hurryup_tick")
        self.phase = "revealing"
        self.programmatic_drops_pending.clear()
        self.secret_target = random.choice(list(self.TARGETS))
        self.standing_targets = set(self.TARGETS)
        self.hurryup_seconds_left = 0

        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post(
            "noah_boddy_secret_target_chosen",
            secret_target=self.secret_target,
            secret_label=self.TARGET_LABELS[self.secret_target],
        )
        self.machine.events.post("noah_boddy_search_started")
        self._show_mode_message("SEARCH STARTED", "HIT UPPER TARGETS")
        self._sync_vars()

    def _upper_target_hit(self, **kwargs):
        if self._in_summary_or_done():
            return

        if self.phase == "get_to_upper" or self.phase == "return_to_upper":
            self.machine.events.post("noah_boddy_upper_target_needs_new_search")
            return

        if self.phase != "revealing":
            return

        self.upper_target_hits += 1
        self._score(self.upper_target_score)

        non_secret_targets = [
            target for target in self.standing_targets
            if target != self.secret_target
        ]

        if non_secret_targets:
            target_to_drop = random.choice(non_secret_targets)
            self._drop_programmatically(target_to_drop)
            self.machine.events.post(
                "noah_boddy_non_secret_target_dropped",
                target=target_to_drop,
                target_label=self.TARGET_LABELS[target_to_drop],
                remaining=len(self.standing_targets),
            )

        self.machine.events.post(
            "noah_boddy_upper_target_reveal_hit",
            hits=self.upper_target_hits,
            score=self.upper_target_score,
            remaining=len(self.standing_targets),
        )
        self._show_mode_message("SEARCHING", f"{len(self.standing_targets)} TARGETS LEFT")

        self._check_reveal_complete()
        self._sync_vars()

    def _spinner_hit(self, **kwargs):
        if self._in_summary_or_done():
            return

        if self.phase not in ("revealing", "hurryup"):
            return

        self.spinner_hits += 1
        self.jackpot_value += self.SPINNER_ADD_VALUE
        self.machine.events.post(
            "noah_boddy_jackpot_increased",
            spinner_hits=self.spinner_hits,
            jackpot=self._current_jackpot_value(),
        )
        self._show_mode_jackpot("JACKPOT BUILDS", self._current_jackpot_value())
        self._sync_vars()

    def _upper_exit(self, **kwargs):
        if self._in_summary_or_done():
            return

        if self.phase == "revealing":
            self._collapse_search("upper_exit_before_reveal")

    def _drop_target_hit(self, target=None, **kwargs):
        if self._in_summary_or_done() or not target:
            return

        if target in self.programmatic_drops_pending:
            self.programmatic_drops_pending.discard(target)
            self.delay.remove(f"noah_boddy_programmatic_drop_{target}")
            self.machine.events.post("noah_boddy_programmatic_drop_ignored", target=target)
            return

        if target in self.standing_targets:
            self.standing_targets.remove(target)

        if self.phase == "hurryup":
            if target == self.secret_target:
                self._award_secret_jackpot(source="drop_target")
            return

        if self.phase == "revealing":
            self._collapse_search("lower_drop_before_reveal")
            return

        self._sync_vars()

    def _bank_rubber_hit(self, bank=None, **kwargs):
        if self._in_summary_or_done():
            return

        if self.phase != "hurryup":
            return

        if not self.has_case_file("shot_assist"):
            return

        if bank != self.TARGET_BANKS.get(self.secret_target):
            return

        self._drop_programmatically(self.secret_target)
        self._award_secret_jackpot(source="shot_assist_rubber")

    def _check_reveal_complete(self):
        if self.phase != "revealing":
            return

        if len(self.standing_targets) == 1 and self.secret_target in self.standing_targets:
            self._start_hurryup()

    def _start_hurryup(self):
        self.phase = "hurryup"
        self.hurryup_seconds_left = self.hurryup_seconds
        self.machine.events.post(
            "noah_boddy_secret_revealed",
            secret_target=self.secret_target,
            secret_label=self.TARGET_LABELS[self.secret_target],
            seconds=self.hurryup_seconds_left,
            jackpot=self._current_jackpot_value(),
        )
        self.machine.events.post("noah_boddy_secret_hurryup_started")
        self._show_mode_countdown("SECRET TARGET FOUND", self.hurryup_seconds_left, self.TARGET_LABELS[self.secret_target])

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self._sync_vars()
        self._schedule_hurryup_tick()

    def _schedule_hurryup_tick(self):
        self.delay.remove("noah_boddy_hurryup_tick")
        self.delay.add(
            name="noah_boddy_hurryup_tick",
            ms=1000,
            callback=self._hurryup_tick,
        )

    def _hurryup_tick(self, **kwargs):
        if self._in_summary_or_done() or self.phase != "hurryup":
            return

        self.hurryup_seconds_left -= 1
        self.machine.events.post(
            "noah_boddy_hurryup_tick",
            seconds=self.hurryup_seconds_left,
            jackpot=self._current_jackpot_value(),
        )
        self._show_mode_countdown("HIT SECRET TARGET", self.hurryup_seconds_left, self.TARGET_LABELS[self.secret_target])
        self._sync_vars()

        if self.hurryup_seconds_left <= 0:
            self._hurryup_expired()
            return

        self._schedule_hurryup_tick()

    def _hurryup_expired(self):
        if self.mode_done:
            return

        if self.secret_target:
            self._drop_programmatically(self.secret_target)

        self.machine.events.post("noah_boddy_secret_timer_failed")
        self._show_mode_message("NOAH BODDY ESCAPED", "SECRET TARGET LOST")
        self._fail_mode()

    def _collapse_search(self, reason):
        if self.mode_done:
            return

        self.delay.remove("noah_boddy_hurryup_tick")
        self._drop_all_remaining_targets()
        self.phase = "return_to_upper"
        self.secret_target = None
        self.hurryup_seconds_left = 0
        self.machine.events.post("noah_boddy_search_collapsed", reason=reason)
        self.machine.events.post("noah_boddy_return_to_upper")
        self._show_mode_message("SEARCH LOST", "RETURN TO THE ROOF")
        self._sync_vars()

    def _drop_all_remaining_targets(self):
        for target in list(self.standing_targets):
            self._drop_programmatically(target)

    def _drop_programmatically(self, target):
        if target not in self.TARGET_COILS:
            return

        self.programmatic_drops_pending.add(target)
        self.delay.remove(f"noah_boddy_programmatic_drop_{target}")
        self.delay.add(
            name=f"noah_boddy_programmatic_drop_{target}",
            ms=1500,
            callback=self._clear_programmatic_drop_pending,
            target=target,
        )

        self.machine.coils[self.TARGET_COILS[target]].pulse()

        if target in self.standing_targets:
            self.standing_targets.remove(target)

    def _clear_programmatic_drop_pending(self, target=None, **kwargs):
        if target:
            self.programmatic_drops_pending.discard(target)

    def _award_secret_jackpot(self, source="drop_target"):
        if self.mode_done or not self.hurryup_active:
            return

        self.hurryup_active = False
        self.delay.remove("noah_boddy_hurryup_tick")
        jackpot = self._current_jackpot_value()
        self.jackpots_collected += 1
        self.best_jackpot = max(self.best_jackpot, jackpot)
        self._score(jackpot)
        self.machine.events.post(
            "noah_boddy_secret_jackpot_awarded",
            source=source,
            target=self.secret_target,
            target_label=self.TARGET_LABELS[self.secret_target],
            jackpot=jackpot,
        )
        self._show_mode_jackpot("NOAH BODDY JACKPOT", jackpot, self.TARGET_LABELS[self.secret_target])
        self._sync_vars()
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        player = self.machine.game.player
        player["noah_boddy_state"] = 2
        player["noah_boddy_phase"] = "complete"
        self.machine.events.post("noah_boddy_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        player = self.machine.game.player
        player["noah_boddy_state"] = 2
        player["noah_boddy_phase"] = "goal_missed"
        self.machine.events.post("noah_boddy_mode_complete")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _current_jackpot_value(self):
        return int(self.jackpot_value * self.jackpot_multiplier)

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["noah_boddy_upper_target_hits"] = self.upper_target_hits
        player["noah_boddy_spinner_hits"] = self.spinner_hits
        player["noah_boddy_jackpots"] = self.jackpots_collected
        player["noah_boddy_best_jackpot"] = self.best_jackpot
        player["noah_boddy_jackpot_value"] = self._current_jackpot_value()
        player["noah_boddy_hurryup_seconds"] = self.hurryup_seconds_left
        player["noah_boddy_secret_target"] = self.TARGET_LABELS[self.secret_target] if self.secret_target else ""
        player["noah_boddy_phase"] = self.phase
        player["noah_boddy_remaining_targets"] = len(self.standing_targets)
        player["noah_boddy_secret_revealed"] = 1 if self.phase == "hurryup" else 0

    def _in_summary_or_done(self):
        if self.mode_done:
            return True

        player = self.machine.game.player
        return player["villain_mode_in_summary"] is True
