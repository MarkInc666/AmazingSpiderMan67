from functools import partial

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class DrManta(CaseFileMixin, Mode):
    """Dr. Manta: staged VUK-to-saucer relay mode.

    Ball 1 is held in the VUK while a second ball is served. Lock Ball 2 in
    any saucer, then the VUK ball is fired to the rooftop for a timed jackpot
    phase. At timeout every flipper is disabled until the active ball reaches
    the trough; the held saucer ball is then released as the continuing ball.
    """

    MODE_KEY = "dr_manta"
    DISPLAY_NAME = "DR. MANTA"

    BASE_VUK_VALUE = 100_000
    BASE_SAUCER_VALUE = 150_000
    BASE_JACKPOT = 100_000

    BIGGER_VUK_VALUE = 150_000
    BIGGER_SAUCER_VALUE = 200_000
    BIGGER_STARTING_JACKPOT = 200_000

    NORMAL_JACKPOT_STEP = 50_000
    MORE_JACKPOTS_STEP = 75_000
    JACKPOT_CAP = 1_000_000

    NORMAL_ATTACK_SECONDS = 20
    MORE_TIME_ATTACK_SECONDS = 28
    NORMAL_SECOND_BALL_SAVE = 10
    SAFETY_NET_SECOND_BALL_SAVE = 25

    SAUCER_EJECT_EVENTS = {
        1: "delayed_kickout_saucer_1",
        2: "delayed_kickout_saucer_2",
        3: "delayed_kickout_saucer_3",
    }

    TARGET_LIGHT_EVENTS = {
        1: "dr_manta_shot_assist_left_ready",
        2: "dr_manta_shot_assist_center_ready",
        3: "dr_manta_shot_assist_right_ready",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.case_files = self.get_case_file_bonuses()
        self.mode_done = False
        self.phase = "shoot_vuk"
        self.held_saucer = None
        self.attack_seconds_remaining = 0
        self.jackpot_hits = 0
        self.biggest_jackpot = 0
        self.mode_points = 0
        self.shot_assist_available = self.has_case_file("shot_assist")

        if self.has_case_file("bigger_jackpots"):
            self.vuk_value = self.BIGGER_VUK_VALUE
            self.saucer_value = self.BIGGER_SAUCER_VALUE
            self.current_jackpot = self.BIGGER_STARTING_JACKPOT
        else:
            self.vuk_value = self.BASE_VUK_VALUE
            self.saucer_value = self.BASE_SAUCER_VALUE
            self.current_jackpot = self.BASE_JACKPOT

        self.jackpot_step = (
            self.MORE_JACKPOTS_STEP
            if self.has_case_file("more_jackpots")
            else self.NORMAL_JACKPOT_STEP
        )
        self.attack_seconds = (
            self.MORE_TIME_ATTACK_SECONDS
            if self.has_case_file("more_time")
            else self.NORMAL_ATTACK_SECONDS
        )
        self.second_ball_save_seconds = (
            self.SAFETY_NET_SECOND_BALL_SAVE
            if self.has_case_file("safety_net")
            else self.NORMAL_SECOND_BALL_SAVE
        )

        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)
        self.add_mode_event_handler("s_saucer_1_active", partial(self._saucer_hit, saucer=1))
        self.add_mode_event_handler("s_saucer_2_active", partial(self._saucer_hit, saucer=2))
        self.add_mode_event_handler("s_saucer_3_active", partial(self._saucer_hit, saucer=3))
        self.add_mode_event_handler("s_trispinner_opto_active", self._spinner_hit)
        self.add_mode_event_handler("s_web_spinner_active", self._spinner_hit)
        self.add_mode_event_handler("s_upper_target_left_active", partial(self._upper_target_hit, target=1))
        self.add_mode_event_handler("s_upper_target_center_active", partial(self._upper_target_hit, target=2))
        self.add_mode_event_handler("s_upper_target_right_active", partial(self._upper_target_hit, target=3))
        self.add_mode_event_handler("balldevice_bd_trough_ball_enter", self._trough_ball_enter)
        self.add_mode_event_handler("multiball_dr_manta_relay_ended", self._relay_multiball_ended)
        self.add_mode_event_handler("ball_ending", self._ball_ending)

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        player["dr_manta_second_ball_save_seconds"] = self.second_ball_save_seconds
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SPINNERS ADD 75K TO JACKPOT"),
            ("bigger_jackpots", "150K VUK / 200K SAUCER / 200K JP"),
            ("more_time", "28 SECOND ATTACK"),
            ("safety_net", "25 SECOND SECOND-BALL SAVE"),
            ("shot_assist", "MATCHED UPPER TARGET SCORES 3X ONCE"),
        ])

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("dr_manta_clear_all")
        self.machine.events.post("dr_manta_phase_vuk")
        self._show_message("ENTER MANTA'S CITY", "SHOOT THE VUK", reminder=True)
        self._update_status()

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            return

        if self.phase != "shoot_vuk":
            # The VUK is not a scoring shot after the first capture.
            self._eject_vuk(750)
            return

        self._score(self.vuk_value)
        self.phase = "lock_saucer"
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("dr_manta_phase_saucers")
        self.machine.events.post("dr_manta_start_relay")
        self.machine.events.post("dr_manta_enable_second_ball_save")
        self._show_message("BALL ONE CAPTURED", "LOCK BALL TWO IN A SAUCER", value=self.vuk_value, reminder=True)
        self._update_status()

    def _saucer_hit(self, saucer=None, **kwargs):
        if self.mode_done or saucer not in self.SAUCER_EJECT_EVENTS:
            return

        if self.phase != "lock_saucer" or self.held_saucer is not None:
            self._eject_saucer(saucer, 750)
            return

        self.held_saucer = saucer
        self.phase = "attack"
        self._score(self.saucer_value)
        self.attack_seconds_remaining = self.attack_seconds
        self.machine.events.post("dr_manta_disable_second_ball_save")
        self.machine.events.post("dr_manta_saucers_off")
        self.machine.events.post(f"dr_manta_saucer_{saucer}_held")
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("dr_manta_attack_started")

        if self.shot_assist_available:
            self.machine.events.post(self.TARGET_LIGHT_EVENTS[saucer])

        # Let the saucer settle before sending Ball 1 to the rooftop.
        self._eject_vuk(500)
        self.delay.reset(name="dr_manta_attack_tick", ms=1000, callback=self._attack_tick)
        self._show_message("MOUNTAIN MONSTER", f"{self.attack_seconds_remaining} SECONDS", value=self.saucer_value)
        self._update_status()

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.phase != "attack":
            return

        old_value = self.current_jackpot
        self.current_jackpot = min(self.JACKPOT_CAP, self.current_jackpot + self.jackpot_step)
        if self.current_jackpot != old_value:
            self.machine.events.post("dr_manta_spinner_increased")
        self._sync_vars()
        self._update_status()

    def _upper_target_hit(self, target=None, **kwargs):
        if self.mode_done or self.phase != "attack" or target not in (1, 2, 3):
            return

        multiplier = 1
        if (
            self.shot_assist_available
            and self.held_saucer == target
        ):
            multiplier = 3
            self.shot_assist_available = False
            self.machine.events.post("dr_manta_shot_assist_consumed")

        award = self.current_jackpot * multiplier
        self._score(award)
        self.jackpot_hits += 1
        self.biggest_jackpot = max(self.biggest_jackpot, award)
        self.machine.events.post(
            "dr_manta_jackpot_collected",
            target=target,
            multiplier=multiplier,
            value=award,
        )
        title = "3X JACKPOT" if multiplier == 3 else "JACKPOT"
        self._show_message(title, self._format_score(award), value=self.mode_points, event="show_mode_jackpot")
        self._sync_vars()
        self._update_status()

    def _attack_tick(self):
        if self.mode_done or self.phase != "attack":
            return

        self.attack_seconds_remaining = max(0, self.attack_seconds_remaining - 1)
        self._sync_vars()
        self._update_status()

        if self.attack_seconds_remaining <= 0:
            self._attack_expired()
            return

        if self.attack_seconds_remaining == 5:
            self.machine.events.post("dr_manta_five_seconds")

        self.delay.reset(name="dr_manta_attack_tick", ms=1000, callback=self._attack_tick)

    def _attack_expired(self):
        if self.mode_done or self.phase != "attack":
            return

        self.phase = "drain_wait"
        self.attack_seconds_remaining = 0
        self.machine.events.post("dr_manta_attack_expired")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("cmd_flippers_disable")
        self._show_message("TIME EXPIRED", "FLIPPERS DISABLED", value=self.mode_points)
        self._sync_vars()
        self._update_status()

    def _trough_ball_enter(self, **kwargs):
        if self.mode_done or self.phase != "drain_wait":
            return
        self._finish_relay()

    def _relay_multiball_ended(self, **kwargs):
        # Before the saucer lock, losing the served ball ends the attempt and
        # releases the VUK ball. After the lock, the custom relay owns ending.
        if self.mode_done or self.phase != "lock_saucer":
            return
        self._show_message("SECOND BALL LOST", "MANTA ESCAPES")
        self._eject_vuk(0)
        self._complete_mode(release_saucer=False, enable_flippers=True)

    def _finish_relay(self):
        if self.mode_done:
            return
        self._show_message("ATTACK COMPLETE", f"{self.jackpot_hits} JACKPOTS", value=self.mode_points, event="show_mode_jackpot")
        self._complete_mode(release_saucer=True, enable_flippers=True)

    def _complete_mode(self, release_saucer=True, enable_flippers=True):
        if self.mode_done:
            return

        self.mode_done = True
        self.delay.remove("dr_manta_attack_tick")
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2

        self.machine.events.post("dr_manta_disable_second_ball_save")
        self.machine.events.post("dr_manta_clear_all")
        self.machine.events.post("rooftop_diverter_close")

        if release_saucer and self.held_saucer is not None:
            self._eject_saucer(self.held_saucer, 0)
            self.held_saucer = None

        if enable_flippers:
            self.machine.events.post("cmd_flippers_enable")

        self.machine.events.post("dr_manta_mode_complete")

    def _ball_ending(self, **kwargs):
        self.delay.remove("dr_manta_attack_tick")
        self.machine.events.post("dr_manta_disable_second_ball_save")

    def _eject_saucer(self, saucer, delay_ms=0):
        event = self.SAUCER_EJECT_EVENTS.get(saucer)
        if not event:
            return
        if delay_ms <= 0:
            self.machine.events.post(event)
            return
        self.delay.reset(
            name=f"dr_manta_eject_saucer_{saucer}",
            ms=delay_ms,
            callback=self.machine.events.post,
            event=event,
        )

    def _eject_vuk(self, delay_ms=0):
        if delay_ms <= 0:
            self.machine.events.post("up_kick")
            return
        self.delay.reset(
            name="dr_manta_eject_vuk",
            ms=delay_ms,
            callback=self.machine.events.post,
            event="up_kick",
        )

    def _score(self, points):
        points = int(points)
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.jackpot_hits
        player["active_mode_major_hits"] = self.jackpot_hits

    def _update_status(self):
        if self.phase == "shoot_vuk":
            title = "SHOOT THE VUK"
            value = self._format_score(self.vuk_value)
        elif self.phase == "lock_saucer":
            title = "LOCK BALL TWO"
            value = f"ANY SAUCER - {self._format_score(self.saucer_value)}"
        elif self.phase == "attack":
            title = f"MOUNTAIN MONSTER - {self.attack_seconds_remaining}"
            value = f"JP {self._format_score(self.current_jackpot)}  HITS {self.jackpot_hits}"
        else:
            title = "TIME EXPIRED"
            value = "WAIT FOR BALL TO DRAIN"

        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)
        self._sync_vars()

    def _show_message(self, title, subtitle="", value="", event="show_mode_message", reminder=False):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            reminder=reminder,
        )

    @staticmethod
    def _format_score(value):
        return f"{int(value):,}"

    def mode_stop(self, **kwargs):
        self.delay.remove("dr_manta_attack_tick")
        self.delay.remove("dr_manta_eject_vuk")
        for saucer in (1, 2, 3):
            self.delay.remove(f"dr_manta_eject_saucer_{saucer}")

        self.machine.events.post("dr_manta_disable_second_ball_save")
        self.machine.events.post("dr_manta_clear_all")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("cmd_flippers_enable")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.clear_active_case_file_helpers()

        # Cleanup for abnormal stops only. Normal completion clears held_saucer
        # before this method runs, so the continuing ball is not double-ejected.
        if self.held_saucer is not None:
            self.machine.events.post(self.SAUCER_EJECT_EVENTS[self.held_saucer])
            self.held_saucer = None

        if self.phase in ("shoot_vuk", "lock_saucer") and not self.mode_done:
            self.machine.events.post("up_kick")

        super().mode_stop(**kwargs)
