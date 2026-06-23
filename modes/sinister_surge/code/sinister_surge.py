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
    SINISTER SURGE: CLEAR THE CITY

    A+B Daily Bugle mystery disabled during wizard mode.

    Start 2-ball multiball with 20s ball save.

    One random city area is active at a time:
    - Pops: 10 hits
    - Spinner: 10 spins
    - Star: 3 hits
    - Upper Targets: 2 hits each
    - Drops: complete both banks

    Active area hits score 50K.
    Inactive area hits score 20K.

    Completing the active area lights Daily Bugle Jackpot at the VUK and opens the gate.
    Jackpot = 100K × (balls in play + cleared areas)

    Complete A+B before collecting Jackpot to add-a-ball on Jackpot collect.
    Max 5 balls in play.
    10 second ball save when ball added.
    A+B resets after each Jackpot.

    Saucers score 50K.
    If more than 1 ball is active, saucers hold the ball for 10s, then eject.
    If only 1 ball remains, saucers eject immediately.

    Upper gate opens only when:
    - Daily Bugle Jackpot is ready
    - Spinner area is active
    - Upper Target area is active

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
    SAUCER_HOLD_MS = 10_000
    MAX_BALLS = 5

    AREAS = {
        "pops": {
            "display": "POP BUMPERS",
            "required": 10,
        },
        "spinner": {
            "display": "SPINNERS",
            "required": 20,
        },
        "star": {
            "display": "STAR",
            "required": 3,
        },
        "upper_targets": {
            "display": "UPPER TARGETS",
            "required": 6,
        },
        "drops": {
            "display": "DROP TARGETS",
            "required": 2,
        },
    }

    UPPER_TARGETS = {
        "left": "sinister_surge_upper_left_hits",
        "center": "sinister_surge_upper_center_hits",
        "right": "sinister_surge_upper_right_hits",
    }

    SAUCER_EJECT_EVENTS = {
        "saucer_1": "delayed_kickout_saucer_1",
        "saucer_2": "delayed_kickout_saucer_2",
        "saucer_3": "delayed_kickout_saucer_3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_exiting = False
        self.current_area = None
        self.jackpot_ready = False
        self.victory_laps = False
        self.super_jackpot_ready = False
        self.held_saucers = set()
        self.left_bank_complete = False
        self.right_bank_complete = False

        self._reset_player_vars()

        self._add_switch_handlers()
        self.add_mode_event_handler("sinister_surge_choose_first_area", self._choose_next_area)
        self.add_mode_event_handler("sinister_surge_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler("sinister_surge_release_all_saucers", self._release_all_held_saucers)

    def mode_stop(self, **kwargs):
        self.mode_exiting = True

        self._release_all_held_saucers()

        self.machine.events.post("sinister_surge_clear_all_sinister_surge_lights")
        self.machine.events.post("sinister_surge_close_upper_gate")

        super().mode_stop(**kwargs)

    def _add_switch_handlers(self):
        # A/B rollovers
        self.add_mode_event_handler("s_inlane_a_active", self._a_hit)
        self.add_mode_event_handler("s_inlane_m_r_active", self._a_hit)
        self.add_mode_event_handler("s_inlane_b_active", self._b_hit)
        self.add_mode_event_handler("s_inlane_m_l_active", self._b_hit)

        # Daily Bugle / VUK jackpot
        self.add_mode_event_handler("s_vuk_switch_active", self._daily_bugle_hit)

        # Area switches
        self.add_mode_event_handler("s_pop_left_active", self._pop_hit)
        self.add_mode_event_handler("s_pop_right_active", self._pop_hit)

        self.add_mode_event_handler("s_trispinner_opto_active", self._spinner_hit)
        self.add_mode_event_handler("s_web_spinner_active", self._spinner_hit)

        self.add_mode_event_handler("s_star_rollover_active", self._star_hit)

        self.add_mode_event_handler("s_upper_target_left_active", self._upper_target_left_hit)
        self.add_mode_event_handler("s_upper_target_center_active", self._upper_target_center_hit)
        self.add_mode_event_handler("s_upper_target_right_active", self._upper_target_right_hit)

        self.add_mode_event_handler("drop_target_bank_dt_bank_left_down", self._left_drops_complete)
        self.add_mode_event_handler("drop_target_bank_dt_bank_right_down", self._right_drops_complete)

        # Saucers
        self.add_mode_event_handler("s_saucer_1_active", self._saucer_1_hit)
        self.add_mode_event_handler("s_saucer_2_active", self._saucer_2_hit)
        self.add_mode_event_handler("s_saucer_3_active", self._saucer_3_hit)

    def _reset_player_vars(self):
        self._set("active_mode_points", 0)
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

        self._set("sinister_surge_upper_left_hits", 0)
        self._set("sinister_surge_upper_center_hits", 0)
        self._set("sinister_surge_upper_right_hits", 0)
        self._set("sinister_surge_area_pops_cleared", 0)
        self._set("sinister_surge_area_spinner_cleared", 0)
        self._set("sinister_surge_area_star_cleared", 0)
        self._set("sinister_surge_area_upper_targets_cleared", 0)
        self._set("sinister_surge_area_drops_cleared", 0)    

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
        self.left_bank_complete = False
        self.right_bank_complete = False

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

    def _reset_area_specific_progress(self):
        self._set("sinister_surge_upper_left_hits", 0)
        self._set("sinister_surge_upper_center_hits", 0)
        self._set("sinister_surge_upper_right_hits", 0)

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

        self._set_area_cleared(completed_area)
        self._add("sinister_surge_areas_cleared", 1)

        # If the drops task was completed, reset the banks immediately
        # so the next part of the mode starts clean.
        if completed_area == "drops":
            self.machine.events.post("sinister_surge_reset_drop_banks")
            self.left_bank_complete = False
            self.right_bank_complete = False

        self.jackpot_ready = True
        self._set("sinister_surge_jackpot_ready", 1)
        self._update_jackpot_value()
        self._update_gate()

        self.machine.events.post("sinister_surge_area_complete", area=completed_area)
        self.machine.events.post("sinister_surge_jackpot_lit", area=completed_area)
        self.machine.events.post("sinister_surge_jackpot_lit_show")

    def _daily_bugle_hit(self, **kwargs):
        self.delay.add(
            name="sinister_surge_vuk_delay_eject",
            ms=2000,
            callback=self.fire_VUK
        )

        if self.victory_laps:
            self._collect_super_jackpot()
            return

        if not self.jackpot_ready:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        self._collect_jackpot()


    def fire_VUK(self):
        self.machine.events.post("up_kick")


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

    def _victory_lap_hit(self):
        self._score(self.ACTIVE_AREA_SCORE)

    def _collect_super_jackpot(self):
        if not self.super_jackpot_ready:
            self._score(self.INACTIVE_AREA_SCORE)
            return

        value = self.SUPER_JACKPOT_BASE * max(1, self._balls_in_play())
        self._score(value)
        self._add("sinister_surge_super_jackpots", 1)

        self.super_jackpot_ready = False
        self._set("sinister_surge_super_jackpot_ready", 0)
        self._set("sinister_surge_super_jackpot_value", 0)
        self._reset_ab()
        self._update_gate()

        self.machine.events.post("sinister_surge_super_jackpot_collected", value=value)

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
                value = self.SUPER_JACKPOT_BASE * max(1, self._balls_in_play())
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
        self._area_hit("pops")

    def _spinner_hit(self, **kwargs):
        self._area_hit("spinner")

    def _star_hit(self, **kwargs):
        self._area_hit("star")

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

        if self.current_area != "upper_targets":
            self._area_hit("upper_targets", amount=0)
            return

        var_name = self.UPPER_TARGETS[target]
        current_hits = self._get(var_name)

        if current_hits >= 2:
            # Already completed this target. Still score inactive-style points.
            self._score(self.INACTIVE_AREA_SCORE)
            return

        self._set(var_name, current_hits + 1)
        self._area_hit("upper_targets")

    def _left_drops_complete(self, **kwargs):
        self.left_bank_complete = True
        self._drops_progress()

    def _right_drops_complete(self, **kwargs):
        self.right_bank_complete = True
        self._drops_progress()

    def _drops_progress(self):
        if self.jackpot_ready:
          return
        
        if self.victory_laps:
          self._victory_lap_hit()
          return

        if self.current_area != "drops":
          self._area_hit("drops", amount=0)
          return

        completed_count = int(self.left_bank_complete) + int(self.right_bank_complete)
        self._set("sinister_surge_area_progress", completed_count)

        self._score(self.ACTIVE_AREA_SCORE)

        if completed_count >= 2:
          self._area_complete()

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
                       
        if saucer_name in self.held_saucers:
         return

        if self._balls_in_play() <= 1:
            self._eject_saucer(saucer_name)
            return

        self.held_saucers.add(saucer_name)
        self.machine.events.post("sinister_surge_saucer_hold_started", saucer=saucer_name)

        self.delay.remove(f"sinister_surge_{saucer_name}_hold")
        self.delay.add(
            name=f"sinister_surge_{saucer_name}_hold",
            ms=self.SAUCER_HOLD_MS,
            callback=self._release_saucer,
            saucer_name=saucer_name
        )

    def _release_saucer(self, saucer_name):
        self.held_saucers.discard(saucer_name)
        self._eject_saucer(saucer_name)
        self.machine.events.post("sinister_surge_saucer_released", saucer=saucer_name)

    def _eject_saucer(self, saucer_name):
        event = self.SAUCER_EJECT_EVENTS.get(saucer_name)

        if event:
            self.machine.events.post(event)

    def _release_all_held_saucers(self, **kwargs):
        for saucer_name in list(self.held_saucers):
            self.delay.remove(f"sinister_surge_{saucer_name}_hold")
            self._release_saucer(saucer_name)

        self.held_saucers.clear()

    def _multiball_ended(self, **kwargs):
        self.mode_exiting = True
        self.info_log("Sinister Surge multiball ended.")

        self._release_all_held_saucers()

        if self.victory_laps:
            self.machine.events.post("sinister_surge_mode_complete")
        else:
            self._set("sinister_surge_state", 2)
            self.machine.events.post("sinister_surge_mode_complete")

        self.machine.events.post("stop_mode_sinister_surge")

    def _update_gate(self):
        if self.jackpot_ready:
            self.machine.events.post("sinister_surge_open_upper_gate")
            return

        if self.victory_laps and self.super_jackpot_ready:
            self.machine.events.post("sinister_surge_open_upper_gate")
            return

        if self.current_area in ("spinner", "upper_targets"):
            self.machine.events.post("sinister_surge_open_upper_gate")
            return

        self.machine.events.post("sinister_surge_close_upper_gate")

    def _update_jackpot_value(self):
        value = self.JACKPOT_BASE * (
            max(1, self._balls_in_play()) + self._get("sinister_surge_areas_cleared")
        )

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
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return default

        try:
            return player[name]
        except KeyError:
            return default

    def _set(self, name, value):
        player = self.machine.game.player if self.machine.game else None

        if player:
            player[name] = value

    def _add(self, name, value):
        self._set(name, self._get(name) + value)