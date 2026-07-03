from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin

"""
Vulcan - Volcano Unleashed

Rules:
- Starts 2-ball multiball.
- Upper gate is open during the mode; Daily Bugle/VUK handling remains global.
- Lower spinner scores 20K and builds the Vulcan Jackpot.
- Base jackpot is 100K. With Bigger Jackpots, base is 150K.
- Spinner adds +20K to jackpot normally, +30K with Bigger Jackpots.
- Right drops collect the current jackpot and stay down.
- The right bank does not auto-reset when all 5 are down.
- Upper-left exit resets the right bank and adds +50K to the jackpot.
- Upper targets score 25K each. Complete all 3 to add-a-ball if below 3 balls.
- If already at 3 balls, upper target completion awards 250K Eruption Bonus.
- When down to 1 ball, a Cooling Timer starts. Spinner hits reset it.
- Cooling Timer is 16s normally, 24s with More Time. If it expires at 1 ball, mode ends.
- More Jackpots: when all 5 right drops are down, light right rubber for one Bonus Jackpot.
- Safety Net: when first down to 1 ball, start one 10s case-file ball save.
- Shot Assist: first right-drop hit also drops/collects one additional right target.
"""


class Vulcan(CaseFileMixin, Mode):
    MODE_KEY = "vulcan"
    DISPLAY_NAME = "Vulcan"

    BASE_JACKPOT = 100_000
    BIGGER_BASE_JACKPOT = 150_000
    SPINNER_SCORE = 20_000
    SPINNER_BUILD = 20_000
    BIGGER_SPINNER_BUILD = 30_000
    UPPER_TARGET_SCORE = 25_000
    SPINNER_BONUS_BANK = 2_000
    VULCAN_JACKPOT_BONUS_BANK = 50_000
    UPPER_TARGET_BONUS_START = 75_000
    UPPER_TARGET_BONUS_STEP = 25_000
    UPPER_LEFT_EXIT_BUILD = 50_000
    ERUPTION_BONUS = 250_000
    COOLING_SECONDS = 10
    MORE_TIME_COOLING_SECONDS = 16
    MAX_BALLS = 3

    RIGHT_DROPS = (1, 2, 3, 4, 5)
    UPPER_TARGETS = ("left", "center", "right")

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.mode_points = 0
        self.spinner_hits = 0
        self.jackpot_value = self.BIGGER_BASE_JACKPOT if self.has_case_file("bigger_jackpots") else self.BASE_JACKPOT
        self.spinner_build_value = self.BIGGER_SPINNER_BUILD if self.has_case_file("bigger_jackpots") else self.SPINNER_BUILD
        self.cooling_seconds = self.MORE_TIME_COOLING_SECONDS if self.has_case_file("more_time") else self.COOLING_SECONDS
        self.cooling_active = False
        self.cooling_seconds_left = 0
        self.safety_net_used = False

        self.right_drops_down = set()
        self.upper_targets_hit = set()
        self.jackpots_collected = 0
        self.bonus_jackpot_lit = False
        self.bonus_jackpot_collected = False
        self.add_a_balls_awarded = 0
        self.eruption_bonuses = 0
        self.shot_assist_used = False
        self.upper_target_bonus_value = self.UPPER_TARGET_BONUS_START

        self._sync_vars()
        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "RUBBER BONUS JACKPOT AFTER 5 DROPS"),
            ("bigger_jackpots", "150K BASE / +30K JP PER SPIN"),
            ("more_time", "COOLING TIMER EXTENDED TO 24s"),
            ("safety_net", "10 SECOND BALL SAVE AT 1 BALL"),
            ("shot_assist", "FIRST DROP COLLECTS AN EXTRA DROP"),
        ])

        self.add_mode_event_handler("vulcan_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("vulcan_upper_left_exit", self._upper_left_exit)
        self.add_mode_event_handler("vulcan_bonus_rubber_hit", self._bonus_rubber_hit)
        self.add_mode_event_handler("vulcan_multiball_ended", self._check_single_ball_phase)
        self.add_mode_event_handler("vulcan_add_a_ball_started", self._add_a_ball_started)
        self.add_mode_event_handler("vulcan_check_cooling", self._check_single_ball_phase)
        self.add_mode_event_handler("vulcan_complete_request", self._complete_mode)
        self.add_mode_event_handler("vulcan_fail_request", self._complete_mode)

        for number in self.RIGHT_DROPS:
            self.add_mode_event_handler(
                f"vulcan_right_drop_{number}_hit",
                self._right_drop_hit,
                number=number,
            )

        for target in self.UPPER_TARGETS:
            self.add_mode_event_handler(
                f"vulcan_upper_target_{target}_hit",
                self._upper_target_hit,
                target=target,
            )

        self.machine.events.post("vulcan_setup")
        self.machine.events.post("vulcan_start_multiball")
        self.machine.events.post("vulcan_mode_intro")
        self._show_mode_message("VOLCANO UNLEASHED", "SPINNER BUILDS - DROPS COLLECT")

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.delay.remove("vulcan_cooling_tick")
        self.delay.remove("vulcan_reset_upper_targets_after_flash")
        self.machine.events.post("vulcan_clear_all_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _spinner_hit(self, **kwargs):
        if self._done():
            return

        self.spinner_hits += 1
        self._score(self.SPINNER_SCORE)
        self._bank_vulcan_bonus(self.SPINNER_BONUS_BANK)
        self.jackpot_value += self.spinner_build_value
        self.machine.events.post("vulcan_jackpot_built", value=self.jackpot_value)

        if self.cooling_active:
            self._start_cooling_timer()

        self._sync_vars()

    def _right_drop_hit(self, number=None, **kwargs):
        if self._done() or number is None:
            return

        if number in self.right_drops_down:
            return

        self._collect_right_drop(number)

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            extra = self._first_available_right_drop(exclude=number)
            if extra is not None:
                self.machine.events.post(f"vulcan_shot_assist_drop_{extra}")
                self.machine.events.post(f"vulcan_right_drop_{extra}_hit")

        self._check_more_jackpots_bonus()
        self._sync_vars()

    def _collect_right_drop(self, number):
        self.right_drops_down.add(number)
        self.jackpots_collected += 1
        self._score(self.jackpot_value)
        self._bank_vulcan_bonus(self.VULCAN_JACKPOT_BONUS_BANK)
        self.machine.events.post("vulcan_right_drop_collected", number=number, value=self.jackpot_value)
        self.machine.events.post(f"vulcan_right_drop_{number}_collected")
        self._show_mode_jackpot("VULCAN JACKPOT", self.jackpot_value, f"DROP {number}")

    def _upper_left_exit(self, **kwargs):
        if self._done():
            return

        self.right_drops_down.clear()
        self.jackpot_value += self.UPPER_LEFT_EXIT_BUILD
        self.bonus_jackpot_lit = False
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("vulcan_right_bank_reloaded")
        self.machine.events.post("vulcan_jackpot_built", value=self.jackpot_value)
        self._show_mode_message("BANK RELOADED", "+50K TO JACKPOT", self.jackpot_value)
        self._sync_vars()

    def _upper_target_hit(self, target=None, **kwargs):
        if self._done() or target not in self.UPPER_TARGETS:
            return

        if target in self.upper_targets_hit:
            return

        self.upper_targets_hit.add(target)
        self._score(self.UPPER_TARGET_SCORE)
        self.machine.events.post(f"vulcan_upper_target_{target}_collected")
        self._sync_vars()

        if len(self.upper_targets_hit) >= 3:
            self._complete_upper_targets()

    def _complete_upper_targets(self):
        self.machine.events.post("vulcan_upper_targets_completed")
        self._bank_vulcan_bonus(self.upper_target_bonus_value)
        self.machine.events.post("vulcan_upper_target_bonus_banked", value=self.upper_target_bonus_value)
        self.upper_target_bonus_value += self.UPPER_TARGET_BONUS_STEP

        if self._balls_in_play() < self.MAX_BALLS:
            self.add_a_balls_awarded += 1
            self.machine.events.post("vulcan_add_a_ball")
            self.machine.events.post("vulcan_add_a_ball_awarded")
            self._show_mode_message("ADD-A-BALL", "VULCAN ERUPTS AGAIN")
        else:
            self.eruption_bonuses += 1
            self._score(self.ERUPTION_BONUS)
            self.machine.events.post("vulcan_eruption_bonus_awarded", value=self.ERUPTION_BONUS)
            self._show_mode_jackpot("ERUPTION BONUS", self.ERUPTION_BONUS)

        self._sync_vars()
        self.delay.remove("vulcan_reset_upper_targets_after_flash")
        self.delay.add(
            name="vulcan_reset_upper_targets_after_flash",
            ms=650,
            callback=self._reset_upper_targets,
        )

    def _reset_upper_targets(self):
        if self._done():
            return

        self.upper_targets_hit.clear()
        self.machine.events.post("vulcan_upper_targets_reset")
        self._sync_vars()

    def _bonus_rubber_hit(self, **kwargs):
        if self._done():
            return

        if not self.has_case_file("more_jackpots"):
            return

        if not self.bonus_jackpot_lit or self.bonus_jackpot_collected:
            self._score(self.UPPER_TARGET_SCORE)
            return

        self.bonus_jackpot_collected = True
        self.bonus_jackpot_lit = False
        self._score(self.jackpot_value)
        self._bank_vulcan_bonus(self.VULCAN_JACKPOT_BONUS_BANK)
        self.machine.events.post("vulcan_bonus_jackpot_collected", value=self.jackpot_value)
        self._show_mode_jackpot("RUBBER BONUS JACKPOT", self.jackpot_value)
        self._sync_vars()

    def _check_more_jackpots_bonus(self):
        if not self.has_case_file("more_jackpots"):
            return

        if self.bonus_jackpot_collected or self.bonus_jackpot_lit:
            return

        if len(self.right_drops_down) >= len(self.RIGHT_DROPS):
            self.bonus_jackpot_lit = True
            self.machine.events.post("vulcan_bonus_jackpot_lit", value=self.jackpot_value)
            self._show_mode_message("BONUS JACKPOT", "HIT THE RUBBER", self.jackpot_value)

    def _add_a_ball_started(self, **kwargs):
        self._cancel_cooling_timer()
        self.delay.add(name="vulcan_check_cooling_after_add", ms=1500, callback=self._check_single_ball_phase)
        self._sync_vars()

    def _check_single_ball_phase(self, **kwargs):
        if self._done():
            return

        if self._balls_in_play() <= 1:
            if self.has_case_file("safety_net") and not self.safety_net_used:
                self.safety_net_used = True
                self.machine.events.post("start_case_file_ball_save")
                self.machine.events.post("vulcan_safety_net_started")
            self._start_cooling_timer()
        else:
            self._cancel_cooling_timer()

        self._sync_vars()

    def _start_cooling_timer(self):
        if self._done():
            return

        self.cooling_active = True
        self.cooling_seconds_left = self.cooling_seconds
        self.machine.events.post("vulcan_cooling_started", seconds=self.cooling_seconds_left)
        self._show_mode_countdown("COOLING TIMER", self.cooling_seconds_left, "SPINNER RESETS TIMER")
        self.delay.remove("vulcan_cooling_tick")
        self.delay.add(name="vulcan_cooling_tick", ms=1000, callback=self._cooling_tick)
        self._sync_vars()

    def _cooling_tick(self):
        if self._done() or not self.cooling_active:
            return

        if self._balls_in_play() > 1:
            self._cancel_cooling_timer()
            return

        self.cooling_seconds_left -= 1
        self.machine.events.post("vulcan_cooling_tick", seconds=self.cooling_seconds_left)
        self.machine.events.post("update_mode_status", mode_status_title="SECONDS LEFT", mode_status_value=max(0, self.cooling_seconds_left))
        self._sync_vars()

        if self.cooling_seconds_left <= 0:
            self._complete_mode()
            return

        self.delay.add(name="vulcan_cooling_tick", ms=1000, callback=self._cooling_tick)

    def _cancel_cooling_timer(self):
        if self.cooling_active:
            self.machine.events.post("vulcan_cooling_cancelled")
        self.cooling_active = False
        self.cooling_seconds_left = 0
        self.delay.remove("vulcan_cooling_tick")
        self.machine.events.post("hide_mode_status")
        self._sync_vars()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self._cancel_cooling_timer()
        self._set(f"{self.MODE_KEY}_state", 2)
        self._set(f"{self.MODE_KEY}_state", 2)
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")

    def _first_available_right_drop(self, exclude=None):
        for number in self.RIGHT_DROPS:
            if number == exclude:
                continue
            if number not in self.right_drops_down:
                return number
        return None

    def _bank_vulcan_bonus(self, value):
        self._add("vulcan_bonus", value)

    def _score(self, points):
        self._add("score", points)
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        self._set("active_mode_points", self.mode_points)
        self._set("active_mode_hits", self.jackpots_collected + self.spinner_hits)
        self._set("active_mode_major_hits", self.add_a_balls_awarded + self.eruption_bonuses)
        self._set("vulcan_spinner_hits", self.spinner_hits)
        self._set("vulcan_jackpot_value", self.jackpot_value)
        self._set("vulcan_jackpots_collected", self.jackpots_collected)
        self._set("vulcan_right_drops_down", len(self.right_drops_down))
        self._set("vulcan_bonus_jackpot_lit", int(self.bonus_jackpot_lit))
        self._set("vulcan_bonus_jackpot_collected", int(self.bonus_jackpot_collected))
        self._set("vulcan_upper_left_hit", int("left" in self.upper_targets_hit))
        self._set("vulcan_upper_center_hit", int("center" in self.upper_targets_hit))
        self._set("vulcan_upper_right_hit", int("right" in self.upper_targets_hit))
        self._set("vulcan_upper_targets_completed", len(self.upper_targets_hit) >= 3)
        self._set("vulcan_add_a_balls", self.add_a_balls_awarded)
        self._set("vulcan_eruption_bonuses", self.eruption_bonuses)
        self._set("vulcan_cooling_active", int(self.cooling_active))
        self._set("vulcan_cooling_seconds", self.cooling_seconds_left)
        self._set("vulcan_balls_in_play", self._balls_in_play())
        self._set("vulcan_upper_target_bonus_value", self.upper_target_bonus_value)

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

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return self.machine.game.balls_in_play

    def _done(self):
        return self.mode_done

    def _get(self, name, default=0):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return default
        try:
            return player[name]
        except KeyError:
            return default

    def _set(self, name, value):
        player = self.machine.game.player if self.machine.game else None
        if player:
            player[name] = value

    def _add(self, name, value):
        player = self.machine.game.player if self.machine.game else None
        if player:
            player[name] += value
