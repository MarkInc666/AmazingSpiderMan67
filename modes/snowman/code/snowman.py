"""The Snowman villain mode.

Current coded rules:
- Hit either web for 100K (150K with Bigger), then hit the opposite web
  within 16 seconds (20 with More Time) for 250K (350K with Bigger).
- Re-hitting the starting web scores 25K and resets the wire timer; Shot
  Assist lets that repeat hit complete the connection once.
- The first lower-spinner spin defeats Snowman, scores the current spin value,
  and starts a 10-second bonus-spin window (16 seconds with More Time).
- Every spin scores 100K (150K with Bigger). More Jackpots raises the value
  of each following spin by 25K. Zaps are unlimited until the timer expires.
- Safety Net starts a 10-second ball save when the spinner becomes ready.
"""

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Snowman(CaseFileMixin, Mode):
    MODE_KEY = "snowman"
    DISPLAY_NAME = "The Snowman"

    START_WEB_SCORE = 100_000
    BIGGER_START_WEB_SCORE = 150_000
    REPEAT_WEB_SCORE = 25_000
    WIRE_SCORE = 250_000
    BIGGER_WIRE_SCORE = 350_000
    SPIN_SCORE = 100_000
    BIGGER_SPIN_SCORE = 150_000
    MORE_JACKPOTS_STEP = 25_000

    WIRE_SECONDS = 16
    MORE_TIME_WIRE_SECONDS = 20
    SPIN_SECONDS = 10
    MORE_TIME_SPIN_SECONDS = 16

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=1)
        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "idle"
        self.starting_web = None
        self.required_web = None
        self.seconds_left = 0
        self.mode_points = 0
        self.bonus_spins = 0
        self.current_spin_value = self._base_spin_value()
        self.biggest_spin = 0

        player = self.machine.game.player
        player["snowman_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SPIN VALUE +25K EACH SPIN"),
            ("bigger_jackpots", "150K / 350K / 150K"),
            ("more_time", "20 SECOND WIRE / 16 SECOND SPINS"),
            ("safety_net", "10 SECOND SAVE AT SPINNER"),
            ("shot_assist", "STARTING WEB CAN COMPLETE WIRE"),
        ])

        self.add_mode_event_handler("snowman_left_web_hit", self._web_hit, web="left")
        self.add_mode_event_handler("snowman_center_web_hit", self._web_hit, web="center")
        self.add_mode_event_handler("snowman_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("snowman_complete_request", self._finish_mode)
        self.add_mode_event_handler("ball_ending", self._ball_ending)

        self.machine.events.post("snowman_idle_phase")
        self._show_status("HIT EITHER WEB")

    def mode_stop(self, **kwargs):
        self._stop_timer()
        self.machine.events.post("snowman_clear_all")
        self.machine.events.post("snowman_disable_safety_net")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _web_hit(self, web, **kwargs):
        if self.mode_done or self.phase == "spins":
            return

        if self.phase == "idle":
            self._start_wire(web)
            return

        if self.phase != "wire":
            return

        if web == self.required_web:
            self._complete_wire()
            return

        if web != self.starting_web:
            return

        if self.has_case_file("shot_assist"):
            self.machine.events.post("snowman_case_file_shot_assist_used")
            self._complete_wire()
            return

        self._score(self.REPEAT_WEB_SCORE)
        self.seconds_left = self._wire_seconds()
        self.machine.events.post("snowman_wire_extended", web=web, value=self.REPEAT_WEB_SCORE)
        self._show_message("WIRE EXTENDED", "KEEP RUNNING THE WIRE", self.REPEAT_WEB_SCORE)
        self._show_status("RUN THE WIRE", self.seconds_left)
        self._schedule_tick()

    def _start_wire(self, web):
        self.phase = "wire"
        self.starting_web = web
        self.required_web = "center" if web == "left" else "left"
        self.seconds_left = self._wire_seconds()
        value = self.BIGGER_START_WEB_SCORE if self.has_case_file("bigger_jackpots") else self.START_WEB_SCORE
        self._score(value)
        self.machine.events.post("snowman_wire_started", starting_web=web, required_web=self.required_web, value=value)
        self.machine.events.post(f"snowman_{web}_web_solid")
        self.machine.events.post(f"snowman_{self.required_web}_web_pulse")
        self._show_message("WIRE STARTED", "HIT THE OPPOSITE WEB", value)
        self._show_status("RUN THE WIRE", self.seconds_left)
        self._schedule_tick()

    def _complete_wire(self):
        self._stop_timer()
        value = self.BIGGER_WIRE_SCORE if self.has_case_file("bigger_jackpots") else self.WIRE_SCORE
        self._score(value)
        self.phase = "spinner_ready"
        self.seconds_left = 0
        self.machine.events.post("snowman_wire_complete", value=value)
        self.machine.events.post("snowman_spinner_ready")
        if self.has_case_file("safety_net"):
            self.machine.events.post("snowman_enable_safety_net")
        self._show_message("WIRE COMPLETE", "SPIN TO DEFEAT SNOWMAN", value)
        self._show_status("SPIN TO DEFEAT SNOWMAN")
        self._sync_vars()

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.phase not in ("spinner_ready", "spins"):
            return

        value = self.current_spin_value
        self._score(value)
        self.bonus_spins += 1
        self.biggest_spin = max(self.biggest_spin, value)
        self.machine.events.post("snowman_bonus_spin_scored", value=value, spins=self.bonus_spins)

        if self.has_case_file("more_jackpots"):
            self.current_spin_value += self.MORE_JACKPOTS_STEP

        if self.phase == "spinner_ready":
            self.phase = "spins"
            self.seconds_left = self._spin_seconds()
            self.machine.game.player["snowman_state"] = 2
            self.machine.events.post("snowman_defeated")
            self._show_message("SNOWMAN DEFEATED", "BONUS SPINS", value)
            self._show_status("BONUS SPINS", self.seconds_left)
            self._schedule_tick()
        else:
            self.machine.events.post("snowman_spin_flash")
            self._show_message("BONUS SPIN", "KEEP SPINNING", value)
            self._show_status("BONUS SPINS", self.seconds_left)
        self._sync_vars()

    def _schedule_tick(self):
        self.delay.remove("snowman_timer_tick")
        self.delay.add(name="snowman_timer_tick", ms=1000, callback=self._timer_tick)

    def _timer_tick(self):
        if self.mode_done or self.phase not in ("wire", "spins"):
            return
        self.seconds_left -= 1
        self._sync_vars()
        if self.seconds_left <= 0:
            if self.phase == "wire":
                self._wire_timeout()
            else:
                self._finish_mode()
            return
        self._show_status("RUN THE WIRE" if self.phase == "wire" else "BONUS SPINS", self.seconds_left)
        self._schedule_tick()

    def _wire_timeout(self):
        self._stop_timer()
        self.phase = "idle"
        self.starting_web = None
        self.required_web = None
        self.seconds_left = 0
        self.machine.events.post("snowman_wire_broken")
        self.machine.events.post("snowman_idle_phase")
        self._show_message("WIRE BROKEN", "HIT EITHER WEB TO RESTART")
        self._show_status("HIT EITHER WEB")
        self._sync_vars()

    def _finish_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._stop_timer()
        player = self.machine.game.player
        player["snowman_state"] = 2
        self._sync_vars()
        self.machine.events.post("snowman_disable_safety_net")
        self.machine.events.post("snowman_mode_complete")

    def _ball_ending(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._stop_timer()
        self._sync_vars()
        if self.phase != "spins":
            self._show_message("SNOWMAN ESCAPED", "THE WIRE WENT COLD")

    def _wire_seconds(self):
        return self.MORE_TIME_WIRE_SECONDS if self.has_case_file("more_time") else self.WIRE_SECONDS

    def _spin_seconds(self):
        return self.MORE_TIME_SPIN_SECONDS if self.has_case_file("more_time") else self.SPIN_SECONDS

    def _base_spin_value(self):
        return self.BIGGER_SPIN_SCORE if self.has_case_file("bigger_jackpots") else self.SPIN_SCORE

    def _stop_timer(self):
        self.delay.remove("snowman_timer_tick")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["snowman_bonus_spins"] = self.bonus_spins
        player["snowman_biggest_spin"] = self.biggest_spin
        player["snowman_seconds_left"] = self.seconds_left
        player["snowman_phase"] = self.phase

    def _show_status(self, title, seconds=""):
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=title,
            mode_status_value=f"{seconds} SECONDS" if seconds != "" else "",
        )

    def _show_message(self, title, subtitle="", value=""):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
        )
