from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
CYCLOPS - EYE OF DOOM

Limited-flips monster mode.
- Center web target is the Cyclops Eye.
- Player starts with 20 flips, or 30 with More Time.
- Each main flipper button press spends 1 flip.
- Each drop target hit adds 3 flips; every rubber hit adds 1 flip.
- Drop banks reset immediately when completed.
- Eye Jackpot = remaining flips * 100K, capped at 2M.
- Bigger Jackpots changes the rate to 150K per flip; the cap remains 2M.
- More Jackpots adds a second Eye after a 2s Jackpot-message hold. The second
  Eye is available for 20s; expiry shows EYE SEE YOU for 2s, then ends.
- Safety Net is a 10s ball save at mode start.
- Shot Assist: the first drop hit also knocks down and awards two standing
  targets on the right bank.
- Final Jackpot and out-of-flips endings hold their message for 2s before the
  villain summary.
"""


class Cyclops(CaseFileMixin, Mode):
    MODE_KEY = "cyclops"
    DISPLAY_NAME = "Cyclops"

    STARTING_FLIPS = 20
    MORE_TIME_FLIPS = 30
    DROP_FLIP_AWARD = 3
    RUBBER_FLIP_AWARD = 1
    JACKPOT_PER_FLIP = 100_000
    BIGGER_JACKPOT_PER_FLIP = 150_000
    JACKPOT_CAP = 2_000_000
    SECOND_EYE_SECONDS = 20
    PRESENTATION_HOLD_MS = 2_000

    RIGHT_DROPS = (1, 2, 3, 4, 5)

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.mode_finishing = False
        self.eye_available = True
        self.first_eye_hold_active = False
        self.second_eye_active = False
        self.second_eye_seconds_remaining = 0
        self.eye_jackpots = 0
        self.best_jackpot = 0
        self.mode_points = 0
        self.flips_used = 0
        self.drops_hit = 0
        self.rubbers_hit = 0
        self.shot_assist_used = False
        self.right_drops_down = set()
        self.safety_net_used = False

        self.starting_flips = (
            self.MORE_TIME_FLIPS
            if self.has_case_file("more_time")
            else self.STARTING_FLIPS
        )
        self.flips_remaining = self.starting_flips
        self.jackpot_per_flip = (
            self.BIGGER_JACKPOT_PER_FLIP
            if self.has_case_file("bigger_jackpots")
            else self.JACKPOT_PER_FLIP
        )
        self.max_eye_jackpots = 2 if self.has_case_file("more_jackpots") else 1

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SECOND EYE - 20 SECOND WINDOW"),
            ("bigger_jackpots", "EYE JACKPOT 150K PER FLIP"),
            ("more_time", "START WITH 30 FLIPS"),
            ("safety_net", "10 SECOND BALL SAVE"),
            ("shot_assist", "FIRST DROP ADDS TWO RIGHT DROPS"),
        ])

        self.add_mode_event_handler("s_left_flipper_active", self._flipper_pressed)
        self.add_mode_event_handler("s_right_flipper_active", self._flipper_pressed)
        self.add_mode_event_handler("cyclops_eye_hit", self._eye_hit)
        self.add_mode_event_handler("cyclops_rubber_hit", self._rubber_hit)

        self.add_mode_event_handler("cyclops_left_drop_1_hit", self._drop_hit, bank="left", number=1)
        self.add_mode_event_handler("cyclops_left_drop_2_hit", self._drop_hit, bank="left", number=2)
        self.add_mode_event_handler("cyclops_left_drop_3_hit", self._drop_hit, bank="left", number=3)
        self.add_mode_event_handler("cyclops_right_drop_1_hit", self._drop_hit, bank="right", number=1)
        self.add_mode_event_handler("cyclops_right_drop_2_hit", self._drop_hit, bank="right", number=2)
        self.add_mode_event_handler("cyclops_right_drop_3_hit", self._drop_hit, bank="right", number=3)
        self.add_mode_event_handler("cyclops_right_drop_4_hit", self._drop_hit, bank="right", number=4)
        self.add_mode_event_handler("cyclops_right_drop_5_hit", self._drop_hit, bank="right", number=5)
        self.add_mode_event_handler("cyclops_right_bank_down", self._right_bank_down)
        self.add_mode_event_handler("ball_save_cyclops_safety_net_saving_ball", self._safety_net_saved_ball)
        self.add_mode_event_handler("cyclops_fail_request", self._complete_mode)
        self.add_mode_event_handler("cyclops_complete_request", self._complete_mode)

        self.machine.events.post("cyclops_mode_started")
        self.machine.events.post("cyclops_eye_lit")
        if self.has_case_file("safety_net"):
            self.machine.events.post("cyclops_enable_safety_net")
        self._show_mode_message("HIT THE EYE", f"{self.flips_remaining} FLIPS", reminder=True)
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

    def mode_stop(self, **kwargs):
        self.delay.remove("cyclops_second_eye_start")
        self.delay.remove("cyclops_second_eye_tick")
        self.delay.remove("cyclops_second_eye_expire")
        self.delay.remove("cyclops_finish_hold")
        self.machine.events.post("cyclops_eye_unlit")
        self.machine.events.post("cyclops_disable_safety_net")
        self.clear_active_case_file_helpers()
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        super().mode_stop(**kwargs)

    def _flipper_pressed(self, **kwargs):
        if self._inactive():
            return

        self.flips_remaining -= 1
        self.flips_used += 1
        self.machine.events.post("cyclops_flip_used", flips_remaining=self.flips_remaining)

        if self.flips_remaining <= 0:
            self.flips_remaining = 0
            self._sync_vars()
            self._finish_out_of_flips()
            return

        if self.flips_remaining <= 5 or self.flips_remaining % 5 == 0:
            self._show_mode_message("FLIPS REMAINING", str(self.flips_remaining))
        self._sync_vars()

    def _drop_hit(self, bank, number, **kwargs):
        if self._inactive():
            return
        if bank == "right" and number in self.right_drops_down:
            return

        self._award_drop(bank, number)

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            self.shot_assist_used = True
            assisted = 0
            for _ in range(2):
                extra = self._first_available_right_drop()
                if extra is None:
                    break
                # Pre-mark and award before the physical switch event arrives;
                # that later event is ignored so assisted targets never double-score.
                self.machine.events.post(f"cyclops_shot_assist_drop_{extra}")
                self._award_drop("right", extra, assisted=True)
                assisted += 1
            self.machine.events.post("cyclops_shot_assist_used", drops_awarded=assisted)
            if assisted:
                self._show_mode_message("SHOT ASSIST", f"+{assisted * self.DROP_FLIP_AWARD} FLIPS")

        self._sync_vars()

    def _award_drop(self, bank, number, assisted=False):
        if bank == "right":
            self.right_drops_down.add(number)
        self.drops_hit += 1
        self.flips_remaining += self.DROP_FLIP_AWARD
        self.machine.events.post(
            "cyclops_flips_added",
            flips_added=self.DROP_FLIP_AWARD,
            flips_remaining=self.flips_remaining,
        )
        self.machine.events.post(
            "cyclops_drop_hit",
            bank=bank,
            number=number,
            assisted=assisted,
            flips_remaining=self.flips_remaining,
        )
        if not assisted:
            self._show_mode_message("+3 FLIPS", f"{self.flips_remaining} FLIPS LEFT")

    def _rubber_hit(self, **kwargs):
        if self._inactive():
            return
        self.rubbers_hit += 1
        self.flips_remaining += self.RUBBER_FLIP_AWARD
        self.machine.events.post(
            "cyclops_flips_added",
            flips_added=self.RUBBER_FLIP_AWARD,
            flips_remaining=self.flips_remaining,
        )
        self.machine.events.post("cyclops_rubber_flip_added", flips_remaining=self.flips_remaining)
        self._show_mode_message("+1 FLIP", f"{self.flips_remaining} FLIPS LEFT")
        self._sync_vars()

    def _right_bank_down(self, **kwargs):
        # The YAML immediately resets the physical bank. Clear software state so
        # every target can award flips again on the next pass.
        self.right_drops_down.clear()
        self._sync_vars()

    def _safety_net_saved_ball(self, **kwargs):
        self.safety_net_used = True
        self._sync_vars()

    def _eye_hit(self, **kwargs):
        if self._inactive() or not self.eye_available:
            return

        jackpot = self._current_jackpot_value()
        self._award_score(jackpot)
        self.eye_jackpots += 1
        self.best_jackpot = max(self.best_jackpot, jackpot)
        self.eye_available = False

        player = self.machine.game.player
        player["cyclops_last_jackpot"] = jackpot
        self.machine.events.post("cyclops_eye_unlit")
        self.machine.events.post(
            "cyclops_eye_jackpot_awarded",
            jackpot=jackpot,
            eye_jackpots=self.eye_jackpots,
            flips_remaining=self.flips_remaining,
        )
        self._show_mode_jackpot("CYCLOPS JACKPOT", jackpot, f"{self.flips_remaining} FLIPS")

        if self.eye_jackpots >= self.max_eye_jackpots:
            self._begin_finish_hold()
        else:
            # Preserve the first Jackpot message for two full seconds. The
            # second Eye chase and its 20s timer begin only after this hold.
            self.first_eye_hold_active = True
            self.delay.add(
                name="cyclops_second_eye_start",
                ms=self.PRESENTATION_HOLD_MS,
                callback=self._start_second_eye,
            )
        self._sync_vars()

    def _start_second_eye(self):
        if self._inactive():
            return
        self.first_eye_hold_active = False
        self.eye_available = True
        self.second_eye_active = True
        self.second_eye_seconds_remaining = self.SECOND_EYE_SECONDS
        self.machine.events.post("cyclops_second_eye_lit")
        self.machine.events.post("cyclops_eye_lit")
        self.delay.add(
            name="cyclops_second_eye_tick",
            ms=1_000,
            callback=self._second_eye_tick,
        )
        self.delay.add(
            name="cyclops_second_eye_expire",
            ms=self.SECOND_EYE_SECONDS * 1_000,
            callback=self._second_eye_expired,
        )
        self._sync_vars()

    def _second_eye_tick(self):
        if self._inactive() or not self.second_eye_active:
            return
        self.second_eye_seconds_remaining = max(0, self.second_eye_seconds_remaining - 1)
        if self.second_eye_seconds_remaining > 1:
            self.delay.add(
                name="cyclops_second_eye_tick",
                ms=1_000,
                callback=self._second_eye_tick,
            )
        self._sync_vars()

    def _second_eye_expired(self):
        if self._inactive() or not self.second_eye_active:
            return
        self.second_eye_active = False
        self.eye_available = False
        self.second_eye_seconds_remaining = 0
        self.machine.events.post("cyclops_eye_unlit")
        self.machine.events.post("hide_mode_status")
        self._show_mode_message("EYE SEE YOU")
        self._schedule_finish()
        self._sync_vars()

    def _finish_out_of_flips(self, **kwargs):
        if self._inactive():
            return
        self.eye_available = False
        self.second_eye_active = False
        self.second_eye_seconds_remaining = 0
        self.machine.events.post("cyclops_eye_unlit")
        self.machine.events.post("hide_mode_status")
        self._show_mode_message("OUT OF FLIPS")
        self._schedule_finish()
        self._sync_vars()

    def _begin_finish_hold(self):
        self.second_eye_active = False
        self.second_eye_seconds_remaining = 0
        self.machine.events.post("hide_mode_status")
        self._schedule_finish()

    def _schedule_finish(self):
        if self.mode_finishing or self.mode_done:
            return
        self.mode_finishing = True
        self.delay.remove("cyclops_second_eye_start")
        self.delay.remove("cyclops_second_eye_tick")
        self.delay.remove("cyclops_second_eye_expire")
        self.delay.add(
            name="cyclops_finish_hold",
            ms=self.PRESENTATION_HOLD_MS,
            callback=self._complete_mode,
        )

    def _current_jackpot_value(self):
        return min(self.flips_remaining * self.jackpot_per_flip, self.JACKPOT_CAP)

    def _first_available_right_drop(self):
        for number in self.RIGHT_DROPS:
            if number not in self.right_drops_down:
                return number
        return None

    def _award_score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.mode_finishing = True
        self.eye_available = False
        self.second_eye_active = False
        self.delay.remove("cyclops_second_eye_start")
        self.delay.remove("cyclops_second_eye_tick")
        self.delay.remove("cyclops_second_eye_expire")
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars()
        self.machine.events.post("cyclops_mode_complete")

    def _update_second_eye_status(self):
        self.machine.events.post(
            "update_mode_status",
            mode_status_title="SECOND EYE",
            mode_status_value=f"{self.flips_remaining} FLIPS / {self.second_eye_seconds_remaining}s",
        )

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.drops_hit + self.rubbers_hit
        player["active_mode_major_hits"] = self.eye_jackpots
        player["cyclops_flips_remaining"] = self.flips_remaining
        player["cyclops_flips_used"] = self.flips_used
        player["cyclops_drops_hit"] = self.drops_hit
        player["cyclops_rubbers_hit"] = self.rubbers_hit
        player["cyclops_eye_jackpots"] = self.eye_jackpots
        player["cyclops_best_jackpot"] = self.best_jackpot
        player["cyclops_jackpot_value"] = self._current_jackpot_value()
        player["cyclops_jackpot_cap"] = self.JACKPOT_CAP
        player["cyclops_second_eye_seconds"] = self.second_eye_seconds_remaining
        player["cyclops_second_eye_active"] = int(self.second_eye_active)
        player["cyclops_safety_net_used"] = int(self.safety_net_used)
        if not self.mode_finishing and not self.mode_done:
            if self.second_eye_active:
                self._update_second_eye_status()
            else:
                self.machine.events.post(
                    "update_mode_status",
                    mode_status_title="FLIPS LEFT",
                    mode_status_value=self.flips_remaining,
                )

    def _show_mode_message(self, title, subtitle="", value="", seconds="", reminder=False):
        if self.first_eye_hold_active:
            return
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )

    def _show_mode_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def _inactive(self):
        return self.mode_done or self.mode_finishing
