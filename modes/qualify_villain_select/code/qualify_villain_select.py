from mpf.modes.carousel.code.carousel import Carousel


class QualifyVillainSelect(Carousel):

    VILLAINS = {
        "lizard": "start_mode_lizard",
        "rhino": "start_mode_rhino_bash",
        "sandman": "start_mode_sandman",
        "vulture": "start_mode_vulture",
        "electro": "start_mode_electro",
        "goblin": "start_mode_goblin",
        "mysterio": "start_mode_mysterio",
        "scorpion": "start_mode_scorpion",
        "doc_ock": "start_mode_doc_ock",
        "parafino": "start_mode_parafino",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.add_mode_event_handler("carousel_item_selected", self.carousel_item_selected)

        for vils in self.VILLAINS:
          played_var = f"{vils}_played"
          self.info_log(f"from player[]: {self.machine.game.player[played_var]}")
  

    def carousel_item_selected(self, item=None, **kwargs):
        if not item:
            return

        played_var = f"{item}_played"
        played_state = self.machine.game.player[played_var]

        self.info_log(f"current villain played variable: {played_var}")
        self.info_log(f"current villain played state: {played_state}")

        if played_state == 1:
            self.machine.events.post("villain_select_played")
            self.machine.events.post("carousel_selection_unlocked")
            return

        self.start_villain(item)


    def start_villain(self, item):
        player = self.machine.game.player

        player[f"{item}_played"] = 1
        player["current_villain"] = item
        player["villain_mode_running"] = 1
        player["villain_start_ready"] = 0

        self.machine.events.post("villain_started_set")
        self.machine.events.post("carousel_selection_locked")
        self.machine.events.post("stop_carousel_select")
        self.machine.events.post(self.VILLAINS[item])