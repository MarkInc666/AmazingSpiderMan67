from random import choice
from mpf.core.mode import Mode

"""
sinister_surge_area_changed
sinister_surge_area_complete
sinister_surge_jackpot_lit
sinister_surge_jackpot_collected
sinister_surge_ab_complete
sinister_surge_ab_reset
sinister_surge_super_jackpot_lit
sinister_surge_super_jackpot_collected
sinister_surge_victory_laps_started
sinister_surge_mode_complete
sinister_surge_mode_failed
sinister_surge_open_upper_gate
sinister_surge_close_upper_gate
sinister_surge_disable_daily_bugle_mystery
sinister_surge_enable_daily_bugle_mystery
"""
class SinisterSurge(Mode):

    """
    SINISTER SURGE: CHAPTER 1 CALLBACKS

    A+B Daily Bugle mystery disabled during wizard mode.

    Start 2-ball multiball with 20s ball save.

    One random unfinished Chapter 1 villain stage is active at a time:
    - Rhino: 6 pop hits
    - Sandman: hit the special right-bank drop; it moves every 4s
    - Vulture: 1 upper-target hit + 3 upper-spinner spins, any order
    - Electro: hit the lit web, then the other web within 20s
    - Green Goblin: park a ball in any saucer for 4s and hit 2 of 4
      flashing-green areas (left web, center web, left bank, right bank)

    Active area hits score 50K.
    Inactive area hits score 20K.

    Completing the active area lights Daily Bugle Jackpot at the VUK and opens the gate.
    Jackpot = 100K × (balls in play + cleared areas)

    Complete A+B before collecting Jackpot to add-a-ball on Jackpot collect.
    Max 5 balls in play.
    10 second ball save when ball added.
    A+B resets after each Jackpot.

    Saucers score 50K.
    If more than 1 ball is active, one saucer may hold one ball for 20s.
    Any additional saucer ejects normally while a ball is already parked.
    Green Goblin overrides the normal rest with its 4s attempt hold.
    If only 1 ball remains, saucers eject immediately.

    Upper gate opens when the Daily Bugle Jackpot is ready, when the Vulture
    stage is active, or when a Victory-Lap Super Jackpot is ready.

    After all city areas are cleared:
    Victory Laps begin.
    All areas are lit for 50K per hit.
    A+B opens gate and Daily Bugle Super Jackpot is lit for 1M × balls in play.

    Mode ends when only 1 ball remains.
    If a ball is held in a saucer when the mode ends, eject it.
    """

    ACTIVE_AREA_SCORE = 50_000
    INACTIVE_AREA_SCORE = 20_000
    SAUCER_SCORE = 50_000
    JACKPOT_BASE = 100_000
    SUPER_JACKPOT_BASE = 1_000_000
    SAUCER_HOLD_MS = 20_000
    GOBLIN_HOLD_MS = 4_000
    ELECTRO_SECOND_SHOT_MS = 20_000
    SANDMAN_MOVE_MS = 4_000
    SANDMAN_RESET_SETTLE_MS = 500
    MAX_BALLS = 5

    AREAS = {
        "rhino": {
            "display": "RHINO",
            "required": 6,
        },
        "sandman": {
            "display": "SANDMAN",
            "required": 1,
        },
        "vulture": {
            "display": "VULTURE",
            "required": 4,
        },
        "electro": {
            "display": "ELECTRO",
            "required": 2,
        },
        "goblin": {
            "display": "GREEN GOBLIN",
            "required": 2,
        },
    }

    SANDMAN_TARGETS = (1, 2, 3, 4, 5)
    ELECTRO_WEBS = ("left", "center")
    GOBLIN_AREAS = ("left_web", "center_web", "left_bank", "right_bank")

    SAUCER_EJECT_EVENTS = {
        "saucer_1": "delayed_kickout_saucer_1",
        "saucer_2": "delayed_kickout_saucer_2",
        "saucer_3": "delayed_kickout_saucer_3",
    }

    # Only values that must survive the gameplay mode belong on the player.
    # All other sinister_surge_* values are working state for this mode run.
    PERSISTENT_VARS = {
        "active_mode_points",
        "active_mode_hits",
        "active_mode_major_hits",
        "sinister_surge_state",
        "mini_wizard_case_file_bonus",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self._runtime_state = {}
        self.mode_exiting = False
        self.current_area = None
        self.jackpot_ready = False
        self.victory_laps = False
        self.super_jackpot_ready = False
        self.case_file_bonus = self._get("mini_wizard_case_file_bonus", 0)
        self.held_saucer = None
        self.sandman_current_target = None
        self.sandman_down_targets = set()
        self.vulture_target_hit = False
        self.vulture_spinner_hits = 0
        self.electro_first_web = None
        self.electro_target_web = None
        self.goblin_attempt_active = False
        self.goblin_qualified_areas = set()

        self._reset_player_vars()

        self._add_switch_handlers()
        self.add_mode_event_handler("sinister_surge_choose_first_area", self._choose_next_area)
        self.add_mode_event_handler("sinister_surge_multiball_ended", self._multiball_ended)

    def mode_stop(self, **kwargs):
        self.mode_exiting = True

        self._release_held_saucer()
        self._cancel_stage_timers()

        self.machine.events.post("sinister_surge_clear_all_sinister_surge_lights")
        self.machine.events.post("sinister_surge_close_upper_gate")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")

        super().mode_stop(**kwargs)

    def _add_switch_handlers(self):
        # A/B rollovers
        self.add_mode_event_handler("s_inlane_a_active", self._a_hit)
        self.add_mode_event_handler("s_inlane_m_r_active", self._a_hit)
        self.add_mode_event_handler("s_inlane_b_active", self._b_hit)
        self.add_mode_event_handler("s_inlane_m_l_active", self._b_hit)

        # Daily Bugle / VUK jackpot.
        # Use a mode-owned event instead of binding the switch directly so YAML
        # can also guarantee the VUK kicks even when the mode starts with a ball
        # already sitting on the VUK switch.
        self.add_mode_event_handler("sinister_surge_vuk_hit", self._daily_bugle_hit)

        # Chapter 1 callback shots.
        self.add_mode_event_handler("s_pop_left_active", self._pop_hit)
        self.add_mode_event_handler("s_pop_right_active", self._pop_hit)

        self.add_mode_event_handler("s_trispinner_opto_active", self._upper_spinner_hit)
        self.add_mode_event_handler("s_web_spinner_active", self._non_stage_hit)
        self.add_mode_event_handler("s_star_rollover_active", self._non_stage_hit)

        self.add_mode_event_handler("s_upper_target_left_active", self._upper_target_left_hit)
        self.add_mode_event_handler("s_upper_target_center_active", self._upper_target_center_hit)
        self.add_mode_event_handler("s_upper_target_right_active", self._upper_target_right_hit)

        self.add_mode_event_handler("s_web_target_left_active", self._left_web_hit)
        self.add_mode_event_handler("s_web_target_mid_active", self._center_web_hit)

        for target in self.SANDMAN_TARGETS:
            self.add_mode_event_handler(
                f"s_right_drops_{target}_active",
                self._right_drop_hit,
                target=target,
            )

        for target in (1, 2, 3):
            self.add_mode_event_handler(
                f"s_left_drops_{target}_active",
                self._left_drop_hit,
                target=target,
            )

        self.add_mode_event_handler("drop_target_bank_dt_bank_right_down", self._right_bank_down)

        # Saucers
        self.add_mode_event_handler("s_saucer_1_active", self._saucer_1_hit)
        self.add_mode_event_handler("s_saucer_2_active", self._saucer_2_hit)
        self.add_mode_event_handler("s_saucer_3_active", self._saucer_3_hit)

    def _reset_player_vars(self):
        self._set("active_mode_points", 0)
        self._set("active_mode_hits", 0)
        self._set("active_mode_major_hits", 0)
        self._set("sinister_surge_areas_cleared", 0)
        self._set("sinister_surge_jackpots", 0)
        self._set("sinister_surge_super_jackpots", 0)
        self._set("sinister_surge_state", 1)

        self._set("sinister_surge_current_area", "")
        self._set("sinister_surge_current_area_display", "")
        self._set("sinister_surge_area_progress", 0)
        self._set("sinister_surge_area_required", 0)

        self._set("sinister_surge_jackpot_ready", 0)
        self._set("sinister_surge_jackpot_value", 0)
        self._set("sinister_surge_super_jackpot_ready", 0)
        self._set("sinister_surge_super_jackpot_value", 0)

        self._set("sinister_surge_a_hit", 0)
        self._set("sinister_surge_b_hit", 0)
        self._set("sinister_surge_ab_ready", 0)

        for area in self.AREAS:
            self._set(f"sinister_surge_area_{area}_cleared", 0)

    def _choose_next_area(self, **kwargs):
        if self.victory_laps:
            return

        uncleared = [
            area for area in self.AREAS
            if not self._get_area_cleared(area)
        ]

        if not uncleared:
            self._start_victory_laps()
            return

        self.current_area = choice(uncleared)
        self.jackpot_ready = False
        self._cancel_stage_timers()

        area_data = self.AREAS[self.current_area]

        self._set("sinister_surge_current_area", self.current_area)
        self._set("sinister_surge_current_area_display", area_data["display"])
        self._set("sinister_surge_area_progress", 0)
        self._set("sinister_surge_area_required", area_data["required"])
        self._set("sinister_surge_hits_still_needed", area_data["required"])

        self._set("sinister_surge_jackpot_ready", 0)

        self._reset_area_specific_progress()

        self._update_gate()
        self.machine.events.post("sinister_surge_area_changed", area=self.current_area)
        self.machine.events.post("sinister_surge_clear_area_lights")
        self.machine.events.post(f"sinister_surge_area_{self.current_area}_lit")
        self._start_area_mechanic()
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=area_data["display"],
            message_mode_subtitle=self._area_instruction(),
            reminder=True,
        )
        self._update_area_status()

    def _reset_area_specific_progress(self):
        self.sandman_current_target = None
        self.sandman_down_targets.clear()
        self.vulture_target_hit = False
        self.vulture_spinner_hits = 0
        self.electro_first_web = None
        self.electro_target_web = None
        self.goblin_attempt_active = False
        self.goblin_qualified_areas.clear()

    def _start_area_mechanic(self):
        if self.current_area == "sandman":
            self.machine.events.post("drop_target_bank_dt_bank_right_reset")
            self.delay.add(
                name="sinister_surge_sandman_reset_settle",
                ms=self.SANDMAN_RESET_SETTLE_MS,
                callback=self._sandman_restart_after_reset,
            )
        elif self.current_area == "electro":
            self._start_electro_attempt()
        elif self.current_area == "goblin" and self.held_saucer is not None:
            # Goblin's 4-second capture replaces the normal 20-second rest.
            # Release a ball parked by the previous stage so the player can
            # make a fresh saucer shot to begin the Goblin attempt.
            self._release_held_saucer()

    def _area_instruction(self):
        instructions = {
            "rhino": "HIT POPS 6 TIMES",
            "sandman": "HIT THE FLASHING DROP",
            "vulture": "1 UPPER TARGET + 3 SPINS",
            "electro": "HIT THE LIT WEB",
            "goblin": "HIT A SAUCER",
        }
        return instructions.get(self.current_area, "COMPLETE STAGE")

    def _score(self, points):
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return

        player["score"] += points
        self._add("active_mode_points", points)        

    def _area_hit(self, area, amount=1):
        if self.victory_laps:
            self._victory_lap_hit()
            return

        if self.jackpot_ready:
            if area == self.current_area:
                self._score(self.ACTIVE_AREA_SCORE)
            else:
                self._score(self.INACTIVE_AREA_SCORE)
            return

        if area == self.current_area:
            self._score(self.ACTIVE_AREA_SCORE)
            self._add("sinister_surge_area_progress", amount)

            sinister_surge_hits_still_needed = self._get("sinister_surge_area_required") - self._get("sinister_surge_area_progress")

            self._set("sinister_surge_hits_still_needed", sinister_surge_hits_still_needed)
            self._update_area_status()
            self.machine.events.post("reset_mode_message_reminder")

            if sinister_surge_hits_still_needed > 0:
                self.machine.events.post("sinister_surge_area_changed", area=self.current_area)

            if self._get("sinister_surge_area_progress") >= self._get("sinister_surge_area_required"):
                self._area_complete()
        else:
            self._score(self.INACTIVE_AREA_SCORE)

    def _area_complete(self):
        if not self.current_area:
            return

        completed_area = self.current_area

        self._cancel_stage_timers()
        self.machine.events.post("sinister_surge_clear_stage_lights")

        if completed_area == "goblin" and self.held_saucer is not None:
            self._release_held_saucer()
        elif completed_area == "sandman":
            # Leave the physical bank clean after the callback ends.
            self.machine.events.post("drop_target_bank_dt_bank_right_reset")

        self._set_area_cleared(completed_area)
        self._add("sinister_surge_areas_cleared", 1)

        self.jackpot_ready = True
        self._set("sinister_surge_jackpot_ready", 1)
        self._update_jackpot_value()
        self._update_gate()

        self.machine.events.post("sinister_surge_area_complete", area=completed_area)
        self.machine.events.post("sinister_surge_jackpot_lit", area=completed_area)
        self.machine.events.post("sinister_surge_jackpot_lit_show")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="JACKPOT LIT",
            message_mode_subtitle="SHOOT DAILY BUGLE",
            message_mode_value=self._get("sinister_surge_jackpot_value"),
            reminder=True,
        )
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="STAGES CLEARED",
            mode_status_value=f"{self._get('sinister_surge_areas_cleared')} / {len(self.AREAS)}",
        )

    def _daily_bugle_hit(self, **kwargs):
        self.machine.events.post("request_vuk_eject", delay_ms=2_000)

        if self.victory_laps:
            self._collect_super_jackpot()
            return

        if not self.jackpot_ready:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        self._collect_jackpot()

    def _collect_jackpot(self):
        jackpot_value = self._update_jackpot_value()
        self._score(jackpot_value)
        self._add("sinister_surge_jackpots", 1)

        if self._get("sinister_surge_ab_ready") == 1 and self._balls_in_play() < self.MAX_BALLS:
            self.machine.events.post("sinister_surge_add_a_ball")

        self._reset_ab()
        self.jackpot_ready = False
        self._set("sinister_surge_jackpot_ready", 0)

        self.machine.events.post("sinister_surge_jackpot_collected", value=jackpot_value)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="JACKPOT",
            message_mode_subtitle=f"{self._get('sinister_surge_areas_cleared')} STAGES CLEARED",
            message_mode_value=jackpot_value,
        )

        self._choose_next_area()

    def _start_victory_laps(self):
        self.victory_laps = True
        self.current_area = "victory_laps"
        self.jackpot_ready = False
        self.super_jackpot_ready = False

        self._set("sinister_surge_state", 2)
        self._set("sinister_surge_current_area", "victory_laps")
        self._set("sinister_surge_current_area_display", "VICTORY LAPS")
        self._set("sinister_surge_jackpot_ready", 0)
        self._set("sinister_surge_super_jackpot_ready", 0)

        self._update_gate()
        self.machine.events.post("sinister_surge_victory_laps_started")
        self.machine.events.post("sinister_surge_victory_laps_show")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="VICTORY LAPS",
            message_mode_subtitle="COMPLETE A + B",
            reminder=True,
        )
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="SUPER JACKPOTS",
            mode_status_value=self._get("sinister_surge_super_jackpots"),
        )

    def _victory_lap_hit(self):
        self._score(self.ACTIVE_AREA_SCORE)

    def _collect_super_jackpot(self):
        if not self.super_jackpot_ready:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        value = (self.SUPER_JACKPOT_BASE * max(1, self._balls_in_play())) + self.case_file_bonus
        self._score(value)
        self._add("sinister_surge_super_jackpots", 1)

        self.super_jackpot_ready = False
        self._set("sinister_surge_super_jackpot_ready", 0)
        self._set("sinister_surge_super_jackpot_value", 0)
        self._reset_ab()
        self._update_gate()

        self.machine.events.post("sinister_surge_super_jackpot_collected", value=value)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SUPER JACKPOT",
            message_mode_value=value,
        )

    def _a_hit(self, **kwargs):
        self._set("sinister_surge_a_hit", 1)
        self._check_ab()

    def _b_hit(self, **kwargs):
        self._set("sinister_surge_b_hit", 1)
        self._check_ab()

    def _check_ab(self):
        if self._get("sinister_surge_a_hit") and self._get("sinister_surge_b_hit"):
            self._set("sinister_surge_ab_ready", 1)
            self.machine.events.post("sinister_surge_ab_complete")
            self.machine.events.post("sinister_surge_ab_ready_show")
            
            if self.victory_laps:
                self.super_jackpot_ready = True
                value = (self.SUPER_JACKPOT_BASE * max(1, self._balls_in_play())) + self.case_file_bonus
                self._set("sinister_surge_super_jackpot_ready", 1)
                self._set("sinister_surge_super_jackpot_value", value)
                self.machine.events.post("sinister_surge_super_jackpot_lit", value=value)
                self.machine.events.post("sinister_surge_super_jackpot_lit_show")
                self._update_gate()

    def _reset_ab(self):
        self._set("sinister_surge_a_hit", 0)
        self._set("sinister_surge_b_hit", 0)
        self._set("sinister_surge_ab_ready", 0)
        self.machine.events.post("sinister_surge_ab_reset")
        self.machine.events.post("sinister_surge_ab_clear_show")

    def _pop_hit(self, **kwargs):
        if self.current_area == "rhino" and not self.jackpot_ready:
            self._area_hit("rhino")
            return
        self._non_stage_hit()

    def _non_stage_hit(self, **kwargs):
        if self.victory_laps:
            self._victory_lap_hit()
        else:
            self._score(self.INACTIVE_AREA_SCORE)

    def _upper_spinner_hit(self, **kwargs):
        if self.victory_laps:
            self._victory_lap_hit()
            return
        if self.current_area != "vulture" or self.jackpot_ready:
            self._score(self.INACTIVE_AREA_SCORE)
            return
        if self.vulture_spinner_hits >= 3:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        self.vulture_spinner_hits += 1
        self._score(self.ACTIVE_AREA_SCORE)
        if self.vulture_spinner_hits >= 3:
            self.machine.events.post("sinister_surge_vulture_spinner_done")
        self._update_vulture_progress()

    def _upper_target_left_hit(self, **kwargs):
        self._upper_target_hit("left")

    def _upper_target_center_hit(self, **kwargs):
        self._upper_target_hit("center")

    def _upper_target_right_hit(self, **kwargs):
        self._upper_target_hit("right")

    def _upper_target_hit(self, target):
        if self.victory_laps:
            self._victory_lap_hit()
            return

        if self.current_area != "vulture" or self.jackpot_ready:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        if self.vulture_target_hit:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        self._score(self.ACTIVE_AREA_SCORE)
        self.vulture_target_hit = True
        self.machine.events.post("sinister_surge_vulture_target_done")
        self._update_vulture_progress()

    def _update_vulture_progress(self):
        progress = int(self.vulture_target_hit) + min(3, self.vulture_spinner_hits)
        self._set("sinister_surge_area_progress", progress)
        self._set("sinister_surge_hits_still_needed", max(0, 4 - progress))
        self.machine.events.post("reset_mode_message_reminder")
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="VULTURE",
            mode_status_value=(
                f"TARGET {int(self.vulture_target_hit)}/1  "
                f"SPINS {self.vulture_spinner_hits}/3"
            ),
        )

        if self.vulture_target_hit and self.vulture_spinner_hits >= 3:
            self._area_complete()

    def _sandman_restart_after_reset(self):
        if self.current_area != "sandman" or self.jackpot_ready or self.victory_laps:
            return
        self.sandman_down_targets.clear()
        self.sandman_current_target = 1
        self._light_sandman_target()
        self._schedule_sandman_shift()

    def _schedule_sandman_shift(self):
        self.delay.remove("sinister_surge_sandman_shift")
        self.delay.add(
            name="sinister_surge_sandman_shift",
            ms=self.SANDMAN_MOVE_MS,
            callback=self._sandman_shift,
        )

    def _sandman_shift(self):
        if self.current_area != "sandman" or self.jackpot_ready or self.victory_laps:
            return

        target = self.sandman_current_target
        if target is not None and target not in self.sandman_down_targets:
            self.sandman_down_targets.add(target)
            self.machine.coils[f"c_right_bank_drop_{target}"].pulse()

        next_target = self._next_sandman_standing_target(target)
        if next_target is None:
            self._reset_sandman_bank()
            return

        self.sandman_current_target = next_target
        self._light_sandman_target()
        self._schedule_sandman_shift()

    def _next_sandman_standing_target(self, current):
        start = current or 0
        for target in self.SANDMAN_TARGETS:
            if target > start and target not in self.sandman_down_targets:
                return target
        return None

    def _right_drop_hit(self, target, **kwargs):
        if self.victory_laps:
            self._victory_lap_hit()
            return

        if self.current_area == "goblin" and not self.jackpot_ready:
            self._goblin_area_hit("right_bank")
            return

        if self.current_area != "sandman" or self.jackpot_ready:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        # Timer-driven knockdowns are marked before their coil is pulsed, so
        # their switch transition cannot be mistaken for a player hit.
        if target in self.sandman_down_targets:
            return

        self.sandman_down_targets.add(target)
        if target == self.sandman_current_target:
            self.delay.remove("sinister_surge_sandman_shift")
            self._score(self.ACTIVE_AREA_SCORE)
            self._set("sinister_surge_area_progress", 1)
            self._set("sinister_surge_hits_still_needed", 0)
            self._area_complete()
            return

        self._score(self.INACTIVE_AREA_SCORE)
        if len(self.sandman_down_targets) >= len(self.SANDMAN_TARGETS):
            self._reset_sandman_bank()

    def _right_bank_down(self, **kwargs):
        if self.current_area == "sandman" and not self.jackpot_ready:
            self._reset_sandman_bank()

    def _reset_sandman_bank(self):
        self.delay.remove("sinister_surge_sandman_shift")
        self.machine.events.post("sinister_surge_sandman_clear")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.delay.remove("sinister_surge_sandman_reset_settle")
        self.delay.add(
            name="sinister_surge_sandman_reset_settle",
            ms=self.SANDMAN_RESET_SETTLE_MS,
            callback=self._sandman_restart_after_reset,
        )

    def _light_sandman_target(self):
        self.machine.events.post("sinister_surge_sandman_clear")
        if self.sandman_current_target is not None:
            self.machine.events.post(
                f"sinister_surge_sandman_target_{self.sandman_current_target}"
            )
            self.machine.events.post(
                "show_mode_status",
                mode_status_title="SANDMAN",
                mode_status_value=f"FLASH DROP {self.sandman_current_target}",
            )

    def _left_web_hit(self, **kwargs):
        self._web_hit("left")

    def _center_web_hit(self, **kwargs):
        self._web_hit("center")

    def _web_hit(self, web):
        if self.victory_laps:
            self._victory_lap_hit()
            return

        if self.current_area == "electro" and not self.jackpot_ready:
            self._electro_web_hit(web)
            return

        if self.current_area == "goblin" and not self.jackpot_ready:
            area = "left_web" if web == "left" else "center_web"
            self._goblin_area_hit(area)
            return

        self._score(self.INACTIVE_AREA_SCORE)

    def _start_electro_attempt(self):
        if self.current_area != "electro" or self.jackpot_ready:
            return
        self.delay.remove("sinister_surge_electro_second_shot")
        self.electro_first_web = None
        self.electro_target_web = choice(self.ELECTRO_WEBS)
        self._set("sinister_surge_area_progress", 0)
        self._set("sinister_surge_hits_still_needed", 2)
        self._light_electro_web()
        self._update_area_status()

    def _electro_web_hit(self, web):
        if web != self.electro_target_web:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        self._score(self.ACTIVE_AREA_SCORE)

        if self.electro_first_web is None:
            self.electro_first_web = web
            self.electro_target_web = "center" if web == "left" else "left"
            self._set("sinister_surge_area_progress", 1)
            self._set("sinister_surge_hits_still_needed", 1)
            self._light_electro_web()
            self.delay.add(
                name="sinister_surge_electro_second_shot",
                ms=self.ELECTRO_SECOND_SHOT_MS,
                callback=self._electro_timeout,
            )
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="ELECTRO",
                message_mode_subtitle="HIT THE OTHER WEB - 20 SECONDS",
                reminder=True,
            )
            self._update_area_status()
            return

        self.delay.remove("sinister_surge_electro_second_shot")
        self._set("sinister_surge_area_progress", 2)
        self._set("sinister_surge_hits_still_needed", 0)
        self._area_complete()

    def _electro_timeout(self):
        if self.current_area != "electro" or self.jackpot_ready:
            return
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="ELECTRO RESET",
            message_mode_subtitle="HIT THE LIT WEB",
            reminder=True,
        )
        self._start_electro_attempt()

    def _light_electro_web(self):
        self.machine.events.post("sinister_surge_electro_clear")
        if self.electro_target_web:
            self.machine.events.post(f"sinister_surge_electro_{self.electro_target_web}_lit")

    def _left_drop_hit(self, target, **kwargs):
        if self.victory_laps:
            self._victory_lap_hit()
            return

        if self.current_area == "goblin" and not self.jackpot_ready:
            self._goblin_area_hit("left_bank")
            return

        self._score(self.INACTIVE_AREA_SCORE)

    def _goblin_area_hit(self, area):
        if not self.goblin_attempt_active or area not in self.GOBLIN_AREAS:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        if area in self.goblin_qualified_areas:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        self.goblin_qualified_areas.add(area)
        self._score(self.ACTIVE_AREA_SCORE)
        progress = len(self.goblin_qualified_areas)
        self._set("sinister_surge_area_progress", progress)
        self._set("sinister_surge_hits_still_needed", max(0, 2 - progress))
        self.machine.events.post(f"sinister_surge_goblin_{area}_collected")
        self._update_area_status()

        if progress >= 2:
            self.delay.remove("sinister_surge_goblin_attempt")
            self.goblin_attempt_active = False
            self.machine.events.post("sinister_surge_goblin_clear")
            self._release_held_saucer()
            self._area_complete()

    def _start_goblin_attempt(self, saucer_name):
        self.goblin_attempt_active = True
        self.goblin_qualified_areas.clear()
        self.held_saucer = saucer_name
        self._set("sinister_surge_area_progress", 0)
        self._set("sinister_surge_hits_still_needed", 2)
        self.machine.events.post("sinister_surge_saucer_hold_started", saucer=saucer_name)
        self.machine.events.post("sinister_surge_goblin_attempt_started")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="GREEN GOBLIN",
            message_mode_subtitle="HIT 2 OF 4 - 4 SECONDS",
            reminder=True,
        )
        self._update_area_status()
        self.delay.add(
            name="sinister_surge_goblin_attempt",
            ms=self.GOBLIN_HOLD_MS,
            callback=self._goblin_timeout,
        )

    def _goblin_timeout(self):
        if self.current_area != "goblin" or not self.goblin_attempt_active:
            return
        self.goblin_attempt_active = False
        self.goblin_qualified_areas.clear()
        self._set("sinister_surge_area_progress", 0)
        self._set("sinister_surge_hits_still_needed", 2)
        self.machine.events.post("sinister_surge_goblin_clear")
        self._release_held_saucer()
        self.machine.events.post("sinister_surge_goblin_ready")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="GOBLIN RESET",
            message_mode_subtitle="HIT A SAUCER TO RESTART",
            reminder=True,
        )
        self._update_area_status()

    def _saucer_1_hit(self, **kwargs):
        self._handle_saucer_hit("saucer_1")

    def _saucer_2_hit(self, **kwargs):
        self._handle_saucer_hit("saucer_2")

    def _saucer_3_hit(self, **kwargs):
        self._handle_saucer_hit("saucer_3")

    def _handle_saucer_hit(self, saucer_name): 
        self._score(self.SAUCER_SCORE)

        if self.mode_exiting:
            self._eject_saucer(saucer_name)
            return

        if self._balls_in_play() <= 1:
            self._eject_saucer(saucer_name)
            return

        # Only one ball may be parked in the three saucers at a time.
        if self.held_saucer is not None:
            if saucer_name != self.held_saucer:
                self._eject_saucer(saucer_name)
            return

        if self.current_area == "goblin" and not self.jackpot_ready and not self.victory_laps:
            self._start_goblin_attempt(saucer_name)
            return

        self.held_saucer = saucer_name
        self.machine.events.post("sinister_surge_saucer_hold_started", saucer=saucer_name)

        self.delay.remove("sinister_surge_saucer_hold")
        self.delay.add(
            name="sinister_surge_saucer_hold",
            ms=self.SAUCER_HOLD_MS,
            callback=self._release_held_saucer,
        )

    def _release_held_saucer(self, **kwargs):
        saucer_name = self.held_saucer
        if saucer_name is None:
            return

        self.delay.remove("sinister_surge_saucer_hold")
        self.delay.remove("sinister_surge_goblin_attempt")
        self.held_saucer = None
        self._eject_saucer(saucer_name)
        self.machine.events.post("sinister_surge_saucer_released", saucer=saucer_name)

    def _eject_saucer(self, saucer_name):
        event = self.SAUCER_EJECT_EVENTS.get(saucer_name)

        if event:
            self.machine.events.post(event)

    def _cancel_stage_timers(self):
        for name in (
            "sinister_surge_sandman_shift",
            "sinister_surge_sandman_reset_settle",
            "sinister_surge_electro_second_shot",
            "sinister_surge_goblin_attempt",
        ):
            self.delay.remove(name)

    def _multiball_ended(self, **kwargs):
        self.mode_exiting = True
        self.info_log("Sinister Surge multiball ended.")

        self._cancel_stage_timers()
        self._release_held_saucer()

        if self.victory_laps:
            self.machine.events.post("sinister_surge_mode_complete")
        else:
            self._set("sinister_surge_state", 2)
            self.machine.events.post("sinister_surge_mode_complete")

        self.machine.events.post("stop_mode_sinister_surge")

    def _update_area_status(self):
        if not self.current_area or self.current_area == "victory_laps":
            return
        display = self.AREAS[self.current_area]["display"]
        progress = self._get("sinister_surge_area_progress")
        required = self._get("sinister_surge_area_required")
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=display,
            mode_status_value=f"{progress} / {required}",
        )

    def _update_gate(self):
        if self.jackpot_ready:
            self.machine.events.post("sinister_surge_open_upper_gate")
            return

        if self.victory_laps and self.super_jackpot_ready:
            self.machine.events.post("sinister_surge_open_upper_gate")
            return

        if self.current_area == "vulture":
            self.machine.events.post("sinister_surge_open_upper_gate")
            return

        self.machine.events.post("sinister_surge_close_upper_gate")

    def _update_jackpot_value(self):
        value = (
            self.JACKPOT_BASE
            * (max(1, self._balls_in_play()) + self._get("sinister_surge_areas_cleared"))
        ) + self.case_file_bonus

        self._set("sinister_surge_jackpot_value", value)
        return value

    def _balls_in_play(self):
        if not self.machine.game:
            return 0

        return self.machine.game.balls_in_play

    def _get_area_cleared(self, area):
        return self._get(f"sinister_surge_area_{area}_cleared") == 1

    def _set_area_cleared(self, area):
        self._set(f"sinister_surge_area_{area}_cleared", 1)

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
            if name == "sinister_surge_areas_cleared":
                self._set("active_mode_hits", value)
            elif name == "sinister_surge_jackpots":
                self._set("active_mode_major_hits", value)
            return

        player = self.machine.game.player if self.machine.game else None

        if player:
            player[name] = value

    def _add(self, name, value):
        self._set(name, self._get(name) + value)
