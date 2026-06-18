from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Parafino(CaseFileMixin, Mode):

    """
    PARAFINO: MELT THE WAX

    Start 2-ball multiball.

    Three zones build temporary saucer jackpots:
    - Left drops  -> Saucer 1
    - Pops        -> Saucer 2
    - Right drops -> Saucer 3

    Each zone starts unlit with no jackpot value.
    Each zone hit adds 100K and lights that zone's saucer.
    Bigger Jackpot case file makes each hit add 150K.

    At 3 zone hits, that zone's saucer qualifies add-a-ball.
    Faster Meltdown case file qualifies add-a-ball at 2 hits.

    Collecting a saucer awards the current zone jackpot.
    If add-a-ball is qualified and not already collected for that zone,
    the saucer also awards add-a-ball.

    After saucer collect, that zone normally resets to unlit / 0.
    With More Jackpots, the first collect per zone does not reset;
    that zone stays lit at the same value for one extra collect.

    Uncollected zone value is lost when the mode ends.
    Mode ends when multiball ends.
    """

    UNLIT_SAUCER_SCORE = 50_000
    ZONE_BUILD_BASE = 100_000
    ZONE_BUILD_BIGGER = 150_000
    ADD_BALL_HIT_THRESHOLD = 3
    ADD_BALL_HIT_THRESHOLD_FAST = 2
    SAUCER_EJECT_DELAY_MS = 2_000
    SAFETY_NET_DELAY_MS = 20_000

    ZONES = {
        "left": {
            "display": "LEFT DROPS",
            "hits_var": "parafino_left_hits",
            "value_var": "parafino_left_jackpot_value",
            "lit_var": "parafino_left_jackpot_lit",
            "add_ball_qualified_var": "parafino_saucer_1_add_ball_qualified",
            "add_ball_used_var": "parafino_saucer_1_add_ball_used",
            "extra_collect_used_var": "parafino_saucer_1_extra_collect_used",
            "jackpots_var": "parafino_left_jackpots",
            "saucer": "saucer_1",
            "jackpot_lit_event": "parafino_left_jackpot_lit",
            "add_ball_lit_event": "parafino_saucer_1_add_ball_lit",
            "reset_event": "parafino_saucer_1_reset",
        },
        "pops": {
            "display": "POP BUMPERS",
            "hits_var": "parafino_pops_hits",
            "value_var": "parafino_pops_jackpot_value",
            "lit_var": "parafino_pops_jackpot_lit",
            "add_ball_qualified_var": "parafino_saucer_2_add_ball_qualified",
            "add_ball_used_var": "parafino_saucer_2_add_ball_used",
            "extra_collect_used_var": "parafino_saucer_2_extra_collect_used",
            "jackpots_var": "parafino_pops_jackpots",
            "saucer": "saucer_2",
            "jackpot_lit_event": "parafino_pops_jackpot_lit",
            "add_ball_lit_event": "parafino_saucer_2_add_ball_lit",
            "reset_event": "parafino_saucer_2_reset",
        },
        "right": {
            "display": "RIGHT DROPS",
            "hits_var": "parafino_right_hits",
            "value_var": "parafino_right_jackpot_value",
            "lit_var": "parafino_right_jackpot_lit",
            "add_ball_qualified_var": "parafino_saucer_3_add_ball_qualified",
            "add_ball_used_var": "parafino_saucer_3_add_ball_used",
            "extra_collect_used_var": "parafino_saucer_3_extra_collect_used",
            "jackpots_var": "parafino_right_jackpots",
            "saucer": "saucer_3",
            "jackpot_lit_event": "parafino_right_jackpot_lit",
            "add_ball_lit_event": "parafino_saucer_3_add_ball_lit",
            "reset_event": "parafino_saucer_3_reset",
        },
    }

    SAUCER_TO_ZONE = {
        "saucer_1": "left",
        "saucer_2": "pops",
        "saucer_3": "right",
    }

    SAUCER_EJECT_EVENTS = {
        "saucer_1": "delayed_kickout_saucer_1",
        "saucer_2": "delayed_kickout_saucer_2",
        "saucer_3": "delayed_kickout_saucer_3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("parafino")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SAUCERS HOLD VALUE FOR EXTRA COLLECT"),
            ("bigger_jackpots", "ZONE HITS BUILD 150K"),
            ("more_time", "FASTER MELTDOWN: 2 HITS FOR ADD-A-BALL"),
            ("safety_net", "SAFETY NET AFTER MULTIBALL SAVE"),
            ("shot_assist", "FIRST ZONE HITS COUNT DOUBLE"),
        ])

        self.mode_exiting = False
        self._reset_player_vars()
        self._add_switch_handlers()

        self.add_mode_event_handler("parafino_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler("multiball_parafino_multiball_started", self._multiball_started)
        self.add_mode_event_handler("parafino_reset_zones", self._reset_all_zones)
        self.add_mode_event_handler("parafino_reset_heat_cycle", self._reset_all_zones)

        # Parafino wants the rooftop gate closed while running.
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("parafino_startup_complete")
        self.machine.events.post("show_mode_message_long", message_mode_title="MELT THE WAX", message_mode_subtitle="HEAT AREAS FOR SAUCER JACKPOTS")

    def mode_stop(self, **kwargs):
        self.clear_active_case_file_helpers()
        self.mode_exiting = True
        self.delay.remove("parafino_start_safety_net")

        self.machine.events.post("parafino_clear_all_lights")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("rooftop_diverter_close")

        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        self.zone_build_value = self.ZONE_BUILD_BASE
        self.add_ball_hit_threshold = self.ADD_BALL_HIT_THRESHOLD
        self.case_file_extra_collects = False
        self.case_file_safety_net_after_mb_save = False
        self.case_file_shot_assist_double_first_zone_hit = False

        if self.has_case_file("more_jackpots"):
            self.case_file_extra_collects = True

        if self.has_case_file("bigger_jackpots"):
            self.zone_build_value = self.ZONE_BUILD_BIGGER

        if self.has_case_file("more_time"):
            self.add_ball_hit_threshold = self.ADD_BALL_HIT_THRESHOLD_FAST

        if self.has_case_file("safety_net"):
            self.case_file_safety_net_after_mb_save = True

        if self.has_case_file("shot_assist"):
            self.case_file_shot_assist_double_first_zone_hit = True

    def _add_switch_handlers(self):
        # Pop bumper zone.
        self.add_mode_event_handler("s_pop_left_active", self._pops_zone_hit)
        self.add_mode_event_handler("s_pop_right_active", self._pops_zone_hit)

        self.add_mode_event_handler("drop_target_bank_dt_bank_left_down", self._left_drops_complete)
        self.add_mode_event_handler("drop_target_bank_dt_bank_right_down", self._right_drops_complete)

        # Left drops.
        self.add_mode_event_handler("s_left_drops_1_active", self._left_drop_hit)
        self.add_mode_event_handler("s_left_drops_2_active", self._left_drop_hit)
        self.add_mode_event_handler("s_left_drops_3_active", self._left_drop_hit)

        # Right drops.
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
        player = self.machine.game.player

        player["parafino_mode_points"] = 0
        player["parafino_completed"] = 0
        player["parafino_zone_hits"] = 0
        player["parafino_jackpots"] = 0
        player["parafino_total_jackpots"] = 0
        player["parafino_jackpot_value"] = 0
        player["parafino_last_jackpot_value"] = 0

        # Compatibility / display vars from the old heat version.
        player["parafino_heat_hits"] = 0
        player["parafino_left_heat"] = 0
        player["parafino_pops_heat"] = 0
        player["parafino_right_heat"] = 0
        player["parafino_lowest_heat"] = 0

        for zone, data in self.ZONES.items():
            player[data["hits_var"]] = 0
            player[data["value_var"]] = 0
            player[data["lit_var"]] = 0
            player[data["add_ball_qualified_var"]] = 0
            player[data["add_ball_used_var"]] = 0
            player[data["extra_collect_used_var"]] = 0
            player[data["jackpots_var"]] = 0

    def _left_drop_hit(self, **kwargs):
        self._zone_hit("left")

    def _pops_zone_hit(self, **kwargs):
        self._zone_hit("pops")

    def _right_drop_hit(self, **kwargs):
        self._zone_hit("right")

    def _left_drops_complete(self, **kwargs):
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")

    def _right_drops_complete(self, **kwargs):
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

    def _zone_hit(self, zone):
        if self.mode_exiting:
            return

        player = self.machine.game.player
        if player["villain_mode_in_summary"] is True:
            return

        data = self.ZONES[zone]
        hits_to_add = 1

        if self.case_file_shot_assist_double_first_zone_hit and player[data["hits_var"]] == 0:
            hits_to_add = 2
            self.machine.events.post("parafino_case_file_shot_assist_used", zone=zone)

        for _ in range(hits_to_add):
            player[data["hits_var"]] += 1
            player[data["value_var"]] += self.zone_build_value
            player["parafino_zone_hits"] += 1
            player["parafino_heat_hits"] += 1

        player[data["lit_var"]] = 1
        player["parafino_jackpot_value"] = player[data["value_var"]]

        self.machine.events.post(
            "parafino_zone_hit",
            zone=zone,
            hits=player[data["hits_var"]],
            value=player[data["value_var"]],
        )
        self.machine.events.post("show_mode_message", message_mode_title="AREA HEATING", message_mode_subtitle=data["display"], message_mode_value=player[data["value_var"]])
        self.machine.events.post(
            data["jackpot_lit_event"],
            value=player[data["value_var"]],
        )

        if (
            player[data["hits_var"]] >= self.add_ball_hit_threshold and
            player[data["add_ball_used_var"]] == 0
        ):
            if player[data["add_ball_qualified_var"]] == 0:
                self.machine.events.post(
                    data["add_ball_lit_event"],
                    value=player[data["value_var"]],
                )
                self.machine.events.post("show_mode_message", message_mode_title="ADD-A-BALL READY", message_mode_subtitle=data["display"])
            player[data["add_ball_qualified_var"]] = 1

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
        player = self.machine.game.player

        if player[data["lit_var"]] != 1:
            self._score(self.UNLIT_SAUCER_SCORE)
            self.machine.events.post("parafino_unlit_saucer_hit", saucer=saucer)
            self._eject_saucer(saucer)
            return

        self._collect_jackpot(zone, saucer)
        self._eject_saucer(saucer)

    def _collect_jackpot(self, zone, saucer):
        data = self.ZONES[zone]
        player = self.machine.game.player
        value = player[data["value_var"]]

        self._score(value)
        player[data["jackpots_var"]] += 1
        player["parafino_jackpots"] += 1
        player["parafino_total_jackpots"] += 1
        player["parafino_last_jackpot_value"] = value
        player["parafino_jackpot_value"] = value

        add_ball_awarded = False
        if (
            player[data["add_ball_qualified_var"]] == 1 and
            player[data["add_ball_used_var"]] == 0
        ):
            player[data["add_ball_used_var"]] = 1
            player[data["add_ball_qualified_var"]] = 0
            self.machine.events.post("parafino_add_a_ball")
            self.machine.events.post("parafino_add_a_ball_collected", zone=zone, saucer=saucer)
            self.machine.events.post("show_mode_message", message_mode_title="ADD-A-BALL", message_mode_subtitle=f"{data["display"]}")
            add_ball_awarded = True

        self.machine.events.post(
            "parafino_jackpot_collected",
            zone=zone,
            saucer=saucer,
            value=value,
            add_ball_awarded=add_ball_awarded,
        )
        self.machine.events.post("show_mode_jackpot", message_mode_title="WAX JACKPOT", message_mode_subtitle=data["display"], message_mode_value=value)

        if self.case_file_extra_collects and player[data["extra_collect_used_var"]] == 0:
            player[data["extra_collect_used_var"]] = 1
            self.machine.events.post(
                "parafino_case_file_extra_collect_ready",
                zone=zone,
                saucer=saucer,
                value=value,
            )
            self.machine.events.post("show_mode_message", message_mode_title="EXTRA COLLECT READY", message_mode_subtitle=data["display"], message_mode_value=value)
            return

        self._reset_zone(zone)

    def _reset_zone(self, zone):
        data = self.ZONES[zone]
        player = self.machine.game.player

        player[data["hits_var"]] = 0
        player[data["value_var"]] = 0
        player[data["lit_var"]] = 0
        player[data["add_ball_qualified_var"]] = 0
        player["parafino_jackpot_value"] = 0

        # Compatibility / old heat vars.
        if zone == "left":
            player["parafino_left_heat"] = 0
        elif zone == "pops":
            player["parafino_pops_heat"] = 0
        elif zone == "right":
            player["parafino_right_heat"] = 0

        self.machine.events.post(data["reset_event"])

    def _reset_all_zones(self, **kwargs):
        for zone in self.ZONES:
            self._reset_zone(zone)

        self.machine.events.post("parafino_clear_jackpot_lights")
        self.machine.events.post("parafino_zones_reset")

    def _multiball_started(self, **kwargs):
        if self.case_file_safety_net_after_mb_save:
            self.delay.remove("parafino_start_safety_net")
            self.delay.add(
                name="parafino_start_safety_net",
                ms=self.SAFETY_NET_DELAY_MS,
                callback=self._start_safety_net_after_mb_save,
            )

    def _start_safety_net_after_mb_save(self):
        if self.mode_exiting:
            return
        self.machine.events.post("start_case_file_ball_save")
        self.machine.events.post("parafino_case_file_safety_net_started")

    def _eject_saucer(self, saucer):
        event = self.SAUCER_EJECT_EVENTS.get(saucer)

        if not event:
            return

        self.delay.remove(f"parafino_eject_{saucer}")
        self.delay.add(
            name=f"parafino_eject_{saucer}",
            ms=self.SAUCER_EJECT_DELAY_MS,
            callback=self.machine.events.post,
            event=event,
        )

    def _multiball_ended(self, **kwargs):
        self.info_log("Parafino multiball ended.")
        self.mode_exiting = True
        self.delay.remove("parafino_start_safety_net")

        for saucer in self.SAUCER_EJECT_EVENTS:
            self._eject_saucer(saucer)

        if self.machine.game.player["parafino_total_jackpots"] >= 3:
            self.machine.game.player["parafino_completed"] = 1
            self.machine.events.post("parafino_mode_complete")
        else:
            self.machine.game.player["parafino_completed"] = 0
            self.machine.events.post("parafino_mode_failed")

    def _score(self, points):
        if points <= 0:
            return

        player = self.machine.game.player
        player["score"] += points
        player["parafino_mode_points"] += points
