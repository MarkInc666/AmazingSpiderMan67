import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode

from modes.common.case_file_mixin import CaseFileMixin


class MasterVine(CaseFileMixin, Mode):
    """Master Vine - Vine Invasion three-wave program-and-collect mode."""

    MODE_KEY = "master_vine"
    DISPLAY_NAME = "MASTER VINE"

    ATTEMPTS = 3
    ATTEMPT_SECONDS = 30
    MORE_TIME_SECONDS = 40
    SPINNER_VALUE = 25_000
    JACKPOT_VALUE = 50_000
    BIGGER_JACKPOT_VALUE = 75_000

    SHOTS = (
        "left_web", "center_web", "left_sling", "right_sling",
        "left_pop", "right_pop", "saucer_1", "saucer_2", "saucer_3",
        "left_drop_1", "left_drop_2", "left_drop_3",
        "right_drop_1", "right_drop_2", "right_drop_3",
        "right_drop_4", "right_drop_5", "a", "b", "middle_a",
        "middle_b", "star",
    )

    SHOT_LABELS = {
        "left_web": "LEFT WEB",
        "center_web": "CENTER WEB",
        "left_sling": "LEFT SLING",
        "right_sling": "RIGHT SLING",
        "left_pop": "LEFT POP",
        "right_pop": "RIGHT POP",
        "saucer_1": "SAUCER 1",
        "saucer_2": "SAUCER 2",
        "saucer_3": "SAUCER 3",
        "left_drop_1": "LEFT DROP 1",
        "left_drop_2": "LEFT DROP 2",
        "left_drop_3": "LEFT DROP 3",
        "right_drop_1": "RIGHT DROP 1",
        "right_drop_2": "RIGHT DROP 2",
        "right_drop_3": "RIGHT DROP 3",
        "right_drop_4": "RIGHT DROP 4",
        "right_drop_5": "RIGHT DROP 5",
        "a": "A ROLLOVER",
        "b": "B ROLLOVER",
        "middle_a": "MIDDLE A",
        "middle_b": "MIDDLE B",
        "star": "STAR",
    }

    LEFT_DROPS = {"left_drop_1", "left_drop_2", "left_drop_3"}
    RIGHT_DROPS = {
        "right_drop_1", "right_drop_2", "right_drop_3",
        "right_drop_4", "right_drop_5",
    }
    DROP_SHOTS = LEFT_DROPS | RIGHT_DROPS

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.phase = "waiting_for_upper"
        self.attempt = 0
        self.seconds_left = 0
        self.mode_points = 0
        self.spinner_hits = 0
        self.spinner_hits_this_attempt = 0
        self.jackpot_awards = 0
        self.waves_completed = 0
        self.programmed_shots = set()
        self.collected_shots = set()
        self.drop_shots_down = set()
        self.shot_assist_used = False
        self.safety_net_started = False

        self.attempt_seconds = (
            self.MORE_TIME_SECONDS
            if self.has_case_file("more_time")
            else self.ATTEMPT_SECONDS
        )
        self.jackpot_value = (
            self.BIGGER_JACKPOT_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.JACKPOT_VALUE
        )

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "FIRST SPIN OF EACH WAVE LIGHTS 3 SHOTS"),
            ("bigger_jackpots", "VINE JACKPOTS WORTH 75K"),
            ("more_time", "EACH VINE WAVE LASTS 40 SECONDS"),
            ("safety_net", "10 SECOND SAVE ON FIRST UPPER ENTRY"),
            ("shot_assist", "FIRST JACKPOT COLLECTS A SECOND"),
        ])

        self._register_handlers()
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.machine.events.post("master_vine_shots_reset")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("clear_saucers_delayed")
        self._show_message(
            "VINE INVASION", "GET TO THE ROOF", value="3 WAVES", reminder=True
        )
        self._update_status()

    def mode_stop(self, **kwargs):
        self._clear_delays()
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.machine.events.post("master_vine_all_lights_off")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("reset_drops")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _register_handlers(self):
        self.add_mode_event_handler("master_vine_upper_entrance", self._upper_entrance)
        self.add_mode_event_handler("master_vine_upper_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("master_vine_complete_request", self._complete_mode)
        self.add_mode_event_handler("master_vine_fail_request", self._complete_mode)
        for shot in self.SHOTS:
            self.add_mode_event_handler(
                f"master_vine_{shot}_hit", self._lower_shot_hit, shot=shot
            )

    def _upper_entrance(self, **kwargs):
        if self._done_or_summary() or self.phase not in (
            "waiting_for_upper", "awaiting_return"
        ):
            return
        if self.attempt >= self.ATTEMPTS:
            return

        self.attempt += 1
        self.phase = "attempt_active"
        self.spinner_hits_this_attempt = 0
        self.seconds_left = self.attempt_seconds
        self.programmed_shots.clear()
        self.collected_shots.clear()
        self.drop_shots_down.clear()

        self.machine.events.post("master_vine_shots_reset")
        self.machine.events.post("master_vine_reset_banks")
        self.machine.events.post("master_vine_attempt_started", attempt=self.attempt)
        self.machine.events.post("rooftop_diverter_close")

        if self.has_case_file("safety_net") and not self.safety_net_started:
            self.safety_net_started = True
            self.machine.events.post("start_case_file_ball_save")

        self._show_message(
            f"VINE WAVE {self.attempt}",
            "SPIN TO SPREAD THE VINES",
            value=f"{self.seconds_left} SECONDS",
            reminder=True,
        )
        self._update_status()
        self._schedule_attempt_tick()

    def _spinner_hit(self, **kwargs):
        if self._done_or_summary() or self.phase != "attempt_active":
            return

        self.spinner_hits += 1
        self.spinner_hits_this_attempt += 1
        self._score(self.SPINNER_VALUE)
        self.seconds_left = self.attempt_seconds
        self._schedule_attempt_tick()

        shots_to_light = 1
        if (
            self.has_case_file("more_jackpots")
            and self.spinner_hits_this_attempt == 1
        ):
            shots_to_light = 3

        selected = self._program_random_shots(shots_to_light)
        self.machine.events.post(
            "master_vine_spinner_scored",
            value=self.SPINNER_VALUE,
            selected=len(selected),
        )

        if len(selected) == 1:
            subtitle = f"{self.SHOT_LABELS[selected[0]]} LIT"
        elif selected:
            subtitle = f"{len(selected)} VINE SHOTS LIT"
        else:
            subtitle = "ALL AVAILABLE SHOTS PROGRAMMED"
        self._show_message("VINES SPREAD", subtitle, value=self.SPINNER_VALUE)
        self._update_status()
        self._sync_vars()

    def _program_random_shots(self, count):
        available = [
            shot for shot in self.SHOTS
            if shot not in self.programmed_shots and shot not in self.drop_shots_down
        ]
        if not available:
            return []

        selected = random.sample(available, min(int(count), len(available)))
        for shot in selected:
            self.programmed_shots.add(shot)
            self._refresh_shot_light(shot)
            self.machine.events.post(
                "master_vine_shot_programmed",
                shot=shot,
                shot_label=self.SHOT_LABELS[shot],
            )
        return selected

    def _lower_shot_hit(self, shot=None, **kwargs):
        if self._done_or_summary() or shot not in self.SHOTS:
            return

        if shot in self.DROP_SHOTS:
            self.drop_shots_down.add(shot)

        if self.phase not in ("attempt_active", "awaiting_return"):
            return
        if shot not in self.programmed_shots or shot in self.collected_shots:
            return

        self._collect_shot(shot, assisted=False)
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            remaining_lit = [
                candidate for candidate in self.SHOTS
                if candidate in self.programmed_shots
                and candidate not in self.collected_shots
            ]
            if remaining_lit:
                self._collect_shot(random.choice(remaining_lit), assisted=True)
            else:
                self._award_jackpot(shot, assisted=True, duplicate=True)

        self._update_status()
        self._sync_vars()

    def _collect_shot(self, shot, assisted=False):
        if shot in self.collected_shots:
            return
        self.collected_shots.add(shot)
        self._refresh_shot_light(shot)
        self._award_jackpot(shot, assisted=assisted, duplicate=False)

    def _award_jackpot(self, shot, assisted=False, duplicate=False):
        self.jackpot_awards += 1
        self._score(self.jackpot_value)
        self.machine.events.post(
            "master_vine_jackpot_collected",
            shot=shot,
            shot_label=self.SHOT_LABELS[shot],
            value=self.jackpot_value,
            assisted=assisted,
            duplicate=duplicate,
        )
        title = "SHOT ASSIST" if assisted else "VINE JACKPOT"
        subtitle = self.SHOT_LABELS[shot]
        if duplicate:
            subtitle = f"{subtitle} SCORES AGAIN"
        self._show_jackpot(title, self.jackpot_value, subtitle)

    def _refresh_shot_light(self, shot):
        if shot in self.LEFT_DROPS:
            self._refresh_left_bank_light()
        elif shot in self.collected_shots:
            self.machine.events.post(f"master_vine_{shot}_collected")
        elif shot in self.programmed_shots:
            self.machine.events.post(f"master_vine_{shot}_lit")
        else:
            self.machine.events.post(f"master_vine_{shot}_off")

    def _refresh_left_bank_light(self):
        lit = bool((self.programmed_shots - self.collected_shots) & self.LEFT_DROPS)
        collected = bool(self.collected_shots & self.LEFT_DROPS)
        if lit:
            self.machine.events.post("master_vine_left_bank_lit")
        elif collected:
            self.machine.events.post("master_vine_left_bank_collected")
        else:
            self.machine.events.post("master_vine_left_bank_off")

    def _schedule_attempt_tick(self):
        self.delay.reset(
            name="master_vine_attempt_tick", ms=1000, callback=self._attempt_tick
        )

    def _attempt_tick(self, **kwargs):
        if self._done_or_summary() or self.phase != "attempt_active":
            return
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self.seconds_left = 0
            self._expire_attempt()
            return
        self._update_status()
        self._schedule_attempt_tick()

    def _expire_attempt(self):
        self.delay.remove("master_vine_attempt_tick")
        self.waves_completed += 1
        self.machine.events.post(
            "master_vine_attempt_expired",
            attempt=self.attempt,
            jackpots=len(self.collected_shots),
        )
        self._sync_vars()

        if self.attempt >= self.ATTEMPTS:
            self._show_message(
                "VINE INVASION COMPLETE",
                f"{self.jackpot_awards} JACKPOTS",
                value=self.mode_points,
            )
            self._complete_mode()
            return

        self.phase = "awaiting_return"
        self.machine.events.post("rooftop_diverter_open")
        self._show_message(
            f"WAVE {self.attempt} COMPLETE",
            "RETURN TO THE ROOF",
            value=f"{self.ATTEMPTS - self.attempt} WAVES LEFT",
            reminder=True,
        )
        self._update_status()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("master_vine_mode_complete")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.jackpot_awards
        player["active_mode_major_hits"] = self.waves_completed

    def _update_status(self):
        if self.mode_done:
            return
        if self.phase == "waiting_for_upper":
            title = "VINE INVASION"
            value = "GATE OPEN - GET TO ROOF"
        elif self.phase == "attempt_active":
            lit = len(self.programmed_shots - self.collected_shots)
            title = f"VINE WAVE {self.attempt} - {self.seconds_left}s"
            value = f"{lit} LIT / {len(self.collected_shots)} CLEARED"
        else:
            title = f"WAVE {self.attempt} COMPLETE"
            value = "GATE OPEN - RETURN TO ROOF"
        self.machine.events.post(
            "show_mode_status", mode_status_title=title, mode_status_value=value
        )

    def _show_message(self, title, subtitle="", value="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
            reminder=reminder,
        )

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _clear_delays(self):
        self.delay.remove("master_vine_attempt_tick")

    def _done_or_summary(self):
        player = self.machine.game.player if self.machine.game else None
        return self.mode_done or bool(player and player["villain_mode_in_summary"])
