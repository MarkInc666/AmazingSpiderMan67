import random

from mpf.core.mode import Mode


class NatureStrikesBack(Mode):
    """Chapter 8 wizard: repeating elemental-chain multiball.

    Cycle flow:
      1. Build charge with lower/upper spinner hits. Upper targets light their
         matching saucers for repeatable Add-a-Balls (or 3M at the 5-ball cap).
      2. Close the roof and connect both web targets to discharge into Snowman.
      3. Snowman explodes and freezes all six established city zones. Thaw all
         six while Blotto rapidly accumulates blocked zones. Star clears all blocks
         and resets Blotto's timer.
      4. Once all zones are warm/stable, open the gate and shoot the Daily Bugle
         VUK for the Super Jackpot, then begin the next harder cycle.

    Saucers remain available for parking throughout the wizard. A parked ball is
    held for at most 20 seconds, but is released immediately if parking would
    leave no loose ball on the playfield.
    """

    MODE_KEY = "nature_strikes_back"
    DISPLAY_NAME = "NATURE STRIKES BACK"

    START_BALLS = 3
    MAX_BALLS = 5
    SAUCER_HOLD_MS = 20_000

    SPIN_VALUE = 100_000
    WEB_FIRST_BASE = 500_000
    WEB_SECOND_BASE = 1_000_000
    ZONE_BASE = 250_000
    SAUCER_CAP_VALUE = 3_000_000
    SUPER_BASE = 3_000_000

    SPINS_BY_CYCLE = (10, 15, 20, 25)
    BLOTTO_MS_BY_CYCLE = (8_000, 7_000, 6_000)
    MAX_BLOTTO_BLOCKS = 3

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
            "s_left_drops_top_right_rubber", "s_pop_left", "s_web_spinner",
            "s_web_target_left",
        ],
        "middle_right": [
            "s_inlane_m_r", "s_mid_right_rubber", "s_pop_right", "s_right_drops_1",
            "s_right_drops_2", "s_right_drops_3", "s_right_drops_4",
            "s_right_drops_5", "s_right_drops_rubber", "s_right_drops_top_rubber",
        ],
        "lower_left": ["s_inlane_l", "s_outlane_l", "s_sling_l"],
        "lower_right": ["s_inlane_r", "s_outlane_r", "s_sling_r"],
    }

    ZONE_LABELS = {
        "upper_left": "UPPER LEFT",
        "upper_right": "UPPER RIGHT",
        "middle_left": "MIDDLE LEFT",
        "middle_right": "MIDDLE RIGHT",
        "lower_left": "LOWER LEFT",
        "lower_right": "LOWER RIGHT",
    }

    UPPER_TARGET_SAUCERS = {
        "s_upper_target_left": 1,
        "s_upper_target_center": 2,
        "s_upper_target_right": 3,
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.multiball_active = False
        self.mode_points = 0
        self.cycle = 1
        self.stage = 0
        self.spin_count = 0
        self.webs_hit = set()
        self.thawed_zones = set()
        self.blocked_zones = set()
        self.lit_saucers = set()
        self.held_saucers = set()
        self.add_a_balls = 0
        self.supers = 0

        player = self.machine.game.player
        self.case_file_bonus = int(player["mini_wizard_case_file_bonus"] or 0)
        player["mini_wizard_current_key"] = self.MODE_KEY
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0

        self.add_mode_event_handler("s_web_spinner_active", self._spinner_hit)
        self.add_mode_event_handler("s_trispinner_opto_active", self._spinner_hit)
        self.add_mode_event_handler("s_web_target_left_active", self._web_hit, web="left")
        self.add_mode_event_handler("s_web_target_mid_active", self._web_hit, web="center")
        self.add_mode_event_handler("s_star_rollover_active", self._star_hit)
        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)

        for switch, saucer in self.UPPER_TARGET_SAUCERS.items():
            self.add_mode_event_handler(f"{switch}_active", self._upper_target_hit, saucer=saucer)
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(f"s_saucer_{saucer}_active", self._saucer_hit, saucer=saucer)
        for zone, switches in self.ZONE_SWITCHES.items():
            for switch in switches:
                self.add_mode_event_handler(f"{switch}_active", self._zone_hit, zone=zone)

        self.add_mode_event_handler(
            "multiball_nature_strikes_back_multiball_started",
            self._multiball_started,
        )
        self.add_mode_event_handler(
            "multiball_nature_strikes_back_multiball_ended",
            self._multiball_ended,
        )
        self.add_mode_event_handler("nature_strikes_back_complete_request", self._complete_mode)

        self._schedule_ball_guard()

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("nature_strikes_back_start_multiball")
        self._start_charge_stage()

    def mode_stop(self, **kwargs):
        self.delay.remove("nature_blotto")
        self.delay.remove("nature_ball_guard")
        self.delay.remove("nature_next_cycle")
        self.delay.remove("nature_multiball_end_check")
        for saucer in (1, 2, 3):
            self.delay.remove(f"nature_saucer_{saucer}")
        self._release_all_saucers()
        self.machine.events.post("nature_strikes_back_clear_all_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        player = self.machine.game.player if self.machine.game else None
        if player and player["mini_wizard_current_key"] == self.MODE_KEY:
            player["mini_wizard_current_key"] = ""
        super().mode_stop(**kwargs)

    # ------------------------------------------------------------------
    # Stage 1 - build charge
    # ------------------------------------------------------------------
    def _start_charge_stage(self):
        if self.mode_done:
            return
        self.stage = 1
        self.spin_count = 0
        self.webs_hit.clear()
        self.thawed_zones.clear()
        self.blocked_zones.clear()
        self.delay.remove("nature_blotto")
        self._clear_lit_saucers()
        self.machine.events.post("nature_strikes_back_stage_charge")
        self.machine.events.post("rooftop_diverter_open")
        self._show_message("BUILD THE CHARGE", f"{self._spin_goal()} SPINS", self.SPIN_VALUE)
        self._update_status()

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.stage != 1:
            return
        self.spin_count += 1
        self._score(self.SPIN_VALUE)
        self.machine.events.post("nature_strikes_back_charge_spin")
        self.machine.events.post("reset_mode_message_reminder")
        if self.spin_count >= self._spin_goal():
            self._start_snowman_stage()
        else:
            self._update_status()

    def _upper_target_hit(self, saucer=None, **kwargs):
        if self.mode_done or self.stage != 1 or saucer not in (1, 2, 3):
            return
        self.lit_saucers.add(saucer)
        self.machine.events.post(f"nature_strikes_back_saucer_{saucer}_lit")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="ADD-A-BALL LIT",
            message_mode_subtitle=f"SAUCER {saucer}",
        )
        self.machine.events.post("reset_mode_message_reminder")

    # ------------------------------------------------------------------
    # Saucers - award in stage 1, park throughout wizard
    # ------------------------------------------------------------------
    def _saucer_hit(self, saucer=None, **kwargs):
        if saucer not in (1, 2, 3):
            return

        if self.mode_done:
            self._eject_saucer(saucer)
            return

        if self.stage == 1 and saucer in self.lit_saucers:
            self._collect_lit_saucer(saucer)

        self.held_saucers.add(saucer)
        self.machine.events.post(f"nature_strikes_back_saucer_{saucer}_parked")
        self.delay.remove(f"nature_saucer_{saucer}")
        self.delay.add(
            name=f"nature_saucer_{saucer}",
            ms=self.SAUCER_HOLD_MS,
            callback=self._release_saucer,
            saucer=saucer,
        )
        self._ensure_loose_ball()

    def _collect_lit_saucer(self, saucer):
        self._clear_lit_saucers()
        if self._balls_in_play() < self.MAX_BALLS:
            self.add_a_balls += 1
            self.machine.game.player["active_mode_major_hits"] = self.add_a_balls
            self.machine.events.post("nature_strikes_back_add_a_ball")
            self.machine.events.post("nature_strikes_back_add_a_ball_collected", saucer=saucer)
            self._show_message("ADD-A-BALL", "NATURE STRIKES BACK")
        else:
            self._score(self.SAUCER_CAP_VALUE)
            self.machine.events.post("nature_strikes_back_saucer_cap_award")
            self._show_message("5 BALLS IN PLAY", "SAUCER JACKPOT", self.SAUCER_CAP_VALUE)
            self.machine.events.post("play_mode_jackpot")

    def _clear_lit_saucers(self):
        self.lit_saucers.clear()
        self.machine.events.post("nature_strikes_back_saucers_unlit")

    def _ensure_loose_ball(self):
        if self._balls_in_play() - len(self.held_saucers) >= 1:
            return
        if not self.held_saucers:
            return
        self._release_saucer(sorted(self.held_saucers)[0])

    def _release_saucer(self, saucer=None, **kwargs):
        if saucer not in (1, 2, 3):
            return
        self.delay.remove(f"nature_saucer_{saucer}")
        was_held = saucer in self.held_saucers
        self.held_saucers.discard(saucer)
        if was_held:
            self.machine.events.post(f"nature_strikes_back_saucer_{saucer}_released")
        self._eject_saucer(saucer)

    def _schedule_ball_guard(self):
        if self.mode_done:
            return
        self.delay.reset(
            name="nature_ball_guard",
            ms=250,
            callback=self._ball_guard,
        )

    def _ball_guard(self, **kwargs):
        if self.mode_done:
            return
        # The wizard survives ordinary multiball drains.  This explicit ball
        # count check is intentionally authoritative in tester mode too, where
        # the protected test ball can generate a different ball lifecycle from
        # a normal game.  Nature ends only after its multiball has genuinely
        # started and the live count has collapsed to one ball.
        if self.multiball_active and self._balls_in_play() <= 1:
            self._complete_mode()
            return
        self._ensure_loose_ball()
        self._schedule_ball_guard()

    def _multiball_started(self, **kwargs):
        self.multiball_active = True

    def _multiball_ended(self, **kwargs):
        # MPF normally posts this as the multiball drops to one ball.  Recheck
        # the actual live count instead of completing blindly so test/service
        # starts cannot terminate Nature on an intermediate drain.
        if self.mode_done or not self.multiball_active:
            return
        self.delay.reset(
            name="nature_multiball_end_check",
            ms=100,
            callback=self._check_multiball_end,
        )

    def _check_multiball_end(self, **kwargs):
        if self.mode_done or not self.multiball_active:
            return
        if self._balls_in_play() <= 1:
            self._complete_mode()

    def _release_all_saucers(self):
        for saucer in tuple(sorted(self.held_saucers)):
            self._release_saucer(saucer)

    def _eject_saucer(self, saucer):
        self.machine.events.post("request_saucer_eject", saucer_number=saucer, delay_ms=0)

    # ------------------------------------------------------------------
    # Stage 2 - discharge Snowman through both webs
    # ------------------------------------------------------------------
    def _start_snowman_stage(self):
        self.stage = 2
        self.webs_hit.clear()
        self._clear_lit_saucers()
        self.machine.events.post("nature_strikes_back_stage_snowman")
        self.machine.events.post("rooftop_diverter_close")
        self._show_message("KILL THE SNOWMAN", "CONNECT BOTH WEB TARGETS")
        self._update_status()

    def _web_hit(self, web=None, **kwargs):
        if self.mode_done or self.stage != 2 or web not in ("left", "center"):
            return
        if web in self.webs_hit:
            return
        self.webs_hit.add(web)
        value = (self.WEB_FIRST_BASE if len(self.webs_hit) == 1 else self.WEB_SECOND_BASE) + self.case_file_bonus
        self._score(value)
        self.machine.events.post(f"nature_strikes_back_web_{web}_collected")
        self.machine.events.post("play_mode_jackpot")
        self._show_message("WEB JACKPOT", f"{len(self.webs_hit)} OF 2 CONNECTED", value)
        if len(self.webs_hit) >= 2:
            self.machine.events.post("nature_strikes_back_snowman_explodes")
            self._start_thaw_stage()
        else:
            self._update_status()

    # ------------------------------------------------------------------
    # Stage 3 - thaw six zones while Blotto accumulates up to three blocks
    # ------------------------------------------------------------------
    def _start_thaw_stage(self):
        self.stage = 3
        self.thawed_zones.clear()
        self.blocked_zones.clear()
        self.machine.events.post("nature_strikes_back_stage_thaw")
        self.machine.events.post("rooftop_diverter_close")
        for zone in self.ZONE_SWITCHES:
            self._publish_zone_state(zone)
        self._schedule_blotto()
        self._show_message("SNOWMAN EXPLODED", "THAW ALL 6 ZONES")
        self._update_status()

    def _zone_hit(self, zone=None, **kwargs):
        if self.mode_done or self.stage != 3 or zone not in self.ZONE_SWITCHES:
            return
        if zone in self.blocked_zones or zone in self.thawed_zones:
            return
        self.thawed_zones.add(zone)
        value = self.ZONE_BASE + self.case_file_bonus
        self._score(value)
        self.machine.events.post(f"nature_strikes_back_zone_{zone}_thawed")
        self.machine.events.post("play_mode_jackpot")
        self._show_message("ZONE THAWED", self.ZONE_LABELS[zone], value)
        self._publish_zone_state(zone)
        if len(self.thawed_zones) >= len(self.ZONE_SWITCHES):
            self._start_stable_stage()
        else:
            self._update_status()

    def _schedule_blotto(self):
        if self.mode_done or self.stage != 3:
            return
        self.delay.reset(
            name="nature_blotto",
            ms=self._blotto_interval_ms(),
            callback=self._blotto_tick,
        )

    def _blotto_tick(self, **kwargs):
        if self.mode_done or self.stage != 3:
            return

        # Accumulate multiple Blotto blocks. Cap at three simultaneous areas
        # so the stage stays readable and the Star remains a tactical clear.
        if len(self.blocked_zones) < self.MAX_BLOTTO_BLOCKS:
            choices = [zone for zone in self.ZONE_SWITCHES if zone not in self.blocked_zones]
            if choices:
                zone = random.choice(choices)
                self.blocked_zones.add(zone)
                self._publish_zone_state(zone)
                self.machine.events.post("nature_strikes_back_blotto_blocks", zone=zone)
                self.machine.events.post(
                    "show_mode_message",
                    message_mode_title="BLOTTO BLOCKS",
                    message_mode_subtitle=self.ZONE_LABELS[zone],
                )
        self._schedule_blotto()

    def _star_hit(self, **kwargs):
        if self.mode_done or self.stage != 3:
            return
        self.delay.remove("nature_blotto")
        cleared = list(self.blocked_zones)
        self.blocked_zones.clear()
        for zone in cleared:
            self._publish_zone_state(zone)
            self.machine.events.post("nature_strikes_back_blotto_cleared", zone=zone)
        self.machine.events.post("nature_strikes_back_star_clears_blotto")
        self._show_message("BLOTTO CLEARED", "BLOCK TIMER RESET")
        self._schedule_blotto()

    def _publish_zone_state(self, zone):
        if self.stage != 3 and self.stage != 4:
            return
        if zone in self.blocked_zones:
            state = "blocked"
        elif zone in self.thawed_zones:
            state = "warm"
        else:
            state = "frozen"
        self.machine.events.post(f"nature_strikes_back_zone_{zone}_{state}")

    # ------------------------------------------------------------------
    # Stage 4 - stable city / VUK Super / next cycle
    # ------------------------------------------------------------------
    def _start_stable_stage(self):
        self.stage = 4
        self.delay.remove("nature_blotto")
        if self.blocked_zones:
            cleared = list(self.blocked_zones)
            self.blocked_zones.clear()
            for zone in cleared:
                self._publish_zone_state(zone)
        for zone in self.ZONE_SWITCHES:
            self.thawed_zones.add(zone)
            self._publish_zone_state(zone)
        self.machine.events.post("nature_strikes_back_stage_stable")
        self.machine.events.post("rooftop_diverter_open")
        self._show_message("CITY STABLE", "SHOOT DAILY BUGLE FOR SUPER")
        self._update_status()

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            self.machine.events.post("request_vuk_eject", delay_ms=0)
            return
        if self.stage != 4:
            self.machine.events.post("request_vuk_eject", delay_ms=750)
            return

        value = self.SUPER_BASE + self.case_file_bonus
        self.supers += 1
        self._score(value)
        self.machine.game.player["active_mode_hits"] = self.supers
        self.machine.events.post("play_mode_super_jackpot")
        self.machine.events.post("nature_strikes_back_super_collected", cycle=self.cycle, value=value)
        self._show_message("SUPER JACKPOT", f"CYCLE {self.cycle} COMPLETE", value)
        self.machine.events.post("request_vuk_eject", delay_ms=1_500)
        self.cycle += 1
        self.delay.reset(name="nature_next_cycle", ms=1_750, callback=self._start_charge_stage)

    # ------------------------------------------------------------------
    # Helpers / completion
    # ------------------------------------------------------------------
    def _spin_goal(self):
        index = min(self.cycle - 1, len(self.SPINS_BY_CYCLE) - 1)
        return self.SPINS_BY_CYCLE[index]

    def _blotto_interval_ms(self):
        index = min(self.cycle - 1, len(self.BLOTTO_MS_BY_CYCLE) - 1)
        return self.BLOTTO_MS_BY_CYCLE[index]

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        player["active_mode_hits"] = self.supers
        player["active_mode_major_hits"] = self.add_a_balls
        self.machine.events.post("nature_strikes_back_mode_complete")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("stop_mode_nature_strikes_back")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += int(points)
        self.mode_points += int(points)
        player["active_mode_points"] = self.mode_points

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return int(self.machine.game.balls_in_play or 0)

    def _show_message(self, title, subtitle="", value=None):
        kwargs = {
            "message_mode_title": title,
            "message_mode_subtitle": subtitle,
            "reminder": True,
        }
        if value is not None:
            kwargs["message_mode_value"] = value
        self.machine.events.post("show_mode_message", **kwargs)
        self.machine.events.post("reset_mode_message_reminder")

    def _update_status(self):
        if self.stage == 1:
            title = f"CYCLE {self.cycle} - CHARGE"
            value = f"SPINS {self.spin_count}/{self._spin_goal()}"
        elif self.stage == 2:
            title = f"CYCLE {self.cycle} - SNOWMAN"
            value = f"WEBS {len(self.webs_hit)}/2"
        elif self.stage == 3:
            title = f"CYCLE {self.cycle} - THAW CITY"
            value = f"ZONES {len(self.thawed_zones)}/6"
        else:
            title = f"CYCLE {self.cycle} - CITY STABLE"
            value = "SHOOT DAILY BUGLE"
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )
