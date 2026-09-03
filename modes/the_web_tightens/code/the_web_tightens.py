import random
import time

from mpf.core.mode import Mode


class TheWebTightens(Mode):
    """Chapter 5 wizard: repeating five-phase VUK-lock multiball.

    Flow:
    - Start 2-ball multiball and lock one ball in the Daily Bugle VUK.
    - A saucer starts each villain-inspired phase and parks excess balls while
      always leaving at least one playable loose ball.
    - Successful phase shots score the shared wizard jackpot plus Chapter Case
      File prep. Each successful phase adds 1M to that cycle's Super Jackpot.
    - After all five phases, release the VUK ball and open the roof for one
      Super Jackpot attempt. Locking another ball in the VUK begins a new cycle.
    - The wizard ends when the multiball drops to one ball in play.
    """

    MODE_KEY = "the_web_tightens"
    DISPLAY_NAME = "THE WEB TIGHTENS"

    BASE_JACKPOT = 100_000
    SUPER_PER_SUCCESS = 1_000_000
    PHASES = ("fiddler", "metal", "conquistador", "spider_slayer", "harley")

    FIDDLER_SHOTS = ("left_web", "left_bank", "right_pop", "right_bank")
    FIDDLER_LABELS = {
        "left_web": "LEFT WEB",
        "left_bank": "LEFT BANK",
        "right_pop": "RIGHT POP",
        "right_bank": "RIGHT BANK",
    }
    FIDDLER_NOTES = {
        "left_web": "play_note_1",
        "left_bank": "play_note_2",
        "right_pop": "play_note_3",
        "right_bank": "play_note_4",
    }
    FIDDLER_FLASH_MS = 700
    FIDDLER_GAP_MS = 180
    FIDDLER_REPEATS = 2
    FIDDLER_INPUT_DEBOUNCE_SECONDS = 0.750

    METAL_ATTACK_INTERVAL_MS = 5_000
    METAL_RETALIATION_INTERVAL_MS = 2_000
    METAL_ZONE_TIMER_MS = 12_000
    METAL_SAVES_TO_WIN = 4
    METAL_DESTROYED_TO_LOSE = 3

    CONQUISTADOR_SPINS_REQUIRED = 3
    CONQUISTADOR_WEB_TIMER_MS = 14_000

    SLAYER_REQUIRED_HITS = 7
    SLAYER_SHOT_TIMER_MS = 8_000
    SLAYER_SHOTS = (
        "left_web", "center_web", "left_sling", "right_sling",
        "left_pop", "right_pop", "left_bank", "right_bank",
        "star", "saucer",
    )

    HARLEY_ZONES_REQUIRED = 4
    HARLEY_STAR_TIMER_MS = 14_000

    # Existing six-zone playfield map from Fifth Dimension Curse. Reused here
    # for both Metal-Eating Monster and Harley & Clivendon phases.
    ZONE_SWITCHES = {
        "upper_left": {
            "s_leaf_next_to_1", "s_saucer_1", "s_saucer_2", "s_saucer_3",
            "s_upper_entrance_opto", "s_upper_exit_left_opto",
        },
        "upper_right": {
            "s_above_star", "s_inlane_a", "s_inlane_b", "s_star_rollover",
            "s_trispinner_opto", "s_upper_exit_right_opto", "s_upper_target_left",
            "s_upper_target_center", "s_upper_target_right", "s_web_target_mid",
        },
        "middle_left": {
            "s_above_spinner", "s_inlane_m_l", "s_left_drops_1", "s_left_drops_2",
            "s_left_drops_3", "s_left_drops_rubber", "s_left_drops_top_left_rubber",
            "s_left_drops_top_right_rubber", "s_pop_left", "s_web_spinner",
            "s_web_target_left",
        },
        "middle_right": {
            "s_inlane_m_r", "s_mid_right_rubber", "s_pop_right", "s_right_drops_1",
            "s_right_drops_2", "s_right_drops_3", "s_right_drops_4", "s_right_drops_5",
            "s_right_drops_rubber", "s_right_drops_top_rubber",
        },
        "lower_left": {"s_inlane_l", "s_outlane_l", "s_sling_l"},
        "lower_right": {"s_inlane_r", "s_outlane_r", "s_sling_r"},
    }
    ZONE_LABELS = {
        "upper_left": "UPPER LEFT",
        "upper_right": "UPPER RIGHT",
        "middle_left": "MIDDLE LEFT",
        "middle_right": "MIDDLE RIGHT",
        "lower_left": "LOWER LEFT",
        "lower_right": "LOWER RIGHT",
    }

    FIDDLER_SWITCH_TO_SHOT = {
        "s_web_target_left": "left_web",
        "s_left_drops_1": "left_bank",
        "s_left_drops_2": "left_bank",
        "s_left_drops_3": "left_bank",
        "s_left_drops_rubber": "left_bank",
        "s_left_drops_top_left_rubber": "left_bank",
        "s_left_drops_top_right_rubber": "left_bank",
        "s_pop_right": "right_pop",
        "s_right_drops_1": "right_bank",
        "s_right_drops_2": "right_bank",
        "s_right_drops_3": "right_bank",
        "s_right_drops_4": "right_bank",
        "s_right_drops_5": "right_bank",
        "s_right_drops_rubber": "right_bank",
        "s_right_drops_top_rubber": "right_bank",
    }

    SLAYER_SWITCH_TO_SHOT = {
        "s_web_target_left": "left_web",
        "s_web_target_mid": "center_web",
        "s_sling_l": "left_sling",
        "s_sling_r": "right_sling",
        "s_pop_left": "left_pop",
        "s_pop_right": "right_pop",
        "s_left_drops_1": "left_bank",
        "s_left_drops_2": "left_bank",
        "s_left_drops_3": "left_bank",
        "s_left_drops_rubber": "left_bank",
        "s_left_drops_top_left_rubber": "left_bank",
        "s_left_drops_top_right_rubber": "left_bank",
        "s_right_drops_1": "right_bank",
        "s_right_drops_2": "right_bank",
        "s_right_drops_3": "right_bank",
        "s_right_drops_4": "right_bank",
        "s_right_drops_5": "right_bank",
        "s_right_drops_rubber": "right_bank",
        "s_right_drops_top_rubber": "right_bank",
        "s_star_rollover": "star",
        "s_saucer_1": "saucer",
        "s_saucer_2": "saucer",
        "s_saucer_3": "saucer",
    }

    # The rooftop Super is a grouped shot: any of the three upper targets
    # collects the same Super Jackpot.
    SUPER_SWITCHES = {
        "s_upper_target_left",
        "s_upper_target_center",
        "s_upper_target_right",
    }

    PHASE_ANNOUNCE_MS = 2_000
    SUPER_GATE_RETRY_MS = 250
    SUPER_VUK_EJECT_DELAY_MS = 750
    SUPER_SAUCER_FIRST_RELEASE_AFTER_VUK_MS = 6_000
    SUPER_SAUCER_STAGGER_MS = 2_000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_done = False
        self.multiball_active = False
        self.mode_points = 0
        self.total_phase_successes = 0
        self.supers_collected = 0

        self.vuk_locked = False
        self.summary_holds_vuk = False
        self.waiting_for_vuk = True
        self.waiting_for_saucer = False
        self.phase_announcing = False
        self.transitioning = False
        self.phase = None
        self.phase_index = 0
        self.cycle_number = 0
        self.cycle_successes = 0
        self.super_available = False
        self.super_collected = False
        self.vuk_relock_lockout_until = 0.0
        self.held_saucers = set()
        self.saucer_lockout_until = 0.0

        self.fiddler_sequence = []
        self.fiddler_expected_index = 0
        self.fiddler_demonstrating = False
        self.fiddler_demo_repeat = 0
        self.fiddler_demo_index = 0
        self._fiddler_last_switch_hit_time = {}

        self.metal_saved = set()
        self.metal_destroyed = set()
        self.metal_attacked = set()

        self.conquistador_step = "bank"
        self.conquistador_spins = 0

        self.slayer_active = set()
        self.slayer_hits = 0
        self.slayer_success_locked = False

        self.harley_completed = set()
        self.harley_star_ready = False

        player = self.machine.game.player
        self.case_file_bonus = int(player["mini_wizard_case_file_bonus"] or 0)
        self.jackpot_value = self.BASE_JACKPOT + self.case_file_bonus
        player["mini_wizard_current_key"] = self.MODE_KEY
        player["mini_wizard_vuk_hold_active"] = 0
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_stat_1"] = 0
        player["active_mode_stat_2"] = 0

        all_switches = set(self.FIDDLER_SWITCH_TO_SHOT)
        all_switches.update(self.SLAYER_SWITCH_TO_SHOT)
        all_switches.update(self.SUPER_SWITCHES)
        all_switches.update({"s_web_spinner", "s_vuk_switch"})
        for switches in self.ZONE_SWITCHES.values():
            all_switches.update(switches)
        for switch in sorted(all_switches):
            self.add_mode_event_handler(f"{switch}_active", self._switch_hit, switch=switch)

        self.add_mode_event_handler(
            "multiball_the_web_tightens_multiball_started",
            self._multiball_started,
        )
        self.add_mode_event_handler(
            "multiball_the_web_tightens_multiball_ended",
            self._multiball_ended,
        )
        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._complete_mode)

        # The Web Tightens owns the rooftop gate. Keep it closed during the
        # VUK lock and all five villain phases, and allow it open only for the
        # earned rooftop Super Jackpot window. Reject legacy open requests too.
        self.add_mode_event_handler("rooftop_diverter_open", self._enforce_gate_state)
        self.add_mode_event_handler("open_rooftop_gate", self._enforce_gate_state)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("the_web_tightens_clear_all")
        self.machine.events.post("the_web_tightens_base_lighting")
        self.machine.events.post("the_web_tightens_vuk_lock_ready")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title=self.DISPLAY_NAME,
            message_mode_subtitle="LOCK A BALL AT DAILY BUGLE",
            message_mode_value=self.jackpot_value,
        )
        self.machine.events.post("the_web_tightens_start_multiball")
        self._update_status()
        self._schedule_ball_guard()

    def mode_stop(self, **kwargs):
        self.delay.clear()
        self._release_all_saucers(delay_step_ms=0)
        self.machine.events.post("the_web_tightens_clear_all")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")

        player = self.machine.game.player if self.machine.game else None
        if player:
            player["mini_wizard_vuk_hold_active"] = 0
            if player["mini_wizard_current_key"] == self.MODE_KEY:
                player["mini_wizard_current_key"] = ""

        if self.vuk_locked and not self.summary_holds_vuk:
            self.machine.events.post("request_vuk_eject", delay_ms=0)
        self.vuk_locked = False

        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        super().mode_stop(**kwargs)

    # ------------------------------------------------------------------
    # Shared switch / ball routing
    # ------------------------------------------------------------------

    def _switch_hit(self, switch=None, **kwargs):
        if self.mode_done or not switch:
            return

        if switch == "s_vuk_switch":
            self._vuk_hit()
            return

        if switch in ("s_saucer_1", "s_saucer_2", "s_saucer_3"):
            saucer = int(switch[-1])
            self._saucer_hit(saucer, switch)
            return

        if self.phase == "fiddler":
            shot = self.FIDDLER_SWITCH_TO_SHOT.get(switch)
            if shot:
                # Debounce the physical switch, not the logical note shot.
                # This means two different drops in the same bank may still
                # register back-to-back, while a bounce/re-hit from one switch
                # within 750ms is ignored.
                now = time.monotonic()
                last = self._fiddler_last_switch_hit_time.get(switch)
                if last is not None and (now - last) < self.FIDDLER_INPUT_DEBOUNCE_SECONDS:
                    return
                self._fiddler_last_switch_hit_time[switch] = now
                self._fiddler_shot_hit(shot)
            return

        if self.phase == "metal":
            zone = self._zone_for_switch(switch)
            if zone:
                self._metal_zone_hit(zone)
            return

        if self.phase == "conquistador":
            self._conquistador_switch(switch)
            return

        if self.phase == "spider_slayer":
            shot = self.SLAYER_SWITCH_TO_SHOT.get(switch)
            if shot:
                self._slayer_shot_hit(shot)
            return

        if self.phase == "harley":
            star_was_ready = self.harley_star_ready
            zone = self._zone_for_switch(switch)
            if zone:
                self._harley_zone_hit(zone)
            # The same star hit that completes the fourth zone must not also
            # collect the newly lit 2X jackpot. Require a subsequent star hit.
            if switch == "s_star_rollover" and star_was_ready:
                self._harley_star_hit()
            return

        if self.phase == "super" and switch in self.SUPER_SWITCHES:
            self._super_hit(switch)

    def _enforce_gate_state(self, **kwargs):
        """Reject outside gate-open requests except during the earned Super window."""
        if self.mode_done:
            return
        if self.phase == "super" and self.super_available and not self.super_collected:
            return
        self.machine.events.post("rooftop_diverter_close")

    def _vuk_hit(self):
        if self.mode_done:
            return

        # Ignore switch chatter from the deliberate VUK release that opens the
        # rooftop Super window. A genuinely new VUK entry after the ball has
        # cleared the device may start the next cycle.
        if time.monotonic() < self.vuk_relock_lockout_until:
            return

        if self.vuk_locked:
            self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
            self.machine.events.post("cancel_vuk_eject_request")
            return

        if self.waiting_for_vuk or self.phase == "super":
            self._lock_vuk_for_cycle()
            return

        self.machine.events.post("request_vuk_eject", delay_ms=750)

    def _lock_vuk_for_cycle(self):
        self.vuk_locked = True
        self.waiting_for_vuk = False
        self.waiting_for_saucer = True
        self.transitioning = False
        self.phase = None
        self.phase_index = 0
        self.cycle_number += 1
        self.cycle_successes = 0
        self.super_available = False
        self.super_collected = False

        player = self.machine.game.player
        player["mini_wizard_vuk_hold_active"] = 1
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.machine.events.post("cancel_vuk_eject_request")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("the_web_tightens_clear_all")
        self.machine.events.post("the_web_tightens_base_lighting")
        self.machine.events.post("the_web_tightens_vuk_locked")
        self.machine.events.post("the_web_tightens_saucers_ready")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="BALL LOCKED",
            message_mode_subtitle="SHOOT A SAUCER - FIDDLER",
            message_mode_value=self.jackpot_value,
        )
        self._sync_vars()
        self._update_status()

    def _saucer_hit(self, saucer, switch):
        if self.mode_done:
            return

        now = time.monotonic()
        if now < self.saucer_lockout_until:
            self._eject_saucer(saucer, 250)
            return

        if not self.vuk_locked or self.phase == "super" or self.waiting_for_vuk:
            self._eject_saucer(saucer, 500)
            return

        if saucer in self.held_saucers:
            return

        if self.waiting_for_saucer and not self.transitioning:
            self.held_saucers.add(saucer)
            self.waiting_for_saucer = False
            self._announce_phase(self.phase_index)
            return

        if self.transitioning or self.phase is None:
            self._eject_saucer(saucer, 500)
            return

        # During an active phase the saucer hit may itself be a valid zone or
        # Slayer shot. Score it first, then park/eject the physical ball.
        if self.phase in ("metal", "harley"):
            zone = self._zone_for_switch(switch)
            if zone:
                if self.phase == "metal":
                    self._metal_zone_hit(zone)
                else:
                    self._harley_zone_hit(zone)
        elif self.phase == "spider_slayer":
            self._slayer_shot_hit("saucer")

        if self.transitioning:
            self._eject_saucer(saucer, 500)
            return
        self._park_or_eject_saucer(saucer)

    def _park_or_eject_saucer(self, saucer):
        self.held_saucers.add(saucer)
        if self._playable_loose_balls() <= 0 and not self.fiddler_demonstrating:
            self.held_saucers.discard(saucer)
            self._eject_saucer(saucer, 250)
            return
        self.machine.events.post("the_web_tightens_ball_parked", saucer=saucer)

    def _eject_saucer(self, saucer, delay_ms=0):
        self.machine.events.post(
            "request_saucer_eject",
            saucer_number=saucer,
            delay_ms=delay_ms,
        )

    def _release_one_saucer(self):
        if not self.held_saucers:
            return False
        saucer = sorted(self.held_saucers)[0]
        self.held_saucers.remove(saucer)
        self._eject_saucer(saucer, 0)
        return True

    def _release_all_saucers(self, delay_step_ms=200, initial_delay_ms=0):
        held = sorted(self.held_saucers)
        self.held_saucers.clear()
        for index, saucer in enumerate(held):
            delay_ms = initial_delay_ms + (index * delay_step_ms)
            self._eject_saucer(saucer, delay_ms)
        if held:
            last_delay_ms = initial_delay_ms + ((len(held) - 1) * delay_step_ms)
            self.saucer_lockout_until = time.monotonic() + (last_delay_ms / 1000.0) + 1.5

    def _schedule_ball_guard(self):
        if self.mode_done:
            return
        self.delay.reset(
            name="the_web_tightens_ball_guard",
            ms=250,
            callback=self._ball_guard,
        )

    def _ball_guard(self):
        if self.mode_done:
            return
        if self.multiball_active and self._balls_in_play() <= 1:
            self._complete_mode()
            return
        if (
            self.phase not in (None, "super")
            and not self.transitioning
            and not self.fiddler_demonstrating
            and self.held_saucers
            and self._playable_loose_balls() <= 0
        ):
            self._release_one_saucer()
        self._schedule_ball_guard()

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return int(self.machine.game.balls_in_play or 0)

    def _playable_loose_balls(self):
        held = len(self.held_saucers)
        vuk = 1 if self.vuk_locked else 0
        return max(0, self._balls_in_play() - held - vuk)

    # ------------------------------------------------------------------
    # Phase control
    # ------------------------------------------------------------------

    def _announce_phase(self, index):
        if self.mode_done or index < 0 or index >= len(self.PHASES):
            return
        self.phase_announcing = True
        self.transitioning = True
        self.machine.events.post("the_web_tightens_saucers_not_ready")
        phase_name = self.PHASES[index].replace("_", " ").upper()
        if phase_name == "METAL":
            phase_name = "METAL-EATING MONSTER"
        elif phase_name == "SPIDER SLAYER":
            phase_name = "SPIDER-SLAYER"
        elif phase_name == "HARLEY":
            phase_name = "HARLEY & CLIVENDON"
        self.machine.events.post("hide_mode_message")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=phase_name,
            message_mode_subtitle="GET READY",
        )
        self.delay.reset(
            name="web_phase_announce",
            ms=self.PHASE_ANNOUNCE_MS,
            callback=self._start_announced_phase,
            index=index,
        )
        self._update_status()

    def _start_announced_phase(self, index=None):
        if self.mode_done or index is None:
            return
        self.phase_announcing = False
        self.transitioning = False
        self._start_phase(index)

    def _start_phase(self, index):
        if self.mode_done or index < 0 or index >= len(self.PHASES):
            return
        self._clear_phase_delays()
        self.machine.events.post("hide_mode_message")
        self.machine.events.post("the_web_tightens_saucers_not_ready")
        self.machine.events.post("the_web_tightens_clear_phase_lights")
        self.machine.events.post("the_web_tightens_base_lighting")
        self.phase = self.PHASES[index]
        self.transitioning = False

        if self.phase == "fiddler":
            self._start_fiddler()
        elif self.phase == "metal":
            self._start_metal()
        elif self.phase == "conquistador":
            self._start_conquistador()
        elif self.phase == "spider_slayer":
            self._start_slayer()
        elif self.phase == "harley":
            self._start_harley()
        self._update_status()

    def _resolve_phase(self, success, title, subtitle=""):
        if self.mode_done or self.transitioning or self.phase in (None, "super"):
            return

        resolved_phase = self.phase
        self.transitioning = True
        self._clear_phase_delays()
        self.machine.events.post("hide_mode_message")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("the_web_tightens_clear_phase_lights")
        self.machine.events.post("the_web_tightens_base_lighting")
        if success:
            self.cycle_successes += 1
            self.total_phase_successes += 1
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title=title,
                message_mode_subtitle=subtitle or "PHASE COMPLETE",
                message_mode_value=self.cycle_successes * self.SUPER_PER_SUCCESS,
            )
        else:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title=title,
                message_mode_subtitle=subtitle or "PHASE FAILED",
            )

        self.machine.events.post(
            "the_web_tightens_phase_resolved",
            phase=resolved_phase,
            success=1 if success else 0,
            cycle_successes=self.cycle_successes,
        )
        self.phase = None
        self.phase_index += 1
        self._sync_vars()
        if self.phase_index < len(self.PHASES):
            self._release_all_saucers(delay_step_ms=200)
        self.delay.reset(
            name="the_web_tightens_phase_transition",
            ms=1_200,
            callback=self._finish_phase_transition,
        )

    def _finish_phase_transition(self):
        if self.mode_done:
            return
        self.transitioning = False
        if self.phase_index >= len(self.PHASES):
            self._begin_super_round()
            return
        self.waiting_for_saucer = True
        next_name = self.PHASES[self.phase_index].replace("_", " ").upper()
        self.machine.events.post("the_web_tightens_saucers_ready")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="NEXT PHASE READY",
            message_mode_subtitle=f"SHOOT A SAUCER - {next_name}",
            message_mode_value=self.jackpot_value,
        )
        self._update_status()

    def _clear_phase_delays(self):
        for name in (
            "web_fiddler_flash", "web_fiddler_gap", "web_fiddler_repeat",
            "web_metal_next_attack", "web_conquistador_web_timeout",
            "web_harley_star_timeout", "web_add_ball_guard", "web_phase_announce",
            "web_super_gate_retry",
        ):
            self.delay.remove(name)
        for zone in self.ZONE_SWITCHES:
            self.delay.remove(f"web_metal_{zone}_expire")
        for shot in self.SLAYER_SHOTS:
            self.delay.remove(f"web_slayer_{shot}_expire")

    # ------------------------------------------------------------------
    # Fiddler phase
    # ------------------------------------------------------------------

    def _start_fiddler(self):
        self.fiddler_sequence = [random.choice(self.FIDDLER_SHOTS) for _ in range(2)]
        self.fiddler_expected_index = 0
        self.fiddler_demonstrating = True
        self.fiddler_demo_repeat = 0
        self.fiddler_demo_index = 0
        self.machine.events.post("the_web_tightens_fiddler_all_off")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="FIDDLER",
            message_mode_subtitle="WATCH - TWO NOTES",
        )
        self._fiddler_demo_next()

    def _fiddler_demo_next(self):
        if self.mode_done or self.phase != "fiddler" or not self.fiddler_demonstrating:
            return
        if self.fiddler_demo_index >= len(self.fiddler_sequence):
            self.fiddler_demo_repeat += 1
            if self.fiddler_demo_repeat >= self.FIDDLER_REPEATS:
                self._finish_fiddler_demo()
                return
            self.fiddler_demo_index = 0
            self.delay.reset(
                name="web_fiddler_repeat", ms=500, callback=self._fiddler_demo_next
            )
            return

        shot = self.fiddler_sequence[self.fiddler_demo_index]
        self.machine.events.post(self.FIDDLER_NOTES[shot])
        self.machine.events.post(f"the_web_tightens_fiddler_{shot}_on")
        self.delay.reset(
            name="web_fiddler_flash",
            ms=self.FIDDLER_FLASH_MS,
            callback=self._fiddler_demo_note_off,
            shot=shot,
        )

    def _fiddler_demo_note_off(self, shot=None):
        if shot:
            self.machine.events.post(f"the_web_tightens_fiddler_{shot}_off")
        self.fiddler_demo_index += 1
        self.delay.reset(
            name="web_fiddler_gap",
            ms=self.FIDDLER_GAP_MS,
            callback=self._fiddler_demo_next,
        )

    def _finish_fiddler_demo(self):
        self.fiddler_demonstrating = False
        self.machine.events.post("the_web_tightens_fiddler_all_off")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="FIDDLER - YOUR TURN",
            message_mode_subtitle="NOTE 1 OF 2",
        )
        if self._playable_loose_balls() <= 0:
            self._release_one_saucer()
        self._update_status()

    def _fiddler_shot_hit(self, shot):
        if self.fiddler_demonstrating or self.transitioning:
            return
        if self.fiddler_expected_index >= len(self.fiddler_sequence):
            return
        expected = self.fiddler_sequence[self.fiddler_expected_index]
        if shot != expected:
            self.machine.events.post("play_bad_note")
            self._resolve_phase(False, "FIDDLER FAILED", f"WANTED {self.FIDDLER_LABELS[expected]}")
            return

        value = self._jackpot(2)
        self.machine.events.post(self.FIDDLER_NOTES[shot])
        self._score(value)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="FIDDLER JACKPOT",
            message_mode_subtitle=self.FIDDLER_LABELS[shot],
            message_mode_value=value,
        )
        self.fiddler_expected_index += 1
        if self.fiddler_expected_index >= 2:
            self._resolve_phase(True, "FIDDLER COMPLETE", "TWO NOTES PLAYED")
        else:
            self.machine.events.post(
                "show_mode_message_long",
                message_mode_title="FIDDLER - YOUR TURN",
                message_mode_subtitle="NOTE 2 OF 2",
            )
            self._update_status()

    # ------------------------------------------------------------------
    # Metal-Eating Monster phase
    # ------------------------------------------------------------------

    def _start_metal(self):
        self.metal_saved.clear()
        self.metal_destroyed.clear()
        self.metal_attacked.clear()
        self.machine.events.post("the_web_tightens_add_a_ball")
        self.machine.events.post("the_web_tightens_metal_all_safe")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="METAL-EATING MONSTER",
            message_mode_subtitle="SAVE 4 ZONES - LOSE 3",
        )
        self.delay.reset(name="web_metal_next_attack", ms=500, callback=self._metal_start_attack)
        self.delay.reset(name="web_add_ball_guard", ms=1_000, callback=self._ensure_playable_ball)

    def _metal_start_attack(self):
        if self.mode_done or self.phase != "metal" or self.transitioning:
            return
        choices = self._metal_available_zones()
        if not choices:
            self._metal_check_end()
            return
        zone = random.choice(choices)
        self.metal_attacked.add(zone)
        self.machine.events.post(f"the_web_tightens_zone_{zone}_attack")
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title="ZONE UNDER ATTACK",
            message_mode_subtitle=self.ZONE_LABELS[zone],
            message_mode_seconds=self.METAL_ZONE_TIMER_MS // 1000,
        )
        self.delay.reset(
            name=f"web_metal_{zone}_expire",
            ms=self.METAL_ZONE_TIMER_MS,
            callback=self._metal_destroy_zone,
            zone=zone,
        )
        self.delay.reset(
            name="web_metal_next_attack",
            ms=self.METAL_ATTACK_INTERVAL_MS,
            callback=self._metal_start_attack,
        )
        self._update_status()

    def _metal_zone_hit(self, zone):
        if zone not in self.metal_attacked or self.transitioning:
            return
        self.delay.remove(f"web_metal_{zone}_expire")
        self.metal_attacked.remove(zone)
        self.metal_saved.add(zone)
        value = self._jackpot()
        self._score(value)
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post(f"the_web_tightens_zone_{zone}_saved")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="ZONE SAVED JACKPOT",
            message_mode_subtitle=self.ZONE_LABELS[zone],
            message_mode_value=value,
        )
        if len(self.metal_saved) >= self.METAL_SAVES_TO_WIN:
            self._resolve_phase(True, "METAL MONSTER STOPPED", "FOUR ZONES SAVED")
            return
        self.delay.reset(
            name="web_metal_next_attack",
            ms=self.METAL_RETALIATION_INTERVAL_MS,
            callback=self._metal_start_attack,
        )
        self._update_status()

    def _metal_destroy_zone(self, zone=None):
        if self.mode_done or self.phase != "metal" or zone not in self.metal_attacked:
            return
        self.metal_attacked.remove(zone)
        self.metal_destroyed.add(zone)
        self.machine.events.post(f"the_web_tightens_zone_{zone}_destroyed")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="ZONE DESTROYED",
            message_mode_subtitle=self.ZONE_LABELS[zone],
        )
        self._metal_check_end()
        self._update_status()

    def _metal_check_end(self):
        if len(self.metal_destroyed) >= self.METAL_DESTROYED_TO_LOSE:
            self._resolve_phase(False, "METAL MONSTER ESCAPES", "THREE ZONES DESTROYED")
            return
        if len(self.metal_saved) >= self.METAL_SAVES_TO_WIN:
            self._resolve_phase(True, "METAL MONSTER STOPPED", "FOUR ZONES SAVED")
            return
        if not self._metal_available_zones() and not self.metal_attacked:
            self._resolve_phase(False, "METAL MONSTER ESCAPES", "NOT ENOUGH ZONES SAVED")

    def _metal_available_zones(self):
        used = self.metal_saved | self.metal_destroyed | self.metal_attacked
        return [zone for zone in self.ZONE_SWITCHES if zone not in used]

    # ------------------------------------------------------------------
    # Conquistador phase
    # ------------------------------------------------------------------

    def _start_conquistador(self):
        self.conquistador_step = "bank"
        self.conquistador_spins = 0
        self.machine.events.post("the_web_tightens_conquistador_bank")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="THE CONQUISTADOR",
            message_mode_subtitle="HIT THE LEFT BANK",
            message_mode_value=self.jackpot_value,
        )
        self._ensure_playable_ball()

    def _conquistador_switch(self, switch):
        if self.transitioning:
            return
        if self.conquistador_step == "bank" and switch in {
            "s_left_drops_1", "s_left_drops_2", "s_left_drops_3"
        }:
            self._score_required_jackpot("CONQUISTADOR JACKPOT", "LEFT BANK")
            self.conquistador_step = "spinner"
            self.machine.events.post("the_web_tightens_conquistador_spinner")
            self.machine.events.post(
                "show_mode_message_long",
                message_mode_title="THE CONQUISTADOR",
                message_mode_subtitle="LOWER SPINNER - 3 SPINS",
            )
            self._update_status()
            return

        if self.conquistador_step == "spinner" and switch == "s_web_spinner":
            self.conquistador_spins += 1
            self._score_required_jackpot(
                "CONQUISTADOR JACKPOT",
                f"SPINNER {self.conquistador_spins} OF {self.CONQUISTADOR_SPINS_REQUIRED}",
            )
            if self.conquistador_spins >= self.CONQUISTADOR_SPINS_REQUIRED:
                self.conquistador_step = "web"
                self.machine.events.post("the_web_tightens_conquistador_web")
                self.machine.events.post(
                    "show_mode_countdown",
                    message_mode_title="FOUNTAIN FOUND",
                    message_mode_subtitle="CENTER WEB FOR JACKPOT",
                    message_mode_seconds=self.CONQUISTADOR_WEB_TIMER_MS // 1000,
                )
                self.delay.reset(
                    name="web_conquistador_web_timeout",
                    ms=self.CONQUISTADOR_WEB_TIMER_MS,
                    callback=self._conquistador_web_failed,
                )
            self._update_status()
            return

        if self.conquistador_step == "web" and switch == "s_web_target_mid":
            self.delay.remove("web_conquistador_web_timeout")
            self._score_required_jackpot("FOUNTAIN JACKPOT", "CENTER WEB")
            self._resolve_phase(True, "CONQUISTADOR COMPLETE", "FOUNTAIN FOUND")

    def _conquistador_web_failed(self):
        if self.phase == "conquistador" and self.conquistador_step == "web":
            self._resolve_phase(False, "CONQUISTADOR FAILED", "FOUNTAIN LOST")

    # ------------------------------------------------------------------
    # Spider-Slayer phase
    # ------------------------------------------------------------------

    def _start_slayer(self):
        self.slayer_active.clear()
        self.slayer_hits = 0
        self.slayer_success_locked = False
        self.machine.events.post("the_web_tightens_slayer_clear")
        self._slayer_add_random_shot()
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="SPIDER-SLAYER",
            message_mode_subtitle="MAKE 7 LIT SHOTS",
            message_mode_value=self.jackpot_value,
        )
        self._ensure_playable_ball()
        self._update_status()

    def _slayer_add_random_shot(self):
        choices = [shot for shot in self.SLAYER_SHOTS if shot not in self.slayer_active]
        if not choices:
            return
        shot = random.choice(choices)
        self.slayer_active.add(shot)
        self.machine.events.post(f"the_web_tightens_slayer_{shot}_on")
        self.delay.reset(
            name=f"web_slayer_{shot}_expire",
            ms=self.SLAYER_SHOT_TIMER_MS,
            callback=self._slayer_expire_shot,
            shot=shot,
        )

    def _slayer_shot_hit(self, shot):
        if shot not in self.slayer_active or self.transitioning:
            return
        value = self._jackpot()
        self._score(value)
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SLAYER JACKPOT",
            message_mode_subtitle=f"{min(self.slayer_hits + 1, self.SLAYER_REQUIRED_HITS)} OF {self.SLAYER_REQUIRED_HITS}",
            message_mode_value=value,
        )

        if not self.slayer_success_locked:
            self.slayer_hits += 1
            if self.slayer_hits >= self.SLAYER_REQUIRED_HITS:
                self.slayer_success_locked = True
                self.cycle_successes += 1
                self.total_phase_successes += 1
                self._sync_vars()
                self.machine.events.post(
                    "show_mode_jackpot",
                    message_mode_title="SPIDER-SLAYER COMPLETE",
                    message_mode_subtitle="LIT SHOTS WILL EXPIRE",
                    message_mode_value=self.cycle_successes * self.SUPER_PER_SUCCESS,
                )
            else:
                self._slayer_add_random_shot()
        self._update_status()

    def _slayer_expire_shot(self, shot=None):
        if self.mode_done or self.phase != "spider_slayer" or shot not in self.slayer_active:
            return
        self.slayer_active.remove(shot)
        self.machine.events.post(f"the_web_tightens_slayer_{shot}_off")
        if self.slayer_active:
            self._update_status()
            return

        if self.slayer_success_locked:
            # Success was already credited on hit 7; finish without double-counting.
            self._resolve_phase_already_credited(
                "SPIDER-SLAYER COMPLETE", "ALL LIT SHOTS EXPIRED"
            )
        else:
            self._resolve_phase(False, "SPIDER-SLAYER FAILED", "ALL LIT SHOTS EXPIRED")

    def _resolve_phase_already_credited(self, title, subtitle=""):
        if self.mode_done or self.transitioning or self.phase in (None, "super"):
            return
        resolved_phase = self.phase
        self.transitioning = True
        self._clear_phase_delays()
        self.machine.events.post("hide_mode_message")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("the_web_tightens_clear_phase_lights")
        self.machine.events.post("the_web_tightens_base_lighting")
        self.machine.events.post(
            "the_web_tightens_phase_resolved",
            phase=resolved_phase,
            success=1,
            cycle_successes=self.cycle_successes,
        )
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
        )
        self.phase = None
        self.phase_index += 1
        self._sync_vars()
        if self.phase_index < len(self.PHASES):
            self._release_all_saucers(delay_step_ms=200)
        self.delay.reset(
            name="the_web_tightens_phase_transition",
            ms=1_200,
            callback=self._finish_phase_transition,
        )

    # ------------------------------------------------------------------
    # Harley & Clivendon phase
    # ------------------------------------------------------------------

    def _start_harley(self):
        self.harley_completed.clear()
        self.harley_star_ready = False
        self.machine.events.post("the_web_tightens_add_a_ball")
        self.machine.events.post("the_web_tightens_harley_zones_reset")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="HARLEY & CLIVENDON",
            message_mode_subtitle="COMPLETE 4 OF 6 ZONES",
            message_mode_value=self.jackpot_value,
        )
        self.delay.reset(name="web_add_ball_guard", ms=1_000, callback=self._ensure_playable_ball)
        self._update_status()

    def _harley_zone_hit(self, zone):
        if self.harley_star_ready or zone in self.harley_completed or self.transitioning:
            return
        self.harley_completed.add(zone)
        value = self._jackpot()
        self._score(value)
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post(f"the_web_tightens_zone_{zone}_complete")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="HARLEY JACKPOT",
            message_mode_subtitle=f"{len(self.harley_completed)} OF {self.HARLEY_ZONES_REQUIRED} ZONES",
            message_mode_value=value,
        )
        if len(self.harley_completed) >= self.HARLEY_ZONES_REQUIRED:
            self.harley_star_ready = True
            self.machine.events.post("the_web_tightens_harley_star_ready")
            self.machine.events.post(
                "show_mode_countdown",
                message_mode_title="HARLEY JACKPOT READY",
                message_mode_subtitle="SHOOT THE STAR - 2X JP",
                message_mode_seconds=self.HARLEY_STAR_TIMER_MS // 1000,
            )
            self.delay.reset(
                name="web_harley_star_timeout",
                ms=self.HARLEY_STAR_TIMER_MS,
                callback=self._harley_star_failed,
            )
        self._update_status()

    def _harley_star_hit(self):
        if not self.harley_star_ready or self.transitioning:
            return
        self.delay.remove("web_harley_star_timeout")
        value = self._jackpot(2)
        self._score(value)
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="HARLEY 2X JACKPOT",
            message_mode_subtitle="STAR",
            message_mode_value=value,
        )
        self._resolve_phase(True, "HARLEY & CLIVENDON COMPLETE", "STAR COLLECTED")

    def _harley_star_failed(self):
        if self.phase == "harley" and self.harley_star_ready:
            self._resolve_phase(False, "HARLEY & CLIVENDON FAILED", "STAR EXPIRED")

    # ------------------------------------------------------------------
    # Super Jackpot / next cycle
    # ------------------------------------------------------------------

    def _begin_super_round(self):
        if self.mode_done:
            return
        self.phase = "super"
        self.waiting_for_saucer = False
        self.transitioning = False
        self.super_collected = False
        self.super_available = True

        self.machine.events.post("the_web_tightens_saucers_not_ready")
        self.machine.events.post("rooftop_diverter_open")
        self.delay.reset(
            name="web_super_gate_retry",
            ms=self.SUPER_GATE_RETRY_MS,
            callback=self._retry_super_gate_open,
        )

        if self.vuk_locked:
            self.vuk_locked = False
            self.machine.game.player["mini_wizard_vuk_hold_active"] = 0
            self.vuk_relock_lockout_until = time.monotonic() + 2.0
            self.machine.events.post(
                "request_vuk_eject",
                delay_ms=self.SUPER_VUK_EJECT_DELAY_MS,
            )

        # Keep parked balls out of the way while the gate opens and the VUK ball
        # is delivered to the roof. Release the first saucer ball six seconds
        # after the VUK kick, then stagger any additional balls by two seconds.
        self._release_all_saucers(
            delay_step_ms=self.SUPER_SAUCER_STAGGER_MS,
            initial_delay_ms=(
                self.SUPER_VUK_EJECT_DELAY_MS
                + self.SUPER_SAUCER_FIRST_RELEASE_AFTER_VUK_MS
            ),
        )

        self.machine.events.post("the_web_tightens_super_ready")
        self.delay.add(
            name="web_super_ready_message",
            ms=self.SUPER_VUK_EJECT_DELAY_MS,
            callback=self._show_super_ready_message,
        )
        self._sync_vars()
        self._update_status()

    def _retry_super_gate_open(self):
        if self.mode_done or self.phase != "super" or not self.super_available:
            return
        # Use the same high-level gate event. The global switch guard prevents
        # an unnecessary second coil pulse if the first open request succeeded.
        self.machine.events.post("rooftop_diverter_open")

    def _show_super_ready_message(self):
        if self.mode_done or not self.super_available or self.super_collected:
            return
        value = self.cycle_successes * self.SUPER_PER_SUCCESS
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="HIT ANY UPPER TARGET",
            message_mode_subtitle="FOR SUPER JACKPOT",
            message_mode_value=value,
        )

    def _super_hit(self, switch):
        if not self.super_available or self.super_collected or self.transitioning:
            return
        value = self.cycle_successes * self.SUPER_PER_SUCCESS
        self.super_collected = True
        self.super_available = False
        if value > 0:
            self.supers_collected += 1
            self._score(value)
        self.machine.events.post("play_mode_super_jackpot")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SUPER JACKPOT",
            message_mode_subtitle=f"{self.cycle_successes} OF 5 PHASES",
            message_mode_value=value,
        )
        self.machine.events.post("the_web_tightens_super_collected")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("the_web_tightens_vuk_lock_ready")
        self.waiting_for_vuk = True
        self._sync_vars()
        self._update_status()

    # ------------------------------------------------------------------
    # Helpers / scoring / status
    # ------------------------------------------------------------------

    def _zone_for_switch(self, switch):
        for zone, switches in self.ZONE_SWITCHES.items():
            if switch in switches:
                return zone
        return None

    def _ensure_playable_ball(self):
        if self.mode_done or self.phase in (None, "super") or self.fiddler_demonstrating:
            return
        if self.held_saucers and self._playable_loose_balls() <= 0:
            self._release_one_saucer()

    def _jackpot(self, multiplier=1):
        return int(multiplier) * (self.BASE_JACKPOT + self.case_file_bonus)

    def _score_required_jackpot(self, title, subtitle):
        value = self._jackpot()
        self._score(value)
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
        )

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.total_phase_successes
        player["active_mode_stat_1"] = self.total_phase_successes
        player["active_mode_stat_2"] = self.supers_collected

    def _update_status(self):
        if self.waiting_for_vuk:
            next_cycle = 1 if self.cycle_number == 0 else self.cycle_number + 1
            title = f"CYCLE {next_cycle}"
            value = "LOCK BALL AT DAILY BUGLE"
        elif self.phase_announcing:
            next_phase = self.PHASES[self.phase_index].replace("_", " ").upper()
            title = next_phase
            value = "GET READY"
        elif self.waiting_for_saucer:
            next_phase = self.PHASES[self.phase_index].replace("_", " ").upper()
            title = f"SUPER BUILD {self.cycle_successes}M"
            value = f"SAUCER -> {next_phase}"
        elif self.phase == "fiddler":
            title = "FIDDLER"
            value = "WATCH" if self.fiddler_demonstrating else f"NOTE {self.fiddler_expected_index + 1}/2"
        elif self.phase == "metal":
            title = f"METAL SAVE {len(self.metal_saved)}/4"
            value = f"DESTROYED {len(self.metal_destroyed)}/3"
        elif self.phase == "conquistador":
            if self.conquistador_step == "bank":
                value = "HIT LEFT BANK"
            elif self.conquistador_step == "spinner":
                value = f"LOWER SPINNER {self.conquistador_spins}/3"
            else:
                value = "CENTER WEB NOW"
            title = "CONQUISTADOR"
        elif self.phase == "spider_slayer":
            title = f"SLAYER {self.slayer_hits}/7"
            value = f"{len(self.slayer_active)} SHOTS LIT"
        elif self.phase == "harley":
            title = f"HARLEY {len(self.harley_completed)}/4"
            value = "SHOOT STAR" if self.harley_star_ready else "COMPLETE UNIQUE ZONES"
        elif self.phase == "super":
            title = f"SUPER JP {self.cycle_successes}M"
            value = "LOCK VUK FOR NEXT CYCLE" if self.super_collected else "SHOOT THE ROOFTOP"
        else:
            title = self.DISPLAY_NAME
            value = "MULTIBALL"
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _multiball_started(self, **kwargs):
        self.multiball_active = True

    def _multiball_ended(self, **kwargs):
        self.multiball_active = False
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._sync_vars()
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        player["mini_wizard_vuk_hold_active"] = 0

        if self.vuk_locked:
            self.summary_holds_vuk = True
            self.machine.events.post("villain_summary_hold_vuk_until_done")

        self.machine.events.post("the_web_tightens_mode_complete")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("stop_mode_the_web_tightens")
