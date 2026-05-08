from mpf.core.mode import Mode


class RhinoBash(Mode):

    MAX_JACKPOTS = 5

    BASE_VALUES = [50000, 100000, 150000, 200000, 250000]
    BERSERK_TIMES_MS = [8000, 7000, 6000, 5000, 4000]

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
        self.pops = 0
        self.jackpots = 0
        self.jackpot_base = self.BASE_VALUES[0]
        self.jackpot_value = self.jackpot_base
        self.add_value = self.STAGE_ADD_VALUES[1]
        self.berserk_running = False
        self.mode_done = False

        self.add_mode_event_handler("rhino_start", self.start)
        self.add_mode_event_handler("rhino_pop_hit", self.pop_hit)
        self.add_mode_event_handler("rhino_smash_hit", self.smash_hit)
        self.add_mode_event_handler("rhino_jackpot_collect_request", self.collect_jackpot)

        self.update_player_vars()

    def start(self, **kwargs):
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
        self.jackpot_value += self.add_value

        self.update_player_vars()

    def collect_jackpot(self, **kwargs):
        if self.mode_done:
            return

        self.stop_berserk()

        self.award_score(self.jackpot_value)
        self.jackpots += 1

        self.machine.game.player["rhino_last_jackpot"] = self.jackpot_value
        self.machine.events.post("rhino_jackpot_collected")

        if self.jackpots >= self.MAX_JACKPOTS:
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
        self.post_rage_show()
        self.update_player_vars()

    def post_rage_show(self):
        self.machine.events.post(f"rhino_show_rage_{self.rage_stage}")

    def start_berserk(self):
        self.berserk_running = True
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
        return self.BERSERK_TIMES_MS[index]

    def crash(self):
        if self.mode_done:
            return

        self.berserk_running = False

        self.jackpot_value = self.jackpot_base
        self.rage_stage = 2
        self.pops = 2
        self.add_value = self.STAGE_ADD_VALUES[2]

        self.machine.events.post("rhino_berserk_stopped")
        self.machine.events.post("rhino_crashed")
        self.post_rage_show()

        self.update_player_vars()

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