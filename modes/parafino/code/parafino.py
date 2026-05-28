from mpf.core.mode import Mode


class Parafino(Mode):

    """
    PARAFINO: MELT THE WAX

    Start 2-ball multiball.

    Raise Heat in three city zones:
    - Left Drops
    - Pop Bumpers
    - Right Drops

    Each hit scores 20K and raises that zone's Heat by 1.
    If a zone is not hit for 4 seconds, its Heat drops by 1.

    Heat Levels:
    0 Icy Blue
    1 Blue-White
    2 White
    3 Warm White
    4 Orange
    5 Red

    When a zone reaches Heat Level 5, its saucer Jackpot lights:
    - Saucer 1 = Left Drops
    - Saucer 2 = Pops
    - Saucer 3 = Right Drops

    Lit saucer Jackpot = 200K x balls in play.

    The first Jackpot collected at each saucer also adds a ball.
    Each saucer can add a ball only once.

    Unlit saucers score 50K.

    After all 3 saucer Jackpots are collected, all Heat zones reset to 0.
    Jackpots can be built again, but add-a-balls do not reset.

    Mode ends when multiball ends.
    """

    HEAT_SCORE = 20_000
    UNLIT_SAUCER_SCORE = 50_000
    JACKPOT_BASE = 200_000
    MAX_HEAT = 5
    HEAT_DECAY_MS = 4_000
    GI_FLASH_MS = 1_000

    ZONES = {
        "left": {
            "display": "LEFT DROPS",
            "heat_var": "parafino_left_heat",
            "lit_var": "parafino_left_jackpot_lit",
            "jackpots_var": "parafino_left_jackpots",
            "saucer": "saucer_1",
            "add_ball_used_var": "parafino_saucer_1_add_ball_used",
            "jackpot_lit_event": "parafino_left_jackpot_lit",
        },
        "pops": {
            "display": "POP BUMPERS",
            "heat_var": "parafino_pops_heat",
            "lit_var": "parafino_pops_jackpot_lit",
            "jackpots_var": "parafino_pops_jackpots",
            "saucer": "saucer_2",
            "add_ball_used_var": "parafino_saucer_2_add_ball_used",
            "jackpot_lit_event": "parafino_pops_jackpot_lit",
        },
        "right": {
            "display": "RIGHT DROPS",
            "heat_var": "parafino_right_heat",
            "lit_var": "parafino_right_jackpot_lit",
            "jackpots_var": "parafino_right_jackpots",
            "saucer": "saucer_3",
            "add_ball_used_var": "parafino_saucer_3_add_ball_used",
            "jackpot_lit_event": "parafino_right_jackpot_lit",
        },
    }

    SAUCER_TO_ZONE = {
        "saucer_1": "left",
        "saucer_2": "pops",
        "saucer_3": "right",
    }

    SAUCER_EJECT_EVENTS = {
        "saucer_1": "kickout_saucer_1",
        "saucer_2": "kickout_saucer_2",
        "saucer_3": "kickout_saucer_3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_exiting = False
        self._reset_player_vars()
        self._add_switch_handlers()

        self.add_mode_event_handler("parafino_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler("parafino_left_drop_hit", self._left_heat_hit)
        self.add_mode_event_handler("parafino_right_drop_hit", self._right_heat_hit)
        self.add_mode_event_handler("parafino_reset_heat_cycle", self._reset_heat_cycle)

        self.machine.events.post("parafino_gi_set_heat_0")
        self.machine.events.post("parafino_startup_complete")
        

    def mode_stop(self, **kwargs):
        self.mode_exiting = True

        for zone in self.ZONES:
            self.delay.remove(f"parafino_{zone}_decay")

        self.delay.remove("parafino_return_gi_to_lowest_heat")

        self.machine.events.post("parafino_clear_all_lights")
        self.machine.events.post("clear_saucers")

        super().mode_stop(**kwargs)

    def _add_switch_handlers(self):
        # Pop bumper heat zone.
        self.add_mode_event_handler("s_pop_left_active", self._pops_heat_hit)
        self.add_mode_event_handler("s_pop_right_active", self._pops_heat_hit)

        self.add_mode_event_handler("drop_target_bank_dt_bank_left_down", self._left_drops_complete)
        self.add_mode_event_handler("drop_target_bank_dt_bank_right_down", self._right_drops_complete)

        # Left drops
        self.add_mode_event_handler("s_left_drops_1_active", self._left_drop_hit)
        self.add_mode_event_handler("s_left_drops_2_active", self._left_drop_hit)
        self.add_mode_event_handler("s_left_drops_3_active", self._left_drop_hit)

        # Right drops
        self.add_mode_event_handler("s_right_drops_1_active", self._right_drop_hit)
        self.add_mode_event_handler("s_right_drops_2_active", self._right_drop_hit)
        self.add_mode_event_handler("s_right_drops_3_active", self._right_drop_hit)
        self.add_mode_event_handler("s_right_drops_4_active", self._right_drop_hit)
        self.add_mode_event_handler("s_right_drops_5_active", self._right_drop_hit)

        # Saucers.
        self.add_mode_event_handler("s_saucer_1_active", self._saucer_1_hit)
        self.add_mode_event_handler("s_saucer_2_active", self._saucer_2_hit)
        self.add_mode_event_handler("s_saucer_3_active", self._saucer_3_hit)

    def _reset_player_vars(self):
        self._set("parafino_mode_points", 0)
        self._set("parafino_completed", 0)

        self._set("parafino_left_heat", 0)
        self._set("parafino_pops_heat", 0)
        self._set("parafino_right_heat", 0)
        self._set("parafino_heat_hits", 0)

        self._set("parafino_left_jackpot_lit", 0)
        self._set("parafino_pops_jackpot_lit", 0)
        self._set("parafino_right_jackpot_lit", 0)

        self._set("parafino_left_jackpots", 0)
        self._set("parafino_pops_jackpots", 0)
        self._set("parafino_right_jackpots", 0)
        self._set("parafino_total_jackpots", 0)

        self._set("parafino_saucer_1_add_ball_used", 0)
        self._set("parafino_saucer_2_add_ball_used", 0)
        self._set("parafino_saucer_3_add_ball_used", 0)

        self._set("parafino_jackpot_value", 0)
        self._set("parafino_lowest_heat", 0)

    def _left_heat_hit(self, **kwargs):
        self._heat_hit("left")

    def _pops_heat_hit(self, **kwargs):
        self._heat_hit("pops")

    def _right_heat_hit(self, **kwargs):
        self._heat_hit("right")

    def _left_drop_hit(self, **kwargs):
        self._heat_hit("left")

    def _right_drop_hit(self, **kwargs):
        self._heat_hit("right")

    def _left_drops_complete(self, **kwargs):
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")

    def _right_drops_complete(self, **kwargs):
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

    def _heat_hit(self, zone):
        if self.mode_exiting:
            return
        if self.machine.game.player["villain_mode_in_summary"] == True: return

        data = self.ZONES[zone]

        # Once jackpot is lit, that zone is locked and does not decay until collected/reset.
        if self._get(data["lit_var"]) == 1:
            self._score(self.HEAT_SCORE)
            return

        self._add("parafino_heat_hits", 1)

        self._score(self.HEAT_SCORE)

        new_heat = min(self.MAX_HEAT, self._get(data["heat_var"]) + 1)
        self._set(data["heat_var"], new_heat)

        self.machine.events.post("parafino_heat_hit", zone=zone, heat=new_heat)
        self.machine.events.post(f"parafino_{zone}_heat_changed", heat=new_heat)
        self._flash_gi_for_heat(new_heat)

        if new_heat >= self.MAX_HEAT:
            self._light_zone_jackpot(zone)
            return

        self._restart_decay_timer(zone)

    def _restart_decay_timer(self, zone):
        self.delay.remove(f"parafino_{zone}_decay")
        self.delay.add(
            name=f"parafino_{zone}_decay",
            ms=self.HEAT_DECAY_MS,
            callback=self._decay_zone_heat,
            zone=zone
        )

    def _decay_zone_heat(self, zone):
        data = self.ZONES[zone]

        if self.mode_exiting:
            return

        if self._get(data["lit_var"]) == 1:
            return

        current_heat = self._get(data["heat_var"])

        if current_heat <= 0:
            self._update_gi_to_lowest_heat()
            return

        new_heat = max(0, current_heat - 1)
        self._set(data["heat_var"], new_heat)

        self.machine.events.post("parafino_heat_decayed", zone=zone, heat=new_heat)
        self.machine.events.post(f"parafino_{zone}_heat_changed", heat=new_heat)
        self._update_gi_to_lowest_heat()

        if new_heat > 0:
            self._restart_decay_timer(zone)

    def _light_zone_jackpot(self, zone):
        data = self.ZONES[zone]

        self.delay.remove(f"parafino_{zone}_decay")
        self._set(data["lit_var"], 1)
        self._update_jackpot_value()

        self.machine.events.post(data["jackpot_lit_event"], value=self._get("parafino_jackpot_value"))
        self.machine.events.post("parafino_jackpot_lit", zone=zone, saucer=data["saucer"])
        self._update_gi_to_lowest_heat()

    def _saucer_1_hit(self, **kwargs):
        self._handle_saucer_hit("saucer_1")

    def _saucer_2_hit(self, **kwargs):
        self._handle_saucer_hit("saucer_2")

    def _saucer_3_hit(self, **kwargs):
        self._handle_saucer_hit("saucer_3")

    def _handle_saucer_hit(self, saucer):
        if self.mode_exiting:
            self._eject_saucer(saucer)
            return

        zone = self.SAUCER_TO_ZONE[saucer]
        data = self.ZONES[zone]

        if self._get(data["lit_var"]) != 1:
            self._score(self.UNLIT_SAUCER_SCORE)
            self.machine.events.post("parafino_unlit_saucer_hit", saucer=saucer)
            self._eject_saucer(saucer)
            return

        self._collect_jackpot(zone, saucer)
        self._eject_saucer(saucer)

    def _collect_jackpot(self, zone, saucer):
        data = self.ZONES[zone]
        value = self._update_jackpot_value()

        self._score(value)
        self._add(data["jackpots_var"], 1)
        self._add("parafino_total_jackpots", 1)
        self._set(data["lit_var"], 0)
        self._set(data["heat_var"], 0)

        add_ball_awarded = False

        if self._get(data["add_ball_used_var"]) == 0:
            self._set(data["add_ball_used_var"], 1)
            self.machine.events.post("parafino_add_a_ball")
            add_ball_awarded = True

        self.machine.events.post(
            "parafino_jackpot_collected",
            zone=zone,
            saucer=saucer,
            value=value,
            add_ball_awarded=add_ball_awarded
        )

        self._update_jackpot_value()
        self._update_gi_to_lowest_heat()

        if self._all_zone_jackpots_collected_this_cycle():
            self.machine.events.post("parafino_all_jackpots_collected")
            self._reset_heat_cycle()

    def _all_zone_jackpots_collected_this_cycle(self):
        return (
            self._get("parafino_left_heat") == 0 and
            self._get("parafino_pops_heat") == 0 and
            self._get("parafino_right_heat") == 0 and
            self._get("parafino_left_jackpot_lit") == 0 and
            self._get("parafino_pops_jackpot_lit") == 0 and
            self._get("parafino_right_jackpot_lit") == 0 and
            self._get("parafino_left_jackpots") > 0 and
            self._get("parafino_pops_jackpots") > 0 and
            self._get("parafino_right_jackpots") > 0 and
            self._get("parafino_total_jackpots") % 3 == 0
        )

    def _reset_heat_cycle(self, **kwargs):
        for zone, data in self.ZONES.items():
            self.delay.remove(f"parafino_{zone}_decay")
            self._set(data["heat_var"], 0)
            self._set(data["lit_var"], 0)

        self._set("parafino_jackpot_value", 0)
        self.machine.events.post("parafino_clear_jackpot_lights")
        self.machine.events.post("parafino_heat_cycle_reset")
        self._update_gi_to_lowest_heat()

    def _flash_gi_for_heat(self, heat):
        self.machine.events.post(f"parafino_gi_flash_heat_{heat}")

        self.delay.remove("parafino_return_gi_to_lowest_heat")
        self.delay.add(
            name="parafino_return_gi_to_lowest_heat",
            ms=self.GI_FLASH_MS,
            callback=self._update_gi_to_lowest_heat
        )

    def _update_gi_to_lowest_heat(self):
        lowest = min(
            self._get("parafino_left_heat"),
            self._get("parafino_pops_heat"),
            self._get("parafino_right_heat")
        )

        self._set("parafino_lowest_heat", lowest)
        self.machine.events.post(f"parafino_gi_set_heat_{lowest}")

    def _update_jackpot_value(self):
        value = self.JACKPOT_BASE * max(1, self._balls_in_play())
        self._set("parafino_jackpot_value", value)
        return value

    def _eject_saucer(self, saucer):
        event = self.SAUCER_EJECT_EVENTS.get(saucer)

        if event:
            self.machine.events.post(event)

    def _multiball_ended(self, **kwargs):
        self.info_log("Parafino multiball ended.")
        self.mode_exiting = True

        for saucer in self.SAUCER_EJECT_EVENTS:
            self._eject_saucer(saucer)

        if self._get("parafino_total_jackpots") >= 3:
            self._set("parafino_completed", 1)
            self.machine.events.post("parafino_mode_complete")
        else:
            self._set("parafino_completed", 0)
            self.machine.events.post("parafino_mode_failed")

        self.machine.events.post(
            "villain_bookend_summary_request",
            villain="parafino",
            done_event="parafino_mode_completed_summary"
        )

    def _score(self, points):
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return

        player["score"] += points
        self._add("parafino_mode_points", points)

    def _balls_in_play(self):
        if not self.machine.game:
            return 0

        return self.machine.game.balls_in_play

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
