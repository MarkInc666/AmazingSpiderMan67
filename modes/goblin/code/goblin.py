from dataclasses import dataclass
import random
from functools import partial

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

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
    "points_var": "active_mode_points",
    "state_var": "goblin_state",


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


class Goblin(CaseFileMixin, Mode):

    # Timing from the mode description.
    CHAOS_WINDOW_MS = 6000
    CHAOS_PAUSE_MS = 2000

    BASE_HOLD_TIME_MS = 10000
    MIN_HOLD_TIME_MS = 5000
    HOLD_REDUCTION_PER_LOCK_MS = 1000
    MIN_HOLD_FLASHING_SHOTS = 4

    JACKPOT_START = 100000
    JACKPOT_STEP = 50000
    JACKPOT_MAX = 500000
    FLASHING_SCORE = 100000
    SOLID_SCORE = 2000

    CHAOS_BONUS_ADD = 100000
    CHAOS_BONUS_LOSS = 50000

    UPPER_GATE_SHOTS = {"upper_targets", "upper_spinner"}

    def _update_upper_gate_from_lit_shots(self):
        upper_lit = bool(
            (self.current_flashing | self.current_solid) & self.UPPER_GATE_SHOTS
        )

        if upper_lit:
            self.machine.events.post("rooftop_diverter_open")
        else:
            self.machine.events.post("rooftop_diverter_close")

    def _update_mode_status(self):
        if getattr(self, "hold_active", False):
            title = "CHAOS STABILIZED"
            value = f"BANK {self.machine.game.player['goblin_bonus_banked']:,}"
        else:
            title = "CHAOS BONUS"
            value = f"{self.machine.game.player['goblin_chaos_bonus']:,}"
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("goblin")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA CHAOS JACKPOT AVAILABLE"),
            ("bigger_jackpots", "CHAOS BONUS BOOSTED"),
            ("more_time", "CHAOS WINDOW EXTENDED"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FLASHING SHOTS HELD LONGER"),
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

    def _apply_case_file_bonuses(self):
        self.case_file_extra_chaos_jackpot = False

        if self.has_case_file("more_jackpots"):
            self.case_file_extra_chaos_jackpot = True

        if self.has_case_file("bigger_jackpots"):
            self.FLASHING_SCORE += 25000
            self.CHAOS_BONUS_ADD += 50000

        if self.has_case_file("more_time"):
            self.CHAOS_WINDOW_MS += 2000
            self.BASE_HOLD_TIME_MS += 2000

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.CHAOS_WINDOW_MS += 1000

    def begin_mode(self):
        self.info_log("Starting Goblin Chaos Multiball")

        self.active_shots = {shot.name for shot in self.shots}
        self.current_flashing.clear()
        self.current_solid.clear()
        self.hold_active = False
        self.mode_finishing = False
        self.bonus_paid = False
        self.held_saucer = None

        self.machine.game.player["goblin_chaos_bonus"] = 0
        self.machine.game.player["goblin_bonus_banked"] = 0
        self.machine.game.player["goblin_chaos_lock"] = 0  # compatibility with older widgets/code
        self.machine.game.player["goblin_hold_count"] = 0
        self.machine.game.player["goblin_hold_active"] = 0
        self.machine.game.player["goblin_attacks_value"] = 0
        self.machine.game.player["active_mode_points"] = 0
        self.machine.game.player["goblin_state"] = 1
        self.machine.game.player["goblin_jackpot_value"] = self.JACKPOT_START

        self.machine.events.post("reset_drops")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("goblin_lite_saucers")
        self.machine.events.post("goblin_start_multiball")
        self.machine.events.post("show_mode_message_long", message_mode_title="CHAOS MULTIBALL", message_mode_subtitle="HIT FLASHING SHOTS")

        self.start_chaos_pattern()
        self._update_mode_status()

    # -------------------------------------------------------------------------
    # Chaos pattern
    # -------------------------------------------------------------------------

    def start_chaos_pattern(self):
        if self.mode_finishing or self.hold_active:
            return
        self.clear_current_shows()
        self.active_shots = {shot.name for shot in self.shots}
        self.current_flashing.clear()
        self.current_solid = set(self.active_shots)
        for shot_name in self.current_solid:
            self.machine.events.post(f"goblin_solid_{shot_name}")
        self.machine.events.post("show_mode_message", message_mode_title="CHAOS!", message_mode_subtitle="GET A BALL TO A SAUCER", reminder=True)
        self._update_mode_status()

    def chaos_window_complete(self):
        if self.mode_finishing or self.hold_active:
            return

        self.clear_current_shows()
        self._update_upper_gate_from_lit_shots()

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
        if self.machine.game.player["villain_mode_in_summary"] is True or self.mode_finishing or not shot_name:
            return
        if shot_name not in self.active_shots:
            return
        if self.hold_active:
            self.collect_flashing_shot(shot_name)
        else:
            self.collect_solid_shot(shot_name)

    def collect_flashing_shot(self, shot_name):
        value = int(self.machine.game.player["goblin_jackpot_value"])
        self._award_points(value)
        self.machine.game.player["goblin_attacks_value"] += value
        self.machine.game.player["goblin_chaos_bonus"] += value
        self.machine.game.player["goblin_bonus_banked"] = self.machine.game.player["goblin_chaos_bonus"]
        self.machine.game.player["goblin_jackpot_value"] = min(self.JACKPOT_MAX, value + self.JACKPOT_STEP)
        self.deactivate_shot(shot_name)
        self.machine.events.post("goblin_flashing_shot_score", shot=shot_name)
        self.machine.events.post("show_mode_jackpot", message_mode_title="GOBLIN JACKPOT", message_mode_subtitle=shot_name.replace("_", " ").upper(), message_mode_value=value)
        self._update_mode_status()

    def collect_solid_shot(self, shot_name):
        value = int(self.machine.game.player["goblin_jackpot_value"])
        loss = value // 2
        self._award_points(self.SOLID_SCORE)
        self.machine.game.player["goblin_chaos_bonus"] = max(0, self.machine.game.player["goblin_chaos_bonus"] - loss)
        self.machine.events.post("goblin_solid_shot_score", shot=shot_name)
        self.machine.events.post("show_mode_message", message_mode_title="CHAOS HIT", message_mode_subtitle="CHAOS BONUS REDUCED", message_mode_value=self.machine.game.player["goblin_chaos_bonus"])
        self._update_mode_status()

    def deactivate_shot(self, shot_name):
        self.active_shots.discard(shot_name)
        self.current_flashing.discard(shot_name)
        self._update_mode_status()
        self.current_solid.discard(shot_name)
        self._update_mode_status()
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
        self.machine.events.post("goblin_stop_saucers")
        self.machine.events.post("goblin_solid_saucers")
        self.held_saucer = saucer
        self.hold_active = True
        self.machine.game.player["goblin_hold_active"] = 1
        self.machine.game.player["goblin_hold_count"] += 1

        # Secure gains or restore to the secured bank.
        current_bonus = self.machine.game.player["goblin_chaos_bonus"]
        banked = self.machine.game.player["goblin_bonus_banked"]

        if current_bonus > banked:
            banked = current_bonus
            self.machine.game.player["goblin_bonus_banked"] = banked
            self.machine.game.player["goblin_chaos_lock"] = banked
        else:
            self.machine.game.player["goblin_chaos_bonus"] = banked
            self.machine.game.player["goblin_chaos_lock"] = banked

        # Stop the active chaos window and turn off all solid penalty shots.
        self.delay.remove("goblin_chaos_window")
        self.delay.remove("goblin_chaos_pause")

        self.active_shots = {shot.name for shot in self.shots}
        self.current_flashing = set(self.active_shots)
        self.current_solid.clear()
        for shot_name in self.current_flashing:
            self.machine.events.post(f"goblin_stop_{shot_name}")
            self.machine.events.post(f"goblin_lite_{shot_name}")
        self._update_upper_gate_from_lit_shots()
        
        self.machine.events.post("goblin_hold_started", saucer=saucer)
        self.machine.events.post("show_mode_message_long", message_mode_title="CHAOS CALMED", message_mode_subtitle="HIT LIT TARGETS BEFORE RELEASE", message_mode_value=banked)

        hold_time_ms = self.get_current_hold_time_ms()
        self.delay.remove("goblin_hold_timer")
        self.delay.add(
            name="goblin_hold_timer",
            ms=hold_time_ms,
            callback=self.end_hold
        )


    def ensure_minimum_hold_flashing_shots(self):
        """Make sure saucer rest mode has enough safe flashing shots.

        Entering a saucer can happen late in a chaos window after several
        flashing shots have already been collected. Rest mode should not leave
        the player with only one or two safe shots available. Re-enable random
        non-flashing shots as flashing-only harvest shots until at least four
        are available, or until every Goblin shot is already flashing.
        """
        needed = self.MIN_HOLD_FLASHING_SHOTS - len(self.current_flashing)
        if needed <= 0:
            return

        candidates = [
            shot.name for shot in self.shots
            if shot.name not in self.current_flashing
        ]
        random.shuffle(candidates)

        for shot_name in candidates[:needed]:
            self.active_shots.add(shot_name)
            self.current_flashing.add(shot_name)
            self.machine.events.post(f"goblin_stop_{shot_name}")
            self.machine.events.post(f"goblin_lite_{shot_name}")

        self.machine.events.post(
            "goblin_hold_flashing_shots_ensured",
            count=len(self.current_flashing)
        )

    def get_current_hold_time_ms(self):
        hold_count = self.machine.game.player["goblin_hold_count"]
        return max(
            self.MIN_HOLD_TIME_MS,
            self.BASE_HOLD_TIME_MS - ((hold_count - 1) * self.HOLD_REDUCTION_PER_LOCK_MS)
        )

    def end_hold(self, **kwargs):
        if self.mode_finishing:
            return

        self.info_log("Goblin saucer hold ended")
        self.hold_active = False
        self.machine.game.player["goblin_hold_active"] = 0

        saucer = self.held_saucer
        self.held_saucer = None

        self.machine.events.post("goblin_hold_ended", saucer=saucer)
        self.machine.events.post("goblin_stop_saucers")
        self.machine.events.post("goblin_lite_saucers")
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
            self.machine.events.post(f"delayed_kickout_saucer_{saucer}")

    def eject_held_saucer(self, reason=None):
        saucer = self.held_saucer
        if saucer is None:
            return

        self.info_log("Goblin ejecting held saucer %s because %s", saucer, reason)
        self.held_saucer = None
        self.hold_active = False
        self.machine.game.player["goblin_hold_active"] = 0
        self.machine.events.post("goblin_hold_ended", saucer=saucer)
        self.delayed_eject(saucer=saucer)

    # -------------------------------------------------------------------------
    # Multiball / mode ending
    # -------------------------------------------------------------------------

    def multiball_started(self, **kwargs):
        self.machine.game.player["multiball_autoplunge_active"] = 1

    def multiball_ended(self, **kwargs):
        self.machine.game.player["multiball_autoplunge_active"] = 0

        # Goblin ends when multiball drops to one ball. If that remaining ball
        # is being held in a saucer, eject it before ending the mode.
        if self.held_saucer is not None:
            self.eject_held_saucer(reason="multiball_ended")

        if not self.mode_finishing:
            self.finish_mode(completed=False)

    def collect_banked_bonus(self, **kwargs):
        if self.bonus_paid:
            return

        banked = self.machine.game.player["goblin_bonus_banked"]
        if banked <= 0:
            return

        if getattr(self, "case_file_extra_chaos_jackpot", False):
            banked += 250000
            self.case_file_extra_chaos_jackpot = False
            self.machine.events.post("goblin_case_file_extra_chaos_jackpot")

        # Match Vulture's bonus behavior: bank the value for the normal
        # end-of-ball bonus count instead of scoring it immediately here.
        player = self.machine.game.player
        player["goblin_bonus"] = player["goblin_bonus"] + banked

        self.bonus_paid = True
        self.machine.events.post("goblin_bonus_collected", value=banked)
        self.machine.events.post("show_mode_jackpot", message_mode_title="GOBLIN BONUS BANKED", message_mode_subtitle="CHAOS BANK", message_mode_value=banked)

    def finish_mode(self, completed=False):
        if self.mode_finishing:
            return

        self.mode_finishing = True

        if self.held_saucer is not None:
            self.eject_held_saucer(reason="mode_finish")

        self.clear_all_delays()
        self.clear_current_shows()
        self.machine.events.post("goblin_mode_ended")

        self.machine.game.player["goblin_state"] = 2

        self.collect_banked_bonus()
        self.machine.events.post("goblin_mode_complete")

    def mode_stop(self, **kwargs):
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        self.clear_all_delays()
        self.clear_current_shows()
        self.machine.events.post("goblin_mode_ended")
        self.machine.game.player["multiball_autoplunge_active"] = 0
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
        self.machine.game.player["score"] += points
        self.machine.game.player["active_mode_points"] += points


