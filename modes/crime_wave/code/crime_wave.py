from mpf.core.mode import Mode


class CrimeWave(Mode):
    """Chapter 4 wizard: timed villain areas feeding upper-exit jackpots."""

    MODE_KEY = "crime_wave"
    DISPLAY_NAME = "Crime Wave"
    AREA_TIMEOUT_MS = 20_000
    SAUCER_HOLD_MS = 15_000
    BASE_JACKPOT_PER_AREA = 250_000

    AREAS = ("plotter", "fly_twins", "phantom", "enforcers", "doctor_cool")
    SAUCER_EJECT_EVENTS = {
        1: "delayed_kickout_saucer_1",
        2: "delayed_kickout_saucer_2",
        3: "delayed_kickout_saucer_3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_done = False
        self.lit_areas = set()
        self.gate_open = False
        self.held_saucers = set()
        self.jackpots = 0
        self.mode_points = 0

        player = self.machine.game.player
        self.case_file_bonus = player["mini_wizard_case_file_bonus"]
        player["mini_wizard_current_key"] = self.MODE_KEY
        player[f"{self.MODE_KEY}_state"] = 1
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0

        self.add_mode_event_handler("crime_wave_plotter_hit", self._area_hit, area="plotter")
        self.add_mode_event_handler("crime_wave_fly_hit", self._area_hit, area="fly_twins")
        self.add_mode_event_handler("crime_wave_phantom_hit", self._area_hit, area="phantom")
        self.add_mode_event_handler("crime_wave_enforcers_hit", self._area_hit, area="enforcers")
        self.add_mode_event_handler("crime_wave_saucer_hit", self._saucer_hit)
        self.add_mode_event_handler("crime_wave_upper_exit_hit", self._upper_exit_hit)
        self.add_mode_event_handler("crime_wave_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("crime_wave_complete_request", self._complete_mode)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="CRIME WAVE",
            message_mode_subtitle="LIGHT 3 AREAS TO OPEN ROOF",
            reminder=True,
        )
        self._update_status()
        self.machine.events.post("crime_wave_saucers_available")
        self.machine.events.post("crime_wave_start_multiball")

    def mode_stop(self, **kwargs):
        for area in self.AREAS:
            self.delay.remove(f"crime_wave_area_{area}")
        self.delay.remove("crime_wave_vuk_eject")
        for saucer in tuple(self.held_saucers):
            self._release_saucer(saucer)
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("crime_wave_clear_saucer_lights")
        self.machine.events.post("crime_wave_clear_lights")
        player = self.machine.game.player if self.machine.game else None
        if player and player["mini_wizard_current_key"] == self.MODE_KEY:
            player["mini_wizard_current_key"] = ""
        super().mode_stop(**kwargs)

    def _area_hit(self, area, **kwargs):
        if self.mode_done:
            return
        newly_lit = area not in self.lit_areas
        self.lit_areas.add(area)
        self.delay.remove(f"crime_wave_area_{area}")
        self.delay.add(
            name=f"crime_wave_area_{area}",
            ms=self.AREA_TIMEOUT_MS,
            callback=self._area_expired,
            area=area,
        )
        self.machine.events.post(f"crime_wave_area_{area}_lit")
        if newly_lit:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title=f"{area.replace('_', ' ').upper()} LIT",
                message_mode_subtitle=f"{len(self.lit_areas)} OF 5 AREAS",
            )
        self._update_gate()
        self._update_status()

    def _area_expired(self, area, **kwargs):
        if area not in self.lit_areas:
            return
        self.lit_areas.remove(area)
        self.machine.events.post(f"crime_wave_area_{area}_unlit")
        self._update_gate()
        self._update_status()

    def _saucer_hit(self, saucer, **kwargs):
        if self.mode_done:
            self.machine.events.post(self.SAUCER_EJECT_EVENTS[saucer])
            return
        self._area_hit("doctor_cool")
        self.held_saucers.add(saucer)
        self.machine.events.post(f"crime_wave_saucer_{saucer}_held")
        self.delay.remove(f"crime_wave_saucer_{saucer}")
        self.delay.add(
            name=f"crime_wave_saucer_{saucer}",
            ms=self.SAUCER_HOLD_MS,
            callback=self._release_saucer,
            saucer=saucer,
        )
        if self._balls_in_play() - len(self.held_saucers) <= 1:
            self._release_saucer(saucer)

    def _release_saucer(self, saucer, **kwargs):
        self.delay.remove(f"crime_wave_saucer_{saucer}")
        was_held = saucer in self.held_saucers
        self.held_saucers.discard(saucer)
        if was_held:
            self.machine.events.post(f"crime_wave_saucer_{saucer}_released")
        self.machine.events.post(self.SAUCER_EJECT_EVENTS[saucer])


    def _vuk_hit(self, **kwargs):
        """Daily Bugle/VUK jackpot collect during Crime Wave.

        Daily Bugle Mystery is disabled during this wizard, so Crime Wave must
        own VUK switch response and kick the ball out itself.
        """
        self.delay.remove("crime_wave_vuk_eject")
        self.delay.add(
            name="crime_wave_vuk_eject",
            ms=1500,
            callback=lambda: self.machine.events.post("up_kick"),
        )
        self._upper_exit_hit(**kwargs)

    def _upper_exit_hit(self, **kwargs):
        if self.mode_done or not self.lit_areas:
            return
        value = len(self.lit_areas) * self.BASE_JACKPOT_PER_AREA + self.case_file_bonus
        self.jackpots += 1
        self._score(value)
        self.machine.game.player["active_mode_major_hits"] = self.jackpots
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="CRIME WAVE JACKPOT",
            message_mode_subtitle=f"{len(self.lit_areas)} AREAS LIT",
            message_mode_value=value,
        )
        self._update_status()

    def _update_gate(self):
        count = len(self.lit_areas)
        if not self.gate_open and count >= 3:
            self.gate_open = True
            self.machine.events.post("rooftop_diverter_open")
        elif self.gate_open and count <= 1:
            self.gate_open = False
            self.machine.events.post("rooftop_diverter_close")

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self.machine.events.post("crime_wave_mode_complete")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("stop_mode_crime_wave")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player["active_mode_points"] = self.mode_points

    def _update_status(self):
        self.machine.game.player["active_mode_hits"] = len(self.lit_areas)
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="AREAS / JACKPOTS",
            mode_status_value=f"{len(self.lit_areas)} / {self.jackpots}",
        )

    def _balls_in_play(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return 0
        return int(player["balls_in_play"] or 0)
