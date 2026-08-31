from mpf.core.mode import Mode


class TestModeSelect(Mode):
    """Physical-machine test harness for all 67 story modes plus Exit.

    Attract mode only arms the session. The player presses START normally, then
    this mode owns the selection UI while a real player/ball context exists.
    A clean both-flipper chord enters setup/toggles a villain Case File; a ball
    leaving the shooter lane launches the configured test.
    """

    CATALOG = [
        ('rhino', 'Rhino', 'VILLAIN', 1, 'start_mode_rhino_bash'),
        ('sandman', 'Sandman', 'VILLAIN', 1, 'start_mode_sandman'),
        ('vulture', 'Vulture', 'VILLAIN', 1, 'start_mode_vulture'),
        ('lizard', 'Green Lizard', 'VILLAIN', 2, 'start_mode_lizard'),
        ('electro', 'Electro', 'VILLAIN', 1, 'start_mode_electro'),
        ('goblin', 'Green Goblin', 'VILLAIN', 1, 'start_mode_goblin'),
        ('doc_ock', 'Doctor Octopus', 'VILLAIN', 2, 'start_mode_doc_ock'),
        ('mysterio', 'Mysterio', 'VILLAIN', 2, 'start_mode_mysterio'),
        ('scorpion', 'Scorpion', 'VILLAIN', 2, 'start_mode_scorpion'),
        ('parafino', 'Parafino', 'VILLAIN', 2, 'start_mode_parafino'),
        ('cerberus', 'Cerberus', 'VILLAIN', 3, 'start_mode_cerberus'),
        ('vulcan', 'Vulcan', 'VILLAIN', 3, 'start_mode_vulcan'),
        ('diana', 'Diana', 'VILLAIN', 3, 'start_mode_diana'),
        ('cyclops', 'Cyclops', 'VILLAIN', 3, 'start_mode_cyclops'),
        ('centaur', 'Centaur', 'VILLAIN', 3, 'start_mode_centaur'),
        ('plotter', 'The Plotter', 'VILLAIN', 4, 'start_mode_plotter'),
        ('fly_twins', 'The Fly Twins', 'VILLAIN', 4, 'start_mode_fly_twins'),
        ('fifth_avenue_phantom', '5th Ave Phantom', 'VILLAIN', 4, 'start_mode_fifth_avenue_phantom'),
        ('enforcers', 'The Enforcers', 'VILLAIN', 4, 'start_mode_enforcers'),
        ('doctor_cool', 'Doctor Cool', 'VILLAIN', 4, 'start_mode_doctor_cool'),
        ('harley_clivendon', 'Harley Clivendon', 'VILLAIN', 5, 'start_mode_harley_clivendon'),
        ('conquistador', 'The Conquistador', 'VILLAIN', 5, 'start_mode_conquistador'),
        ('spider_slayer', 'Spider-Slayer', 'VILLAIN', 5, 'start_mode_spider_slayer'),
        ('metal_eating_robot', 'Metal Monster', 'VILLAIN', 5, 'start_mode_metal_eating_robot'),
        ('fiddler', 'Fiddler', 'VILLAIN', 5, 'start_mode_fiddler'),
        ('pardo', 'Pardo', 'VILLAIN', 6, 'start_mode_pardo'),
        ('fakir', 'The Fantastic Fakir', 'VILLAIN', 6, 'start_mode_fakir'),
        ('kotep', 'Kotep', 'VILLAIN', 6, 'start_mode_kotep'),
        ('super_swami', 'Super Swami', 'VILLAIN', 6, 'start_mode_super_swami'),
        ('infinata', 'Infinata', 'VILLAIN', 6, 'start_mode_infinata'),
        ('noah_boddy', 'Dr. Noah Boddy', 'VILLAIN', 7, 'start_mode_noah_boddy'),
        ('dr_magneto', 'Dr. Magneto', 'VILLAIN', 7, 'start_mode_dr_magneto'),
        ('professor_pretorius', 'Professor Pretorius', 'VILLAIN', 7, 'start_mode_professor_pretorius'),
        ('doctor_dumpty', 'Doctor Dumpty', 'VILLAIN', 7, 'start_mode_doctor_dumpty'),
        ('dr_von_schlick', 'Dr. Von Schlick', 'VILLAIN', 7, 'start_mode_dr_von_schlick'),
        ('clive_blotto', 'Clive and Blotto', 'VILLAIN', 8, 'start_mode_clive_blotto'),
        ('dr_zapp', 'Doctor Zapp', 'VILLAIN', 8, 'start_mode_dr_zapp'),
        ('bolton_boomer', 'Bolton and Boomer', 'VILLAIN', 8, 'start_mode_bolton_boomer'),
        ('snowman', 'The Snowman', 'VILLAIN', 8, 'start_mode_snowman'),
        ('plutonians', 'The Plutonians', 'VILLAIN', 8, 'start_mode_plutonians'),
        ('dr_manta', 'Dr. Manta', 'VILLAIN', 9, 'start_mode_dr_manta'),
        ('igor', 'Igor', 'VILLAIN', 9, 'start_mode_igor'),
        ('doctor_atlantean', 'Doctor Atlantean', 'VILLAIN', 9, 'start_mode_doctor_atlantean'),
        ('devargas', 'DeVargas', 'VILLAIN', 9, 'start_mode_devargas'),
        ('molemen', 'The Molemen', 'VILLAIN', 9, 'start_mode_molemen'),
        ('charles_cameo', 'Charles Cameo', 'VILLAIN', 10, 'start_mode_charles_cameo'),
        ('brutus', 'Brutus', 'VILLAIN', 10, 'start_mode_brutus'),
        ('desperado', 'Desperado', 'VILLAIN', 10, 'start_mode_desperado'),
        ('skymaster', 'Skymaster', 'VILLAIN', 10, 'start_mode_skymaster'),
        ('conners_reptiles', "Conner's Reptiles", 'VILLAIN', 10, 'start_mode_conners_reptiles'),
        ('sir_galahad', 'Sir Galahad', 'VILLAIN', 11, 'start_mode_sir_galahad'),
        ('master_vine', 'Master Vine', 'VILLAIN', 11, 'start_mode_master_vine'),
        ('master_technician', 'Master Technician', 'VILLAIN', 11, 'start_mode_master_technician'),
        ('spider_men', 'The Spider-Men', 'VILLAIN', 11, 'start_mode_spider_men'),
        ('von_rantenraven', 'Baron von Rantenraven', 'VILLAIN', 11, 'start_mode_von_rantenraven'),
        ('sinister_surge', 'Sinister Surge', 'WIZARD', 1, 'start_mode_sinister_surge'),
        ('mastermind_trap', 'Mastermind Trap', 'WIZARD', 2, 'start_mode_mastermind_trap'),
        ('trubble_unleashed', 'Trubble Unleashed', 'WIZARD', 3, 'start_mode_trubble_unleashed'),
        ('crime_wave', 'Crime Wave', 'WIZARD', 4, 'start_mode_crime_wave'),
        ('the_web_tightens', 'The Web Tightens', 'WIZARD', 5, 'start_mode_the_web_tightens'),
        ('fifth_dimension_curse', 'Fifth Dimension Curse', 'WIZARD', 6, 'start_mode_fifth_dimension_curse'),
        ('mad_science_meltdown', 'Mad Science Meltdown', 'WIZARD', 7, 'start_mode_mad_science_meltdown'),
        ('nature_strikes_back', 'Nature Strikes Back', 'WIZARD', 8, 'start_mode_nature_strikes_back'),
        ('invasion_from_everywhere', 'Invasion from Everywhere', 'WIZARD', 9, 'start_mode_invasion_from_everywhere'),
        ('who_is_the_real_villain', 'Who Is the Real Villain?', 'WIZARD', 10, 'start_mode_who_is_the_real_villain'),
        ('time_tossed_showdown', 'Time-Tossed Showdown', 'WIZARD', 11, 'start_mode_time_tossed_showdown'),
        ('final_showdown', 'Kingpin / Final Showdown', 'FINAL', 0, 'start_mode_final_showdown'),
        ('exit_to_attract', 'Exit to Attract', 'EXIT', 0, ''),
    ]

    CASE_FILES = [
        ("more_jackpots", "MORE JACKPOTS"),
        ("more_time", "MORE TIME"),
        ("bigger_jackpots", "BIGGER JACKPOTS"),
        ("safety_net", "SAFETY NET"),
        ("shot_assist", "SHOT ASSIST"),
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        player = self.machine.game.player
        player["test_mode_session"] = 1
        player["villain_mode_running"] = 1
        self.left_active = self._switch_active("s_left_flipper")
        self.right_active = self._switch_active("s_right_flipper")
        self.clean_release = not self.left_active and not self.right_active
        self.both_armed = False
        self.suppress_next_single_release = False
        self.launch_armed = self._switch_active("s_plunger")

        self.add_mode_event_handler("s_left_flipper_active", self._left_active)
        self.add_mode_event_handler("s_left_flipper_inactive", self._left_inactive)
        self.add_mode_event_handler("s_right_flipper_active", self._right_active)
        self.add_mode_event_handler("s_right_flipper_inactive", self._right_inactive)
        self.add_mode_event_handler("s_plunger_active", self._plunger_active)
        self.add_mode_event_handler("s_plunger_inactive", self._plunger_inactive)

        stage = str(player["test_mode_select_stage"] or "MODE")
        if stage not in ("MODE", "VILLAIN_SETUP", "WIZARD_SETUP"):
            player["test_mode_select_stage"] = "MODE"
        self._clamp_values()
        self._publish()
        self.machine.events.post("test_mode_selector_ready")

    def _switch_active(self, name):
        switch = self.machine.switches.get(name)
        return bool(switch and self.machine.switch_controller.is_active(switch))

    def _clamp_values(self):
        p = self.machine.game.player
        p["test_mode_select_index"] = max(0, min(len(self.CATALOG) - 1, int(p["test_mode_select_index"] or 0)))
        p["test_case_cursor"] = max(0, min(len(self.CASE_FILES), int(p["test_case_cursor"] or 0)))
        p["test_wizard_case_files"] = max(0, min(25, int(p["test_wizard_case_files"] or 0)))

    def _left_active(self, **kwargs):
        self.left_active = True
        self._arm_both()

    def _right_active(self, **kwargs):
        self.right_active = True
        self._arm_both()

    def _left_inactive(self, **kwargs):
        select = self.both_armed
        self.left_active = False
        self._release(select, "left")

    def _right_inactive(self, **kwargs):
        select = self.both_armed
        self.right_active = False
        self._release(select, "right")

    def _arm_both(self):
        if self.clean_release and self.left_active and self.right_active:
            self.both_armed = True

    def _release(self, select, direction):
        if select:
            self.both_armed = False
            self.suppress_next_single_release = True
            self._both_flippers()
            return
        if self.suppress_next_single_release:
            if not self.left_active and not self.right_active:
                self.suppress_next_single_release = False
                self.clean_release = True
            return
        if not self.left_active and not self.right_active:
            self.clean_release = True
            self.both_armed = False
        if direction == "right" and not self.left_active:
            self._move(1)
        elif direction == "left" and not self.right_active:
            self._move(-1)

    def _move(self, delta):
        p = self.machine.game.player
        stage = p["test_mode_select_stage"]
        if stage == "MODE":
            p["test_mode_select_index"] = (int(p["test_mode_select_index"]) + delta) % len(self.CATALOG)
        elif stage == "VILLAIN_SETUP":
            p["test_case_cursor"] = (int(p["test_case_cursor"]) + delta) % (len(self.CASE_FILES) + 1)
        else:
            p["test_wizard_case_files"] = (int(p["test_wizard_case_files"]) + delta) % 26
        self.machine.events.post("test_mode_select_move")
        self._publish()

    def _both_flippers(self):
        p = self.machine.game.player
        stage = p["test_mode_select_stage"]
        if stage == "MODE":
            _, _, kind, _, _ = self.CATALOG[int(p["test_mode_select_index"])]
            if kind == "EXIT":
                self.machine.events.post("test_mode_exit_requires_plunge")
                self._publish()
                return
            p["test_mode_select_stage"] = "VILLAIN_SETUP" if kind == "VILLAIN" else "WIZARD_SETUP"
        elif stage == "VILLAIN_SETUP":
            cursor = int(p["test_case_cursor"])
            if cursor >= len(self.CASE_FILES):
                p["test_mode_select_stage"] = "MODE"
            else:
                key, _ = self.CASE_FILES[cursor]
                var = f"test_case_{key}"
                p[var] = 0 if int(p[var] or 0) else 1
                self.machine.events.post("test_mode_case_file_toggled", case_file=key, enabled=p[var])
        else:
            # In wizard setup, a both-flipper chord is the BACK command.
            p["test_mode_select_stage"] = "MODE"
        self._publish()

    def _plunger_active(self, **kwargs):
        self.launch_armed = True

    def _plunger_inactive(self, **kwargs):
        if not self.launch_armed:
            return
        self.launch_armed = False
        stage = self.machine.game.player["test_mode_select_stage"]
        if stage == "MODE":
            index = int(self.machine.game.player["test_mode_select_index"])
            if self.CATALOG[index][2] == "EXIT":
                self._exit_to_attract()
            return
        self._launch()

    def _exit_to_attract(self):
        """Disarm the test harness and end this disposable test game."""
        player = self.machine.game.player
        player["test_mode_exit_requested"] = 1
        player["test_mode_waiting_for_ball_return"] = 0
        self.machine.variables.set_machine_var("test_mode_session_requested", 0)
        self.machine.variables.set_machine_var("chapter_progression_test_unlock_all", 0)
        self.machine.events.post("test_mode_ball_loop_disable")
        self.machine.events.post("test_mode_exit_selected")
        self.machine.events.post("end_game")

    def _launch(self):
        p = self.machine.game.player
        index = int(p["test_mode_select_index"])
        key, name, kind, chapter, start_event = self.CATALOG[index]
        self.machine.events.post(
            "test_mode_launch_requested",
            mode_key=key,
            mode_name=name,
            mode_kind=kind,
            chapter=chapter,
            start_event=start_event,
            wizard_case_files=int(p["test_wizard_case_files"]),
        )
        self.machine.events.post("stop_mode_test_mode_select")

    def _publish(self):
        p = self.machine.game.player
        index = int(p["test_mode_select_index"])
        key, name, kind, chapter, _ = self.CATALOG[index]
        p["test_mode_select_header"] = f"TEST MODE {index + 1:02d} / {len(self.CATALOG)}"
        p["test_mode_select_name"] = name.upper()
        p["test_mode_select_detail"] = (f"CHAPTER {chapter} - {kind}" if chapter else kind)

        stage = p["test_mode_select_stage"]
        if stage == "MODE":
            if kind == "EXIT":
                p["test_mode_select_setup_title"] = "END TEST SESSION"
                p["test_mode_select_detail"] = "RETURN TO ATTRACT"
                p["test_mode_select_help"] = "PLUNGE = EXIT TO ATTRACT"
            else:
                p["test_mode_select_setup_title"] = "CHOOSE MODE"
                p["test_mode_select_help"] = "LEFT/RIGHT = SCROLL    BOTH FLIPPERS = SETUP"
            p["test_mode_select_setup_value"] = ""
            p["test_mode_select_case_summary"] = ""
        elif stage == "VILLAIN_SETUP":
            cursor = int(p["test_case_cursor"])
            if cursor >= len(self.CASE_FILES):
                title = "< BACK TO MODE LIST >"
            else:
                key2, label = self.CASE_FILES[cursor]
                title = f"> {label}: {'ON' if int(p[f'test_case_{key2}']) else 'OFF'} <"
            p["test_mode_select_setup_title"] = "VILLAIN CASE FILES"
            p["test_mode_select_setup_value"] = title
            p["test_mode_select_case_summary"] = self._case_summary()
            p["test_mode_select_help"] = "LEFT/RIGHT = CHOOSE    BOTH = TOGGLE/BACK    PLUNGE = START"
        else:
            total = int(p["test_wizard_case_files"])
            p["test_mode_select_setup_title"] = "WIZARD CASE FILE TOTAL"
            p["test_mode_select_setup_value"] = f"{total} / 25   (+{total * 20000:,} / JACKPOT)"
            p["test_mode_select_case_summary"] = ""
            p["test_mode_select_help"] = "LEFT/RIGHT = 0-25    BOTH = BACK    PLUNGE = START"
        self.machine.events.post("test_mode_select_view_changed", mode_key=key, mode_kind=kind)

    def _case_summary(self):
        p = self.machine.game.player
        parts = []
        for key, label in self.CASE_FILES:
            short = {
                "more_jackpots": "MORE JP",
                "more_time": "TIME",
                "bigger_jackpots": "BIGGER",
                "safety_net": "SAFETY",
                "shot_assist": "ASSIST",
            }[key]
            parts.append(f"{short} [{'X' if int(p[f'test_case_{key}']) else ' '}]")
        return "   ".join(parts)
