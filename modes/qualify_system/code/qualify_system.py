from mpf.core.mode import Mode


class QualifySystem(Mode):
    """Left 3-bank drops + three saucer state system.

    s_left_drops_1 -> saucer 1
    s_left_drops_2 -> saucer 2
    s_left_drops_3 -> saucer 3

    MPF bank event drop_target_bank_dt_bank_left_down marks completion.
    """

    SAUCERS = ["saucer_1", "saucer_2", "saucer_3"]
    MAX_SAUCER_STATE = 5

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.qualify_logic_active = True
        self._add_handlers()
        self._restore_state()

    def mode_stop(self, **kwargs):
        self.qualify_logic_active = False
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("villain_qualify_drop_1_hit", self._drop_hit, saucer="saucer_1")
        self.add_mode_event_handler("villain_qualify_drop_2_hit", self._drop_hit, saucer="saucer_2")
        self.add_mode_event_handler("villain_qualify_drop_3_hit", self._drop_hit, saucer="saucer_3")

        # Rooftop targets act like the lower drops, but every hit advances
        # the associated saucer state. No per-bank cycle lockout.
        self.add_mode_event_handler("villain_qualify_rooftop_target_1_hit", self._rooftop_target_hit, saucer="saucer_1")
        self.add_mode_event_handler("villain_qualify_rooftop_target_2_hit", self._rooftop_target_hit, saucer="saucer_2")
        self.add_mode_event_handler("villain_qualify_rooftop_target_3_hit", self._rooftop_target_hit, saucer="saucer_3")

        self.add_mode_event_handler("drop_target_bank_dt_bank_left_down", self._bank_completed)
        self.add_mode_event_handler("saucer_star_upgrade_hit", self._star_hit)

        self.add_mode_event_handler("ball_started", self._ball_started_restore)
        self.add_mode_event_handler("villain_started_set", self._reset_after_villain)
        self.add_mode_event_handler("villain_mode_started", self._reset_after_villain)
        self.add_mode_event_handler("villain_mode_ended", self._reset_after_villain)
        self.add_mode_event_handler("chapter_mini_wizard_completed", self._reset_after_villain)
        self.add_mode_event_handler("qualify_system_restore_state", self._restore_state)

    def _ball_started_restore(self, **kwargs):
        self._reset_drop_cycle()
        self.machine.events.post("villain_qualify_drop_bank_reset_request")
        self._restore_state()

    def _qualify_blocked(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return True
        if player["villain_mode_running"] == 1:
            return True
        if player["chapter_mini_wizard_ready"] == 1:
            return True
        if player["final_wizard_ready"] == 1:
            return True
        return False

    def _drop_hit(self, saucer=None, **kwargs):
        if not self.qualify_logic_active or saucer not in self.SAUCERS:
            return

        player = self.machine.game.player

        if player["villain_mode_running"] == 1:
            self.machine.events.post("villain_drop_ignored_mode_running", saucer=saucer)
            return

        if player["chapter_mini_wizard_ready"] == 1:
            self.machine.events.post("mini_wizard_start_ready_at_daily_bugle")
            self.machine.events.post("villain_mini_wizard_gate_opened")
            return

        hit_var = f"{saucer}_drop_hit_this_cycle"
        state_var = f"{saucer}_state"

        if self.machine.game.player[hit_var] == 0:
            self.machine.game.player[hit_var] = 1

            if self.machine.game.player[state_var] < self.MAX_SAUCER_STATE:
                self.machine.game.player[state_var] += 1
                self.machine.events.post(
                    "saucer_state_advanced",
                    saucer=saucer,
                    state=self.machine.game.player[state_var],
                )
                self.machine.events.post(f"{saucer}_state_{self.machine.game.player[state_var]}")
            else:
                self.machine.events.post("saucer_already_maxed", saucer=saucer)
        else:
            self.machine.events.post("drop_already_hit_this_cycle", saucer=saucer)

        self._restore_state()

    def _rooftop_target_hit(self, saucer=None, **kwargs):
        if not self.qualify_logic_active or saucer not in self.SAUCERS:
            return

        if self._qualify_blocked():
            self.machine.events.post("villain_rooftop_target_ignored_mode_running", saucer=saucer)
            return

        self._advance_saucer_state(saucer=saucer, source="rooftop_target")
        self._restore_state()

    def _advance_saucer_state(self, saucer=None, source="unknown"):
        state_var = f"{saucer}_state"

        if self.machine.game.player[state_var] < self.MAX_SAUCER_STATE:
            self.machine.game.player[state_var] += 1
            state = self.machine.game.player[state_var]
            self.machine.events.post(
                "saucer_state_advanced",
                saucer=saucer,
                state=state,
                source=source,
            )
            self.machine.events.post(f"{saucer}_state_{state}")

            if source == "rooftop_target":
                self.machine.events.post(
                    "saucer_state_advanced_by_rooftop_target",
                    saucer=saucer,
                    state=state,
                )
                self.machine.events.post(f"{saucer}_advanced_by_rooftop_target")
        else:
            self.machine.events.post("saucer_already_maxed", saucer=saucer)

    def _bank_completed(self, **kwargs):
        if not self.qualify_logic_active:
            return

        if self._qualify_blocked():
            self.machine.events.post("villain_bank_complete_ignored_mode_running")
            return

        self.machine.game.player["drop_bank_completions_this_ball"] += 1
        self.machine.game.player["drop_bank_completions_this_chapter"] += 1

        self.machine.events.post(
            "villain_qualify_drop_bank_completed",
            completions_this_ball=self.machine.game.player["drop_bank_completions_this_ball"],
            completions_this_chapter=self.machine.game.player["drop_bank_completions_this_chapter"],
        )

        self._reset_drop_cycle()
        self.machine.events.post("villain_qualify_drop_bank_reset_request")
        self._restore_state()

    def _reset_drop_cycle(self):
        for saucer in self.SAUCERS:
            self.machine.game.player[f"{saucer}_drop_hit_this_cycle"] = 0

    def _star_hit(self, **kwargs):
        if not self.qualify_logic_active:
            return

        if self._qualify_blocked():
            self.machine.events.post("villain_star_ignored_mode_running")
            return

        if not all(self.machine.game.player[f"{s}_state"] >= 1 for s in self.SAUCERS):
            self.machine.events.post("saucer_star_not_ready")
            return

        advanced = False
        for saucer in self.SAUCERS:
            state_var = f"{saucer}_state"
            if self.machine.game.player[state_var] < self.MAX_SAUCER_STATE:
                self.machine.game.player[state_var] += 1
                advanced = True
                self.machine.events.post(
                    "saucer_state_advanced_by_star",
                    saucer=saucer,
                    state=self.machine.game.player[state_var],
                )

        if advanced:
            self.machine.events.post("saucer_star_advanced_all")
        else:
            self.machine.events.post("saucers_all_maxed")

        self._restore_state()

    def _reset_after_villain(self, **kwargs):
        for saucer in self.SAUCERS:
            self.machine.game.player[f"{saucer}_state"] = 0
            self.machine.game.player[f"{saucer}_drop_hit_this_cycle"] = 0

        self.machine.game.player["drop_bank_completions_this_ball"] = 0
        self.machine.events.post("villain_qualify_reset_after_villain")
        self.machine.events.post("villain_qualify_drop_bank_reset_request")
        self._restore_state()

    def _restore_state(self, **kwargs):
        if not self.qualify_logic_active:
            return

        for saucer in self.SAUCERS:
            state = int(self.machine.game.player[f"{saucer}_state"])
            self.machine.events.post(
                "saucer_state_restore",
                saucer=saucer,
                state=state,
            )
            self.machine.events.post(f"{saucer}_restore_state_{state}")
