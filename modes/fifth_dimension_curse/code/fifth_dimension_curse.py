import random

from mpf.core.mode import Mode


class FifthDimensionCurse(Mode):
    """City-zone multiball with Ruby parking and repeatable Add-a-Balls."""

    MODE_KEY = "fifth_dimension_curse"
    DISPLAY_NAME = "Fifth Dimension Curse"
    VUK_EJECT_DELAY_MS = 1_500
    RUBY_SAUCER_EJECT_DELAY_MS = 2_000
    RUBY_SUPER_BASE_VALUE = 1_000_000
    ADD_A_BALL_WINDOW_MS = 10_000
    MAX_BALLS = 4

    ZONE_SWITCHES = {
        "upper_left": [
            "s_leaf_next_to_1", "s_saucer_1", "s_saucer_2", "s_saucer_3",
            "s_upper_entrance_opto", "s_upper_exit_left_opto",
        ],
        "upper_right": [
            "s_above_star", "s_inlane_a", "s_inlane_b", "s_star_rollover",
            "s_trispinner_opto", "s_upper_exit_right_opto", "s_upper_target_left",
            "s_upper_target_center", "s_upper_target_right", "s_web_target_mid",
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

    ADD_A_BALL_TARGETS = {
        "star": "s_star_rollover",
        "upper_a": "s_inlane_a",
        "upper_b": "s_inlane_b",
    }

    RUBY_TARGETS = {
        "left": ("s_upper_target_left", 1),
        "center": ("s_upper_target_center", 2),
        "right": ("s_upper_target_right", 3),
    }

    def _post_mode_jackpot_sfx_if_needed(
        self,
        guarded_display_event="",
        message_mode_title="",
        message_mode_subtitle="",
    ):
        """Mode-local jackpot SFX hook; replace these events per mode as desired."""
        if guarded_display_event != "base_show_mode_jackpot":
            return
        title = str(message_mode_title or "").upper()
        subtitle = str(message_mode_subtitle or "").upper()
        combined = f"{title} {subtitle}".replace("-", " ")
        words = combined.split()
        if "JACKPOT" not in words:
            return
        if any(marker in title.split() for marker in ("BUILDS", "LIT", "READY", "NEXT")):
            return
        if "SUPER" in words:
            self.machine.events.post("play_mode_super_jackpot")
        else:
            self.machine.events.post("play_mode_jackpot")

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.mode_points = 0
        self.active_zones = set()
        self.zone_states = {zone: "dim" for zone in self.ZONE_SWITCHES}
        self.add_a_ball_target = None
        self.add_a_balls_awarded = 0
        self.jackpots_collected = 0
        self.parked_saucers = set()
        self.ruby_lit_saucers = set()
        self.ruby_release_pending = set()

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

        self.add_mode_event_handler("s_web_spinner_active", self._spinner_hit)
        for target, switch in self.ADD_A_BALL_TARGETS.items():
            self.add_mode_event_handler(
                f"{switch}_active",
                self._add_a_ball_target_hit,
                target=target,
            )
        for target, (switch, saucer) in self.RUBY_TARGETS.items():
            self.add_mode_event_handler(
                f"{switch}_active",
                self._ruby_target_hit,
                target=target,
                saucer=saucer,
            )
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(
                f"s_saucer_{saucer}_active",
                self._saucer_hit,
                saucer=saucer,
            )

        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)
        self.add_mode_event_handler("fifth_dimension_curse_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._complete_mode)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post("fifth_dimension_curse_dim_all_zones")
        self.machine.events.post("fifth_dimension_curse_add_a_ball_target_clear")
        self.machine.events.post("fifth_dimension_curse_saucer_lights_clear")
        self.machine.events.post("fifth_dimension_curse_ruby_lights_clear")
        self.machine.events.post("fifth_dimension_curse_start_multiball")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="FIFTH DIMENSION CURSE",
            message_mode_subtitle="LIGHT ZONES - COLLECT VUK JACKPOTS",
            reminder=True,
        )
        self._schedule_ball_guard()
        self._update_gate_and_status()

    def mode_stop(self, **kwargs):
        for zone in self.ZONE_SWITCHES:
            self.delay.remove(f"fdc_{zone}_flicker")
            self.delay.remove(f"fdc_{zone}_dim")
        self.delay.remove("fdc_add_a_ball_window")
        self.delay.remove("fdc_ball_guard")
        for saucer in (1, 2, 3):
            self.delay.remove(f"fdc_ruby_eject_{saucer}")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("fifth_dimension_curse_restore_all_lights")
        self.machine.events.post("fifth_dimension_curse_upper_targets_off")
        self.machine.events.post("fifth_dimension_curse_add_a_ball_target_clear")
        self.machine.events.post("fifth_dimension_curse_saucer_lights_clear")
        self.machine.events.post("fifth_dimension_curse_ruby_lights_clear")
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
            self.machine.events.post(
                "request_vuk_eject",
                delay_ms=self.VUK_EJECT_DELAY_MS,
            )
            return

        value = 500_000 + (zones - 1) * 250_000 + self.case_file_bonus
        self._score(value)
        self.jackpots_collected += 1
        player = self.machine.game.player
        player["active_mode_hits"] = self.jackpots_collected
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="CURSE JACKPOT",
            message_mode_subtitle=f"{zones} ZONES ACTIVE",
            message_mode_value=value,
        )
        self.machine.events.post("play_mode_jackpot")
        self.ruby_lit_saucers.update(self.parked_saucers)
        self._refresh_ruby_lights()
        self.machine.events.post(
            "request_vuk_eject",
            delay_ms=self.VUK_EJECT_DELAY_MS,
        )
        self.machine.events.post("reset_mode_message_reminder")
        self._update_gate_and_status()

    def _saucer_hit(self, saucer=None, **kwargs):
        if self.mode_done or saucer is None:
            return
        saucer = int(saucer)
        if saucer in self.parked_saucers:
            return

        if self._can_park_current_saucer():
            self.parked_saucers.add(saucer)
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="RUBY PARKED",
                message_mode_subtitle=f"SAUCER {saucer}",
            )
            self._refresh_saucer_lights()
            return
        self._kick_saucer(saucer)

    def _ruby_target_hit(self, target=None, saucer=None, **kwargs):
        if self.mode_done or saucer is None:
            return
        saucer = int(saucer)
        if saucer not in self.ruby_lit_saucers:
            return

        self.ruby_lit_saucers.discard(saucer)
        self.ruby_release_pending.add(saucer)
        self._refresh_ruby_lights()

        value = self.RUBY_SUPER_BASE_VALUE + self.case_file_bonus
        self._score(value)
        self.jackpots_collected += 1
        self.machine.game.player["active_mode_hits"] = self.jackpots_collected
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="RUBY SUPER JACKPOT",
            message_mode_subtitle=f"SAUCER {saucer}",
            message_mode_value=value,
        )
        self.machine.events.post("play_mode_super_jackpot")
        self.delay.add(
            name=f"fdc_ruby_eject_{saucer}",
            ms=self.RUBY_SAUCER_EJECT_DELAY_MS,
            callback=self._eject_ruby_saucer,
            saucer=saucer,
        )

    def _eject_ruby_saucer(self, saucer=None, **kwargs):
        if saucer is None:
            return
        self._kick_saucer(int(saucer))

    def _can_park_current_saucer(self):
        # The entering ball is physically in the saucer but is not yet counted
        # in parked_saucers. Keep at least one other ball loose and playable.
        return (self._balls_in_play() - len(self.parked_saucers) - 1) >= 1

    def _schedule_ball_guard(self):
        if not self.mode_done:
            self.delay.reset(
                name="fdc_ball_guard",
                ms=250,
                callback=self._ball_guard,
            )

    def _ball_guard(self, **kwargs):
        if self.mode_done:
            return
        if self.parked_saucers and self._playable_loose_balls() <= 0:
            available = sorted(self.parked_saucers - self.ruby_release_pending)
            saucer = available[0] if available else sorted(self.parked_saucers)[0]
            self._kick_saucer(saucer)
        self._schedule_ball_guard()

    def _kick_saucer(self, saucer):
        saucer = int(saucer)
        self.delay.remove(f"fdc_ruby_eject_{saucer}")
        self.parked_saucers.discard(saucer)
        self.ruby_lit_saucers.discard(saucer)
        self.ruby_release_pending.discard(saucer)
        self.machine.events.post(
            "request_saucer_eject",
            saucer_number=saucer,
            delay_ms=0,
        )
        self._refresh_saucer_lights()
        self._refresh_ruby_lights()

    def _playable_loose_balls(self):
        return max(0, self._balls_in_play() - len(self.parked_saucers))

    def _refresh_saucer_lights(self):
        self.machine.events.post("fifth_dimension_curse_saucer_lights_clear")
        for saucer in sorted(self.parked_saucers):
            self.machine.events.post(f"fifth_dimension_curse_saucer_{saucer}_parked")

    def _refresh_ruby_lights(self):
        self.machine.events.post("fifth_dimension_curse_ruby_lights_clear")
        for saucer in sorted(self.ruby_lit_saucers):
            target = {1: "left", 2: "center", 3: "right"}[saucer]
            self.machine.events.post(f"fifth_dimension_curse_ruby_{target}_lit")

    def _spinner_hit(self, **kwargs):
        """Light one repeatable ten-second Add-a-Ball target."""
        if self.mode_done or self.add_a_ball_target is not None:
            return
        if self._balls_in_play() >= self.MAX_BALLS:
            return

        self.add_a_ball_target = random.choice(tuple(self.ADD_A_BALL_TARGETS))
        self.machine.events.post(
            f"fifth_dimension_curse_add_a_ball_{self.add_a_ball_target}_lit"
        )
        display_name = {
            "star": "STAR",
            "upper_a": "UPPER A",
            "upper_b": "UPPER B",
        }[self.add_a_ball_target]
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="ADD-A-BALL LIT",
            message_mode_subtitle=f"{display_name} - 10 SECONDS",
        )
        self.delay.add(
            name="fdc_add_a_ball_window",
            ms=self.ADD_A_BALL_WINDOW_MS,
            callback=self._expire_add_a_ball_target,
        )

    def _add_a_ball_target_hit(self, target=None, **kwargs):
        if self.mode_done or not target or target != self.add_a_ball_target:
            return
        self.delay.remove("fdc_add_a_ball_window")
        self._clear_add_a_ball_target()

        if self._balls_in_play() >= self.MAX_BALLS:
            return
        self.add_a_balls_awarded += 1
        self.machine.game.player["active_mode_major_hits"] = self.add_a_balls_awarded
        self.machine.events.post("fifth_dimension_curse_add_a_ball")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="ADD-A-BALL",
            message_mode_subtitle=f"{self.add_a_balls_awarded} COLLECTED",
        )

    def _expire_add_a_ball_target(self, **kwargs):
        if self.mode_done or self.add_a_ball_target is None:
            return
        self._clear_add_a_ball_target()

    def _clear_add_a_ball_target(self):
        self.add_a_ball_target = None
        self.machine.events.post("fifth_dimension_curse_add_a_ball_target_clear")

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

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        try:
            return int(self.machine.game.balls_in_play or 0)
        except (TypeError, ValueError, AttributeError):
            return 0
