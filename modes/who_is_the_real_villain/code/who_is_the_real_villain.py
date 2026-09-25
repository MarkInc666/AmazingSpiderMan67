import random

from mpf.core.mode import Mode


class WhoIsTheRealVillain(Mode):
    """Chapter 10 wizard: Cameo investigation -> Desperado -> Brutus -> VUK Super.

    Repeating cycle:
      1. Hit both pops once to reveal one random Cameo pair (no repeats until
         all three pairs have been used).
      2. For A/B or slings, the pair is immediately active. For bank rubbers,
         the rooftop gate opens and each upper-spinner spin drops one standing
         bank target until the rubbers are exposed.
      3. While the pair is unresolved, all three saucers flash. Shoot any
         saucer to reveal the truth: the impostor shuts off and the correct
         Cameo target flashes. Hitting a candidate early scores 100K and plays
         one of the Daily Bugle impostor callouts.
      4. Correct Cameo shot starts Desperado. Collect each unique right-bank
         target once; the bank resets after every target. Upper-spinner spins
         may spot/drop the next needed target.
      5. Desperado completion starts Brutus with all three saucers lit. A left-
         bank hit shuts them off; a right-bank hit relights them. Any lit saucer
         completes Brutus.
      6. Gate opens and the shared rooftop chase points to the VUK for a 20s
         2M Super. Collect or miss it, then begin another Cameo cycle.

    Global rooftop rule: every upper target scores 50K. Completing unique L/C/R
    adds a ball up to four balls in play (15s add-a-ball save); at the four-ball
    cap it awards 500K + the Chapter 10 case-file bonus instead.

    Saucers park balls for up to 20 seconds whenever they are not active Cameo
    or Brutus objective shots. At least one loose ball is always kept in play.
    """

    MODE_KEY = "who_is_the_real_villain"
    DISPLAY_NAME = "WHO IS THE REAL VILLAIN?"

    MAX_BALLS = 4
    SAUCER_HOLD_MS = 20_000
    SAUCER_EJECT_MS = 500
    BANK_RESET_MS = 350

    IMPOSTOR_SCORE = 100_000
    REVEAL_SCORE = 100_000
    CAMEO_BASE = 1_000_000
    DESPERADO_TARGET_SCORE = 50_000
    BRUTUS_BASE = 500_000
    SUPER_BASE = 2_000_000
    UPPER_TARGET_SCORE = 50_000
    MAX_BALLS_SCORE_BASE = 500_000
    SUPER_SECONDS = 20

    CAMEO_PAIRS = ("ab", "slings", "rubbers")
    PAIR_LABELS = {
        "ab": "A + B",
        "slings": "LEFT / RIGHT SLINGS",
        "rubbers": "BANK RUBBERS",
    }

    RUBBER_EXPOSURE_ORDER = (
        ("left", 1), ("left", 2), ("left", 3),
        ("right", 1), ("right", 2), ("right", 3), ("right", 4), ("right", 5),
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.multiball_active = False
        self.mode_points = 0
        self.cycles_completed = 0
        self.supers_collected = 0
        self.add_a_balls = 0

        self.phase = "cameo_pops"
        self.cameo_pair_pool = list(self.CAMEO_PAIRS)
        self.cameo_pair = None
        self.cameo_correct_side = None
        self.cameo_truth_revealed = False
        self.pops_hit = set()
        self.rubber_exposure_index = 0

        self.desperado_collected = set()
        self.desperado_auto_ignore = set()
        self.brutus_saucers_lit = False

        self.super_seconds_left = 0
        self.held_saucers = []
        self.upper_targets_hit = set()

        player = self.machine.game.player
        self.case_file_bonus = int(player["mini_wizard_case_file_bonus"] or 0)
        player["mini_wizard_current_key"] = self.MODE_KEY
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player[f"{self.MODE_KEY}_case_file_bonus"] = self.case_file_bonus

        self._register_handlers()
        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("who_is_the_real_villain_clear_all")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("who_is_the_real_villain_start_multiball")
        self.machine.events.post("who_is_the_real_villain_upper_targets_reset")
        self._start_cameo_cycle()
        self._schedule_ball_guard()
        self._sync_vars()

    def mode_stop(self, **kwargs):
        self.delay.clear()
        self._release_all_saucers()
        self.machine.events.post("who_is_the_real_villain_clear_all")
        self.machine.events.post("who_is_the_real_villain_super_off")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        player = self.machine.game.player if self.machine.game else None
        if player and player["mini_wizard_current_key"] == self.MODE_KEY:
            player["mini_wizard_current_key"] = ""
        super().mode_stop(**kwargs)

    def _register_handlers(self):
        self.add_mode_event_handler("s_pop_left_active", self._pop_hit, pop="left")
        self.add_mode_event_handler("s_pop_right_active", self._pop_hit, pop="right")

        self.add_mode_event_handler("s_inlane_a_active", self._cameo_candidate_hit, pair="ab", side="left")
        self.add_mode_event_handler("s_inlane_b_active", self._cameo_candidate_hit, pair="ab", side="right")
        self.add_mode_event_handler("s_sling_l_active", self._cameo_candidate_hit, pair="slings", side="left")
        self.add_mode_event_handler("s_sling_r_active", self._cameo_candidate_hit, pair="slings", side="right")
        self.add_mode_event_handler("s_left_drops_rubber_active", self._cameo_candidate_hit, pair="rubbers", side="left")
        self.add_mode_event_handler("s_right_drops_rubber_active", self._cameo_candidate_hit, pair="rubbers", side="right")

        for target in range(1, 6):
            self.add_mode_event_handler(f"s_right_drops_{target}_active", self._right_drop_hit, target=target)
        for target in range(1, 4):
            self.add_mode_event_handler(f"s_left_drops_{target}_active", self._left_drop_hit, target=target)

        self.add_mode_event_handler("s_trispinner_opto_active", self._upper_spinner_hit)
        self.add_mode_event_handler("s_upper_target_left_active", self._upper_target_hit, target="left")
        self.add_mode_event_handler("s_upper_target_center_active", self._upper_target_hit, target="center")
        self.add_mode_event_handler("s_upper_target_right_active", self._upper_target_hit, target="right")

        for saucer in (1, 2, 3):
            self.add_mode_event_handler(f"s_saucer_{saucer}_active", self._saucer_hit, saucer=saucer)
        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)

        self.add_mode_event_handler(
            "multiball_who_is_the_real_villain_multiball_started", self._multiball_started
        )
        self.add_mode_event_handler(
            "multiball_who_is_the_real_villain_multiball_ended", self._multiball_ended
        )
        self.add_mode_event_handler("who_is_the_real_villain_complete_request", self._complete_mode)

    # ------------------------------------------------------------------
    # Cameo
    # ------------------------------------------------------------------
    def _start_cameo_cycle(self):
        if self.mode_done:
            return
        self.phase = "cameo_pops"
        self.pops_hit.clear()
        self.cameo_pair = None
        self.cameo_correct_side = None
        self.cameo_truth_revealed = False
        self.rubber_exposure_index = 0
        self.brutus_saucers_lit = False
        self.desperado_collected.clear()
        self.desperado_auto_ignore.clear()
        self.super_seconds_left = 0
        self.machine.events.post("who_is_the_real_villain_clear_phase_lights")
        self.machine.events.post("who_is_the_real_villain_super_off")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("who_is_the_real_villain_cameo_pops_on")
        self._show_message("CHARLES CAMEO", "HIT BOTH POPS TO REVEAL A PAIR", reminder=True)
        self._update_status()

    def _pop_hit(self, pop=None, **kwargs):
        if self.mode_done or self.phase != "cameo_pops" or pop not in ("left", "right"):
            return
        if pop in self.pops_hit:
            return
        self.pops_hit.add(pop)
        self.machine.events.post(f"who_is_the_real_villain_pop_{pop}_collected")
        if len(self.pops_hit) >= 2:
            self._select_cameo_pair()
        else:
            self._update_status()

    def _select_cameo_pair(self):
        if not self.cameo_pair_pool:
            self.cameo_pair_pool = list(self.CAMEO_PAIRS)
        self.cameo_pair = random.choice(self.cameo_pair_pool)
        self.cameo_pair_pool.remove(self.cameo_pair)
        self.cameo_correct_side = random.choice(("left", "right"))
        self.cameo_truth_revealed = False
        self.machine.events.post("who_is_the_real_villain_clear_cameo_pair")

        if self.cameo_pair == "rubbers":
            self.phase = "cameo_rubber_expose"
            self.rubber_exposure_index = 0
            self.machine.events.post("drop_target_bank_dt_bank_left_reset")
            self.machine.events.post("drop_target_bank_dt_bank_right_reset")
            self.machine.events.post("rooftop_diverter_open")
            self.machine.events.post("who_is_the_real_villain_rubber_expose")
            self._show_message("CAMEO: BANK RUBBERS", "UPPER SPINNER EXPOSES THE PAIR", reminder=True)
        else:
            self.phase = "cameo_pair"
            self.machine.events.post(f"who_is_the_real_villain_cameo_{self.cameo_pair}_pulse")
            self._enable_truth_saucers()
            self._show_message("CAMEO PAIR REVEALED", self.PAIR_LABELS[self.cameo_pair], reminder=True)
        self._update_status()

    def _cameo_candidate_hit(self, pair=None, side=None, **kwargs):
        if self.mode_done or pair != self.cameo_pair:
            return
        if self.phase not in ("cameo_pair", "cameo_truth"):
            return
        if not self.cameo_truth_revealed:
            self._score(self.IMPOSTOR_SCORE)
            self.machine.events.post(f"daily_bugle_ab_callout_{random.randint(1, 4)}")
            self._show_message("HE'S THE IMPOSTOR!", "REVEAL THE TRUTH AT A SAUCER", self.IMPOSTOR_SCORE)
            return
        if side != self.cameo_correct_side:
            return

        value = self._major_value(self.CAMEO_BASE)
        self._score(value)
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post("who_is_the_real_villain_cameo_complete")
        self._show_jackpot("CAMEO JACKPOT", value, "THE TRUTH REVEALED")
        self._start_desperado()

    def _enable_truth_saucers(self):
        self._release_all_saucers()
        self.machine.events.post("who_is_the_real_villain_saucers_flash")

    def _reveal_cameo_truth(self, saucer):
        self._score(self.REVEAL_SCORE)
        self.cameo_truth_revealed = True
        self.phase = "cameo_truth"
        self.machine.events.post("who_is_the_real_villain_saucers_off")
        self.machine.events.post("who_is_the_real_villain_clear_cameo_pair")
        self.machine.events.post(
            f"who_is_the_real_villain_cameo_{self.cameo_pair}_{self.cameo_correct_side}_flash"
        )
        self._show_message("TRUTH REVEALED", "HIT THE FLASHING TARGET", self.REVEAL_SCORE, reminder=True)
        self._eject_saucer(saucer, delay_ms=self.SAUCER_EJECT_MS)
        self._update_status()

    # ------------------------------------------------------------------
    # Desperado
    # ------------------------------------------------------------------
    def _start_desperado(self):
        self.phase = "desperado"
        self.desperado_collected.clear()
        self.desperado_auto_ignore.clear()
        self.machine.events.post("who_is_the_real_villain_clear_cameo_pair")
        self.machine.events.post("who_is_the_real_villain_saucers_off")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("who_is_the_real_villain_desperado_start")
        self._restore_desperado_lights()
        self._show_message("DESPERADO", "HIT EACH RIGHT DROP ONCE", reminder=True)
        self._update_status()

    def _right_drop_hit(self, target=None, **kwargs):
        if self.mode_done or target not in range(1, 6):
            return
        if self.phase == "desperado":
            if target in self.desperado_auto_ignore:
                self.desperado_auto_ignore.discard(target)
                return
            self._collect_desperado_target(target)
            return
        if self.phase == "brutus" and not self.brutus_saucers_lit:
            self._reset_bank("right")
            self._set_brutus_saucers(True)

    def _left_drop_hit(self, target=None, **kwargs):
        if self.mode_done:
            return
        if self.phase == "brutus" and self.brutus_saucers_lit:
            self._reset_bank("left")
            self._set_brutus_saucers(False)
            self._show_message("BRUTUS RETURNS", "HIT RIGHT BANK TO REOPEN SAUCERS", reminder=True)

    def _collect_desperado_target(self, target, spotted=False):
        if self.phase != "desperado":
            return
        if target not in self.desperado_collected:
            self.desperado_collected.add(target)
            self._score(self.DESPERADO_TARGET_SCORE)
            self.machine.events.post(f"who_is_the_real_villain_desperado_target_{target}_solid")
            self._show_message(
                "DESPERADO",
                f"TARGET {target} FOUND - {len(self.desperado_collected)}/5",
                self.DESPERADO_TARGET_SCORE,
            )
        self._reset_bank("right")
        if len(self.desperado_collected) >= 5:
            self.delay.reset(name="real_villain_start_brutus", ms=450, callback=self._start_brutus)
        else:
            self.delay.reset(name="real_villain_restore_desperado", ms=450, callback=self._restore_desperado_lights)
            self._update_status()

    def _restore_desperado_lights(self):
        if self.mode_done or self.phase != "desperado":
            return
        self.machine.events.post("who_is_the_real_villain_desperado_clear_inserts")
        for target in range(1, 6):
            state = "solid" if target in self.desperado_collected else "pulse"
            self.machine.events.post(f"who_is_the_real_villain_desperado_target_{target}_{state}")

    # ------------------------------------------------------------------
    # Brutus
    # ------------------------------------------------------------------
    def _start_brutus(self):
        if self.mode_done:
            return
        self.phase = "brutus"
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("who_is_the_real_villain_desperado_stop")
        self._reset_bank("left")
        self._reset_bank("right")
        self._set_brutus_saucers(True)
        self._show_message("BRUTUS", "SHOOT ANY FLASHING SAUCER", reminder=True)
        self._update_status()

    def _set_brutus_saucers(self, lit):
        self.brutus_saucers_lit = bool(lit)
        if lit:
            self._release_all_saucers()
            self.machine.events.post("who_is_the_real_villain_saucers_flash")
        else:
            self.machine.events.post("who_is_the_real_villain_saucers_off")
        self._update_status()

    def _complete_brutus(self, saucer):
        value = self._major_value(self.BRUTUS_BASE)
        self._score(value)
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post("who_is_the_real_villain_saucers_off")
        self.brutus_saucers_lit = False
        self._show_jackpot("BRUTUS JACKPOT", value, "THE WAY IS CLEAR")
        self._eject_saucer(saucer, delay_ms=750)
        self.delay.reset(name="real_villain_start_super", ms=900, callback=self._start_super)

    # ------------------------------------------------------------------
    # VUK Super
    # ------------------------------------------------------------------
    def _start_super(self):
        if self.mode_done:
            return
        self.phase = "super"
        self.super_seconds_left = self.SUPER_SECONDS
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("who_is_the_real_villain_super_on")
        value = self._major_value(self.SUPER_BASE)
        self._show_countdown("SUPER JACKPOT LIT", "SHOOT DAILY BUGLE", value, self.super_seconds_left)
        self._schedule_super_tick()
        self._update_status()

    def _schedule_super_tick(self):
        self.delay.reset(name="real_villain_super_tick", ms=1000, callback=self._super_tick)

    def _super_tick(self):
        if self.mode_done or self.phase != "super":
            return
        self.super_seconds_left -= 1
        if self.super_seconds_left <= 0:
            self.machine.events.post("who_is_the_real_villain_super_off")
            self._show_message("SUPER LOST", "CAMEO RETURNS")
            self.cycles_completed += 1
            self.delay.reset(name="real_villain_next_cycle", ms=700, callback=self._start_cameo_cycle)
            self._sync_vars()
            return
        self._show_countdown(
            "SUPER JACKPOT LIT",
            "SHOOT DAILY BUGLE",
            self._major_value(self.SUPER_BASE),
            self.super_seconds_left,
        )
        self._schedule_super_tick()
        self._update_status()

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            self.machine.events.post("request_vuk_eject", delay_ms=0)
            return
        if self.phase == "super":
            # Move out of the collectible state immediately. The raw VUK
            # switch can chatter/retrigger while the ball is physically held;
            # without this guard the Super and its audio could award repeatedly.
            self.phase = "super_collected"
            self.delay.remove("real_villain_super_tick")
            self.machine.events.post("who_is_the_real_villain_super_off")
            value = self._major_value(self.SUPER_BASE)
            self._score(value)
            self.supers_collected += 1
            self.cycles_completed += 1
            self.machine.events.post("play_mode_super_jackpot")
            self._show_jackpot("SUPER JACKPOT", value, f"CYCLE {self.cycles_completed} COMPLETE")
            self.machine.events.post("request_vuk_eject", delay_ms=1_500)
            self.delay.reset(name="real_villain_next_cycle", ms=1_750, callback=self._start_cameo_cycle)
            self._sync_vars()
            return
        self.machine.events.post("request_vuk_eject", delay_ms=500)

    # ------------------------------------------------------------------
    # Rooftop / add-a-ball
    # ------------------------------------------------------------------
    def _upper_spinner_hit(self, **kwargs):
        if self.mode_done:
            return
        if self.phase == "cameo_rubber_expose":
            self._drop_next_rubber_exposure_target()
        elif self.phase == "desperado":
            remaining = [t for t in range(1, 6) if t not in self.desperado_collected]
            if remaining:
                target = remaining[0]
                self.desperado_auto_ignore.add(target)
                self._pulse_drop("right", target)
                self._collect_desperado_target(target, spotted=True)

    def _drop_next_rubber_exposure_target(self):
        if self.rubber_exposure_index >= len(self.RUBBER_EXPOSURE_ORDER):
            return
        bank, target = self.RUBBER_EXPOSURE_ORDER[self.rubber_exposure_index]
        self._pulse_drop(bank, target)
        self.rubber_exposure_index += 1
        if self.rubber_exposure_index >= len(self.RUBBER_EXPOSURE_ORDER):
            self.phase = "cameo_pair"
            self.machine.events.post("who_is_the_real_villain_rubber_expose_done")
            self.machine.events.post("who_is_the_real_villain_cameo_rubbers_pulse")
            self._enable_truth_saucers()
            self._show_message("RUBBERS EXPOSED", "SHOOT A SAUCER TO REVEAL THE TRUTH", reminder=True)
        self._update_status()

    def _upper_target_hit(self, target=None, **kwargs):
        if self.mode_done or target not in ("left", "center", "right"):
            return
        self._score(self.UPPER_TARGET_SCORE)
        self.upper_targets_hit.add(target)
        self.machine.events.post(f"who_is_the_real_villain_upper_{target}_solid")
        if len(self.upper_targets_hit) >= 3:
            self.upper_targets_hit.clear()
            if self._balls_in_play() < self.MAX_BALLS:
                self.add_a_balls += 1
                self.machine.events.post("who_is_the_real_villain_add_a_ball")
                self._show_message("ADD-A-BALL", "UPPER TARGETS COMPLETE")
            else:
                value = self._major_value(self.MAX_BALLS_SCORE_BASE)
                self._score(value)
                self.machine.events.post("play_mode_jackpot")
                self._show_jackpot("4-BALL MAX JACKPOT", value, "UPPER TARGETS COMPLETE")
            self.machine.events.post("who_is_the_real_villain_upper_targets_reset")
        self._sync_vars()

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

        if self.phase == "cameo_pair" and self.cameo_pair is not None and not self.cameo_truth_revealed:
            self._reveal_cameo_truth(saucer)
            return
        if self.phase == "brutus" and self.brutus_saucers_lit:
            self._complete_brutus(saucer)
            return

        self._park_saucer(saucer)
        self._ensure_free_ball()

    def _park_saucer(self, saucer):
        if saucer not in self.held_saucers:
            self.held_saucers.append(saucer)
        self.delay.remove(f"real_villain_saucer_{saucer}")
        self.delay.add(
            name=f"real_villain_saucer_{saucer}",
            ms=self.SAUCER_HOLD_MS,
            callback=self._release_saucer,
            saucer=saucer,
        )
        self.machine.events.post(f"who_is_the_real_villain_saucer_{saucer}_parked")

    def _release_saucer(self, saucer=None):
        if saucer not in self.held_saucers:
            return
        self.held_saucers.remove(saucer)
        self.delay.remove(f"real_villain_saucer_{saucer}")
        self.machine.events.post(f"who_is_the_real_villain_saucer_{saucer}_released")
        self._eject_saucer(saucer)

    def _release_all_saucers(self):
        for saucer in list(self.held_saucers):
            self._release_saucer(saucer)

    def _ensure_free_ball(self):
        if self._balls_in_play() - len(self.held_saucers) >= 1:
            return
        if self.held_saucers:
            self._release_saucer(self.held_saucers[0])

    def _eject_saucer(self, saucer, delay_ms=0):
        self.machine.events.post("request_saucer_eject", saucer_number=saucer, delay_ms=delay_ms)

    # ------------------------------------------------------------------
    # Ball lifecycle / helpers
    # ------------------------------------------------------------------
    def _multiball_started(self, **kwargs):
        self.multiball_active = True

    def _multiball_ended(self, **kwargs):
        if self.mode_done or not self.multiball_active:
            return
        # MPF's multiball lifecycle is authoritative. This event is posted
        # when the multiball has collapsed to its configured end condition
        # (one ball remaining for this mode), so do not re-count balls here.
        self.multiball_active = False
        self._complete_mode()

    def _schedule_ball_guard(self):
        self.delay.reset(name="real_villain_ball_guard", ms=500, callback=self._ball_guard)

    def _ball_guard(self):
        if self.mode_done:
            return
        # Keep at least one loose ball available when balls are parked in
        # saucers, but never use transient balls_in_play counts to decide
        # whether multiball has ended. MPF's multiball_..._ended event owns
        # that transition.
        self._ensure_free_ball()
        self._schedule_ball_guard()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars()
        self.machine.events.post("who_is_the_real_villain_mode_complete")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("stop_mode_who_is_the_real_villain")

    def _reset_bank(self, bank):
        self.delay.reset(
            name=f"real_villain_reset_{bank}_bank",
            ms=self.BANK_RESET_MS,
            callback=lambda: self.machine.events.post(f"drop_target_bank_dt_bank_{bank}_reset"),
        )

    def _pulse_drop(self, bank, target):
        coil = f"c_{bank}_bank_drop_{target}"
        try:
            self.machine.coils[coil].pulse()
        except KeyError:
            self.warning_log("Missing %s while running Who Is the Real Villain", coil)

    def _major_value(self, base):
        return int(base) + self.case_file_bonus if int(base) >= 500_000 else int(base)

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return int(self.machine.game.balls_in_play or 0)

    def _score(self, points):
        if not points:
            return
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.cycles_completed
        player["active_mode_major_hits"] = self.supers_collected
        player[f"{self.MODE_KEY}_case_file_bonus"] = self.case_file_bonus
        player[f"{self.MODE_KEY}_cycles"] = self.cycles_completed
        player[f"{self.MODE_KEY}_supers"] = self.supers_collected
        player[f"{self.MODE_KEY}_add_a_balls"] = self.add_a_balls

    def _show_message(self, title, subtitle="", value=None, reminder=False):
        kwargs = {
            "message_mode_title": title,
            "message_mode_subtitle": subtitle,
            "reminder": reminder,
        }
        if value is not None:
            kwargs["message_mode_value"] = value
        self.machine.events.post("show_mode_message", **kwargs)
        self.machine.events.post("reset_mode_message_reminder")

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
        )

    def _show_countdown(self, title, subtitle, value, seconds):
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
        )

    def _update_status(self):
        if self.phase == "cameo_pops":
            title = "CAMEO - FIND THE PAIR"
            value = f"POPS {len(self.pops_hit)}/2"
        elif self.phase == "cameo_rubber_expose":
            title = "CAMEO - EXPOSE RUBBERS"
            value = f"UPPER SPINS {self.rubber_exposure_index}/8"
        elif self.phase == "cameo_pair":
            title = "CAMEO - REVEAL TRUTH"
            value = "SHOOT ANY SAUCER"
        elif self.phase == "cameo_truth":
            title = "CAMEO - TRUTH REVEALED"
            value = "HIT FLASHING TARGET"
        elif self.phase == "desperado":
            title = "DESPERADO"
            value = f"TARGETS {len(self.desperado_collected)}/5"
        elif self.phase == "brutus":
            title = "BRUTUS"
            value = "SHOOT SAUCER" if self.brutus_saucers_lit else "HIT RIGHT BANK"
        else:
            title = "SUPER JACKPOT"
            value = f"DAILY BUGLE - {max(0, self.super_seconds_left)}s"
        self.machine.events.post("show_mode_status", mode_status_title=title, mode_status_value=value)
