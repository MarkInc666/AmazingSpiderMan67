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

        self.current_item = None

        self.add_mode_event_handler("carousel_item_highlighted", self.my_carousel_item_highlighted)
       # self.add_mode_event_handler("carousel_item_selected", self.my_carousel_item_selected)
        self.add_mode_event_handler(
            "flipper_cancel",
            self.my_carousel_item_selected
        )


    def my_carousel_item_highlighted(self, item=None, **kwargs):
        if not item:
            return

        self.current_item = item

        played_var = f"{item}_played"
        played_state = self.machine.game.player[played_var]

        if played_state == 1:
            self.machine.events.post(f"villain_select_{item}_played")
        else:
            self.machine.events.post(f"villain_select_{item}_available")
            return

    def my_carousel_item_selected(self, **kwargs):
        if not self.current_item:
            return

        played_var = f"{self.current_item}_played"
        played_state = self.machine.game.player[played_var]

        #debugging
        self.info_log(f"current villain played variable: {played_var}")
        self.info_log(f"current villain played state: {played_state}")

        if played_state == 1:
            self.machine.events.post("villain_select_already_played")
            return

        self.start_villain(self.current_item)


    def start_villain(self, item):
        player = self.machine.game.player

        player[f"{item}_played"] = 1
        player["current_villain"] = item
        player["villain_mode_running"] = 1
        player["villain_mode_running_name"] = item

        player["villain_start_ready"] = 0
        player["villain_locate_spins"] = 0
        player["saucer_1_select_ready"] = 0
        player["saucer_2_select_ready"] = 0
        player["saucer_3_select_ready"] = 0

        self.machine.events.post("villain_started_set")
        self.machine.events.post(self.VILLAINS[item])
        self.machine.events.post("villain_carousel_accept_selection")
        self.machine.events.post("stop_carousel_select")
        