from mpf.core.mode import Mode


class MastermindTrap(Mode):
    """Chapter 2 mini-wizard: Mastermind Trap.

    Rules:
    - Start 2-ball multiball.
    - Five villain trap objectives are available at once:
        Goblin: complete the right 5-bank.
        Doc Ock: hit all three upper targets.
        Mysterio: collect all three saucers.
        Scorpion: spin 10 times, then hit the star.
        Parafino: score 15 pop bumper hits.
    - Completing a trap scores a Trap Award and lights the VUK Mastermind Jackpot.
    - VUK Jackpot grows with traps completed and chapter case-file bonus.
    - Completing all five traps lights the VUK Super Jackpot.
    - Super Jackpot starts victory laps, but the wizard still ends when multiball ends.
    - Active case-file powers are not used; only mini_wizard_case_file_bonus scales values.
    """

    MODE_KEY = "mastermind_trap"
    DISPLAY_NAME = "Mastermind Trap"

    TRAP_AWARD_BASE = 300_000
    JACKPOT_BASE = 750_000
    JACKPOT_PER_TRAP = 250_000
    SUPER_JACKPOT_BASE = 2_500_000
    VICTORY_LAP_SCORE = 75_000

    SCORPION_SPINS_REQUIRED = 10
    PARAFINO_POP_HITS_REQUIRED = 15

    TRAPS = ("goblin", "doc_ock", "mysterio", "scorpion", "parafino")

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_done = False
        self.victory_laps = False
        self.case_file_bonus = self.machine.game.player["mini_wizard_case_file_bonus"]

        self.completed_traps = set()
        self.doc_ock_targets = set()
        self.mysterio_saucers = set()
        self.scorpion_spins = 0
        self.scorpion_star_lit = False
        self.parafino_pop_hits = 0
        self.jackpot_ready = False
        self.super_jackpot_ready = False
        self.jackpots_collected = 0
        self.super_jackpots_collected = 0

        self._reset_player_vars()
        self._add_switch_handlers()

        self.add_mode_event_handler(f"{self.MODE_KEY}_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler(f"{self.MODE_KEY}_complete_request", self._complete_mode)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post(f"{self.MODE_KEY}_start_multiball")
        self._post_message("MASTERMIND TRAP", "Complete villain traps", "VUK collects jackpots")
        self._sync_status("TRAPS", "0/5")
        self.machine.events.post(f"{self.MODE_KEY}_setup_lights")

    def mode_stop(self, **kwargs):
        player = self.machine.game.player
        if player["mini_wizard_current_key"] == self.MODE_KEY:
            player["mini_wizard_current_key"] = ""

        self.machine.events.post(f"{self.MODE_KEY}_clear_lights")
        self.machine.events.post("hide_mode_status")
        super().mode_stop(**kwargs)

    def _add_switch_handlers(self):
        self.add_mode_event_handler("s_pop_left_active", self._pop_hit)
        self.add_mode_event_handler("s_pop_right_active", self._pop_hit)

        self.add_mode_event_handler("s_trispinner_opto_active", self._spinner_hit)
        self.add_mode_event_handler("s_web_spinner_active", self._spinner_hit)
        self.add_mode_event_handler("s_star_rollover_active", self._star_hit)

        self.add_mode_event_handler("s_upper_target_left_active", self._upper_target_hit, target="left")
        self.add_mode_event_handler("s_upper_target_center_active", self._upper_target_hit, target="center")
        self.add_mode_event_handler("s_upper_target_right_active", self._upper_target_hit, target="right")

        self.add_mode_event_handler("s_saucer_1_active", self._saucer_hit, saucer=1)
        self.add_mode_event_handler("s_saucer_2_active", self._saucer_hit, saucer=2)
        self.add_mode_event_handler("s_saucer_3_active", self._saucer_hit, saucer=3)

        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)

        self.add_mode_event_handler("drop_target_bank_dt_bank_right_down", self._right_bank_complete)
        self.add_mode_event_handler("drop_target_bank_dt_bank_left_down", self._left_bank_complete)

        for num in range(1, 6):
            self.add_mode_event_handler(f"s_right_drops_{num}_active", self._right_drop_hit)
        for num in range(1, 4):
            self.add_mode_event_handler(f"s_left_drops_{num}_active", self._left_drop_hit)

    def _reset_player_vars(self):
        self._set("mini_wizard_current_key", self.MODE_KEY)
        self._set(f"{self.MODE_KEY}_state", 1)
        self._set("active_mode_points", 0)
        self._set("active_mode_hits", 0)
        self._set("active_mode_major_hits", 0)

        self._set(f"{self.MODE_KEY}_case_file_bonus", self.case_file_bonus)
        self._set(f"{self.MODE_KEY}_traps_completed", 0)
        self._set(f"{self.MODE_KEY}_jackpots_collected", 0)
        self._set(f"{self.MODE_KEY}_super_jackpots_collected", 0)
        self._set(f"{self.MODE_KEY}_jackpot_ready", 0)
        self._set(f"{self.MODE_KEY}_super_jackpot_ready", 0)
        self._set(f"{self.MODE_KEY}_jackpot_value", self._current_jackpot_value())
        self._set(f"{self.MODE_KEY}_super_jackpot_value", self._current_super_jackpot_value())
        self._set(f"{self.MODE_KEY}_current_objective", "COMPLETE 5 TRAPS")
        self._set(f"{self.MODE_KEY}_current_status", "0/5 TRAPS")

        for trap in self.TRAPS:
            self._set(f"{self.MODE_KEY}_{trap}_complete", 0)

        self._set(f"{self.MODE_KEY}_doc_ock_progress", 0)
        self._set(f"{self.MODE_KEY}_mysterio_progress", 0)
        self._set(f"{self.MODE_KEY}_scorpion_spins", 0)
        self._set(f"{self.MODE_KEY}_parafino_pop_hits", 0)

        self._sync_status_vars()

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self._add("active_mode_points", points)

    def _minor_hit(self, points=25_000):
        if self.mode_done:
            return
        if self.victory_laps:
            points = self.VICTORY_LAP_SCORE
        self._score(points)
        self._add("active_mode_hits", 1)

    def _pop_hit(self, **kwargs):
        if self.mode_done:
            return
        self._minor_hit()
        if "parafino" not in self.completed_traps:
            self.parafino_pop_hits += 1
            self._set(f"{self.MODE_KEY}_parafino_pop_hits", self.parafino_pop_hits)
            if self.parafino_pop_hits >= self.PARAFINO_POP_HITS_REQUIRED:
                self._complete_trap("parafino", "PARAFINO TRAP", "Pop trap broken")
            else:
                self._sync_status("PARAFINO", f"{self.parafino_pop_hits}/{self.PARAFINO_POP_HITS_REQUIRED}")

    def _spinner_hit(self, **kwargs):
        if self.mode_done:
            return
        self._minor_hit(30_000)
        if "scorpion" not in self.completed_traps and not self.scorpion_star_lit:
            self.scorpion_spins += 1
            self._set(f"{self.MODE_KEY}_scorpion_spins", self.scorpion_spins)
            if self.scorpion_spins >= self.SCORPION_SPINS_REQUIRED:
                self.scorpion_star_lit = True
                self._sync_status("SCORPION", "STAR LIT")
                self._post_message("SCORPION TRAP", "Venom charged", "Hit the star")
                self.machine.events.post(f"{self.MODE_KEY}_scorpion_star_lit")
            else:
                self._sync_status("SCORPION", f"{self.scorpion_spins}/{self.SCORPION_SPINS_REQUIRED}")

    def _star_hit(self, **kwargs):
        if self.mode_done:
            return
        self._minor_hit(50_000)
        if "scorpion" not in self.completed_traps and self.scorpion_star_lit:
            self._complete_trap("scorpion", "SCORPION TRAP", "Venom stopped")

    def _upper_target_hit(self, target, **kwargs):
        if self.mode_done:
            return
        self._minor_hit(50_000)
        if "doc_ock" not in self.completed_traps:
            self.doc_ock_targets.add(target)
            self._set(f"{self.MODE_KEY}_doc_ock_progress", len(self.doc_ock_targets))
            if len(self.doc_ock_targets) >= 3:
                self._complete_trap("doc_ock", "DOC OCK TRAP", "Arms disabled")
            else:
                self._sync_status("DOC OCK", f"{len(self.doc_ock_targets)}/3 TARGETS")

    def _saucer_hit(self, saucer, **kwargs):
        if self.mode_done:
            return
        self._minor_hit(50_000)
        if "mysterio" not in self.completed_traps:
            self.mysterio_saucers.add(saucer)
            self._set(f"{self.MODE_KEY}_mysterio_progress", len(self.mysterio_saucers))
            if len(self.mysterio_saucers) >= 3:
                self._complete_trap("mysterio", "MYSTERIO TRAP", "Illusion exposed")
            else:
                self._sync_status("MYSTERIO", f"{len(self.mysterio_saucers)}/3 SAUCERS")

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            return

        if self.super_jackpot_ready:
            value = self._current_super_jackpot_value()
            self.super_jackpot_ready = False
            self.super_jackpots_collected += 1
            self.victory_laps = True
            self._score(value)
            self._add("active_mode_major_hits", 1)
            self._set(f"{self.MODE_KEY}_super_jackpots_collected", self.super_jackpots_collected)
            self._set(f"{self.MODE_KEY}_super_jackpot_ready", 0)
            self._sync_status("VICTORY LAPS", "ALL SHOTS")
            self._post_message("SUPER JACKPOT", "Trap escaped", value)
            self.machine.events.post(f"{self.MODE_KEY}_super_jackpot_collected", value=value)
            self.machine.events.post(f"{self.MODE_KEY}_victory_laps_started")
            return

        if self.jackpot_ready:
            value = self._current_jackpot_value()
            self.jackpot_ready = False
            self.jackpots_collected += 1
            self._score(value)
            self._add("active_mode_major_hits", 1)
            self._set(f"{self.MODE_KEY}_jackpots_collected", self.jackpots_collected)
            self._set(f"{self.MODE_KEY}_jackpot_ready", 0)
            self._sync_status("TRAPS", f"{len(self.completed_traps)}/5")
            self._post_message("MASTERMIND JACKPOT", "VUK escape route", value)
            self.machine.events.post(f"{self.MODE_KEY}_jackpot_collected", value=value)
            self._maybe_light_super_jackpot()
            return

        self._minor_hit(50_000)
        self._sync_status("VUK", "NO JACKPOT")

    def _right_drop_hit(self, **kwargs):
        self._minor_hit(25_000)

    def _left_drop_hit(self, **kwargs):
        self._minor_hit(25_000)

    def _right_bank_complete(self, **kwargs):
        if self.mode_done:
            return
        if "goblin" not in self.completed_traps:
            self._complete_trap("goblin", "GOBLIN TRAP", "Right bank smashed")
        else:
            self._minor_hit(100_000)

    def _left_bank_complete(self, **kwargs):
        if self.mode_done:
            return
        self._minor_hit(100_000)
        self.machine.events.post(f"{self.MODE_KEY}_left_bank_complete")

    def _complete_trap(self, trap, title, subtitle):
        if trap in self.completed_traps or self.mode_done:
            return

        self.completed_traps.add(trap)
        value = self.TRAP_AWARD_BASE + self.case_file_bonus
        self._score(value)
        self._add("active_mode_major_hits", 1)
        self._set(f"{self.MODE_KEY}_{trap}_complete", 1)
        self._set(f"{self.MODE_KEY}_traps_completed", len(self.completed_traps))
        self._set(f"{self.MODE_KEY}_jackpot_value", self._current_jackpot_value())
        self._set(f"{self.MODE_KEY}_super_jackpot_value", self._current_super_jackpot_value())

        self.machine.events.post(f"{self.MODE_KEY}_{trap}_trap_complete")
        self.machine.events.post(f"{self.MODE_KEY}_trap_complete", trap=trap, value=value)
        self._post_message(title, subtitle, value)

        if not self.jackpot_ready and not self.super_jackpot_ready:
            self.jackpot_ready = True
            self._set(f"{self.MODE_KEY}_jackpot_ready", 1)
            self._sync_status("VUK JACKPOT", self._current_jackpot_value())
            self.machine.events.post(f"{self.MODE_KEY}_jackpot_lit", value=self._current_jackpot_value())
        else:
            self._sync_status("TRAPS", f"{len(self.completed_traps)}/5")

        self._maybe_light_super_jackpot()
        self._sync_status_vars()

    def _maybe_light_super_jackpot(self):
        if len(self.completed_traps) < 5:
            return
        if self.super_jackpots_collected > 0 or self.super_jackpot_ready:
            return
        if self.jackpot_ready:
            return

        self.super_jackpot_ready = True
        self._set(f"{self.MODE_KEY}_super_jackpot_ready", 1)
        self._sync_status("SUPER", self._current_super_jackpot_value())
        self._post_message("SUPER JACKPOT LIT", "Shoot the VUK", self._current_super_jackpot_value())
        self.machine.events.post(f"{self.MODE_KEY}_super_jackpot_lit", value=self._current_super_jackpot_value())

    def _multiball_ended(self, **kwargs):
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._set(f"{self.MODE_KEY}_state", 2)
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")
        self.machine.events.post(f"stop_mode_{self.MODE_KEY}")

    def _current_jackpot_value(self):
        return self.JACKPOT_BASE + (self.JACKPOT_PER_TRAP * len(self.completed_traps)) + self.case_file_bonus

    def _current_super_jackpot_value(self):
        return self.SUPER_JACKPOT_BASE + (500_000 * len(self.completed_traps)) + (self.case_file_bonus * 2)

    def _sync_status_vars(self):
        self._set(f"{self.MODE_KEY}_jackpot_value", self._current_jackpot_value())
        self._set(f"{self.MODE_KEY}_super_jackpot_value", self._current_super_jackpot_value())
        self._set(f"{self.MODE_KEY}_traps_completed", len(self.completed_traps))
        self._set(f"{self.MODE_KEY}_current_status", f"{len(self.completed_traps)}/5 TRAPS")

    def _sync_status(self, title, value):
        self._set(f"{self.MODE_KEY}_current_objective", title)
        self._set(f"{self.MODE_KEY}_current_status", str(value))
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _post_message(self, title, subtitle, value):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _set(self, name, value):
        self.machine.game.player[name] = value

    def _add(self, name, amount):
        player = self.machine.game.player
        player[name] = player[name] + amount
