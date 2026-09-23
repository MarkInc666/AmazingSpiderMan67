import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode


class TimeTossedShowdown(Mode):
    """Chapter 11 endurance wizard.

    Each cycle starts on the rooftop. The first 12 upper-flipper presses build
    all three possible lower phases at once; the physical rooftop exit chooses
    which one is played:
      left   -> Spider-Men
      center -> Master Vine
      right  -> Master Technician

    The mode repeats until its 3-ball multiball collapses to one ball.
    """

    MODE_KEY = "time_tossed_showdown"
    DISPLAY_NAME = "TIME-TOSSED SHOWDOWN"

    ROOFTOP_SETUP_FLIPS = 12
    MAX_BALLS = 4
    SAUCER_HOLD_MS = 15_000

    VINE_VALUE = 100_000
    VINE_MAX_SPINNER_SPINS = 20
    SPIDER_VALUE = 250_000
    TECH_BASE_SPIN_VALUE = 100_000
    TECH_UPPER_TARGET_BONUS = 10_000

    SPIDER_SHOTS = (
        {"key": "saucer_1", "switch": "s_saucer_1"},
        {"key": "saucer_2", "switch": "s_saucer_2"},
        {"key": "saucer_3", "switch": "s_saucer_3"},
        {"key": "star", "switch": "s_star_rollover"},
        {"key": "upper_a", "switch": "s_inlane_a"},
        {"key": "upper_b", "switch": "s_inlane_b"},
    )

    # Same lower-playfield shot pool as standalone Master Vine. Star is always
    # spotted by this wizard, so rooftop upper-spinner spins select only from
    # the remaining shots (capped at 20 by design).
    VINE_SHOTS = (
        "left_web", "center_web", "left_sling", "right_sling",
        "left_pop", "right_pop", "saucer_1", "saucer_2", "saucer_3",
        "left_drop_1", "left_drop_2", "left_drop_3",
        "right_drop_1", "right_drop_2", "right_drop_3",
        "right_drop_4", "right_drop_5", "a", "b", "middle_a",
        "middle_b", "star",
    )

    VINE_SWITCHES = {
        "left_web": "s_web_target_left_active",
        "center_web": "s_web_target_mid_active",
        "left_sling": "s_sling_l_active",
        "right_sling": "s_sling_r_active",
        "left_pop": "s_pop_left_active",
        "right_pop": "s_pop_right_active",
        "saucer_1": "s_saucer_1_active",
        "saucer_2": "s_saucer_2_active",
        "saucer_3": "s_saucer_3_active",
        "left_drop_1": "s_left_drops_1_active",
        "left_drop_2": "s_left_drops_2_active",
        "left_drop_3": "s_left_drops_3_active",
        "right_drop_1": "s_right_drops_1_active",
        "right_drop_2": "s_right_drops_2_active",
        "right_drop_3": "s_right_drops_3_active",
        "right_drop_4": "s_right_drops_4_active",
        "right_drop_5": "s_right_drops_5_active",
        "a": "s_inlane_a_active",
        "b": "s_inlane_b_active",
        "middle_a": "s_inlane_m_r_active",
        "middle_b": "s_inlane_m_l_active",
        "star": "s_star_rollover_active",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.multiball_active = False
        self.phase = "starting"
        self.mode_points = 0
        self.jackpots = 0
        self.phases_completed = 0
        self.held_saucers = []

        # Rooftop setup state.
        self.roof_visit_active = False
        self.roof_flips_used = 0
        self.roof_upper_target_hits = 0
        self.roof_unique_targets = set()
        self.roof_spinner_spins = 0

        # Lower-phase state.
        self.vine_lit = set()
        self.spider_pattern = [False] * len(self.SPIDER_SHOTS)
        self.tech_star_available = False
        self.tech_spin_value = self.TECH_BASE_SPIN_VALUE

        player = self.machine.game.player
        self.case_file_bonus = int(player["mini_wizard_case_file_bonus"] or 0)
        player["mini_wizard_current_key"] = self.MODE_KEY
        player[f"{self.MODE_KEY}_state"] = 1
        player[f"{self.MODE_KEY}_case_file_bonus"] = self.case_file_bonus
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_stat_1"] = 0
        player["active_mode_stat_2"] = 0

        self._register_handlers()

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.machine.events.post("time_tossed_showdown_clear_all")
        self.machine.events.post("time_tossed_showdown_start_multiball")
        self._start_rooftop_phase()

    def mode_stop(self, **kwargs):
        self.delay.clear()
        self._release_all_saucers()
        self.machine.events.post("time_tossed_showdown_clear_all")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        player = self.machine.game.player if self.machine.game else None
        if player and player["mini_wizard_current_key"] == self.MODE_KEY:
            player["mini_wizard_current_key"] = ""
        super().mode_stop(**kwargs)

    def _register_handlers(self):
        # Rooftop setup / selection.
        self.add_mode_event_handler("s_upper_entrance_opto_active", self._upper_entrance)
        self.add_mode_event_handler("s_right_flipper_upper_active", self._upper_flipper)
        self.add_mode_event_handler("s_upper_target_left_active", self._roof_target_hit, target="left")
        self.add_mode_event_handler("s_upper_target_center_active", self._roof_target_hit, target="center")
        self.add_mode_event_handler("s_upper_target_right_active", self._roof_target_hit, target="right")
        self.add_mode_event_handler("s_trispinner_opto_active", self._roof_spinner_hit)
        self.add_mode_event_handler("s_upper_exit_left_opto_active", self._select_exit, exit_name="left")
        self.add_mode_event_handler("s_upper_exit_right_opto_active", self._select_exit, exit_name="right")
        # There is no physical center-exit switch. These two switches are the
        # established center-drain inference used elsewhere in the game.
        self.add_mode_event_handler("s_right_drops_top_rubber_active", self._select_exit, exit_name="center")
        self.add_mode_event_handler("s_inlane_m_r_active", self._select_exit, exit_name="center")

        # Spider-Men rotation and collection.
        self.add_mode_event_handler("s_left_flipper_active", self._spider_rotate_left)
        self.add_mode_event_handler("s_right_flipper_active", self._spider_rotate_right)
        for index, shot in enumerate(self.SPIDER_SHOTS):
            self.add_mode_event_handler(shot["switch"] + "_active", self._spider_shot_hit, index=index)

        # Master Vine uses the exact standalone shot pool.
        for shot, event in self.VINE_SWITCHES.items():
            self.add_mode_event_handler(event, self._vine_shot_hit, shot=shot)

        # Master Technician.
        self.add_mode_event_handler("s_web_spinner_active", self._tech_spinner_hit)
        self.add_mode_event_handler("s_left_drops_1_active", self._tech_danger_drop_hit)
        self.add_mode_event_handler("s_star_rollover_active", self._tech_star_hit)

        # Saucers park in every phase.
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(f"s_saucer_{saucer}_active", self._saucer_seen, saucer=saucer)

        self.add_mode_event_handler(
            "multiball_time_tossed_showdown_multiball_started",
            self._multiball_started,
        )
        self.add_mode_event_handler(
            "multiball_time_tossed_showdown_multiball_ended",
            self._multiball_ended,
        )
        self.add_mode_event_handler("time_tossed_showdown_complete_request", self._complete_mode)

    # ------------------------------------------------------------------
    # Rooftop setup / phase selection
    # ------------------------------------------------------------------
    def _start_rooftop_phase(self):
        if self.mode_done:
            return
        self.phase = "rooftop"
        self.roof_visit_active = False
        self.roof_flips_used = 0
        self.roof_upper_target_hits = 0
        self.roof_unique_targets.clear()
        self.roof_spinner_spins = 0
        self.vine_lit.clear()
        self.spider_pattern = [False] * len(self.SPIDER_SHOTS)
        self.tech_star_available = False

        self.machine.events.post("time_tossed_showdown_clear_phase_lights")
        self.machine.events.post("time_tossed_showdown_rooftop")
        self.machine.events.post("rooftop_diverter_open")
        # Restore physical drops after any previous Technician/Vine visit.
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self._show_message(
            "TIME PORTAL OPEN",
            "L SPIDER-MEN / C VINE / R TECH",
            value=f"{self.ROOFTOP_SETUP_FLIPS} SETUP FLIPS",
            reminder=True,
        )
        self._update_status()

    def _upper_entrance(self, **kwargs):
        if self.mode_done or self.phase != "rooftop":
            return
        self.roof_visit_active = True
        self.machine.events.post("time_tossed_showdown_roof_setup_active")
        self._update_status()

    def _upper_flipper(self, **kwargs):
        if self.mode_done or self.phase != "rooftop" or not self.roof_visit_active:
            return
        if self.roof_flips_used >= self.ROOFTOP_SETUP_FLIPS:
            return
        self.roof_flips_used += 1
        if self.roof_flips_used >= self.ROOFTOP_SETUP_FLIPS:
            self.machine.events.post("time_tossed_showdown_roof_setup_locked")
            self._show_message("SETUP LOCKED", "EXIT CHOOSES THE ERA", reminder=True)
        self._update_status()

    def _setup_window_open(self):
        return (
            not self.mode_done
            and self.phase == "rooftop"
            and self.roof_visit_active
            and self.roof_flips_used < self.ROOFTOP_SETUP_FLIPS
        )

    def _roof_target_hit(self, target=None, **kwargs):
        if not self._setup_window_open() or target not in ("left", "center", "right"):
            return
        self.roof_upper_target_hits += 1
        self.roof_unique_targets.add(target)
        self.machine.events.post(
            "time_tossed_showdown_roof_target_build",
            target=target,
            hits=self.roof_upper_target_hits,
        )
        self._update_status()

    def _roof_spinner_hit(self, **kwargs):
        if not self._setup_window_open():
            return
        if self.roof_spinner_spins < self.VINE_MAX_SPINNER_SPINS:
            self.roof_spinner_spins += 1
            self.machine.events.post(
                "time_tossed_showdown_roof_spinner_build",
                spins=self.roof_spinner_spins,
            )
            self._update_status()

    def _select_exit(self, exit_name=None, **kwargs):
        if (
            self.mode_done
            or self.phase != "rooftop"
            or not self.roof_visit_active
            or exit_name not in ("left", "center", "right")
        ):
            return

        # First valid exit wins. Closing the gate and changing phase prevents
        # later switch bounces from reclassifying the same rooftop visit.
        self.roof_visit_active = False
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("time_tossed_showdown_rooftop_off")

        if exit_name == "left":
            self._start_spider_phase()
        elif exit_name == "center":
            self._start_vine_phase()
        else:
            self._start_technician_phase()

    # ------------------------------------------------------------------
    # Spider-Men phase
    # ------------------------------------------------------------------
    def _start_spider_phase(self):
        self.phase = "spider_men"
        # Initial pattern: Star is always lit; unique upper targets add their
        # corresponding saucer. The entire six-position boolean pattern then
        # rotates with the flippers exactly like standalone Spider-Men.
        self.spider_pattern = [
            "left" in self.roof_unique_targets,
            "center" in self.roof_unique_targets,
            "right" in self.roof_unique_targets,
            True,
            False,
            False,
        ]
        self.machine.events.post("time_tossed_showdown_phase_spider")
        self._refresh_spider_lights()
        self._show_message(
            "THE SPIDER-MEN",
            "FLIPPERS ROTATE THE JACKPOTS",
            value=self._spider_value(),
            reminder=True,
        )
        self._update_status()

    def _spider_rotate_left(self, **kwargs):
        if self.mode_done or self.phase != "spider_men":
            return
        self.spider_pattern = self.spider_pattern[1:] + self.spider_pattern[:1]
        self._refresh_spider_lights()

    def _spider_rotate_right(self, **kwargs):
        if self.mode_done or self.phase != "spider_men":
            return
        self.spider_pattern = self.spider_pattern[-1:] + self.spider_pattern[:-1]
        self._refresh_spider_lights()

    def _spider_shot_hit(self, index=None, **kwargs):
        if self.mode_done or self.phase != "spider_men" or index is None:
            return
        if not self.spider_pattern[index]:
            return

        self.spider_pattern[index] = False
        value = self._spider_value()
        self._award_jackpot(value, "SPIDER-MEN JACKPOT")
        self._refresh_spider_lights()

        if not any(self.spider_pattern):
            self._phase_complete("SPIDER-MEN CLEARED")
        else:
            self._update_status()

    def _refresh_spider_lights(self):
        self.machine.events.post("time_tossed_showdown_spider_all_off")
        for index, lit in enumerate(self.spider_pattern):
            if lit:
                key = self.SPIDER_SHOTS[index]["key"]
                self.machine.events.post(f"time_tossed_showdown_spider_{key}_lit")

    def _spider_value(self):
        return self.SPIDER_VALUE + self.case_file_bonus

    # ------------------------------------------------------------------
    # Master Vine phase
    # ------------------------------------------------------------------
    def _start_vine_phase(self):
        self.phase = "vine"
        non_star = [shot for shot in self.VINE_SHOTS if shot != "star"]
        extra_count = min(self.roof_spinner_spins, self.VINE_MAX_SPINNER_SPINS, len(non_star))
        selected = random.sample(non_star, extra_count) if extra_count else []
        self.vine_lit = {"star", *selected}

        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("time_tossed_showdown_phase_vine")
        self._refresh_vine_lights()
        self._show_message(
            "MASTER VINE",
            f"COLLECT {len(self.vine_lit)} GREEN SHOTS",
            value=self._vine_value(),
            reminder=True,
        )
        self._update_status()

    def _vine_shot_hit(self, shot=None, **kwargs):
        if self.mode_done or self.phase != "vine" or shot not in self.vine_lit:
            return
        self.vine_lit.discard(shot)
        self._award_jackpot(self._vine_value(), "VINE JACKPOT")
        self._refresh_vine_lights()

        if not self.vine_lit:
            self._phase_complete("VINES CLEARED")
        else:
            self._update_status()

    def _refresh_vine_lights(self):
        self.machine.events.post("time_tossed_showdown_vine_all_off")
        for shot in self.vine_lit:
            self.machine.events.post(f"time_tossed_showdown_vine_{shot}_lit")

    def _vine_value(self):
        return self.VINE_VALUE + self.case_file_bonus

    # ------------------------------------------------------------------
    # Master Technician phase
    # ------------------------------------------------------------------
    def _start_technician_phase(self):
        self.phase = "technician_staging"
        self.tech_spin_value = (
            self.TECH_BASE_SPIN_VALUE
            + self.case_file_bonus
            + (self.roof_upper_target_hits * self.TECH_UPPER_TARGET_BONUS)
        )
        self.tech_star_available = True
        self.machine.events.post("time_tossed_showdown_phase_technician")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.delay.reset(
            name="time_tossed_tech_stage",
            ms=400,
            callback=self._finish_technician_staging,
        )
        self._show_message(
            "MASTER TECHNICIAN",
            "STAGING MACHINE AGE",
            value=self.tech_spin_value,
            reminder=True,
        )
        self._update_status()

    def _finish_technician_staging(self, **kwargs):
        if self.mode_done or self.phase != "technician_staging":
            return

        # Verify the reset took physically before staging the one standing
        # danger target. This avoids delayed-reset races seen in other modes.
        if not self._all_drop_targets_up():
            self.machine.events.post("drop_target_bank_dt_bank_left_reset")
            self.machine.events.post("drop_target_bank_dt_bank_right_reset")
            self.delay.reset(
                name="time_tossed_tech_stage",
                ms=300,
                callback=self._finish_technician_staging,
            )
            return

        for name in (
            "dt_left_2", "dt_left_3",
            "dt_right_1", "dt_right_2", "dt_right_3", "dt_right_4", "dt_right_5",
        ):
            device = self.machine.drop_targets.get(name)
            if device:
                device.knockdown()

        self.phase = "technician"
        self.machine.events.post("time_tossed_showdown_tech_ready")
        self._show_message(
            "MASTER TECHNICIAN",
            "SPIN - AVOID THE STANDING DROP",
            value=self.tech_spin_value,
            reminder=True,
        )
        self._update_status()

    def _all_drop_targets_up(self):
        for name in (
            "s_left_drops_1", "s_left_drops_2", "s_left_drops_3",
            "s_right_drops_1", "s_right_drops_2", "s_right_drops_3",
            "s_right_drops_4", "s_right_drops_5",
        ):
            switch = self.machine.switches.get(name)
            if switch and self.machine.switch_controller.is_active(switch):
                return False
        return True

    def _tech_spinner_hit(self, **kwargs):
        if self.mode_done or self.phase != "technician":
            return
        self._score(self.tech_spin_value)
        self.machine.events.post("time_tossed_showdown_tech_spinner_scored", value=self.tech_spin_value)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="TECH SPINNER",
            message_mode_subtitle="KEEP SPINNING",
            message_mode_value=self.tech_spin_value,
        )
        self._update_status()

    def _tech_danger_drop_hit(self, **kwargs):
        if self.mode_done or self.phase != "technician":
            return
        self._phase_complete("MACHINE AGE ENDED")

    def _tech_star_hit(self, **kwargs):
        if self.mode_done or self.phase != "technician" or not self.tech_star_available:
            return
        if self._balls_in_play() < self.MAX_BALLS:
            self.tech_star_available = False
            self.machine.events.post("time_tossed_showdown_add_a_ball")
            self.machine.events.post("time_tossed_showdown_tech_star_consumed")
            self._show_message("ADD-A-BALL", "STAR COLLECTED", reminder=True)
        else:
            # At the cap the Star behaves like another spinner shot and remains
            # lit. If a ball later drains, the same Star can still add a ball.
            self._score(self.tech_spin_value)
            self.machine.events.post("time_tossed_showdown_tech_star_score", value=self.tech_spin_value)
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="STAR SPIN VALUE",
                message_mode_subtitle="4 BALL MAX - STAR STAYS LIT",
                message_mode_value=self.tech_spin_value,
            )
        self._update_status()

    # ------------------------------------------------------------------
    # Saucer parking
    # ------------------------------------------------------------------
    def _saucer_seen(self, saucer=None, **kwargs):
        if self.mode_done or saucer not in (1, 2, 3):
            return
        if saucer in self.held_saucers:
            return
        self.held_saucers.append(saucer)
        self.delay.reset(
            name=f"time_tossed_saucer_{saucer}",
            ms=self.SAUCER_HOLD_MS,
            callback=self._release_saucer,
            saucer=saucer,
        )
        self.machine.events.post(f"time_tossed_showdown_saucer_{saucer}_parked")
        self._ensure_free_ball()

    def _release_saucer(self, saucer=None, **kwargs):
        if saucer not in self.held_saucers:
            return
        self.held_saucers.remove(saucer)
        self.delay.remove(f"time_tossed_saucer_{saucer}")
        self.machine.events.post(f"time_tossed_showdown_saucer_{saucer}_released")
        self.machine.events.post("request_saucer_eject", saucer_number=saucer, delay_ms=0)

    def _release_all_saucers(self):
        for saucer in list(self.held_saucers):
            self._release_saucer(saucer)

    def _ensure_free_ball(self):
        if self._balls_in_play() - len(self.held_saucers) >= 1:
            return
        if self.held_saucers:
            # List order is parking order: oldest ball is released first.
            self._release_saucer(self.held_saucers[0])

    # ------------------------------------------------------------------
    # Common phase / mode flow
    # ------------------------------------------------------------------
    def _phase_complete(self, title):
        if self.mode_done or self.phase in ("rooftop", "phase_complete"):
            return
        self.phase = "phase_complete"
        self.phases_completed += 1
        self._sync_vars()
        self.machine.events.post("time_tossed_showdown_clear_phase_lights")
        self._show_message(title, "TIME SHIFT!", reminder=False)
        self.delay.reset(
            name="time_tossed_next_rooftop",
            ms=1_000,
            callback=self._start_rooftop_phase,
        )

    def _multiball_started(self, **kwargs):
        self.multiball_active = True

    def _multiball_ended(self, **kwargs):
        if self.mode_done or not self.multiball_active:
            return
        self.multiball_active = False
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars()
        self.machine.events.post("time_tossed_showdown_mode_complete")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("stop_mode_time_tossed_showdown")

    # ------------------------------------------------------------------
    # Scoring / status
    # ------------------------------------------------------------------
    def _award_jackpot(self, points, title):
        self._score(points)
        self.jackpots += 1
        self._sync_vars()
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle="TIME JACKPOT",
            message_mode_value=points,
        )
        self._update_status()

    def _score(self, points):
        points = int(points)
        self.machine.game.player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.jackpots
        player["active_mode_stat_1"] = self.phases_completed
        player["active_mode_stat_2"] = self.roof_upper_target_hits
        player[f"{self.MODE_KEY}_case_file_bonus"] = self.case_file_bonus

    def _update_status(self):
        if self.mode_done:
            return
        if self.phase == "rooftop":
            flips_left = max(0, self.ROOFTOP_SETUP_FLIPS - self.roof_flips_used)
            title = "TIME PORTAL"
            value = (
                f"{flips_left} FLIPS | TGT {self.roof_upper_target_hits} | "
                f"VINE {self.roof_spinner_spins}"
            )
        elif self.phase == "spider_men":
            title = "SPIDER-MEN"
            value = f"{sum(1 for lit in self.spider_pattern if lit)} JACKPOTS LEFT"
        elif self.phase == "vine":
            title = "MASTER VINE"
            value = f"{len(self.vine_lit)} GREEN SHOTS LEFT"
        elif self.phase == "technician_staging":
            title = "MASTER TECHNICIAN"
            value = "STAGING DROPS"
        elif self.phase == "technician":
            title = "MASTER TECHNICIAN"
            value = f"SPIN {self.tech_spin_value:,}"
        else:
            title = "TIME SHIFT"
            value = f"{self.phases_completed} PHASES"
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _show_message(self, title, subtitle="", value="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            reminder=reminder,
        )
        if reminder:
            self.machine.events.post("reset_mode_message_reminder")

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return int(self.machine.game.balls_in_play or 0)
