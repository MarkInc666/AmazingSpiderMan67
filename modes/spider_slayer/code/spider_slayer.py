import random
import time

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class SpiderSlayer(CaseFileMixin, Mode):
    MODE_KEY = "spider_slayer"
    DISPLAY_NAME = "Spider-Slayer"

    REQUIRED_HITS = 15
    NORMAL_SHOT_VALUES = (50_000, 25_000, 10_000, 5_000)
    MORE_JACKPOTS_SHOT_VALUES = (50_000, 50_000, 10_000, 5_000)
    BIGGER_SHOT_VALUES = (75_000, 50_000, 25_000, 10_000)
    BIGGER_MORE_JACKPOTS_SHOT_VALUES = (75_000, 75_000, 25_000, 10_000)
    BASE_JACKPOT = 2_000_000
    BIGGER_JACKPOT = 2_500_000
    JACKPOT_DECAY = 100_000
    MIN_JACKPOT = 100_000
    JACKPOT_SECONDS = 20
    MORE_TIME_JACKPOT_SECONDS = 25
    VUK_EJECT_DELAY_MS = 1_500

    SHOTS = (
        "left_web", "center_web", "left_sling", "right_sling",
        "left_pop", "right_pop", "left_bank", "right_bank",
        "star", "saucer",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=2)
        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "hunt"
        self.active_shots = set()
        self.shot_hits = {shot: 0 for shot in self.SHOTS}
        self.hits = 0
        self.mode_points = 0
        self.hunt_started_at = None
        self.hunt_completed = False
        self.hunt_time_tenths = 0
        self.slayers_jackpot = self.BIGGER_JACKPOT if self.has_case_file("bigger_jackpots") else self.BASE_JACKPOT
        self.collected_jackpot = 0
        bigger = self.has_case_file("bigger_jackpots")
        more_jackpots = self.has_case_file("more_jackpots")
        if bigger and more_jackpots:
            self.shot_values = self.BIGGER_MORE_JACKPOTS_SHOT_VALUES
        elif bigger:
            self.shot_values = self.BIGGER_SHOT_VALUES
        elif more_jackpots:
            self.shot_values = self.MORE_JACKPOTS_SHOT_VALUES
        else:
            self.shot_values = self.NORMAL_SHOT_VALUES
        self.jackpot_seconds = self.MORE_TIME_JACKPOT_SECONDS if self.has_case_file("more_time") else self.JACKPOT_SECONDS
        self.jackpot_seconds_left = 0
        self.shot_assist_used = False

        player = self.machine.game.player
        player["spider_slayer_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SECOND SHOT STAYS AT FULL VALUE"),
            ("bigger_jackpots", "BIGGER SHOTS / 2.5M JACKPOT"),
            ("more_time", "25 SECOND SLAYER JACKPOT"),
            ("safety_net", "10 SECOND SAVE AT DAILY BUGLE"),
            ("shot_assist", "FIRST SHOT SCORES AND COUNTS TWICE"),
        ])

        for shot in self.SHOTS:
            self.add_mode_event_handler(f"spider_slayer_shot_{shot}", self._shot_hit, shot=shot)
        self.add_mode_event_handler("spider_slayer_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("ball_ending", self._ball_ending)

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("spider_slayer_hunt_started")
        self._add_random_shots(1)
        self._show_message("SPIDER-SLAYER HUNT", "HIT THE LIT SHOT")
        self._update_status()

    def _shot_hit(self, shot=None, **kwargs):
        if self.mode_done or self.phase not in ("hunt", "jackpot", "expired") or shot not in self.active_shots:
            return

        if self.hits == 0:
            self.hunt_started_at = time.monotonic()

        hit_count = 1
        if self.phase == "hunt" and self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            hit_count = 2
            self.machine.events.post("spider_slayer_case_file_shot_assist_used")

        total_value = 0
        for _ in range(hit_count):
            repeat_index = min(self.shot_hits[shot], len(self.shot_values) - 1)
            total_value += self.shot_values[repeat_index]
            self.shot_hits[shot] += 1
        self._score(total_value)

        if self.phase != "hunt":
            self.machine.events.post("spider_slayer_successful_hit", shot=shot, hits=self.hits, value=total_value)
            self._sync_vars()
            self._update_status()
            return

        self.hits = min(self.REQUIRED_HITS, self.hits + hit_count)
        self.machine.events.post("spider_slayer_successful_hit", shot=shot, hits=self.hits, value=total_value)

        if self.hits >= self.REQUIRED_HITS:
            self._finish_hunt()
            return

        self._add_random_shots(hit_count)
        self._sync_vars()
        self._update_status()

    def _add_random_shots(self, count):
        choices = [shot for shot in self.SHOTS if shot not in self.active_shots]
        for shot in random.sample(choices, min(count, len(choices))):
            self.active_shots.add(shot)
            self.machine.events.post(f"spider_slayer_light_{shot}")

    def _finish_hunt(self):
        if self.hunt_started_at is not None:
            elapsed = max(0.0, time.monotonic() - self.hunt_started_at)
            self.hunt_time_tenths = int(round(elapsed * 10.0))

        self.phase = "jackpot"
        self.hunt_completed = True
        self.machine.events.post("spider_slayer_hunt_complete")
        self.machine.events.post("final_vuk_chase_start")
        self.machine.events.post("rooftop_diverter_open")
        if self.has_case_file("safety_net"):
            self.machine.events.post("spider_slayer_enable_safety_net")

        self._show_message("SLAYER EXPOSED", "SHOOT THE DAILY BUGLE", self.slayers_jackpot)
        self.jackpot_seconds_left = self.jackpot_seconds
        self._sync_vars()
        self._update_status()
        self.delay.add(name="spider_slayer_decay", ms=1000, callback=self._decay_tick)

    def _decay_tick(self):
        if self.mode_done or self.phase != "jackpot":
            return
        self.jackpot_seconds_left = max(0, self.jackpot_seconds_left - 1)
        self.slayers_jackpot = max(self.MIN_JACKPOT, self.slayers_jackpot - self.JACKPOT_DECAY)
        self.machine.events.post("spider_slayer_jackpot_changed", value=self.slayers_jackpot)
        self._sync_vars()
        self._update_status()
        if self.jackpot_seconds_left <= 0:
            self._expire_jackpot()
        else:
            self.delay.add(name="spider_slayer_decay", ms=1000, callback=self._decay_tick)

    def _expire_jackpot(self):
        self.phase = "expired"
        self.slayers_jackpot = 0
        self.collected_jackpot = 0
        self.machine.events.post("final_vuk_chase_stop")
        self.machine.events.post("spider_slayer_jackpot_expired")
        self.machine.events.post("spider_slayer_disable_safety_net")
        self.machine.events.post("rooftop_diverter_close")
        self._show_message("SLAYER ESCAPED", "JACKPOT EXPIRED")
        self._sync_vars()
        self._update_status()

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            # The winning VUK ball is owned by the villain-summary hold. Ignore
            # switch chatter until VillainBookends releases it after summary.
            return
        if self.phase != "jackpot":
            self.machine.events.post(
                "request_vuk_eject",
                delay_ms=self.VUK_EJECT_DELAY_MS,
            )
            return

        self.delay.remove("spider_slayer_decay")
        self.machine.events.post("final_vuk_chase_stop")
        self.collected_jackpot = self.slayers_jackpot
        self._score(self.collected_jackpot)
        self.mode_done = True
        self.machine.game.player["spider_slayer_state"] = 2
        self._sync_vars()
        self.machine.events.post("spider_slayer_disable_safety_net")
        self.machine.events.post("show_mode_jackpot", message_mode_title="SPIDER-SLAYER DESTROYED", message_mode_subtitle="SLAYER JACKPOT", message_mode_value=self.collected_jackpot)
        self.machine.events.post("villain_summary_hold_vuk_until_done")
        self.delay.add(name="spider_slayer_finish", ms=2000, callback=self.machine.events.post, event="spider_slayer_mode_complete")

    def _ball_ending(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._sync_vars()
        self.machine.events.post("show_mode_message", message_mode_title="SLAYER ESCAPED", message_mode_subtitle="THE HUNT IS OVER")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["spider_slayer_hits"] = self.hits
        player["active_mode_stat_count"] = 3 if self.hunt_completed else 2
        player["active_mode_stat_1"] = self.collected_jackpot
        player["spider_slayer_hunt_time_tenths"] = self.hunt_time_tenths
        player["active_mode_stat_2"] = self.hunt_time_tenths

    def _update_status(self):
        if self.phase == "hunt":
            title = f"HUNT {self.hits}/{self.REQUIRED_HITS}"
            value = "HIT THE LIT SHOT"
        elif self.phase == "jackpot":
            title = f"DAILY BUGLE {self.jackpot_seconds_left}S"
            value = f"SLAYER JP {self.slayers_jackpot:,}"
        else:
            title = "SLAYER JACKPOT EXPIRED"
            value = "LIT SHOTS STILL SCORE"
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)

    def _show_message(self, title, subtitle="", value=""):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
        )

    def mode_stop(self, **kwargs):
        self.delay.remove("spider_slayer_decay")
        self.delay.remove("spider_slayer_finish")
        self.machine.events.post("spider_slayer_clear_all")
        self.machine.events.post("final_vuk_chase_stop")
        self.machine.events.post("spider_slayer_disable_safety_net")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        # Catch-all: no delayed villain/wizard callback may survive into bonus.
        self.delay.clear()
        super().mode_stop(**kwargs)
