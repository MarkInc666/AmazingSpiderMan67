from dataclasses import dataclass
from functools import partial
import random
import time

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


@dataclass(frozen=True)
class GoblinShot:
    name: str
    event: str


class Goblin(CaseFileMixin, Mode):
    """Green Goblin two-ball risk/reward multiball."""

    CHAOS_START = 250_000
    CHAOS_MIN = 50_000
    CHAOS_MAX = 1_000_000
    UNSAFE_SCORE = 20_000
    UNSAFE_LOSS = 150_000
    EXTRA_SAUCER_SCORE = 50_000

    SAFE_TIME_SECONDS = 10
    MORE_TIME_SECONDS = 15
    SAFE_IMMEDIATE_SCORE = 100_000
    MORE_JACKPOTS_SCORE = 150_000
    SAFE_BONUS_VALUES = (100_000, 125_000, 150_000, 175_000, 200_000, 225_000)
    BIGGER_SAFE_BONUS_VALUES = (150_000, 175_000, 200_000, 225_000, 250_000, 275_000)

    UPPER_GATE_SHOTS = set()

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.case_files = self.get_case_file_bonuses()
        self.more_jackpots = self.has_case_file("more_jackpots")
        self.bigger_jackpots = self.has_case_file("bigger_jackpots")
        self.more_time = self.has_case_file("more_time")
        self.safety_net_available = self.has_case_file("safety_net")
        self.shot_assist_available = self.has_case_file("shot_assist")
        self.safety_net_used = False
        self.shot_assist_used = False

        self.publish_case_file_bonus_events("goblin")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SAFE SHOTS SCORE 150K"),
            ("bigger_jackpots", "BIGGER CHAOS BONUS BUILDS"),
            ("more_time", "15 SECOND SAFE PHASE"),
            ("safety_net", "BALL SAVE AFTER FIRST RELEASE"),
            ("shot_assist", "FIRST SAFE HIT AWARDS ANOTHER"),
        ])

        self.shots = [
            GoblinShot("star", "goblin_star_hit"),
            GoblinShot("pops", "goblin_pops_hit"),
            GoblinShot("left_web", "goblin_left_web_hit"),
            GoblinShot("right_web", "goblin_right_web_hit"),
            GoblinShot("left_drops", "goblin_left_drops_hit"),
            GoblinShot("right_drops", "goblin_right_drops_hit"),
        ]

        self.active_shots = set()
        self.current_flashing = set()
        self.current_solid = set()
        self.hold_active = False
        self.held_saucer = None
        self.mode_finishing = False
        self.bonus_paid = False
        self.safe_hit_count = 0
        self.safe_seconds_remaining = 0
        self.message_queue_next_time = time.monotonic()
        self.message_sequence = 0
        self.message_delay_names = set()

        for shot in self.shots:
            self.add_mode_event_handler(shot.event, self.shot_hit, shot_name=shot.name)

        self.add_mode_event_handler("goblin_saucer_1_hit", partial(self.saucer_hit, saucer=1))
        self.add_mode_event_handler("goblin_saucer_2_hit", partial(self.saucer_hit, saucer=2))
        self.add_mode_event_handler("goblin_saucer_3_hit", partial(self.saucer_hit, saucer=3))
        self.add_mode_event_handler("goblin_collect_bonus", self.collect_banked_bonus)
        self.add_mode_event_handler("ball_ending", self.collect_banked_bonus)
        self.add_mode_event_handler("multiball_goblin_chaos_multiball_started", self.multiball_started)
        self.add_mode_event_handler("multiball_goblin_chaos_multiball_ended", self.multiball_ended)

        self.begin_mode()

    def begin_mode(self):
        player = self.machine.game.player
        player["goblin_chaos_bonus"] = self.CHAOS_START
        player["goblin_bonus_banked"] = 0
        player["goblin_chaos_lock"] = 0
        player["goblin_hold_count"] = 0
        player["goblin_hold_active"] = 0
        player["goblin_attacks_value"] = 0
        player["active_mode_points"] = 0
        player["goblin_state"] = 1
        player["goblin_jackpot_value"] = self.SAFE_IMMEDIATE_SCORE

        self.machine.events.post("reset_drops")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("goblin_lite_saucers")
        self.machine.events.post("goblin_start_multiball")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="CHAOS MULTIBALL",
            message_mode_subtitle="HIT SAUCER TO BANK BONUS",
        )
        self.start_unsafe_phase()

    # ------------------------------------------------------------------
    # Phase control
    # ------------------------------------------------------------------

    def start_unsafe_phase(self, **kwargs):
        if self.mode_finishing:
            return
        self.hold_active = False
        self.machine.game.player["goblin_hold_active"] = 0
        self.safe_seconds_remaining = 0
        self.safe_hit_count = 0
        self.clear_shot_shows()
        self.active_shots = {shot.name for shot in self.shots}
        self.current_solid = set(self.active_shots)
        self.current_flashing.clear()
        for shot_name in self.current_solid:
            self.machine.events.post(f"goblin_solid_{shot_name}")
        self.machine.events.post("goblin_gi_unsafe")
        self.machine.events.post("goblin_lite_saucers")
        self._update_mode_status()

    def start_safe_phase(self, saucer):
        self.hold_active = True
        self.held_saucer = saucer
        player = self.machine.game.player
        player["goblin_hold_active"] = 1
        player["goblin_hold_count"] += 1
        self.safe_hit_count = 0
        self.safe_seconds_remaining = self.MORE_TIME_SECONDS if self.more_time else self.SAFE_TIME_SECONDS
        self.clear_shot_shows()
        self.active_shots = {shot.name for shot in self.shots}
        self.current_flashing = set(self.active_shots)
        self.current_solid.clear()
        for shot_name in self.current_flashing:
            self.machine.events.post(f"goblin_lite_{shot_name}")
        self.machine.events.post("goblin_gi_safe")
        self.machine.events.post("goblin_lite_saucers")
        self.machine.events.post("goblin_hold_started", saucer=saucer)
        self._update_mode_status()
        self.delay.remove("goblin_safe_tick")
        self.delay.add(name="goblin_safe_tick", ms=1000, callback=self.safe_tick)

    def safe_tick(self, **kwargs):
        if self.mode_finishing or not self.hold_active:
            return
        self.safe_seconds_remaining = max(0, self.safe_seconds_remaining - 1)
        self._update_mode_status()
        if self.safe_seconds_remaining <= 0:
            self.end_safe_phase(reason="timeout")
            return
        self.delay.add(name="goblin_safe_tick", ms=1000, callback=self.safe_tick)

    def end_safe_phase(self, reason="complete", **kwargs):
        if self.mode_finishing or not self.hold_active:
            return
        self.delay.remove("goblin_safe_tick")
        saucer = self.held_saucer
        self.held_saucer = None
        self.hold_active = False
        self.machine.game.player["goblin_hold_active"] = 0
        self.machine.events.post("goblin_hold_ended", saucer=saucer, reason=reason)
        self._queue_temp("MORE CHAOS!")
        if saucer is not None:
            self.delayed_eject(saucer=saucer)
        if self.safety_net_available and not self.safety_net_used:
            self.safety_net_used = True
            self.machine.events.post("start_case_file_ball_save")
        self.delay.add(name="goblin_resume_after_hold", ms=250, callback=self.start_unsafe_phase)

    # ------------------------------------------------------------------
    # Shots and scoring
    # ------------------------------------------------------------------

    def shot_hit(self, shot_name=None, **kwargs):
        if self.mode_finishing or not shot_name or shot_name not in self.active_shots:
            return
        if self.machine.game.player["villain_mode_in_summary"] is True:
            return
        if self.hold_active:
            self.collect_safe_shot(shot_name)
        else:
            self.collect_unsafe_shot(shot_name)

    def collect_unsafe_shot(self, shot_name):
        self._award_points(self.UNSAFE_SCORE)
        player = self.machine.game.player
        player["goblin_attacks_value"] += self.UNSAFE_SCORE
        player["goblin_chaos_bonus"] = max(
            self.CHAOS_MIN,
            int(player["goblin_chaos_bonus"]) - self.UNSAFE_LOSS,
        )
        self.machine.events.post("goblin_solid_shot_score", shot=shot_name)
        self._show_temp("CHAOS HIT - 20K", "CHAOS BONUS -150K")
        self._update_mode_status()

    def collect_safe_shot(self, shot_name, assisted=False):
        if shot_name not in self.active_shots:
            return
        immediate = self.MORE_JACKPOTS_SCORE if self.more_jackpots else self.SAFE_IMMEDIATE_SCORE
        values = self.BIGGER_SAFE_BONUS_VALUES if self.bigger_jackpots else self.SAFE_BONUS_VALUES
        add_value = values[min(self.safe_hit_count, len(values) - 1)]

        self._award_points(immediate)
        player = self.machine.game.player
        player["goblin_attacks_value"] += immediate
        player["goblin_chaos_bonus"] = min(
            self.CHAOS_MAX,
            int(player["goblin_chaos_bonus"]) + add_value,
        )
        self.safe_hit_count += 1
        self.deactivate_safe_shot(shot_name)
        self.machine.events.post("goblin_flashing_shot_score", shot=shot_name, assisted=assisted)
        self._queue_safe_messages(immediate, player["goblin_chaos_bonus"])

        trigger_assist = (
            not assisted
            and self.shot_assist_available
            and not self.shot_assist_used
        )
        if trigger_assist:
            self.shot_assist_used = True
            candidates = list(self.active_shots)
            if candidates:
                self.collect_safe_shot(random.choice(candidates), assisted=True)

        self._update_mode_status()
        if not self.active_shots:
            self.end_safe_phase(reason="all_six")

    def deactivate_safe_shot(self, shot_name):
        self.active_shots.discard(shot_name)
        self.current_flashing.discard(shot_name)
        self.machine.events.post(f"goblin_stop_{shot_name}")

    # ------------------------------------------------------------------
    # Saucers
    # ------------------------------------------------------------------

    def saucer_hit(self, saucer=None, **kwargs):
        if self.mode_finishing or saucer is None:
            return
        if self.hold_active:
            self._award_points(self.EXTRA_SAUCER_SCORE)
            self._show_temp("NO NO NO")
            self.delay.add(
                name=f"goblin_extra_saucer_eject_{saucer}",
                ms=250,
                callback=self.delayed_eject,
                saucer=saucer,
            )
            return

        player = self.machine.game.player
        bank_value = int(player["goblin_chaos_bonus"])
        player["goblin_bonus_banked"] += bank_value
        player["goblin_chaos_lock"] = player["goblin_bonus_banked"]
        self.machine.events.post("goblin_bonus_bank_added", value=bank_value)
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="CHAOS BONUS BANKED",
            message_mode_subtitle="GOBLIN BONUS",
            message_mode_value=bank_value,
        )
        self.start_safe_phase(saucer)
        self._schedule_temp_after(2000, "SAFE JACKPOTS", "HIT ALL 6")

    def delayed_eject(self, saucer=None, **kwargs):
        if saucer is not None:
            self.machine.events.post(f"delayed_kickout_saucer_{saucer}")

    def eject_held_saucer(self, reason=None):
        saucer = self.held_saucer
        if saucer is None:
            return
        self.delay.remove("goblin_safe_tick")
        self.held_saucer = None
        self.hold_active = False
        self.machine.game.player["goblin_hold_active"] = 0
        self.machine.events.post("goblin_hold_ended", saucer=saucer, reason=reason)
        self.delayed_eject(saucer=saucer)

    # ------------------------------------------------------------------
    # Messages / status
    # ------------------------------------------------------------------

    def _show_temp(self, title, subtitle="", value=""):
        self.machine.events.post(
            "goblin_show_temp_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
        )

    def _schedule_temp_after(self, delay_ms, title, subtitle="", value=""):
        self.message_sequence += 1
        name = f"goblin_temp_message_{self.message_sequence}"
        self.message_delay_names.add(name)
        self.delay.add(
            name=name,
            ms=max(0, int(delay_ms)),
            callback=self._show_temp,
            title=title,
            subtitle=subtitle,
            value=value,
        )

    def _queue_temp(self, title, subtitle="", value=""):
        now = time.monotonic()
        start_time = max(now, self.message_queue_next_time)
        delay_ms = int((start_time - now) * 1000)
        self._schedule_temp_after(delay_ms, title, subtitle, value)
        self.message_queue_next_time = start_time + 1.0

    def _queue_safe_messages(self, immediate, chaos_bonus):
        self._queue_temp(f"SAFE JACKPOT - {immediate // 1000}K")
        self._queue_temp("CHAOS BONUS NOW", value=chaos_bonus)

    def _update_mode_status(self):
        if self.hold_active:
            title = "SAFE JACKPOTS"
            value = f"TIME: {self.safe_seconds_remaining}"
        else:
            title = "CHAOS BONUS"
            value = f"{int(self.machine.game.player['goblin_chaos_bonus']):,}"
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    # ------------------------------------------------------------------
    # Multiball / ending
    # ------------------------------------------------------------------

    def multiball_started(self, **kwargs):
        self.machine.game.player["multiball_autoplunge_active"] = 1

    def multiball_ended(self, **kwargs):
        self.machine.game.player["multiball_autoplunge_active"] = 0
        if self.held_saucer is not None:
            self.eject_held_saucer(reason="multiball_ended")
        if not self.mode_finishing:
            self.finish_mode(completed=False)

    def collect_banked_bonus(self, **kwargs):
        if self.bonus_paid:
            return
        banked = int(self.machine.game.player["goblin_bonus_banked"])
        if banked <= 0:
            return
        player = self.machine.game.player
        player["goblin_bonus"] += banked
        self.bonus_paid = True
        self.machine.events.post("goblin_bonus_collected", value=banked)

    def finish_mode(self, completed=False):
        if self.mode_finishing:
            return
        self.mode_finishing = True
        if self.held_saucer is not None:
            self.eject_held_saucer(reason="mode_finish")
        self.clear_all_delays()
        self.clear_shot_shows()
        self.machine.events.post("goblin_gi_stop")
        self.machine.events.post("goblin_mode_ended")
        self.machine.game.player["goblin_state"] = 2
        self.collect_banked_bonus()
        self.machine.events.post("goblin_mode_complete")

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        self.clear_all_delays()
        self.clear_shot_shows()
        self.machine.events.post("goblin_gi_stop")
        self.machine.events.post("goblin_mode_ended")
        self.machine.game.player["multiball_autoplunge_active"] = 0
        super().mode_stop(**kwargs)

    def clear_all_delays(self):
        for name in (
            "goblin_safe_tick",
            "goblin_resume_after_hold",
            "goblin_extra_saucer_eject_1",
            "goblin_extra_saucer_eject_2",
            "goblin_extra_saucer_eject_3",
        ):
            self.delay.remove(name)
        for name in list(self.message_delay_names):
            self.delay.remove(name)
        self.message_delay_names.clear()

    def clear_shot_shows(self):
        for shot_name in set(self.current_flashing) | set(self.current_solid):
            self.machine.events.post(f"goblin_stop_{shot_name}")
        self.current_flashing.clear()
        self.current_solid.clear()

    def _award_points(self, points):
        self.machine.game.player["score"] += points
        self.machine.game.player["active_mode_points"] += points
