import random
from functools import partial

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class BoltonBoomer(CaseFileMixin, Mode):
    MODE_KEY = "bolton_boomer"
    DISPLAY_NAME = "Bolton and Boomer"

    TARGET_SCORE = 100_000
    SAUCER_SCORE = 100_000
    SUPER_VALUE = 500_000
    BIGGER_TARGET_SCORE = 150_000
    BIGGER_SAUCER_SCORE = 150_000
    BIGGER_SUPER_VALUE = 750_000
    SUPER_STEP = 100_000
    SUPER_CAP = 1_500_000
    NORMAL_SUPER_SECONDS = 20
    MORE_TIME_SUPER_SECONDS = 30
    NORMAL_OPENING_SAVE = 15
    SAFETY_NET_OPENING_SAVE = 25

    TARGETS = (
        "left_web", "center_web", "left_sling", "right_sling",
        "left_pop", "right_pop", "left_bank", "right_bank", "star",
    )
    SAUCER_EJECT_EVENTS = {
        1: "delayed_kickout_saucer_1",
        2: "delayed_kickout_saucer_2",
        3: "delayed_kickout_saucer_3",
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
        self.reset_active_mode_summary(stat_count=1)
        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.phase = "target"
        self.lit_target = None
        self.held_saucer = None
        self.super_number = 0
        self.super_jackpots = 0
        self.biggest_super = 0
        self.mode_points = 0
        self.super_seconds = self.MORE_TIME_SUPER_SECONDS if self.has_case_file("more_time") else self.NORMAL_SUPER_SECONDS
        self.opening_save_seconds = self.SAFETY_NET_OPENING_SAVE if self.has_case_file("safety_net") else self.NORMAL_OPENING_SAVE
        self.target_value = self.BIGGER_TARGET_SCORE if self.has_case_file("bigger_jackpots") else self.TARGET_SCORE
        self.saucer_value = self.BIGGER_SAUCER_SCORE if self.has_case_file("bigger_jackpots") else self.SAUCER_SCORE
        self.base_super_value = self.BIGGER_SUPER_VALUE if self.has_case_file("bigger_jackpots") else self.SUPER_VALUE
        self.current_super_value = self.base_super_value
        self.shot_assist_used = False
        self.timer_seconds_remaining = 0

        for target in self.TARGETS:
            self.add_mode_event_handler(f"bolton_boomer_target_{target}", self._target_hit, target=target)
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(f"bolton_boomer_saucer_{saucer}", partial(self._saucer_hit, saucer=saucer))
        self.add_mode_event_handler("bolton_boomer_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("multiball_bolton_boomer_multiball_ended", self._multiball_ended)

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")

        player = self.machine.game.player
        player["bolton_boomer_state"] = 1
        player["bolton_boomer_opening_save_seconds"] = self.opening_save_seconds
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SUPERS GROW 100K TO 1.5M"),
            ("bigger_jackpots", "150K TARGET / LOCK - 750K SUPER"),
            ("more_time", "30 SECOND TIMED SUPERS"),
            ("safety_net", "25 SECOND OPENING SAVE"),
            ("shot_assist", "FIRST TIMED SUPER AUTO-COLLECTS AT 10"),
        ])

        self.machine.events.post("reset_drops")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("bolton_boomer_start_multiball")
        self._start_target_stage()
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="THUNDER RUMBLE",
            message_mode_subtitle="HIT THE LIT TARGET",
        )

    def _start_target_stage(self):
        if self.mode_done:
            return
        self._cancel_super_delays()
        self.phase = "target"
        self.timer_seconds_remaining = 0
        self.lit_target = random.choice(self.TARGETS)
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("bolton_boomer_clear_lights")
        self.machine.events.post(f"bolton_boomer_light_{self.lit_target}")
        self._update_status()

    def _target_hit(self, target=None, **kwargs):
        if self.mode_done or self.phase != "target" or target != self.lit_target:
            return
        self._score(self.target_value)
        self.phase = "capture"
        self.lit_target = None
        self.machine.events.post("bolton_boomer_clear_targets")
        self.machine.events.post("bolton_boomer_saucers_ready")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="TARGET HIT",
            message_mode_subtitle="CAPTURE A BALL",
            message_mode_value=self.target_value,
        )
        self._update_status()

    def _saucer_hit(self, saucer=None, **kwargs):
        if self.mode_done or saucer not in self.SAUCER_EJECT_EVENTS:
            return

        if self.held_saucer is not None:
            self._eject_saucer(saucer, 1000)
            return

        if self.phase != "capture":
            self._eject_saucer(saucer, 1000)
            return

        self.held_saucer = saucer
        self.phase = "super"
        self.super_number += 1
        self._score(self.saucer_value)
        self.current_super_value = self._next_super_value()
        self.machine.events.post("bolton_boomer_saucers_not_ready")
        self.machine.events.post(f"bolton_boomer_saucer_{saucer}_held")
        self.machine.events.post("bolton_boomer_vuk_ready")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="BALL CAPTURED",
            message_mode_subtitle="SHOOT THE VUK",
            message_mode_value=self.saucer_value,
        )

        if self.super_number > 1:
            self._start_super_timer()
        self._update_status()

    def _start_super_timer(self):
        self.timer_seconds_remaining = self.super_seconds
        self.delay.reset(name="bolton_boomer_super_tick", ms=1000, callback=self._super_tick)
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            auto_ms = max(0, (self.super_seconds - 10) * 1000)
            self.delay.reset(name="bolton_boomer_shot_assist", ms=auto_ms, callback=self._shot_assist_collect)

    def _super_tick(self):
        if self.mode_done or self.phase != "super" or self.super_number <= 1:
            return
        self.timer_seconds_remaining = max(0, self.timer_seconds_remaining - 1)
        self._update_status()
        if self.timer_seconds_remaining <= 0:
            self._super_expired()
            return
        self.delay.reset(name="bolton_boomer_super_tick", ms=1000, callback=self._super_tick)

    def _shot_assist_collect(self):
        if self.mode_done or self.phase != "super" or self.super_number <= 1 or self.shot_assist_used:
            return
        self.shot_assist_used = True
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="SHOT ASSIST",
            message_mode_subtitle="SUPER AWARDED",
            message_mode_value=self.current_super_value,
        )
        self._collect_super(vuk_ball_present=False)

    def _vuk_hit(self, **kwargs):
        if self.mode_done or self.phase != "super" or self.held_saucer is None:
            self._eject_vuk(750)
            return
        self._collect_super(vuk_ball_present=True)

    def _collect_super(self, vuk_ball_present):
        if self.mode_done or self.phase != "super":
            return
        self._cancel_super_delays()
        value = self.current_super_value
        self._score(value)
        self.super_jackpots += 1
        self.biggest_super = max(self.biggest_super, value)
        self.phase = "release"
        self.timer_seconds_remaining = 0
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("bolton_boomer_vuk_not_ready")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="SUPER JACKPOT",
            message_mode_subtitle=f"SUPER {self.super_jackpots}",
            message_mode_value=value,
        )

        held = self.held_saucer
        self.held_saucer = None
        if vuk_ball_present:
            self._eject_vuk(2000)
        else:
            # Keep the same timing sequence even when Shot Assist spots the Super.
            self._eject_vuk(2000)
        self._eject_saucer(held, 4000)
        self.delay.reset(name="bolton_boomer_next_round", ms=4400, callback=self._start_target_stage)
        self._sync_vars()

    def _super_expired(self):
        if self.mode_done or self.phase != "super":
            return
        self._cancel_super_delays()
        self.phase = "release"
        self.timer_seconds_remaining = 0
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("bolton_boomer_vuk_not_ready")
        self.machine.events.post("show_mode_message", message_mode_title="SUPER MISSED", message_mode_subtitle="FIND ANOTHER TARGET")
        held = self.held_saucer
        self.held_saucer = None
        self._eject_saucer(held, 2000)
        self.delay.reset(name="bolton_boomer_next_round", ms=2400, callback=self._start_target_stage)
        self._sync_vars()

    def _next_super_value(self):
        if not self.has_case_file("more_jackpots"):
            return self.base_super_value
        return min(self.SUPER_CAP, self.base_super_value + (self.super_jackpots * self.SUPER_STEP))

    def _eject_saucer(self, saucer, delay_ms=0):
        if saucer in self.SAUCER_EJECT_EVENTS:
            self.machine.events.post(
                "request_saucer_eject",
                saucer_number=saucer,
                delay_ms=delay_ms,
            )

    def _eject_vuk(self, delay_ms=0):
        self.machine.events.post("request_vuk_eject", delay_ms=delay_ms)

    def _cancel_super_delays(self):
        for name in ("bolton_boomer_super_tick", "bolton_boomer_shot_assist"):
            self.delay.remove(name)

    def _multiball_ended(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._cancel_super_delays()
        self.delay.remove("bolton_boomer_next_round")
        self.machine.game.player["bolton_boomer_state"] = 2
        if self.held_saucer is not None:
            self._eject_saucer(self.held_saucer, 0)
            self.held_saucer = None
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("bolton_boomer_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["bolton_boomer_super_jackpots"] = self.super_jackpots
        player["bolton_boomer_biggest_super"] = self.biggest_super
        player["bolton_boomer_super_seconds"] = self.timer_seconds_remaining
        player["bolton_boomer_super_value"] = self.current_super_value

    def _update_status(self):
        if self.phase == "target":
            title = "HIT THE LIT TARGET"
            value = "START THE CAPTURE"
        elif self.phase == "capture":
            title = "CAPTURE A BALL"
            value = "ANY SAUCER"
        elif self.phase == "super":
            title = "SHOOT THE VUK"
            if self.super_number == 1:
                value = f"SUPER {self.current_super_value:,}"
            else:
                self.machine.events.post(
                    "update_mode_timer_status",
                    mode_status_title=f"SHOOT THE VUK - SUPER {self.current_super_value:,}",
                    mode_status_value=max(0, self.timer_seconds_remaining),
                )
                self._sync_vars()
                return
        else:
            title = "RELEASING BALLS"
            value = "GET READY"
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)
        self._sync_vars()

    def mode_stop(self, **kwargs):
        self._cancel_super_delays()
        self.delay.remove("bolton_boomer_next_round")
        self.machine.events.post("bolton_boomer_clear_lights")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        if self.held_saucer is not None:
            self._eject_saucer(self.held_saucer, 0)
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        vuk_switch = self.machine.switches.get("s_vuk_switch")
        if vuk_switch and self.machine.switch_controller.is_active(vuk_switch):
            if self.mode_done:
                self.machine.events.post("villain_summary_hold_vuk_until_done")
            else:
                self.machine.events.post("request_vuk_eject")
        super().mode_stop(**kwargs)
