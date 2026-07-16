from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Enforcers(Mode, CaseFileMixin):
    """Enforcers / Ox villain mode.

    Three crime-wave zones build upper target jackpots:
      - Left drops  -> upper left target
      - Pops        -> upper center target
      - Right drops -> upper right target

    Zone hits light the matching upper target. Upper spinner builds the OX
    Super Jackpot. Collect all three upper target jackpots, then hit the center
    web target to collect OX and complete the mode.
    """

    MODE_KEY = "enforcers"
    DISPLAY_NAME = "Enforcers / Ox"

    ZONES = ("left", "pops", "right")
    ZONE_NAMES = {
        "left": "LEFT DROPS",
        "pops": "POPS",
        "right": "RIGHT DROPS",
    }

    BASE_JACKPOT = 100_000
    BIGGER_BASE_JACKPOT = 150_000
    AREA_HIT_SCORE = 25_000
    SPINNER_SUPER_ADD = 50_000
    MAX_MULTIPLIER = 5

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_done = False
        self.case_files = self.get_case_file_bonuses()
        self.base_jackpot = self.BIGGER_BASE_JACKPOT if self.has_case_file("bigger_jackpots") else self.BASE_JACKPOT
        self.required_hits_to_light = 1 if self.has_case_file("shot_assist") else 2

        self.zone_hits = {zone: 0 for zone in self.ZONES}
        self.zone_multiplier = {zone: 0 for zone in self.ZONES}
        self.upper_lit = {zone: False for zone in self.ZONES}
        self.upper_collected = {zone: False for zone in self.ZONES}
        self.upper_awards = {zone: 0 for zone in self.ZONES}
        self.saucer_bonus_lit = {zone: False for zone in self.ZONES}
        self.saucer_bonus_collected = {zone: False for zone in self.ZONES}

        self.mode_points = 0
        self.upper_jackpots_collected = 0
        self.saucer_bonus_collected_count = 0
        self.spinner_spins = 0
        self.spinner_super_value = 0
        self.ox_lit = False
        self.ox_super_value = 0
        self.rooftop_gate_open = False

        self._sync_vars()
        self._apply_case_file_effects()
        self._add_handlers()

        self.machine.events.post("enforcers_started")
        self.machine.events.post("enforcers_clear_all_lights")
        self.machine.events.post("enforcers_clear_upper_shows")
        self.machine.events.post("enforcers_clear_saucers")
        self.machine.events.post("enforcers_build_phase_started")
        self.machine.events.post("show_mode_message_long", message_mode_title="BREAK THE GANG", message_mode_subtitle="BUILD THREE ZONES")
        self.machine.events.post(
            "enforcers_base_jackpot_set",
            value=self.base_jackpot,
            value_str=self._format_score(self.base_jackpot),
        )

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        self.machine.events.post("enforcers_clear_all_lights")
        self.machine.events.post("enforcers_clear_upper_shows")
        self.machine.events.post("enforcers_clear_saucers")
        self._close_rooftop_gate()
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("enforcers_left_zone_hit", self._zone_hit, zone="left")
        self.add_mode_event_handler("enforcers_pops_zone_hit", self._zone_hit, zone="pops")
        self.add_mode_event_handler("enforcers_right_zone_hit", self._zone_hit, zone="right")

        self.add_mode_event_handler("enforcers_upper_left_hit", self._upper_hit, zone="left")
        self.add_mode_event_handler("enforcers_upper_center_hit", self._upper_hit, zone="pops")
        self.add_mode_event_handler("enforcers_upper_right_hit", self._upper_hit, zone="right")

        self.add_mode_event_handler("enforcers_saucer_1_hit", self._saucer_bonus_hit, zone="left")
        self.add_mode_event_handler("enforcers_saucer_2_hit", self._saucer_bonus_hit, zone="pops")
        self.add_mode_event_handler("enforcers_saucer_3_hit", self._saucer_bonus_hit, zone="right")

        self.add_mode_event_handler("enforcers_upper_spinner_hit", self._upper_spinner_hit)
        self.add_mode_event_handler("enforcers_ox_hit", self._ox_hit)
        self.add_mode_event_handler("enforcers_complete_request", self._complete_mode)
        self.add_mode_event_handler("enforcers_fail_request", self._fail_mode)

    def _apply_case_file_effects(self):
        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SAUCER BONUS JACKPOTS LIT"),
            ("bigger_jackpots", "BASE JACKPOT 150K"),
            ("more_time", "OX BALL SAVE READY"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST HIT LIGHTS JACKPOTS"),
        ])

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

    def _zone_hit(self, zone, **kwargs):
        if self.mode_done or self.ox_lit or self.upper_collected[zone]:
            return

        self.zone_hits[zone] += 1
        self._score(self.AREA_HIT_SCORE)

        previous_multiplier = self.zone_multiplier[zone]
        self.zone_multiplier[zone] = self._multiplier_for_hits(self.zone_hits[zone])

        if self.zone_hits[zone] >= self.required_hits_to_light:
            if not self.upper_lit[zone]:
                self.upper_lit[zone] = True
                self._upper_target_lit(zone)
            elif self.zone_multiplier[zone] != previous_multiplier:
                self._update_upper_flash(zone)

        self._sync_vars()
        self.machine.events.post(
            "enforcers_zone_hit",
            zone=zone,
            zone_name=self.ZONE_NAMES[zone],
            hits=self.zone_hits[zone],
            multiplier=self.zone_multiplier[zone],
            jackpot=self._current_zone_jackpot(zone),
            jackpot_str=self._format_score(self._current_zone_jackpot(zone)),
        )
        self.machine.events.post("show_mode_message", message_mode_title="ZONE HIT", message_mode_subtitle=self.ZONE_NAMES[zone], message_mode_value=self._current_zone_jackpot(zone))

    def _upper_target_lit(self, zone):
        self._update_upper_flash(zone)
        self._open_rooftop_gate()
        self.machine.events.post(
            f"enforcers_{zone}_upper_jackpot_lit",
            zone=zone,
            zone_name=self.ZONE_NAMES[zone],
            multiplier=self.zone_multiplier[zone],
            jackpot=self._current_zone_jackpot(zone),
            jackpot_str=self._format_score(self._current_zone_jackpot(zone)),
        )
        self.machine.events.post(
            "enforcers_upper_jackpot_lit",
            zone=zone,
            zone_name=self.ZONE_NAMES[zone],
            multiplier=self.zone_multiplier[zone],
            jackpot=self._current_zone_jackpot(zone),
            jackpot_str=self._format_score(self._current_zone_jackpot(zone)),
        )
        self.machine.events.post("show_mode_message", message_mode_title="UPPER JACKPOT LIT", message_mode_subtitle=self.ZONE_NAMES[zone], message_mode_value=self._current_zone_jackpot(zone))

        if self.has_case_file("more_jackpots") and not self.saucer_bonus_collected[zone]:
            self.saucer_bonus_lit[zone] = True
            self.machine.events.post(f"enforcers_{zone}_saucer_lit")
            self.machine.events.post(
                "enforcers_saucer_bonus_lit",
                zone=zone,
                zone_name=self.ZONE_NAMES[zone],
            )
            self.machine.events.post("show_mode_message", message_mode_title="SAUCER BONUS LIT", message_mode_subtitle=self.ZONE_NAMES[zone])

    def _update_upper_flash(self, zone):
        self.machine.events.post(f"enforcers_stop_{zone}_upper_flash")
        if not self.upper_lit[zone] or self.upper_collected[zone]:
            return
        multiplier = max(1, min(self.MAX_MULTIPLIER, self.zone_multiplier[zone]))
        self.machine.events.post(f"enforcers_{zone}_upper_flash_{multiplier}x")

    def _upper_hit(self, zone, **kwargs):
        if self.mode_done or not self.upper_lit[zone] or self.upper_collected[zone]:
            return

        award = self._current_zone_jackpot(zone)
        self.upper_collected[zone] = True
        self.upper_jackpots_collected += 1
        self.upper_awards[zone] = award
        self.ox_super_value += award
        self.saucer_bonus_lit[zone] = False

        self._score(award)
        self.machine.events.post(f"enforcers_stop_{zone}_upper_flash")
        self.machine.events.post(f"enforcers_{zone}_saucer_off")
        self.machine.events.post(
            "enforcers_upper_jackpot_awarded",
            zone=zone,
            zone_name=self.ZONE_NAMES[zone],
            value=award,
            value_str=self._format_score(award),
            collected=self.upper_jackpots_collected,
        )
        self.machine.events.post("show_mode_jackpot", message_mode_title="ENFORCER JACKPOT", message_mode_subtitle=self.ZONE_NAMES[zone], message_mode_value=award)

        if self.upper_jackpots_collected >= 3:
            self._light_ox()
        else:
            self._sync_vars()

    def _saucer_bonus_hit(self, zone, **kwargs):
        if (
            self.mode_done
            or not self.has_case_file("more_jackpots")
            or not self.saucer_bonus_lit[zone]
            or self.saucer_bonus_collected[zone]
        ):
            return

        award = self._current_zone_jackpot(zone)
        self.saucer_bonus_lit[zone] = False
        self.saucer_bonus_collected[zone] = True
        self.saucer_bonus_collected_count += 1

        self._score(award)
        self.machine.events.post(f"enforcers_{zone}_saucer_off")
        self.machine.events.post(
            "enforcers_saucer_bonus_awarded",
            zone=zone,
            zone_name=self.ZONE_NAMES[zone],
            value=award,
            value_str=self._format_score(award),
        )
        self.machine.events.post("show_mode_jackpot", message_mode_title="SAUCER BONUS", message_mode_subtitle=self.ZONE_NAMES[zone], message_mode_value=award)
        self._sync_vars()

    def _upper_spinner_hit(self, **kwargs):
        if self.mode_done:
            return
        self.spinner_spins += 1
        self.spinner_super_value += self.SPINNER_SUPER_ADD
        self.ox_super_value += self.SPINNER_SUPER_ADD
        self._score(5_000)
        self._sync_vars()
        self.machine.events.post(
            "enforcers_spinner_super_add",
            spins=self.spinner_spins,
            value=self.ox_super_value,
            value_str=self._format_score(self.ox_super_value),
        )
        self.machine.events.post("show_mode_message", message_mode_title="OX VALUE UP", message_mode_subtitle="UPPER SPINNER", message_mode_value=self.ox_super_value)

    def _light_ox(self):
        if self.ox_lit or self.mode_done:
            return
        self.ox_lit = True
        self._open_rooftop_gate()
        if self.has_case_file("more_time"):
            self.machine.events.post("start_case_file_ball_save")
        self._sync_vars()
        self.machine.events.post(
            "enforcers_ox_lit",
            value=self.ox_super_value,
            value_str=self._format_score(self.ox_super_value),
        )
        self.machine.events.post("show_mode_message_long", message_mode_title="OX IS READY", message_mode_subtitle="HIT CENTER WEB", message_mode_value=self.ox_super_value)

    def _ox_hit(self, **kwargs):
        if self.mode_done or not self.ox_lit:
            return
        award = self.ox_super_value
        self._score(award)
        self.machine.events.post(
            "enforcers_ox_super_jackpot_awarded",
            value=award,
            value_str=self._format_score(award),
        )
        self.machine.events.post("show_mode_jackpot", message_mode_title="OX SUPER JACKPOT", message_mode_subtitle="CENTER WEB", message_mode_value=award)
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player["enforcers_state"] = 2
        self._sync_vars()
        self.machine.events.post("enforcers_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player["enforcers_state"] = 2
        self._sync_vars()
        self.machine.events.post("enforcers_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _multiplier_for_hits(self, hits):
        if hits < self.required_hits_to_light:
            return 0
        return max(1, min(self.MAX_MULTIPLIER, hits // 2))

    def _current_zone_jackpot(self, zone):
        multiplier = max(1, self.zone_multiplier[zone])
        return self.base_jackpot * multiplier

    def _open_rooftop_gate(self):
        if self.rooftop_gate_open:
            return
        self.rooftop_gate_open = True
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("enforcers_rooftop_gate_opened")

    def _close_rooftop_gate(self):
        if not self.rooftop_gate_open:
            return
        self.rooftop_gate_open = False
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enforcers_rooftop_gate_closed")

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["enforcers_base_jackpot"] = self.base_jackpot
        player["enforcers_upper_jackpots"] = self.upper_jackpots_collected
        player["enforcers_saucer_bonus_jackpots"] = self.saucer_bonus_collected_count
        player["enforcers_spinner_spins"] = self.spinner_spins
        player["enforcers_ox_super_value"] = self.ox_super_value
        player["enforcers_ox_lit"] = 1 if self.ox_lit else 0
        player["enforcers_gate_open"] = 1 if self.rooftop_gate_open else 0

        self._update_mode_status()

        for zone in self.ZONES:
            player[f"enforcers_{zone}_hits"] = self.zone_hits[zone]
            player[f"enforcers_{zone}_multiplier"] = self.zone_multiplier[zone]
            player[f"enforcers_{zone}_jackpot_value"] = self._current_zone_jackpot(zone)
            player[f"enforcers_{zone}_upper_lit"] = 1 if self.upper_lit[zone] else 0
            player[f"enforcers_{zone}_upper_collected"] = 1 if self.upper_collected[zone] else 0
            player[f"enforcers_{zone}_saucer_lit"] = 1 if self.saucer_bonus_lit[zone] else 0
            player[f"enforcers_{zone}_saucer_collected"] = 1 if self.saucer_bonus_collected[zone] else 0
            player[f"enforcers_{zone}_award"] = self.upper_awards[zone]

    def _update_mode_status(self):
        if self.ox_lit:
            title = "OX SUPER LIT"
            value = "HIT CENTER WEB"
        else:
            lit = sum(1 for zone in self.ZONES if self.upper_lit[zone])
            collected = sum(1 for zone in self.ZONES if self.upper_collected[zone])
            title = "UPPER JPS / CLEARED"
            value = f"{lit} LIT / {collected}/3"
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)

    def _format_score(self, value):
        return f"{int(value):,}"
