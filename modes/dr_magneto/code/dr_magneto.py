from mpf.core.delays import DelayManager
from mpf.core.mode import Mode

from modes.common.case_file_mixin import CaseFileMixin


class DrMagneto(CaseFileMixin, Mode):
    """Dr. Magneto: cross-feed the A/B rollovers into the pop bumpers."""

    MODE_KEY = "dr_magneto"
    DISPLAY_NAME = "DR. MAGNETO"

    ROLLOVER_VALUE = 100_000
    BIGGER_ROLLOVER_VALUE = 150_000
    POP_VALUE = 250_000
    STAR_VALUE = 250_000
    SUPER_VALUE = 500_000
    BIGGER_SUPER_VALUE = 750_000

    OBJECTIVE_SECONDS = 8
    MORE_TIME_OBJECTIVE_SECONDS = 10
    STAR_SECONDS = 6
    SUPER_SECONDS = 16
    MORE_TIME_SUPER_SECONDS = 20
    OBJECTIVE_FAST_AFTER_MS = 4_000
    SUPER_CHASE_FAST_AFTER_MS = 8_000

    POP_FOR_ROLLOVER = {"a": "left", "b": "right"}

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.phase = "circuits"
        self.mode_points = 0
        self.rollovers_collected = 0
        self.pops_completed = 0
        self.super_jackpots = 0
        self.seconds_left = 0
        self.shot_assist_used = False
        self.star_lit = False
        self.rollover_lit = {"a": False, "b": False}
        self.pop_state = {"left": "off", "right": "off"}

        self.objective_seconds = (
            self.MORE_TIME_OBJECTIVE_SECONDS
            if self.has_case_file("more_time")
            else self.OBJECTIVE_SECONDS
        )
        self.super_seconds = (
            self.MORE_TIME_SUPER_SECONDS
            if self.has_case_file("more_time")
            else self.SUPER_SECONDS
        )

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "NEW OBJECTIVES LIGHT STAR FOR 250K"),
            ("bigger_jackpots", "150K ROLLOVERS / 750K SUPER"),
            ("more_time", "10 SECOND CIRCUITS / 20 SECOND SUPER"),
            ("safety_net", "10 SECOND OPENING BALL SAVE"),
            ("shot_assist", "FIRST QUALIFIER LIGHTS A AND B"),
        ])

        self.add_mode_event_handler("dr_magneto_left_qualifier_hit", self._qualifier_hit, side="left")
        self.add_mode_event_handler("dr_magneto_right_qualifier_hit", self._qualifier_hit, side="right")
        self.add_mode_event_handler("dr_magneto_a_rollover_hit", self._rollover_hit, rollover="a")
        self.add_mode_event_handler("dr_magneto_b_rollover_hit", self._rollover_hit, rollover="b")
        self.add_mode_event_handler("dr_magneto_left_pop_hit", self._pop_hit, side="left")
        self.add_mode_event_handler("dr_magneto_right_pop_hit", self._pop_hit, side="right")
        self.add_mode_event_handler("dr_magneto_center_web_hit", self._center_web_hit)
        self.add_mode_event_handler("dr_magneto_star_hit", self._star_hit)
        self.add_mode_event_handler("dr_magneto_complete_request", self._complete_mode)
        self.add_mode_event_handler("dr_magneto_fail_request", self._fail_mode)

        self.machine.events.post("dr_magneto_clear_all")
        self.machine.events.post("dr_magneto_left_qualifier_ready")
        self.machine.events.post("dr_magneto_right_qualifier_ready")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")
        self._show_message("DR. MAGNETO", "SLINGS AND INLANES LIGHT A / B", reminder=True)
        self._update_status()

    def mode_stop(self, **kwargs):
        self._clear_delays()
        self.machine.events.post("dr_magneto_clear_all")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _qualifier_hit(self, side=None, **kwargs):
        if self.mode_done or self.phase != "circuits" or side not in ("left", "right"):
            return

        rollover = "a" if side == "left" else "b"

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            newly_lit = False
            for assisted_rollover in ("a", "b"):
                newly_lit = self._light_rollover(assisted_rollover, light_star=False) or newly_lit
            if newly_lit:
                self._light_star()
            self.machine.events.post("dr_magneto_shot_assist_used")
        else:
            self._light_rollover(rollover)

        self._update_status()
        self._sync_vars()

    def _light_rollover(self, rollover, light_star=True):
        pop_side = self.POP_FOR_ROLLOVER[rollover]
        if self.pop_state[pop_side] == "solid":
            return False

        timer_name = f"dr_magneto_{rollover}_timeout"
        was_lit = self.rollover_lit[rollover]
        self.rollover_lit[rollover] = True
        self.delay.reset(
            name=timer_name,
            ms=self.objective_seconds * 1000,
            callback=self._rollover_expired,
            rollover=rollover,
        )
        self.delay.reset(
            name=f"dr_magneto_{rollover}_fast_delay",
            ms=self.OBJECTIVE_FAST_AFTER_MS,
            callback=self._objective_fast,
            objective=rollover,
        )
        self.machine.events.post(f"dr_magneto_{rollover}_lit")
        qualifier_side = "left" if rollover == "a" else "right"
        self.machine.events.post(f"dr_magneto_{qualifier_side}_qualifier_stop")

        if was_lit:
            self.machine.events.post(
                "dr_magneto_rollover_timer_restarted",
                rollover=rollover,
                seconds=self.objective_seconds,
            )
            return False

        self.machine.events.post(
            "dr_magneto_objective_lit",
            objective=rollover,
            seconds=self.objective_seconds,
        )
        if light_star:
            self._light_star()
        return True

    def _rollover_expired(self, rollover):
        if self.mode_done or self.phase != "circuits" or not self.rollover_lit[rollover]:
            return
        self.rollover_lit[rollover] = False
        self.delay.remove(f"dr_magneto_{rollover}_fast_delay")
        self.machine.events.post(f"dr_magneto_{rollover}_expired")
        qualifier_side = "left" if rollover == "a" else "right"
        self.machine.events.post(f"dr_magneto_{qualifier_side}_qualifier_ready")
        self._update_status()
        self._sync_vars()

    def _rollover_hit(self, rollover=None, **kwargs):
        if (
            self.mode_done
            or self.phase != "circuits"
            or rollover not in self.rollover_lit
            or not self.rollover_lit[rollover]
        ):
            return

        self.rollover_lit[rollover] = False
        self.delay.remove(f"dr_magneto_{rollover}_timeout")
        self.delay.remove(f"dr_magneto_{rollover}_fast_delay")
        self.machine.events.post(f"dr_magneto_{rollover}_collected")

        value = (
            self.BIGGER_ROLLOVER_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.ROLLOVER_VALUE
        )
        self.rollovers_collected += 1
        self._score(value)
        pop_side = self.POP_FOR_ROLLOVER[rollover]
        self._light_pop(pop_side)
        self._show_message(
            f"{rollover.upper()} CIRCUIT COMPLETE",
            f"HIT {pop_side.upper()} POP",
            value=value,
        )
        self._update_status()
        self._sync_vars()

    def _light_pop(self, side):
        if self.pop_state[side] == "solid":
            return

        was_flashing = self.pop_state[side] == "flashing"
        self.pop_state[side] = "flashing"
        self.delay.reset(
            name=f"dr_magneto_{side}_pop_timeout",
            ms=self.objective_seconds * 1000,
            callback=self._pop_expired,
            side=side,
        )
        self.delay.reset(
            name=f"dr_magneto_{side}_pop_fast_delay",
            ms=self.OBJECTIVE_FAST_AFTER_MS,
            callback=self._objective_fast,
            objective=f"{side}_pop",
        )
        self.machine.events.post(f"dr_magneto_{side}_pop_flashing")
        if was_flashing:
            return

        self.machine.events.post(
            "dr_magneto_objective_lit",
            objective=f"{side}_pop",
            seconds=self.objective_seconds,
        )
        self._light_star()

    def _pop_expired(self, side):
        if self.mode_done or self.phase != "circuits" or self.pop_state[side] != "flashing":
            return
        self.pop_state[side] = "off"
        self.delay.remove(f"dr_magneto_{side}_pop_fast_delay")
        self.machine.events.post(f"dr_magneto_{side}_pop_expired")
        self.machine.events.post(f"dr_magneto_{side}_qualifier_ready")
        self._show_message("POP CIRCUIT LOST", f"RELIGHT {side.upper()} POP")
        self._update_status()
        self._sync_vars()

    def _pop_hit(self, side=None, **kwargs):
        if (
            self.mode_done
            or self.phase != "circuits"
            or side not in self.pop_state
            or self.pop_state[side] != "flashing"
        ):
            return

        self.pop_state[side] = "solid"
        self.delay.remove(f"dr_magneto_{side}_pop_timeout")
        self.delay.remove(f"dr_magneto_{side}_pop_fast_delay")
        self.pops_completed += 1
        self._score(self.POP_VALUE)
        self.machine.events.post(f"dr_magneto_{side}_pop_solid")
        self._show_message("POP MAGNETIZED", f"{side.upper()} POP COMPLETE", value=self.POP_VALUE)

        if all(state == "solid" for state in self.pop_state.values()):
            self._stage_super()
        else:
            self._update_status()
        self._sync_vars()

    def _stage_super(self):
        if self.mode_done or self.phase != "circuits":
            return
        self.phase = "super"
        self.seconds_left = self.super_seconds
        self.machine.events.post("dr_magneto_left_qualifier_stop")
        self.machine.events.post("dr_magneto_right_qualifier_stop")
        self.machine.events.post("dr_magneto_super_ready")
        self.machine.events.post(
            "dr_magneto_objective_lit",
            objective="center_web_super",
            seconds=self.super_seconds,
        )
        self._light_star()
        self._show_countdown("MAGNETO SUPER", self.seconds_left, "HIT CENTER WEB")
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="SECONDS LEFT",
            mode_status_value=self.seconds_left,
        )
        self.delay.reset(
            name="dr_magneto_super_chase_fast_delay",
            ms=self.SUPER_CHASE_FAST_AFTER_MS,
            callback=self._super_chase_fast,
        )
        self._schedule_super_tick()
        self._sync_vars()

    def _schedule_super_tick(self):
        self.delay.reset(name="dr_magneto_super_tick", ms=1000, callback=self._super_tick)

    def _super_tick(self):
        if self.mode_done or self.phase != "super":
            return
        self.seconds_left = max(0, self.seconds_left - 1)
        if self.seconds_left <= 0:
            self.machine.events.post("dr_magneto_super_expired")
            self._show_message("DR. MAGNETO ESCAPED", "SUPER EXPIRED")
            self._fail_mode()
            return
        self.machine.events.post(
            "update_mode_status",
            mode_status_title="SECONDS LEFT",
            mode_status_value=self.seconds_left,
        )
        self._schedule_super_tick()
        self._sync_vars()

    def _center_web_hit(self, **kwargs):
        if self.mode_done or self.phase != "super":
            return
        self.delay.remove("dr_magneto_super_tick")
        self.delay.remove("dr_magneto_super_chase_fast_delay")
        value = self.BIGGER_SUPER_VALUE if self.has_case_file("bigger_jackpots") else self.SUPER_VALUE
        self.super_jackpots = 1
        self._score(value)
        self.machine.events.post("dr_magneto_super_collected", value=value)
        self._show_jackpot("MAGNETO SUPER", value)
        self.machine.events.post("play_mode_super_jackpot")
        self._complete_mode()

    def _light_star(self):
        if not self.has_case_file("more_jackpots") or self.mode_done:
            return
        self.star_lit = True
        self.delay.reset(
            name="dr_magneto_star_timeout",
            ms=self.STAR_SECONDS * 1000,
            callback=self._star_expired,
        )
        self.machine.events.post("dr_magneto_star_lit", seconds=self.STAR_SECONDS)

    def _star_hit(self, **kwargs):
        if self.mode_done or not self.star_lit:
            return
        self.star_lit = False
        self.delay.remove("dr_magneto_star_timeout")
        self._score(self.STAR_VALUE)
        self.machine.events.post("dr_magneto_star_collected", value=self.STAR_VALUE)
        self._show_message("MAGNETIC STAR", "MORE JACKPOTS", value=self.STAR_VALUE)
        self._sync_vars()

    def _star_expired(self):
        if self.mode_done or not self.star_lit:
            return
        self.star_lit = False
        self.machine.events.post("dr_magneto_star_expired")
        self._sync_vars()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("dr_magneto_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._clear_delays()
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("dr_magneto_mode_complete")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.rollovers_collected + self.pops_completed
        player["active_mode_stat_2"] = self.super_jackpots

    def _objective_fast(self, objective):
        if self.mode_done or self.phase != "circuits":
            return
        if objective in self.rollover_lit and self.rollover_lit[objective]:
            self.machine.events.post(f"dr_magneto_{objective}_fast")
        elif objective.endswith("_pop"):
            side = objective.removesuffix("_pop")
            if self.pop_state.get(side) == "flashing":
                self.machine.events.post(f"dr_magneto_{side}_pop_fast")

    def _super_chase_fast(self):
        if not self.mode_done and self.phase == "super":
            self.machine.events.post("dr_magneto_super_chase_fast")

    def _update_status(self):
        if self.mode_done or self.phase != "circuits":
            return
        left = "SOLID" if self.pop_state["left"] == "solid" else "BUILD"
        right = "SOLID" if self.pop_state["right"] == "solid" else "BUILD"
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="MAGNETIC CIRCUITS",
            mode_status_value=f"LEFT {left} / RIGHT {right}",
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

    def _show_countdown(self, title, seconds, subtitle=""):
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value="",
            message_mode_seconds=seconds,
        )

    def _show_jackpot(self, title, value):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle="DR. MAGNETO DEFEATED",
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _clear_delays(self):
        for name in (
            "dr_magneto_a_timeout",
            "dr_magneto_b_timeout",
            "dr_magneto_a_fast_delay",
            "dr_magneto_b_fast_delay",
            "dr_magneto_left_pop_timeout",
            "dr_magneto_right_pop_timeout",
            "dr_magneto_left_pop_fast_delay",
            "dr_magneto_right_pop_fast_delay",
            "dr_magneto_star_timeout",
            "dr_magneto_super_tick",
            "dr_magneto_super_chase_fast_delay",
        ):
            self.delay.remove(name)
