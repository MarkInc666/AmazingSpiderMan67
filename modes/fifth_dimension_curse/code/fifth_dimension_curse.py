from mpf.core.mode import Mode


class FifthDimensionCurse(Mode):
    """Mystic Menace mini-wizard: keep six city zones alive for VUK jackpots."""

    MODE_KEY = "fifth_dimension_curse"
    DISPLAY_NAME = "Fifth Dimension Curse"

    ZONE_SWITCHES = {
        "upper_left": [
            "s_leaf_next_to_1", "s_saucer_1", "s_saucer_2", "s_saucer_3",
            "s_upper_entrance_opto", "s_upper_exit_left_opto",
        ],
        "upper_right": [
            "s_above_star", "s_inlane_a", "s_inlane_b", "s_star_rollover",
            "s_trispinner_opto", "s_upper_exit_right_opto", "s_upper_target_left",
            "s_upper_target_center", "s_upper_target_right", "s_web_target_mid", "s_web_target_top",
        ],
        "middle_left": [
            "s_above_spinner", "s_inlane_m_l", "s_left_drops_1", "s_left_drops_2",
            "s_left_drops_3", "s_left_drops_rubber", "s_left_drops_top_left_rubber",
            "s_left_drops_top_right_rubber", "s_pop_left", "s_web_spinner", "s_web_target_left",
        ],
        "middle_right": [
            "s_inlane_m_r", "s_mid_right_rubber", "s_pop_right", "s_right_drops_1",
            "s_right_drops_2", "s_right_drops_3", "s_right_drops_4", "s_right_drops_5",
            "s_right_drops_rubber", "s_right_drops_top_rubber",
        ],
        "lower_left": ["s_inlane_l", "s_outlane_l", "s_sling_l"],
        "lower_right": ["s_inlane_r", "s_outlane_r", "s_sling_r"],
    }

    UPPER_TARGETS = {
        "left": "s_upper_target_left",
        "center": "s_upper_target_center",
        "right": "s_upper_target_right",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.mode_points = 0
        self.active_zones = set()
        self.zone_states = {zone: "dim" for zone in self.ZONE_SWITCHES}
        self.upper_targets_hit = set()
        self.upper_completion_active = False
        self.add_a_balls_awarded = 0
        self.add_a_ball_qualified = False
        self.jackpots_collected = 0

        player = self.machine.game.player
        self.case_file_bonus = player["mini_wizard_case_file_bonus"]
        player["mini_wizard_current_key"] = self.MODE_KEY
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0

        for zone, switches in self.ZONE_SWITCHES.items():
            for switch in switches:
                self.add_mode_event_handler(f"{switch}_active", self._zone_hit, zone=zone)

        for target, switch in self.UPPER_TARGETS.items():
            self.add_mode_event_handler(f"{switch}_active", self._upper_target_hit, target=target)

        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)
        self.add_mode_event_handler("fifth_dimension_curse_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._complete_mode)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post("fifth_dimension_curse_dim_all_zones")
        self.machine.events.post("fifth_dimension_curse_upper_targets_reset")
        self.machine.events.post("fifth_dimension_curse_start_multiball")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="FIFTH DIMENSION CURSE",
            message_mode_subtitle="LIGHT ZONES - COLLECT VUK JACKPOTS",
            reminder=True,
        )
        self._update_gate_and_status()

    def mode_stop(self, **kwargs):
        for zone in self.ZONE_SWITCHES:
            self.delay.remove(f"fdc_{zone}_flicker")
            self.delay.remove(f"fdc_{zone}_dim")
        self.delay.remove("fdc_upper_reset")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("fifth_dimension_curse_restore_all_lights")
        self.machine.events.post("fifth_dimension_curse_upper_targets_off")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        player = self.machine.game.player
        if player["mini_wizard_current_key"] == self.MODE_KEY:
            player["mini_wizard_current_key"] = ""
        super().mode_stop(**kwargs)

    def _zone_hit(self, zone=None, **kwargs):
        if self.mode_done or not zone:
            return
        self._light_zone(zone)

    def _light_zone(self, zone):
        self.delay.remove(f"fdc_{zone}_flicker")
        self.delay.remove(f"fdc_{zone}_dim")
        self.active_zones.add(zone)
        self.zone_states[zone] = "bright"
        self.machine.events.post(f"fifth_dimension_curse_zone_{zone}_bright")
        self.delay.add(name=f"fdc_{zone}_flicker", ms=5000, callback=self._zone_flicker, zone=zone)
        self.delay.add(name=f"fdc_{zone}_dim", ms=8000, callback=self._zone_dim, zone=zone)
        self._update_gate_and_status()

    def _zone_flicker(self, zone=None, **kwargs):
        if self.mode_done or zone not in self.active_zones:
            return
        self.zone_states[zone] = "flicker"
        self.machine.events.post(f"fifth_dimension_curse_zone_{zone}_flicker")

    def _zone_dim(self, zone=None, **kwargs):
        if self.mode_done or not zone:
            return
        self.active_zones.discard(zone)
        self.zone_states[zone] = "dim"
        self.machine.events.post(f"fifth_dimension_curse_zone_{zone}_dim")
        self._update_gate_and_status()

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            return
        zones = len(self.active_zones)
        if zones <= 0:
            self.machine.events.post("up_kick")
            return

        value = 500_000 + (zones - 1) * 250_000 + self.case_file_bonus
        self._score(value)
        self.jackpots_collected += 1
        self.add_a_ball_qualified = zones >= 3 and self.add_a_balls_awarded < 3
        player = self.machine.game.player
        player["active_mode_hits"] = self.jackpots_collected
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="CURSE JACKPOT",
            message_mode_subtitle=f"{zones} ZONES ACTIVE",
            message_mode_value=value,
        )
        self.machine.events.post("up_kick")
        self.machine.events.post("reset_mode_message_reminder")
        self._update_gate_and_status()

    def _upper_target_hit(self, target=None, **kwargs):
        if self.mode_done or not target or self.upper_completion_active:
            return
        zones = len(self.active_zones)
        value = 100_000 + 25_000 * zones
        self._score(value)

        if target not in self.upper_targets_hit:
            self.upper_targets_hit.add(target)
            self.machine.events.post(f"fifth_dimension_curse_upper_{target}_solid")

        self.machine.events.post(
            "show_mode_message",
            message_mode_title="MYSTIC TARGET",
            message_mode_subtitle=f"{zones} ZONES - {value // 1000}K",
        )

        if len(self.upper_targets_hit) == 3:
            self._complete_upper_targets()

    def _complete_upper_targets(self):
        self.upper_completion_active = True
        self.machine.events.post("fifth_dimension_curse_upper_targets_complete")
        if self.add_a_ball_qualified and self.add_a_balls_awarded < 3:
            self.add_a_balls_awarded += 1
            self.add_a_ball_qualified = False
            self.machine.game.player["active_mode_major_hits"] = self.add_a_balls_awarded
            self.machine.events.post("fifth_dimension_curse_add_a_ball")
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="ADD-A-BALL",
                message_mode_subtitle=f"{self.add_a_balls_awarded} OF 3",
            )
        self.delay.add(name="fdc_upper_reset", ms=1500, callback=self._reset_upper_targets)

    def _reset_upper_targets(self, **kwargs):
        self.upper_completion_active = False
        self.upper_targets_hit.clear()
        self.machine.events.post("fifth_dimension_curse_upper_targets_reset")

    def _multiball_ended(self, **kwargs):
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _update_gate_and_status(self):
        zones = len(self.active_zones)
        if zones:
            self.machine.events.post("rooftop_diverter_open")
        else:
            self.machine.events.post("rooftop_diverter_close")
        next_value = 0 if zones == 0 else 500_000 + (zones - 1) * 250_000 + self.case_file_bonus
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="ZONES / JACKPOT",
            mode_status_value=f"{zones} / {next_value:,}",
        )

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points
