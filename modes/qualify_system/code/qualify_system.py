from mpf.core.mode import Mode


class QualifySystem(Mode):
    """3-bank drops + three saucer state system.

    Physical drops reset at ball start, bank completion, and after villain modes.
    Saucer states persist between balls but reset after a villain starts/ends.
    """

    SAUCERS = ["left", "center", "right"]
    MAX_SAUCER_STATE = 5

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.qualify_logic_active = True
        self._ensure_player_vars()
        self._add_handlers()
        self._restore_state()

    def mode_stop(self, **kwargs):
        self.qualify_logic_active = False
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("villain_qualify_drop_left_hit", self._drop_hit, saucer="left")
        self.add_mode_event_handler("villain_qualify_drop_center_hit", self._drop_hit, saucer="center")
        self.add_mode_event_handler("villain_qualify_drop_right_hit", self._drop_hit, saucer="right")

        self.add_mode_event_handler("saucer_star_upgrade_hit", self._star_hit)

        self.add_mode_event_handler("ball_started", self._ball_started_restore)
        self.add_mode_event_handler("villain_mode_started", self._reset_after_villain)
        self.add_mode_event_handler("villain_mode_ended", self._reset_after_villain)
        self.add_mode_event_handler("qualify_system_restore_state", self._restore_state)

    def _ensure_player_vars(self):
        defaults = {
            "left_saucer_state": 0,
            "center_saucer_state": 0,
            "right_saucer_state": 0,

            "left_drop_hit_this_cycle": 0,
            "center_drop_hit_this_cycle": 0,
            "right_drop_hit_this_cycle": 0,

            "drop_bank_completions_this_ball": 0,
            "drop_bank_completions_this_chapter": 0,
        }

        for name, value in defaults.items():
            try:
                self.player[name]
            except Exception:
                self.player[name] = value

    def _ball_started_restore(self, **kwargs):
        self._reset_drop_cycle()
        self.machine.events.post("villain_qualify_drop_bank_reset")
        self._restore_state()

    def _drop_hit(self, saucer=None, **kwargs):
        if not self.qualify_logic_active or saucer not in self.SAUCERS:
            return

        hit_var = f"{saucer}_drop_hit_this_cycle"
        state_var = f"{saucer}_saucer_state"

        # One saucer-state increase per physical drop per bank cycle.
        if self.player[hit_var] == 0:
            self.player[hit_var] = 1

            if self.player[state_var] < self.MAX_SAUCER_STATE:
                self.player[state_var] += 1
                self.machine.events.post(
                    "saucer_state_advanced",
                    saucer=saucer,
                    state=self.player[state_var],
                )
                self.machine.events.post(
                    f"{saucer}_saucer_state_{self.player[state_var]}"
                )
            else:
                self.machine.events.post("saucer_already_maxed", saucer=saucer)

        else:
            self.machine.events.post("drop_already_hit_this_cycle", saucer=saucer)

        self._check_bank_complete()
        self._restore_state()

    def _check_bank_complete(self):
        if all(self.player[f"{s}_drop_hit_this_cycle"] == 1 for s in self.SAUCERS):
            self.player["drop_bank_completions_this_ball"] += 1
            self.player["drop_bank_completions_this_chapter"] += 1
            self.machine.events.post(
                "villain_qualify_drop_bank_completed",
                completions_this_ball=self.player["drop_bank_completions_this_ball"],
                completions_this_chapter=self.player["drop_bank_completions_this_chapter"],
            )
            self._reset_drop_cycle()
            self.machine.events.post("villain_qualify_drop_bank_reset")

    def _reset_drop_cycle(self):
        for saucer in self.SAUCERS:
            self.player[f"{saucer}_drop_hit_this_cycle"] = 0

    def _star_hit(self, **kwargs):
        if not self.qualify_logic_active:
            return

        if not all(self.player[f"{s}_saucer_state"] >= 1 for s in self.SAUCERS):
            self.machine.events.post("saucer_star_not_ready")
            return

        advanced = False
        for saucer in self.SAUCERS:
            state_var = f"{saucer}_saucer_state"
            if self.player[state_var] < self.MAX_SAUCER_STATE:
                self.player[state_var] += 1
                advanced = True
                self.machine.events.post(
                    "saucer_state_advanced_by_star",
                    saucer=saucer,
                    state=self.player[state_var],
                )

        if advanced:
            self.machine.events.post("saucer_star_advanced_all")
        else:
            self.machine.events.post("saucers_all_maxed")

        self._restore_state()

    def _reset_after_villain(self, **kwargs):
        for saucer in self.SAUCERS:
            self.player[f"{saucer}_saucer_state"] = 0
            self.player[f"{saucer}_drop_hit_this_cycle"] = 0

        self.player["drop_bank_completions_this_ball"] = 0
        self.machine.events.post("villain_qualify_reset_after_villain")
        self.machine.events.post("villain_qualify_drop_bank_reset")
        self._restore_state()

    def _restore_state(self, **kwargs):
        if not self.qualify_logic_active:
            return

        for saucer in self.SAUCERS:
            state = int(self.player[f"{saucer}_saucer_state"])
            self.machine.events.post(
                "saucer_state_restore",
                saucer=saucer,
                state=state,
            )
            self.machine.events.post(f"{saucer}_saucer_restore_state_{state}")
