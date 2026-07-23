from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin

import random


class Fakir(CaseFileMixin, Mode):
    """Fakir: Ruby Heist.

    2-ball multiball. Saucers are fake rubies. A saucer hold opens the roof
    and reveals the real ruby at an upper target. Spinners build the current
    Ruby/Super value. Three Ruby Jackpots qualify one Super Jackpot. After the
    Super is collected, additional Ruby Jackpots continue at base value until
    the multiball ends.
    """

    NORMAL_RUBY_BASE = 250_000
    BIGGER_RUBY_BASE = 400_000
    SPINNER_ADD = 25_000
    SAUCER_LOCK_SCORE = 25_000
    NORMAL_RUBY_TIMER_MS = 10_000
    MORE_TIME_RUBY_TIMER_MS = 15_000
    SAUCER_EJECT_SAFETY_NET_MS = 650
    GI_RESTORE_AFTER_JACKPOT_MS = 650

    SAUCER_KICKOUTS = {
        1: "kickout_saucer_1",
        2: "kickout_saucer_2",
        3: "kickout_saucer_3",
    }

    SAUCER_TARGET_MAP = {
        1: "left",
        2: "center",
        3: "right",
    }

    TARGET_NAMES = {
        "left": "UPPER LEFT",
        "center": "UPPER CENTER",
        "right": "UPPER RIGHT",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.ruby_active = False
        self.locked_saucer = None
        self.current_target = None
        self.current_award_is_super = False
        self.super_qualified = False
        self.super_collected = False
        self.more_jackpots_used = False
        self.safety_net_started = False
        self.shot_assist_available = False
        self.shot_assist_active = False

        self.ruby_base_value = self.NORMAL_RUBY_BASE
        self.ruby_timer_ms = self.NORMAL_RUBY_TIMER_MS
        self.current_jackpot_value = self.ruby_base_value
        self.spinner_build = 0
        self.rubies_collected = 0
        self.total_ruby_jackpot_value = 0
        self.super_jackpot_value = 0
        self.super_jackpots_collected = 0
        self.total_rubies_collected = 0
        self.mode_points = 0
        self.incorrect_shots = 0

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("fakir")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "FIRST POST-SUPER RUBY IS 2X"),
            ("bigger_jackpots", "BIGGER RUBY JACKPOTS"),
            ("more_time", "LONGER REAL RUBY TIMER"),
            ("safety_net", "BALL SAVE AFTER FIRST SAUCER KICKOUT"),
            ("shot_assist", "FIRST REVEAL LIGHTS ALL UPPER TARGETS"),
        ])

        self.add_mode_event_handler("fakir_saucer_1_hit", self._saucer_hit, saucer=1)
        self.add_mode_event_handler("fakir_saucer_2_hit", self._saucer_hit, saucer=2)
        self.add_mode_event_handler("fakir_saucer_3_hit", self._saucer_hit, saucer=3)
        self.add_mode_event_handler("fakir_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("fakir_upper_left_hit", self._upper_target_hit, target="left")
        self.add_mode_event_handler("fakir_upper_center_hit", self._upper_target_hit, target="center")
        self.add_mode_event_handler("fakir_upper_right_hit", self._upper_target_hit, target="right")
        self.add_mode_event_handler("fakir_ruby_timer_expired_request", self._ruby_timer_expired)
        self.add_mode_event_handler("fakir_multiball_ended", self._multiball_ended)

        self._sync_player_vars("SHOOT SAUCERS", "FAKE RUBIES")
        self.machine.events.post("fakir_startup_complete")

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.delay.remove("fakir_ruby_timer")
        self.delay.remove("fakir_restore_base_gi")
        self.delay.remove("fakir_safety_net_after_kickout")
        self._release_locked_saucer()
        self.machine.events.post("fakir_all_lights_off")
        self.machine.events.post("fakir_stop_all_gi")
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        if self.has_case_file("bigger_jackpots"):
            self.ruby_base_value = self.BIGGER_RUBY_BASE
            self.current_jackpot_value = self.ruby_base_value

        if self.has_case_file("more_time"):
            self.ruby_timer_ms = self.MORE_TIME_RUBY_TIMER_MS

        if self.has_case_file("shot_assist"):
            self.shot_assist_available = True

    def _saucer_hit(self, saucer, **kwargs):
        if self._inactive() or self.ruby_active:
            return

        self.locked_saucer = saucer
        self.spinner_build = 0
        self.current_award_is_super = self.super_qualified and not self.super_collected

        if self.current_award_is_super:
            self.current_jackpot_value = self.super_jackpot_value
            title = "SUPER RUBY"
        else:
            self.current_jackpot_value = self.ruby_base_value
            title = "REAL RUBY"

        self.current_target = self.SAUCER_TARGET_MAP.get(saucer, random.choice(["left", "center", "right"]))
        self.shot_assist_active = self.shot_assist_available
        self.shot_assist_available = False
        self.ruby_active = True

        self._score(self.SAUCER_LOCK_SCORE)
        self._sync_player_vars(title, self.TARGET_NAMES[self.current_target])
        self.machine.events.post("fakir_fake_ruby_locked", saucer=saucer, target=self.current_target, value=self.current_jackpot_value)
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("show_mode_message", message_mode_title="FAKE RUBY!", message_mode_subtitle=f"{self.TARGET_NAMES[self.current_target]}", message_mode_value=self.current_jackpot_value)
        self._light_current_target()

        self.delay.remove("fakir_ruby_timer")
        self.delay.add(
            name="fakir_ruby_timer",
            ms=self.ruby_timer_ms,
            callback=self._ruby_timer_expired,
        )

    def _spinner_hit(self, **kwargs):
        if self._inactive() or not self.ruby_active:
            return

        self.spinner_build += self.SPINNER_ADD
        self.current_jackpot_value += self.SPINNER_ADD
        if self.current_award_is_super:
            self.super_jackpot_value = self.current_jackpot_value
            title = "SUPER BUILD"
        else:
            title = "RUBY BUILD"

        self._sync_player_vars(title, f"+{self.SPINNER_ADD:,}")
        self.machine.events.post("fakir_spinner_build", value=self.current_jackpot_value, build=self.spinner_build)

    def _upper_target_hit(self, target, **kwargs):
        if self._inactive() or not self.ruby_active:
            return

        if not self.shot_assist_active and target != self.current_target:
            self.machine.events.post("show_mode_message", message_mode_title="WRONG TARGET", message_mode_subtitle=self.TARGET_NAMES[self.current_target])
            return

        self.delay.remove("fakir_ruby_timer")
        award = self.current_jackpot_value

        if self.current_award_is_super:
            self._collect_super(award)
        else:
            self._collect_ruby(award)

        self._end_ruby_attempt(release_saucer=True, jackpot_collected=True)

    def _collect_ruby(self, award):
        if self.super_collected and self.has_case_file("more_jackpots") and not self.more_jackpots_used:
            award *= 2
            self.current_jackpot_value = award
            self.more_jackpots_used = True
            self.machine.events.post("fakir_more_jackpots_ruby")

        self._score(award)
        self.rubies_collected += 1
        self.total_rubies_collected += 1

        if not self.super_collected and self.rubies_collected <= 3:
            self.total_ruby_jackpot_value += award
            self.super_jackpot_value = self.total_ruby_jackpot_value
            if self.rubies_collected >= 3:
                self.super_qualified = True

        self.machine.events.post("fakir_ruby_jackpot_collected", value=award, rubies=self.rubies_collected)
        self.machine.events.post("show_mode_jackpot", message_mode_title="RUBY JACKPOT", message_mode_subtitle=f"RUBY {self.total_rubies_collected}", message_mode_value=award)
        self._sync_player_vars("RUBY JACKPOT", f"{award:,}")

    def _collect_super(self, award):
        self._score(award)
        self.super_collected = True
        self.super_qualified = False
        self.super_jackpots_collected += 1
        self.machine.events.post("fakir_super_jackpot_collected", value=award)
        self.machine.events.post("show_mode_jackpot", message_mode_title="SUPER RUBY JACKPOT", message_mode_subtitle="THE REAL RUBY", message_mode_value=award)
        self._sync_player_vars("SUPER JACKPOT", f"{award:,}")

    def _ruby_timer_expired(self, **kwargs):
        if self._inactive() or not self.ruby_active:
            return

        self.incorrect_shots += 1
        self.machine.events.post("fakir_ruby_timer_expired", target=self.current_target)
        self.machine.events.post("show_mode_message", message_mode_title="RUBY VANISHES", message_mode_subtitle="SHOOT SAUCER AGAIN")
        self._sync_player_vars("RUBY VANISHED", "SHOOT SAUCER")
        self._end_ruby_attempt(release_saucer=True, jackpot_collected=False)

    def _end_ruby_attempt(self, release_saucer=True, jackpot_collected=False):
        self.machine.events.post("fakir_all_targets_off")
        self.machine.events.post("rooftop_diverter_close")

        if jackpot_collected:
            self.machine.events.post("fakir_restore_base_gi_delayed")
            self.delay.remove("fakir_restore_base_gi")
            self.delay.add(
                name="fakir_restore_base_gi",
                ms=self.GI_RESTORE_AFTER_JACKPOT_MS,
                callback=self._restore_base_gi,
            )
        else:
            self.machine.events.post("fakir_restore_base_gi")

        released_saucer = self.locked_saucer
        self.ruby_active = False
        self.locked_saucer = None
        self.current_target = None
        self.current_award_is_super = False
        self.shot_assist_active = False
        self.spinner_build = 0
        self.current_jackpot_value = self.ruby_base_value if not self.super_qualified else self.super_jackpot_value

        if release_saucer and released_saucer:
            self._release_saucer(released_saucer)

        if not self.mode_done:
            if self.super_qualified and not self.super_collected:
                self._sync_player_vars("SUPER READY", "SHOOT SAUCER")
            else:
                self._sync_player_vars("SHOOT SAUCERS", "FAKE RUBIES")

    def _restore_base_gi(self, **kwargs):
        if not self._inactive() and not self.ruby_active:
            self.machine.events.post("fakir_restore_base_gi")

    def _release_saucer(self, saucer):
        kickout = self.SAUCER_KICKOUTS.get(saucer)
        if kickout:
            self.machine.events.post(kickout)
            if self.has_case_file("safety_net") and not self.safety_net_started:
                self.safety_net_started = True
                self.delay.remove("fakir_safety_net_after_kickout")
                self.delay.add(
                    name="fakir_safety_net_after_kickout",
                    ms=self.SAUCER_EJECT_SAFETY_NET_MS,
                    callback=self._start_safety_net_ball_save,
                )

    def _release_locked_saucer(self):
        if self.locked_saucer:
            self._release_saucer(self.locked_saucer)
            self.locked_saucer = None

    def _start_safety_net_ball_save(self, **kwargs):
        if not self._inactive():
            self.machine.events.post("start_case_file_ball_save")
            self.machine.events.post("show_mode_message", message_mode_title="SAFETY NET", message_mode_subtitle="BALL SAVE ACTIVE")

    def _light_current_target(self):
        self.machine.events.post("fakir_all_targets_off")
        if self.shot_assist_active:
            self.machine.events.post("fakir_real_ruby_all_targets_lit")
            return

        if self.current_target == "left":
            self.machine.events.post("fakir_real_ruby_left_lit")
        elif self.current_target == "center":
            self.machine.events.post("fakir_real_ruby_center_lit")
        elif self.current_target == "right":
            self.machine.events.post("fakir_real_ruby_right_lit")

    def _multiball_ended(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("fakir_ruby_timer")
        self.machine.game.player["fakir_state"] = 2
        self._release_locked_saucer()
        self.machine.events.post("fakir_all_lights_off")
        self.machine.events.post("fakir_stop_all_gi")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("show_mode_message_long", message_mode_title="FAKIR DEFEATED", message_mode_subtitle="RUBY HEIST STOPPED")
        self.machine.events.post("fakir_mode_complete")

    def _score(self, points):
        self.machine.game.player["score"] += points
        self.mode_points += points
        self._sync_player_vars()

    def _sync_player_vars(self, status=None, target=None):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return

        # Keep player variables lean. Detailed Ruby state stays in this mode's
        # Python instance; only generic summary counters are published.
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.total_rubies_collected
        player["active_mode_major_hits"] = self.super_jackpots_collected
        self._update_mode_status()

    def _update_mode_status(self):
        if getattr(self, "super_lit", False):
            title = "SUPER JACKPOT LIT"
            value = f"RUBIES {self.total_rubies_collected}"
        elif getattr(self, "ruby_attempt_active", False):
            title = "HIT REVEALED RUBY"
            value = f"RUBIES {self.total_rubies_collected}/3"
        else:
            title = "SAUCERS REVEAL RUBY"
            value = f"RUBIES {self.total_rubies_collected}/3"
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)

    def _inactive(self):
        if self.mode_done:
            return True
        if self.machine.game.player["villain_mode_in_summary"] is True:
            return True
        return False
