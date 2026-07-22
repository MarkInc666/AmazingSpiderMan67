import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class ScarletSorcerer(CaseFileMixin, Mode):
    MODE_KEY = "scarlet_sorcerer"
    DISPLAY_NAME = "Scarlet Sorcerer"

    DEMON_SHOTS = (
        "left_web",
        "center_web",
        "left_drops",
        "right_drops",
        "left_pop",
        "right_pop",
    )
    DEMONS_REQUIRED = 4
    DEMON_ADD_INTERVAL_MS = 4000
    SCEPTER_TIMER_SECONDS = 20
    MORE_TIME_SCEPTER_SECONDS = 30
    DEMON_JACKPOT_VALUES = (200_000, 250_000, 300_000, 350_000)
    BIGGER_DEMON_JACKPOT_VALUES = (300_000, 350_000, 400_000, 450_000)
    BONUS_DEMON_VALUE = 500_000
    SCEPTER_SUPER_VALUE = 1_000_000
    BIGGER_SCEPTER_SUPER_VALUE = 1_500_000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.phase = "demons"
        self.mode_points = 0
        self.demons_destroyed = 0
        self.bonus_demons_destroyed = 0
        self.super_jackpots = 0
        self.scepter_seconds_left = 0
        self.shot_assist_used = False

        self.case_files = self.get_case_file_bonuses()
        self.demon_jackpot_values = (
            self.BIGGER_DEMON_JACKPOT_VALUES
            if self.has_case_file("bigger_jackpots")
            else self.DEMON_JACKPOT_VALUES
        )
        self.scepter_super_value = (
            self.BIGGER_SCEPTER_SUPER_VALUE
            if self.has_case_file("bigger_jackpots")
            else self.SCEPTER_SUPER_VALUE
        )
        self.scepter_timer_seconds = (
            self.MORE_TIME_SCEPTER_SECONDS
            if self.has_case_file("more_time")
            else self.SCEPTER_TIMER_SECONDS
        )

        self.selected_demons = random.sample(list(self.DEMON_SHOTS), self.DEMONS_REQUIRED)
        remaining = [shot for shot in self.DEMON_SHOTS if shot not in self.selected_demons]
        self.bonus_demon = random.choice(remaining) if self.has_case_file("more_jackpots") else None
        self.bonus_demon_available = False
        self.introduced_demons = []
        self.active_demons = set()
        self.destroyed_demons = set()

        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["active_mode_hits"] = 0
        player["active_mode_major_hits"] = 0
        player[f"{self.MODE_KEY}_state"] = 1

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "5TH DEMON WORTH 500K DURING SCEPTER TIMER"),
            ("bigger_jackpots", "BIGGER DEMON JACKPOTS AND 1.5M SUPER"),
            ("more_time", "SCEPTER TIMER EXTENDED TO 30 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST DEMON ALSO DESTROYS THE NEXT DEMON"),
        ])
        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        for shot in self.DEMON_SHOTS:
            self.add_mode_event_handler(
                f"scarlet_sorcerer_{shot}_hit",
                self._demon_hit,
                shot=shot,
            )

        self.add_mode_event_handler("scarlet_sorcerer_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("scarlet_sorcerer_complete_request", self._complete_mode)
        self.add_mode_event_handler("scarlet_sorcerer_fail_request", self._fail_mode)
        self.add_mode_event_handler("s_inlane_a_active", self._keep_gate_closed)
        self.add_mode_event_handler("s_inlane_b_active", self._keep_gate_closed)

        self.machine.events.post("scarlet_sorcerer_mode_started")
        self.machine.events.post("scarlet_sorcerer_gi_red")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("reset_drops")

        self._introduce_next_demon()
        self._show_message("DESTROY THE DEMONS", "4 DEMONS LIGHT OVER TIME", reminder=True)

    def mode_stop(self, **kwargs):
        self.delay.remove("scarlet_sorcerer_add_demon")
        self.delay.remove("scarlet_sorcerer_scepter_tick")
        self.machine.events.post("scarlet_sorcerer_clear_lights")
        self.machine.events.post("scarlet_sorcerer_stop_gi_flash")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("reset_drops")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _keep_gate_closed(self, **kwargs):
        if not self.mode_done and self.phase == "demons":
            self.machine.events.post("rooftop_diverter_close")

    def _introduce_next_demon(self):
        if self.mode_done or self.phase != "demons":
            return

        next_shot = self._next_unintroduced_required_demon()
        if next_shot is None:
            return

        self._light_required_demon(next_shot)
        self._schedule_next_demon()

    def _next_unintroduced_required_demon(self):
        for shot in self.selected_demons:
            if shot not in self.introduced_demons:
                return shot
        return None

    def _light_required_demon(self, shot):
        if shot not in self.introduced_demons:
            self.introduced_demons.append(shot)
        if shot not in self.destroyed_demons:
            self.active_demons.add(shot)
            self.machine.events.post("scarlet_sorcerer_demon_lit", shot=shot)
            self.machine.events.post(f"scarlet_sorcerer_light_{shot}")
        self._sync_vars()

    def _schedule_next_demon(self):
        if self.phase != "demons" or self._next_unintroduced_required_demon() is None:
            self.delay.remove("scarlet_sorcerer_add_demon")
            return
        self.delay.reset(
            name="scarlet_sorcerer_add_demon",
            ms=self.DEMON_ADD_INTERVAL_MS,
            callback=self._introduce_next_demon,
        )

    def _demon_hit(self, shot=None, **kwargs):
        if self.mode_done or shot not in self.active_demons:
            return

        if self.phase == "demons" and shot in self.selected_demons:
            self._destroy_required_demon(shot, assisted=False)
            return

        if self.phase == "scepter" and self.bonus_demon_available and shot == self.bonus_demon:
            self._collect_bonus_demon()

    def _destroy_required_demon(self, shot, assisted=False):
        if shot not in self.active_demons or shot in self.destroyed_demons:
            return

        self.active_demons.remove(shot)
        self.destroyed_demons.add(shot)
        self.demons_destroyed += 1
        jackpot = self.demon_jackpot_values[self.demons_destroyed - 1]
        self._score(jackpot)
        self.machine.events.post(f"scarlet_sorcerer_unlight_{shot}")
        self.machine.events.post(
            "scarlet_sorcerer_demon_destroyed",
            shot=shot,
            demons_destroyed=self.demons_destroyed,
            value=jackpot,
            assisted=assisted,
        )
        subtitle = f"{self.demons_destroyed} OF 4 DESTROYED"
        if assisted:
            subtitle = f"SHOT ASSIST - {subtitle}"
        self._show_jackpot("DEMON JACKPOT", jackpot, subtitle)
        self._sync_vars()

        if (
            not assisted
            and self.has_case_file("shot_assist")
            and not self.shot_assist_used
            and self.demons_destroyed < self.DEMONS_REQUIRED
        ):
            self.shot_assist_used = True
            self._use_shot_assist()

        if self.demons_destroyed >= self.DEMONS_REQUIRED:
            self._start_scepter_phase()

    def _use_shot_assist(self):
        next_shot = next(
            (shot for shot in self.selected_demons if shot not in self.destroyed_demons),
            None,
        )
        if next_shot is None:
            return

        # The next demon may not have reached its timed reveal yet. Introduce it now,
        # destroy it immediately, then restart the four-second reveal interval.
        if next_shot not in self.introduced_demons:
            self._light_required_demon(next_shot)
        self._destroy_required_demon(next_shot, assisted=True)
        if self.phase == "demons" and self.demons_destroyed < self.DEMONS_REQUIRED:
            self._schedule_next_demon()

    def _start_scepter_phase(self):
        if self.mode_done or self.phase != "demons":
            return

        self.phase = "scepter"
        self.delay.remove("scarlet_sorcerer_add_demon")
        self.active_demons.clear()
        self.machine.events.post("scarlet_sorcerer_clear_demon_lights")
        self.machine.events.post("scarlet_sorcerer_start_gi_flash")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("scarlet_sorcerer_scepter_lit")

        if self.bonus_demon:
            self.bonus_demon_available = True
            self.active_demons.add(self.bonus_demon)
            self.machine.events.post("scarlet_sorcerer_bonus_demon_lit", shot=self.bonus_demon)
            self.machine.events.post(f"scarlet_sorcerer_light_{self.bonus_demon}")

        self.scepter_seconds_left = self.scepter_timer_seconds
        self._sync_vars()
        subtitle = "SHOOT THE VUK"
        if self.bonus_demon_available:
            subtitle = "OPTIONAL 500K DEMON - THEN VUK"
        self._show_countdown("DESTROY THE SCEPTER", self.scepter_seconds_left, subtitle)
        self._schedule_scepter_tick()

    def _collect_bonus_demon(self):
        shot = self.bonus_demon
        if not shot or shot not in self.active_demons:
            return
        self.active_demons.remove(shot)
        self.destroyed_demons.add(shot)
        self.bonus_demon_available = False
        self.bonus_demons_destroyed = 1
        self._score(self.BONUS_DEMON_VALUE)
        self.machine.events.post(f"scarlet_sorcerer_unlight_{shot}")
        self.machine.events.post(
            "scarlet_sorcerer_bonus_demon_destroyed",
            shot=shot,
            value=self.BONUS_DEMON_VALUE,
        )
        self._show_jackpot("BONUS DEMON JACKPOT", self.BONUS_DEMON_VALUE, "NOW DESTROY THE SCEPTER")
        self._sync_vars()

    def _schedule_scepter_tick(self):
        self.delay.reset(
            name="scarlet_sorcerer_scepter_tick",
            ms=1000,
            callback=self._scepter_tick,
        )

    def _scepter_tick(self):
        if self.mode_done or self.phase != "scepter":
            return
        self.scepter_seconds_left -= 1
        self._sync_vars()
        if self.scepter_seconds_left <= 0:
            self._fail_mode()
            return
        subtitle = "SHOOT THE VUK"
        if self.bonus_demon_available:
            subtitle = "OPTIONAL 500K DEMON - THEN VUK"
        self._show_countdown("DESTROY THE SCEPTER", self.scepter_seconds_left, subtitle)
        self._schedule_scepter_tick()

    def _vuk_hit(self, **kwargs):
        if self.mode_done or self.phase != "scepter":
            return

        # The optional fifth demon is lost if the Super is collected first.
        if self.bonus_demon_available and self.bonus_demon in self.active_demons:
            self.active_demons.remove(self.bonus_demon)
            self.machine.events.post(f"scarlet_sorcerer_unlight_{self.bonus_demon}")
            self.bonus_demon_available = False

        self.delay.remove("scarlet_sorcerer_scepter_tick")
        self.super_jackpots = 1
        self._score(self.scepter_super_value)
        self._sync_vars()
        self.machine.events.post("scarlet_sorcerer_scepter_destroyed", value=self.scepter_super_value)
        self._show_jackpot("SUPER JACKPOT", self.scepter_super_value, "SCEPTER DESTROYED")
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.phase = "done"
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars()
        self.machine.events.post("scarlet_sorcerer_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.phase = "done"
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars()
        self.machine.events.post("scarlet_sorcerer_scepter_survived")
        self._show_message("THE SCEPTER SURVIVED", "SCARLET SORCERER ESCAPES")
        self.machine.events.post("scarlet_sorcerer_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.demons_destroyed + self.bonus_demons_destroyed
        player["active_mode_major_hits"] = self.super_jackpots

    def _show_message(self, title, subtitle="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value="",
            message_mode_seconds="",
            reminder=reminder,
        )

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _show_countdown(self, title, seconds, subtitle=""):
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value="",
            message_mode_seconds=seconds,
        )
