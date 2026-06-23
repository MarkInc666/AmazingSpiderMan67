from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class DiamondSmugglers(Mode, CaseFileMixin):
    """Diamond Smugglers villain mode.

    Build the Diamond Jackpot with both drop banks. Completing the right 5-bank
    starts a cycling saucer chase. The lit saucer collects the jackpot; wrong
    saucers kick out and resume the chase. Star rollover freezes the chase and
    lights all three saucers for a short collect window.
    """

    MODE_KEY = "diamond_smugglers"
    DISPLAY_NAME = "Diamond Smugglers"

    BASE_JACKPOT = 100_000
    BIGGER_BASE_JACKPOT = 200_000

    RIGHT_DROP_ADD = 25_000
    BIGGER_RIGHT_DROP_ADD = 50_000

    LEFT_DROP_ADD = 40_000
    BIGGER_LEFT_DROP_ADD = 75_000

    WRONG_SAUCER_SCORE = 10_000
    STAR_FREEZE_MS = 10_000
    MORE_TIME_STAR_FREEZE_MS = 15_000

    SAUCER_CYCLE_MS_BY_ROUND = (750, 500, 350, 300)
    NORMAL_REQUIRED_JACKPOTS = 3
    MORE_JACKPOTS_REQUIRED_JACKPOTS = 4

    SAUCER_KICK_EVENTS = {
        1: "kickout_saucer_1",
        2: "kickout_saucer_2",
        3: "kickout_saucer_3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_done = False
        self.case_files = self.get_case_file_bonuses()

        self.base_jackpot = self.BIGGER_BASE_JACKPOT if self.has_case_file("bigger_jackpots") else self.BASE_JACKPOT
        self.right_drop_add = self.BIGGER_RIGHT_DROP_ADD if self.has_case_file("bigger_jackpots") else self.RIGHT_DROP_ADD
        self.left_drop_add = self.BIGGER_LEFT_DROP_ADD if self.has_case_file("bigger_jackpots") else self.LEFT_DROP_ADD
        self.required_jackpots = self.MORE_JACKPOTS_REQUIRED_JACKPOTS if self.has_case_file("more_jackpots") else self.NORMAL_REQUIRED_JACKPOTS
        self.star_freeze_ms = self.MORE_TIME_STAR_FREEZE_MS if self.has_case_file("more_time") else self.STAR_FREEZE_MS

        self.jackpot_value = self.base_jackpot
        self.jackpots_collected = 0
        self.drop_hits = 0
        self.mode_points = 0
        self.saucer_chase_active = False
        self.star_freeze_active = False
        self.lit_saucer = 0
        self.next_saucer = 1
        self.shot_assist_used = False

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars()
        self._add_handlers()
        self._apply_case_file_effects()

        self.machine.events.post("diamond_smugglers_started")
        self.machine.events.post("diamond_smugglers_clear_lights")
        self.machine.events.post("diamond_smugglers_build_phase_started")
        self.machine.events.post("show_mode_message_long", message_mode_title="DIAMOND SMUGGLERS", message_mode_subtitle="BUILD JACKPOT WITH DROPS")
        self.machine.events.post(
            "diamond_smugglers_jackpot_changed",
            value=self.jackpot_value,
            value_str=self._format_score(self.jackpot_value),
        )

    def mode_stop(self, **kwargs):
        self.delay.remove("diamond_smugglers_saucer_cycle")
        self.delay.remove("diamond_smugglers_star_freeze")
        self.delay.remove("diamond_smugglers_resume_chase")
        self.clear_active_case_file_helpers()
        self.machine.events.post("diamond_smugglers_clear_lights")
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("diamond_smugglers_right_drop_hit", self._drop_hit, bank="right")
        self.add_mode_event_handler("diamond_smugglers_left_drop_hit", self._drop_hit, bank="left")
        self.add_mode_event_handler("diamond_smugglers_right_bank_complete", self._right_bank_complete)
        self.add_mode_event_handler("diamond_smugglers_left_bank_complete", self._left_bank_complete)
        self.add_mode_event_handler("diamond_smugglers_saucer_1_hit", self._saucer_hit, saucer=1)
        self.add_mode_event_handler("diamond_smugglers_saucer_2_hit", self._saucer_hit, saucer=2)
        self.add_mode_event_handler("diamond_smugglers_saucer_3_hit", self._saucer_hit, saucer=3)
        self.add_mode_event_handler("diamond_smugglers_star_hit", self._star_hit)
        self.add_mode_event_handler("diamond_smugglers_complete_request", self._complete_mode)

    def _apply_case_file_effects(self):
        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "4TH DIAMOND ROUND ADDED"),
            ("bigger_jackpots", "DIAMOND VALUES INCREASED"),
            ("more_time", "STAR FREEZE 15 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST WRONG SAUCER COUNTS"),
        ])

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

    def _drop_hit(self, bank, **kwargs):
        if self.mode_done:
            return

        add_value = self.right_drop_add if bank == "right" else self.left_drop_add
        score_value = 25_000
        self.drop_hits += 1
        self.jackpot_value += add_value
        self._score(score_value)
        self._sync_vars()

        self.machine.events.post(
            "diamond_smugglers_drop_value_added",
            bank=bank,
            add_value=add_value,
            add_value_str=self._format_score(add_value),
            jackpot=self.jackpot_value,
            jackpot_str=self._format_score(self.jackpot_value),
        )
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="DIAMOND VALUE +",
            message_mode_subtitle="RIGHT BANK" if bank == "right" else "LEFT BANK",
            message_mode_value=self.jackpot_value,
        )

    def _right_bank_complete(self, **kwargs):
        if self.mode_done:
            return
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("diamond_smugglers_right_bank_completed")
        if not self.saucer_chase_active:
            self._start_saucer_chase()

    def _left_bank_complete(self, **kwargs):
        if self.mode_done:
            return
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("diamond_smugglers_left_bank_completed")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="LEFT BANK RESET",
            message_mode_subtitle="DIAMOND VALUE HOLDS",
            message_mode_value=self.jackpot_value,
        )

    def _start_saucer_chase(self):
        self.saucer_chase_active = True
        self.star_freeze_active = False
        self.lit_saucer = 0
        self.next_saucer = 1
        self.machine.events.post("diamond_smugglers_saucer_chase_started")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="SHIPMENT CHASE",
            message_mode_subtitle="SHOOT THE LIT SAUCER",
            message_mode_value=self.jackpot_value,
        )
        self._sync_vars()
        self._cycle_saucer()

    def _cycle_saucer(self, **kwargs):
        if self.mode_done or not self.saucer_chase_active or self.star_freeze_active:
            return

        self.lit_saucer = self.next_saucer
        self.next_saucer = 1 if self.next_saucer >= 3 else self.next_saucer + 1
        self.machine.events.post("diamond_smugglers_clear_saucer_lights")
        self.machine.events.post(f"diamond_smugglers_saucer_{self.lit_saucer}_lit")
        self._sync_vars()

        self.delay.add(
            name="diamond_smugglers_saucer_cycle",
            ms=self._current_cycle_ms(),
            callback=self._cycle_saucer,
        )

    def _current_cycle_ms(self):
        index = min(self.jackpots_collected, len(self.SAUCER_CYCLE_MS_BY_ROUND) - 1)
        return self.SAUCER_CYCLE_MS_BY_ROUND[index]

    def _saucer_hit(self, saucer, **kwargs):
        if self.mode_done:
            self._kick_saucer(saucer)
            return

        if not self.saucer_chase_active:
            self.machine.events.post("show_mode_message", message_mode_title="NO SHIPMENT", message_mode_subtitle="COMPLETE 5-BANK")
            self._kick_saucer(saucer)
            return

        self.delay.remove("diamond_smugglers_saucer_cycle")

        correct = self.star_freeze_active or saucer == self.lit_saucer
        if not correct and self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            correct = True
            self.machine.events.post("diamond_smugglers_shot_assist_used")

        if correct:
            self._collect_jackpot(saucer)
        else:
            self._wrong_saucer(saucer)

    def _wrong_saucer(self, saucer):
        self._score(self.WRONG_SAUCER_SCORE)
        self.machine.events.post("diamond_smugglers_wrong_saucer", saucer=saucer)
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="DECOY SHIPMENT",
            message_mode_subtitle=f"SAUCER {saucer}",
            message_mode_value=self.WRONG_SAUCER_SCORE,
        )
        self._kick_saucer(saucer)
        self.delay.add(
            name="diamond_smugglers_resume_chase",
            ms=1_000,
            callback=self._resume_saucer_chase,
        )

    def _collect_jackpot(self, saucer):
        if self.mode_done or not self.saucer_chase_active:
            return

        self.saucer_chase_active = False
        self.star_freeze_active = False
        self.delay.remove("diamond_smugglers_star_freeze")
        self.machine.events.post("diamond_smugglers_clear_saucer_lights")

        award = self.jackpot_value
        self._score(award)
        self.jackpots_collected += 1
        self.machine.events.post(
            "diamond_smugglers_jackpot_collected",
            saucer=saucer,
            jackpot=award,
            jackpot_str=self._format_score(award),
            jackpots_collected=self.jackpots_collected,
            required_jackpots=self.required_jackpots,
        )
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="DIAMOND JACKPOT",
            message_mode_subtitle=f"{self.jackpots_collected}/{self.required_jackpots} SHIPMENTS",
            message_mode_value=award,
        )
        self._kick_saucer(saucer)
        self._sync_vars()

        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

        if self.jackpots_collected >= self.required_jackpots:
            self.mode_done = True
            self.delay.add(name="diamond_smugglers_complete_delay", ms=1_000, callback=self._complete_mode)
        else:
            self.machine.events.post("diamond_smugglers_build_phase_started")

    def _star_hit(self, **kwargs):
        if self.mode_done or not self.saucer_chase_active:
            return

        self.delay.remove("diamond_smugglers_saucer_cycle")
        self.delay.remove("diamond_smugglers_star_freeze")
        self.star_freeze_active = True
        self.lit_saucer = 0
        self.machine.events.post("diamond_smugglers_all_saucers_lit")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="OPEN SHIPMENT",
            message_mode_subtitle=f"ALL SAUCERS {int(self.star_freeze_ms / 1000)} SECONDS",
            message_mode_value=self.jackpot_value,
        )
        self._sync_vars()
        self.delay.add(
            name="diamond_smugglers_star_freeze",
            ms=self.star_freeze_ms,
            callback=self._resume_saucer_chase,
        )

    def _resume_saucer_chase(self, **kwargs):
        if self.mode_done or not self.saucer_chase_active:
            return
        self.star_freeze_active = False
        self.machine.events.post("diamond_smugglers_clear_saucer_lights")
        self._sync_vars()
        self._cycle_saucer()

    def _complete_mode(self, **kwargs):
        if not self.mode_done:
            self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("diamond_smugglers_clear_lights")
        self.machine.events.post("diamond_smugglers_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _kick_saucer(self, saucer):
        self.machine.events.post(self.SAUCER_KICK_EVENTS[saucer])

    def _sync_vars(self):
        player = self.machine.game.player
        # Use shared active-mode counters. Do not recreate per-mode
        # *_mode_points / *_hits / *_major_hits player vars.
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.drop_hits
        player["active_mode_major_hits"] = self.jackpots_collected

    def _format_score(self, value):
        return f"{int(value):,}"
