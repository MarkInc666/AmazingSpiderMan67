from mpf.core.mode import Mode
from modes.common.shot_registry import Shot
import random


class Goblin(Mode):

    FLASHING = "flashing"
    SOLID = "solid"

    BASE_HOLD_TIME = 10
    MIN_HOLD_TIME = 5

    BASE_FLASH_TIME = 5
    MIN_FLASH_TIME = 3

    SOLID_TIME = 3

    FLASHING_SCORE = 50000
    SOLID_SCORE = 2000

    CHAOS_BONUS_ADD = 50000
    CHAOS_BONUS_LOSS = 50000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.active_shots = []
        self.current_flashing = set()
        self.current_solid = set()

        self.hold_active = False

        self.flash_time = self.BASE_FLASH_TIME
        self.hold_time = self.BASE_HOLD_TIME

        self.shots = [
            Shot("left_web", 10, 70, "goblin_left_web_hit", group="left"),
            Shot("spinner", 20, 50, "goblin_spinner_hit", group="center"),
            Shot("left_drops", 40, 60, "goblin_left_drops_hit", group="left"),
            Shot("saucers", 50, 30, "goblin_saucers_hit", group="center"),
            Shot("right_web", 80, 30, "goblin_right_web_hit", group="right"),
            Shot("upper_spinner", 90, 30, "goblin_upper_spinner_hit", group="upper"),
            Shot("upper_target", 95, 20, "goblin_upper_target_hit", group="upper"),
            Shot("right_drops", 100, 80, "goblin_right_drops_hit", group="right"),
        ]

        self.shots_by_name = {
            shot.name: shot for shot in self.shots
        }

        for shot in self.shots:
            self.add_mode_event_handler(
                shot.event,
                self.shot_hit,
                shot_name=shot.name
            )

        self.add_mode_event_handler("goblin_flash_timer_complete",self.flash_timer_complete)
        self.add_mode_event_handler("goblin_solid_timer_complete",self.solid_timer_complete)
        self.add_mode_event_handler("goblin_saucer_hit",self.saucer_lock)

        self.add_mode_event_handler("goblin_hold_timer_complete",self.end_hold)

        self.begin_mode()

    def begin_mode(self):

        self.active_shots = [
            shot.name for shot in self.shots
        ]

        self.current_flashing.clear()
        self.current_solid.clear()

        self.pick_flashing_shots()

    def pick_flashing_shots(self):

        if self.hold_active:
            return

        self.clear_current_shows()

        available = [
            shot for shot in self.active_shots
            if shot not in self.current_solid
        ]

        if len(available) <= 3:
            self.start_final_phase()
            return

        random.shuffle(available)

        self.current_flashing = set(available[:3])

        for shot_name in self.current_flashing:
            self.machine.events.post(
                f"goblin_lite_{shot_name}"
            )

        self.start_flash_timer()

    def flash_timer_complete(self, **kwargs):

        if self.hold_active:
            return

        self.clear_flashing()

        self.current_solid = set(self.current_flashing)

        for shot_name in self.current_solid:
            self.machine.events.post(
                f"goblin_solid_{shot_name}"
            )

        self.start_solid_timer()

    def solid_timer_complete(self, **kwargs):

        if self.hold_active:
            return

        for shot_name in self.current_solid:
            self.machine.events.post(
                f"goblin_stop_{shot_name}"
            )

        self.current_flashing.clear()
        self.current_solid.clear()

        self.pick_flashing_shots()

    def shot_hit(self, shot_name=None, **kwargs):

        if not shot_name:
            return

        if shot_name not in self.active_shots:
            return

        if self.hold_active:

            if shot_name in self.current_flashing:
                self.collect_flashing_shot(shot_name)

            return

        if shot_name in self.current_flashing:
            self.collect_flashing_shot(shot_name)

        elif shot_name in self.current_solid:
            self.collect_solid_shot(shot_name)

    def collect_flashing_shot(self, shot_name):

        self.machine.events.post("goblin_flashing_shot_score")

        self.active_shots.remove(shot_name)

        self.machine.events.post(f"goblin_stop_{shot_name}")

        self.current_flashing.discard(shot_name)

        if len(self.active_shots) <= 1:
            self.start_final_phase()
            return

        if not self.hold_active:
            self.pick_flashing_shots()

    def collect_solid_shot(self, shot_name):

        self.machine.events.post(
            "goblin_solid_shot_score"
        )

        player = self.machine.game.player

        new_bonus = max(
            player.goblin_chaos_lock,
            player.goblin_chaos_bonus - self.CHAOS_BONUS_LOSS
        )

        player.goblin_chaos_bonus = new_bonus

    def saucer_lock(self, saucer, **kwargs):

        if self.hold_active:
            #eject this new lock, we have one already
            self.machine.events.post("eject_saucer", saucer = saucer)
            return

        self.hold_active = True

        player = self.machine.game.player

        player.goblin_hold_active = 1

        player.goblin_chaos_lock = (
            player.goblin_chaos_bonus
        )

        player.goblin_hold_count += 1

        self.flash_time = max(
            self.MIN_FLASH_TIME,
            self.BASE_FLASH_TIME - player.goblin_hold_count
        )

        self.hold_time = max(
            self.MIN_HOLD_TIME,
            self.BASE_HOLD_TIME - player.goblin_hold_count
        )

        self.machine.events.post("goblin_hold_started")
        self.machine.events.post("goblin_flash_timer_stop")
        self.machine.events.post("goblin_solid_timer_stop")
        self.machine.events.post("goblin_hold_timer_start")

    def end_hold(self, **kwargs):

        self.hold_active = False

        player = self.machine.game.player
        player.goblin_hold_active = 0

        self.machine.events.post("goblin_hold_ended")

        self.pick_flashing_shots()

    def clear_flashing(self):

        for shot_name in self.current_flashing:
            self.machine.events.post(f"goblin_stop_{shot_name}")

    def clear_current_shows(self):

        self.clear_flashing()

        for shot_name in self.current_solid:
            self.machine.events.post(
                f"goblin_stop_{shot_name}"
            )

        self.current_flashing.clear()
        self.current_solid.clear()

    def start_flash_timer(self):

        self.machine.events.post(
            "goblin_flash_timer_stop"
        )

        self.machine.events.post(
            "goblin_flash_timer_start"
        )

    def start_solid_timer(self):

        self.machine.events.post(
            "goblin_solid_timer_stop"
        )

        self.machine.events.post(
            "goblin_solid_timer_start"
        )

    def start_final_phase(self):

        self.clear_current_shows()

        if not self.active_shots:
            self.machine.events.post(
                "goblin_mode_ended"
            )
            return

        final_shot = self.active_shots[0]

        self.current_flashing = {final_shot}

        self.machine.events.post(
            f"goblin_lite_{final_shot}"
        )

        self.machine.events.post(
            "goblin_super_jackpot_ready"
        )

    def mode_stop(self, **kwargs):

        self.clear_current_shows()

        self.machine.events.post(
            "goblin_flash_timer_stop"
        )

        self.machine.events.post(
            "goblin_solid_timer_stop"
        )

        self.machine.events.post(
            "goblin_hold_timer_stop"
        )