from mpf.core.mode import Mode
from modes.common.shot_registry import Shot
import random


class Electro(Mode):

    NORMAL_JACKPOT_VALUE = 100000
    SUPER_JACKPOT_VALUE = 1000000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.super_active = False
        self.current_shot = None

        self.shots = [
            Shot("left_web", 10, 70, "electro_left_web_hit", group="left"),
            Shot("spinner", 20, 50, "electro_spinner_hit", group="center"),
            Shot("left_drops", 40, 60, "electro_left_drops_hit", group="left"),
            Shot("saucers", 50, 30, "electro_saucers_hit", group="left"),
            Shot("right_web", 80, 30, "electro_right_web_hit", group="right"),
            Shot("upper_spinner", 90, 30, "electro_upper_spinner_hit", group="upper"),
            Shot("upper_targets", 95, 20, "electro_upper_target_hit", group="upper"),
            Shot("right_drops", 100, 80, "electro_right_drops_hit", group="right"),
        ]

        self.shots_by_name = {shot.name: shot for shot in self.shots}

        for shot in self.shots:
            self.add_mode_event_handler(shot.event, self.shot_hit, shot_name=shot.name)

        self.add_mode_event_handler("electro_lit_shot_timeout", self.lit_shot_timeout)
        self.add_mode_event_handler("electro_super_timeout", self.super_timeout)

        self.begin_power_surge()

    def begin_power_surge(self):
        self.super_active = False
        self.current_shot = None

        for shot in self.shots:
            shot.is_lit = False
            shot.disabled = False
            shot.is_jackpot = False

        self.machine.events.post("electro_mode_started")
        self.pick_next_lit_shot()

    def active_shots(self):
        return [shot for shot in self.shots if not shot.disabled]

    def pick_next_lit_shot(self):
        self.stop_current_lit_shot()

        active = self.active_shots()

        if len(active) <= 0:
            self.machine.events.post("electro_mode_failed")
            return

        if len(active) == 1:
            self.start_super_jackpot(active[0])
            return

        previous_location = selc.current_shot.group
        
        self.current_shot = random.choice(active)
        self.current_shot.is_lit = True

        self.machine.events.post("electro_lit_shot_changed")
        self.machine.events.post(f"electro_lite_{self.current_shot.name}")
        self.machine.events.post("electro_shot_timer_start")
        if previous_location == "upper" and self.current_shot.group != "upper":
            self.machine.events.post("rooftop_diverter_close")
        if previous_location != "upper" and self.current_shot.group == "upper":
            self.machine.events.post("rooftop_diverter_open")

    def stop_current_lit_shot(self):
        if self.current_shot:
            self.current_shot.is_lit = False
            self.machine.events.post(f"electro_stop_{self.current_shot.name}")

        self.machine.events.post("electro_shot_timer_stop")

    def lit_shot_timeout(self, **kwargs):
        if self.super_active:
            return

        # Timeout means the shot remains active, but the spark moves elsewhere.
        self.pick_next_lit_shot()

    def shot_hit(self, shot_name=None, **kwargs):
        if not shot_name:
            return

        shot = self.shots_by_name.get(shot_name)

        if not shot or shot.disabled:
            return

        if self.super_active:
            if shot == self.current_shot:
                self.collect_super()
            return

        if shot != self.current_shot:
            return

        self.collect_normal_jackpot(shot)

    def collect_normal_jackpot(self, shot):
        self.machine.game.player["electro_jackpot_value"] = self.NORMAL_JACKPOT_VALUE

        self.machine.events.post("electro_jackpot_collected")
        self.machine.events.post(f"electro_{shot.name}_collected")

        shot.disabled = True
        shot.is_lit = False

        self.machine.events.post(f"electro_stop_{shot.name}")
        self.machine.events.post(f"electro_deactivate_{shot.name}")

        self.machine.events.post("electro_shot_timer_stop")
        self.pick_next_lit_shot()

    def start_super_jackpot(self, shot):
        self.stop_current_lit_shot()

        self.super_active = True
        self.current_shot = shot
        self.current_shot.is_lit = True
        self.current_shot.is_jackpot = True

        self.machine.game.player["electro_super_jackpot_value"] = self.SUPER_JACKPOT_VALUE

        self.machine.events.post("electro_super_lit")
        self.machine.events.post(f"electro_super_lite_{shot.name}")
        self.machine.events.post("electro_super_timer_start")

    def collect_super(self):
        self.machine.events.post("electro_super_collected")
        self.machine.events.post(f"electro_{self.current_shot.name}_super_collected")
        self.machine.events.post("electro_super_timer_stop")
        self.machine.events.post("electro_mode_complete")

    def super_timeout(self, **kwargs):
        self.machine.events.post("electro_super_missed")
        self.machine.events.post("electro_mode_failed")