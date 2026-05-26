from dataclasses import dataclass
import random
from functools import partial

from mpf.core.mode import Mode

"""
    "title": "GREEN GOBLIN",
    "intro_1": "Goblin is attacking from above.",
    "intro_2": "Lit shots decrease - Flashing shots increase.",
    "intro_3": "Collect Jackpots and Rest in the saucers.",
    "summary_title_complete": "GOBLIN DEFEATED",
    "summary_title_failed": "GOBLIN ESCAPED",
    "stat_1_label": "ATTACK TOTAL",
    "stat_1_var": "goblin_attacks_value", # points collected from flashing shots
    "stat_2_label": "BONUS BANKED",
    "stat_2_var": "goblin_bonus_banked",
    "points_var": "goblin_mode_points",
    "completed_var": "goblin_completed",


# GOBLIN CHAOS MULTIBALL

### Start:

* 2-ball multiball begins
* Chaos Bonus = 0
* Chaos Bonus Banked = 0

### During Chaos:

* 3 random shots solid
* 3 random shots flashing
* shots becomes active
* after 6 sec all off
* pause for 2 sec
* repeat

### Shot scoring:

#### flashing hit:

* 50K live score
* +100K Chaos Bonus
* shot becomes inactive

#### solid hit:

* penalty shot
* only 2K live score
* deduct 100K from Chaos Bonus
* but never below Chaos Bonus Banked
* shot becomes inactive

---

# SAUCER = CHAOS STABILIZER

When either ball enters saucer:

* if current Chaos Bonus is greater than bank, set Chaos Bonus Bank
* else set Chaos Bonus to Chaos Bonus Bank
* held ball stays for 10 sec
* no penalty shots during hold window
* all currently active flashing shots stay flashing, solid shots turn off
* player gets controlled single-ball harvest time

Then:

* saucer eject
* random chaos pattern resumes

Each time saucer lock occurs:

* next hold time decreases by 1 second down to min 5 seconds

Players understand:
“I secured my gains, now I can push higher.”

---

### Chaos Bonus:

* banked bonus is paid out at end of ball
"""


@dataclass(frozen=True)
class GoblinShot:
    name: str
    event: str


class Goblin(Mode):

    # Timing from the mode description.
    CHAOS_WINDOW_MS = 6000
    CHAOS_PAUSE_MS = 2000

    BASE_HOLD_TIME_MS = 10000
    MIN_HOLD_TIME_MS = 5000
    HOLD_REDUCTION_PER_LOCK_MS = 1000

    FLASHING_SCORE = 50000
    SOLID_SCORE = 2000

    CHAOS_BONUS_ADD = 100000
    CHAOS_BONUS_LOSS = 100000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.shots = [
            GoblinShot("left_web", "goblin_left_web_hit"),
            GoblinShot("spinner", "goblin_spinner_hit"),
            GoblinShot("left_drops", "goblin_left_drops_hit"),
            GoblinShot("right_web", "goblin_right_web_hit"),
            GoblinShot("upper_spinner", "goblin_upper_spinner_hit"),
            GoblinShot("upper_target", "goblin_upper_target_hit"),
            GoblinShot("right_drops", "goblin_right_drops_hit"),
        ]

        self.active_shots = set()
        self.current_flashing = set()
        self.current_solid = set()
        self.hold_active = False
        self.mode_finishing = False
        self.bonus_paid = False
        self.held_saucer = None

        for shot in self.shots:
            self.add_mode_event_handler(
                shot.event,
                self.shot_hit,
                shot_name=shot.name
            )

        self.add_mode_event_handler("goblin_saucer_hit", self.saucer_lock)
        self.add_mode_event_handler("goblin_saucer_1_hit", partial(self.saucer_lock, saucer=1))
        self.add_mode_event_handler("goblin_saucer_2_hit", partial(self.saucer_lock, saucer=2))
        self.add_mode_event_handler("goblin_saucer_3_hit", partial(self.saucer_lock, saucer=3))
        self.add_mode_event_handler("goblin_collect_bonus", self.collect_banked_bonus)
        self.add_mode_event_handler("ball_ending", self.collect_banked_bonus)

        self.add_mode_event_handler(
            "multiball_goblin_chaos_multiball_started",
            self.multiball_started
        )
        self.add_mode_event_handler(
            "multiball_goblin_chaos_multiball_ended",
            self.multiball_ended
        )

        self.begin_mode()

    def begin_mode(self):
        self.info_log("Starting Goblin Chaos Multiball")

        self.active_shots = {shot.name for shot in self.shots}
        self.current_flashing.clear()
        self.current_solid.clear()
        self.hold_active = False
        self.mode_finishing = False
        self.bonus_paid = False
        self.held_saucer = None

        self._set_player_var("goblin_chaos_bonus", 0)
        self._set_player_var("goblin_bonus_banked", 0)
        self._set_player_var("goblin_chaos_lock", 0)  # compatibility with older widgets/code
        self._set_player_var("goblin_hold_count", 0)
        self._set_player_var("goblin_hold_active", 0)
        self._set_player_var("goblin_attacks_value", 0)
        self._set_player_var("goblin_mode_points", 0)
        self._set_player_var("goblin_completed", 0)

        self.machine.events.post("reset_drops")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("goblin_start_multiball")

        self.start_chaos_pattern()

    # -------------------------------------------------------------------------
    # Chaos pattern
    # -------------------------------------------------------------------------

    def start_chaos_pattern(self):
        if self.mode_finishing or self.hold_active:
            return

        self.clear_current_shows()

        # Every new chaos window resets shot availability. A hit only disables
        # that shot for the current 6 second chaos window / hold window, not for
        # the whole mode.
        self.active_shots = {shot.name for shot in self.shots}

        available = list(self.active_shots)
        random.shuffle(available)

        flashing = available[:3]
        solid = available[3:6]

        self.current_flashing = set(flashing)
        self.current_solid = set(solid)

        for shot_name in self.current_flashing:
            self.machine.events.post(f"goblin_lite_{shot_name}")

        for shot_name in self.current_solid:
            self.machine.events.post(f"goblin_solid_{shot_name}")

        self.delay.remove("goblin_chaos_window")
        self.delay.add(
            name="goblin_chaos_window",
            ms=self.CHAOS_WINDOW_MS,
            callback=self.chaos_window_complete
        )

    def chaos_window_complete(self):
        if self.mode_finishing or self.hold_active:
            return

        self.clear_current_shows()

        self.delay.remove("goblin_chaos_pause")
        self.delay.add(
            name="goblin_chaos_pause",
            ms=self.CHAOS_PAUSE_MS,
            callback=self.start_chaos_pattern
        )

    # -------------------------------------------------------------------------
    # Shot handling
    # -------------------------------------------------------------------------

    def shot_hit(self, shot_name=None, **kwargs):
        if self.mode_finishing or not shot_name:
            return

        if shot_name not in self.active_shots:
            return

        if shot_name in self.current_flashing:
            self.collect_flashing_shot(shot_name)
            return

        # No penalty shots during saucer hold. Solids are normally turned off during
        # hold, but this guard keeps the rule safe if a switch/event sneaks through.
        if self.hold_active:
            return

        if shot_name in self.current_solid:
            self.collect_solid_shot(shot_name)

    def collect_flashing_shot(self, shot_name):
        self.info_log("Goblin flashing shot collected: %s", shot_name)

        self._award_points(self.FLASHING_SCORE)
        self._add_player_var("goblin_attacks_value", self.FLASHING_SCORE)
        self._add_player_var("goblin_chaos_bonus", self.CHAOS_BONUS_ADD)

        self.deactivate_shot(shot_name)
        self.machine.events.post("goblin_flashing_shot_score", shot=shot_name)

    def collect_solid_shot(self, shot_name):
        self.info_log("Goblin solid penalty shot hit: %s", shot_name)

        self._award_points(self.SOLID_SCORE)

        banked = self._get_player_var("goblin_bonus_banked", 0)
        current_bonus = self._get_player_var("goblin_chaos_bonus", 0)
        new_bonus = max(banked, current_bonus - self.CHAOS_BONUS_LOSS)
        self._set_player_var("goblin_chaos_bonus", new_bonus)

        self.deactivate_shot(shot_name)
        self.machine.events.post("goblin_solid_shot_score", shot=shot_name)

    def deactivate_shot(self, shot_name):
        self.active_shots.discard(shot_name)
        self.current_flashing.discard(shot_name)
        self.current_solid.discard(shot_name)
        self.machine.events.post(f"goblin_stop_{shot_name}")

    # -------------------------------------------------------------------------
    # Saucers / hold window
    # -------------------------------------------------------------------------

    def saucer_lock(self, saucer=None, **kwargs):
        if self.mode_finishing:
            return

        if self.hold_active:
            # Do not allow a second saucer to restart/extend the hold. Eject it.
            self.delay.add(
                name=f"goblin_extra_saucer_eject_{saucer}",
                ms=1000,
                callback=self.delayed_eject,
                saucer=saucer
            )
            return

        self.info_log("Goblin saucer stabilizer hit: %s", saucer)
        self.held_saucer = saucer
        self.hold_active = True
        self._set_player_var("goblin_hold_active", 1)
        self._add_player_var("goblin_hold_count", 1)

        # Secure gains or restore to the secured bank.
        current_bonus = self._get_player_var("goblin_chaos_bonus", 0)
        banked = self._get_player_var("goblin_bonus_banked", 0)

        if current_bonus > banked:
            banked = current_bonus
            self._set_player_var("goblin_bonus_banked", banked)
            self._set_player_var("goblin_chaos_lock", banked)
        else:
            self._set_player_var("goblin_chaos_bonus", banked)
            self._set_player_var("goblin_chaos_lock", banked)

        # Stop the active chaos window and turn off all solid penalty shots.
        self.delay.remove("goblin_chaos_window")
        self.delay.remove("goblin_chaos_pause")

        for shot_name in list(self.current_solid):
            self.machine.events.post(f"goblin_stop_{shot_name}")
        self.current_solid.clear()

        self.machine.events.post("goblin_hold_started", saucer=saucer)

        hold_time_ms = self.get_current_hold_time_ms()
        self.delay.remove("goblin_hold_timer")
        self.delay.add(
            name="goblin_hold_timer",
            ms=hold_time_ms,
            callback=self.end_hold
        )

    def get_current_hold_time_ms(self):
        hold_count = self._get_player_var("goblin_hold_count", 0)
        return max(
            self.MIN_HOLD_TIME_MS,
            self.BASE_HOLD_TIME_MS - ((hold_count - 1) * self.HOLD_REDUCTION_PER_LOCK_MS)
        )

    def end_hold(self, **kwargs):
        if self.mode_finishing:
            return

        self.info_log("Goblin saucer hold ended")
        self.hold_active = False
        self._set_player_var("goblin_hold_active", 0)

        saucer = self.held_saucer
        self.held_saucer = None

        self.machine.events.post("goblin_hold_ended", saucer=saucer)
        self.machine.events.post("clear_saucers")

        if saucer is not None:
            self.delayed_eject(saucer=saucer)

        # Resume with a fresh random chaos pattern after the hold.
        self.delay.add(
            name="goblin_resume_after_hold",
            ms=250,
            callback=self.start_chaos_pattern
        )

    def delayed_eject(self, saucer=None, **kwargs):
        if saucer is not None:
            self.machine.events.post("eject_saucer", saucer=saucer)

    def eject_held_saucer(self, reason=None):
        saucer = self.held_saucer
        if saucer is None:
            return

        self.info_log("Goblin ejecting held saucer %s because %s", saucer, reason)
        self.held_saucer = None
        self.hold_active = False
        self._set_player_var("goblin_hold_active", 0)
        self.machine.events.post("goblin_hold_ended", saucer=saucer)
        self.machine.events.post("clear_saucers")
        self.delayed_eject(saucer=saucer)

    # -------------------------------------------------------------------------
    # Multiball / mode ending
    # -------------------------------------------------------------------------

    def multiball_started(self, **kwargs):
        self._set_player_var("multiball_autoplunge_active", 1)

    def multiball_ended(self, **kwargs):
        self._set_player_var("multiball_autoplunge_active", 0)

        # Goblin ends when multiball drops to one ball. If that remaining ball
        # is being held in a saucer, eject it before ending the mode.
        if self.held_saucer is not None:
            self.eject_held_saucer(reason="multiball_ended")

        if not self.mode_finishing:
            self.finish_mode(completed=False)

    def collect_banked_bonus(self, **kwargs):
        if self.bonus_paid:
            return

        banked = self._get_player_var("goblin_bonus_banked", 0)
        if banked <= 0:
            return

        self.bonus_paid = True
        self._award_points(banked)
        self.machine.events.post("goblin_bonus_collected", value=banked)

    def finish_mode(self, completed=False):
        if self.mode_finishing:
            return

        self.mode_finishing = True

        if self.held_saucer is not None:
            self.eject_held_saucer(reason="mode_finish")

        self.clear_all_delays()
        self.clear_current_shows()
        self.machine.events.post("goblin_mode_ended")

        self._set_player_var("goblin_completed", 1 if completed else 0)

        if completed:
            self.collect_banked_bonus()
            self.machine.events.post("goblin_mode_complete")
        else:
            self.machine.events.post("goblin_mode_failed")

        self.machine.events.post(
            "villain_bookend_summary_request",
            villain="goblin",
            done_event="goblin_mode_completed_summary"
        )

    def mode_stop(self, **kwargs):
        self.clear_all_delays()
        self.clear_current_shows()
        self.machine.events.post("goblin_mode_ended")
        self._set_player_var("multiball_autoplunge_active", 0)
        super().mode_stop(**kwargs)

    def clear_all_delays(self):
        for name in (
            "goblin_chaos_window",
            "goblin_chaos_pause",
            "goblin_hold_timer",
            "goblin_resume_after_hold",
            "goblin_extra_saucer_eject_1",
            "goblin_extra_saucer_eject_2",
            "goblin_extra_saucer_eject_3",
        ):
            self.delay.remove(name)

    # -------------------------------------------------------------------------
    # Shows / variables / scoring helpers
    # -------------------------------------------------------------------------

    def clear_current_shows(self):
        for shot_name in list(self.current_flashing):
            self.machine.events.post(f"goblin_stop_{shot_name}")

        for shot_name in list(self.current_solid):
            self.machine.events.post(f"goblin_stop_{shot_name}")

        self.current_flashing.clear()
        self.current_solid.clear()

    def _award_points(self, points):
        self._add_player_var("score", points)
        self._add_player_var("goblin_mode_points", points)

    def _player(self):
        if not self.machine.game:
            return None
        return self.machine.game.player

    def _get_player_var(self, name, default=0):
        player = self._player()
        if not player:
            return default

        try:
            return player[name]
        except (KeyError, TypeError):
            return getattr(player, name, default)

    def _set_player_var(self, name, value):
        player = self._player()
        if not player:
            return

        try:
            player[name] = value
        except TypeError:
            setattr(player, name, value)

    def _add_player_var(self, name, amount):
        self._set_player_var(name, self._get_player_var(name, 0) + amount)
