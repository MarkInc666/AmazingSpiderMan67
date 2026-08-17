from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Conquistador(CaseFileMixin, Mode):
    MODE_KEY = "conquistador"
    DISPLAY_NAME = "The Conquistador"

    DROP_SCORE = 50_000
    SPIN_SCORE = 50_000
    BASE_JACKPOT = 300_000
    BIGGER_BASE_JACKPOT = 400_000
    TARGET_ADD = 100_000
    BIGGER_TARGET_ADD = 150_000
    SPEED_VALUE = 50_000
    NORMAL_SECONDS = 20
    MORE_TIME_SECONDS = 30
    EXTRA_SIP_SECONDS = 10
    REQUIRED_SPINS = 3

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "left_bank"
        self.seconds_left = self.MORE_TIME_SECONDS if self.has_case_file("more_time") else self.NORMAL_SECONDS
        self.spins = 0
        self.target_hits = 0
        self.mode_points = 0
        self.jackpot_points = 0
        self.speed_bonus = 0
        self.jackpot_value = self.BIGGER_BASE_JACKPOT if self.has_case_file("bigger_jackpots") else self.BASE_JACKPOT
        self.locked_extra_jackpot = 0
        self.shot_assist_used = False
        self.extra_sip_pending = False

        player = self.machine.game.player
        player["conquistador_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "TAKE ANOTHER SIP"),
            ("bigger_jackpots", "400K BASE / 150K TARGETS"),
            ("more_time", "30 SECOND TIMERS"),
            ("safety_net", "10 SECOND SAVE AT FOUNTAIN"),
            ("shot_assist", "FIRST TARGET COUNTS TWICE"),
        ])

        self.add_mode_event_handler("conquistador_left_drop_hit", self._left_drop_hit)
        self.add_mode_event_handler("conquistador_left_bank_complete", self._left_bank_complete)
        self.add_mode_event_handler("conquistador_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("conquistador_upper_target_hit", self._upper_target_hit)
        self.add_mode_event_handler("conquistador_center_web_hit", self._center_web_hit)
        self.add_mode_event_handler("conquistador_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("conquistador_complete_request", self._complete_mode)
        self.add_mode_event_handler("conquistador_fail_request", self._fail_main_phase)

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("conquistador_left_bank_phase")
        self._show_status("LEFT DROPS TO OPEN GATE", self.seconds_left)
        self._schedule_tick()

    def _vuk_hit(self, **kwargs):
        """Return a neutral VUK ball while Daily Bugle is disabled."""
        self.machine.events.post("request_vuk_eject", delay_ms=1_000)

    def mode_stop(self, **kwargs):
        self._clear_delays()
        self.machine.events.post("conquistador_clear_lights")
        self.machine.events.post("conquistador_disable_safety_net")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _left_drop_hit(self, **kwargs):
        if self._done() or self.phase != "left_bank":
            return
        self._score(self.DROP_SCORE)
        self.machine.events.post("conquistador_drop_scored", value=self.DROP_SCORE)

    def _left_bank_complete(self, **kwargs):
        if self._done() or self.phase != "left_bank":
            return
        self._award_speed_bonus()
        self._stop_tick()
        self.phase = "spinner"
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("conquistador_gate_open")
        self._show_message("PATH OPEN", "SPIN TO FIND FOUNTAIN")
        self._show_status("SPIN TO FIND FOUNTAIN")
        self._sync_vars()

    def _spinner_hit(self, **kwargs):
        if self._done():
            return
        self._score(self.SPIN_SCORE)
        if self.phase != "spinner":
            return
        self.spins += 1
        self.machine.events.post("conquistador_spin_progress", spins=self.spins)
        if self.spins < self.REQUIRED_SPINS:
            self._show_status("SPIN TO FIND FOUNTAIN")
            self._sync_vars()
            return

        self.phase = "fountain"
        self.seconds_left = self.MORE_TIME_SECONDS if self.has_case_file("more_time") else self.NORMAL_SECONDS
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("conquistador_fountain_ready")
        if self.has_case_file("safety_net"):
            self.machine.events.post("conquistador_enable_safety_net")
        self._show_message("FOUNTAIN FOUND", "HIT FOUNTAIN TO COLLECT", value=self.jackpot_value)
        self._show_status("HIT FOUNTAIN TO COLLECT", self.seconds_left)
        self._schedule_tick()
        self._sync_vars()

    def _upper_target_hit(self, **kwargs):
        if self._done() or self.phase == "extra_sip":
            return
        increments = 1
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            increments = 2
            self.machine.events.post("conquistador_case_file_shot_assist_used")
        self.target_hits += increments
        add_value = self.BIGGER_TARGET_ADD if self.has_case_file("bigger_jackpots") else self.TARGET_ADD
        self.jackpot_value += add_value * increments
        self.machine.events.post("conquistador_jackpot_increased", value=self.jackpot_value)
        if self.phase == "fountain":
            self._show_status("TARGETS INCREASE JP", self.seconds_left)
        self._sync_vars()

    def _center_web_hit(self, **kwargs):
        if self._done():
            return
        if self.phase == "fountain":
            self._collect_first_jackpot()
        elif self.phase == "extra_sip":
            self._collect_second_jackpot()

    def _collect_first_jackpot(self):
        self._stop_tick()
        self._award_speed_bonus()
        value = self.jackpot_value
        self.locked_extra_jackpot = value
        self._score(value)
        self.jackpot_points += value
        self.machine.events.post("conquistador_fountain_jackpot", value=value)
        self._show_jackpot("FOUNTAIN JACKPOT", value)
        self._sync_vars()

        if not self.has_case_file("more_jackpots"):
            self.delay.add(name="conquistador_finish_after_jackpot", ms=2000, callback=self._complete_mode)
            return

        self.phase = "extra_sip_wait"
        self.extra_sip_pending = True
        self.delay.add(name="conquistador_extra_sip_start", ms=2000, callback=self._start_extra_sip)

    def _start_extra_sip(self):
        if self._done() or not self.extra_sip_pending:
            return
        self.extra_sip_pending = False
        self.phase = "extra_sip"
        self.seconds_left = self.EXTRA_SIP_SECONDS
        self.machine.events.post("conquistador_extra_sip_started")
        self._show_message("TAKE ANOTHER SIP", "HIT FOUNTAIN AGAIN", value=self.locked_extra_jackpot)
        self._show_status("TAKE ANOTHER SIP", self.seconds_left)
        self._schedule_tick()

    def _collect_second_jackpot(self):
        self._stop_tick()
        self._award_speed_bonus()
        value = self.locked_extra_jackpot
        self._score(value)
        self.jackpot_points += value
        self.machine.events.post("conquistador_second_fountain_jackpot", value=value)
        self._show_jackpot("FOUNTAIN JACKPOT", value, "ANOTHER SIP")
        self._sync_vars()
        self.delay.add(name="conquistador_finish_after_second", ms=2000, callback=self._complete_mode)

    def _schedule_tick(self):
        self.delay.remove("conquistador_timer_tick")
        self.delay.add(name="conquistador_timer_tick", ms=1000, callback=self._timer_tick)

    def _timer_tick(self):
        if self._done() or self.phase not in ("left_bank", "fountain", "extra_sip"):
            return
        self.seconds_left -= 1
        self._sync_vars()
        if self.seconds_left <= 0:
            if self.phase == "extra_sip":
                self._finish_wasted_youth()
            else:
                self._fail_main_phase()
            return
        if self.phase == "left_bank":
            self._show_status("LEFT DROPS TO OPEN GATE", self.seconds_left)
        elif self.phase == "fountain":
            self._show_status("HIT FOUNTAIN TO COLLECT", self.seconds_left)
        else:
            self._show_status("TAKE ANOTHER SIP", self.seconds_left)
        self._schedule_tick()

    def _award_speed_bonus(self):
        bonus = max(0, int(self.seconds_left)) * self.SPEED_VALUE
        if bonus <= 0:
            return
        self.speed_bonus += bonus
        self._score(bonus)
        self.machine.events.post("conquistador_speed_bonus", value=bonus, seconds=self.seconds_left)
        self._show_message("SPEED BONUS", f"{self.seconds_left} SECONDS LEFT", value=bonus)

    def _fail_main_phase(self, **kwargs):
        if self._done():
            return
        self._stop_tick()
        self.mode_done = True
        self.machine.game.player["conquistador_state"] = 2
        self.machine.events.post("rooftop_diverter_close")
        self._show_message("FOUNTAIN NOT FOUND", "THE CONQUISTADOR ESCAPES")
        self.machine.events.post("conquistador_mode_complete")

    def _finish_wasted_youth(self):
        if self._done():
            return
        self._stop_tick()
        self.mode_done = True
        self.machine.game.player["conquistador_state"] = 2
        self._show_message("WASTED YOUTH", "THE SECOND SIP IS LOST")
        self.machine.events.post("conquistador_mode_complete")

    def _complete_mode(self, **kwargs):
        if self._done():
            return
        self._stop_tick()
        self.mode_done = True
        self.machine.game.player["conquistador_state"] = 2
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("conquistador_mode_complete")

    def _clear_delays(self):
        for name in (
            "conquistador_timer_tick",
            "conquistador_finish_after_jackpot",
            "conquistador_extra_sip_start",
            "conquistador_finish_after_second",
        ):
            self.delay.remove(name)

    def _stop_tick(self):
        self.delay.remove("conquistador_timer_tick")

    def _done(self):
        return self.mode_done or self.phase == "summary"

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += int(points)
        self.mode_points += int(points)
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["conquistador_jackpot_points"] = self.jackpot_points
        player["conquistador_speed_bonus"] = self.speed_bonus
        player["conquistador_jackpot_value"] = self.jackpot_value
        player["conquistador_target_hits"] = self.target_hits
        player["conquistador_spins"] = self.spins
        player["conquistador_seconds_left"] = max(0, self.seconds_left)

    def _show_status(self, text, seconds=""):
        self.machine.events.post(
            "show_mode_countdown" if seconds != "" else "show_mode_message",
            message_mode_title=text,
            message_mode_subtitle="",
            message_mode_value=self.jackpot_value if self.phase in ("fountain", "extra_sip") else "",
            message_mode_seconds=seconds,
            reminder=True,
        )

    def _show_message(self, title, subtitle="", value=""):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )
