from mpf.core.mode import Mode


class QualifyVillainStart(Mode):

    VILLAINS = [
        ("doc_ock", "start_mode_doc_ock"),
        ("sandman", "start_mode_sandman"),
        ("vulture", "start_mode_vulture"),
        ("rhino", "start_mode_rhino_bash"),
        ("goblin", "start_mode_goblin"),
        ("mysterio", "start_mode_mysterio"),
        ("scorpion", "start_mode_scorpion"),
        ("electro", "start_mode_electro"),
        ("parafino", "start_mode_parafino"),
        ("lizard", "start_mode_lizard"),
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.add_mode_event_handler("start_current_villain", self.start_current_villain)
        self.add_mode_event_handler("advance_current_villain", self.advance_current_villain)
        self.add_mode_event_handler("reset_villain_locate", self.reset_villain_locate)
        self.add_mode_event_handler("clear_saucers", self.clear_saucers)


    def start_current_villain(self, **kwargs):
        player = self.machine.game.player

        self.info_log(f"current villain: {player["villain_current_name"]}")

        if player["kingpin_ready"] == 1:
            self.start_villain("kingpin", "start_mode_kingpin")
            return

        villain = self.find_next_unplayed_villain()

        if not villain:
            self.machine.events.post("all_villains_played")
            self.machine.events.post("kingpin_ready_set")
            self.machine.events.post("kingpin_wizard_ready")
            return

        name, start_event = villain
        self.start_villain(name, start_event)

    def find_next_unplayed_villain(self):
        start_index = self.machine.game.player["villain_current_index"]

        # Convert 1-based index to Python 0-based index.
        start_pos = max(0, start_index - 1)

        for offset in range(len(self.VILLAINS)):
            pos = (start_pos + offset) % len(self.VILLAINS)
            name, start_event = self.VILLAINS[pos]

            played_var = f"{name}_played"
            played_state = self.machine.game.player[played_var]

            if played_state == 0:
                self.machine.game.player["villain_current_index"] = pos + 1
                return name, start_event

        return None

    def start_villain(self, name, start_event):
        player = self.machine.game.player

        player[f"{name}_played"] = 1
        player["villain_current_name"] = name

        player["villain_mode_running"] = 1
        player["villain_mode_running_name"] = name

        player["villain_start_ready"] = 0
        player["villain_locate_spins"] = 0
        player["saucer_1_select_ready"] = 0
        player["saucer_2_select_ready"] = 0
        player["saucer_3_select_ready"] = 0
        
        self.machine.events.post("villain_started_set")
        self.machine.events.post(start_event)

    def advance_current_villain(self, **kwargs):
        current = self.machine.game.player["villain_current_index"]
        current += 1

        if current > len(self.VILLAINS):
            current = 1

        name_pos = max(0, current - 1)
        name, start_event = self.VILLAINS[name_pos]

        self.machine.game.player["villain_current_index"] = current
        self.machine.game.player["villain_current_name"] = name

        self.info_log(f"current villain: {self.machine.game.player["villain_current_name"]}")
    

    def reset_villain_locate(self, **kwargs):
        player = self.machine.game.player

        player["villain_mode_running"] = 0
        player["villain_start_ready"] = 0
        player["saucer_1_select_ready"] = 0
        player["saucer_2_select_ready"] = 0
        player["saucer_3_select_ready"] = 0

        self.advance_current_villain()

# called after villain mode starts have given the signal
# can wait until they are done their instruction intros
# multiballs may wait
    def clear_saucers(self, **kwargs):

        if self.machine.switch_controller.is_active(self.machine.switches["s_saucer_1"]):
            self.machine.events.post("kickout_saucer_1")

        if self.machine.switch_controller.is_active(self.machine.switches["s_saucer_2"]):
            self.machine.events.post("kickout_saucer_2")

        if self.machine.switch_controller.is_active(self.machine.switches["s_saucer_3"]):
            self.machine.events.post("kickout_saucer_3")

