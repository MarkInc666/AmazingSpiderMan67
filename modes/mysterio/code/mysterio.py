from mpf.core.mode import Mode
from mpf.core.delays import DelayManager
from modes.common.case_file_mixin import CaseFileMixin
from modes.common.shot_registry import Shot
import random


class Mysterio(CaseFileMixin, Mode):
    STARTING_SUPER = 1_000_000
    BIGGER_STARTING_SUPER = 1_500_000
    SUPER_FLOOR = 100_000
    WRONG_SCORE = 50_000
    WRONG_DEDUCT = 100_000
    MORE_TIME_DEDUCT = 50_000
    COMPLETION_HOLD_MS = 2_000
    COMPLETION_DELAY_NAME = "mysterio_completion_hold"

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.super_value = (
            self.BIGGER_STARTING_SUPER
            if self.has_case_file("bigger_jackpots")
            else self.STARTING_SUPER
        )
        self.wrong_deduct = (
            self.MORE_TIME_DEDUCT
            if self.has_case_file("more_time")
            else self.WRONG_DEDUCT
        )
        self.extra_chance_available = self.has_case_file("more_jackpots")
        self.reveal_false_shot = self.has_case_file("shot_assist")
        self.mysterio_illusions_cleared = 0
        self.mysterio_jackpot_value = 0
        self.clues_used = 0
        self.active_mode_points = 0
        self.mode_done = False
        self.mode_finishing = False

        self.publish_case_file_bonus_events("mysterio")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "FIRST WRONG SHOT PROTECTED"),
            ("bigger_jackpots", "1.5M SUPER JACKPOT"),
            ("more_time", "SUPER PENALTY REDUCED"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "ONE FALSE SHOT REMOVED"),
        ])

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        # Nine distinct shot groups: five clues, three false shots, one hidden Super.
        self.shots = [
            Shot("left_web", 10, 70, "mysterio_left_web_hit", group="left"),
            Shot("left_pop", 25, 45, "mysterio_left_pop_hit", group="left"),
            Shot("left_drops", 40, 60, "mysterio_left_drops_hit", group="left"),
            Shot("saucers", 50, 30, "mysterio_saucers_hit", group="left"),
            Shot("center_web", 60, 30, "mysterio_center_web_hit", group="center"),
            Shot("right_pop", 75, 45, "mysterio_right_pop_hit", group="right"),
            Shot("upper_spinner", 90, 30, "mysterio_upper_spinner_hit", group="upper"),
            Shot("upper_targets", 95, 20, "mysterio_upper_targets_hit", group="upper"),
            Shot("right_drops", 100, 80, "mysterio_right_drops_hit", group="right"),
        ]
        self.shots_by_name = {shot.name: shot for shot in self.shots}

        for shot in self.shots:
            self.add_mode_event_handler(shot.event, self.shot_hit, shot_name=shot.name)

        self.start_trial()

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        if hasattr(self, "delay"):
            self.delay.remove(self.COMPLETION_DELAY_NAME)
        self.machine.events.post("rooftop_diverter_close")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _rules_active(self):
        return (
            not self.mode_done
            and not self.mode_finishing
            and not self.machine.game.player["villain_mode_in_summary"]
        )

    def _award_points(self, value):
        value = int(value)
        self.active_mode_points += value
        player = self.machine.game.player
        player["active_mode_points"] = self.active_mode_points
        player["score"] += value

    def _update_mode_status(self):
        if self.mode_finishing:
            return
        active_count = sum(1 for shot in self.shots if not shot.disabled)
        self.machine.events.post(
            "update_mode_status",
            mode_status_title="SHOTS LEFT / SUPER",
            mode_status_value=f"{active_count} / {self.super_value:,}",
        )

    def start_trial(self):
        for shot in self.shots:
            shot.is_lit = True
            shot.is_clue = False
            shot.is_jackpot = False
            shot.disabled = False
            shot.hint = None

        jackpot = random.choice(self.shots)
        jackpot.is_jackpot = True

        clue_shots = random.sample([shot for shot in self.shots if not shot.is_jackpot], 5)
        for clue in clue_shots:
            clue.is_clue = True
            clue.hint = self.build_hint(jackpot)

        if self.reveal_false_shot:
            false_shots = [
                shot for shot in self.shots
                if not shot.is_jackpot and not shot.is_clue
            ]
            if false_shots:
                revealed = random.choice(false_shots)
                self._disable_shot(revealed)
                self.machine.events.post(
                    "mysterio_case_file_false_shot_revealed", shot=revealed.name
                )
                self.machine.events.post(
                    "show_mode_message",
                    message_mode_title="FALSE SHOT REMOVED",
                    message_mode_subtitle=revealed.name.replace("_", " ").upper(),
                )

        player = self.machine.game.player
        player["mysterio_super_value"] = self.super_value
        player["mysterio_illusions_cleared"] = 0
        player["active_mode_stat_2"] = 0
        player["active_mode_points"] = 0

        self._update_mode_status()
        self.machine.events.post("mysterio_startup_complete")
        self.machine.events.post("mysterio_all_shots_lit")
        self.check_gate_status()
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="MYSTERIO",
            message_mode_subtitle="FIND THE REAL MYSTERY SHOT",
            message_mode_value=self.super_value,
        )

    @staticmethod
    def build_hint(jackpot_shot):
        if jackpot_shot.group == "upper":
            return "upper"
        if jackpot_shot.group == "center":
            return "center"
        if jackpot_shot.x < 60:
            return "left"
        return "right"

    def shot_hit(self, shot_name=None, **kwargs):
        if not self._rules_active() or not shot_name:
            return

        shot = self.shots_by_name.get(shot_name)
        if not shot or shot.disabled:
            return

        self.mysterio_illusions_cleared += 1
        self.machine.game.player["mysterio_illusions_cleared"] = self.mysterio_illusions_cleared

        if shot.is_jackpot:
            self.collect_super(shot)
            return

        protected = self.extra_chance_available
        if protected:
            self.extra_chance_available = False
            self.machine.events.post("mysterio_case_file_extra_chance_used", shot=shot.name)

        if shot.is_clue:
            self.handle_clue_shot(shot, protected=protected)
        else:
            self.handle_wrong_shot(shot, protected=protected)

        self.check_gate_status()

    def check_gate_status(self):
        upper_active = any(
            not shot.disabled and shot.group == "upper"
            for shot in self.shots
        )
        self.machine.events.post(
            "rooftop_diverter_open" if upper_active else "rooftop_diverter_close"
        )

    def handle_wrong_shot(self, shot, protected=False):
        self.machine.events.post("mysterio_non_clue_shot")
        self.machine.events.post("mysterio_wrong_shot")
        self.machine.events.post("mysterio_score_wrong_shot")
        self._award_points(self.WRONG_SCORE)

        if protected:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="MYSTERIO FOOLED!",
                message_mode_subtitle="SUPER VALUE PROTECTED",
            )
        else:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="HE MUST BE HERE SOMEWHERE",
                message_mode_value=self.WRONG_SCORE,
            )
            self.reduce_super(self.wrong_deduct)

        self._disable_shot(shot)
        self._update_mode_status()

    def handle_clue_shot(self, shot, protected=False):
        self.clues_used += 1
        self.machine.game.player["active_mode_stat_1"] = self.clues_used
        self.machine.events.post("mysterio_clue_shot")
        self.machine.events.post("mysterio_score_wrong_shot")
        self._award_points(self.WRONG_SCORE)

        self.machine.events.post(
            "show_mode_message",
            message_mode_title="CLUE FOUND",
            message_mode_subtitle=f"SPIDEY SENSE: {shot.hint.upper()}",
            message_mode_value=self.WRONG_SCORE,
        )
        self._post_hint_audio(shot.hint)

        if protected:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="MYSTERIO FOOLED!",
                message_mode_subtitle="SUPER VALUE PROTECTED",
            )
        else:
            self.reduce_super(self.wrong_deduct)

        self._disable_shot(shot)
        self._update_mode_status()

    def _post_hint_audio(self, hint):
        if hint == "left":
            self.machine.events.post("mysterio_spidey_sense_left")
        elif hint == "right":
            self.machine.events.post("mysterio_spidey_sense_right")
        elif hint == "upper":
            self.machine.events.post("mysterio_spidey_sense_upper")
        else:
            self.machine.events.post("mysterio_spidey_sense_center")

    def _disable_shot(self, shot):
        shot.disabled = True
        shot.is_lit = False
        self.machine.events.post(f"mysterio_stop_{shot.name}")

    def reduce_super(self, amount):
        self.super_value = max(self.SUPER_FLOOR, self.super_value - int(amount))
        self.machine.game.player["mysterio_super_value"] = self.super_value
        self.machine.events.post("mysterio_super_changed")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="SUPER NOW",
            message_mode_value=self.super_value,
        )

    def collect_super(self, shot):
        if self.mode_done or self.mode_finishing:
            return

        collected_value = self.super_value
        self.mode_done = True
        self.mode_finishing = True
        self._disable_shot(shot)
        self.mysterio_jackpot_value = collected_value
        self.machine.game.player["active_mode_stat_2"] = collected_value
        self._award_points(collected_value)

        self.machine.events.post("hide_mode_status")
        self.machine.events.post("mysterio_super_collected")
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="MYSTERIO SUPER JACKPOT",
            message_mode_value=collected_value,
        )
        self.delay.add(
            name=self.COMPLETION_DELAY_NAME,
            ms=self.COMPLETION_HOLD_MS,
            callback=self._complete_mode,
        )

    def _complete_mode(self, **kwargs):
        if not self.mode_finishing:
            return
        self.machine.events.post("mysterio_mode_complete")
