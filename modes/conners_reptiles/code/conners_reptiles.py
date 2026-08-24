import random

from mpf.core.mode import Mode

from modes.common.case_file_mixin import CaseFileMixin


class ConnersReptiles(CaseFileMixin, Mode):
    """Conner's Reptiles: pops reveal swamp Jackpot shots."""

    MODE_KEY = "conners_reptiles"

    POP_VALUE = 25_000
    SWAMP_BONUS_PER_POP = 50_000
    JACKPOT_VALUE = 100_000
    BIGGER_JACKPOT_VALUE = 150_000
    SUPER_VALUE = 500_000

    UPPER_A_SHOT = "upper_a"
    UPPER_B_SHOT = "upper_b"
    MIDDLE_A_SHOT = "middle_a"
    MIDDLE_B_SHOT = "middle_b"
    LEFT_WEB_SHOT = "left_web"
    CENTER_WEB_SHOT = "center_web"
    SAUCERS_SHOT = "saucers"
    STAR_SHOT = "star"

    BASE_SHOTS = (
        UPPER_A_SHOT,
        UPPER_B_SHOT,
        MIDDLE_A_SHOT,
        MIDDLE_B_SHOT,
        LEFT_WEB_SHOT,
        CENTER_WEB_SHOT,
        SAUCERS_SHOT,
    )

    SHOT_NAMES = {
        UPPER_A_SHOT: "UPPER A",
        UPPER_B_SHOT: "UPPER B",
        MIDDLE_A_SHOT: "MIDDLE A",
        MIDDLE_B_SHOT: "MIDDLE B",
        LEFT_WEB_SHOT: "LEFT WEB",
        CENTER_WEB_SHOT: "CENTER WEB",
        SAUCERS_SHOT: "ANY SAUCER",
        STAR_SHOT: "STAR",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.machine.game.player["active_mode_stat_2"] = self.machine.game.player["swamp_bonus"]

        self.mode_done = False
        self.super_lit = False
        self.super_collected = False
        self.shot_assist_used = False
        self.pop_hits = 0
        self.mode_points = 0
        self.jackpots_collected = 0
        self.revealed_shots = set()
        self.lit_shots = set()
        self.collected_shots = set()

        self.case_files = self.get_case_file_bonuses()
        self.more_jackpots_active = self.has_case_file("more_jackpots")
        self.bigger_jackpots_active = self.has_case_file("bigger_jackpots")
        self.more_time_active = self.has_case_file("more_time")
        self.safety_net_active = self.has_case_file("safety_net")
        self.shot_assist_active = self.has_case_file("shot_assist")

        self.required_shots = list(self.BASE_SHOTS)
        if self.more_jackpots_active:
            self.required_shots.append(self.STAR_SHOT)
        self.required_jackpots = len(self.required_shots)
        self.jackpot_value = (
            self.BIGGER_JACKPOT_VALUE
            if self.bigger_jackpots_active
            else self.JACKPOT_VALUE
        )

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "STAR JACKPOT ADDED"),
            ("bigger_jackpots", "RAMPAGE JACKPOTS 150K"),
            ("more_time", "OPENING SAVE EXTENDED TO 20s"),
            ("safety_net", "10s OPENING BALL SAVE"),
            ("shot_assist", "FIRST POP COUNTS TWICE"),
        ])

        self.add_mode_event_handler("conners_reptiles_pop_hit", self._pop_hit)
        for shot in self.required_shots:
            if shot != self.SAUCERS_SHOT:
                self.add_mode_event_handler(
                    f"conners_reptiles_{shot}_hit",
                    self._shot_hit,
                    shot=shot,
                )
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(
                f"conners_reptiles_saucer_{saucer}_hit",
                self._shot_hit,
                shot=self.SAUCERS_SHOT,
            )
        self.add_mode_event_handler("conners_reptiles_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("rooftop_diverter_open", self._reject_early_gate_open)

        player = self.machine.game.player
        player["conners_reptiles_state"] = 1

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("conners_reptiles_clear_all_lights")
        self.machine.events.post("conners_reptiles_pop_pulse_start")
        self.machine.events.post("clear_saucers_delayed")

        if self.safety_net_active:
            event = (
                "conners_reptiles_enable_20s_ball_save"
                if self.more_time_active
                else "conners_reptiles_enable_10s_ball_save"
            )
            self.machine.events.post(event)

        self._show_message(
            "SWAMP RAMPAGE",
            "HIT POPS TO REVEAL JACKPOTS",
            reminder=True,
        )
        self._sync_vars()

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("conners_reptiles_clear_all_lights")
        self.machine.events.post("final_vuk_chase_stop")
        self.machine.events.post("clear_saucers_delayed")
        if not self.super_collected:
            self.machine.events.post("request_vuk_eject")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _pop_hit(self, **kwargs):
        if self._in_summary_or_done():
            return

        effective_hits = 1
        if self.shot_assist_active and not self.shot_assist_used:
            effective_hits = 2
            self.shot_assist_used = True

        points = self.POP_VALUE * effective_hits
        bonus_added = self.SWAMP_BONUS_PER_POP * effective_hits
        self.pop_hits += effective_hits
        self._score(points)

        player = self.machine.game.player
        player["swamp_bonus"] += bonus_added
        self.machine.events.post(
            "conners_reptiles_swamp_bonus_added",
            value=bonus_added,
            total=player["swamp_bonus"],
            pop_hits=effective_hits,
        )

        revealed = []
        if not self.super_lit:
            for _ in range(effective_hits):
                shot = self._reveal_random_shot()
                if shot is not None:
                    revealed.append(shot)

        if revealed:
            title = "SHOT ASSIST - 2 JACKPOTS LIT" if len(revealed) == 2 else "JACKPOT LIT"
            subtitle = " / ".join(self.SHOT_NAMES[shot] for shot in revealed)
            self._show_message(title, subtitle, value=points)
        else:
            self._show_message(
                "SWAMP BONUS",
                f"TOTAL {player['swamp_bonus']:,}",
                value=bonus_added,
            )

        self.machine.events.post(
            "conners_reptiles_pop_scored",
            pop_hits=effective_hits,
            total_pop_hits=self.pop_hits,
            value=points,
            swamp_bonus=player["swamp_bonus"],
        )
        self._sync_vars()

    def _reveal_random_shot(self):
        available = [shot for shot in self.required_shots if shot not in self.revealed_shots]
        if not available:
            return None

        shot = random.choice(available)
        self.revealed_shots.add(shot)
        self.lit_shots.add(shot)
        self.machine.events.post(f"conners_reptiles_{shot}_lit")
        self.machine.events.post(
            "conners_reptiles_rampage_shot_lit",
            shot=shot,
            revealed=len(self.revealed_shots),
            required=self.required_jackpots,
        )
        return shot

    def _shot_hit(self, shot=None, **kwargs):
        if self._in_summary_or_done() or self.super_lit:
            return
        if shot not in self.lit_shots or shot in self.collected_shots:
            return

        self.lit_shots.discard(shot)
        self.collected_shots.add(shot)
        self.jackpots_collected += 1
        self._score(self.jackpot_value)

        self.machine.events.post(f"conners_reptiles_{shot}_collected")
        self.machine.events.post(
            "conners_reptiles_rampage_jackpot_collected",
            shot=shot,
            value=self.jackpot_value,
            collected=self.jackpots_collected,
            required=self.required_jackpots,
        )
        self._show_jackpot("RAMPAGE JACKPOT", self.jackpot_value, self.SHOT_NAMES[shot])

        if self.jackpots_collected >= self.required_jackpots:
            self._qualify_super()
        self._sync_vars()

    def _qualify_super(self):
        if self.mode_done or self.super_lit:
            return
        self.super_lit = True
        self.machine.events.post("conners_reptiles_clear_jackpot_lights")
        self.machine.events.post("conners_reptiles_super_jackpot_lit")
        self.machine.events.post("final_vuk_chase_start")
        self.machine.events.post("rooftop_diverter_open")
        self._show_message(
            "SWAMP SUPER READY",
            "SHOOT THE VUK",
            value=self.SUPER_VALUE,
            reminder=True,
        )

    def _vuk_hit(self, **kwargs):
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        if self._in_summary_or_done():
            return
        if not self.super_lit:
            self.machine.events.post("request_vuk_eject")
            return

        self.super_lit = False
        self.machine.events.post("final_vuk_chase_stop")
        self.super_collected = True
        self._score(self.SUPER_VALUE)
        self.machine.events.post("conners_reptiles_super_jackpot_collected", value=self.SUPER_VALUE)
        self._show_jackpot("SWAMP RAMPAGE SUPER", self.SUPER_VALUE)
        self.machine.events.post("villain_summary_hold_vuk_until_done")
        self._complete_mode()

    def _complete_mode(self):
        if self.mode_done:
            return
        self.machine.events.post("final_vuk_chase_stop")
        self.mode_done = True
        self.machine.game.player["conners_reptiles_state"] = 2
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("conners_reptiles_mode_complete")

    def _reject_early_gate_open(self, **kwargs):
        if self.mode_done or self.super_lit:
            return
        self.machine.events.post("rooftop_diverter_close")

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["conners_reptiles_pop_hits"] = self.pop_hits
        player["conners_reptiles_rampage_level"] = len(self.revealed_shots)
        player["conners_reptiles_current_jackpot"] = self.jackpot_value
        player["conners_reptiles_super_jackpot"] = self.SUPER_VALUE
        player["active_mode_stat_1"] = self.jackpots_collected
        player["active_mode_stat_2"] = player["swamp_bonus"]
        player["conners_reptiles_jackpots_required"] = self.required_jackpots
        player["conners_reptiles_pop_score_value"] = self.POP_VALUE
        player["conners_reptiles_super_lit"] = 1 if self.super_lit else 0
        player["conners_reptiles_super_timer_seconds"] = 0
        self._update_mode_status()

    def _update_mode_status(self):
        player = self.machine.game.player
        if self.super_lit:
            title = "SWAMP SUPER 500,000"
            value = "SHOOT THE VUK"
        else:
            title = f"JACKPOTS {self.jackpots_collected}/{self.required_jackpots}"
            value = f"LIT {len(self.lit_shots)}  SWAMP {player['swamp_bonus']:,}"
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)

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

    def _in_summary_or_done(self):
        if self.mode_done:
            return True
        return bool(self.machine.game.player["villain_mode_in_summary"])
