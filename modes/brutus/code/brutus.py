from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Brutus(CaseFileMixin, Mode):
    """Brutus — lure the bodyguard away and recover the artwork."""

    MODE_KEY = "brutus"
    DISPLAY_NAME = "Brutus"

    LURE_SCORE = 50_000
    BLOCKED_SAUCER_SCORE = 25_000
    JACKPOT_SCORE = 250_000
    BIGGER_JACKPOT_SCORE = 400_000

    JACKPOTS_TO_COMPLETE = 3
    MORE_JACKPOTS_TO_COMPLETE = 4
    WINDOW_SECONDS = 15
    MORE_TIME_SECONDS = 20
    ROUND_TRANSITION_MS = 1_000
    SHOT_ASSIST_DELAY_MS = 2_000
    VUK_EJECT_MS = 1_000

    RIGHT_TARGETS = (1, 2, 3, 4, 5)
    SAUCER_EJECT_EVENTS = {
        1: "delayed_kickout_saucer_1",
        2: "delayed_kickout_saucer_2",
        3: "delayed_kickout_saucer_3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.case_files = self.get_case_file_bonuses()
        self.required_jackpots = (
            self.MORE_JACKPOTS_TO_COMPLETE
            if self.has_case_file("more_jackpots")
            else self.JACKPOTS_TO_COMPLETE
        )

        self.mode_done = False
        self.phase = "guarded"
        self.seconds_left = 0
        self.lures = 0
        self.jackpots = 0
        self.blocked_saucers = 0
        self.biggest_jackpot = 0
        self.mode_points = 0
        self.shot_assist_used = False

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "FOUR ARTWORK JACKPOTS AVAILABLE"),
            ("bigger_jackpots", "ARTWORK JACKPOTS SCORE 400K"),
            ("more_time", "BRUTUS STAYS AWAY FOR 20 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE"),
            ("shot_assist", "OPENING RIGHT BANK DROPS AFTER 2 SECONDS"),
        ])

        for target in self.RIGHT_TARGETS:
            self.add_mode_event_handler(
                f"brutus_right_drop_{target}_hit",
                self._right_drop_hit,
                target=target,
            )

        self.add_mode_event_handler("brutus_left_drop_hit", self._left_drop_hit)
        self.add_mode_event_handler("brutus_saucer_1_hit", self._saucer_hit, saucer=1)
        self.add_mode_event_handler("brutus_saucer_2_hit", self._saucer_hit, saucer=2)
        self.add_mode_event_handler("brutus_saucer_3_hit", self._saucer_hit, saucer=3)
        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)
        self.add_mode_event_handler("ball_ending", self._ball_ending)

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.machine.events.post("brutus_clear_all")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self._begin_guarded_round()

        if self.has_case_file("shot_assist"):
            self.delay.reset(
                name="brutus_shot_assist",
                ms=self.SHOT_ASSIST_DELAY_MS,
                callback=self._shot_assist_opening,
            )

    def mode_stop(self, **kwargs):
        self._stop_window_timer()
        for delay_name in (
            "brutus_shot_assist",
            "brutus_round_transition",
            "brutus_finish",
        ):
            self.delay.remove(delay_name)

        self.machine.events.post("brutus_clear_all")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _begin_guarded_round(self):
        if self.mode_done:
            return

        self.phase = "guarded"
        self.seconds_left = 0
        self.machine.events.post("brutus_clear_shots")
        self.machine.events.post("brutus_guarded_lights")
        self._show_message(
            "BRUTUS GUARDS THE ART",
            "HIT ANY RIGHT DROP",
            reminder=True,
        )
        self._update_status()
        self._sync_vars()

    def _right_drop_hit(self, target, **kwargs):
        if self.mode_done or self.phase != "guarded":
            return

        self.delay.remove("brutus_shot_assist")
        self.shot_assist_used = self.has_case_file("shot_assist")
        self._score(self.LURE_SCORE)
        self.lures += 1
        self._open_saucer_window(assisted=False, hit_target=target)

    def _shot_assist_opening(self):
        if self.mode_done or self.phase != "guarded" or self.shot_assist_used:
            return

        self.shot_assist_used = True
        self.machine.events.post("brutus_case_file_shot_assist_used")
        self._open_saucer_window(assisted=True, hit_target=None)

    def _open_saucer_window(self, assisted, hit_target):
        # Change phase before firing knockdown coils. Their switch events must
        # not be interpreted as additional player lures.
        self.phase = "open"
        self.seconds_left = self._window_seconds()

        for target in self.RIGHT_TARGETS:
            if assisted or target != hit_target:
                self.machine.drop_targets[f"dt_right_{target}"].knockdown()

        self.machine.events.post("brutus_clear_shots")
        self.machine.events.post("brutus_saucers_open")
        self.machine.events.post(
            "brutus_lured_away",
            assisted=assisted,
            seconds=self.seconds_left,
        )
        title = "SHOT ASSIST — BRUTUS LURED" if assisted else "BRUTUS LURED AWAY"
        self._show_message(title, "SHOOT ANY SAUCER", value=self.seconds_left)
        self._update_status()
        self._sync_vars()
        self._schedule_window_tick()

    def _left_drop_hit(self, **kwargs):
        if self.mode_done or self.phase != "open":
            return

        self.machine.events.post("brutus_returned_early")
        self._end_window(
            title="BRUTUS CAME BACK",
            subtitle="SAUCERS GUARDED — TRY AGAIN",
        )

    def _saucer_hit(self, saucer, **kwargs):
        if self.mode_done:
            self._eject_saucer(saucer)
            return

        if self.phase != "open":
            self._score(self.BLOCKED_SAUCER_SCORE)
            self.blocked_saucers += 1
            self._sync_vars()
            self.machine.events.post("brutus_guarded_saucer_hit", saucer=saucer)
            self._show_message("BLOCKED BY BRUTUS", "LURE HIM WITH A RIGHT DROP", value=self.BLOCKED_SAUCER_SCORE)
            self._eject_saucer(saucer)
            return

        value = self._jackpot_value()
        self._score(value)
        self.jackpots += 1
        self.biggest_jackpot = max(self.biggest_jackpot, value)
        self._stop_window_timer()
        self.phase = "transition"
        self.machine.events.post("brutus_clear_shots")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post(
            "brutus_artwork_jackpot_collected",
            saucer=saucer,
            value=value,
            jackpots=self.jackpots,
            required=self.required_jackpots,
        )
        self._show_message(
            "ARTWORK JACKPOT",
            f"{self.jackpots} OF {self.required_jackpots}",
            value=self._format_score(value),
            event="show_mode_jackpot",
        )
        terminal_saucer = self.jackpots >= self.required_jackpots
        if terminal_saucer:
            self.machine.events.post("villain_summary_hold_saucer_until_done")
        self._eject_saucer(saucer)
        self._sync_vars()

        if terminal_saucer:
            self.mode_done = True
            self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
            self.delay.reset(
                name="brutus_finish",
                ms=self.ROUND_TRANSITION_MS,
                callback=lambda: self.machine.events.post("brutus_mode_complete"),
            )
            return

        self._schedule_next_round()

    def _schedule_window_tick(self):
        self.delay.reset(
            name="brutus_window_tick",
            ms=1_000,
            callback=self._window_tick,
        )

    def _window_tick(self):
        if self.mode_done or self.phase != "open":
            return

        self.seconds_left = max(0, self.seconds_left - 1)
        self._sync_vars()
        if self.seconds_left <= 0:
            self.machine.events.post("brutus_window_expired")
            self._end_window(
                title="BRUTUS RETURNED",
                subtitle="SAUCERS GUARDED — TRY AGAIN",
            )
            return

        self._update_status()
        self._schedule_window_tick()

    def _end_window(self, title, subtitle):
        self._stop_window_timer()
        self.phase = "transition"
        self.machine.events.post("brutus_clear_shots")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self._show_message(title, subtitle)
        self._schedule_next_round()

    def _schedule_next_round(self):
        self.delay.reset(
            name="brutus_round_transition",
            ms=self.ROUND_TRANSITION_MS,
            callback=self._begin_guarded_round,
        )

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            return
        self.machine.events.post("request_vuk_eject", delay_ms=self.VUK_EJECT_MS)

    def _ball_ending(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._stop_window_timer()
        self._sync_vars()
        self._show_message("BRUTUS ESCAPED", "THE ARTWORK IS STILL GUARDED")

    def _stop_window_timer(self):
        self.delay.remove("brutus_window_tick")
        self.seconds_left = 0

    def _eject_saucer(self, saucer):
        event = self.SAUCER_EJECT_EVENTS.get(int(saucer))
        if event:
            self.machine.events.post(event)

    def _window_seconds(self):
        return self.MORE_TIME_SECONDS if self.has_case_file("more_time") else self.WINDOW_SECONDS

    def _jackpot_value(self):
        return self.BIGGER_JACKPOT_SCORE if self.has_case_file("bigger_jackpots") else self.JACKPOT_SCORE

    def _score(self, value):
        value = int(value)
        player = self.machine.game.player
        player["score"] += value
        self.mode_points += value

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.jackpots
        player["active_mode_stat_2"] = self.biggest_jackpot
        player["brutus_blocked_saucers"] = self.blocked_saucers
        player["brutus_seconds_left"] = self.seconds_left

    def _update_status(self):
        if self.mode_done:
            return
        if self.phase == "open":
            title = f"ARTWORK {self.jackpots}/{self.required_jackpots}"
            value = f"SHOOT SAUCER  {self.seconds_left}s"
        else:
            title = f"ARTWORK {self.jackpots}/{self.required_jackpots}"
            value = "HIT ANY RIGHT DROP"
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _show_message(self, title, subtitle="", value="", event="show_mode_message", reminder=False):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            reminder=reminder,
        )

    @staticmethod
    def _format_score(value):
        return f"{int(value):,}"
