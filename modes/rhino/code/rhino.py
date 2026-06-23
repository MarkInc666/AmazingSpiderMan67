from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin

"""
    "title": "RHINO BASH",
    "intro_1": "Build RAGE value with pop bumpers.",
    "intro_2": "Bash everything to add RAGE to Jackpot.",
    "intro_3": "Collect all 5 JACKPOTS at B rollover.",
    "summary_title_complete": "RHINO DEFEATED",
    "summary_title_failed": "RHINO ESCAPED",
    "stat_1_label": "BIGGEST JACKPOT",
    "stat_1_var": "rhino_best_jackpot_value",
    "stat_2_label": "BEST RAGE",
    "stat_2_var": "rhino_best_rage_stage",
    "points_var": "active_mode_points",
    "state_var": "rhino_state",
"""

class RhinoBash(CaseFileMixin, Mode):

    MAX_JACKPOTS_DEEFAULT = 5

    BASE_VALUES = [100000, 150000, 200000, 250000, 300000, 350000]
    BERSERK_TIMES_MS = [8000, 7000, 6000, 5000, 4000, 4000]

    STAGE_POPS = {
        1: 0,
        2: 2,
        3: 4,
        4: 7,
    }

    STAGE_ADD_VALUES = {
        1: 2000,
        2: 5000,
        3: 15000,
        4: 50000,
        5: 100000,
    }

    POP_SCORE = 10000
    SMASH_SCORE = 25000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.rage_stage = 1

        self.rhino_best_rage_stage = 0
        self.rhino_best_jackpot_value = 0
        self.active_mode_points = 0
    
        self.pops = 0
        self.jackpots = 0
        self.bonus_mode_time = 0
        self.shot_assist_available = False
        self.max_jackpots = self.MAX_JACKPOTS_DEEFAULT
        self.jackpot_base = self.BASE_VALUES[0]
        self.jackpot_value = self.jackpot_base
        self.add_value = self.STAGE_ADD_VALUES[1]
        self.berserk_running = False
        self.mode_done = False

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("rhino")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA RHINO JACKPOT AVAILABLE"),
            ("bigger_jackpots", "BIGGER RHINO JACKPOTS"),
            ("more_time", "RAGE TIMER EXTENDED 5s"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "RAGE CRASH SAVE AVAILABLE"),
        ])
        
        self.add_mode_event_handler("rhino_start", self.start_rh)
        self.add_mode_event_handler("rhino_pop_hit", self.pop_hit)
        self.add_mode_event_handler("rhino_smash_hit", self.smash_hit)
        self.add_mode_event_handler("rhino_jackpot_collect_request", self.collect_jackpot)

        self.update_player_vars()
        self._show_message("RHINO BASH", "POPS BUILD RAGE", value=self.jackpot_value)
        self.machine.events.post("rhino_startup_complete")


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
        if self.has_case_file("more_jackpots"):
            #one more jackpot
            self.max_jackpots += 1

        if self.has_case_file("bigger_jackpots"):
            #bigger jackpots
            self.jackpot_base += 100000

        if self.has_case_file("more_time"):
            #5 extra seconds before crash
            self.bonus_mode_time = 5000

        if self.has_case_file("safety_net"):
            #start 10 sec ball save
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            #allows one crash jackpot
            self.shot_assist_available = True


    def start_rh(self, **kwargs):
        self.post_rage_show()
        self.update_player_vars()

    def pop_hit(self, **kwargs):
        if self.mode_done:
            return

        self.award_score(self.POP_SCORE)
        self.pops += 1

        self.check_rage_stage()
        self.update_player_vars()

    def smash_hit(self, **kwargs):
        if self.mode_done:
            return

        self.award_score(self.SMASH_SCORE)
        self.active_mode_points += self.SMASH_SCORE
        self.jackpot_value += self.add_value
        self._show_message("JACKPOT BUILDS", f"+{self.add_value:,} FROM SMASH", value=self.jackpot_value)

        self.update_player_vars()

    def collect_jackpot(self, **kwargs):
        if self.mode_done:
            return

        self.stop_berserk()

        self.award_score(self.jackpot_value)
        self.jackpots += 1

        self.active_mode_points += self.jackpot_value

        if self.jackpot_value > self.rhino_best_jackpot_value:
            self.rhino_best_jackpot_value = self.jackpot_value

        self.machine.game.player["rhino_last_jackpot"] = self.jackpot_value
        self._show_message("RHINO JACKPOT", "BASH COLLECTED", value=self.jackpot_value, event="show_mode_jackpot")
        self.machine.events.post("rhino_jackpot_collected")

        if self.jackpots >= self.max_jackpots:
            self.complete_mode()
            return

        self.jackpot_base = self.BASE_VALUES[self.jackpots]
        self.jackpot_value = self.jackpot_base

        self.drop_rage_after_collect()
        self.update_player_vars()

    def check_rage_stage(self):
        required_stage_5 = self.stage_5_required_pops()

        if self.pops >= required_stage_5 and self.rage_stage < 5:
            self.set_rage_stage(5)
            self.start_berserk()
            return

        if self.pops >= 7 and self.rage_stage < 4:
            self.set_rage_stage(4)
            self.machine.events.post("rhino_rage_callout")
            return

        if self.pops >= 4 and self.rage_stage < 3:
            self.set_rage_stage(3)
            return

        if self.pops >= 2 and self.rage_stage < 2:
            self.set_rage_stage(2)

    def stage_5_required_pops(self):
        # 10, 11, 12, 13, 14 as jackpots progress
        return 10 + self.jackpots

    def set_rage_stage(self, stage):
        self.rage_stage = stage
        self.add_value = self.STAGE_ADD_VALUES[stage]
        self._show_message("RAGE LEVEL UP", f"RAGE {stage}  +{self.add_value:,} PER HIT")

        if self.rage_stage > self.rhino_best_rage_stage:
            self.rhino_best_rage_stage = self.rage_stage

        self.post_rage_show()
        self.update_player_vars()

    def post_rage_show(self):
        self.machine.events.post(f"rhino_show_rage_{self.rage_stage}")

    def start_berserk(self):
        self.berserk_running = True
        self._show_message("BERSERK!", "COLLECT AT B ROLLOVER", value=self.jackpot_value, seconds=int(self.berserk_time_ms() / 1000), event="show_mode_countdown")
        self.machine.events.post("rhino_berserk_started")

        self.delay.remove("rhino_berserk_crash")
        self.delay.add(
            name="rhino_berserk_crash",
            ms=self.berserk_time_ms(),
            callback=self.crash
        )

    def stop_berserk(self):
        if not self.berserk_running:
            return

        self.berserk_running = False
        self.delay.remove("rhino_berserk_crash")
        self.machine.events.post("rhino_berserk_stopped")

    def berserk_time_ms(self):
        index = min(self.jackpots, len(self.BERSERK_TIMES_MS) - 1)
        return (self.BERSERK_TIMES_MS[index] + self.bonus_mode_time)  #0 or 5000 ms

    def crash(self):
        if self.mode_done:
            return
        
        if self.shot_assist_available == True:
            #one free jackpot at timeout
            self.collect_jackpot()
            self.shot_assist_available = False
            return
        
        self.berserk_running = False

        self.jackpot_value = self.jackpot_base
        self.rage_stage = 2
        self.pops = 2
        self.add_value = self.STAGE_ADD_VALUES[2]

        self.machine.events.post("rhino_berserk_stopped")
        self._show_message("RHINO CRASHED", "RAGE RESET")
        self.machine.events.post("rhino_crashed")
        self.post_rage_show()
        self.update_player_vars()

        self.complete_mode()        

    def drop_rage_after_collect(self):
        if self.rage_stage >= 5:
            self.rage_stage = 4
            self.pops = 7
        elif self.rage_stage == 4:
            self.rage_stage = 3
            self.pops = 4
        elif self.rage_stage == 3:
            self.rage_stage = 2
            self.pops = 2
        elif self.rage_stage == 2:
            self.rage_stage = 1
            self.pops = 0
        else:
            self.rage_stage = 1
            self.pops = 0

        self.add_value = self.STAGE_ADD_VALUES[self.rage_stage]
        self.post_rage_show()

    def complete_mode(self):
        self.mode_done = True
        self.stop_berserk()
        self._show_message("RHINO DEFEATED", "MODE COMPLETE", event="show_mode_jackpot")
        self.machine.events.post("rhino_bash_complete")
        self.machine.game.player["rhino_state"] = 2

    def award_score(self, value):
        self.machine.game.player["score"] += value

    def update_player_vars(self):
        player = self.machine.game.player

        player["rhino_rage_stage"] = self.rage_stage
        player["rhino_pops"] = self.pops
        player["rhino_jackpots"] = self.jackpots
        player["rhino_jackpot_base"] = self.jackpot_base
        player["rhino_jackpot_value"] = self.jackpot_value
        player["rhino_add_value"] = self.add_value
        player["rhino_stage_5_required_pops"] = self.stage_5_required_pops()
        player["rhino_berserk_running"] = int(self.berserk_running)
        player["rhino_berserk_time_ms"] = self.berserk_time_ms()

        player["rhino_best_rage_stage"]=  self.rhino_best_rage_stage
        player["rhino_best_jackpot_value"] = self.rhino_best_jackpot_value
        player["active_mode_points"] = self.active_mode_points
        