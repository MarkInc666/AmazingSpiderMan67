from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
CYCLOPS - EYE OF DOOM

Limited-flips monster mode.
- Center web target is the Cyclops Eye.
- Player starts with 20 flips, or 30 with More Time.
- Each main flipper button press spends 1 flip.
- Each drop target switch hit adds 3 flips.
- Drop banks reset when the physical bank-down event fires.
- Shot Assist: first drop in a bank knocks down the rest of that bank.
- Eye Jackpot = remaining flips * 100K, capped at 2M or 3M with Bigger Jackpot.
- More Jackpots gives a second Eye Jackpot opportunity.
- Safety Net restores 5 flips once if flips hit 0.
"""


class Cyclops(CaseFileMixin, Mode):
    MODE_KEY = "cyclops"
    DISPLAY_NAME = "Cyclops"

    STARTING_FLIPS = 20
    MORE_TIME_FLIPS = 30
    DROP_FLIP_AWARD = 3
    SAFETY_NET_FLIPS = 5
    JACKPOT_PER_FLIP = 100_000
    JACKPOT_CAP = 2_000_000
    BIGGER_JACKPOT_CAP = 3_000_000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_done = False
        self.eye_jackpots = 0
        self.best_jackpot = 0
        self.mode_points = 0
        self.flips_used = 0
        self.drops_hit = 0
        self.bank_assist_used = {"left": False, "right": False}
        self.safety_net_used = False

        self.case_files = self.get_case_file_bonuses()
        self.starting_flips = self.MORE_TIME_FLIPS if self.has_case_file("more_time") else self.STARTING_FLIPS
        self.flips_remaining = self.starting_flips
        self.jackpot_cap = self.BIGGER_JACKPOT_CAP if self.has_case_file("bigger_jackpots") else self.JACKPOT_CAP
        self.max_eye_jackpots = 2 if self.has_case_file("more_jackpots") else 1

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "SECOND EYE JACKPOT AVAILABLE"),
            ("bigger_jackpots", "EYE JACKPOT CAP 3M"),
            ("more_time", "START WITH 30 FLIPS"),
            ("safety_net", "5 FLIP SAFETY NET ACTIVE"),
            ("shot_assist", "DROP BANK ASSIST ACTIVE"),
        ])

        self.add_mode_event_handler("s_left_flipper_active", self._flipper_pressed)
        self.add_mode_event_handler("s_right_flipper_active", self._flipper_pressed)

        self.add_mode_event_handler("cyclops_eye_hit", self._eye_hit)
        self.add_mode_event_handler("cyclops_left_drop_1_hit", self._drop_hit, bank="left", number=1)
        self.add_mode_event_handler("cyclops_left_drop_2_hit", self._drop_hit, bank="left", number=2)
        self.add_mode_event_handler("cyclops_left_drop_3_hit", self._drop_hit, bank="left", number=3)
        self.add_mode_event_handler("cyclops_right_drop_1_hit", self._drop_hit, bank="right", number=1)
        self.add_mode_event_handler("cyclops_right_drop_2_hit", self._drop_hit, bank="right", number=2)
        self.add_mode_event_handler("cyclops_right_drop_3_hit", self._drop_hit, bank="right", number=3)
        self.add_mode_event_handler("cyclops_right_drop_4_hit", self._drop_hit, bank="right", number=4)
        self.add_mode_event_handler("cyclops_right_drop_5_hit", self._drop_hit, bank="right", number=5)
        self.add_mode_event_handler("cyclops_fail_request", self._fail_mode)
        self.add_mode_event_handler("cyclops_complete_request", self._complete_mode)

        self.machine.events.post("cyclops_mode_started")
        self.machine.events.post("cyclops_eye_lit")
        self._show_mode_message("HIT THE EYE", f"{self.flips_remaining} FLIPS")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")


    def _show_mode_message(self, title, subtitle="", value="", seconds=""):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
        )

    def _show_mode_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )

    def mode_stop(self, **kwargs):
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _flipper_pressed(self, **kwargs):
        if self.mode_done:
            return

        self.flips_remaining -= 1
        self.flips_used += 1
        self.machine.events.post("cyclops_flip_used", flips_remaining=self.flips_remaining)
        if self.flips_remaining > 0 and (self.flips_remaining <= 5 or self.flips_remaining % 5 == 0):
            self._show_mode_message("FLIPS REMAINING", str(self.flips_remaining))

        if self.flips_remaining <= 0:
            if self.has_case_file("safety_net") and not self.safety_net_used:
                self.safety_net_used = True
                self.flips_remaining = self.SAFETY_NET_FLIPS
                self.machine.events.post("cyclops_safety_net_used", flips_remaining=self.flips_remaining)
                self._show_mode_message("SAFETY NET", "5 FLIPS RESTORED")
            else:
                self.flips_remaining = 0
                self._sync_vars()
                self._fail_mode()
                return

        self._sync_vars()

    def _drop_hit(self, bank, number, **kwargs):
        if self.mode_done:
            return

        self.drops_hit += 1
        self.flips_remaining += self.DROP_FLIP_AWARD
        self.machine.events.post(
            "cyclops_flips_added",
            flips_added=self.DROP_FLIP_AWARD,
            flips_remaining=self.flips_remaining,
        )
        self.machine.events.post("cyclops_drop_hit", bank=bank, number=number, flips_remaining=self.flips_remaining)
        self._show_mode_message("+3 FLIPS", f"{self.flips_remaining} FLIPS LEFT")

        if self.has_case_file("shot_assist") and not self.bank_assist_used[bank]:
            self.bank_assist_used[bank] = True
            self.machine.events.post(f"cyclops_shot_assist_{bank}_bank")
            self.machine.events.post("cyclops_shot_assist_bank_dropped", bank=bank, flips_remaining=self.flips_remaining)
            self._show_mode_message("SHOT ASSIST", f"{bank.upper()} BANK DROPPED")

        self._sync_vars()

    def _eye_hit(self, **kwargs):
        if self.mode_done:
            return

        jackpot = self._current_jackpot_value()
        self._award_score(jackpot)
        self.eye_jackpots += 1

        if jackpot > self.best_jackpot:
            self.best_jackpot = jackpot

        player = self.machine.game.player
        player["cyclops_last_jackpot"] = jackpot
        self.machine.events.post(
            "cyclops_eye_jackpot_awarded",
            jackpot=jackpot,
            eye_jackpots=self.eye_jackpots,
            flips_remaining=self.flips_remaining,
        )
        self._show_mode_jackpot("CYCLOPS JACKPOT", jackpot, f"{self.flips_remaining} FLIPS")

        if self.eye_jackpots >= self.max_eye_jackpots:
            self._complete_mode()
        else:
            self.machine.events.post("cyclops_second_eye_lit")
            self._show_mode_message("SECOND EYE JACKPOT", "HIT CENTER WEB AGAIN")
            self._sync_vars()

    def _current_jackpot_value(self):
        return min(self.flips_remaining * self.JACKPOT_PER_FLIP, self.jackpot_cap)

    def _award_score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars()
        self.machine.events.post("cyclops_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars()
        self.machine.events.post("cyclops_mode_complete")

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["cyclops_flips_remaining"] = self.flips_remaining
        player["cyclops_flips_used"] = self.flips_used
        player["cyclops_drops_hit"] = self.drops_hit
        player["cyclops_eye_jackpots"] = self.eye_jackpots
        player["cyclops_best_jackpot"] = self.best_jackpot
        player["cyclops_jackpot_value"] = self._current_jackpot_value()
        player["cyclops_jackpot_cap"] = self.jackpot_cap
        player["cyclops_safety_net_used"] = 1 if self.safety_net_used else 0
