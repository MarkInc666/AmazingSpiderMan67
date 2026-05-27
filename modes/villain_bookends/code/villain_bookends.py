from mpf.core.mode import Mode


class VillainBookends(Mode):

    INTRO_MS = 5000
    SUMMARY_MS = 6000

    VILLAINS = {
        "rhino": {
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
            "points_var": "rhino_mode_points",
            "completed_var": "rhino_completed",
        },

        "sandman": {
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
            "points_var": "sandman_mode_points",
            "completed_var": "sandman_completed",
        },

        "vulture": {
            "title": "VULTURE",
            "intro_1": "Get to the rooftop.",
            "intro_2": "Hit targets to raise spinner value.",
            "intro_3": "Spin fast before the targets decay.",
            "summary_title_complete": "VULTURE DEFEATED",
            "summary_title_failed": "VULTURE ESCAPED",
            "stat_1_label": "SPINS",
            "stat_1_var": "vulture_spins",
            "stat_2_label": "BONUS BANKED",
            "stat_2_var": "vulture_banked_bonus",
            "points_var": "vulture_mode_points",
            "completed_var": "vulture_completed",
        },

        "electro": {
            "title": "ELECTRO",
            "intro_1": "Follow the moving spark.",
            "intro_2": "Hit each charged shot before time runs out.",
            "intro_3": "The eigth spark awards Super Jackpot.",
            "summary_title_complete": "ELECTRO DEFEATED",
            "summary_title_failed": "ELECTRO ESCAPED",
            "stat_1_label": "BEST SPARK",
            "stat_1_var": "electro_best_spark",
            "stat_2_label": "SUPER JACKPOT",
            "stat_2_var": "electro_super_jackpot",
            "points_var": "electro_mode_points",
            "completed_var": "electro_completed",
        },

        "goblin": {
            "title": "GREEN GOBLIN",
            "intro_1": "Goblin is attacking from above.",
            "intro_2": "Lit shots decrease - Flashing shots increase.",
            "intro_3": "Collect Jackpots and Rest in the saucers.",
            "summary_title_complete": "GOBLIN DEFEATED",
            "summary_title_failed": "GOBLIN ESCAPED",
            "stat_1_label": "ATTACK TOTAL",
            "stat_1_var": "goblin_attacks_value", #points collected from flashing shots
            "stat_2_label": "BONUS BANKED",
            "stat_2_var": "goblin_bonus_banked",
            "points_var": "goblin_mode_points",
            "completed_var": "goblin_completed",
        },

        "mysterio": {
            "title": "MYSTERIO",
            "intro_1": "Find the real Mysterio.",
            "intro_2": "Shoot lit illusions to reveal him.",
            "intro_3": "Choose carefully for Jackpot.",
            "summary_title_complete": "MYSTERIO DEFEATED",
            "summary_title_failed": "MYSTERIO ESCAPED",
            "stat_1_label": "REVEALS USED",
            "stat_1_var": "mysterio_illusions_cleared",
            "stat_2_label": "JACKPOT",
            "stat_2_var": "mysterio_jackpot_value",
            "points_var": "mysterio_mode_points",
            "completed_var": "mysterio_completed",
        },

        "scorpion": {
            "title": "SCORPION",
            "intro_1": "Build Venom with the upper spinner.",
            "intro_2": "Exit left or right to set up your attack.",
            "intro_3": "Hit the single drop target for Jackpot.",
            "summary_title_complete": "SCORPION DEFEATED",
            "summary_title_failed": "SCORPION ESCAPED",
            "stat_1_label": "STINGS",
            "stat_1_var": "scorpion_stings",
            "stat_2_label": "BIGGEST JACKPOT",
            "stat_2_var": "scorpion_biggest_jackpot",
            "points_var": "scorpion_mode_points",
            "completed_var": "scorpion_completed",
        },

        "doc_ock": {
            "title": "DOC OCK",
            "intro_1": "Lock tentacle arms with rollovers.",
            "intro_2": "Shoot web targets for Jackpot.",
            "intro_3": "Spinner increases the multiplier.",
            "summary_title_complete": "DOC OCK DEFEATED",
            "summary_title_failed": "DOC OCK ESCAPED",
            "stat_1_label": "ARMS LOCKED",
            "stat_1_var": "doc_ock_max_arms_locked",
            "stat_2_label": "JACKPOTS",
            "stat_2_var": "doc_ock_jackpots",
            "points_var": "doc_ock_mode_points",
            "completed_var": "doc_ock_completed",
        },

        "lizard": {
            "title": "THE LIZARD MAN",
            "intro_1": "Create the antidote at the star rollover.",
            "intro_2": "Get it to Lizard Man lit web targets.",
            "intro_3": "Move fast before the value drains.",
            "summary_title_complete": "LIZARD MAN CURED",
            "summary_title_failed": "LIZARD MAN ESCAPED",
            "stat_1_label": "DELIVERIES",
            "stat_1_var": "lizard_deliveries_made",
            "stat_2_label": "BEST VALUE",
            "stat_2_var": "lizard_best_delivery_value",
            "points_var": "lizard_mode_points",
            "completed_var": "lizard_completed",
        },

        "parafino": {
            "title": "PARAFINO",
            "intro_1": "Parafino has sealed the city.",
            "intro_2": "Shoot pops and drops to break his control.",
            "intro_3": "Lit SAUCERS for JACKPOTS. Flashing add-a-ball.",
            "summary_title_complete": "PARAFINO DEFEATED",
            "summary_title_failed": "PARAFINO ESCAPED",
            "stat_1_label": "HEAT BLASTS",
            "stat_1_var": "parafino_heat_hits",
            "stat_2_label": "JACKPOTS",
            "stat_2_var": "parafino_total_jackpots",
            "points_var": "parafino_mode_points",
            "completed_var": "parafino_completed",
        },
        "kingpin": {
            "title": "KINGPIN",
            "intro_1": "Kingpin is terrorizing the city.",
            "intro_2": "Clear every area. JACKPOTS at Daily Bugle.",
            "intro_3": "A+B lights Add-a-ball at the Daily Bugle.",
            "summary_title_complete": "KINGPIN DEFEATED",
            "summary_title_failed": "KINGPIN ESCAPED",
            "stat_1_label": "AREAS CLEARED",
            "stat_1_var": "kingpin_areas_cleared",
            "stat_2_label": "MEGABALLS",
            "stat_2_var": "kingpin_max_balls",
            "points_var": "kingpin_mode_points",
            "completed_var": "kingpin_completed",
        },
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.current_stage = None
        self.current_done_event = None
        self.current_villain = None

        self.add_mode_event_handler("villain_bookend_intro_request", self._intro_request)
        self.add_mode_event_handler("villain_bookend_summary_request", self._summary_request)

        #both flippers held and released
        self.add_mode_event_handler("flipper_cancel", self._skip_current_bookend)

        self.add_mode_event_handler(
            "villain_bookend_intro_hold_request",
            self._intro_hold_request
        )

        self.add_mode_event_handler(
            "villain_bookend_intro_hold_release",
            self._intro_hold_release
        )

    def _intro_request(self, villain=None, start_event=None, **kwargs):
        if villain not in self.VILLAINS:
            self.warning_log("Unknown villain intro requested: %s", villain)
            return

        data = self.VILLAINS[villain]

        self.current_stage = "intro"
        self.current_villain = villain
        self.current_done_event = start_event # or f"{villain}_gameplay_start"

        self._set_machine_var("villain_bookend_title", data["title"])
        self._set_machine_var("villain_bookend_line_1", data["intro_1"])
        self._set_machine_var("villain_bookend_line_2", data["intro_2"])
        self._set_machine_var("villain_bookend_line_3", data["intro_3"])
        self._set_machine_var("villain_bookend_footer", "HOLD BOTH FLIPPERS TO SKIP")

        self.machine.events.post("villain_bookend_summary_hide")
        self.machine.events.post("villain_bookend_intro_show", villain=villain)

        self.delay.remove("villain_bookend_done")
        self.delay.add(
            name="villain_bookend_done",
            ms=self.INTRO_MS,
            callback=self._finish_current_bookend
        )

    def _summary_request(self, villain=None, done_event=None, **kwargs):
        if villain not in self.VILLAINS:
            self.warning_log("Unknown villain summary requested: %s", villain)
            return

        data = self.VILLAINS[villain]
        completed = self._get_player_value(data["completed_var"], 0)

        title = data["summary_title_complete"] if completed else data["summary_title_failed"]

        points = self._get_player_value(data["points_var"], 0)
        stat_1 = self._get_player_value(data["stat_1_var"], 0)
        stat_2 = self._get_player_value(data["stat_2_var"], 0)

        self.current_stage = "summary"
        self.current_villain = villain
        self.current_done_event = done_event or f"{villain}_summary_done"

        self._set_machine_var("villain_bookend_title", title)
        self._set_machine_var(
            "villain_bookend_line_1",
            f"{data['stat_1_label']}: {stat_1}"
        )
        self._set_machine_var(
            "villain_bookend_line_2",
            f"{data['stat_2_label']}: {stat_2}"
        )
        self._set_machine_var(
            "villain_bookend_line_3",
            f"POINTS: {points:,}"
        )
        self._set_machine_var("villain_bookend_footer", "HOLD BOTH FLIPPERS TO CONTINUE")

        self.machine.events.post("villain_bookend_intro_hide")
        self.machine.events.post("villain_bookend_summary_show", villain=villain)

        self.delay.remove("villain_bookend_done")
        self.delay.add(
            name="villain_bookend_done",
            ms=self.SUMMARY_MS,
            callback=self._finish_current_bookend
        )
    def _intro_hold_request(self, **kwargs):
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return

        try:
            villain = player["villain_current_name"]
        except KeyError:
            return

        if not villain:
            return

        if villain not in self.VILLAINS:
            self.warning_log("No bookend intro found for current villain: %s", villain)
            return

        data = self.VILLAINS[villain]

        self._set_machine_var("villain_bookend_title", data["title"])
        self._set_machine_var("villain_bookend_line_1", data["intro_1"])
        self._set_machine_var("villain_bookend_line_2", data["intro_2"])
        self._set_machine_var("villain_bookend_line_3", data["intro_3"])
        self._set_machine_var("villain_bookend_footer", "RELEASE FLIPPER TO RETURN")

        self.machine.events.post("villain_bookend_intro_show")


    def _intro_hold_release(self, **kwargs):
        self.machine.events.post("villain_bookend_intro_hide")

    def _skip_current_bookend(self, **kwargs):
        if self.current_stage in ("intro", "summary"):
            self.delay.remove("villain_bookend_done")
            self._finish_current_bookend()

    def _finish_current_bookend(self):
        if not self.current_stage:
            return

        done_event = self.current_done_event
        villain = self.current_villain
        stage = self.current_stage

        if stage == "intro":
            self.machine.events.post("villain_bookend_intro_hide")
            self.machine.events.post("villain_bookend_intro_done", villain=villain)

        elif stage == "summary":
            self.machine.events.post("reset_villain_locate")
            self.machine.events.post("villain_bookend_summary_hide")
            self.machine.events.post("villain_bookend_summary_done", villain=villain)

        self.current_stage = None
        self.current_villain = None
        self.current_done_event = None

        if done_event:
            self.machine.events.post(done_event, villain=villain)

    def _get_player_value(self, var_name, default=0):
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return default

        try:
            return player[var_name]
        except KeyError:
            return default

    def _set_machine_var(self, name, value):
        self.machine.variables.set_machine_var(name, value)