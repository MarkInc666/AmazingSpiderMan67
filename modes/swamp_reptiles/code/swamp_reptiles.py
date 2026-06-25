from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin

"""
SwampReptiles — Swamp Rampage

- Pops build Rampage and light jackpot shots, one new shot every 3 pops.
- Lit jackpot shots are added in order: left-bank middle drop, upper middle target,
  right-bank middle drop, and center web target if More Jackpots is active.
- Lit jackpot shots may be collected in any order.
- Each pop scores an increasing value and increases the current Rampage Jackpot.
- Each Rampage Jackpot collect scores the current jackpot value and adds that
  value into the Super Jackpot total.
- After the 3rd jackpot collect, or 4th with More Jackpots, saucer 2 lights for
  the Super Jackpot. Pops reset the Super timer.
"""


class SwampReptiles(CaseFileMixin, Mode):
    MODE_KEY = "swamp_reptiles"

    POP_SCORE_START = 20_000
    POP_SCORE_ADD = 1_000
    POP_SCORE_MAX = 50_000

    JACKPOT_ADD_PER_POP = 25_000
    JACKPOT_MAX = 500_000

    SUPER_TIMER_SECONDS = 10
    MORE_TIME_SUPER_TIMER_SECONDS = 16

    LEFT_BANK_SHOT = "left_bank"
    UPPER_MIDDLE_SHOT = "upper_middle"
    RIGHT_BANK_SHOT = "right_bank"
    CENTER_WEB_SHOT = "center_web"

    BASE_SHOT_ORDER = [LEFT_BANK_SHOT, UPPER_MIDDLE_SHOT, RIGHT_BANK_SHOT]
    MORE_JACKPOTS_SHOT_ORDER = [
        LEFT_BANK_SHOT,
        UPPER_MIDDLE_SHOT,
        RIGHT_BANK_SHOT,
        CENTER_WEB_SHOT,
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.super_lit = False
        self.super_collected = False
        self.rooftop_gate_open = False

        self.case_files = self.get_case_file_bonuses()
        self.more_jackpots_active = self.has_case_file("more_jackpots")
        self.bigger_jackpots_active = self.has_case_file("bigger_jackpots")
        self.more_time_active = self.has_case_file("more_time")
        self.shot_assist_active = self.has_case_file("shot_assist")

        self.shot_order = (
            list(self.MORE_JACKPOTS_SHOT_ORDER)
            if self.more_jackpots_active
            else list(self.BASE_SHOT_ORDER)
        )
        self.required_jackpots = len(self.shot_order)

        self.pop_hits = 0
        self.pop_score_value = self.POP_SCORE_START
        self.current_jackpot_value = 0
        self.super_jackpot_value = 0
        self.jackpots_collected = 0
        self.mode_points = 0
        self.rampage_level = 0

        self.lit_shots = set()
        self.collected_shots = set()
        self.shots_activated = 0

        self.publish_case_file_bonus_events("swamp_reptiles")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "CENTER WEB RAMPAGE JACKPOT ADDED"),
            ("bigger_jackpots", "SWAMP REPTILES JACKPOTS 2X"),
            ("more_time", "SUPER TIMER EXTENDED TO 16s"),
            ("safety_net", "BALL SAVE DURING RAMPAGE"),
            ("shot_assist", "LEFT BANK ASSIST AVAILABLE"),
        ])

        player = self.machine.game.player
        player["swamp_reptiles_state"] = 2
        self._sync_vars()

        self.add_mode_event_handler("swamp_reptiles_pop_hit", self._pop_hit)
        for target in [1, 2, 3]:
            self.add_mode_event_handler(
                f"swamp_reptiles_left_drop_{target}_hit",
                self._left_drop_hit,
                target=target,
            )

        for target in [1, 2, 3, 4, 5]:
            self.add_mode_event_handler(
                f"swamp_reptiles_right_drop_{target}_hit",
                self._right_drop_hit,
                target=target,
            )
        self.add_mode_event_handler("swamp_reptiles_upper_middle_hit", self._upper_middle_hit)
        self.add_mode_event_handler("swamp_reptiles_center_web_hit", self._center_web_hit)
        self.add_mode_event_handler("swamp_reptiles_saucer_2_hit", self._saucer_2_hit)
        self.add_mode_event_handler("swamp_reptiles_fail_request", self._complete_mode)

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.machine.events.post("swamp_reptiles_startup_complete")
        self._show_mode_message("SWAMP RAMPAGE", "HIT POPS TO LIGHT JACKPOTS")
        self.machine.events.post("swamp_reptiles_clear_all_lights")
        self.machine.events.post("clear_saucers")
        self._update_rooftop_gate()
        self._sync_vars()


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
        self.machine.events.post("hide_mode_status")
        self.delay.remove("swamp_reptiles_super_timer")
        self._close_rooftop_gate()
        self.clear_active_case_file_helpers()
        self.machine.events.post("swamp_reptiles_clear_all_lights")
        self.machine.events.post("clear_saucers")
        super().mode_stop(**kwargs)

    def _pop_hit(self, **kwargs):
        if self._in_summary_or_done():
            return

        self.pop_hits += 1
        self._score(self.pop_score_value)
        self.pop_score_value = min(
            self.POP_SCORE_MAX,
            self.pop_score_value + self.POP_SCORE_ADD,
        )

        if not self.super_lit:
            self.current_jackpot_value = min(
                self.JACKPOT_MAX,
                self.current_jackpot_value + self.JACKPOT_ADD_PER_POP,
            )
            self._maybe_light_next_rampage_shot()
        else:
            self._restart_super_timer()

        self._sync_vars()
        self.machine.events.post(
            "swamp_reptiles_pop_scored",
            pop_hits=self.pop_hits,
            jackpot_value=self._display_jackpot_value(),
        )

    def _maybe_light_next_rampage_shot(self):
        shots_to_light = min(self.required_jackpots, self.pop_hits // 3)
        self.rampage_level = shots_to_light

        while self.shots_activated < shots_to_light:
            next_shot = self.shot_order[self.shots_activated]
            self.shots_activated += 1
            self._light_rampage_shot(next_shot)

    def _light_rampage_shot(self, shot):
        if shot in self.collected_shots:
            return

        self.lit_shots.add(shot)
        self.machine.events.post(f"swamp_reptiles_{shot}_lit")
        self.machine.events.post("swamp_reptiles_rampage_shot_lit", shot=shot)
        self._show_mode_message("RAMPAGE SHOT LIT", self._shot_display_name(shot))

        if shot == self.LEFT_BANK_SHOT:
            self._stage_left_bank()
        elif shot == self.RIGHT_BANK_SHOT:
            self._stage_right_bank()

        self._update_rooftop_gate()

    def _stage_left_bank(self):
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")

        # Normal rule: leave only the middle drop standing.
        # Shot Assist: leave all three standing; any left-bank drop can collect.
        if not self.shot_assist_active:
            self.delay.add(
                ms=350,
                callback=self._drop_left_outer_targets,
                name="swamp_reptiles_stage_left_bank",
            )

    def _stage_right_bank(self):
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.delay.add(
            ms=350,
            callback=self._drop_right_non_middle_targets,
            name="swamp_reptiles_stage_right_bank",
        )

    def _drop_left_outer_targets(self):
        if self._in_summary_or_done() or self.LEFT_BANK_SHOT not in self.lit_shots:
            return
        self.machine.coils["c_left_bank_drop_1"].pulse()
        self.machine.coils["c_left_bank_drop_3"].pulse()

    def _drop_right_non_middle_targets(self):
        if self._in_summary_or_done() or self.RIGHT_BANK_SHOT not in self.lit_shots:
            return
        for target in [1, 2, 4, 5]:
            self.machine.coils[f"c_right_bank_drop_{target}"].pulse()

    def _left_drop_hit(self, target=None, **kwargs):
        if self._in_summary_or_done() or self.super_lit:
            return
        if self.LEFT_BANK_SHOT not in self.lit_shots:
            return
        if target == 2 or self.shot_assist_active:
            self._collect_rampage_jackpot(self.LEFT_BANK_SHOT)

    def _right_drop_hit(self, target=None, **kwargs):
        if self._in_summary_or_done() or self.super_lit:
            return
        if self.RIGHT_BANK_SHOT not in self.lit_shots:
            return
        if target == 3:
            self._collect_rampage_jackpot(self.RIGHT_BANK_SHOT)

    def _upper_middle_hit(self, **kwargs):
        if self._in_summary_or_done() or self.super_lit:
            return
        if self.UPPER_MIDDLE_SHOT in self.lit_shots:
            self._collect_rampage_jackpot(self.UPPER_MIDDLE_SHOT)

    def _center_web_hit(self, **kwargs):
        if self._in_summary_or_done() or self.super_lit:
            return
        if self.CENTER_WEB_SHOT in self.lit_shots:
            self._collect_rampage_jackpot(self.CENTER_WEB_SHOT)

    def _collect_rampage_jackpot(self, shot):
        if shot in self.collected_shots:
            return

        jackpot_value = self._display_jackpot_value()
        self.collected_shots.add(shot)
        self.lit_shots.discard(shot)
        self.jackpots_collected += 1
        self.super_jackpot_value += jackpot_value
        self._score(jackpot_value)

        self.machine.events.post(f"swamp_reptiles_{shot}_collected")
        self.machine.events.post(
            "swamp_reptiles_rampage_jackpot_collected",
            shot=shot,
            value=jackpot_value,
            collected=self.jackpots_collected,
            required=self.required_jackpots,
        )
        self._show_mode_jackpot("RAMPAGE JACKPOT", jackpot_value, self._shot_display_name(shot))

        if self.jackpots_collected >= self.required_jackpots:
            self._light_super_jackpot()
        else:
            self._update_rooftop_gate()

        self._sync_vars()
        self._refresh_lights()

    def _light_super_jackpot(self):
        if self.super_lit:
            return

        self.super_lit = True
        self._close_rooftop_gate()
        self.machine.events.post("swamp_reptiles_clear_rampage_lights")
        self.machine.events.post("swamp_reptiles_super_jackpot_lit")
        self._show_mode_jackpot("SUPER JACKPOT LIT", self.super_jackpot_value, "SAUCER 2")
        self.machine.events.post("reset_drops")
        self._restart_super_timer()

    def _restart_super_timer(self):
        if self._in_summary_or_done() or not self.super_lit:
            return

        seconds = self._super_timer_seconds()
        self.delay.remove("swamp_reptiles_super_timer")
        self.delay.add(
            ms=seconds * 1000,
            callback=self._super_timer_expired,
            name="swamp_reptiles_super_timer",
        )
        self.machine.events.post("swamp_reptiles_super_timer_started", seconds=seconds)
        self._show_mode_countdown("HIT SAUCER 2", seconds, "SUPER JACKPOT")
        self._sync_vars()

    def _super_timer_expired(self):
        if self._in_summary_or_done():
            return
        self.machine.events.post("swamp_reptiles_super_timer_expired")
        self._show_mode_message("SWAMP REPTILES ESCAPED", "SUPER TIMER EXPIRED")
        self._fail_mode()

    def _saucer_2_hit(self, **kwargs):
        if self._in_summary_or_done():
            return
        if not self.super_lit:
            self.machine.events.post("swamp_reptiles_saucer_unlit")
            return

        self.super_collected = True
        self.super_lit = False
        self._score(self.super_jackpot_value)
        self.machine.events.post(
            "swamp_reptiles_super_jackpot_collected",
            value=self.super_jackpot_value,
        )
        self._show_mode_jackpot("SWAMP REPTILES SUPER JACKPOT", self.super_jackpot_value)
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("swamp_reptiles_super_timer")
        self._close_rooftop_gate()
        player = self.machine.game.player
        player["swamp_reptiles_state"] = 2
        self._sync_vars()
        self.machine.events.post("swamp_reptiles_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("swamp_reptiles_super_timer")
        self._close_rooftop_gate()
        player = self.machine.game.player
        player["swamp_reptiles_state"] = 2
        self._sync_vars()
        self.machine.events.post("swamp_reptiles_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _display_jackpot_value(self):
        value = self.current_jackpot_value
        if self.bigger_jackpots_active:
            value *= 2
        return value

    def _super_timer_seconds(self):
        if self.more_time_active:
            return self.MORE_TIME_SUPER_TIMER_SECONDS
        return self.SUPER_TIMER_SECONDS

    def _shot_display_name(self, shot):
        names = {
            self.LEFT_BANK_SHOT: "LEFT DROP",
            self.UPPER_MIDDLE_SHOT: "UPPER MIDDLE",
            self.RIGHT_BANK_SHOT: "RIGHT DROP",
            self.CENTER_WEB_SHOT: "CENTER WEB",
        }
        return names.get(shot, str(shot).upper())

    def _refresh_lights(self):
        self.machine.events.post("swamp_reptiles_clear_rampage_lights")
        for shot in self.lit_shots:
            self.machine.events.post(f"swamp_reptiles_{shot}_lit")
        if self.super_lit:
            self.machine.events.post("swamp_reptiles_super_jackpot_lit")
        self._update_rooftop_gate()

    def _update_rooftop_gate(self):
        if self._in_summary_or_done():
            return
        if self.UPPER_MIDDLE_SHOT in self.lit_shots and not self.super_lit:
            self._open_rooftop_gate()
        else:
            self._close_rooftop_gate()

    def _open_rooftop_gate(self):
        if self.rooftop_gate_open:
            return
        self.rooftop_gate_open = True
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("swamp_reptiles_rooftop_gate_opened")

    def _close_rooftop_gate(self):
        if not self.rooftop_gate_open:
            return
        self.rooftop_gate_open = False
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("swamp_reptiles_rooftop_gate_closed")

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["swamp_reptiles_pop_hits"] = self.pop_hits
        player["swamp_reptiles_rampage_level"] = self.rampage_level
        player["swamp_reptiles_current_jackpot"] = self._display_jackpot_value()
        player["swamp_reptiles_super_jackpot"] = self.super_jackpot_value
        player["swamp_reptiles_jackpots_collected"] = self.jackpots_collected
        player["swamp_reptiles_jackpots_required"] = self.required_jackpots
        player["swamp_reptiles_pop_score_value"] = self.pop_score_value
        player["swamp_reptiles_super_lit"] = 1 if self.super_lit else 0
        player["swamp_reptiles_super_timer_seconds"] = self._super_timer_seconds()

    def _in_summary_or_done(self):
        if self.mode_done:
            return True
        player = self.machine.game.player
        return player["villain_mode_in_summary"] is True
