import random

from mpf.core.mode import Mode


class FinalShowdown(Mode):
    """Kingpin / Final Showdown.

    Final Showdown is a two-ball multiball built from five recap phases. The
    lower spinner chooses the next unplayed phase while the current phase is
    active. Phase jackpots are scored immediately and also accumulated in the
    Kingpin Bank. After all five phases, three balls must be locked in the
    saucers. That exposes Kingpin, opens the rooftop gate, releases the three
    locks two seconds apart, and leaves the Daily Bugle VUK as the final shot.
    Unused future game balls can buy retries of that final shot.
    """

    PHASES = ("timed", "staged_drops", "rooftop", "area_control", "reveal")
    PHASE_NAMES = {
        "timed": "TIMED COLLECT",
        "staged_drops": "STAGED DROPS",
        "rooftop": "ROOFTOP BUILD",
        "area_control": "AREA CONTROL",
        "reveal": "REVEAL & COLLECT",
        "final_lock": "KINGPIN",
    }

    MAX_BALLS = 4
    SAUCER_HOLD_MS = 20_000
    ADDED_BALL_PENDING_MS = 2_000
    FINAL_VICTORY_HOLD_MS = 8_000

    TIMED_DURATION_MS = 20_000
    TIMED_SPAWN_MS = 1_000
    TIMED_SHOT_VALUE = 100_000
    TIMED_SUPER_BASE = 1_000_000
    TIMED_SUPER_PER_SHOT = 250_000
    WEB_COLLECT_MS = 20_000

    STAGED_TARGET_VALUE = 250_000
    STAGED_BASE_JACKPOT = 1_000_000
    STAGED_MULTIPLIERS = (1, 2, 3, 5)
    STAGED_SETTLE_MS = 450

    ROOFTOP_FLIPS = 20
    ROOFTOP_SPIN_VALUE = 100_000

    AREA_LOWER_MS = 25_000
    AREA_ROOF_MS = 20_000
    AREA_SPINNER_VALUE = 100_000

    REVEAL_DROP_VALUE = 50_000
    REVEAL_SAUCER_VALUES = {1: 1_000_000, 2: 2_000_000, 3: 3_000_000}
    REVEAL_EJECT_MS = 2_000
    REVEAL_FINISH_AFTER_EJECT_MS = 200

    TIMED_SHOTS = (
        "left_web",
        "center_web",
        "left_pop",
        "right_pop",
        "left_bank",
        "right_bank",
        "upper_a",
        "upper_b",
        "middle_a",
        "middle_b",
        "upper_targets",
        "spinner",
        "upper_spinner",
    )
    TIMED_UPPER_SHOTS = {"upper_targets", "upper_spinner"}

    DROP_TARGETS = (
        "left_1", "left_2", "left_3",
        "right_1", "right_2", "right_3", "right_4", "right_5",
    )

    SAUCER_EJECT_EVENTS = {
        1: "kickout_saucer_1",
        2: "kickout_saucer_2",
        3: "kickout_saucer_3",
    }

    PERSISTENT_VARS = {
        "active_mode_points",
        "active_mode_hits",
        "active_mode_major_hits",
        "final_showdown_state",
    }

    def _post_mode_jackpot_sfx_if_needed(
        self,
        guarded_display_event="",
        message_mode_title="",
        message_mode_subtitle="",
    ):
        if guarded_display_event != "base_show_mode_jackpot":
            return
        title = str(message_mode_title or "").upper()
        subtitle = str(message_mode_subtitle or "").upper()
        words = f"{title} {subtitle}".replace("-", " ").split()
        if "JACKPOT" not in words:
            return
        if any(marker in title.split() for marker in ("BUILDS", "LIT", "READY", "NEXT")):
            return
        self.machine.events.post(
            "play_mode_super_jackpot" if "SUPER" in words else "play_mode_jackpot"
        )

    # ------------------------------------------------------------------
    # Mode lifecycle
    # ------------------------------------------------------------------
    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        # A fresh Final Showdown attempt must not inherit the completed flag
        # from an earlier Kingpin victory (important for test-mode replays too).
        if self.machine.game and self.machine.game.player:
            self.machine.game.player["final_wizard_completed"] = 0

        self._runtime_state = {}
        self.mode_exiting = False
        self.current_phase = None
        self.played_phases = set()
        self.next_phase = None
        self.kingpin_bank = 0

        self.a_hit = False
        self.b_hit = False
        self.add_a_ball_ready = False
        self.pending_add_a_ball = False

        self.held_saucers = set()
        self.locked_saucers = set()
        # Each delayed Kingpin saucer eject gets a per-saucer generation token.
        # A new hit/action invalidates any older callback so a stale Reveal,
        # parking, or final-lock release can never eject a newly owned ball.
        self._saucer_eject_generation = {1: 0, 2: 0, 3: 0}
        self.final_gate_ready = False
        self.final_shot_active = False

        self.timed_active = set()
        self.timed_last_shot = None
        self.timed_shots_made = 0
        self.web_collect_kind = None
        self.web_collect_value = 0

        self.staged_stage = 0
        self.staged_successes = 0
        self.staged_target = None
        self.staged_programming = False
        self.staged_used_targets = set()

        self.roof_visit_active = False
        self.roof_flips_remaining = 0
        self.roof_spinner_spins = 0
        self.roof_target_hits = {"left": 0, "center": 0, "right": 0}

        self.area_lower = self._new_area_state()
        self.area_roof_active = False
        self.area_roof_target_hit = False
        self.area_spinner_spins = 0

        self.reveal_count = 0
        self.reveal_collect_started = False
        self.reveal_collect_value = 0
        self.reveal_lit_positions = set()

        self._reset_player_vars()
        self._register_handlers()

        # Final Showdown owns all saucer timing while active. Cancel any
        # delayed clear/eject left behind by bookends or another mode before
        # taking ownership, then clear any balls physically sitting in a saucer.
        self.machine.events.post("cancel_pending_saucer_ejects")
        self._clear_startup_saucers()

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("cmd_upper_flippers_enable")
        self.machine.events.post("final_showdown_clear_all_final_showdown_lights")
        self.machine.events.post("final_showdown_ab_available_show")

    def mode_stop(self, **kwargs):
        self.mode_exiting = True
        self.delay.clear()
        self._release_all_saucers()
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("final_showdown_disable_final_shot_save")
        self.machine.events.post("final_showdown_clear_all_final_showdown_lights")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        super().mode_stop(**kwargs)

    def _clear_startup_saucers(self):
        occupied = []
        for saucer in (1, 2, 3):
            switch = self.machine.switches.get(f"s_saucer_{saucer}")
            if switch and self.machine.switch_controller.is_active(switch):
                occupied.append(saucer)
        for index, saucer in enumerate(occupied):
            self._eject_saucer(
                saucer,
                delay_ms=index * 300,
                owner="startup_clear",
                expected_phase=None,
            )

    def _register_handlers(self):
        # Multiball / drain lifecycle.
        self.add_mode_event_handler(
            "multiball_final_showdown_multiball_started", self._multiball_started
        )
        self.add_mode_event_handler(
            "multiball_final_showdown_multiball_ended", self._multiball_ended
        )
        self.add_mode_event_handler("ball_drain", self._ball_drain)
        self.add_mode_event_handler(
            "ball_will_end", self._ball_will_end, priority=100000
        )
        self.add_mode_event_handler(
            "ball_save_final_showdown_final_shot_save_saving_ball",
            self._final_shot_ball_saved,
            priority=100000,
        )
        self.add_mode_event_handler("final_showdown_release_all_saucers", self._release_all_saucers)
        self.add_mode_event_handler("final_showdown_test_last_ball_lost", self._test_last_ball_lost)

        # A+B / flipper controls.
        self.add_mode_event_handler("s_inlane_a_active", self._a_rollover)
        self.add_mode_event_handler("s_inlane_m_r_active", self._middle_a)
        self.add_mode_event_handler("s_inlane_b_active", self._b_rollover)
        self.add_mode_event_handler("s_inlane_m_l_active", self._middle_b)
        self.add_mode_event_handler("s_left_flipper_active", self._left_flipper)
        self.add_mode_event_handler("s_right_flipper_active", self._right_flipper)
        self.add_mode_event_handler("s_right_flipper_upper_active", self._upper_flipper)

        # Spinners / rooftop.
        self.add_mode_event_handler("s_web_spinner_active", self._main_spinner)
        self.add_mode_event_handler("s_trispinner_opto_active", self._upper_spinner)
        self.add_mode_event_handler("s_upper_entrance_opto_active", self._upper_entrance)
        self.add_mode_event_handler("s_upper_exit_left_opto_active", self._roof_exit, exit_name="left")
        self.add_mode_event_handler("s_upper_exit_right_opto_active", self._roof_exit, exit_name="right")
        self.add_mode_event_handler("s_right_drops_top_rubber_active", self._center_exit_proxy)

        # Upper targets.
        self.add_mode_event_handler("s_upper_target_left_active", self._upper_target, target="left")
        self.add_mode_event_handler("s_upper_target_center_active", self._upper_target, target="center")
        self.add_mode_event_handler("s_upper_target_right_active", self._upper_target, target="right")

        # Web targets.
        self.add_mode_event_handler("s_web_target_left_active", self._web_target, shot="left_web")
        self.add_mode_event_handler("s_web_target_mid_active", self._web_target, shot="center_web")

        # Pops / slings / rubbers.
        self.add_mode_event_handler("s_pop_left_active", self._pop, side="left")
        self.add_mode_event_handler("s_pop_right_active", self._pop, side="right")
        self.add_mode_event_handler("s_sling_l_active", self._sling, side="left")
        self.add_mode_event_handler("s_sling_r_active", self._sling, side="right")
        self.add_mode_event_handler("s_left_drops_rubber_active", self._bank_rubber, bank="left")
        self.add_mode_event_handler("s_right_drops_rubber_active", self._bank_rubber, bank="right")

        # Individual drops and bank completions.
        for target in self.DROP_TARGETS:
            self.add_mode_event_handler(
                f"s_{target.split('_')[0]}_drops_{target.split('_')[1]}_active",
                self._drop_target,
                target=target,
            )
        self.add_mode_event_handler("drop_target_bank_dt_bank_left_down", self._bank_complete, bank="left")
        self.add_mode_event_handler("drop_target_bank_dt_bank_right_down", self._bank_complete, bank="right")

        # Saucers / VUK.
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(
                f"s_saucer_{saucer}_active", self._saucer_hit, saucer=saucer
            )
        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)

    def _reset_player_vars(self):
        self._set("active_mode_points", 0)
        self._set("active_mode_hits", 0)
        self._set("active_mode_major_hits", 0)
        self._set("final_showdown_state", 1)
        self._set("final_showdown_current_area", "")
        self._set("final_showdown_current_area_display", "FINAL SHOWDOWN")
        self._set("final_showdown_area_progress", 0)
        self._set("final_showdown_area_required", len(self.PHASES))
        self._set("final_showdown_hits_still_needed", len(self.PHASES))
        self._set("final_showdown_areas_cleared", 0)
        self._set("final_showdown_jackpots", 0)
        self._set("final_showdown_super_jackpots", 0)
        self._set("final_showdown_jackpot_ready", 0)
        self._set("final_showdown_jackpot_value", 0)
        self._set("final_showdown_super_jackpot_ready", 0)
        self._set("final_showdown_super_jackpot_value", 0)
        self._set("final_showdown_a_hit", 0)
        self._set("final_showdown_b_hit", 0)
        self._set("final_showdown_ab_ready", 0)
        self._set("final_showdown_kingpin_bank", 0)
        self._set("final_showdown_next_phase", "")

    def _multiball_started(self, **kwargs):
        if self.mode_exiting:
            return
        self._start_phase("timed")

    # ------------------------------------------------------------------
    # Phase framework / spinner selection
    # ------------------------------------------------------------------
    def _start_phase(self, phase):
        if self.mode_exiting:
            return
        if phase == "final_lock":
            self._start_final_lock()
            return
        if phase not in self.PHASES or phase in self.played_phases:
            return

        self._invalidate_all_saucer_ejects()
        self.current_phase = phase
        self.played_phases.add(phase)
        self._set("final_showdown_current_area", phase)
        self._set("final_showdown_current_area_display", self.PHASE_NAMES[phase])
        self._set("final_showdown_areas_cleared", len(self.played_phases) - 1)
        self._set("final_showdown_area_progress", len(self.played_phases) - 1)
        self._set("final_showdown_hits_still_needed", len(self.PHASES) - len(self.played_phases) + 1)

        remaining = self._unplayed_phases()
        self.next_phase = remaining[0] if remaining else None
        self._publish_next_phase()

        self.machine.events.post("cmd_upper_flippers_enable")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("final_showdown_phase_changed", phase=phase)
        if phase == "reveal":
            self.machine.events.post("final_showdown_parking_saucers_off")
        else:
            self.machine.events.post("final_showdown_parking_saucers_on")

        getattr(self, f"_start_{phase}_phase")()

    def _finish_phase(self):
        if self.mode_exiting or self.current_phase not in self.PHASES:
            return
        phase = self.current_phase
        self._cleanup_phase(phase)
        self._set("final_showdown_areas_cleared", len(self.played_phases))
        self._set("final_showdown_area_progress", len(self.played_phases))
        self._set("final_showdown_hits_still_needed", len(self.PHASES) - len(self.played_phases))
        self.machine.events.post("final_showdown_phase_complete", phase=phase)

        remaining = self._unplayed_phases()
        if not remaining:
            self.current_phase = None
            self.next_phase = None
            self._publish_next_phase()
            self.delay.reset(name="final_showdown_next_phase", ms=500, callback=self._start_final_lock)
            return

        selected = self.next_phase if self.next_phase in remaining else remaining[0]
        self.current_phase = None
        self.delay.reset(
            name="final_showdown_next_phase",
            ms=500,
            callback=self._start_phase,
            phase=selected,
        )

    def _cleanup_phase(self, phase):
        if phase == "timed":
            self.delay.remove("final_showdown_timed_end")
            self.delay.remove("final_showdown_timed_spawn")
            self._clear_timed_shots()
        elif phase == "staged_drops":
            self.delay.remove("final_showdown_staged_settle")
            self.delay.remove("final_showdown_web_collect_timeout")
            self.staged_programming = False
            self.staged_target = None
            self._clear_web_collect()
            self._reset_drop_banks()
        elif phase == "rooftop":
            self.roof_visit_active = False
            self.machine.events.post("cmd_upper_flippers_enable")
            self.machine.events.post("rooftop_diverter_close")
            self.machine.events.post("final_showdown_rooftop_off")
        elif phase == "area_control":
            self.delay.remove("final_showdown_area_lower_timeout")
            self.delay.remove("final_showdown_area_roof_timeout")
            self.area_roof_active = False
            self.machine.events.post("rooftop_diverter_close")
            self.machine.events.post("final_showdown_area_control_off")
        elif phase == "reveal":
            self.machine.events.post("final_showdown_reveal_clear")
            self._reset_drop_banks()

    def _unplayed_phases(self):
        return [phase for phase in self.PHASES if phase not in self.played_phases]

    def _advance_next_phase(self):
        if self.current_phase not in self.PHASES:
            return
        remaining = self._unplayed_phases()
        if not remaining:
            self.next_phase = None
            self._publish_next_phase()
            return
        if self.next_phase not in remaining:
            self.next_phase = remaining[0]
        else:
            index = remaining.index(self.next_phase)
            self.next_phase = remaining[(index + 1) % len(remaining)]
        self._publish_next_phase()
        self.machine.events.post("final_showdown_next_phase_changed", phase=self.next_phase)

    def _publish_next_phase(self):
        display = self.PHASE_NAMES.get(self.next_phase, "KINGPIN") if self.next_phase else "KINGPIN"
        self._set("final_showdown_next_phase", display)

    # ------------------------------------------------------------------
    # A+B add-a-ball
    # ------------------------------------------------------------------
    def _a_rollover(self, **kwargs):
        self._timed_hit("upper_a")
        self._mark_a()

    def _middle_a(self, **kwargs):
        self._timed_hit("middle_a")
        self._mark_a()
        self._center_exit_proxy()

    def _b_rollover(self, **kwargs):
        self._timed_hit("upper_b")
        self._mark_b()

    def _middle_b(self, **kwargs):
        self._timed_hit("middle_b")
        self._mark_b()

    def _mark_a(self):
        if self.mode_exiting or self.a_hit:
            return
        self.a_hit = True
        self._set("final_showdown_a_hit", 1)
        self.machine.events.post("final_showdown_a_hit")
        self._check_ab()

    def _mark_b(self):
        if self.mode_exiting or self.b_hit:
            return
        self.b_hit = True
        self._set("final_showdown_b_hit", 1)
        self.machine.events.post("final_showdown_b_hit")
        self._check_ab()

    def _check_ab(self):
        if self.add_a_ball_ready or not (self.a_hit and self.b_hit):
            return
        self.add_a_ball_ready = True
        self._set("final_showdown_ab_ready", 1)
        self.machine.events.post("final_showdown_ab_complete")
        self.machine.events.post("final_showdown_ab_available_clear_show")
        self.machine.events.post("final_showdown_add_a_ball_ready_show")
        self._show_message("ADD-A-BALL READY", "SHOOT ANY SAUCER")

    def _collect_add_a_ball_if_ready(self):
        if not self.add_a_ball_ready or self._balls_in_play() >= self.MAX_BALLS:
            return False

        # MPF ends a multiball device when play drops to one ball. Final
        # Showdown deliberately continues on that last ball, so the normal
        # add_a_ball event is no longer valid at that point. Restart the
        # 2-ball multiball from one ball; from 2-3 balls use its normal
        # add-a-ball path.
        if self._balls_in_play() <= 1:
            self.machine.events.post("final_showdown_start_multiball")
        else:
            self.machine.events.post("final_showdown_add_a_ball")

        self.pending_add_a_ball = True
        self.delay.reset(
            name="final_showdown_add_ball_pending",
            ms=self.ADDED_BALL_PENDING_MS,
            callback=self._clear_pending_add_a_ball,
        )
        self._reset_ab()
        self._show_message("ADD-A-BALL", "BALL SERVED")
        return True

    def _clear_pending_add_a_ball(self):
        self.pending_add_a_ball = False
        if self.current_phase == "final_lock":
            self._check_final_lock_state()

    def _reset_ab(self):
        self.a_hit = False
        self.b_hit = False
        self.add_a_ball_ready = False
        self._set("final_showdown_a_hit", 0)
        self._set("final_showdown_b_hit", 0)
        self._set("final_showdown_ab_ready", 0)
        self.machine.events.post("final_showdown_ab_reset")
        self.machine.events.post("final_showdown_add_a_ball_ready_clear")
        self.machine.events.post("final_showdown_ab_available_show")

    # ------------------------------------------------------------------
    # Phase 1: timed City-of-Gold-style collect
    # ------------------------------------------------------------------
    def _start_timed_phase(self):
        self.timed_active.clear()
        self.timed_last_shot = None
        self.timed_shots_made = 0
        self.web_collect_kind = None
        self.web_collect_value = 0
        self._show_message("TIMED COLLECT", "20 SECONDS - 100K PER SHOT", reminder=True)
        self._update_timed_status()
        self._spawn_timed_shot()
        self.delay.reset(
            name="final_showdown_timed_end",
            ms=self.TIMED_DURATION_MS,
            callback=self._timed_window_ended,
        )

    def _spawn_timed_shot(self):
        if self.current_phase != "timed" or self.web_collect_kind:
            return
        choices = [shot for shot in self.TIMED_SHOTS if shot not in self.timed_active]
        if len(choices) > 1 and self.timed_last_shot in choices:
            choices.remove(self.timed_last_shot)
        if choices:
            shot = random.choice(choices)
            self.timed_active.add(shot)
            self.timed_last_shot = shot
            self.machine.events.post(f"final_showdown_timed_{shot}_on")
            self._sync_timed_gate()
        self.delay.reset(
            name="final_showdown_timed_spawn",
            ms=self.TIMED_SPAWN_MS,
            callback=self._spawn_timed_shot,
        )

    def _timed_hit(self, shot):
        if self.current_phase != "timed" or shot not in self.timed_active:
            return False
        self.timed_active.discard(shot)
        self.machine.events.post(f"final_showdown_timed_{shot}_off")
        self.timed_shots_made += 1
        self._score(self.TIMED_SHOT_VALUE)
        self._sync_timed_gate()
        self._update_timed_status()
        return True

    def _timed_window_ended(self):
        if self.current_phase != "timed" or self.web_collect_kind:
            return
        self.delay.remove("final_showdown_timed_spawn")
        self._clear_timed_shots()
        self.machine.events.post("rooftop_diverter_close")
        value = self.TIMED_SUPER_BASE + (self.timed_shots_made * self.TIMED_SUPER_PER_SHOT)
        self._start_web_collect("timed_super", value)

    def _clear_timed_shots(self):
        for shot in list(self.timed_active):
            self.machine.events.post(f"final_showdown_timed_{shot}_off")
        self.timed_active.clear()
        self._sync_timed_gate()

    def _sync_timed_gate(self):
        if self.current_phase != "timed":
            return
        should_open = any(shot in self.TIMED_UPPER_SHOTS for shot in self.timed_active)
        self.machine.events.post("rooftop_diverter_open" if should_open else "rooftop_diverter_close")

    def _update_timed_status(self):
        self._show_status("TIMED COLLECT", f"SHOTS {self.timed_shots_made}  BANK {self.kingpin_bank:,}")

    # ------------------------------------------------------------------
    # Phase 2: staged precision drops
    # ------------------------------------------------------------------
    def _start_staged_drops_phase(self):
        self.staged_stage = 0
        self.staged_successes = 0
        self.staged_target = None
        self.staged_programming = False
        self.staged_used_targets.clear()
        self._show_message("STAGED DROPS", "HIT THE ONE STANDING TARGET")
        self._start_next_staged_target()

    def _start_next_staged_target(self):
        if self.current_phase != "staged_drops":
            return
        if self.staged_stage >= 3:
            multiplier = self.STAGED_MULTIPLIERS[self.staged_successes]
            value = self.STAGED_BASE_JACKPOT * multiplier
            self._start_web_collect("staged_jackpot", value)
            return

        available = [target for target in self.DROP_TARGETS if target not in self.staged_used_targets]
        if not available:
            available = list(self.DROP_TARGETS)
        self.staged_target = random.choice(available)
        self.staged_used_targets.add(self.staged_target)
        self.staged_stage += 1
        self.staged_programming = True

        self._reset_drop_banks()
        self.delay.reset(
            name="final_showdown_staged_settle",
            ms=self.STAGED_SETTLE_MS,
            callback=self._program_staged_target,
        )
        self._show_status(
            "STAGED DROPS",
            f"STAGE {self.staged_stage}/3  HITS {self.staged_successes}",
        )

    def _program_staged_target(self):
        if self.current_phase != "staged_drops" or not self.staged_target:
            return
        for target in self.DROP_TARGETS:
            if target == self.staged_target:
                continue
            try:
                device = self.machine.drop_targets[f"dt_{target}"]
            except KeyError:
                continue
            device.knockdown()
        self.delay.reset(
            name="final_showdown_staged_ready",
            ms=250,
            callback=self._staged_ready,
        )

    def _staged_ready(self):
        self.staged_programming = False
        if self.current_phase == "staged_drops":
            self._show_message(
                "PRECISION SHOT",
                f"STAGE {self.staged_stage} - AVOID THE RUBBER",
            )

    def _resolve_staged_attempt(self, success):
        if self.current_phase != "staged_drops" or self.staged_programming or not self.staged_target:
            return
        target = self.staged_target
        self.staged_target = None
        if success:
            self.staged_successes += 1
            self._score(self.STAGED_TARGET_VALUE)
            self._show_message("TARGET HIT", f"{self.STAGED_TARGET_VALUE:,}")
        else:
            self._show_message("MISSED", "RUBBER HIT")
        self.delay.reset(
            name="final_showdown_staged_next",
            ms=500,
            callback=self._start_next_staged_target,
        )

    # ------------------------------------------------------------------
    # Shared web-target collect for timed/staged phases
    # ------------------------------------------------------------------
    def _start_web_collect(self, kind, value):
        self.web_collect_kind = kind
        self.web_collect_value = max(0, int(value))
        self._set("final_showdown_jackpot_ready", 1)
        self._set("final_showdown_jackpot_value", self.web_collect_value)
        self.machine.events.post("final_showdown_web_jackpot_on")
        title = "SUPER JACKPOT" if kind == "timed_super" else "JACKPOT"
        self._show_message(title, "HIT EITHER WEB TARGET", value=self.web_collect_value, reminder=True)
        self._show_status(title, f"{self.web_collect_value:,}")
        self.delay.reset(
            name="final_showdown_web_collect_timeout",
            ms=self.WEB_COLLECT_MS,
            callback=self._web_collect_timeout,
        )

    def _collect_web_jackpot(self):
        if not self.web_collect_kind:
            return False
        kind = self.web_collect_kind
        value = self.web_collect_value
        self._clear_web_collect()
        self._award_jackpot(value, super_jackpot=(kind == "timed_super"))
        self._finish_phase()
        return True

    def _web_collect_timeout(self):
        if not self.web_collect_kind:
            return
        kind = self.web_collect_kind
        self._clear_web_collect()
        if kind == "timed_super":
            self._show_message("SUPER JACKPOT MISSED", "PHASE COMPLETE")
        else:
            self._show_message("JACKPOT MISSED", "PHASE COMPLETE")
        self._finish_phase()

    def _clear_web_collect(self):
        self.delay.remove("final_showdown_web_collect_timeout")
        self.machine.events.post("final_showdown_web_jackpot_off")
        self.web_collect_kind = None
        self.web_collect_value = 0
        self._set("final_showdown_jackpot_ready", 0)
        self._set("final_showdown_jackpot_value", 0)

    # ------------------------------------------------------------------
    # Phase 3: rooftop 20-flip build
    # ------------------------------------------------------------------
    def _start_rooftop_phase(self):
        self.roof_visit_active = False
        self.roof_flips_remaining = self.ROOFTOP_FLIPS
        self.roof_spinner_spins = 0
        self.roof_target_hits = {"left": 0, "center": 0, "right": 0}
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("final_showdown_rooftop_on")
        self._show_message("ROOFTOP BUILD", "GET TO THE ROOF - 20 FLIPS", reminder=True)
        self._update_rooftop_status()

    def _upper_entrance(self, **kwargs):
        if self.current_phase == "rooftop":
            self.roof_visit_active = True
            self.roof_flips_remaining = self.ROOFTOP_FLIPS
            self.machine.events.post("cmd_upper_flippers_enable")
            self._show_message("ROOFTOP BUILD", "SPINNER BUILDS - TARGETS MULTIPLY")
            self._update_rooftop_status()
            return

        if self.current_phase == "area_control" and self._all_lower_areas_complete() and not self.area_roof_active:
            self.area_roof_active = True
            self.area_roof_target_hit = False
            self.area_spinner_spins = 0
            self.machine.events.post("cmd_upper_flippers_enable")
            self.delay.reset(
                name="final_showdown_area_roof_timeout",
                ms=self.AREA_ROOF_MS,
                callback=self._area_roof_timeout,
            )
            self._show_message("ROOFTOP AREA", "HIT ANY UPPER TARGET", reminder=True)
            self._update_area_status()

    def _upper_flipper(self, **kwargs):
        if self.current_phase != "rooftop" or not self.roof_visit_active:
            return
        if self.roof_flips_remaining <= 0:
            return
        self.roof_flips_remaining -= 1
        if self.roof_flips_remaining <= 0:
            self.roof_flips_remaining = 0
            self.machine.events.post("cmd_upper_flippers_disable")
            self._show_message("20 FLIPS USED", "EXIT TO COLLECT")
        self._update_rooftop_status()

    def _upper_spinner(self, **kwargs):
        self._timed_hit("upper_spinner")
        if self.current_phase == "rooftop" and self.roof_visit_active and self.roof_flips_remaining > 0:
            self.roof_spinner_spins += 1
            self._update_rooftop_status()
        elif self.current_phase == "area_control" and self.area_roof_active and self.area_roof_target_hit:
            self.area_spinner_spins += 1
            self._score(self.AREA_SPINNER_VALUE)
            self._update_area_status()

    def _upper_target(self, target=None, **kwargs):
        self._timed_hit("upper_targets")
        if self.current_phase == "rooftop" and self.roof_visit_active and self.roof_flips_remaining > 0:
            if target in self.roof_target_hits:
                self.roof_target_hits[target] += 1
                self._update_rooftop_status()
            return
        if self.current_phase == "area_control" and self.area_roof_active and not self.area_roof_target_hit:
            self.area_roof_target_hit = True
            self.machine.events.post("final_showdown_area_roof_target_complete")
            self._show_message("5TH AREA CONTROLLED", "UPPER SPINNER 100K PER SPIN")
            self._update_area_status()

    def _roof_exit(self, exit_name=None, **kwargs):
        if self.current_phase != "rooftop" or not self.roof_visit_active:
            return
        if exit_name not in ("left", "right"):
            return
        self._collect_rooftop_exit(exit_name)

    def _center_exit_proxy(self, **kwargs):
        if self.current_phase != "rooftop" or not self.roof_visit_active:
            return
        self._collect_rooftop_exit("center")

    def _collect_rooftop_exit(self, exit_name):
        if not self.roof_visit_active:
            return
        self.roof_visit_active = False
        value = self._rooftop_exit_value(exit_name)
        self.machine.events.post("cmd_upper_flippers_enable")
        self.machine.events.post("rooftop_diverter_close")
        if value <= 0:
            self._show_message("ROOFTOP JACKPOT MISSED", "NO SPINNER VALUE BUILT")
            self._finish_phase()
            return
        self._award_jackpot(value)
        self._finish_phase()

    def _rooftop_exit_value(self, exit_name):
        base = self.roof_spinner_spins * self.ROOFTOP_SPIN_VALUE
        multiplier = self.roof_target_hits.get(exit_name, 0) + 1
        return base * multiplier

    def _update_rooftop_status(self):
        left = self._rooftop_exit_value("left")
        center = self._rooftop_exit_value("center")
        right = self._rooftop_exit_value("right")
        self._show_status(
            f"ROOF - {self.roof_flips_remaining} FLIPS",
            f"L {left:,}  C {center:,}  R {right:,}",
        )

    # ------------------------------------------------------------------
    # Phase 4: area control
    # ------------------------------------------------------------------
    @staticmethod
    def _new_area_state():
        return {
            "left_bank": False,
            "left_web": False,
            "right_bank": False,
            "right_rubber": False,
            "left_pop": False,
            "right_pop": False,
            "center_web": False,
            "left_sling": False,
            "right_sling": False,
        }

    def _start_area_control_phase(self):
        self.area_lower = self._new_area_state()
        self.area_roof_active = False
        self.area_roof_target_hit = False
        self.area_spinner_spins = 0
        self._reset_drop_banks()
        self.machine.events.post("final_showdown_area_control_on")
        self._refresh_area_lights()
        self.delay.reset(
            name="final_showdown_area_lower_timeout",
            ms=self.AREA_LOWER_MS,
            callback=self._area_lower_timeout,
        )
        self._show_message("AREA CONTROL", "25 SECONDS - CONTROL 4 LOWER AREAS", reminder=True)
        self._update_area_status()

    def _mark_area_item(self, item):
        if self.current_phase != "area_control" or self.area_roof_active:
            return
        if item in self.area_lower:
            self.area_lower[item] = True
        self._refresh_area_lights()
        self._update_area_status()
        if self._all_lower_areas_complete():
            self.delay.remove("final_showdown_area_lower_timeout")
            self.machine.events.post("rooftop_diverter_open")
            self._show_message("LOWER AREAS CONTROLLED", "ENTER THE ROOFTOP", reminder=True)

    def _lower_area_results(self):
        return {
            "left": self.area_lower["left_bank"] and self.area_lower["left_web"],
            "right": self.area_lower["right_bank"] and self.area_lower["right_rubber"],
            "center": (
                self.area_lower["left_pop"]
                and self.area_lower["right_pop"]
                and self.area_lower["center_web"]
            ),
            "slings": self.area_lower["left_sling"] and self.area_lower["right_sling"],
        }

    def _all_lower_areas_complete(self):
        return all(self._lower_area_results().values())

    def _refresh_area_lights(self):
        results = self._lower_area_results()
        for area, complete in results.items():
            self.machine.events.post(
                f"final_showdown_area_{area}_{'complete' if complete else 'needed'}"
            )

    def _update_area_status(self):
        if self.area_roof_active:
            if self.area_roof_target_hit:
                self._show_status("ROOFTOP CONTROLLED", f"SPINS {self.area_spinner_spins}  {self.area_spinner_spins * self.AREA_SPINNER_VALUE:,}")
            else:
                self._show_status("ROOFTOP AREA", "HIT ANY UPPER TARGET")
            return
        complete = sum(1 for value in self._lower_area_results().values() if value)
        self._show_status("AREA CONTROL", f"LOWER AREAS {complete}/4")

    def _area_lower_timeout(self):
        if self.current_phase != "area_control" or self.area_roof_active:
            return
        self._show_message("AREA CONTROL INCOMPLETE", "25 SECONDS EXPIRED")
        self._finish_phase()

    def _area_roof_timeout(self):
        if self.current_phase != "area_control" or not self.area_roof_active:
            return
        self.machine.events.post("cmd_upper_flippers_disable")
        self.machine.events.post("rooftop_diverter_close")
        if not self.area_roof_target_hit:
            self._show_message("ROOFTOP AREA INCOMPLETE", "TARGET NOT HIT")
            self._finish_phase()
            return
        self._show_message("ROOFTOP TIME", f"{self.area_spinner_spins * self.AREA_SPINNER_VALUE:,} COLLECTED")
        self._finish_phase()

    # ------------------------------------------------------------------
    # Phase 5: reveal / collect
    # ------------------------------------------------------------------
    def _start_reveal_phase(self):
        self.reveal_count = 0
        self.reveal_collect_started = False
        self.reveal_collect_value = 0
        self.reveal_lit_positions = set()
        self._reset_drop_banks()
        self._refresh_reveal_lights()
        self._show_message("REVEAL & COLLECT", "COMPLETE BANKS - FLIPPERS MOVE SAUCERS", reminder=True)
        self._update_reveal_status()

    def _reveal_saucer(self):
        if self.current_phase != "reveal" or self.reveal_collect_started or self.reveal_count >= 3:
            return
        self.reveal_count += 1
        unlit = [position for position in range(3) if position not in self.reveal_lit_positions]
        if unlit:
            self.reveal_lit_positions.add(unlit[0])
        self._refresh_reveal_lights()
        self._update_reveal_status()
        self._show_message("SAUCER REVEALED", f"{self.reveal_count} OF 3")

    def _rotate_reveal(self, direction):
        if self.current_phase != "reveal" or not self.reveal_lit_positions:
            return
        self.reveal_lit_positions = {(position + direction) % 3 for position in self.reveal_lit_positions}
        self._refresh_reveal_lights()

    def _refresh_reveal_lights(self):
        for position in range(3):
            self.machine.events.post(
                f"final_showdown_reveal_saucer_{position + 1}_{'on' if position in self.reveal_lit_positions else 'off'}"
            )

    def _collect_reveal_saucer(self, saucer):
        position = saucer - 1
        if position not in self.reveal_lit_positions:
            return False
        if not self.reveal_collect_started:
            self.reveal_collect_started = True
            self.reveal_collect_value = self.REVEAL_SAUCER_VALUES.get(self.reveal_count, 0)
        self.reveal_lit_positions.discard(position)
        self._award_jackpot(self.reveal_collect_value)
        self._refresh_reveal_lights()
        self._update_reveal_status()
        self._eject_saucer(
            saucer,
            delay_ms=self.REVEAL_EJECT_MS,
            owner="reveal",
            expected_phase="reveal",
        )
        if not self.reveal_lit_positions:
            # Do not leave Reveal before its final jackpot ball has actually
            # been released. Otherwise the delayed eject can land in the next
            # recap phase and kick a newly parked ball.
            self.delay.reset(
                name="final_showdown_reveal_finish",
                ms=self.REVEAL_EJECT_MS + self.REVEAL_FINISH_AFTER_EJECT_MS,
                callback=self._finish_phase,
            )
        return True

    def _update_reveal_status(self):
        if self.reveal_collect_started:
            self._show_status(
                "COLLECT SAUCERS",
                f"{len(self.reveal_lit_positions)} LEFT  {self.reveal_collect_value:,} EACH",
            )
        else:
            value = self.REVEAL_SAUCER_VALUES.get(self.reveal_count, 0)
            self._show_status("REVEAL SAUCERS", f"REVEALED {self.reveal_count}/3  VALUE {value:,}")

    # ------------------------------------------------------------------
    # Final Kingpin lock phase
    # ------------------------------------------------------------------
    def _start_final_lock(self):
        if self.mode_exiting:
            return
        self._invalidate_all_saucer_ejects()
        self.current_phase = "final_lock"
        self.machine.events.post("final_showdown_parking_saucers_off")
        self.locked_saucers.clear()
        self.final_gate_ready = False
        self.final_shot_active = False
        for saucer in (1, 2, 3):
            switch = self.machine.switches.get(f"s_saucer_{saucer}")
            if switch and self.machine.switch_controller.is_active(switch):
                self._cancel_saucer_hold(saucer)
                self.locked_saucers.add(saucer)
                self.machine.events.post("final_showdown_final_saucer_locked", saucer=f"saucer_{saucer}")
        self._set("final_showdown_current_area", "final_lock")
        self._set("final_showdown_current_area_display", self.PHASE_NAMES["final_lock"])
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("final_showdown_final_lock_started")
        self._show_message("KINGPIN", "LOCK 3 SAUCERS", value=self.kingpin_bank, reminder=True)
        self._check_final_lock_state()

    def _lock_saucer(self, saucer):
        if saucer in self.locked_saucers:
            return
        self._cancel_saucer_hold(saucer)
        self.locked_saucers.add(saucer)
        self.machine.events.post("final_showdown_final_saucer_locked", saucer=f"saucer_{saucer}")
        self._check_final_lock_state()

    def _check_final_lock_state(self):
        if self.current_phase != "final_lock" or self.mode_exiting:
            return

        # Once Kingpin is exposed, the final shot is its own state. The gate
        # remains open while the three lock balls are released back into play,
        # and normal multiball-end handling is intentionally ignored.
        if self.final_shot_active:
            self._update_final_lock_status()
            return

        free_balls = self._balls_in_play() - len(self.locked_saucers)

        if len(self.locked_saucers) >= 3 and free_balls > 0:
            self._begin_final_shot()
            return

        if self.final_gate_ready:
            self.final_gate_ready = False
            self.machine.events.post("rooftop_diverter_close")
            self.machine.events.post("final_showdown_kingpin_vuk_off")

        # Never leave every physical ball parked before Kingpin is exposed. If
        # there is no free ball and an add-a-ball is not already on its way,
        # release one lock so the player can continue building the final state.
        if free_balls <= 0 and self.locked_saucers and not self.pending_add_a_ball:
            self._release_one_final_lock()
            return

        self._update_final_lock_status()

    def _begin_final_shot(self):
        if self.final_shot_active or self.mode_exiting:
            return
        self.final_shot_active = True
        self.final_gate_ready = True
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("final_showdown_kingpin_vuk_on")
        self._update_final_shot_ball_save()
        self._show_message("KINGPIN EXPOSED", "SHOOT DAILY BUGLE", value=self.kingpin_bank, reminder=True)

        # Release the three locked balls one at a time, two seconds apart. The
        # first release is immediate; the final shot remains live throughout.
        for index, saucer in enumerate(sorted(self.locked_saucers)):
            if index == 0:
                self._release_final_shot_ball(saucer)
            else:
                self.delay.reset(
                    name=f"final_showdown_final_release_{index}",
                    ms=index * 2000,
                    callback=self._release_final_shot_ball,
                    saucer=saucer,
                )
        self._update_final_lock_status()

    def _release_final_shot_ball(self, saucer):
        if self.mode_exiting or not self.final_shot_active:
            return
        if saucer not in self.locked_saucers:
            return
        self.locked_saucers.discard(saucer)
        self.machine.events.post("final_showdown_final_saucer_released", saucer=f"saucer_{saucer}")
        self._eject_saucer(saucer)
        self._update_final_lock_status()

    def _release_one_final_lock(self):
        if not self.locked_saucers:
            return
        saucer = sorted(self.locked_saucers)[-1]
        self.locked_saucers.discard(saucer)
        self.final_gate_ready = False
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("final_showdown_kingpin_vuk_off")
        self.machine.events.post("final_showdown_final_saucer_released", saucer=f"saucer_{saucer}")
        self._eject_saucer(saucer)
        self._update_final_lock_status()

    def _update_final_lock_status(self):
        if self.final_shot_active or self.final_gate_ready:
            self._show_status("KINGPIN EXPOSED", f"FINAL SHOT {self.kingpin_bank:,}")
        else:
            self._show_status("LOCK SAUCERS", f"{len(self.locked_saucers)}/3  KINGPIN BANK {self.kingpin_bank:,}")

    def _ball_drain(self, **kwargs):
        if self.current_phase != "final_lock" or self.mode_exiting:
            return
        if self.final_shot_active:
            # During the final VUK shot the dedicated only-last-ball save owns
            # survival. Do not use the normal multiball-ended result here.
            self._update_final_shot_ball_save()
            return
        self.delay.reset(
            name="final_showdown_final_drain_check",
            ms=150,
            callback=self._check_final_lock_state,
        )

    def _ball_will_end(self, **kwargs):
        del kwargs
        if self.mode_exiting:
            return

        # Reaching ball_will_end means there are no physical balls left in
        # play. Merely dropping from multiball to one ball is allowed and is
        # handled by ignoring multiball_ended below. Before Kingpin is exposed,
        # exhausting that last live ball ends the Final Showdown attempt.
        if not self.final_shot_active:
            self._fail_showdown("KINGPIN GETS AWAY", "ALL BALLS LOST")
            return

        # During the final VUK shot, the dedicated only-last-ball save may buy
        # another attempt by consuming a future game ball. If ball_will_end is
        # reached anyway, no such retry was available.
        self._fail_showdown("KINGPIN GETS AWAY", "FINAL BALL LOST")

    def _remaining_game_balls(self):
        game = self.machine.game
        if not game or not game.player:
            return 0
        player = game.player
        try:
            current_ball = int(player["ball"])
        except (KeyError, TypeError, ValueError):
            current_ball = 0
        try:
            extra_balls = max(0, int(player["extra_balls"]))
        except (KeyError, TypeError, ValueError):
            extra_balls = 0
        try:
            balls_per_game = max(0, int(game.balls_per_game))
        except (TypeError, ValueError):
            balls_per_game = 0
        normal_remaining = max(0, balls_per_game - current_ball)
        return normal_remaining + extra_balls

    def _consume_one_remaining_game_ball(self):
        game = self.machine.game
        if not game or not game.player:
            return False
        player = game.player
        try:
            current_ball = int(player["ball"])
        except (KeyError, TypeError, ValueError):
            current_ball = 0
        try:
            balls_per_game = max(0, int(game.balls_per_game))
        except (TypeError, ValueError):
            balls_per_game = 0

        # Consume the next normal ball first. Because MPF's ball save keeps the
        # same physical ball turn alive, advancing this player variable is what
        # prevents that future normal ball from being served again later.
        if balls_per_game > 0 and current_ball < balls_per_game:
            player["ball"] = current_ball + 1
            return True

        try:
            extra_balls = max(0, int(player["extra_balls"]))
        except (KeyError, TypeError, ValueError):
            extra_balls = 0
        if extra_balls > 0:
            player["extra_balls"] = extra_balls - 1
            return True
        return False

    def _update_final_shot_ball_save(self):
        if self.mode_exiting or not self.final_shot_active:
            self.machine.events.post("final_showdown_disable_final_shot_save")
            return
        if self._remaining_game_balls() > 0:
            self.machine.events.post("final_showdown_enable_final_shot_save")
        else:
            self.machine.events.post("final_showdown_disable_final_shot_save")

    def _final_shot_ball_saved(self, **kwargs):
        del kwargs
        if self.mode_exiting or not self.final_shot_active:
            return
        if not self._consume_one_remaining_game_ball():
            # Defensive guard. The save should have been disabled before this
            # point if no future game ball was available.
            self.machine.events.post("final_showdown_disable_final_shot_save")
            return
        remaining = self._remaining_game_balls()
        self.machine.events.post(
            "final_showdown_final_shot_retry", remaining_balls=remaining
        )
        self._show_message(
            "KINGPIN STILL ESCAPING",
            "FINAL SHOT - SHOOT DAILY BUGLE",
            value=self.kingpin_bank,
            reminder=True,
        )
        self._update_final_shot_ball_save()

    # ------------------------------------------------------------------
    # Shared switch handlers
    # ------------------------------------------------------------------
    def _main_spinner(self, **kwargs):
        if self.mode_exiting:
            return
        self._advance_next_phase()
        self._timed_hit("spinner")

    def _web_target(self, shot=None, **kwargs):
        if self.mode_exiting:
            return
        if self.web_collect_kind and self.current_phase in ("timed", "staged_drops"):
            self._collect_web_jackpot()
            return
        self._timed_hit(shot)
        if self.current_phase == "area_control":
            if shot == "left_web":
                self._mark_area_item("left_web")
            elif shot == "center_web":
                self._mark_area_item("center_web")

    def _pop(self, side=None, **kwargs):
        if self.mode_exiting:
            return
        self._timed_hit(f"{side}_pop")
        if self.current_phase == "area_control" and side in ("left", "right"):
            self._mark_area_item(f"{side}_pop")

    def _sling(self, side=None, **kwargs):
        if self.current_phase == "area_control" and side in ("left", "right"):
            self._mark_area_item(f"{side}_sling")

    def _bank_rubber(self, bank=None, **kwargs):
        if self.mode_exiting:
            return
        self._timed_hit(f"{bank}_bank")
        if self.current_phase == "staged_drops" and not self.staged_programming and self.staged_target:
            if self.staged_target.startswith(f"{bank}_"):
                self._resolve_staged_attempt(False)
                return
        if self.current_phase == "area_control" and bank == "right":
            self._mark_area_item("right_rubber")

    def _drop_target(self, target=None, **kwargs):
        if self.mode_exiting or not target:
            return
        bank = target.split("_", 1)[0]
        self._timed_hit(f"{bank}_bank")

        if self.current_phase == "staged_drops":
            if self.staged_programming:
                return
            if target == self.staged_target:
                self._resolve_staged_attempt(True)
            return

        if self.current_phase == "reveal":
            self._score(self.REVEAL_DROP_VALUE)

    def _bank_complete(self, bank=None, **kwargs):
        if self.mode_exiting or bank not in ("left", "right"):
            return
        if self.current_phase == "staged_drops":
            return
        if self.current_phase == "area_control":
            self._mark_area_item(f"{bank}_bank")
            self.machine.events.post(f"drop_target_bank_dt_bank_{bank}_reset")
            return
        if self.current_phase == "reveal":
            self._reveal_saucer()
            self.machine.events.post(f"drop_target_bank_dt_bank_{bank}_reset")
            return
        # Timed and all other phases retain normal bank reset behavior.
        self.machine.events.post(f"drop_target_bank_dt_bank_{bank}_reset")

    def _left_flipper(self, **kwargs):
        if self.current_phase == "reveal":
            self._rotate_reveal(-1)

    def _right_flipper(self, **kwargs):
        if self.current_phase == "reveal":
            self._rotate_reveal(1)

    def _saucer_hit(self, saucer=None, **kwargs):
        if self.mode_exiting or saucer not in (1, 2, 3):
            return

        # A fresh saucer switch means this occupancy is new/current. Any
        # delayed eject that was scheduled for an older occupancy must not be
        # allowed to fire against this ball.
        self._invalidate_saucer_eject(saucer)
        self.machine.events.post("cancel_pending_saucer_ejects")
        self._collect_add_a_ball_if_ready()

        if self.current_phase == "final_lock":
            if self.final_shot_active:
                # Once Kingpin is exposed, saucers no longer relock balls. Keep
                # all surviving balls moving while the player shoots the VUK.
                self._eject_saucer(saucer, delay_ms=250)
            else:
                self._lock_saucer(saucer)
            return

        if self.current_phase == "reveal" and self._collect_reveal_saucer(saucer):
            return

        self._park_saucer(saucer)

    def _park_saucer(self, saucer):
        if saucer in self.held_saucers:
            return

        # Always allow the first ball to park. Only enforce the last-free-ball
        # guard after at least one ball is already parked. This avoids a false
        # quick eject if MPF briefly reports balls_in_play=1 while another ball
        # is still physically loose on the playfield.
        if self.held_saucers and self._balls_in_play() - len(self.held_saucers) <= 1:
            self._eject_saucer(saucer, delay_ms=250)
            return

        self.held_saucers.add(saucer)
        self.machine.events.post("final_showdown_parking_saucer_unavailable", saucer=f"saucer_{saucer}")
        self.machine.events.post("final_showdown_saucer_hold_started", saucer=f"saucer_{saucer}")
        self.delay.reset(
            name=f"final_showdown_saucer_{saucer}_hold",
            ms=self.SAUCER_HOLD_MS,
            callback=self._release_parked_saucer,
            saucer=saucer,
        )

    def _release_parked_saucer(self, saucer):
        if saucer not in self.held_saucers:
            return
        self.held_saucers.discard(saucer)
        self.machine.events.post("final_showdown_saucer_released", saucer=f"saucer_{saucer}")
        if self.current_phase in ("timed", "staged_drops", "rooftop", "area_control"):
            self.machine.events.post("final_showdown_parking_saucer_available", saucer=f"saucer_{saucer}")
        self._eject_saucer(saucer)

    def _cancel_saucer_hold(self, saucer):
        self.delay.remove(f"final_showdown_saucer_{saucer}_hold")
        self.held_saucers.discard(saucer)

    def _invalidate_saucer_eject(self, saucer):
        if saucer not in self._saucer_eject_generation:
            return
        self._saucer_eject_generation[saucer] += 1
        self.delay.remove(f"final_showdown_saucer_{saucer}_eject")

    def _invalidate_all_saucer_ejects(self):
        for saucer in (1, 2, 3):
            self._invalidate_saucer_eject(saucer)

    def _post_owned_saucer_eject(self, saucer, generation, owner, expected_phase):
        if self.mode_exiting:
            return
        if generation != self._saucer_eject_generation.get(saucer):
            self.log.debug(
                "Ignoring stale Final Showdown saucer %s eject owner=%s generation=%s",
                saucer, owner, generation,
            )
            return
        if expected_phase is not None and self.current_phase != expected_phase:
            self.log.debug(
                "Ignoring Final Showdown saucer %s eject owner=%s: phase changed %s -> %s",
                saucer, owner, expected_phase, self.current_phase,
            )
            return
        event = self.SAUCER_EJECT_EVENTS.get(saucer)
        if event:
            self.machine.events.post(event)

    def _eject_saucer(self, saucer, delay_ms=0, owner="final_showdown", expected_phase=None):
        event = self.SAUCER_EJECT_EVENTS.get(saucer)
        if not event:
            return

        # Supersede any older Kingpin eject for this saucer before scheduling
        # the new one. Shared villain_progression remains only the physical
        # executor of the explicit request.
        self._invalidate_saucer_eject(saucer)
        generation = self._saucer_eject_generation[saucer]

        if delay_ms:
            if expected_phase is None:
                expected_phase = self.current_phase
            self.delay.reset(
                name=f"final_showdown_saucer_{saucer}_eject",
                ms=delay_ms,
                callback=self._post_owned_saucer_eject,
                saucer=saucer,
                generation=generation,
                owner=owner,
                expected_phase=expected_phase,
            )
        else:
            self.machine.events.post(event)

    def _release_all_saucers(self, **kwargs):
        self._invalidate_all_saucer_ejects()

        # Clear Kingpin's logical hold/lock state first. A ball can enter a
        # saucer during the victory hold after mode_exiting is set, so that
        # physical occupancy may never be added to either tracking set.
        for saucer in list(self.held_saucers):
            self._cancel_saucer_hold(saucer)
            self.machine.events.post("final_showdown_saucer_released", saucer=f"saucer_{saucer}")
        self.held_saucers.clear()

        for saucer in list(self.locked_saucers):
            self.machine.events.post("final_showdown_final_saucer_released", saucer=f"saucer_{saucer}")
        self.locked_saucers.clear()

        # Trust the physical switches at cleanup. Eject every actually occupied
        # saucer, including balls that arrived after the winning VUK shot.
        for saucer in (1, 2, 3):
            switch = self.machine.switches.get(f"s_saucer_{saucer}")
            if switch and self.machine.switch_controller.is_active(switch):
                self._eject_saucer(saucer)

    def _vuk_hit(self, **kwargs):
        if self.mode_exiting:
            return
        if self.current_phase == "final_lock" and self.final_shot_active:
            self._defeat_kingpin()
            return
        self.machine.events.post("request_vuk_eject")

    # ------------------------------------------------------------------
    # Completion / defeat
    # ------------------------------------------------------------------
    def _defeat_kingpin(self):
        if self.mode_exiting:
            return

        # The winning VUK shot is a deliberate victory hold. Keep the physical
        # ball trapped while the finale/message plays, disable the flippers so
        # any remaining multiball balls can drain naturally, and only release
        # the VUK / start the summary after the hold has finished.
        self.mode_exiting = True
        final_value = self.kingpin_bank
        self._score(final_value)

        self.machine.events.post("final_showdown_disable_final_shot_save")
        self.machine.events.post("final_showdown_stop_all_multiballs")
        self.machine.events.post("final_showdown_kingpin_vuk_off")
        self.machine.events.post("cmd_flippers_disable")
        self.machine.events.post("cmd_upper_flippers_disable")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post(
            "final_showdown_victory_hold_started",
            value=final_value,
            duration_ms=self.FINAL_VICTORY_HOLD_MS,
        )
        self.machine.events.post("final_showdown_kingpin_defeated", value=final_value)
        self._show_message("KINGPIN DEFEATED", f"{final_value:,}", reminder=True)

        self.delay.reset(
            name="final_showdown_victory_hold",
            ms=self.FINAL_VICTORY_HOLD_MS,
            callback=self._finish_kingpin_victory_hold,
            final_value=final_value,
        )

    def _finish_kingpin_victory_hold(self, final_value=0):
        # Keep every flipper disabled through the handoff. Clear any balls that
        # are still trapped in Kingpin-owned saucers, then release the winning
        # VUK ball and continue into the completion/summary flow.
        self.machine.events.post("cmd_flippers_disable")
        self.machine.events.post("cmd_upper_flippers_disable")
        self.machine.events.post("cancel_mode_message_reminder")
        self._release_all_saucers()
        self.machine.events.post("final_showdown_victory_hold_finished", value=int(final_value))
        self.machine.events.post("request_vuk_eject")
        self.machine.events.post("final_showdown_mode_complete")

    def _fail_showdown(self, title="KINGPIN GETS AWAY", subtitle="FINAL SHOWDOWN LOST"):
        if self.mode_exiting:
            return
        self.mode_exiting = True
        if self.current_phase in self.PHASES:
            self._cleanup_phase(self.current_phase)
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self._release_all_saucers()
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("final_showdown_kingpin_vuk_off")
        self.machine.events.post("final_showdown_disable_final_shot_save")
        self.machine.events.post("final_showdown_stop_all_multiballs")
        self._show_message(title, subtitle)
        self.machine.events.post("final_showdown_mode_failed")

    def _test_last_ball_lost(self, **kwargs):
        del kwargs
        if self.mode_exiting:
            return
        # In test mode the harness saves the physical last ball so the test
        # session can continue. Treat that saved drain as a real exhausted
        # Final Showdown attempt; otherwise recap play can loop forever.
        self._fail_showdown("KINGPIN GETS AWAY", "ALL BALLS LOST")

    def _multiball_ended(self, **kwargs):
        del kwargs
        if self.mode_exiting:
            return

        # MPF reports multiball ended when play drops to one ball. Final
        # Showdown deliberately continues on that last ball. The attempt only
        # fails when ball_will_end confirms that every live ball has actually
        # drained. Once Kingpin is exposed, this same rule lets the final VUK
        # shot continue down to one ball while its conditional save owns any
        # future-ball retries.
        return

    # ------------------------------------------------------------------
    # Scoring / display helpers
    # ------------------------------------------------------------------
    def _award_jackpot(self, value, super_jackpot=False):
        value = max(0, int(value))
        self._score(value)
        self.kingpin_bank += value
        self._set("final_showdown_kingpin_bank", self.kingpin_bank)
        self._add("final_showdown_jackpots", 1)
        self._add("active_mode_major_hits", 1)
        if super_jackpot:
            self._add("final_showdown_super_jackpots", 1)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SUPER JACKPOT" if super_jackpot else "JACKPOT",
            message_mode_value=value,
        )
        self.machine.events.post("play_mode_super_jackpot" if super_jackpot else "play_mode_jackpot")
        self.machine.events.post("final_showdown_kingpin_bank_changed", value=self.kingpin_bank)

    def _score(self, points):
        points = max(0, int(points))
        player = self.machine.game.player if self.machine.game else None
        if not player or points <= 0:
            return
        player["score"] += points
        self._add("active_mode_points", points)

    def _show_message(self, title, subtitle="", value=None, reminder=False):
        payload = {
            "message_mode_title": str(title),
            "message_mode_subtitle": str(subtitle),
            "reminder": bool(reminder),
        }
        if value is not None:
            payload["message_mode_value"] = value
        self.machine.events.post("show_mode_message", **payload)

    def _show_status(self, title, value):
        if self.mode_exiting:
            return
        next_name = self.PHASE_NAMES.get(self.next_phase, "KINGPIN") if self.current_phase in self.PHASES else ""
        suffix = f"  NEXT {next_name}" if next_name else ""
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=str(title),
            mode_status_value=f"{value}{suffix}",
        )

    def _reset_drop_banks(self):
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return int(self.machine.game.balls_in_play)

    def _get(self, name, default=0):
        if name not in self.PERSISTENT_VARS:
            return self._runtime_state.get(name, default)
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return default
        try:
            return player[name]
        except KeyError:
            return default

    def _set(self, name, value):
        if name not in self.PERSISTENT_VARS:
            self._runtime_state[name] = value
            return
        player = self.machine.game.player if self.machine.game else None
        if player:
            player[name] = value

    def _add(self, name, value):
        self._set(name, self._get(name) + value)
