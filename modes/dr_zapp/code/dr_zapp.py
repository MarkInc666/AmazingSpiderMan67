import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class DrZapp(CaseFileMixin, Mode):
    MODE_KEY = "dr_zapp"
    DISPLAY_NAME = "Doctor Zapp"

    BANK_SCORE = 100_000
    BIGGER_BANK_SCORE = 150_000
    TARGET_SCORE = 50_000
    BIGGER_TARGET_SCORE = 75_000
    SPIN_SCORE = 50_000
    BIGGER_SPIN_SCORE = 75_000

    FLASHES_TO_DEFEAT = 25
    MORE_JACKPOTS_SECONDS = 10

    UPPER_TARGETS = ("left", "center", "right")

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=1)
        self.delay = DelayManager(self.machine)
        self.case_files = self.get_case_file_bonuses()

        self.mode_done = False
        self.phase = "qualify"
        self.left_bank_qualified = False
        self.right_bank_qualified = False
        self.roof_open = False
        self.first_upper_entry_seen = False
        self.shot_assist_used = False
        self.collected_upper_targets = set()
        self.camera_flashes = 0
        self.spinner_spins = 0
        self.mode_points = 0
        self.seconds_left = 0

        player = self.machine.game.player
        player["dr_zapp_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "10 SECOND BONUS SPINS"),
            ("bigger_jackpots", "150K BANKS / 75K TARGETS AND SPINS"),
            ("more_time", "15 SECOND SAVE ON FIRST ROOF ENTRY"),
            ("safety_net", "10 SECOND SAVE AT MODE START"),
            ("shot_assist", "FIRST UPPER TARGET AWARDS ANOTHER"),
        ])

        self.add_mode_event_handler("dr_zapp_left_bank_hit", self._bank_hit, bank="left")
        self.add_mode_event_handler("dr_zapp_right_bank_hit", self._bank_hit, bank="right")
        self.add_mode_event_handler("dr_zapp_upper_target_left", self._upper_target_hit, target="left")
        self.add_mode_event_handler("dr_zapp_upper_target_center", self._upper_target_hit, target="center")
        self.add_mode_event_handler("dr_zapp_upper_target_right", self._upper_target_hit, target="right")
        self.add_mode_event_handler("dr_zapp_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("dr_zapp_upper_entered", self._upper_entered)
        self.add_mode_event_handler("dr_zapp_complete_request", self._finish_mode)
        self.add_mode_event_handler("ball_ending", self._ball_ending)

        self.machine.events.post("dr_zapp_clear_all")
        self.machine.events.post("dr_zapp_qualification_started")
        self.machine.events.post("rooftop_diverter_close")
        if self.has_case_file("safety_net"):
            self.machine.events.post("dr_zapp_enable_start_safety_net")
        self._show_status("HIT EACH DROP BANK")

    def mode_stop(self, **kwargs):
        self.delay.remove("dr_zapp_bonus_tick")
        self.machine.events.post("dr_zapp_clear_all")
        self.machine.events.post("dr_zapp_disable_start_safety_net")
        self.machine.events.post("dr_zapp_disable_upper_entry_save")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        self.machine.events.post("rooftop_diverter_close")
        # Catch-all: no delayed villain/wizard callback may survive into bonus.
        self.delay.clear()
        super().mode_stop(**kwargs)

    def _bank_hit(self, bank, **kwargs):
        if self.mode_done or self.phase != "qualify":
            return

        if bank == "left":
            if self.left_bank_qualified:
                return
            self.left_bank_qualified = True
        else:
            if self.right_bank_qualified:
                return
            self.right_bank_qualified = True

        value = self._bank_value()
        self._score(value)
        self.machine.events.post(f"dr_zapp_{bank}_bank_qualified", value=value)
        self._show_message("BANK QUALIFIED", f"{bank.upper()} BANK", value)

        if self.left_bank_qualified and self.right_bank_qualified:
            self._open_roof()
        else:
            self._show_status("HIT EACH DROP BANK")
        self._sync_vars()

    def _open_roof(self):
        self.phase = "roof"
        self.roof_open = True
        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("dr_zapp_roof_open")
        self._show_message("ROOFTOP ACCESS OPEN", "SPIN FOR 25 CAMERA FLASHES")
        self._show_status("25 CAMERA FLASHES", self._flash_status())
        self._sync_vars()

    def _upper_entered(self, **kwargs):
        if self.mode_done or not self.roof_open or self.first_upper_entry_seen:
            return
        self.first_upper_entry_seen = True
        if self.has_case_file("more_time"):
            self.machine.events.post("dr_zapp_enable_upper_entry_save")
        self._sync_vars()

    def _upper_target_hit(self, target, **kwargs):
        if self.mode_done or self.phase not in ("roof", "bonus"):
            return
        if self.phase == "bonus" or target in self.collected_upper_targets:
            return

        self._collect_upper_target(target, assisted=False)

        if self.has_case_file("shot_assist") and not self.shot_assist_used:
            remaining = [name for name in self.UPPER_TARGETS if name not in self.collected_upper_targets]
            if remaining:
                self.shot_assist_used = True
                assisted_target = random.choice(remaining)
                self._collect_upper_target(assisted_target, assisted=True)
                self.machine.events.post("dr_zapp_case_file_shot_assist_used", target=assisted_target)

        self._show_status("25 CAMERA FLASHES", self._flash_status())
        self._sync_vars()

    def _collect_upper_target(self, target, assisted=False):
        self.collected_upper_targets.add(target)
        value = self._target_value()
        self._score(value)
        event = "dr_zapp_assisted_target_collected" if assisted else "dr_zapp_upper_target_collected"
        self.machine.events.post(event, target=target, value=value)
        self.machine.events.post(f"dr_zapp_{target}_target_solid")
        title = "EXTRA FLASH BOOST" if assisted else "FLASH BOOST +1"
        self._show_message(title, f"{target.upper()} TARGET", value)

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.phase not in ("roof", "bonus"):
            return

        value = self._spin_value()
        self._score(value)
        self.spinner_spins += 1

        if self.phase == "bonus":
            self.machine.events.post("dr_zapp_bonus_spin_scored", value=value, spins=self.spinner_spins)
            self._show_message("BONUS SPIN", "DOCTOR ZAPP DEFEATED", value)
            self._show_status("BONUS SPINS", self.seconds_left)
            self._sync_vars()
            return

        flashes_added = 1 + len(self.collected_upper_targets)
        self.camera_flashes += flashes_added
        self.machine.events.post(
            "dr_zapp_camera_flashes_added",
            flashes_added=flashes_added,
            camera_flashes=self.camera_flashes,
            value=value,
        )
        self._show_status("25 CAMERA FLASHES", self._flash_status())
        self._sync_vars()

        if self.camera_flashes >= self.FLASHES_TO_DEFEAT:
            self._defeated()

    def _defeated(self):
        self.machine.events.post("dr_zapp_defeated")
        self._show_message("DOCTOR ZAPP DEFEATED", "CAMERA FLASHES COMPLETE")

        if self.has_case_file("more_jackpots"):
            self.phase = "bonus"
            self.seconds_left = self.MORE_JACKPOTS_SECONDS
            self.machine.events.post("dr_zapp_bonus_started")
            self._show_message("BONUS SPINS", "10 SECONDS")
            self._show_status("BONUS SPINS", self.seconds_left)
            self._schedule_bonus_tick()
        else:
            self._finish_mode()

    def _schedule_bonus_tick(self):
        self.delay.remove("dr_zapp_bonus_tick")
        self.delay.add(name="dr_zapp_bonus_tick", ms=1000, callback=self._bonus_tick)

    def _bonus_tick(self):
        if self.mode_done or self.phase != "bonus":
            return
        self.seconds_left -= 1
        self._sync_vars()
        if self.seconds_left <= 0:
            self._finish_mode()
            return
        self._show_status("BONUS SPINS", self.seconds_left)
        self._schedule_bonus_tick()

    def _finish_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("dr_zapp_bonus_tick")
        self.seconds_left = 0
        player = self.machine.game.player
        player["dr_zapp_state"] = 2
        self._sync_vars()

        # Base mode owns the timer so the upper-flipper lockout survives this
        # villain mode tearing down and the summary beginning immediately.
        self.machine.events.post("dr_zapp_upper_flipper_lockout")
        self.machine.events.post("dr_zapp_mode_complete")

    def _ball_ending(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("dr_zapp_bonus_tick")
        self._sync_vars()

    def _bank_value(self):
        return self.BIGGER_BANK_SCORE if self.has_case_file("bigger_jackpots") else self.BANK_SCORE

    def _target_value(self):
        return self.BIGGER_TARGET_SCORE if self.has_case_file("bigger_jackpots") else self.TARGET_SCORE

    def _spin_value(self):
        return self.BIGGER_SPIN_SCORE if self.has_case_file("bigger_jackpots") else self.SPIN_SCORE

    def _flash_status(self):
        return f"{min(self.camera_flashes, self.FLASHES_TO_DEFEAT)} / {self.FLASHES_TO_DEFEAT}"

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        self._sync_vars()

    def _sync_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["dr_zapp_camera_flashes"] = self.camera_flashes
        player["dr_zapp_spinner_spins"] = self.spinner_spins
        player["dr_zapp_upper_targets"] = len(self.collected_upper_targets)
        player["dr_zapp_seconds_left"] = self.seconds_left
        player["dr_zapp_phase"] = self.phase

    def _show_status(self, title, value=""):
        self.machine.events.post(
            "update_mode_status",
            mode_status_title=title,
            mode_status_value=value,
        )

    def _show_message(self, title, subtitle="", value=""):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
        )
