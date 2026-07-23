from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class ProfessorPretoris(CaseFileMixin, Mode):
    MODE_KEY = "professor_pretoris"
    BAND_SCORE = 100_000
    MAIN_SUPER_BASE = 1_000_000
    MAIN_SUPER_BIG = 1_500_000
    OVERFLOW_BASE = 500_000
    OVERFLOW_BIG = 750_000
    MAIN_SECONDS = 20
    MAIN_SECONDS_MORE_TIME = 30
    OVERFLOW_SECONDS = 10

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.phase = "flood"
        self.bands_blue = 0
        self.seconds_left = 0
        self.mode_points = 0
        self.hits = 0
        self.major_hits = 0
        self.shot_assist_used = False
        self.case_files = self.get_case_file_bonuses()

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_shared_vars()

        self.add_mode_event_handler("s_web_spinner_active", self._spinner_hit)
        self.add_mode_event_handler("s_web_target_mid_active", self._center_web_hit)
        self.add_mode_event_handler("s_web_target_left_active", self._left_web_hit)
        self.add_mode_event_handler("professor_pretoris_main_timer_tick", self._main_timer_tick)
        self.add_mode_event_handler("professor_pretoris_overflow_timer_tick", self._overflow_timer_tick)
        self.add_mode_event_handler("professor_pretoris_complete_request", self._complete_mode)
        self.add_mode_event_handler("professor_pretoris_fail_request", self._fail_mode)

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "LEFT WEB REACTOR OVERFLOW SUPER"),
            ("bigger_jackpots", "SUPER JACKPOTS INCREASED"),
            ("more_time", "MAIN SUPER TIMER 30 SECONDS"),
            ("safety_net", "BALL SAVE WHEN MAIN SUPER LIGHTS"),
            ("shot_assist", "FIRST SPIN FLOODS TWO BANDS"),
        ])

        self.machine.events.post("professor_pretoris_flood_started")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self._show_status("FLOOD THE REACTOR", "SPIN 8 TIMES", value="0 / 8", reminder=True)

    def mode_stop(self, **kwargs):
        self.delay.remove("pretoris_timer")
        self.machine.events.post("professor_pretoris_clear_lights")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.phase != "flood" or self.bands_blue >= 8:
            return
        conversions = 1
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            conversions = 2
        converted = 0
        for _ in range(conversions):
            if self.bands_blue >= 8:
                break
            self.bands_blue += 1
            converted += 1
            self.machine.events.post(f"professor_pretoris_band_{self.bands_blue}_blue")
        if converted:
            self.hits += converted
            self._score(self.BAND_SCORE * converted)
            self.machine.events.post("professor_pretoris_band_converted", bands_blue=self.bands_blue, converted=converted)
            self._show_status("REACTOR FLOODING", f"{self.bands_blue} / 8 BLUE", value=self.BAND_SCORE * converted)
        if self.bands_blue >= 8:
            self._start_main_super()

    def _start_main_super(self):
        self.phase = "main_super"
        self.seconds_left = self.MAIN_SECONDS_MORE_TIME if self.has_case_file("more_time") else self.MAIN_SECONDS
        self.machine.events.post("professor_pretoris_main_super_ready")
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")
        self._show_status("SUPER JACKPOT", "CENTER WEB", seconds=self.seconds_left, reminder=True)
        self._schedule_timer("professor_pretoris_main_timer_tick")

    def _center_web_hit(self, **kwargs):
        if self.mode_done or self.phase != "main_super":
            return
        self.delay.remove("pretoris_timer")
        value = self.MAIN_SUPER_BIG if self.has_case_file("bigger_jackpots") else self.MAIN_SUPER_BASE
        self.major_hits += 1
        self._score(value)
        self.machine.events.post("professor_pretoris_main_super_collected", value=value)
        self._show_status("SUPER JACKPOT", "REACTOR FLOODED", value=value, event="show_mode_jackpot")
        if self.has_case_file("more_jackpots"):
            self._start_overflow_super()
        else:
            self._complete_mode()

    def _start_overflow_super(self):
        self.phase = "overflow_super"
        self.seconds_left = self.OVERFLOW_SECONDS
        self.machine.events.post("professor_pretoris_overflow_super_ready")
        self._show_status("REACTOR OVERFLOW", "LEFT WEB", seconds=self.seconds_left, reminder=True)
        self._schedule_timer("professor_pretoris_overflow_timer_tick")

    def _left_web_hit(self, **kwargs):
        if self.mode_done or self.phase != "overflow_super":
            return
        self.delay.remove("pretoris_timer")
        value = self.OVERFLOW_BIG if self.has_case_file("bigger_jackpots") else self.OVERFLOW_BASE
        self.major_hits += 1
        self._score(value)
        self.machine.events.post("professor_pretoris_overflow_super_collected", value=value)
        self._show_status("MAGNETIC OVERFLOW", "SUPER JACKPOT", value=value, event="show_mode_jackpot")
        self._complete_mode()

    def _schedule_timer(self, event):
        self.delay.reset(name="pretoris_timer", ms=1000, callback=lambda: self.machine.events.post(event))

    def _main_timer_tick(self, **kwargs):
        if self.mode_done or self.phase != "main_super":
            return
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self.machine.events.post("professor_pretoris_main_super_expired")
            self._fail_mode()
            return
        self._show_status("SUPER JACKPOT", "CENTER WEB", seconds=self.seconds_left)
        self._schedule_timer("professor_pretoris_main_timer_tick")

    def _overflow_timer_tick(self, **kwargs):
        if self.mode_done or self.phase != "overflow_super":
            return
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self.machine.events.post("professor_pretoris_overflow_super_expired")
            self._complete_mode()
            return
        self._show_status("REACTOR OVERFLOW", "LEFT WEB", seconds=self.seconds_left)
        self._schedule_timer("professor_pretoris_overflow_timer_tick")

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("pretoris_timer")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("professor_pretoris_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("pretoris_timer")
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("professor_pretoris_mode_complete")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_shared_vars()

    def _sync_shared_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.hits
        player["active_mode_major_hits"] = self.major_hits

    def _show_status(self, title, subtitle="", value="", seconds="", event="show_mode_message", reminder=False):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )
