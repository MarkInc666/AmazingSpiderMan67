from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class HumanFlies(CaseFileMixin, Mode):
    """HUMAN FLIES - STAN AND LEE PATTERSON

    2-ball rooftop chase multiball.
    - Get upstairs and hit upper targets to light saucers.
    - Upper spinner builds the base jackpot.
    - Any lit saucer collects the current round jackpot.
    - Capture Brother 1, capture Brother 2, then collect a Super Jackpot.
    - After the Super, the brothers escape and the cycle repeats until MB ends.
    - Multiball ending ends/resolves the mode.
    """

    MODE_KEY = "human_flies"
    DISPLAY_NAME = "Human Flies"

    BASE_JACKPOT = 200_000
    SPINNER_BUILD = 25_000
    BIGGER_BASE_JACKPOT = 300_000
    BIGGER_SPINNER_BUILD = 50_000
    UPPER_TARGET_SCORE = 25_000
    UNLIT_SAUCER_SCORE = 25_000

    BROTHER_1 = 1
    BROTHER_2 = 2
    SUPER_ROUND = 3

    UPPER_TARGETS = {
        "left": "saucer_1",
        "center": "saucer_2",
        "right": "saucer_3",
    }
    SAUCERS = ("saucer_1", "saucer_2", "saucer_3")

    SAUCER_EJECT_EVENTS = {
        "saucer_1": "delayed_kickout_saucer_1",
        "saucer_2": "delayed_kickout_saucer_2",
        "saucer_3": "delayed_kickout_saucer_3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.mode_points = 0
        self.round_number = self.BROTHER_1
        self.rounds_completed = 0
        self.captures = 0
        self.super_jackpots = 0
        self.jackpots_collected = 0
        self.spinner_hits = 0
        self.last_award = 0
        self.shot_assist_used = False
        self.upper_targets_hit = set()
        self.lit_saucers = set()

        self.base_jackpot = self.BIGGER_BASE_JACKPOT if self.has_case_file("bigger_jackpots") else self.BASE_JACKPOT
        self.spinner_build = self.BIGGER_SPINNER_BUILD if self.has_case_file("bigger_jackpots") else self.SPINNER_BUILD

        self._reset_player_vars()
        self._add_handlers()
        self._publish_case_file_status()

        if self.has_case_file("safety_net"):
            # Existing base-mode outlane save/add-a-ball logic consumes this once on either outlane.
            self.machine.events.post("increase_outlane_add_a_ball")
            self.machine.events.post("human_flies_safety_net_lit")

        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("human_flies_clear_all_lights")
        self.machine.events.post("human_flies_round_started", round=self.round_number)
        self.machine.events.post("human_flies_start_more_time_multiball" if self.has_case_file("more_time") else "human_flies_start_multiball")
        self._sync_vars()
        self._show_mode_message("HUMAN FLIES", "GET TO THE ROOF")

    def mode_stop(self, **kwargs):
        self.clear_active_case_file_helpers()
        self.machine.events.post("human_flies_clear_all_lights")
        self.machine.events.post("clear_saucers_delayed")
        super().mode_stop(**kwargs)

    def _publish_case_file_status(self):
        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "+1X SAUCER MULTIPLIER"),
            ("bigger_jackpots", "300K BASE / +50K PER SPIN"),
            ("more_time", "LONGER MULTIBALL SAVE"),
            ("safety_net", "ONE OUTLANE SAVE"),
            ("shot_assist", "ONE UPPER HIT LIGHTS ALL"),
        ])

    def _reset_player_vars(self):
        player = self.machine.game.player
        player["human_flies_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player["human_flies_round"] = self.round_number
        player["human_flies_rounds_completed"] = 0
        player["human_flies_captures"] = 0
        player["human_flies_super_jackpots"] = 0
        player["human_flies_jackpots"] = 0
        player["human_flies_spinner_hits"] = 0
        player["human_flies_base_jackpot"] = self.base_jackpot
        player["human_flies_lit_saucers"] = 0
        player["human_flies_multiplier"] = 0
        player["human_flies_last_award"] = 0
        player["human_flies_shot_assist_used"] = 0

        player["human_flies_upper_left_hit"] = 0
        player["human_flies_upper_center_hit"] = 0
        player["human_flies_upper_right_hit"] = 0
        player["human_flies_saucer_1_lit"] = 0
        player["human_flies_saucer_2_lit"] = 0
        player["human_flies_saucer_3_lit"] = 0

    def _add_handlers(self):
        self.add_mode_event_handler("human_flies_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler("human_flies_complete_request", self._complete_mode)
        self.add_mode_event_handler("human_flies_fail_request", self._complete_mode)
        self.add_mode_event_handler("human_flies_upper_spinner_hit", self._upper_spinner_hit)
        self.add_mode_event_handler("human_flies_upper_target_left_hit", self._upper_target_hit, target="left")
        self.add_mode_event_handler("human_flies_upper_target_center_hit", self._upper_target_hit, target="center")
        self.add_mode_event_handler("human_flies_upper_target_right_hit", self._upper_target_hit, target="right")
        self.add_mode_event_handler("human_flies_saucer_1_hit", self._saucer_hit, saucer="saucer_1")
        self.add_mode_event_handler("human_flies_saucer_2_hit", self._saucer_hit, saucer="saucer_2")
        self.add_mode_event_handler("human_flies_saucer_3_hit", self._saucer_hit, saucer="saucer_3")

    def _done_or_summary(self):
        if self.mode_done:
            return True
        player = self.machine.game.player
        return player["villain_mode_in_summary"] is True

    def _current_base_jackpot(self):
        return self.base_jackpot + (self.spinner_hits * self.spinner_build)

    def _current_multiplier(self):
        if not self.lit_saucers:
            return 0
        multiplier = len(self.lit_saucers)
        if self.has_case_file("more_jackpots"):
            multiplier += 1
        return multiplier

    def _round_name(self):
        if self.round_number == self.BROTHER_1:
            return "STAN PATTERSON"
        if self.round_number == self.BROTHER_2:
            return "LEE PATTERSON"
        return "SUPER JACKPOT"

    def _upper_spinner_hit(self, **kwargs):
        if self._done_or_summary():
            return
        self.spinner_hits += 1
        self._sync_vars()
        self.machine.events.post("human_flies_jackpot_built", value=self._current_base_jackpot(), spinner_hits=self.spinner_hits)
        self._show_mode_message("JP BUILD", self._round_name(), self._current_base_jackpot())

    def _upper_target_hit(self, target, **kwargs):
        if self._done_or_summary():
            return

        self._score(self.UPPER_TARGET_SCORE)

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            for assist_target in self.UPPER_TARGETS:
                self._light_saucer_for_target(assist_target)
            self.machine.events.post("human_flies_shot_assist_used")
            self._show_mode_message("SHOT ASSIST", "ALL SAUCERS LIT")
        else:
            self._light_saucer_for_target(target)

        self._sync_vars()
        self.machine.events.post(
            "human_flies_upper_target_awarded",
            target=target,
            lit_saucers=len(self.lit_saucers),
            multiplier=self._current_multiplier(),
        )
        self._show_mode_message("SAUCER LIT", self._round_name(), f"{self._current_multiplier()}X")

    def _light_saucer_for_target(self, target):
        self.upper_targets_hit.add(target)
        saucer = self.UPPER_TARGETS[target]
        self.lit_saucers.add(saucer)
        self.machine.events.post(f"human_flies_upper_{target}_complete")
        self.machine.events.post(f"human_flies_{saucer}_lit")

    def _saucer_hit(self, saucer, **kwargs):
        if self._done_or_summary():
            self._eject_saucer(saucer)
            return

        if saucer not in self.lit_saucers:
            self._score(self.UNLIT_SAUCER_SCORE)
            self.machine.events.post("human_flies_unlit_saucer_hit", saucer=saucer)
            self._show_mode_message("SAUCER UNLIT", "GET TO THE ROOF", self.UNLIT_SAUCER_SCORE)
            self._eject_saucer(saucer)
            return

        award = self._current_base_jackpot() * self._current_multiplier()
        self.last_award = award
        self.jackpots_collected += 1

        if self.round_number == self.SUPER_ROUND:
            self.super_jackpots += 1
            self._score(award)
            self.machine.events.post("human_flies_super_jackpot_collected", value=award)
            self._show_mode_jackpot("SUPER JACKPOT", award, "THE FLIES ESCAPE")
            self._reset_cycle_to_brother_1()
        else:
            self.captures += 1
            self._score(award)
            self.machine.events.post("human_flies_brother_captured", brother=self.round_number, value=award)
            self._show_mode_jackpot("HUMAN FLY CAUGHT", award, self._round_name())
            self._advance_round_after_capture()

        self._eject_all_saucers()
        self._sync_vars()

    def _advance_round_after_capture(self):
        self.rounds_completed += 1
        if self.round_number == self.BROTHER_1:
            self.round_number = self.BROTHER_2
        elif self.round_number == self.BROTHER_2:
            self.round_number = self.SUPER_ROUND
        self._reset_round_progress()

    def _reset_cycle_to_brother_1(self):
        self.rounds_completed += 1
        self.round_number = self.BROTHER_1
        self._reset_round_progress()

    def _reset_round_progress(self):
        self.upper_targets_hit.clear()
        self.lit_saucers.clear()
        self.machine.events.post("human_flies_round_reset")
        self.machine.events.post("human_flies_round_started", round=self.round_number)
        self._sync_vars()

    def _multiball_ended(self, **kwargs):
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player["human_flies_state"] = 2
        self.machine.events.post("human_flies_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = len(self.upper_targets_hit)
        player["active_mode_major_hits"] = self.jackpots_collected
        player["human_flies_round"] = self.round_number
        player["human_flies_rounds_completed"] = self.rounds_completed
        player["human_flies_captures"] = self.captures
        player["human_flies_super_jackpots"] = self.super_jackpots
        player["human_flies_jackpots"] = self.jackpots_collected
        player["human_flies_spinner_hits"] = self.spinner_hits
        player["human_flies_base_jackpot"] = self._current_base_jackpot()
        player["human_flies_lit_saucers"] = len(self.lit_saucers)
        player["human_flies_multiplier"] = self._current_multiplier()
        player["human_flies_last_award"] = self.last_award
        player["human_flies_shot_assist_used"] = 1 if self.shot_assist_used else 0

        player["human_flies_upper_left_hit"] = 1 if "left" in self.upper_targets_hit else 0
        player["human_flies_upper_center_hit"] = 1 if "center" in self.upper_targets_hit else 0
        player["human_flies_upper_right_hit"] = 1 if "right" in self.upper_targets_hit else 0
        player["human_flies_saucer_1_lit"] = 1 if "saucer_1" in self.lit_saucers else 0
        player["human_flies_saucer_2_lit"] = 1 if "saucer_2" in self.lit_saucers else 0
        player["human_flies_saucer_3_lit"] = 1 if "saucer_3" in self.lit_saucers else 0

    def _eject_saucer(self, saucer):
        self.machine.events.post(self.SAUCER_EJECT_EVENTS[saucer])

    def _eject_all_saucers(self):
        self.machine.events.post("clear_saucers_delayed")

    def _show_mode_message(self, title, subtitle="", value=""):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _show_mode_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )
