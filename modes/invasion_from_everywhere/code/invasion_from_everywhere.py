import random

from mpf.core.mode import Mode


class InvasionFromEverywhere(Mode):
    """Chapter 9 wizard: repeating VUK / saucer relay multiball.

    Loop:
      LOAD VUK -> Igor -> Atlantean -> LOAD VUK -> Molemen -> Atlantean
      -> LOAD VUK -> DeVargas -> Atlantean -> repeat.

    The mode starts 3-ball multiball, caps at four balls, and ends as soon as
    the multiball collapses to one ball. Saucers may park balls for 20 seconds,
    while the VUK intentionally holds its ball for the entire lower-playfield
    phase until that phase's lock condition launches it to the rooftop.
    """

    MODE_KEY = "invasion_from_everywhere"
    DISPLAY_NAME = "INVASION FROM EVERYWHERE"

    START_BALLS = 3
    MAX_BALLS = 4
    SAUCER_HOLD_MS = 20_000

    IGOR_GOOD_SCORE = 500_000
    IGOR_BAD_SCORE = 50_000
    IGOR_STREAK_GOAL = 3

    MOLEMEN_FIRST_LOCK_SCORE = 250_000
    MOLEMEN_FIRST_LOCK_CAP_SCORE = 500_000
    MOLEMEN_SECOND_LOCK_SCORE = 250_000

    DEVARGAS_CORRECT_SCORE = 250_000
    DEVARGAS_WRONG_SCORE = 50_000

    ATLANTEAN_TARGET_SCORE = 250_000
    ATLANTEAN_BASE_JACKPOT = 1_000_000
    ATLANTEAN_SPINNER_STEP = 50_000

    PHASE_ORDER = ("igor", "molemen", "devargas")

    IGOR_SHOT_SETS = {
        1: {"good": "right_bank", "bad": ("left_pop", "right_pop")},
        2: {"good": "right_pop", "bad": ("left_pop", "right_bank")},
        3: {"good": "left_bank", "bad": ("spinner", "right_pop")},
        4: {"good": "spinner", "bad": ("left_web", "left_bank")},
        5: {"good": "left_bank", "bad": ("left_web", "spinner", "left_pop", "right_pop")},
        6: {"good": "right_pop", "bad": ("left_bank", "right_bank")},
        7: {"good": "right_pop", "bad": ("center_web", "right_bank")},
    }

    MOLEMEN_AREAS = {
        "left": {"saucer": 1, "display": "LEFT POP"},
        "center": {"saucer": 2, "display": "CENTER WEB"},
        "right": {"saucer": 3, "display": "RIGHT POP"},
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.mode_points = 0
        self.phase_index = 0
        self.phase = "load_vuk"
        self.vuk_held = False
        self.held_saucers = []
        self.saucer_qualified = set()

        self.igor_current_set = None
        self.igor_streak = 0
        self.igor_complete = False

        self.molemen_locks = 0
        self.molemen_area_lit = {area: False for area in self.MOLEMEN_AREAS}

        self.devargas_step = "stage"

        self.atlantean_visit = 0
        self.atlantean_hits = 0
        self.atlantean_goal = 1
        self.atlantean_jackpot = 0

        player = self.machine.game.player
        self.case_file_bonus = int(player["mini_wizard_case_file_bonus"] or 0)
        player["mini_wizard_current_key"] = self.MODE_KEY
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player["invasion_from_everywhere_vuk_hold_active"] = 0

        self._register_handlers()
        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("invasion_from_everywhere_clear_all")
        self.machine.events.post("invasion_from_everywhere_start_multiball")

        if self._vuk_is_occupied():
            self._claim_vuk_and_start_phase()
        else:
            player["mini_wizard_vuk_hold_active"] = 0
            self._start_load_vuk()

        self._sync_vars()

    def mode_stop(self, **kwargs):
        self.delay.clear()
        self._set_vuk_hold(False)
        self._release_all_saucers()
        self.machine.events.post("invasion_from_everywhere_clear_all")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        player = self.machine.game.player if self.machine.game else None
        if player:
            player["mini_wizard_vuk_hold_active"] = 0
            player["invasion_from_everywhere_vuk_hold_active"] = 0
            if player["mini_wizard_current_key"] == self.MODE_KEY:
                player["mini_wizard_current_key"] = ""
        super().mode_stop(**kwargs)

    def _register_handlers(self):
        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(f"s_saucer_{saucer}_active", self._saucer_hit, saucer=saucer)

        # Igor shot groups.
        for target in range(1, 6):
            self.add_mode_event_handler(f"s_right_drops_{target}_active", self._igor_group_hit, group="right_bank")
        for target in range(1, 4):
            self.add_mode_event_handler(f"s_left_drops_{target}_active", self._igor_group_hit, group="left_bank")
        self.add_mode_event_handler("s_pop_left_active", self._igor_group_hit, group="left_pop")
        self.add_mode_event_handler("s_pop_right_active", self._igor_group_hit, group="right_pop")
        self.add_mode_event_handler("s_web_target_mid_active", self._igor_group_hit, group="center_web")
        self.add_mode_event_handler("s_web_target_left_active", self._igor_group_hit, group="left_web")
        self.add_mode_event_handler("s_web_spinner_active", self._igor_group_hit, group="spinner")

        # Molemen areas.
        self.add_mode_event_handler("s_pop_left_active", self._molemen_area_hit, area="left")
        self.add_mode_event_handler("s_web_target_mid_active", self._molemen_area_hit, area="center")
        self.add_mode_event_handler("s_pop_right_active", self._molemen_area_hit, area="right")

        # DeVargas sequence.
        for target in range(1, 6):
            self.add_mode_event_handler(f"s_right_drops_{target}_active", self._devargas_bank_hit, target=target)
        self.add_mode_event_handler("s_web_spinner_active", self._devargas_spinner_hit)

        # Atlantean rooftop.
        self.add_mode_event_handler("s_upper_target_left_active", self._atlantean_target_hit)
        self.add_mode_event_handler("s_upper_target_center_active", self._atlantean_target_hit)
        self.add_mode_event_handler("s_upper_target_right_active", self._atlantean_target_hit)
        self.add_mode_event_handler("s_trispinner_opto_active", self._atlantean_spinner_hit)

        self.add_mode_event_handler(
            "multiball_invasion_from_everywhere_multiball_ended",
            self._multiball_ended,
        )
        self.add_mode_event_handler("invasion_from_everywhere_complete_request", self._complete_mode)

    # ------------------------------------------------------------------
    # VUK / phase routing
    # ------------------------------------------------------------------
    def _start_load_vuk(self):
        if self.mode_done:
            return
        self.phase = "load_vuk"
        self.vuk_held = False
        self._set_vuk_hold(False)
        self.machine.events.post("invasion_from_everywhere_clear_phase_lights")
        self.machine.events.post("invasion_from_everywhere_load_vuk")
        self.machine.events.post("rooftop_diverter_open")
        self._show_message("LOAD THE DAILY BUGLE", "SHOOT THE VUK", reminder=True)
        self._update_status()

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            self.machine.events.post("request_vuk_eject", delay_ms=0)
            return
        if self.phase == "load_vuk":
            self._claim_vuk_and_start_phase()
            return
        if self.vuk_held:
            self.machine.events.post("cancel_vuk_eject_request")
            return
        # During rooftop play a VUK entry is not a phase lock; send it upstairs.
        self.machine.events.post("request_vuk_eject", delay_ms=500)

    def _claim_vuk_and_start_phase(self):
        if self.mode_done:
            return
        self.vuk_held = True
        self._set_vuk_hold(True)
        self.machine.events.post("cancel_vuk_eject_request")
        self.machine.events.post("rooftop_diverter_close")
        lower_phase = self.PHASE_ORDER[self.phase_index]
        if lower_phase == "igor":
            self._start_igor()
        elif lower_phase == "molemen":
            self._start_molemen()
        else:
            self._start_devargas()

    def _launch_vuk_to_rooftop(self):
        if not self.vuk_held:
            return
        self.vuk_held = False
        self._set_vuk_hold(False)
        self.machine.game.player["mini_wizard_vuk_hold_active"] = 0
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("request_vuk_eject", delay_ms=500)
        self._start_atlantean()

    def _set_vuk_hold(self, active):
        if not self.machine.game:
            return
        player = self.machine.game.player
        player["invasion_from_everywhere_vuk_hold_active"] = 1 if active else 0
        if active:
            player["mini_wizard_vuk_hold_active"] = 1
        self.machine.events.post("cancel_vuk_eject_request")

    def _vuk_is_occupied(self):
        switch = self.machine.switches.get("s_vuk_switch")
        return bool(switch and self.machine.switch_controller.is_active(switch))

    # ------------------------------------------------------------------
    # Igor
    # ------------------------------------------------------------------
    def _start_igor(self):
        self.phase = "igor"
        self.igor_streak = 0
        self.igor_complete = False
        self.saucer_qualified.clear()
        self.machine.events.post("invasion_from_everywhere_phase_igor")
        self._select_igor_set()
        self._show_message("IGOR", "3 GOOD SHOTS IN A ROW", reminder=True)
        self._update_status()

    def _select_igor_set(self):
        choices = [n for n in self.IGOR_SHOT_SETS if n != self.igor_current_set]
        self.igor_current_set = random.choice(choices)
        shot_set = self.IGOR_SHOT_SETS[self.igor_current_set]
        self.machine.events.post("invasion_igor_all_off")
        self.machine.events.post(f"invasion_igor_good_{shot_set['good']}")
        for group in shot_set["bad"]:
            self.machine.events.post(f"invasion_igor_bad_{group}")
        self._update_status()

    def _igor_group_hit(self, group=None, **kwargs):
        if self.mode_done or self.phase != "igor" or self.igor_complete:
            return
        shot_set = self.IGOR_SHOT_SETS[self.igor_current_set]
        if group == shot_set["good"]:
            self.igor_streak += 1
            self._score(self.IGOR_GOOD_SCORE)
            self.machine.events.post("play_mode_jackpot")
            self._show_message("CORRECT SHOT", f"{self.igor_streak} / {self.IGOR_STREAK_GOAL}", self.IGOR_GOOD_SCORE)
            if self.igor_streak >= self.IGOR_STREAK_GOAL:
                self.igor_complete = True
                self.saucer_qualified = {1, 2, 3}
                self.machine.events.post("invasion_igor_all_off")
                self.machine.events.post("invasion_saucers_ready")
                self._show_message("IGOR DEFEATED", "LOCK A BALL IN ANY SAUCER", reminder=True)
                self._update_status()
                return
        elif group in shot_set["bad"]:
            self.igor_streak = 0
            self._score(self.IGOR_BAD_SCORE)
            self.machine.events.post("invasion_igor_bad_scored")
            self._show_message("WRONG SHOT", "STREAK RESET", self.IGOR_BAD_SCORE)
        else:
            return
        self._select_igor_set()

    # ------------------------------------------------------------------
    # Molemen
    # ------------------------------------------------------------------
    def _start_molemen(self):
        self.phase = "molemen"
        self.molemen_locks = 0
        self.saucer_qualified.clear()
        self.molemen_area_lit = {area: False for area in self.MOLEMEN_AREAS}
        self.machine.events.post("invasion_from_everywhere_phase_molemen")
        self.machine.events.post("invasion_molemen_areas_on")
        self._show_message("THE MOLEMEN", "BUILD AREAS - FILL 2 SAUCERS", reminder=True)
        self._update_status()

    def _molemen_area_hit(self, area=None, **kwargs):
        if self.mode_done or self.phase != "molemen" or area not in self.MOLEMEN_AREAS:
            return
        saucer = self.MOLEMEN_AREAS[area]["saucer"]
        if saucer in self.held_saucers:
            return
        self.molemen_area_lit[area] = True
        self.saucer_qualified.add(saucer)
        self.machine.events.post(f"invasion_molemen_saucer_{saucer}_ready")
        self._show_message(self.MOLEMEN_AREAS[area]["display"], f"SAUCER {saucer} LIT")
        self._update_status()

    # ------------------------------------------------------------------
    # DeVargas
    # ------------------------------------------------------------------
    def _start_devargas(self):
        self.phase = "devargas"
        self.saucer_qualified.clear()
        self.machine.events.post("invasion_from_everywhere_phase_devargas")
        self._restage_devargas_bank()
        self._show_message("DEVARGAS", "5 - THEN 1", reminder=True)
        self._update_status()

    def _restage_devargas_bank(self):
        self.devargas_step = "stage"
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("invasion_devargas_all_off")
        self.delay.reset(name="invasion_devargas_stage", ms=350, callback=self._finish_devargas_staging)

    def _finish_devargas_staging(self):
        if self.mode_done or self.phase != "devargas":
            return
        for target in (2, 3, 4):
            device = self.machine.drop_targets.get(f"dt_right_{target}")
            if device:
                device.knockdown()
        self.devargas_step = "5"
        self.machine.events.post("invasion_devargas_target_5")
        self._update_status()

    def _devargas_bank_hit(self, target=None, **kwargs):
        if self.mode_done or self.phase != "devargas" or self.devargas_step == "stage":
            return
        if self.devargas_step == "5":
            if target == 5:
                self._score(self.DEVARGAS_CORRECT_SCORE)
                self.devargas_step = "1"
                self.machine.events.post("invasion_devargas_target_1")
                self._show_message("CORRECT", "NOW HIT 1", self.DEVARGAS_CORRECT_SCORE)
            else:
                self._devargas_wrong_and_reset()
        elif self.devargas_step == "1":
            if target == 1:
                self._score(self.DEVARGAS_CORRECT_SCORE)
                self.devargas_step = "any_bank"
                self.machine.events.post("drop_target_bank_dt_bank_right_reset")
                self.machine.events.post("invasion_devargas_any_bank")
                self._show_message("CORRECT", "HIT ANY RIGHT BANK", self.DEVARGAS_CORRECT_SCORE)
            else:
                self._devargas_wrong_and_reset()
        elif self.devargas_step == "any_bank":
            self._score(self.DEVARGAS_CORRECT_SCORE)
            self.devargas_step = "spinner"
            self.machine.events.post("invasion_devargas_spinner")
            self._show_message("BANK COMPLETE", "SHOOT SPINNER", self.DEVARGAS_CORRECT_SCORE)
        self._update_status()

    def _devargas_wrong_and_reset(self):
        self._score(self.DEVARGAS_WRONG_SCORE)
        self._show_message("WRONG TARGET", "START AGAIN AT 5", self.DEVARGAS_WRONG_SCORE)
        self._restage_devargas_bank()

    def _devargas_spinner_hit(self, **kwargs):
        if self.mode_done or self.phase != "devargas" or self.devargas_step != "spinner":
            return
        self._score(self.DEVARGAS_CORRECT_SCORE)
        self.devargas_step = "saucer"
        self.saucer_qualified = {1, 2, 3}
        self.machine.events.post("invasion_devargas_saucers")
        self._show_message("SPINNER COMPLETE", "LOCK A BALL IN A SAUCER", self.DEVARGAS_CORRECT_SCORE, reminder=True)
        self._update_status()

    # ------------------------------------------------------------------
    # Saucers / parking
    # ------------------------------------------------------------------
    def _saucer_hit(self, saucer=None, **kwargs):
        if saucer not in (1, 2, 3):
            return
        if self.mode_done:
            self._eject_saucer(saucer)
            return
        if saucer in self.held_saucers:
            return

        qualifies = saucer in self.saucer_qualified
        phase_completed = False

        if self.phase == "igor" and self.igor_complete and qualifies:
            self._park_saucer(saucer)
            self.saucer_qualified.clear()
            self.machine.events.post("invasion_saucers_off")
            phase_completed = True
        elif self.phase == "molemen" and qualifies:
            self._park_saucer(saucer)
            self.saucer_qualified.discard(saucer)
            self.molemen_locks += 1
            if self.molemen_locks == 1:
                if self._balls_in_play() < self.MAX_BALLS:
                    self._score(self.MOLEMEN_FIRST_LOCK_SCORE)
                    self.machine.events.post("invasion_from_everywhere_add_a_ball")
                    self._show_message("MOLEMEN LOCK 1", "ADD-A-BALL", self.MOLEMEN_FIRST_LOCK_SCORE)
                else:
                    self._score(self.MOLEMEN_FIRST_LOCK_CAP_SCORE)
                    self._show_message("MOLEMEN LOCK 1", "4 BALL MAX", self.MOLEMEN_FIRST_LOCK_CAP_SCORE)
            else:
                self._score(self.MOLEMEN_SECOND_LOCK_SCORE)
                self._show_message("MOLEMEN LOCK 2", "ATTACK THE ROOFTOP", self.MOLEMEN_SECOND_LOCK_SCORE)
                phase_completed = True
        elif self.phase == "devargas" and self.devargas_step == "saucer" and qualifies:
            self._score(self.DEVARGAS_CORRECT_SCORE)
            self._park_saucer(saucer)
            self.saucer_qualified.clear()
            self.machine.events.post("invasion_saucers_off")
            self._show_message("DEVARGAS COMPLETE", "ATTACK THE ROOFTOP", self.DEVARGAS_CORRECT_SCORE)
            phase_completed = True
        else:
            self._park_saucer(saucer)

        if phase_completed:
            self._launch_vuk_to_rooftop()
        else:
            self._ensure_free_ball()
        self._update_status()

    def _park_saucer(self, saucer):
        if saucer not in self.held_saucers:
            self.held_saucers.append(saucer)
        self.delay.remove(f"invasion_saucer_{saucer}")
        self.delay.add(
            name=f"invasion_saucer_{saucer}",
            ms=self.SAUCER_HOLD_MS,
            callback=self._release_saucer,
            saucer=saucer,
        )
        self.machine.events.post(f"invasion_saucer_{saucer}_parked")

    def _release_saucer(self, saucer=None):
        if saucer not in self.held_saucers:
            return
        self.held_saucers.remove(saucer)
        self.delay.remove(f"invasion_saucer_{saucer}")
        self.machine.events.post(f"invasion_saucer_{saucer}_released")
        self._eject_saucer(saucer)

    def _release_all_saucers(self):
        for saucer in list(self.held_saucers):
            self._release_saucer(saucer)

    def _ensure_free_ball(self):
        held = len(self.held_saucers) + (1 if self.vuk_held else 0)
        if self._balls_in_play() - held >= 1:
            return
        if self.held_saucers:
            self._release_saucer(self.held_saucers[0])

    def _eject_saucer(self, saucer):
        self.machine.events.post("request_saucer_eject", saucer_number=saucer, delay_ms=0)

    # ------------------------------------------------------------------
    # Atlantean rooftop payoff
    # ------------------------------------------------------------------
    def _start_atlantean(self):
        self.phase = "atlantean"
        self.atlantean_visit += 1
        self.atlantean_hits = 0
        self.atlantean_goal = min(3, self.atlantean_visit)
        self.atlantean_jackpot = self.ATLANTEAN_BASE_JACKPOT + self.case_file_bonus
        self.machine.events.post("invasion_from_everywhere_phase_atlantean")
        self.machine.events.post("invasion_atlantean_rooftop_on")
        self._show_message(
            "DOCTOR ATLANTEAN",
            f"{self.atlantean_goal} UPPER TARGET{'S' if self.atlantean_goal != 1 else ''}",
            self.atlantean_jackpot,
            reminder=True,
        )
        self._update_status()

    def _atlantean_spinner_hit(self, **kwargs):
        if self.mode_done or self.phase != "atlantean":
            return
        self.atlantean_jackpot += self.ATLANTEAN_SPINNER_STEP
        self.machine.events.post("invasion_atlantean_spinner_build", value=self.atlantean_jackpot)
        self._update_status()

    def _atlantean_target_hit(self, **kwargs):
        if self.mode_done or self.phase != "atlantean":
            return
        self.atlantean_hits += 1
        self._score(self.ATLANTEAN_TARGET_SCORE)
        if self.atlantean_hits < self.atlantean_goal:
            self._show_message(
                "UPPER TARGET",
                f"{self.atlantean_hits} / {self.atlantean_goal}",
                self.ATLANTEAN_TARGET_SCORE,
            )
            self._update_status()
            return

        jackpot = self.atlantean_jackpot
        self._score(jackpot)
        self.machine.game.player["active_mode_major_hits"] += 1
        self.machine.events.post("show_mode_jackpot", message_mode_title="ATLANTEAN JACKPOT", message_mode_subtitle="INVASION REPELLED", message_mode_value=jackpot)
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post("invasion_atlantean_rooftop_off")
        self.phase_index = (self.phase_index + 1) % len(self.PHASE_ORDER)
        self._start_load_vuk()

    # ------------------------------------------------------------------
    # End / status / scoring
    # ------------------------------------------------------------------
    def _multiball_ended(self, **kwargs):
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._set_vuk_hold(False)
        if self._vuk_is_occupied():
            self.machine.events.post("request_vuk_eject", delay_ms=0)
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return int(self.machine.game.balls_in_play or 0)

    def _score(self, points):
        if points <= 0:
            return
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points

    def _show_message(self, title, subtitle="", value=None, reminder=False):
        kwargs = {
            "message_mode_title": title,
            "message_mode_subtitle": subtitle,
            "reminder": reminder,
        }
        if value is not None:
            kwargs["message_mode_value"] = value
        self.machine.events.post("show_mode_message", **kwargs)
        if reminder:
            self.machine.events.post("reset_mode_message_reminder")

    def _update_status(self):
        if self.mode_done:
            return
        if self.phase == "load_vuk":
            title, value = "LOAD VUK", "SHOOT DAILY BUGLE"
        elif self.phase == "igor":
            if self.igor_complete:
                title, value = "IGOR", "LOCK ANY SAUCER"
            else:
                title, value = "IGOR STREAK", f"{self.igor_streak} / {self.IGOR_STREAK_GOAL}"
        elif self.phase == "molemen":
            title, value = "MOLEMEN LOCKS", f"{self.molemen_locks} / 2"
        elif self.phase == "devargas":
            labels = {"stage": "STAGING", "5": "HIT 5", "1": "HIT 1", "any_bank": "ANY RIGHT BANK", "spinner": "SHOOT SPINNER", "saucer": "LOCK A SAUCER"}
            title, value = "DEVARGAS", labels.get(self.devargas_step, "")
        else:
            title = f"ATLANTEAN {self.atlantean_hits}/{self.atlantean_goal}"
            value = f"JP {self.atlantean_jackpot:,}"
        self.machine.events.post("show_mode_status", mode_status_title=title, mode_status_value=value)
        self._sync_vars()

    def _sync_vars(self):
        if not self.machine.game:
            return
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.atlantean_hits if self.phase == "atlantean" else 0
        player[f"{self.MODE_KEY}_case_file_bonus"] = self.case_file_bonus
        player[f"{self.MODE_KEY}_jackpot_value"] = self.atlantean_jackpot
