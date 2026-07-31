import random
import time

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class SpiderSlayer(CaseFileMixin, Mode):
    MODE_KEY = "spider_slayer"
    DISPLAY_NAME = "Spider-Slayer"

    REQUIRED_HITS = 15
    SHOT_SCORE = 50_000
    BIGGER_SHOT_SCORE = 75_000
    BASE_JACKPOT = 2_000_000
    BIGGER_JACKPOT = 2_500_000
    NORMAL_DECAY = 100_000
    MORE_TIME_DECAY = 50_000
    MIN_JACKPOT = 100_000
    MORE_JACKPOTS_FREEZE_SECONDS = 10

    SHOTS = (
        "left_web", "center_web", "left_sling", "right_sling",
        "left_pop", "right_pop", "left_bank", "right_bank",
        "star", "saucer",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "hunt"
        self.active_shots = set()
        self.hits = 0
        self.mode_points = 0
        self.hunt_started_at = None
        self.hunt_time_tenths = 0
        self.slayers_jackpot = self.BIGGER_JACKPOT if self.has_case_file("bigger_jackpots") else self.BASE_JACKPOT
        self.collected_jackpot = 0
        self.shot_value = self.BIGGER_SHOT_SCORE if self.has_case_file("bigger_jackpots") else self.SHOT_SCORE
        self.decay_value = self.MORE_TIME_DECAY if self.has_case_file("more_time") else self.NORMAL_DECAY
        self.shot_assist_used = False

        player = self.machine.game.player
        player["spider_slayer_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "FULL JACKPOT FROZEN 10 SECONDS"),
            ("bigger_jackpots", "75K SHOTS / 2.5M JACKPOT"),
            ("more_time", "JACKPOT DECAYS 50K PER SECOND"),
            ("safety_net", "10 SECOND SAVE AT DAILY BUGLE"),
            ("shot_assist", "FIRST HIT ADDS TWO SHOTS"),
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
        if self.mode_done or self.phase != "hunt" or shot not in self.active_shots:
            return

        if self.hits == 0:
            self.hunt_started_at = time.monotonic()

        self.hits += 1
        self._score(self.shot_value)
        self.machine.events.post("spider_slayer_successful_hit", shot=shot, hits=self.hits, value=self.shot_value)

        if self.hits >= self.REQUIRED_HITS:
            self._finish_hunt()
            return

        add_count = 1
        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            add_count = 2
            self.machine.events.post("spider_slayer_case_file_shot_assist_used")
        self._add_random_shots(add_count)
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
        self.machine.events.post("spider_slayer_clear_hunt_shots")
        self.machine.events.post("spider_slayer_hunt_complete")
        self.machine.events.post("rooftop_diverter_open")
        if self.has_case_file("safety_net"):
            self.machine.events.post("spider_slayer_enable_safety_net")

        self._show_message("SLAYER EXPOSED", "SHOOT THE DAILY BUGLE", self.slayers_jackpot)
        self._sync_vars()
        self._update_status()

        freeze_ms = self.MORE_JACKPOTS_FREEZE_SECONDS * 1000 if self.has_case_file("more_jackpots") else 0
        self.delay.add(name="spider_slayer_begin_decay", ms=freeze_ms, callback=self._schedule_decay)

    def _schedule_decay(self):
        if self.mode_done or self.phase != "jackpot" or self.slayers_jackpot <= self.MIN_JACKPOT:
            return
        self.delay.add(name="spider_slayer_decay", ms=1000, callback=self._decay_tick)

    def _decay_tick(self):
        if self.mode_done or self.phase != "jackpot":
            return
        self.slayers_jackpot = max(self.MIN_JACKPOT, self.slayers_jackpot - self.decay_value)
        self.machine.events.post("spider_slayer_jackpot_changed", value=self.slayers_jackpot)
        self._sync_vars()
        self._update_status()
        self._schedule_decay()

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            self.machine.events.post("up_kick")
            return
        if self.phase != "jackpot":
            self.machine.events.post("up_kick")
            return

        self.delay.remove("spider_slayer_begin_decay")
        self.delay.remove("spider_slayer_decay")
        self.collected_jackpot = self.slayers_jackpot
        self._score(self.collected_jackpot)
        self.mode_done = True
        self.machine.game.player["spider_slayer_state"] = 2
        self._sync_vars()
        self.machine.events.post("spider_slayer_disable_safety_net")
        self.machine.events.post("show_mode_jackpot", message_mode_title="SPIDER-SLAYER DESTROYED", message_mode_subtitle="SLAYER JACKPOT", message_mode_value=self.collected_jackpot)
        self.delay.add(name="spider_slayer_vuk_eject", ms=1200, callback=self.machine.events.post, event="up_kick")
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
        player["spider_slayer_jackpot"] = self.collected_jackpot or self.slayers_jackpot
        player["spider_slayer_hunt_time_tenths"] = self.hunt_time_tenths
        player["spider_slayer_hunt_time"] = f"{self.hunt_time_tenths / 10:.1f} SEC"

    def _update_status(self):
        if self.phase == "hunt":
            title = f"HUNT {self.hits}/{self.REQUIRED_HITS}"
            value = "HIT THE LIT SHOT"
        else:
            title = "SHOOT THE DAILY BUGLE"
            value = f"SLAYER JP {self.slayers_jackpot:,}"
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)

    def _show_message(self, title, subtitle="", value=""):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
        )

    def mode_stop(self, **kwargs):
        self.delay.remove("spider_slayer_begin_decay")
        self.delay.remove("spider_slayer_decay")
        self.delay.remove("spider_slayer_vuk_eject")
        self.delay.remove("spider_slayer_finish")
        self.machine.events.post("spider_slayer_clear_all")
        self.machine.events.post("spider_slayer_disable_safety_net")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)
