from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class RhinoBash(CaseFileMixin, Mode):
    """Build Rhino's rage with pops, build the pending jackpot with other shots."""

    MAX_JACKPOTS_DEFAULT = 5
    BASE_VALUES = [100000, 150000, 200000, 250000, 300000, 350000]
    BERSERK_TIME_MS = 10000

    # Cumulative pop totals required to reach each stage in every cycle.
    STAGE_POPS = {
        1: 0,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
    }

    STAGE_ADD_VALUES = {
        1: 5000,
        2: 10000,
        3: 25000,
        4: 50000,
        5: 100000,
    }

    POP_SCORE = 10000
    SMASH_SCORE = 25000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.rage_stage = 1
        self.rhino_best_rage_stage = 1
        self.rhino_best_jackpot_value = 0
        self.active_mode_points = 0

        self.pops = 0
        self.jackpots = 0
        self.bonus_mode_time = 0
        self.shot_assist_available = False
        self.max_jackpots = self.MAX_JACKPOTS_DEFAULT
        self.bigger_jackpots = False
        self.jackpot_base = 0
        self.jackpot_value = 0
        self.add_value = self.STAGE_ADD_VALUES[1]
        self.berserk_running = False
        self.mode_done = False

        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self._set_jackpot_for_cycle()
        self.publish_case_file_bonus_events("rhino")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA RHINO JACKPOT AVAILABLE"),
            ("bigger_jackpots", "+100K TO EVERY RHINO JACKPOT"),
            ("more_time", "BERSERK TIMER EXTENDED 5s"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "ONE BERSERK CRASH SAVE"),
        ])

        self.add_mode_event_handler("rhino_start", self.start_rh)
        self.add_mode_event_handler("rhino_pop_hit", self.pop_hit)
        self.add_mode_event_handler("rhino_smash_hit", self.smash_hit)
        self.add_mode_event_handler("rhino_jackpot_collect_request", self.collect_jackpot)

        self.update_player_vars()
        self._show_message("RHINO BASH", "POPS BUILD RAGE", value=self.jackpot_value, reminder=True)
        self.machine.events.post("rhino_startup_complete")

    def mode_stop(self, **kwargs):
        self.delay.remove("rhino_berserk_crash")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        self.machine.events.post("cancel_mode_message_reminder")
        super().mode_stop(**kwargs)

    def _show_message(self, title, subtitle="", value="", seconds="", event="show_mode_message", reminder=False):
        self.machine.events.post(
            event,
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )

    def _update_status(self):
        if self.mode_done or self.berserk_running:
            return
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="RAGE / JACKPOTS",
            mode_status_value=f"{self.rage_stage} / {self.jackpots} OF {self.max_jackpots}",
        )

    def _apply_case_file_bonuses(self):
        if self.has_case_file("more_jackpots"):
            self.max_jackpots = 6

        if self.has_case_file("bigger_jackpots"):
            self.bigger_jackpots = True

        if self.has_case_file("more_time"):
            self.bonus_mode_time = 5000

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.shot_assist_available = True

    def _set_jackpot_for_cycle(self):
        index = min(self.jackpots, len(self.BASE_VALUES) - 1)
        self.jackpot_base = self.BASE_VALUES[index]
        if self.bigger_jackpots:
            self.jackpot_base += 100000
        self.jackpot_value = self.jackpot_base

    def start_rh(self, **kwargs):
        del kwargs
        self.post_rage_show()
        self.update_player_vars()

    def pop_hit(self, **kwargs):
        del kwargs
        if self.mode_done:
            return

        self.award_score(self.POP_SCORE)
        self.active_mode_points += self.POP_SCORE
        self.pops += 1
        self.check_rage_stage()
        self.update_player_vars()

    def smash_hit(self, **kwargs):
        del kwargs
        if self.mode_done:
            return

        self.award_score(self.SMASH_SCORE)
        self.active_mode_points += self.SMASH_SCORE
        self.jackpot_value += self.add_value
        self._show_message("JACKPOT BUILDS", f"+{self.add_value:,} FROM SMASH", value=self.jackpot_value)
        self.update_player_vars()

    def collect_jackpot(self, **kwargs):
        del kwargs
        if self.mode_done:
            return

        self.stop_berserk()
        collected_value = self.jackpot_value
        self.award_score(collected_value)
        self.active_mode_points += collected_value
        self.jackpots += 1

        self.rhino_best_jackpot_value = max(self.rhino_best_jackpot_value, collected_value)
        self.machine.game.player["rhino_last_jackpot"] = collected_value
        self._show_message("RHINO JACKPOT", "BASH COLLECTED", value=collected_value, event="show_mode_jackpot")
        self.machine.events.post("rhino_jackpot_collected")

        if self.jackpots >= self.max_jackpots:
            self.complete_mode()
            return

        self._set_jackpot_for_cycle()
        self.reset_rage_cycle()
        self.update_player_vars()

    def check_rage_stage(self):
        for stage in (5, 4, 3, 2):
            if self.pops >= self.STAGE_POPS[stage] and self.rage_stage < stage:
                self.set_rage_stage(stage)
                if stage == 4:
                    self.machine.events.post("rhino_rage_callout")
                if stage == 5:
                    self.start_berserk()
                return

    def stage_5_required_pops(self):
        return self.STAGE_POPS[5]

    def set_rage_stage(self, stage):
        self.rage_stage = stage
        self.add_value = self.STAGE_ADD_VALUES[stage]
        self.rhino_best_rage_stage = max(self.rhino_best_rage_stage, stage)
        self._show_message("RAGE LEVEL UP", f"RAGE {stage}  +{self.add_value:,} PER HIT")
        self.post_rage_show()
        self.update_player_vars()

    def post_rage_show(self):
        self.machine.events.post(f"rhino_show_rage_{self.rage_stage}")

    def start_berserk(self):
        if self.berserk_running or self.mode_done:
            return
        self.berserk_running = True
        self._show_message(
            "BERSERK!",
            "COLLECT AT B ROLLOVER",
            value=self.jackpot_value,
            seconds=int(self.berserk_time_ms() / 1000),
            event="show_mode_countdown",
        )
        self.machine.events.post("rhino_berserk_started")
        self.delay.remove("rhino_berserk_crash")
        self.delay.add(name="rhino_berserk_crash", ms=self.berserk_time_ms(), callback=self.crash)

    def stop_berserk(self):
        if not self.berserk_running:
            return
        self.berserk_running = False
        self.delay.remove("rhino_berserk_crash")
        self.machine.events.post("rhino_berserk_stopped")
        self.machine.events.post("hide_mode_status")

    def berserk_time_ms(self):
        return self.BERSERK_TIME_MS + self.bonus_mode_time

    def crash(self):
        if self.mode_done:
            return

        if self.shot_assist_available:
            self.shot_assist_available = False
            self._show_message("SHOT ASSIST", "RHINO JACKPOT SAVED", value=self.jackpot_value)
            self.collect_jackpot()
            return

        self.berserk_running = False
        self.machine.events.post("rhino_berserk_stopped")
        self.machine.events.post("hide_mode_status")
        self._show_message("RHINO CRASHED", "BERSERK MISSED")
        self.machine.events.post("rhino_crashed")
        self.fail_mode()

    def reset_rage_cycle(self):
        self.rage_stage = 1
        self.pops = 0
        self.add_value = self.STAGE_ADD_VALUES[1]
        self.post_rage_show()

    def complete_mode(self):
        if self.mode_done:
            return
        self.mode_done = True
        self.stop_berserk()
        self._show_message("RHINO DEFEATED", "MODE COMPLETE", event="show_mode_jackpot")
        self.machine.game.player["rhino_state"] = 2
        self.machine.events.post("rhino_bash_complete")

    def fail_mode(self):
        if self.mode_done:
            return
        self.mode_done = True
        self.machine.game.player["rhino_state"] = 2
        self.update_player_vars()
        self.machine.events.post("rhino_bash_complete")

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
        player["rhino_best_rage_stage"] = self.rhino_best_rage_stage
        player["rhino_best_jackpot_value"] = self.rhino_best_jackpot_value
        player["active_mode_points"] = self.active_mode_points
        self._update_status()
