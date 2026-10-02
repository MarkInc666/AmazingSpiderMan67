import time

from mpf.core.mode import Mode


class CrimeWave(Mode):
    """Chapter 4 wizard: timed villain captures feeding rooftop rewards."""

    MODE_KEY = "crime_wave"
    DISPLAY_NAME = "Crime Wave"

    AREA_TIMEOUT_MS = 15_000
    AREA_WARNING_MS = 10_000
    SAUCER_HOLD_MS = 15_000
    SUPER_TIMEOUT_MS = 15_000

    BASE_JACKPOT_PER_AREA = 100_000
    AREA_RELIGHT_SCORE = 25_000
    VUK_SCORE = 100_000
    SUPER_JACKPOT = 5_000_000
    VUK_COLLECT_LOCKOUT_SECONDS = 2.0

    AREAS = ("plotter", "fly_twins", "phantom", "enforcers", "doctor_cool")
    AREA_NAMES = {
        "plotter": "THE PLOTTER",
        "fly_twins": "THE FLY TWINS",
        "phantom": "5TH AVE PHANTOM",
        "enforcers": "THE ENFORCERS",
        "doctor_cool": "DOCTOR COOL",
    }
    SAUCER_EJECT_EVENTS = {
        1: "delayed_kickout_saucer_1",
        2: "delayed_kickout_saucer_2",
        3: "delayed_kickout_saucer_3",
    }
    EXIT_SAUCER = {
        "left": 1,
        "center": 2,
        "right": 3,
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
        self.lit_areas = set()
        self.warning_areas = set()
        self.max_areas_lit = 0
        self.gate_open = False
        self.held_saucers = set()
        self.jackpots = 0
        self.super_jackpots = 0
        self.mode_points = 0
        self.super_active = False
        self.roof_visit_active = False
        self.vuk_display_active = False
        self._vuk_collect_lockout_until = 0.0

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
        self.add_mode_event_handler("crime_wave_center_exit_hit", self._center_exit_hit)
        self.add_mode_event_handler("crime_wave_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("crime_wave_web_hit", self._web_hit)
        self.add_mode_event_handler("crime_wave_complete_request", self._complete_mode)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="CRIME WAVE",
            message_mode_subtitle="CAPTURE 3 VILLAINS TO OPEN ROOF",
            reminder=True,
        )
        self.machine.events.post("crime_wave_gi_restore")
        for area in self.AREAS:
            self.machine.events.post(f"crime_wave_area_{area}_available")
        self._update_status()
        self.machine.events.post("crime_wave_start_multiball")

    def mode_stop(self, **kwargs):
        self.delay.clear()
        for saucer in tuple(self.held_saucers):
            self._release_saucer(saucer)
        self.super_active = False
        self.roof_visit_active = False
        self.vuk_display_active = False
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("crime_wave_super_off")
        self.machine.events.post("crime_wave_clear_lights")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        player = self.machine.game.player if self.machine.game else None
        if player and player["mini_wizard_current_key"] == self.MODE_KEY:
            player["mini_wizard_current_key"] = ""
        super().mode_stop(**kwargs)

    def _area_hit(self, area, **kwargs):
        if self.mode_done:
            return

        newly_lit = area not in self.lit_areas
        self.lit_areas.add(area)
        self.warning_areas.discard(area)
        self.max_areas_lit = max(self.max_areas_lit, len(self.lit_areas))
        self._reset_area_timer(area)
        self.machine.events.post(f"crime_wave_area_{area}_active")

        if newly_lit:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title=f"{self.AREA_NAMES[area]} CAPTURED",
                message_mode_subtitle=f"{len(self.lit_areas)} OF 5 CAPTURED",
            )
        else:
            self._score(self.AREA_RELIGHT_SCORE)

        self._update_gate()
        self._refresh_vuk_display_if_active()
        self._update_status()

    def _reset_area_timer(self, area):
        self.delay.remove(f"crime_wave_area_warning_{area}")
        self.delay.remove(f"crime_wave_area_expire_{area}")
        self.delay.add(
            name=f"crime_wave_area_warning_{area}",
            ms=self.AREA_WARNING_MS,
            callback=self._area_warning,
            area=area,
        )
        self.delay.add(
            name=f"crime_wave_area_expire_{area}",
            ms=self.AREA_TIMEOUT_MS,
            callback=self._area_expired,
            area=area,
        )

    def _area_warning(self, area, **kwargs):
        if self.mode_done or area not in self.lit_areas:
            return
        self.warning_areas.add(area)
        self.machine.events.post(f"crime_wave_area_{area}_warning")

    def _area_expired(self, area, **kwargs):
        if self.mode_done or area not in self.lit_areas:
            return
        self.lit_areas.remove(area)
        self.warning_areas.discard(area)
        self.machine.events.post(f"crime_wave_area_{area}_available")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=f"{self.AREA_NAMES[area]} ESCAPING",
            message_mode_subtitle="CAPTURE THEM AGAIN",
        )
        self._update_gate()
        self._refresh_vuk_display_if_active()
        self._update_status()

    def _saucer_hit(self, saucer, **kwargs):
        if self.mode_done:
            self.machine.events.post(self.SAUCER_EJECT_EVENTS[saucer])
            return
        self._area_hit("doctor_cool")
        self.held_saucers.add(saucer)
        self.delay.remove(f"crime_wave_saucer_{saucer}")
        self.delay.add(
            name=f"crime_wave_saucer_{saucer}",
            ms=self.SAUCER_HOLD_MS,
            callback=self._release_saucer,
            saucer=saucer,
        )
        self._refresh_vuk_display_if_active()
        if self._balls_in_play() - len(self.held_saucers) <= 0:
            self._release_saucer(saucer)

    def _release_saucer(self, saucer, **kwargs):
        self.delay.remove(f"crime_wave_saucer_{saucer}")
        was_held = saucer in self.held_saucers
        self.held_saucers.discard(saucer)
        if was_held:
            self._refresh_vuk_display_if_active()
        self.machine.events.post(self.SAUCER_EJECT_EVENTS[saucer])

    def _vuk_hit(self, **kwargs):
        """Award the VUK value, show live roof rewards, then kick toward the roof."""
        if self.mode_done:
            return
        now = time.monotonic()
        if now < self._vuk_collect_lockout_until:
            return
        self._vuk_collect_lockout_until = now + self.VUK_COLLECT_LOCKOUT_SECONDS

        self._score(self.VUK_SCORE)
        self.vuk_display_active = True
        self._show_roof_values()
        self.delay.reset(
            name="crime_wave_vuk_display_done",
            ms=1_500,
            callback=self._finish_vuk_hold,
        )
        self.machine.events.post("request_vuk_eject", delay_ms=1_500)

    def _finish_vuk_hold(self, **kwargs):
        self.vuk_display_active = False
        self.roof_visit_active = self.gate_open

    def _show_roof_values(self):
        left = self._roof_value("left")
        center = self._roof_value("center")
        right = self._roof_value("right")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="ROOF REWARDS",
            message_mode_subtitle=f"L {left:,}   C {center:,}   R {right:,}",
        )

    def _refresh_vuk_display_if_active(self):
        if self.vuk_display_active:
            self._show_roof_values()

    def _roof_value(self, exit_name):
        value = len(self.lit_areas) * self.BASE_JACKPOT_PER_AREA + self.case_file_bonus
        if self.EXIT_SAUCER[exit_name] in self.held_saucers:
            value *= 2
        return value

    def _upper_exit_hit(self, exit_name, **kwargs):
        if self.mode_done or not self.roof_visit_active or len(self.lit_areas) < 3:
            return
        if exit_name not in ("left", "right"):
            return
        self._collect_roof_reward(exit_name)

    def _center_exit_hit(self, **kwargs):
        if self.mode_done or not self.roof_visit_active or len(self.lit_areas) < 3:
            return
        self._collect_roof_reward("center")

    def _collect_roof_reward(self, exit_name):
        value = self._roof_value(exit_name)
        self.roof_visit_active = False
        self.jackpots += 1
        self._score(value)
        self.machine.game.player["active_mode_major_hits"] = self.jackpots + self.super_jackpots
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="REWARD COLLECTED",
            message_mode_subtitle="",
            message_mode_value=value,
        )
        self.machine.events.post("play_mode_jackpot")

        if len(self.lit_areas) == 5:
            self._light_or_refresh_super()

        self._update_status()

    def _light_or_refresh_super(self):
        self.super_active = True
        self.delay.reset(
            name="crime_wave_super_timeout",
            ms=self.SUPER_TIMEOUT_MS,
            callback=self._super_timeout,
        )
        self.machine.events.post("crime_wave_super_on")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="SUPER JACKPOT LIT",
            message_mode_subtitle="HIT EITHER WEB - 15 SECONDS",
        )
        self._update_status()

    def _web_hit(self, **kwargs):
        if self.mode_done or not self.super_active:
            return
        self.super_active = False
        self.delay.remove("crime_wave_super_timeout")
        self.machine.events.post("crime_wave_super_off")
        self.super_jackpots += 1
        self._score(self.SUPER_JACKPOT)
        self.machine.game.player["active_mode_major_hits"] = self.jackpots + self.super_jackpots
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SUPER JACKPOT",
            message_mode_subtitle="",
            message_mode_value=self.SUPER_JACKPOT,
        )
        self.machine.events.post("play_mode_super_jackpot")
        self._flash_super_gi()
        self._update_status()

    def _super_timeout(self, **kwargs):
        if not self.super_active:
            return
        self.super_active = False
        self.machine.events.post("crime_wave_super_off")
        self._update_status()

    def _flash_super_gi(self):
        # Pause the area shows during the celebration so they cannot overwrite
        # the exact 250ms-on / 50ms-off GI burst.
        self.machine.events.post("crime_wave_area_shows_stop")
        self.machine.events.post("crime_wave_super_gi_on")
        sequence = (
            (250, "crime_wave_super_gi_off"),
            (300, "crime_wave_super_gi_on"),
            (550, "crime_wave_super_gi_off"),
            (600, "crime_wave_super_gi_on"),
            (850, "crime_wave_super_gi_off"),
        )
        for index, (delay_ms, event) in enumerate(sequence):
            self.delay.add(
                name=f"crime_wave_super_gi_{index}",
                ms=delay_ms,
                callback=self._post_event,
                event=event,
            )
        self.delay.add(
            name="crime_wave_super_gi_restore",
            ms=900,
            callback=self._restore_lighting_after_super,
        )

    def _post_event(self, event):
        self.machine.events.post(event)

    def _restore_lighting_after_super(self):
        if self.mode_done:
            return
        self.machine.events.post("crime_wave_gi_restore")
        for area in self.AREAS:
            if area not in self.lit_areas:
                self.machine.events.post(f"crime_wave_area_{area}_available")
            elif area in self.warning_areas:
                self.machine.events.post(f"crime_wave_area_{area}_warning")
            else:
                self.machine.events.post(f"crime_wave_area_{area}_active")
        if self.super_active:
            self.machine.events.post("crime_wave_super_on")

    def _update_gate(self):
        count = len(self.lit_areas)
        if not self.gate_open and count >= 3:
            self.gate_open = True
            self.machine.events.post("rooftop_diverter_open")
        elif self.gate_open and count <= 2:
            self.gate_open = False
            self.roof_visit_active = False
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
        self.machine.game.player["active_mode_hits"] = self.max_areas_lit
        if self.super_active:
            title = "SUPER JACKPOT"
            value = f"{self.SUPER_JACKPOT:,} - WEB TARGETS"
        elif len(self.lit_areas) == 5:
            title = "ALL 5 CAPTURED"
            value = "COLLECT ROOF REWARD"
        elif len(self.lit_areas) >= 3:
            title = "ROOF OPEN"
            value = f"{len(self.lit_areas)} OF 5 CAPTURED"
        else:
            title = "CAPTURE VILLAINS"
            value = f"{len(self.lit_areas)} OF 5"
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _balls_in_play(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return 0
        return int(player["balls_in_play"] or 0)
