import random

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class CharlesCameo(CaseFileMixin, Mode):
    """Charles Cameo — Double Identity mirrored-shot mode."""

    MODE_KEY = "charles_cameo"
    DISPLAY_NAME = "Charles Cameo"

    SOURCE_SCORE = 50_000
    BIGGER_SOURCE_SCORE = 75_000
    JACKPOT_SCORE = 250_000
    BIGGER_JACKPOT_SCORE = 300_000
    SUPER_JACKPOT_SCORE = 1_000_000

    MIRROR_SECONDS = 10
    MORE_TIME_SECONDS = 15
    VUK_EJECT_MS = 1_000
    TRANSITION_MS = 1_000

    NORMAL_STAGES = ("pops", "drops", "ab", "webs")
    MORE_JACKPOTS_STAGES = ("upper", "pops", "drops", "ab", "webs")

    STAGE_SIDES = {
        "upper": ("left", "right"),
        "pops": ("left", "right"),
        "drops": ("left", "right"),
        "ab": ("a", "b"),
        "webs": ("left", "right"),
    }

    STAGE_LABELS = {
        "upper": "UPPER TARGETS",
        "pops": "POPS",
        "drops": "DROP BANKS",
        "ab": "A + B",
        "webs": "WEB SUPER",
    }

    SIDE_LABELS = {
        "left": "LEFT",
        "right": "RIGHT",
        "a": "A",
        "b": "B",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)

        self.case_files = self.get_case_file_bonuses()
        self.stages = self.MORE_JACKPOTS_STAGES if self.has_case_file("more_jackpots") else self.NORMAL_STAGES

        self.mode_done = False
        self.stage_index = 0
        self.stage = None
        self.phase = "source"
        self.source_side = None
        self.mirror_side = None
        self.seconds_left = 0
        self.source_hits = 0
        self.jackpots = 0
        self.biggest_jackpot = 0
        self.mode_points = 0
        self.shot_assist_used = False

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "UPPER-TARGET PAIR ADDED FIRST"),
            ("bigger_jackpots", "75K SOURCES / 300K JACKPOTS"),
            ("more_time", "15 SECOND MIRROR WINDOWS"),
            ("safety_net", "10 SECOND BALL SAVE"),
            ("shot_assist", "FIRST EXPIRED MIRROR AUTO-COLLECTS"),
        ])

        self.add_mode_event_handler("charles_cameo_upper_left_hit", self._pair_hit, stage="upper", side="left")
        self.add_mode_event_handler("charles_cameo_upper_right_hit", self._pair_hit, stage="upper", side="right")
        self.add_mode_event_handler("charles_cameo_pop_left_hit", self._pair_hit, stage="pops", side="left")
        self.add_mode_event_handler("charles_cameo_pop_right_hit", self._pair_hit, stage="pops", side="right")
        self.add_mode_event_handler("charles_cameo_drop_left_hit", self._pair_hit, stage="drops", side="left")
        self.add_mode_event_handler("charles_cameo_drop_right_hit", self._pair_hit, stage="drops", side="right")
        # YAML combines both physical A switches into the A event and both
        # physical B switches into the B event, so either matching insert can
        # complete the currently lit side of the A+B pair.
        self.add_mode_event_handler("charles_cameo_a_hit", self._pair_hit, stage="ab", side="a")
        self.add_mode_event_handler("charles_cameo_b_hit", self._pair_hit, stage="ab", side="b")
        self.add_mode_event_handler("charles_cameo_web_left_hit", self._pair_hit, stage="webs", side="left")
        self.add_mode_event_handler("charles_cameo_web_right_hit", self._pair_hit, stage="webs", side="right")
        self.add_mode_event_handler("s_vuk_switch_active", self._vuk_hit)
        self.add_mode_event_handler("ball_ending", self._ball_ending)

        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("charles_cameo_clear_all")
        self.machine.events.post("clear_saucers_delayed")

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self._start_stage(new_side=True)

    def mode_stop(self, **kwargs):
        self._stop_timer()
        self.delay.remove("charles_cameo_next_stage")
        self.delay.remove("charles_cameo_restart_pair")
        self.machine.events.post("charles_cameo_clear_all")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _start_stage(self, new_side):
        if self.mode_done:
            return

        self._stop_timer()
        self.stage = self.stages[self.stage_index]
        self.phase = "source"

        if new_side or self.source_side not in self.STAGE_SIDES[self.stage]:
            self.source_side = random.choice(self.STAGE_SIDES[self.stage])
        self.mirror_side = self._opposite_side(self.stage, self.source_side)

        self.machine.events.post("charles_cameo_clear_shots")
        if self.stage == "upper":
            self.machine.events.post("rooftop_diverter_open")
        else:
            self.machine.events.post("rooftop_diverter_close")

        self._light_current_shot()
        self._show_message(
            self.STAGE_LABELS[self.stage],
            f"HIT {self.SIDE_LABELS[self.source_side]}",
            reminder=True,
        )
        self._update_status()
        self._sync_vars()

    def _pair_hit(self, stage, side, **kwargs):
        if self.mode_done or stage != self.stage:
            return

        if self.phase == "source":
            if side == self.source_side:
                self._collect_source()
            return

        if self.phase == "mirror" and side == self.mirror_side:
            self._collect_mirror(assisted=False)

    def _collect_source(self):
        value = self._source_value()
        self._score(value)
        self.source_hits += 1
        self.phase = "mirror"
        self.seconds_left = self._mirror_seconds()

        self.machine.events.post("charles_cameo_clear_shots")
        self.machine.events.post(
            "charles_cameo_source_collected",
            stage=self.stage,
            side=self.source_side,
            value=value,
        )
        self._light_current_shot()
        self._show_message("CAMEO COPIED IT", f"HIT {self.SIDE_LABELS[self.mirror_side]}", value=value)
        self._update_status()
        self._sync_vars()
        self._schedule_tick()

    def _collect_mirror(self, assisted):
        self._stop_timer()
        is_super = self.stage == "webs"
        value = self.SUPER_JACKPOT_SCORE if is_super else self._jackpot_value()

        self._score(value)
        self.jackpots += 1
        self.biggest_jackpot = max(self.biggest_jackpot, value)
        self.machine.events.post("charles_cameo_clear_shots")

        event = "charles_cameo_super_jackpot_collected" if is_super else "charles_cameo_jackpot_collected"
        self.machine.events.post(
            event,
            stage=self.stage,
            source_side=self.source_side,
            mirror_side=self.mirror_side,
            value=value,
            assisted=assisted,
        )

        if assisted and is_super:
            title = "ASSIST SUPER JACKPOT"
        elif is_super:
            title = "SUPER JACKPOT"
        elif assisted:
            title = "ASSIST JACKPOT"
        else:
            title = "CAMEO JACKPOT"
        self._show_message(title, self._format_score(value), value=value, event="show_mode_jackpot")
        self._sync_vars()

        if is_super:
            self._complete_mode()
            return

        if self.stage == "upper":
            self.machine.events.post("rooftop_diverter_close")

        self.stage_index += 1
        self.phase = "transition"
        self.delay.reset(
            name="charles_cameo_next_stage",
            ms=self.TRANSITION_MS,
            callback=lambda: self._start_stage(new_side=True),
        )

    def _schedule_tick(self):
        self.delay.remove("charles_cameo_mirror_tick")
        self.delay.add(name="charles_cameo_mirror_tick", ms=1_000, callback=self._timer_tick)

    def _timer_tick(self):
        if self.mode_done or self.phase != "mirror":
            return

        self.seconds_left = max(0, self.seconds_left - 1)
        self._sync_vars()

        if self.seconds_left <= 0:
            self._mirror_timeout()
            return

        self._update_status()
        self._schedule_tick()

    def _mirror_timeout(self):
        self._stop_timer()

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            self.machine.events.post(
                "charles_cameo_case_file_shot_assist_used",
                stage=self.stage,
                mirror_side=self.mirror_side,
            )
            self._collect_mirror(assisted=True)
            return

        self.machine.events.post("charles_cameo_mirror_expired", stage=self.stage)
        self._show_message("CAMEO ESCAPED", "RESTARTING THIS PAIR")
        self.phase = "transition"
        self.machine.events.post("charles_cameo_clear_shots")
        self.delay.reset(
            name="charles_cameo_restart_pair",
            ms=self.TRANSITION_MS,
            callback=lambda: self._start_stage(new_side=False),
        )

    def _light_current_shot(self):
        side = self.source_side if self.phase == "source" else self.mirror_side
        self.machine.events.post(f"charles_cameo_{self.stage}_{side}_{self.phase}")

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            return
        self.machine.events.post("request_vuk_eject", delay_ms=self.VUK_EJECT_MS)

    def _complete_mode(self):
        if self.mode_done:
            return
        self.mode_done = True
        self._stop_timer()
        self.machine.game.player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars()
        self.machine.events.post("charles_cameo_mode_complete")

    def _ball_ending(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self._stop_timer()
        self._sync_vars()
        self._show_message("CHARLES CAMEO ESCAPED", "DOUBLE IDENTITY UNSOLVED")

    def _stop_timer(self):
        self.delay.remove("charles_cameo_mirror_tick")
        self.seconds_left = 0

    def _source_value(self):
        return self.BIGGER_SOURCE_SCORE if self.has_case_file("bigger_jackpots") else self.SOURCE_SCORE

    def _jackpot_value(self):
        return self.BIGGER_JACKPOT_SCORE if self.has_case_file("bigger_jackpots") else self.JACKPOT_SCORE

    def _mirror_seconds(self):
        return self.MORE_TIME_SECONDS if self.has_case_file("more_time") else self.MIRROR_SECONDS

    @staticmethod
    def _opposite_side(stage, side):
        if stage == "ab":
            return "b" if side == "a" else "a"
        return "right" if side == "left" else "left"

    def _score(self, value):
        value = int(value)
        player = self.machine.game.player
        player["score"] += value
        self.mode_points += value

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_stat_1"] = self.jackpots
        player["active_mode_stat_2"] = self.biggest_jackpot

    def _update_status(self):
        if self.mode_done or not self.stage:
            return

        if self.phase == "source":
            status = f"HIT {self.SIDE_LABELS[self.source_side]}"
        else:
            status = f"MIRROR {self.SIDE_LABELS[self.mirror_side]}  {self.seconds_left}s"

        self.machine.events.post(
            "update_mode_status",
            mode_status_title=self.STAGE_LABELS[self.stage],
            mode_status_value=status,
        )

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
