from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin
from mpf.core.delays import DelayManager

#possible bug when 2 targets hit, flash doesn't move

"""
    "title": "SANDMAN",
    "intro_1": "Shoot the flashing drop target.",
    "intro_2": "Hit drops in sequence for big points.",
    "intro_3": "5 in a row for Super Jackpot.",
    "summary_title_complete": "SANDMAN DEFEATED",
    "summary_title_failed": "SANDMAN ESCAPED",
    "stat_1_label": "DROPS HIT",
    "stat_1_var": "sandman_total_drops",
    "stat_2_label": "BEST RUNS",
    "stat_2_var": "sandman_best_run",
    "points_var": "active_mode_points",
    "state_var": "sandman_state",
"""
class Sandman(CaseFileMixin, Mode):

    BANK_TARGETS = [1, 2, 3, 4, 5]
    MAX_BANKS = 3
    MOVE_INTERVAL_MS = 3000
    RESET_SETTLE_MS = 500

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)

        self.current_flash = 1
        self.first_target = 0
        self.down_targets = set()
        self.banks_completed = 0
        self.hit_order = []
        self.direction = 0 # 0 = L to R, 1 = R to L
        self.active_mode_points = 0
        self.sandman_best_run = 0
        self.flash_hits = 0
        self.shot_assist = False
        self.mode_done = False
        self.awarded_run_jackpots = set()

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("sandman")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA SANDMAN BANK AVAILABLE"),
            ("bigger_jackpots", "FLASHING TARGETS SCORE MORE"),
            ("more_time", "TARGET SHIFT SLOWED"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST TARGET SPOTTED"),
        ])

        for target in self.BANK_TARGETS:
            self.add_mode_event_handler(
                f"sandman_drop_{target}_hit",
                self.drop_hit,
                target=target
            )
        
        #self.start_bank()
        self.add_mode_event_handler("sandman_start_bank", self.start_bank)
        self.add_mode_event_handler("sandman_rubber_hit", self.schedule_next_shift)  #reset current flash timer      

        self.update_player_vars()
        self._show_message("SANDMAN", "HIT THE FLASHING DROP")
        self.machine.events.post("sandman_startup_complete")

    def mode_stop(self, **kwargs):
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _show_message(self, title, subtitle="", value="", seconds="", event="show_mode_message"):
        self.machine.events.post(
            event,
            title=title,
            subtitle=subtitle,
            value=value,
            seconds=seconds,
        )

    def _apply_case_file_bonuses(self):
        self.case_file_bigger_jackpots = False

        if self.has_case_file("more_jackpots"):
            self.MAX_BANKS += 1

        if self.has_case_file("bigger_jackpots"):
            self.case_file_bigger_jackpots = True

        if self.has_case_file("more_time"):
            self.MOVE_INTERVAL_MS += 1500

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.shot_assist = True

    def start_bank(self, **kwargs):
        if self.mode_done:
            return

        self.down_targets = set()
        self.hit_order = []
        self.current_flash = 1

        # Use the MPF drop target bank reset event instead of only pulsing the
        # reset coil. This keeps the physical bank and MPF device state in sync,
        # and is more reliable when the intro is skipped quickly.
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

        self.delay.remove("sandman_after_bank_reset")
        self.delay.add(
            name="sandman_after_bank_reset",
            ms=self.RESET_SETTLE_MS,
            callback=self.after_bank_reset
        )

    def after_bank_reset(self):
        if self.mode_done:
            return

        self.light_current_flash()
        self._show_message("SHIFTING SANDS", f"HIT DROP {self.current_flash}", seconds=int(self.MOVE_INTERVAL_MS / 1000), event="show_mode_countdown")
        if self.first_target == 1:        
            self.schedule_next_shift()


    def schedule_next_shift(self, **kwargs):
        if self.mode_done:
            return

        self.delay.remove("sandman_shift")
        self.delay.add(
            name="sandman_shift",
            ms=self.MOVE_INTERVAL_MS,
            callback=self.shift_flash
        )

    def shift_flash(self):
        if self.mode_done:
            return

        if self.shot_assist == True:
            self.shot_assist = False
            self.drop_hit(target=self.current_flash)
            return
        
        self.hit_order = []

        if self.current_flash not in self.down_targets:
            self.down_targets.add(self.current_flash)

        target = self.current_flash
        if self.direction == 1:
            target = 6 - target

        self.machine.coils[f"c_right_bank_drop_{target}"].pulse()

        next_target = self.find_next_standing_target(self.current_flash)

        self.info_log(f"direction:{self.direction} next target {next_target}")

        if next_target is None:
            self.complete_bank()
            return

        self.current_flash = next_target
        self.light_current_flash()
        self.schedule_next_shift()


    def light_current_flash(self):
        if self.direction == 1:
            self.machine.events.post(f"sandman_flash_{(6-self.current_flash)}")
        else:
            self.machine.events.post(f"sandman_flash_{self.current_flash}")
        

    def find_next_standing_target(self, current):
        ordered = self.BANK_TARGETS[current:]

        for target in ordered:
            if target not in self.down_targets:
                return target

        return None
        

    def drop_hit(self, target, **kwargs):
        if self.mode_done:
            return

        if self.direction == 1:
            target = 6 - target

        if target in self.down_targets:
            return

        self.down_targets.add(target)

        if target == self.current_flash:
            self.hit_order.append(target)
            self.flash_hits += 1
            self._show_message("FLASHING HIT!", f"RUN: {len(self.hit_order)}", event="show_mode_jackpot")
            self.machine.events.post("sandman_flashing_hit")
            if getattr(self, "case_file_bigger_jackpots", False):
                self.machine.game.player["score"] += 25000
                self.machine.game.player["active_mode_points"] += 25000
                self.machine.events.post("sandman_case_file_bonus_score")
        else:
            self._show_message("SANDMAN SHIFTED", "HIT THE FLASHING TARGET")
            self.machine.events.post("sandman_regular_hit")

        self.award_points()
        self.update_player_vars()

        if target == self.current_flash:
            next_target = self.find_next_standing_target(self.current_flash)
            if next_target is not None:
                self.first_target = 1
                self.current_flash = next_target
                self.light_current_flash()
                self.schedule_next_shift()

        #first target down, start timer
        if self.first_target == 0:
            self.first_target = 1
            self.schedule_next_shift()

        if len(self.down_targets) >= 5:
            self.complete_bank()
            return


    def award_points(self):

        if self.flash_hits == 5 and "5_flash" not in self.awarded_run_jackpots:
            self.awarded_run_jackpots.add("5_flash")
            self._show_message("SANDMAN JACKPOT", "5 FLASHING HITS", value=750000, event="show_mode_jackpot")
            self.machine.events.post("sandman_5_flashing_jackpot")

        if self.flash_hits == 10 and "10_flash" not in self.awarded_run_jackpots:
            self.awarded_run_jackpots.add("10_flash")
            self._show_message("SANDMAN JACKPOT", "10 FLASHING HITS", value=1500000, event="show_mode_jackpot")
            self.machine.events.post("sandman_10_flashing_jackpot")

        if self.hit_order == [1, 2, 3, 4, 5]:
            self.machine.events.post("sandman_5_in_a_row_jackpot")
            if self.sandman_best_run < 5: self.sandman_best_run = 5
            
        if self.hit_order == [1, 2, 3, 4]:
            self.machine.events.post("sandman_4_in_a_row_jackpot")
            if self.sandman_best_run < 4: self.sandman_best_run = 4
        if self.hit_order == [2, 3, 4, 5]:
            self.machine.events.post("sandman_4_in_a_row_jackpot")
            if self.sandman_best_run < 4: self.sandman_best_run = 4
           
        if self.hit_order == [1, 2, 3]:
            self.machine.events.post("sandman_3_in_a_row_jackpot")
            if self.sandman_best_run < 3: self.sandman_best_run = 3
        if self.hit_order == [2, 3, 4]:
            self.machine.events.post("sandman_3_in_a_row_jackpot")
            if self.sandman_best_run < 3: self.sandman_best_run = 3
        if self.hit_order == [3, 4, 5]:
            self.machine.events.post("sandman_3_in_a_row_jackpot")
            if self.sandman_best_run < 3: self.sandman_best_run = 3

        if self.hit_order == [1, 2]:
            self.machine.events.post("sandman_2_in_a_row_jackpot")
            if self.sandman_best_run < 2: self.sandman_best_run = 2
        if self.hit_order == [2, 3]:
            self.machine.events.post("sandman_2_in_a_row_jackpot")
            if self.sandman_best_run < 2: self.sandman_best_run = 2
        if self.hit_order == [3, 4]:
            self.machine.events.post("sandman_2_in_a_row_jackpot")
            if self.sandman_best_run < 2: self.sandman_best_run = 2
        if self.hit_order == [4, 5]:
            self.machine.events.post("sandman_2_in_a_row_jackpot")
            if self.sandman_best_run < 2: self.sandman_best_run = 2


    def complete_bank(self):
        if self.mode_done:
            return

        self.delay.remove("sandman_shift")
        self.direction = 1 - self.direction

        self.banks_completed += 1
        self._show_message("BANK CLEARED", f"{self.banks_completed} OF {self.MAX_BANKS}", event="show_mode_jackpot")
        self.machine.events.post("sandman_bank_complete")

        self.update_player_vars()

        if self.banks_completed >= self.MAX_BANKS:
            self.mode_done = True
            self._show_message("SANDMAN DEFEATED", "MODE COMPLETE", event="show_mode_jackpot")
            self.machine.events.post("sandman_mode_complete")
            self.machine.game.player["sandman_state"] = 2
            self.machine.events.post("reset_5bank_delayed")
            return

        self.delay.add(
            ms=750,
            callback=self.start_bank
        )

    def update_player_vars(self):
        player = self.machine.game.player

        player["sandman_banks_completed"] = self.banks_completed
        player["sandman_total_drops"] = self.flash_hits
        player["sandman_best_run"] = self.sandman_best_run
    

