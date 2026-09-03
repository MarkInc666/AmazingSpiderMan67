import math
import random

from mpf.core.mode import Mode


class MastermindTrap(Mode):
    """Chapter 2 mini-wizard: three mixed phases plus a timed Super.

    The mode starts 2-ball multiball and cycles until multiball ends:
      1. Parafino + Scorpion: park balls in saucers, choose rooftop exits,
         then collect the staged lower-playfield jackpot. Matching the held
         saucer to the chosen exit makes the jackpot 3X. Three roof attempts.
      2. Lizard + Mysterio: two pop hits make serum, then find the real
         delivery among Mysterio illusions. Three successful deliveries.
      3. Doctor Octopus: spinner scores while six red danger shots rotate and
         accumulate. Inlanes light 3X spinner for six seconds. Three red hits
         end the phase.
      4. Super: either web target collects a value falling from 2M to 100K in
         eight seconds, then holding at 100K for two seconds.
    """

    MODE_KEY = "mastermind_trap"
    DISPLAY_NAME = "Mastermind Trap"

    MAX_BALLS = 4
    PARA_ATTEMPTS_REQUIRED = 3
    PARA_JACKPOT = 300_000
    PARA_MATCH_MULTIPLIER = 3
    ROOF_CENTER_TIMEOUT_MS = 6_000

    LIZARD_SERUM_POP_HITS = 2
    LIZARD_DELIVERIES_REQUIRED = 3
    LIZARD_POP_VALUE = 25_000
    LIZARD_WRONG_VALUE = 50_000
    LIZARD_DELIVERY_JACKPOT = 500_000

    DOC_SPINNER_VALUE = 50_000
    DOC_UNLIT_VALUE = 50_000
    DOC_RED_VALUE = 1_000
    DOC_STRIKES_TO_END = 3
    DOC_ROTATE_MS = 1_000
    DOC_3X_MS = 6_000

    SUPER_START = 2_000_000
    SUPER_FLOOR = 100_000
    SUPER_COUNTDOWN_MS = 8_000
    SUPER_HOLD_MS = 2_000
    SUPER_TICK_MS = 100

    SAUCER_TO_AREA = {1: "left_bank", 2: "pops", 3: "right_bank"}
    EXIT_TO_AREA = {"left": "right_bank", "center": "pops", "right": "left_bank"}
    AREA_LABELS = {"left_bank": "LEFT BANK", "pops": "POPS", "right_bank": "RIGHT BANK"}

    LIZARD_CANDIDATES = ("left_web", "left_bank", "right_bank", "upper")
    LIZARD_LABELS = {
        "left_web": "LEFT WEB",
        "left_bank": "LEFT BANK",
        "right_bank": "RIGHT BANK",
        "upper": "UPPER TARGETS",
    }
    LIZARD_DIRECTIONS = {
        "left_web": "LEFT",
        "left_bank": "LEFT",
        "right_bank": "RIGHT",
        "upper": "UPPER",
    }

    DOC_SHOTS = ("upper_left", "upper_center", "upper_right", "star", "upper_a", "upper_b")

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.phase = "para_scorpion"
        self.cycle = 1

        self.held_saucers = set()
        self.roof_active = False
        self.para_attempts = 0
        self.para_upper_targets = set()
        self.staged_area = None
        self.staged_multiplier = 1

        self.serum_hits = 0
        self.deliveries = 0
        self.delivery_candidates = set()
        self.delivery_correct = None

        self.doc_permanent_red = set()
        self.doc_rotating_red = None
        self.doc_rotation_index = -1
        self.doc_strikes = 0
        self.doc_spins = 0
        self.doc_3x_active = False
        self.doc_3x_remaining = 0

        self.super_value = self.SUPER_START
        self.super_elapsed_ms = 0

        self._reset_player_vars()
        self._add_switch_handlers()
        self.add_mode_event_handler(f"{self.MODE_KEY}_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler(f"{self.MODE_KEY}_complete_request", self._complete_mode)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post(f"{self.MODE_KEY}_start_multiball")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        self._post_message("MASTERMIND TRAP", "PARAFINO + SCORPION", "PARK A BALL")
        self._start_para_scorpion()

    def mode_stop(self, **kwargs):
        self._clear_delays()
        self._release_all_saucers()
        player = self.machine.game.player
        if player["mini_wizard_current_key"] == self.MODE_KEY:
            player["mini_wizard_current_key"] = ""
        self.machine.events.post(f"{self.MODE_KEY}_clear_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("hide_mode_status")
        super().mode_stop(**kwargs)

    def _add_switch_handlers(self):
        self.add_mode_event_handler("s_saucer_1_active", self._saucer_hit, saucer=1)
        self.add_mode_event_handler("s_saucer_2_active", self._saucer_hit, saucer=2)
        self.add_mode_event_handler("s_saucer_3_active", self._saucer_hit, saucer=3)

        self.add_mode_event_handler("s_upper_entrance_opto_active", self._upper_entry)
        self.add_mode_event_handler("s_upper_exit_left_opto_active", self._upper_exit, side="left")
        self.add_mode_event_handler("s_upper_exit_right_opto_active", self._upper_exit, side="right")
        self.add_mode_event_handler("s_upper_target_left_active", self._upper_target, target="left")
        self.add_mode_event_handler("s_upper_target_center_active", self._upper_target, target="center")
        self.add_mode_event_handler("s_upper_target_right_active", self._upper_target, target="right")

        self.add_mode_event_handler("s_pop_left_active", self._pop_hit)
        self.add_mode_event_handler("s_pop_right_active", self._pop_hit)
        self.add_mode_event_handler("s_web_target_left_active", self._left_web_hit)
        self.add_mode_event_handler("s_web_target_mid_active", self._mid_web_hit)

        for num in range(1, 4):
            self.add_mode_event_handler(f"s_left_drops_{num}_active", self._left_bank_hit)
        for num in range(1, 6):
            self.add_mode_event_handler(f"s_right_drops_{num}_active", self._right_bank_hit)

        self.add_mode_event_handler("s_web_spinner_active", self._main_spinner_hit)
        self.add_mode_event_handler("s_inlane_l_active", self._doc_inlane)
        self.add_mode_event_handler("s_inlane_r_active", self._doc_inlane)
        self.add_mode_event_handler("s_star_rollover_active", self._doc_danger_hit, shot="star")
        self.add_mode_event_handler("s_inlane_a_active", self._doc_danger_hit, shot="upper_a")
        self.add_mode_event_handler("s_inlane_b_active", self._doc_danger_hit, shot="upper_b")

        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)

    # ------------------------------------------------------------------
    # Phase 1: Parafino + Scorpion
    # ------------------------------------------------------------------
    def _start_para_scorpion(self):
        if self.mode_done:
            return
        self.phase = "para_scorpion"
        self.para_attempts = 0
        self.para_upper_targets.clear()
        self.staged_area = None
        self.staged_multiplier = 1
        self.roof_active = False
        self._release_all_saucers()
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post(f"{self.MODE_KEY}_phase_para")
        self._sync_status("PARK A BALL", "SAUCER -> ROOF")

    def _saucer_hit(self, saucer, **kwargs):
        if self.mode_done:
            return
        if self.phase != "para_scorpion":
            self.machine.events.post(f"delayed_kickout_saucer_{saucer}")
            return

        balls = self._balls_in_play()
        # Always preserve at least one playable ball. A last live ball may enter
        # a saucer, but it is immediately returned instead of being parked.
        if saucer not in self.held_saucers and len(self.held_saucers) >= max(0, balls - 1):
            self.machine.events.post(f"delayed_kickout_saucer_{saucer}")
            return

        self.held_saucers.add(saucer)
        self.machine.events.post(f"{self.MODE_KEY}_saucer_{saucer}_held")
        self.machine.events.post("rooftop_diverter_open")
        areas = ", ".join(self.AREA_LABELS[self.SAUCER_TO_AREA[s]] for s in sorted(self.held_saucers))
        self._sync_status("ROOF OPEN", areas)

    def _upper_entry(self, **kwargs):
        if self.phase != "para_scorpion" or not self.held_saucers or self.staged_area:
            return
        self.roof_active = True
        self.machine.events.post(f"{self.MODE_KEY}_roof_choice_on")
        self.delay.reset(
            name="mastermind_roof_center",
            ms=self.ROOF_CENTER_TIMEOUT_MS,
            callback=self._roof_center_timeout,
        )
        self._sync_status("CHOOSE ROOF EXIT", "L / CENTER / R")

    def _upper_exit(self, side, **kwargs):
        if self.phase != "para_scorpion" or not self.roof_active or self.staged_area:
            return
        self._stage_para_area(side)

    def _roof_center_timeout(self):
        if self.phase == "para_scorpion" and self.roof_active and not self.staged_area:
            self._stage_para_area("center")

    def _stage_para_area(self, exit_name):
        self.delay.remove("mastermind_roof_center")
        self.roof_active = False
        self.machine.events.post(f"{self.MODE_KEY}_roof_choice_off")
        self.staged_area = self.EXIT_TO_AREA[exit_name]
        matching_saucer = next(
            (s for s, area in self.SAUCER_TO_AREA.items() if area == self.staged_area), None
        )
        self.staged_multiplier = (
            self.PARA_MATCH_MULTIPLIER if matching_saucer in self.held_saucers else 1
        )
        self.machine.events.post(f"{self.MODE_KEY}_para_stage_{self.staged_area}")
        suffix = "3X" if self.staged_multiplier == 3 else "1X"
        self._sync_status(f"{self.AREA_LABELS[self.staged_area]} JACKPOT", suffix)

    def _collect_para_area(self, area):
        if self.phase != "para_scorpion" or self.staged_area != area:
            return False
        value = self.PARA_JACKPOT * self.staged_multiplier
        self._score(value, major=True)
        self.para_attempts += 1
        self._set(f"{self.MODE_KEY}_para_attempts", self.para_attempts)
        self.machine.events.post(f"{self.MODE_KEY}_para_area_collected", area=area)
        self._post_message(
            "3X JACKPOT" if self.staged_multiplier == 3 else "JACKPOT",
            self.AREA_LABELS[area],
            value,
        )
        self.staged_area = None
        self.staged_multiplier = 1
        self._release_all_saucers()
        self.machine.events.post("rooftop_diverter_close")
        if self.para_attempts >= self.PARA_ATTEMPTS_REQUIRED:
            self.delay.reset(name="mastermind_next_phase", ms=1_500, callback=self._start_lizard_mysterio)
        else:
            self.delay.reset(name="mastermind_next_attempt", ms=1_000, callback=self._next_para_attempt)
        return True

    def _next_para_attempt(self):
        if self.phase != "para_scorpion":
            return
        self.machine.events.post(f"{self.MODE_KEY}_phase_para")
        self._sync_status("PARK A BALL", f"ROOF ATTEMPT {self.para_attempts + 1}/3")

    def _upper_target(self, target, **kwargs):
        if self.phase == "para_scorpion":
            self.para_upper_targets.add(target)
            if len(self.para_upper_targets) >= 3:
                self.para_upper_targets.clear()
                if self._balls_in_play() < self.MAX_BALLS:
                    self.machine.events.post(f"{self.MODE_KEY}_add_a_ball")
                    self._post_message("ADD-A-BALL", "UPPER TARGETS COMPLETE", "")
                else:
                    self._post_message("4 BALLS MAX", "UPPER TARGETS COMPLETE", "")
            return
        if self.phase == "lizard_mysterio":
            self._delivery_shot("upper")
            return
        if self.phase == "doc_ock":
            mapping = {"left": "upper_left", "center": "upper_center", "right": "upper_right"}
            self._doc_danger_hit(shot=mapping[target])

    # ------------------------------------------------------------------
    # Phase 2: Lizard + Mysterio
    # ------------------------------------------------------------------
    def _start_lizard_mysterio(self):
        if self.mode_done:
            return
        self.phase = "lizard_mysterio"
        self.deliveries = 0
        self.serum_hits = 0
        self.delivery_candidates.clear()
        self.delivery_correct = None
        self._release_all_saucers()
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post(f"{self.MODE_KEY}_phase_lizard")
        self._sync_status("MAKE SERUM", "HIT POPS 0/2")

    def _pop_hit(self, **kwargs):
        if self.mode_done:
            return
        if self.phase == "para_scorpion" and self._collect_para_area("pops"):
            return
        if self.phase != "lizard_mysterio" or self.delivery_candidates:
            return
        self._score(self.LIZARD_POP_VALUE)
        self.serum_hits += 1
        if self.serum_hits >= self.LIZARD_SERUM_POP_HITS:
            self._start_delivery_search()
        else:
            self._sync_status("MAKE SERUM", f"HIT POPS {self.serum_hits}/2")

    def _start_delivery_search(self):
        self.serum_hits = 0
        self.delivery_candidates = set(self.LIZARD_CANDIDATES)
        self.delivery_correct = random.choice(self.LIZARD_CANDIDATES)
        self.machine.events.post(f"{self.MODE_KEY}_delivery_all_on")
        self._post_message("SERUM READY", "MYSTERIO HIDES THE TARGET", "FIND DELIVERY")
        self._sync_status("DELIVER SERUM", f"{self.deliveries + 1}/3")

    def _delivery_shot(self, candidate):
        if self.phase != "lizard_mysterio" or candidate not in self.delivery_candidates:
            return
        if candidate == self.delivery_correct:
            self._score(self.LIZARD_DELIVERY_JACKPOT, major=True)
            self.deliveries += 1
            self._set(f"{self.MODE_KEY}_deliveries", self.deliveries)
            self.machine.events.post(f"{self.MODE_KEY}_delivery_clear")
            self._post_message("SERUM DELIVERED", self.LIZARD_LABELS[candidate], self.LIZARD_DELIVERY_JACKPOT)
            self.delivery_candidates.clear()
            self.delivery_correct = None
            if self.deliveries >= self.LIZARD_DELIVERIES_REQUIRED:
                self.delay.reset(name="mastermind_next_phase", ms=1_500, callback=self._start_doc_ock)
            else:
                self.delay.reset(name="mastermind_next_serum", ms=1_000, callback=self._next_serum)
            return

        self._score(self.LIZARD_WRONG_VALUE)
        self.delivery_candidates.remove(candidate)
        self.machine.events.post(f"{self.MODE_KEY}_delivery_{candidate}_off")
        clue = self.LIZARD_DIRECTIONS[self.delivery_correct]
        self._post_message("ILLUSION!", f"SPIDEY SENSE: {clue}", self.LIZARD_WRONG_VALUE)
        self._sync_status("DELIVER SERUM", f"{len(self.delivery_candidates)} POSSIBLE")

    def _next_serum(self):
        if self.phase != "lizard_mysterio":
            return
        self._sync_status("MAKE SERUM", "HIT POPS 0/2")

    def _left_web_hit(self, **kwargs):
        if self.phase == "lizard_mysterio":
            self._delivery_shot("left_web")
        elif self.phase == "super":
            self._collect_super()

    def _mid_web_hit(self, **kwargs):
        if self.phase == "super":
            self._collect_super()

    def _left_bank_hit(self, **kwargs):
        if self.phase == "para_scorpion":
            if self._collect_para_area("left_bank"):
                return
        elif self.phase == "lizard_mysterio":
            self._delivery_shot("left_bank")
            self.machine.events.post("drop_target_bank_dt_bank_left_reset")

    def _right_bank_hit(self, **kwargs):
        if self.phase == "para_scorpion":
            if self._collect_para_area("right_bank"):
                return
        elif self.phase == "lizard_mysterio":
            self._delivery_shot("right_bank")
            self.machine.events.post("drop_target_bank_dt_bank_right_reset")

    # ------------------------------------------------------------------
    # Phase 3: Doctor Octopus
    # ------------------------------------------------------------------
    def _start_doc_ock(self):
        if self.mode_done:
            return
        self.phase = "doc_ock"
        self.doc_permanent_red.clear()
        self.doc_rotating_red = None
        self.doc_rotation_index = -1
        self.doc_strikes = 0
        self.doc_spins = 0
        self.doc_3x_active = False
        self.doc_3x_remaining = 0
        self.machine.events.post(f"{self.MODE_KEY}_delivery_clear")
        self.machine.events.post(f"{self.MODE_KEY}_phase_doc")
        self._rotate_doc_danger()
        self._sync_status("DOC OCK", "SPIN - AVOID RED")

    def _rotate_doc_danger(self):
        if self.phase != "doc_ock" or self.mode_done:
            return
        self.doc_rotation_index = (self.doc_rotation_index + 1) % len(self.DOC_SHOTS)
        self.doc_rotating_red = self.DOC_SHOTS[self.doc_rotation_index]
        self._refresh_doc_lights()
        self.delay.reset(name="mastermind_doc_rotate", ms=self.DOC_ROTATE_MS, callback=self._rotate_doc_danger)

    def _refresh_doc_lights(self):
        for shot in self.DOC_SHOTS:
            is_red = shot in self.doc_permanent_red or shot == self.doc_rotating_red
            self.machine.events.post(f"{self.MODE_KEY}_doc_{shot}_{'red' if is_red else 'off'}")

    def _doc_danger_hit(self, shot=None, **kwargs):
        if self.phase != "doc_ock" or shot not in self.DOC_SHOTS:
            return
        is_red = shot in self.doc_permanent_red or shot == self.doc_rotating_red
        if is_red:
            self._score(self.DOC_RED_VALUE)
            self.doc_strikes += 1
            self._set(f"{self.MODE_KEY}_doc_strikes", self.doc_strikes)
            self._post_message("DOC OCK STRIKE!", f"{self.doc_strikes} OF 3", self.DOC_RED_VALUE)
            if self.doc_strikes >= self.DOC_STRIKES_TO_END:
                self.delay.reset(name="mastermind_super_start", ms=1_000, callback=self._start_super)
            else:
                self._sync_status("AVOID RED", f"{self.doc_strikes}/3 STRIKES")
            return

        self._score(self.DOC_UNLIT_VALUE)
        self.doc_permanent_red.add(shot)
        self._refresh_doc_lights()
        self._sync_status("DOC OCK", f"SPINS {self.doc_spins} - STRIKES {self.doc_strikes}/3")

    def _main_spinner_hit(self, **kwargs):
        if self.phase != "doc_ock":
            return
        multiplier = 3 if self.doc_3x_active else 1
        value = self.DOC_SPINNER_VALUE * multiplier
        self._score(value)
        self.doc_spins += 1
        self._set(f"{self.MODE_KEY}_doc_spins", self.doc_spins)
        if not self.doc_3x_active:
            self._sync_status("DOC OCK", f"SPINS {self.doc_spins} - STRIKES {self.doc_strikes}/3")

    def _doc_inlane(self, **kwargs):
        if self.phase != "doc_ock":
            return
        self.doc_3x_active = True
        self.doc_3x_remaining = self.DOC_3X_MS // 1000
        self.machine.events.post(f"{self.MODE_KEY}_doc_3x_on")
        self.delay.reset(name="mastermind_doc_3x_end", ms=self.DOC_3X_MS, callback=self._doc_3x_end)
        self.delay.reset(name="mastermind_doc_3x_tick", ms=1_000, callback=self._doc_3x_tick)
        self._show_timer("3X SPINNER", self.doc_3x_remaining)

    def _doc_3x_tick(self):
        if self.phase != "doc_ock" or not self.doc_3x_active:
            return
        self.doc_3x_remaining = max(0, self.doc_3x_remaining - 1)
        if self.doc_3x_remaining > 0:
            self._show_timer("3X SPINNER", self.doc_3x_remaining)
            self.delay.reset(name="mastermind_doc_3x_tick", ms=1_000, callback=self._doc_3x_tick)

    def _doc_3x_end(self):
        self.doc_3x_active = False
        self.doc_3x_remaining = 0
        self.delay.remove("mastermind_doc_3x_tick")
        self.machine.events.post(f"{self.MODE_KEY}_doc_3x_off")
        if self.phase == "doc_ock":
            self._sync_status("DOC OCK", f"SPINS {self.doc_spins} - STRIKES {self.doc_strikes}/3")

    # ------------------------------------------------------------------
    # Super and cycle restart
    # ------------------------------------------------------------------
    def _start_super(self):
        if self.mode_done:
            return
        self.phase = "super"
        self.delay.remove("mastermind_doc_rotate")
        self.delay.remove("mastermind_doc_3x_tick")
        self.delay.remove("mastermind_doc_3x_end")
        self.doc_3x_active = False
        self.machine.events.post(f"{self.MODE_KEY}_doc_clear")
        self.machine.events.post(f"{self.MODE_KEY}_super_on")
        self.super_elapsed_ms = 0
        self.super_value = self.SUPER_START
        self._set(f"{self.MODE_KEY}_super_jackpot_ready", 1)
        self._set(f"{self.MODE_KEY}_super_jackpot_value", self.super_value)
        self._post_message("SUPER JACKPOT", "EITHER WEB TARGET", self.super_value)
        self._super_tick()

    def _super_tick(self):
        if self.phase != "super" or self.mode_done:
            return
        total_ms = self.SUPER_COUNTDOWN_MS + self.SUPER_HOLD_MS
        if self.super_elapsed_ms >= total_ms:
            self._super_expired()
            return

        if self.super_elapsed_ms < self.SUPER_COUNTDOWN_MS:
            fraction = self.super_elapsed_ms / self.SUPER_COUNTDOWN_MS
            self.super_value = int(round(self.SUPER_START - ((self.SUPER_START - self.SUPER_FLOOR) * fraction)))
            self.super_value = max(self.SUPER_FLOOR, self.super_value)
        else:
            self.super_value = self.SUPER_FLOOR

        self._set(f"{self.MODE_KEY}_super_jackpot_value", self.super_value)
        remaining_ms = total_ms - self.super_elapsed_ms
        remaining_seconds = max(1, math.ceil(remaining_ms / 1000))
        self.machine.events.post(
            "show_mode_timer_status",
            mode_status_title=f"SUPER {self.super_value:,}",
            mode_status_value=remaining_seconds,
        )
        self.super_elapsed_ms += self.SUPER_TICK_MS
        self.delay.reset(name="mastermind_super_tick", ms=self.SUPER_TICK_MS, callback=self._super_tick)

    def _collect_super(self):
        if self.phase != "super":
            return
        value = self.super_value
        self._score(value, major=True)
        self._add(f"{self.MODE_KEY}_super_jackpots_collected", 1)
        self._post_message("SUPER JACKPOT", "MASTERMIND TRAP", value)
        self._finish_super()

    def _super_expired(self):
        if self.phase != "super":
            return
        self._post_message("SUPER MISSED", "NEXT CYCLE", self.SUPER_FLOOR)
        self._finish_super()

    def _finish_super(self):
        self.delay.remove("mastermind_super_tick")
        self.machine.events.post(f"{self.MODE_KEY}_super_off")
        self._set(f"{self.MODE_KEY}_super_jackpot_ready", 0)
        self.cycle += 1
        self._set(f"{self.MODE_KEY}_cycle", self.cycle)
        self.delay.reset(name="mastermind_cycle_restart", ms=1_500, callback=self._start_para_scorpion)

    def _vuk_hit(self, **kwargs):
        # Mastermind Trap no longer uses the VUK as a jackpot shot. Always feed
        # the ball back to play so the wizard cannot trap it there.
        self.machine.events.post("request_vuk_eject")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _release_all_saucers(self):
        for saucer in sorted(self.held_saucers):
            self.machine.events.post(f"{self.MODE_KEY}_saucer_{saucer}_released")
            self.machine.events.post(f"delayed_kickout_saucer_{saucer}")
        self.held_saucers.clear()

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return int(self.machine.game.balls_in_play or 0)

    def _score(self, points, major=False):
        player = self.machine.game.player
        player["score"] += int(points)
        self._add("active_mode_points", int(points))
        self._add("active_mode_hits", 1)
        if major:
            self._add("active_mode_major_hits", 1)

    def _show_timer(self, title, seconds):
        self.machine.events.post(
            "show_mode_timer_status",
            mode_status_title=title,
            mode_status_value=int(seconds),
        )

    def _sync_status(self, title, value):
        self._set(f"{self.MODE_KEY}_current_objective", str(title))
        self._set(f"{self.MODE_KEY}_current_status", str(value))
        self.machine.events.post("show_mode_status", mode_status_title=title, mode_status_value=value)

    def _post_message(self, title, subtitle, value):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _reset_player_vars(self):
        self._set("mini_wizard_current_key", self.MODE_KEY)
        self._set(f"{self.MODE_KEY}_state", 1)
        self._set("active_mode_points", 0)
        self._set("active_mode_hits", 0)
        self._set("active_mode_major_hits", 0)
        self._set(f"{self.MODE_KEY}_cycle", 1)
        self._set(f"{self.MODE_KEY}_para_attempts", 0)
        self._set(f"{self.MODE_KEY}_deliveries", 0)
        self._set(f"{self.MODE_KEY}_doc_strikes", 0)
        self._set(f"{self.MODE_KEY}_doc_spins", 0)
        self._set(f"{self.MODE_KEY}_super_jackpots_collected", 0)
        self._set(f"{self.MODE_KEY}_super_jackpot_ready", 0)
        self._set(f"{self.MODE_KEY}_super_jackpot_value", self.SUPER_START)
        self._set(f"{self.MODE_KEY}_current_objective", "PARK A BALL")
        self._set(f"{self.MODE_KEY}_current_status", "PARAFINO + SCORPION")

    def _multiball_ended(self, **kwargs):
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._set(f"{self.MODE_KEY}_state", 2)
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _clear_delays(self):
        for name in (
            "mastermind_roof_center", "mastermind_next_phase", "mastermind_next_attempt",
            "mastermind_next_serum", "mastermind_doc_rotate", "mastermind_doc_3x_end",
            "mastermind_doc_3x_tick", "mastermind_super_start", "mastermind_super_tick",
            "mastermind_cycle_restart",
        ):
            self.delay.remove(name)

    def _set(self, name, value):
        self.machine.game.player[name] = value

    def _add(self, name, amount):
        player = self.machine.game.player
        player[name] = player[name] + amount
