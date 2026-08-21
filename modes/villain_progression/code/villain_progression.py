from mpf.core.mode import Mode


class VillainProgression(Mode):
    """Single source of truth for villain chapters, states, and launches.

    Other modes should not keep their own villain lists or start villain modes
    directly. The intended flow is:

        villain_start.py decides that a physical shot is allowed to request a start
        villain_progression.py decides what that request means
        villain_select.py only shows/returns a selected key when choices are needed
        villain_progression.py starts the selected/default villain through bookends

    Durable progression states are numeric to keep the Godot BCP player-var payload small.
    Display labels are produced only for the chapter/status widgets.
    """

    # Durable progression states. These match config/player_vars.yaml.
    # 0 = not played, 1 = playing, 2 = completed.
    # Do not use a FAILED state for progression; a started mode is consumed
    # and resolved to COMPLETED. Separate goal-result flags can be added later.
    NOT_PLAYED = 0
    PLAYING = 1
    COMPLETED = 2

    # Display-only / compatibility labels. Wizard readiness is stored in
    # chapter_mini_wizard_ready / mini_wizard_daily_bugle_ready, not as a
    # durable mode state.
    READY = "ready"
    LIT = "lit"

    CASE_FILE_KEYS = [
        "more_jackpots",
        "more_time",
        "bigger_jackpots",
        "safety_net",
        "shot_assist",
    ]
    CASE_FILE_MINI_WIZARD_BONUS = 20_000
    MINI_WIZARD_BASE_JACKPOT = 50_000
    GATE_POWER_RECOVERY_MS = 500
    GATE_OPEN_VERIFY_MS = 1000
    GATE_OPEN_MAX_ATTEMPTS = 2
    VUK_EJECT_DEFAULT_DELAY_MS = 1_500
    VUK_EJECT_VERIFY_MS = 900
    GATE_POWER_SWITCHES = (
        "s_left_flipper",
        "s_right_flipper",
        "s_right_flipper_upper",
    )

    CHAPTERS = [
        {
            'key': 'classic_rogues',
            'name': 'Sinister Surge',
            'villains': ['rhino', 'sandman', 'vulture', 'electro', 'goblin'],
            'mini_wizard_key': 'sinister_surge',
            'mini_wizard_name': 'Sinister Surge',
            'mini_wizard_event': 'start_mode_sinister_surge',
        },
        {
            'key': 'masked_masterminds',
            'name': 'Mastermind Trap',
            'villains': ['doc_ock', 'mysterio', 'scorpion', 'lizard', 'parafino'],
            'mini_wizard_key': 'mastermind_trap',
            'mini_wizard_name': 'Mastermind Trap',
            'mini_wizard_event': 'start_mode_mastermind_trap',
        },
        {
            'key': 'trubbles_monsters',
            'name': 'Trubble Unleashed',
            'villains': ['cerberus', 'vulcan', 'diana', 'cyclops', 'centaur'],
            'mini_wizard_key': 'trubble_unleashed',
            'mini_wizard_name': 'Trubble Unleashed',
            'mini_wizard_event': 'start_mode_trubble_unleashed',
        },
        {
            'key': 'crime_wave',
            'name': 'Crime Wave',
            'villains': ['plotter', 'fly_twins', 'fifth_avenue_phantom', 'enforcers', 'doctor_cool'],
            'mini_wizard_key': 'crime_wave',
            'mini_wizard_name': 'Crime Wave',
            'mini_wizard_event': 'start_mode_crime_wave',
        },
        {
            'key': 'danger_lurks',
            'name': 'The Web Tightens',
            'villains': ['harley_clivendon', 'conquistador', 'spider_slayer', 'metal_eating_robot', 'fiddler'],
            'mini_wizard_key': 'the_web_tightens',
            'mini_wizard_name': 'The Web Tightens',
            'mini_wizard_event': 'start_mode_the_web_tightens',
        },
        {
            'key': 'mystic_menace',
            'name': 'Fifth Dimension Curse',
            'villains': ['pardo', 'fakir', 'kotep', 'super_swami', 'infinata'],
            'mini_wizard_key': 'fifth_dimension_curse',
            'mini_wizard_name': 'Fifth Dimension Curse',
            'mini_wizard_event': 'start_mode_fifth_dimension_curse',
        },
        {
            'key': 'mad_science',
            'name': 'Mad Science Meltdown',
            'villains': ['noah_boddy', 'dr_magneto', 'professor_pretorius', 'doctor_dumpty', 'dr_von_schlick'],
            'mini_wizard_key': 'mad_science_meltdown',
            'mini_wizard_name': 'Mad Science Meltdown',
            'mini_wizard_event': 'start_mode_mad_science_meltdown',
        },
        {
            'key': 'elemental_chaos',
            'name': 'Nature Strikes Back',
            'villains': ['clive_blotto', 'dr_zapp', 'bolton_boomer', 'snowman', 'plutonians'],
            'mini_wizard_key': 'nature_strikes_back',
            'mini_wizard_name': 'Nature Strikes Back',
            'mini_wizard_event': 'start_mode_nature_strikes_back',
        },
        {
            'key': 'lost_worlds',
            'name': 'Invasion from Everywhere',
            'villains': ['dr_manta', 'igor', 'doctor_atlantean', 'devargas', 'molemen'],
            'mini_wizard_key': 'invasion_from_everywhere',
            'mini_wizard_name': 'Invasion from Everywhere',
            'mini_wizard_event': 'start_mode_invasion_from_everywhere',
        },
        {
            'key': 'savage_oddities',
            'name': 'Who Is the Real Villain?',
            'villains': ['charles_cameo', 'brutus', 'desperado', 'skymaster', 'conners_reptiles'],
            'mini_wizard_key': 'who_is_the_real_villain',
            'mini_wizard_name': 'Who Is the Real Villain?',
            'mini_wizard_event': 'start_mode_who_is_the_real_villain',
        },
        {
            'key': 'dimensional_finale',
            'name': 'Time-Tossed Showdown',
            'villains': ['sir_galahad', 'master_vine', 'master_technician', 'spider_men', 'von_rantenraven'],
            'mini_wizard_key': 'time_tossed_showdown',
            'mini_wizard_name': 'Time-Tossed Showdown',
            'mini_wizard_event': 'start_mode_time_tossed_showdown',
        },
    ]

    INITIAL_AVAILABLE_CHAPTERS = (1, 2, 3)
    # Fixed reveal order keeps chapter discovery non-sequential but fair for
    # multiplayer/tournament games. Chapters 1-3 start available.
    CHAPTER_UNLOCK_DECK = (7, 4, 9, 5, 11, 8, 10, 6)

    VILLAINS = {
        'rhino': {'chapter': 1, 'name': 'Rhino', 'start_event': 'start_mode_rhino_bash'},
        'sandman': {'chapter': 1, 'name': 'Sandman', 'start_event': 'start_mode_sandman'},
        'vulture': {'chapter': 1, 'name': 'Vulture', 'start_event': 'start_mode_vulture'},
        'lizard': {'chapter': 2, 'name': 'Green Lizard', 'start_event': 'start_mode_lizard'},
        'electro': {'chapter': 1, 'name': 'Electro', 'start_event': 'start_mode_electro'},
        'goblin': {'chapter': 1, 'name': 'Green Goblin', 'start_event': 'start_mode_goblin'},
        'doc_ock': {'chapter': 2, 'name': 'Doctor Octopus', 'start_event': 'start_mode_doc_ock'},
        'mysterio': {'chapter': 2, 'name': 'Mysterio', 'start_event': 'start_mode_mysterio'},
        'scorpion': {'chapter': 2, 'name': 'Scorpion', 'start_event': 'start_mode_scorpion'},
        'parafino': {'chapter': 2, 'name': 'Parafino', 'start_event': 'start_mode_parafino'},
        'cerberus': {'chapter': 3, 'name': 'Cerberus', 'start_event': 'start_mode_cerberus'},
        'vulcan': {'chapter': 3, 'name': 'Vulcan', 'start_event': 'start_mode_vulcan'},
        'diana': {'chapter': 3, 'name': 'Diana', 'start_event': 'start_mode_diana'},
        'cyclops': {'chapter': 3, 'name': 'Cyclops', 'start_event': 'start_mode_cyclops'},
        'centaur': {'chapter': 3, 'name': 'Centaur', 'start_event': 'start_mode_centaur'},
        'plotter': {'chapter': 4, 'name': 'The Plotter', 'start_event': 'start_mode_plotter'},
        'fly_twins': {'chapter': 4, 'name': 'The Fly Twins', 'start_event': 'start_mode_fly_twins'},
        'fifth_avenue_phantom': {'chapter': 4, 'name': '5th Ave Phantom', 'start_event': 'start_mode_fifth_avenue_phantom'},
        'enforcers': {'chapter': 4, 'name': 'The Enforcers', 'start_event': 'start_mode_enforcers'},
        'doctor_cool': {'chapter': 4, 'name': 'Doctor Cool', 'start_event': 'start_mode_doctor_cool'},
        'harley_clivendon': {'chapter': 5, 'name': 'Harley Clivendon', 'start_event': 'start_mode_harley_clivendon'},
        'conquistador': {'chapter': 5, 'name': 'The Conquistador', 'start_event': 'start_mode_conquistador'},
        'spider_slayer': {'chapter': 5, 'name': 'Spider-Slayer', 'start_event': 'start_mode_spider_slayer'},
        'metal_eating_robot': {'chapter': 5, 'name': 'Metal Monster', 'start_event': 'start_mode_metal_eating_robot'},
        'fiddler': {'chapter': 5, 'name': 'Fiddler', 'start_event': 'start_mode_fiddler'},
        'pardo': {'chapter': 6, 'name': 'Pardo', 'start_event': 'start_mode_pardo'},
        'fakir': {'chapter': 6, 'name': 'The Fantastic Fakir', 'start_event': 'start_mode_fakir'},
        'kotep': {'chapter': 6, 'name': 'Kotep', 'start_event': 'start_mode_kotep'},
        'super_swami': {'chapter': 6, 'name': 'Super Swami', 'start_event': 'start_mode_super_swami'},
        'infinata': {'chapter': 6, 'name': 'Infinata', 'start_event': 'start_mode_infinata'},
        'noah_boddy': {'chapter': 7, 'name': 'Dr. Noah Boddy', 'start_event': 'start_mode_noah_boddy'},
        'dr_magneto': {'chapter': 7, 'name': 'Dr. Magneto', 'start_event': 'start_mode_dr_magneto'},
        'professor_pretorius': {'chapter': 7, 'name': 'Professor Pretorius', 'start_event': 'start_mode_professor_pretorius'},
        'doctor_dumpty': {'chapter': 7, 'name': 'Doctor Dumpty', 'start_event': 'start_mode_doctor_dumpty'},
        'dr_von_schlick': {'chapter': 7, 'name': 'Dr. Von Schlick', 'start_event': 'start_mode_dr_von_schlick'},
        'clive_blotto': {'chapter': 8, 'name': 'Clive and Blotto', 'start_event': 'start_mode_clive_blotto'},
        'dr_zapp': {'chapter': 8, 'name': 'Doctor Zapp', 'start_event': 'start_mode_dr_zapp'},
        'bolton_boomer': {'chapter': 8, 'name': 'Bolton and Boomer', 'start_event': 'start_mode_bolton_boomer'},
        'snowman': {'chapter': 8, 'name': 'The Snowman', 'start_event': 'start_mode_snowman'},
        'plutonians': {'chapter': 8, 'name': 'The Plutonians', 'start_event': 'start_mode_plutonians'},
        'dr_manta': {'chapter': 9, 'name': 'Dr. Manta', 'start_event': 'start_mode_dr_manta'},
        'igor': {'chapter': 9, 'name': 'Igor', 'start_event': 'start_mode_igor'},
        'doctor_atlantean': {'chapter': 9, 'name': 'Doctor Atlantean', 'start_event': 'start_mode_doctor_atlantean'},
        'devargas': {'chapter': 9, 'name': 'DeVargas', 'start_event': 'start_mode_devargas'},
        'molemen': {'chapter': 9, 'name': 'The Molemen', 'start_event': 'start_mode_molemen'},
        'charles_cameo': {'chapter': 10, 'name': 'Charles Cameo', 'start_event': 'start_mode_charles_cameo'},
        'brutus': {'chapter': 10, 'name': 'Brutus', 'start_event': 'start_mode_brutus'},
        'desperado': {'chapter': 10, 'name': 'Desperado', 'start_event': 'start_mode_desperado'},
        'skymaster': {'chapter': 10, 'name': 'Skymaster', 'start_event': 'start_mode_skymaster'},
        'conners_reptiles': {'chapter': 10, 'name': "Conner's Reptiles", 'start_event': 'start_mode_conners_reptiles'},
        'sir_galahad': {'chapter': 11, 'name': 'Sir Galahad', 'start_event': 'start_mode_sir_galahad'},
        'master_vine': {'chapter': 11, 'name': 'Master Vine', 'start_event': 'start_mode_master_vine'},
        'master_technician': {'chapter': 11, 'name': 'Master Technician', 'start_event': 'start_mode_master_technician'},
        'spider_men': {'chapter': 11, 'name': 'The Spider-Men', 'start_event': 'start_mode_spider_men'},
        'von_rantenraven': {'chapter': 11, 'name': 'Baron von Rantenraven', 'start_event': 'start_mode_von_rantenraven'},
    }

    FINAL_WIZARD_KEY = "final_showdown"
    FINAL_WIZARD_NAME = "Kingpin"
    FINAL_WIZARD_EVENT = "start_mode_final_showdown"

    # These are the events posted by the individual villain modes when their
    # gameplay is finished. Progression owns the next step: mark state, stop the
    # gameplay mode, then ask villain_bookends to show the summary.
    COMPLETION_EVENTS = {
        'rhino_bash_complete': ('rhino', True),
        'rhino_mode_complete': ('rhino', True),
        'sandman_mode_complete': ('sandman', True),
        'vulture_mode_complete': ('vulture', True),
        'lizard_mode_complete': ('lizard', True),
        'electro_mode_complete': ('electro', True),
        'goblin_mode_complete': ('goblin', True),
        'doc_ock_mode_complete': ('doc_ock', True),
        'mysterio_mode_complete': ('mysterio', True),
        'scorpion_mode_complete': ('scorpion', True),
        'parafino_mode_complete': ('parafino', True),
        'cerberus_mode_complete': ('cerberus', True),
        'vulcan_mode_complete': ('vulcan', True),
        'diana_mode_complete': ('diana', True),
        'cyclops_mode_complete': ('cyclops', True),
        'centaur_mode_complete': ('centaur', True),
        'plotter_mode_complete': ('plotter', True),
        'fly_twins_mode_complete': ('fly_twins', True),
        'fifth_avenue_phantom_mode_complete': ('fifth_avenue_phantom', True),
        'enforcers_mode_complete': ('enforcers', True),
        'doctor_cool_mode_complete': ('doctor_cool', True),
        'harley_clivendon_mode_complete': ('harley_clivendon', True),
        'conquistador_mode_complete': ('conquistador', True),
        'spider_slayer_mode_complete': ('spider_slayer', True),
        'metal_eating_robot_mode_complete': ('metal_eating_robot', True),
        'fiddler_mode_complete': ('fiddler', True),
        'pardo_mode_complete': ('pardo', True),
        'fakir_mode_complete': ('fakir', True),
        'kotep_mode_complete': ('kotep', True),
        'super_swami_mode_complete': ('super_swami', True),
        'infinata_mode_complete': ('infinata', True),
        'noah_boddy_mode_complete': ('noah_boddy', True),
        'dr_magneto_mode_complete': ('dr_magneto', True),
        'professor_pretorius_mode_complete': ('professor_pretorius', True),
        'doctor_dumpty_mode_complete': ('doctor_dumpty', True),
        'dr_von_schlick_mode_complete': ('dr_von_schlick', True),
        'clive_blotto_mode_complete': ('clive_blotto', True),
        'clive_blotto_mode_failed': ('clive_blotto', False),
        'dr_zapp_mode_complete': ('dr_zapp', True),
        'bolton_boomer_mode_complete': ('bolton_boomer', True),
        'snowman_mode_complete': ('snowman', True),
        'plutonians_mode_complete': ('plutonians', True),
        'dr_manta_mode_complete': ('dr_manta', True),
        'igor_mode_complete': ('igor', True),
        'doctor_atlantean_mode_complete': ('doctor_atlantean', True),
        'devargas_mode_complete': ('devargas', True),
        'molemen_mode_complete': ('molemen', True),
        'charles_cameo_mode_complete': ('charles_cameo', True),
        'brutus_mode_complete': ('brutus', True),
        'desperado_mode_complete': ('desperado', True),
        'skymaster_mode_complete': ('skymaster', True),
        'conners_reptiles_mode_complete': ('conners_reptiles', True),
        'sir_galahad_mode_complete': ('sir_galahad', True),
        'master_vine_mode_complete': ('master_vine', True),
        'master_technician_mode_complete': ('master_technician', True),
        'spider_men_mode_complete': ('spider_men', True),
        'spider_men_mode_failed': ('spider_men', False),
        'von_rantenraven_mode_complete': ('von_rantenraven', True),
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.villain_progression_logic_active = True
        self.mini_wizard_gate_open_pending = False
        self.mini_wizard_gate_open_reason = ""
        self.mini_wizard_gate_open_cycle_active = False
        self.mini_wizard_gate_open_attempts = 0
        self.summary_held_saucers = set()

        # Player vars are initialized in config/player_vars.yaml. This mode is
        # a stateless interpreter of those durable vars: it recovers unresolved
        # PLAYING states on ball start, recalculates readiness, then restores
        # the current physical/display state.
        recovered = self._recover_playing_modes_as_completed()
        self._clear_runtime_flow_flags()
        self._clear_active_case_file_helpers()

        # If a mode was recovered from PLAYING, it probably died at ball end.
        # Run common cleanup before recalculating readiness, so a newly-ready
        # wizard can reopen the gate afterward.
        if recovered:
            self._post_global_cleanup_events(reason="startup_recovery")

        self._recalculate_progression_from_states(post_events=True)

        self._add_handlers()
        self._try_pending_mini_wizard_gate_open()

        # Central saucer clearing lives here because villain_progression is
        # active during normal gameplay. This lets clear_saucers only pulse
        # saucer kickout coils when the matching saucer switch is actually active.
        self.add_mode_event_handler("clear_saucers", self._clear_saucers)
        self.add_mode_event_handler("clear_saucers_delayed", self._clear_saucers_delayed)

        self._restore_state()

        if recovered:
            self._schedule_case_files_restore(reason="startup_recovery")

        if (
            self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) == 1
            and self._safe_int(self.machine.game.player["chapter_select_needed"], 0) == 0
        ):
            self._mini_wizard_ready_at_daily_bugle(
                post_restore=False,
                reason="ball_start_restore",
            )

        # Chapter Select starts automatically from config.yaml when needed;
        # the Start button remains reserved for normal start/add-player behavior.

    def _schedule_chapter_select_at_shooter_lane(self):
        self.delay.remove("chapter_select_at_shooter_lane")
        self.delay.add(
            name="chapter_select_at_shooter_lane",
            ms=500,
            callback=lambda: self.machine.events.post(
                "start_mode_chapter_select",
                chapter=self.machine.game.player["selected_chapter"],
            ),
        )

    def _schedule_mini_wizard_gate_open(self, reason=""):
        """Open rooftop access once the flipper power load has cleared.

        The rooftop diverter/gate coil toggles mechanically, so this method must
        only be called when readiness is first awarded or restored on a new ball.
        A summary can finish from a both-flipper hold. Waiting for every flipper
        button to be released prevents their hold coils from starving the 220ms
        gate pulse. A short recovery period follows release, and the switch state
        is checked again immediately before the one allowed gate-open request.
        """
        self.delay.remove("mini_wizard_ready_gate_open")
        self.delay.remove("mini_wizard_ready_gate_verify")
        if not self.mini_wizard_gate_open_cycle_active:
            self.mini_wizard_gate_open_attempts = 0
        self.mini_wizard_gate_open_cycle_active = True
        self.mini_wizard_gate_open_pending = True
        self.mini_wizard_gate_open_reason = reason
        self._try_pending_mini_wizard_gate_open()

    def _flipper_power_in_use(self):
        return any(
            self.machine.switch_controller.is_active(self.machine.switches[switch_name])
            for switch_name in self.GATE_POWER_SWITCHES
        )

    def _try_pending_mini_wizard_gate_open(self, **kwargs):
        if not self.mini_wizard_gate_open_pending:
            return
        if self._flipper_power_in_use():
            self.delay.remove("mini_wizard_ready_gate_open")
            self.machine.events.post(
                "mini_wizard_gate_open_waiting_for_flipper_release",
                reason=self.mini_wizard_gate_open_reason,
            )
            return
        self.delay.remove("mini_wizard_ready_gate_open")
        self.delay.add(
            name="mini_wizard_ready_gate_open",
            ms=self.GATE_POWER_RECOVERY_MS,
            callback=self._fire_pending_mini_wizard_gate_open,
        )

    def _fire_pending_mini_wizard_gate_open(self, **kwargs):
        if not self.mini_wizard_gate_open_pending:
            return
        if self._flipper_power_in_use():
            self._try_pending_mini_wizard_gate_open()
            return

        reason = self.mini_wizard_gate_open_reason
        self.mini_wizard_gate_open_pending = False
        self.mini_wizard_gate_open_attempts += 1
        self.machine.events.post(
            "rooftop_diverter_open",
            reason=reason,
        )
        self.machine.events.post(
            "mini_wizard_gate_open_requested",
            reason=reason,
            attempt=self.mini_wizard_gate_open_attempts,
        )
        self.delay.remove("mini_wizard_ready_gate_verify")
        self.delay.add(
            name="mini_wizard_ready_gate_verify",
            ms=self.GATE_OPEN_VERIFY_MS,
            callback=self._verify_mini_wizard_gate_open,
        )

    def _gate_still_needs_opening(self):
        # Follow the established state guards in config/config.yaml. Despite
        # the switch name, state 1 enables the open pulse and state 0 enables
        # the close pulse, so active means the requested opening did not occur.
        return self.machine.switch_controller.is_active(
            self.machine.switches["s_diverter_open"]
        )

    def _verify_mini_wizard_gate_open(self, **kwargs):
        if not self.mini_wizard_gate_open_cycle_active:
            return

        if not self._gate_still_needs_opening():
            reason = self.mini_wizard_gate_open_reason
            attempts = self.mini_wizard_gate_open_attempts
            self.mini_wizard_gate_open_cycle_active = False
            self.mini_wizard_gate_open_pending = False
            self.mini_wizard_gate_open_reason = ""
            self.mini_wizard_gate_open_attempts = 0
            self.machine.events.post(
                "villain_mini_wizard_gate_opened",
                reason=reason,
                attempts=attempts,
            )
            return

        if self.mini_wizard_gate_open_attempts >= self.GATE_OPEN_MAX_ATTEMPTS:
            reason = self.mini_wizard_gate_open_reason
            attempts = self.mini_wizard_gate_open_attempts
            self.mini_wizard_gate_open_cycle_active = False
            self.mini_wizard_gate_open_pending = False
            self.mini_wizard_gate_open_reason = ""
            self.mini_wizard_gate_open_attempts = 0
            self.machine.events.post(
                "mini_wizard_gate_open_failed_verification",
                reason=reason,
                attempts=attempts,
            )
            return

        self.mini_wizard_gate_open_pending = True
        self.machine.events.post(
            "mini_wizard_gate_open_retry",
            reason=self.mini_wizard_gate_open_reason,
            attempt=self.mini_wizard_gate_open_attempts + 1,
        )
        self._try_pending_mini_wizard_gate_open()

    def mode_stop(self, **kwargs):
        # Do not make progression decisions while stopping at ball_ending.
        # Anything still PLAYING will be resolved on the next mode_start.
        self.villain_progression_logic_active = False
        self.mini_wizard_gate_open_pending = False
        self.mini_wizard_gate_open_cycle_active = False
        self.delay.remove("mini_wizard_ready_gate_open")
        self.delay.remove("mini_wizard_ready_gate_verify")
        super().mode_stop(**kwargs)

    def _recover_playing_modes_as_completed(self):
        """Resolve durable PLAYING states left over from a previous ball.

        We cannot rely on villain/wizard modes, or this mode, to update state
        during ball_ending. The reliable contract is:

            start path writes PLAYING
            live completion/failure writes COMPLETED
            next ball startup converts any remaining PLAYING to COMPLETED

        Returns True if anything was recovered.
        """
        player = self.machine.game.player
        recovered = []

        for villain_key, info in self.VILLAINS.items():
            state = self._normalize_state(player[f"{villain_key}_state"])
            if state == self.PLAYING:
                player[f"{villain_key}_state"] = self.COMPLETED
                recovered.append(villain_key)
                self.machine.events.post(
                    "villain_gameplay_recovered_completed",
                    villain_key=villain_key,
                    villain_name=info["name"],
                )
            elif state == self.COMPLETED:
                player[f"{villain_key}_state"] = self.COMPLETED
            else:
                player[f"{villain_key}_state"] = self.NOT_PLAYED

        for chapter_number, chapter in enumerate(self.CHAPTERS, start=1):
            mini_key = chapter["mini_wizard_key"]
            state = self._normalize_state(player[f"{mini_key}_state"])
            if state == self.PLAYING:
                player[f"{mini_key}_state"] = self.COMPLETED
                recovered.append(mini_key)
                self.machine.events.post(
                    "chapter_mini_wizard_recovered_completed",
                    mini_wizard=mini_key,
                    chapter_number=chapter_number,
                )
            elif state == self.COMPLETED:
                player[f"{mini_key}_state"] = self.COMPLETED
            else:
                player[f"{mini_key}_state"] = self.NOT_PLAYED

        final_state = self._normalize_state(player[f"{self.FINAL_WIZARD_KEY}_state"])
        if final_state == self.PLAYING:
            player[f"{self.FINAL_WIZARD_KEY}_state"] = self.COMPLETED
            player["final_wizard_ready"] = 0
            recovered.append(self.FINAL_WIZARD_KEY)
            self.machine.events.post("final_wizard_recovered_completed")
        elif final_state == self.COMPLETED:
            player[f"{self.FINAL_WIZARD_KEY}_state"] = self.COMPLETED
        else:
            player[f"{self.FINAL_WIZARD_KEY}_state"] = self.NOT_PLAYED

        if recovered:
            self.machine.events.post(
                "villain_progression_recovered_playing_modes",
                recovered_count=len(recovered),
                recovered_keys=",".join(recovered),
            )

        return bool(recovered)

    def _force_safe_ball_start_state(self):
        """Compatibility hook for older event names."""
        recovered = self._recover_playing_modes_as_completed()
        self._clear_runtime_flow_flags()
        self._clear_active_case_file_helpers()
        if recovered:
            self._post_global_cleanup_events(reason="ball_start_recovery")
        self._recalculate_progression_from_states(post_events=True)
        if (
            self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) == 1
            and self._safe_int(self.machine.game.player["chapter_select_needed"], 0) == 0
        ):
            self._mini_wizard_ready_at_daily_bugle(
                post_restore=False,
                reason="ball_start_state_restore",
            )

    def _finalize_active_flow_on_mode_stop(self):
        """Deprecated: progression is no longer resolved during mode_stop."""
        return

    def _mark_stale_playing_items_failed(self):
        """Compatibility wrapper. Stale PLAYING now resolves to COMPLETED."""
        return self._recover_playing_modes_as_completed()

    def _clear_runtime_flow_flags(self):
        player = self.machine.game.player

        player["villain_mode_running"] = 0
        player["villain_mode_in_summary"] = 0
        player["villain_current_key"] = ""
        player["villain_current_name"] = ""
        player["villain_mode_running_name"] = ""
        player["villain_select_active"] = 0

        player["mini_wizard_current_key"] = ""
        player["mini_wizard_daily_bugle_ready"] = 0
        player["mini_wizard_vuk_hold_active"] = 0

    def _clear_active_case_file_helpers(self):
        player = self.machine.game.player
        player["active_case_file_helper_count"] = 0
        for index in range(1, 6):
            player[f"active_case_file_helper_{index}"] = ""

        self.machine.events.post("case_files_active_helpers_changed")
        self.machine.events.post("daily_bugle_widget_update")

    def _post_global_cleanup_events(self, reason=""):
        self.machine.events.post("villain_full_cleanup", reason=reason)
        self.machine.events.post("case_files_clear_lights", reason=reason)
        self.machine.events.post("clear_villain_saucer_lights", reason=reason)
        self.machine.events.post("timer_timer_up_post_hold_complete", reason=reason)
        # Mini-wizards and final wizard disable Daily Bugle while they own the
        # VUK. Re-enable and redraw it during any global cleanup so A/B and the
        # default VUK eject path recover even if a wizard stops unexpectedly.
        self.machine.events.post("enable_daily_bugle_mystery", reason=reason)
        self.machine.events.post("daily_bugle_restore_state", reason=reason)
        self.machine.events.post("case_files_active_helpers_changed", reason=reason)
        self.machine.events.post("case_files_restore_state", reason=reason)
        self.machine.events.post("daily_bugle_widget_update", reason=reason)
        self.machine.events.post("villain_mode_ended", villain_key="", villain="", reason=reason)

    def _sync_chapter_ready_flags(self, post_events=True):
        """Compatibility wrapper for the recalculation pass."""
        self._recalculate_progression_from_states(post_events=post_events)

    def _recalculate_progression_from_states(self, post_events=True):
        """Derive selected chapter, wizard readiness, and counts.

        Chapter Select owns which comic/chapter is active. Completing a
        mini-wizard marks that comic COLLECTED and reveals another chapter from
        the fixed deck, but progression does not force a strict 1->2->3->4 path.
        """
        player = self.machine.game.player

        self._sync_chapter_collection_state()

        completed_minis = sum(
            1
            for index, chapter_info in enumerate(self.CHAPTERS, start=1)
            if self._safe_int(player[f"chapter_{index}_collected"], 0) == 1
        )
        player["mini_wizards_completed"] = completed_minis

        selected = self._safe_int(player["selected_chapter"], 1)
        if selected < 1 or selected > len(self.CHAPTERS):
            selected = self._first_available_chapter_number() or 1
            player["selected_chapter"] = selected

        player["villain_chapter"] = selected

        chapter = self._get_current_chapter()
        if chapter is None:
            player["chapter_mini_wizard_ready"] = 0
            player["mini_wizard_daily_bugle_ready"] = 0
            final_completed = self._normalize_state(player[f"{self.FINAL_WIZARD_KEY}_state"]) == self.COMPLETED
            was_ready = self._safe_int(player["final_wizard_ready"], 0) == 1
            player["final_wizard_ready"] = 0 if final_completed else 1
            if not final_completed and self._normalize_state(player[f"{self.FINAL_WIZARD_KEY}_state"]) != self.PLAYING:
                player[f"{self.FINAL_WIZARD_KEY}_state"] = self.NOT_PLAYED
            if post_events and player["final_wizard_ready"] == 1 and not was_ready:
                self.machine.events.post("final_wizard_ready")
            return

        player["final_wizard_ready"] = 0

        completed_count = 0
        for key in chapter["villains"]:
            state = self._villain_state(key)
            if state == self.COMPLETED:
                completed_count += 1

        player["villains_played_this_chapter"] = completed_count
        player["villains_played_total"] = sum(
            1 for key in self.VILLAINS
            if self._villain_state(key) == self.COMPLETED
        )

        mini_key = chapter["mini_wizard_key"]
        mini_completed = self._normalize_state(player[f"{mini_key}_state"]) == self.COMPLETED
        mini_playing = self._normalize_state(player[f"{mini_key}_state"]) == self.PLAYING
        required = len(chapter["villains"])

        # While waiting for comic/chapter selection at the shooter lane, do not
        # reopen the completed chapter's wizard or advance start logic.
        if self._safe_int(player["chapter_select_needed"], 0) == 1:
            player["chapter_mini_wizard_ready"] = 0
            player["mini_wizard_daily_bugle_ready"] = 0
            return

        if completed_count >= required and not mini_completed:
            was_ready = self._safe_int(player["chapter_mini_wizard_ready"], 0) == 1
            player["chapter_mini_wizard_ready"] = 1
            player["mini_wizard_daily_bugle_ready"] = 1
            if not mini_playing:
                player[f"{mini_key}_state"] = self.NOT_PLAYED

            if post_events and not was_ready:
                self.machine.events.post(
                    "chapter_mini_wizard_ready",
                    chapter=chapter["key"],
                    chapter_name=chapter["name"],
                    mini_wizard_key=mini_key,
                    mini_wizard_name=chapter["mini_wizard_name"],
                    mini_wizard_event=chapter["mini_wizard_event"],
                )
                self._mini_wizard_ready_at_daily_bugle(post_restore=False)
            return

        player["chapter_mini_wizard_ready"] = 0
        player["mini_wizard_daily_bugle_ready"] = 0
        if not mini_completed and not mini_playing:
            player[f"{mini_key}_state"] = self.NOT_PLAYED

    SAUCER_EJECT_DELAY_MS = 750
    SAUCER_CLEAR_STAGGER_MS = 300
    SAUCER_EJECTS = {
        "1": ("s_saucer_1", "kickout_saucer_1"),
        "2": ("s_saucer_2", "kickout_saucer_2"),
        "3": ("s_saucer_3", "kickout_saucer_3"),
    }

    def _clear_saucers_delayed(self, **kwargs):
        """Delay normal saucer kickout so saucer awards feel intentional."""
        self.delay.remove("clear_saucers_delayed")
        self.delay.add(
            name="clear_saucers_delayed",
            ms=1000,
            callback=self._clear_saucers_now,
        )

    def _clear_saucers(self, **kwargs):
        """Default saucer cleanup waits briefly before kicking balls out."""
        self.info_log("CLEAR SAUCERS requested. kwargs=%s", kwargs)
        self.delay.remove("clear_saucers")
        self.delay.add(
            name="clear_saucers",
            ms=self.SAUCER_EJECT_DELAY_MS,
            callback=self._clear_saucers_now,
        )

    def _clear_saucers_now(self, **kwargs):
        """Kick out only saucers that currently contain a ball.

        The saucers are not MPF ball devices, so this checks the physical
        saucer switches first and only posts the matching raw kickout event
        when a ball is actually sitting there.
        """
        self.info_log("CLEAR SAUCERS NOW called. kwargs=%s", kwargs)

        occupied_saucers = []
        for saucer_number, (switch_name, _kickout_event) in self.SAUCER_EJECTS.items():
            if saucer_number in self.summary_held_saucers:
                self.machine.events.post(
                    "villain_summary_saucer_eject_suppressed",
                    saucer=saucer_number,
                )
                continue
            active = self.machine.switch_controller.is_active(self.machine.switches[switch_name])
            self.info_log("Saucer check %s active=%s", switch_name, active)

            if active:
                occupied_saucers.append(saucer_number)

        # Do not fire multiple high-current saucer coils on the same tick.
        # The first occupied saucer releases now; any others follow 300 ms apart.
        for saucer_number in self.SAUCER_EJECTS:
            self.delay.remove(f"clear_saucer_{saucer_number}_stagger")
            self.delay.remove(f"request_saucer_eject_{saucer_number}")

        for index, saucer_number in enumerate(occupied_saucers):
            self.delay.reset(
                name=f"clear_saucer_{saucer_number}_stagger",
                ms=index * self.SAUCER_CLEAR_STAGGER_MS,
                callback=self._kickout_saucer_if_occupied,
                saucer_number=saucer_number,
            )

    def _delayed_kickout_saucer(self, saucer_number, **kwargs):
        """Public delayed kickout event for modes that hold/release saucers."""
        self._request_saucer_eject(saucer_number=saucer_number)

    def _request_saucer_eject(self, saucer_number=None, delay_ms=None, **kwargs):
        """Schedule one occupancy-checked saucer release from this persistent mode."""
        saucer_number = str(saucer_number)
        if saucer_number not in self.SAUCER_EJECTS:
            self.warning_log("Unknown delayed saucer kickout requested: %s", saucer_number)
            return

        delay_name = f"request_saucer_eject_{saucer_number}"
        self.delay.remove(f"clear_saucer_{saucer_number}_stagger")
        if saucer_number in self.summary_held_saucers:
            self.delay.remove(delay_name)
            self.machine.events.post(
                "villain_summary_saucer_eject_suppressed",
                saucer=saucer_number,
            )
            return

        try:
            release_delay = int(delay_ms)
        except (TypeError, ValueError):
            release_delay = self.SAUCER_EJECT_DELAY_MS

        self.delay.reset(
            name=delay_name,
            ms=max(0, release_delay),
            callback=self._kickout_saucer_if_occupied,
            saucer_number=saucer_number,
        )

    def _kickout_saucer_if_occupied(self, saucer_number, **kwargs):
        saucer_number = str(saucer_number)
        if saucer_number in self.summary_held_saucers:
            self.machine.events.post(
                "villain_summary_saucer_eject_suppressed",
                saucer=saucer_number,
            )
            return
        switch_name, kickout_event = self.SAUCER_EJECTS[saucer_number]
        active = self.machine.switch_controller.is_active(self.machine.switches[switch_name])
        self.info_log("Delayed saucer %s eject check %s active=%s", saucer_number, switch_name, active)

        if active:
            self.machine.events.post(kickout_event)
        else:
            self.machine.events.post("delayed_saucer_kickout_skipped_empty", saucer=saucer_number)

    def _hold_saucer_until_summary_done(self, saucer_number=None, **kwargs):
        """Suppress normal ejects for a terminal saucer shot until summary."""
        requested = []
        if saucer_number is not None:
            requested.append(str(saucer_number).replace("saucer_", ""))
        else:
            for number, (switch_name, _kickout_event) in self.SAUCER_EJECTS.items():
                if self.machine.switch_controller.is_active(self.machine.switches[switch_name]):
                    requested.append(number)

        for number in requested:
            if number not in self.SAUCER_EJECTS:
                continue
            self.summary_held_saucers.add(number)
            self.delay.remove(f"delayed_kickout_saucer_{number}")
            self.delay.remove(f"request_saucer_eject_{number}")
            self.delay.remove(f"clear_saucer_{number}_stagger")
            self.machine.events.post(
                "villain_summary_saucer_hold_started",
                saucer=number,
            )

    def _release_summary_saucer_holds(self, **kwargs):
        """Allow the existing end-of-summary saucer cleanup to eject balls."""
        held = sorted(self.summary_held_saucers)
        self.summary_held_saucers.clear()
        for number in held:
            self.machine.events.post(
                "villain_summary_saucer_hold_released",
                saucer=number,
            )

    def _add_handlers(self):
        # Public API for the rest of the game.
        self.add_mode_event_handler("villain_progression_request_start", self._request_start)
        self.add_mode_event_handler("villain_progression_request_choices", self._post_available_choices)
        self.add_mode_event_handler("villain_progression_start_default", self._start_default_villain)
        self.add_mode_event_handler("mystery_award_start_next_villain", self._mystery_start_next_villain)
        self.add_mode_event_handler("villain_progression_start_selected", self._start_selected_villain)
        self.add_mode_event_handler("villain_select_choice_made", self._start_selected_villain)
        self.add_mode_event_handler("chapter_select_selected", self._chapter_selected)
        self.add_mode_event_handler("villain_progression_start_final_wizard", self._start_final_wizard)
        self.add_mode_event_handler("final_showdown_mode_complete", self._final_wizard_gameplay_finished, completed=True)
        self.add_mode_event_handler("villain_progression_restore_state", self._restore_state)

        # Completion / wizard flow.
        for event_name, finish_info in self.COMPLETION_EVENTS.items():
            villain_key, completed = finish_info
            self.add_mode_event_handler(
                event_name,
                self._villain_mode_finished,
                villain_key=villain_key,
                completed=completed,
            )

        # Legacy manual completion hook. Prefer the concrete events above for
        # real gameplay modes.
        self.add_mode_event_handler("villain_played", self._villain_completed)
        self.add_mode_event_handler("villain_bookend_summary_done", self._summary_done)
        self.add_mode_event_handler("chapter_mini_wizard_completed", self._mini_wizard_completed)

        # Mini-wizard gameplay ends first, then bookends shows the summary,
        # then progression advances to the next chapter.
        for chapter in self.CHAPTERS:
            mini_key = chapter["mini_wizard_key"]
            self.add_mode_event_handler(
                f"{mini_key}_mode_complete",
                self._mini_wizard_gameplay_finished,
                mini_wizard=mini_key,
                completed=True,
            )
            self.add_mode_event_handler(
                f"{mini_key}_summary_done",
                self._mini_wizard_summary_done,
                mini_wizard=mini_key,
            )

        self.add_mode_event_handler("mini_wizard_start_ready_at_daily_bugle", self._mini_wizard_ready_at_daily_bugle)
        self.add_mode_event_handler("s_vuk_switch_active", self._daily_bugle_hit)
        self.add_mode_event_handler("villain_bookend_intro_done", self._mini_wizard_intro_done)

        # Shared VUK release API. The VUK is a raw switch/coil pair rather than
        # an MPF ball device, so delayed releases must survive the scoring
        # mode that requested them stopping. Every up_kick also gets one
        # switch-confirmed retry in case the first pulse does not clear the VUK.
        self.add_mode_event_handler("request_vuk_eject", self._request_vuk_eject)
        self.add_mode_event_handler("cancel_vuk_eject_request", self._cancel_vuk_eject_request)
        self.add_mode_event_handler("up_kick", self._up_kick_requested)
        self.add_mode_event_handler("villain_summary_hold_vuk_until_done", self._cancel_vuk_eject_request)
        self.add_mode_event_handler("villain_summary_hold_saucer_until_done", self._hold_saucer_until_summary_done)
        self.add_mode_event_handler("villain_summary_release_saucer_holds", self._release_summary_saucer_holds)

        # Delayed saucer eject API. Raw kickout_saucer_* events still exist for
        # explicit immediate coil tests/manual use, but gameplay modes should use
        # these so saucer releases don't stack on top of other high-current events.
        self.add_mode_event_handler("delayed_kickout_saucer_1", self._delayed_kickout_saucer, saucer_number="1")
        self.add_mode_event_handler("delayed_kickout_saucer_2", self._delayed_kickout_saucer, saucer_number="2")
        self.add_mode_event_handler("delayed_kickout_saucer_3", self._delayed_kickout_saucer, saucer_number="3")
        self.add_mode_event_handler("request_saucer_eject", self._request_saucer_eject)
        self.add_mode_event_handler("clear_saucers_now", self._clear_saucers_now)
        self.add_mode_event_handler("s_left_flipper_inactive", self._try_pending_mini_wizard_gate_open)
        self.add_mode_event_handler("s_right_flipper_inactive", self._try_pending_mini_wizard_gate_open)
        self.add_mode_event_handler("s_right_flipper_upper_inactive", self._try_pending_mini_wizard_gate_open)

    def _request_vuk_eject(self, delay_ms=None, **kwargs):
        """Schedule a VUK release from this persistent progression mode."""
        try:
            release_delay = int(delay_ms)
        except (TypeError, ValueError):
            release_delay = self.VUK_EJECT_DEFAULT_DELAY_MS

        self.delay.reset(
            name="shared_vuk_eject_request",
            ms=max(0, release_delay),
            callback=self._eject_vuk_if_occupied,
        )

    def _eject_vuk_if_occupied(self):
        vuk_switch = self.machine.switches.get("s_vuk_switch")
        if vuk_switch and self.machine.switch_controller.is_active(vuk_switch):
            self.machine.events.post("up_kick")
        else:
            self.machine.events.post("vuk_eject_skipped_empty")

    def _cancel_vuk_eject_request(self, **kwargs):
        self.delay.remove("shared_vuk_eject_request")
        self.delay.remove("shared_vuk_eject_verify")

    def _up_kick_requested(self, **kwargs):
        """Verify one raw VUK pulse and retry once if the ball remains."""
        self.delay.remove("shared_vuk_eject_request")
        self.delay.reset(
            name="shared_vuk_eject_verify",
            ms=self.VUK_EJECT_VERIFY_MS,
            callback=self._verify_vuk_released,
        )

    def _verify_vuk_released(self, **kwargs):
        vuk_switch = self.machine.switches.get("s_vuk_switch")
        if vuk_switch and self.machine.switch_controller.is_active(vuk_switch):
            self.machine.events.post("up_kick_retry")


    def _mini_wizard_gameplay_finished(self, mini_wizard=None, completed=True, **kwargs):
        """Stop mini-wizard gameplay, show summary, then advance/fail chapter flow.

        Placeholder mini-wizards are intentionally simple right now: they start
        a multiball and complete when that multiball ends. This method keeps the
        chapter flow consistent with villain modes by inserting the bookend
        summary before changing chapters.
        """
        player = self.machine.game.player
        mini_key = mini_wizard or player["mini_wizard_current_key"]

        if not mini_key:
            self.machine.events.post("chapter_mini_wizard_finish_ignored_no_key")
            return

        chapter_number, chapter = self._chapter_for_mini_wizard(mini_key)
        if not chapter:
            self.machine.events.post("chapter_mini_wizard_finish_unknown", mini_wizard=mini_key)
            return

        # Mini-wizards are consumed once played. A failed/ended mini-wizard
        # still counts as complete for progression and will not be replayed
        # during the same game.
        completed = bool(completed)
        player[f"{mini_key}_state"] = self.COMPLETED

        player["mini_wizard_current_key"] = mini_key
        player["villain_mode_running"] = 1
        player["villain_mode_in_summary"] = 1
        player["villain_current_key"] = mini_key
        player["villain_current_name"] = mini_key
        player["villain_mode_running_name"] = mini_key

        self.machine.events.post(
            "chapter_mini_wizard_gameplay_finished",
            mini_wizard=mini_key,
            completed=1 if completed else 0,
        )

        # Arm the controlled chapter-select drain before the summary starts.
        # If the wizard-ending drain reaches the trough during the summary,
        # the transition ball save replaces it without ending the ball, while
        # queue_relay_player holds the trough eject until the summary-complete
        # event below releases it.
        player["chapter_select_waiting_for_summary"] = 1
        self.machine.events.post("chapter_select_pending_drain", chapter_number=chapter_number, chapter_name=chapter["name"])

        self.machine.events.post(f"stop_mode_{mini_key}")

        self.delay.add(
            name=f"{mini_key}_summary_after_mode_stop",
            ms=100,
            callback=lambda: self._request_mini_wizard_summary(mini_key),
        )

        self._restore_state()

    def _request_mini_wizard_summary(self, mini_key):
        self.machine.events.post(
            "villain_bookend_summary_request",
            villain=mini_key,
            done_event=f"{mini_key}_summary_done",
        )

    def _mini_wizard_summary_done(self, mini_wizard=None, **kwargs):
        mini_key = mini_wizard or self.machine.game.player["mini_wizard_current_key"]
        if not mini_key:
            self.machine.events.post("chapter_mini_wizard_summary_ignored_no_key")
            return

        # Once a mini-wizard has been played, it is consumed. The summary result
        # does not decide whether progression advances.
        self._mini_wizard_completed(mini_wizard=mini_key, **kwargs)

    def _mini_wizard_failed(self, mini_wizard=None, **kwargs):
        """Compatibility path: a played mini-wizard is consumed either way."""
        player = self.machine.game.player
        mini_key = mini_wizard or player["mini_wizard_current_key"]

        if not mini_key:
            self.machine.events.post("chapter_mini_wizard_failure_ignored_no_key")
            return

        self.machine.events.post("chapter_mini_wizard_failed_but_consumed", mini_wizard=mini_key)
        self._mini_wizard_completed(mini_wizard=mini_key, **kwargs)

    def _count_current_case_files(self):
        """Return the number of currently collected Case Files for this villain attempt."""
        player = self.machine.game.player
        count = 0
        for key in self.CASE_FILE_KEYS:
            if self._safe_int(player[f"case_file_{key}_collected"], 0) == 1:
                count += 1
        return count

    def _sync_mini_wizard_case_file_bonus(self):
        """Publish the chapter-local Case File bonus used by mini-wizards."""
        player = self.machine.game.player
        collected = self._safe_int(player["chapter_case_files_collected"], 0)
        if collected < 0:
            collected = 0
        if collected > 25:
            collected = 25
            player["chapter_case_files_collected"] = 25

        bonus = collected * self.CASE_FILE_MINI_WIZARD_BONUS
        jackpot = self.MINI_WIZARD_BASE_JACKPOT + bonus
        player["mini_wizard_case_file_bonus_per_file"] = self.CASE_FILE_MINI_WIZARD_BONUS
        player["mini_wizard_case_file_bonus"] = bonus
        player["mini_wizard_base_jackpot"] = self.MINI_WIZARD_BASE_JACKPOT
        player["mini_wizard_jackpot_value"] = jackpot
        player["wizard_prep_summary"] = f"{collected} / 25 CASE FILES   +{bonus:,}"
        player["wizard_prep_next_award"] = f"MINI-WIZARD JACKPOT {jackpot:,}"
        self.machine.events.post(
            "chapter_case_files_status_changed",
            chapter_case_files_collected=player["chapter_case_files_collected"],
            mini_wizard_case_file_bonus=player["mini_wizard_case_file_bonus"],
            mini_wizard_jackpot_value=player["mini_wizard_jackpot_value"],
            wizard_prep_summary=player["wizard_prep_summary"],
            wizard_prep_next_award=player["wizard_prep_next_award"],
        )
        self.machine.events.post("case_files_status_changed")
        self.machine.events.post("daily_bugle_widget_update")

    def _add_villain_case_files_to_chapter_total(self, villain_key):
        """Bank the active Case Files into the current chapter mini-wizard bonus.

        The progression state is the source of truth. A villain can only start
        from NOT_PLAYED, so no per-villain *_case_files_counted_for_chapter
        flag is needed.
        """
        player = self.machine.game.player

        count = self._count_current_case_files()
        player["current_villain_case_files_collected"] = count
        player["chapter_case_files_collected"] = min(25, player["chapter_case_files_collected"] + count)
        self._sync_mini_wizard_case_file_bonus()

        self.machine.events.post(
            "chapter_case_files_bank_villain",
            villain_key=villain_key,
            case_files=count,
            chapter_case_files=player["chapter_case_files_collected"],
            bonus=player["mini_wizard_case_file_bonus"],
            jackpot=player["mini_wizard_jackpot_value"],
        )


    def _reset_chapter_case_file_bonus(self):
        """Reset the chapter-local Case File total after a mini-wizard/chapter ends."""
        player = self.machine.game.player
        player["chapter_case_files_collected"] = 0
        player["current_villain_case_files_collected"] = 0
        self._sync_mini_wizard_case_file_bonus()

        self.machine.events.post("chapter_case_file_bonus_reset")

    def _request_start(self, saucer=None, state=0, max_choices=None, source="", **kwargs):
        """Handle a villain start request from a physical shot.

        villain_start.py should call this instead of deciding chapter contents or
        starting villains itself.
        """
        if (
            self._safe_int(self.machine.game.player["chapter_select_needed"], 0) == 1
            or self._safe_int(self.machine.game.player["chapter_select_active"], 0) == 1
        ):
            self.machine.events.post(
                "villain_start_ignored_chapter_select_active",
                saucer=saucer,
                source=source,
            )
            self.machine.events.post("clear_saucers_delayed")
            return

        state = self._safe_int(state, 0)
        if max_choices is None:
            max_choices = state
        max_choices = self._safe_int(max_choices, state)

        if self._safe_int(self.machine.game.player["final_wizard_ready"], 0) == 1:
            self.machine.events.post("villain_saucer_start_final_wizard", saucer=saucer, source=source)
            self._start_final_wizard()
            return

        if self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) == 1:
            self.machine.events.post("villain_saucer_ignored_mini_wizard_ready", saucer=saucer, source=source)
            self.machine.events.post("villain_mini_wizard_shoot_vuk", saucer=saucer, source=source)
            self.machine.events.post("clear_saucers_delayed")
            self.machine.events.post("reset_drops")
            return

        if state <= 0:
            self.machine.events.post("villain_saucer_points_only", saucer=saucer, source=source)
            # Points-only saucer hits should eject immediately. Only villain
            # select/intro starts should hold the ball.
            self.machine.events.post("clear_saucers_delayed")
            return

        available = self._get_available_villains(limit=max_choices)
        if not available:
            self.machine.events.post("villain_saucer_no_valid_villains", saucer=saucer, state=state, source=source)
            self.machine.events.post("villain_start_request_failed", saucer=saucer, reason="no_valid_villains")
            self._check_chapter_complete()

            if self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) == 1:
                self.machine.events.post("villain_mini_wizard_shoot_vuk", saucer=saucer, source=source)

            self.machine.events.post("clear_saucers_delayed")
            return

        if len(available) == 1:
            villain_key = available[0]
            self.machine.events.post(
                "villain_saucer_start_default",
                saucer=saucer,
                state=state,
                villain_key=villain_key,
                source=source,
            )
            self._start_villain(villain_key)
            return

        self.machine.events.post(
            "villain_saucer_start_select",
            saucer=saucer,
            state=state,
            max_choices=max_choices,
            villain_keys=",".join(available),
            source=source,
        )
        self.machine.events.post(
            "start_mode_villain_select",
            max_choices=max_choices,
            villain_keys=",".join(available),
        )

    def _chapter_selected(self, chapter_number=None, chapter_name="", **kwargs):
        chapter_number = self._safe_int(chapter_number, 0)
        if not self._chapter_is_available(chapter_number):
            self.machine.events.post(
                "chapter_select_rejected_by_progression",
                chapter_number=chapter_number,
                chapter_name=chapter_name,
            )
            return

        player = self.machine.game.player
        player["selected_chapter"] = chapter_number
        player["villain_chapter"] = chapter_number
        player["chapter_select_needed"] = 0
        player["chapter_select_active"] = 0
        player["chapter_select_waiting_for_summary"] = 0

        chapter = self.CHAPTERS[chapter_number - 1]
        self.machine.events.post(
            "villain_chapter_started",
            chapter=chapter["key"],
            chapter_name=chapter["name"],
            chapter_number=chapter_number,
        )
        self.machine.events.post(
            "chapter_comic_selected",
            chapter=chapter["key"],
            chapter_name=chapter["name"],
            chapter_number=chapter_number,
        )
        self._recalculate_progression_from_states(post_events=True)
        self._restore_state()
        self._schedule_case_files_restore(reason="chapter_selected")

    def _sync_chapter_collection_state(self):
        player = self.machine.game.player

        for chapter_number in self.INITIAL_AVAILABLE_CHAPTERS:
            player[f"chapter_{chapter_number}_unlocked"] = 1

        completed_count = 0
        for chapter_number, chapter in enumerate(self.CHAPTERS, start=1):
            mini_key = chapter["mini_wizard_key"]
            if self._normalize_state(player[f"{mini_key}_state"]) == self.COMPLETED:
                player[f"chapter_{chapter_number}_collected"] = 1
                player[f"chapter_{chapter_number}_unlocked"] = 1
                completed_count += 1

        while self._safe_int(player["chapter_unlock_deck_index"], 0) < completed_count:
            if not self._unlock_next_chapter_from_deck():
                break

    def _unlock_next_chapter_from_deck(self):
        player = self.machine.game.player
        index = self._safe_int(player["chapter_unlock_deck_index"], 0)

        while index < len(self.CHAPTER_UNLOCK_DECK):
            chapter_number = self.CHAPTER_UNLOCK_DECK[index]
            index += 1
            player["chapter_unlock_deck_index"] = index
            if self._safe_int(player[f"chapter_{chapter_number}_unlocked"], 0) == 0:
                player[f"chapter_{chapter_number}_unlocked"] = 1
                self.machine.events.post(
                    "chapter_comic_unlocked",
                    chapter_number=chapter_number,
                    chapter_name=self.CHAPTERS[chapter_number - 1]["name"],
                )
                return True

        player["chapter_unlock_deck_index"] = len(self.CHAPTER_UNLOCK_DECK)
        return False

    def _chapter_is_available(self, chapter_number):
        if chapter_number < 1 or chapter_number > len(self.CHAPTERS):
            return False
        player = self.machine.game.player
        return (
            self._safe_int(player[f"chapter_{chapter_number}_unlocked"], 0) == 1
            and self._safe_int(player[f"chapter_{chapter_number}_collected"], 0) == 0
        )

    def _first_available_chapter_number(self):
        for chapter_number in range(1, len(self.CHAPTERS) + 1):
            if self._chapter_is_available(chapter_number):
                return chapter_number
        return None

    def _chapter_for_mini_wizard(self, mini_key):
        for index, chapter in enumerate(self.CHAPTERS, start=1):
            if chapter["mini_wizard_key"] == mini_key:
                return index, chapter
        return None, None

    def _is_mini_wizard_key(self, key):
        if not key:
            return False
        for chapter in self.CHAPTERS:
            if chapter["mini_wizard_key"] == key:
                return True
        return False

    def _schedule_case_files_restore(self, reason=""):
        # Case-file lights can be cleared by summary cleanup/global cleanup.
        # Restore them after the summary/mini-wizard flow has fully released
        # its runtime locks so the CaseFiles mode no longer sees itself locked.
        self.delay.remove("case_files_restore_after_progression_cleanup")
        self.delay.add(
            name="case_files_restore_after_progression_cleanup",
            ms=250,
            callback=lambda: self.machine.events.post("case_files_restore_state", reason=reason),
        )

    def _get_current_chapter(self):
        chapter_num = self._safe_int(self.machine.game.player["villain_chapter"], 1)
        index = chapter_num - 1
        if index < 0 or index >= len(self.CHAPTERS):
            return None
        return self.CHAPTERS[index]

    def _get_available_villains(self, limit=None):
        chapter = self._get_current_chapter()
        if not chapter:
            return []

        available = []
        for key in chapter["villains"]:
            if self._villain_state(key) == self.NOT_PLAYED:
                available.append(key)

        if limit is not None:
            return available[:self._safe_int(limit, len(available))]
        return available

    def _post_available_choices(self, max_choices=5, **kwargs):
        available = self._get_available_villains(limit=max_choices)
        self.machine.events.post(
            "villain_progression_choices_ready",
            max_choices=max_choices,
            available_count=len(available),
            villain_keys=",".join(available),
        )

    def _start_default_villain(self, **kwargs):
        available = self._get_available_villains(limit=1)
        if not available:
            self.machine.events.post("no_villains_available")
            self.machine.events.post("villain_start_request_failed", reason="no_villains_available")
            return
        self._start_villain(available[0])

    def _mystery_start_next_villain(self, **kwargs):
        """Immediately start the next unplayed villain when Mystery awards it."""
        player = self.machine.game.player
        blocked_flags = (
            "villain_mode_running",
            "villain_select_active",
            "chapter_mini_wizard_ready",
            "final_wizard_ready",
            "chapter_select_needed",
            "chapter_select_active",
        )
        if any(self._safe_int(player[name], 0) == 1 for name in blocked_flags):
            self.machine.events.post("mystery_start_next_villain_rejected", reason="start_flow_active")
            return

        available = self._get_available_villains(limit=1)
        if not available:
            self.machine.events.post("mystery_start_next_villain_rejected", reason="no_villains_remaining")
            return

        villain_key = available[0]
        info = self.VILLAINS[villain_key]
        self.machine.events.post(
            "mystery_next_villain_started",
            villain_key=villain_key,
            villain_name=info["name"],
        )
        self.machine.events.post(
            "show_mode_message",
            message=f"STARTING NEXT VILLAIN\n{info['name'].upper()}",
            duration=2,
            priority=200,
        )
        self.delay.remove("mystery_start_next_villain")
        self.delay.add(
            name="mystery_start_next_villain",
            ms=2000,
            callback=self._execute_mystery_start_next_villain,
            villain_key=villain_key,
        )

    def _execute_mystery_start_next_villain(self, villain_key, **kwargs):
        """Start the Mystery-selected villain after its award message is readable."""
        player = self.machine.game.player
        blocked_flags = (
            "villain_mode_running",
            "villain_select_active",
            "chapter_mini_wizard_ready",
            "final_wizard_ready",
            "chapter_select_needed",
            "chapter_select_active",
        )
        if any(self._safe_int(player[name], 0) == 1 for name in blocked_flags):
            self.machine.events.post("mystery_start_next_villain_rejected", reason="start_flow_changed")
            return
        if villain_key not in self._get_available_villains():
            self.machine.events.post("mystery_start_next_villain_rejected", reason="villain_no_longer_available")
            return
        self._start_villain(villain_key)

    def _start_selected_villain(self, villain_key=None, item=None, **kwargs):
        villain_key = villain_key or item
        if not villain_key:
            self.machine.events.post("villain_selection_missing")
            self.machine.events.post("villain_start_request_failed", reason="missing_villain_key")
            return
        if villain_key not in self.VILLAINS:
            self.machine.events.post("villain_selection_invalid", villain_key=villain_key)
            self.machine.events.post("villain_start_request_failed", reason="invalid_villain_key")
            return
        if villain_key not in self._get_available_villains():
            self.machine.events.post("villain_selection_already_played", villain_key=villain_key)
            self.machine.events.post("villain_start_request_failed", reason="already_played", villain_key=villain_key)
            return
        self._start_villain(villain_key)

    def _start_villain(self, villain_key):
        info = self.VILLAINS[villain_key]

        self._add_villain_case_files_to_chapter_total(villain_key)

        # Progression is tracked only by numeric *_state.
        self.machine.game.player[f"{villain_key}_state"] = self.PLAYING
        self.machine.game.player["villain_current_key"] = villain_key
        self.machine.game.player["villain_current_name"] = villain_key
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_mode_running_name"] = villain_key

        self.info_log("VILLAIN START: %s state=%s", villain_key, self.machine.game.player[f"{villain_key}_state"])

        self.machine.events.post("clear_villain_saucer_lights")
        self.machine.events.post("case_files_clear_lights")
        # Do not clear/eject saucers here. The ball that started the villain
        # should stay held during the bookend intro. villain_bookends posts
        # clear_saucers when the intro finishes, right before the start_event.
        self.machine.events.post("villain_started_set", villain_key=villain_key, villain=villain_key)
        self.machine.events.post(
            "villain_mode_started",
            villain_key=villain_key,
            villain_name=info["name"],
        )
        self.machine.events.post(
            "villain_bookend_intro_request",
            villain=villain_key,
            start_event=info["start_event"],
        )
        self._restore_state()

    def _villain_mode_finished(self, villain_key=None, completed=True, **kwargs):
        """Finish gameplay immediately, then show the bookend summary.

        The old flow let each villain mode keep running until its summary was
        dismissed. This method makes the summary a separate bookend step:
        complete/fail event -> stop gameplay mode -> show summary -> cleanup.
        """
        if not villain_key:
            villain_key = self.machine.game.player["villain_current_key"]
        if not villain_key or villain_key not in self.VILLAINS:
            self.machine.events.post("villain_finish_invalid", villain_key=villain_key)
            return

        current_key = self.machine.game.player["villain_current_key"]
        if current_key == self.FINAL_WIZARD_KEY:
            self.machine.events.post("villain_finish_ignored_during_final_wizard", villain_key=villain_key)
            return
        if current_key and current_key != villain_key:
            self.machine.events.post("villain_finish_ignored_wrong_active_villain", villain_key=villain_key, current_key=current_key)
            return

        completed = bool(completed)
        finish_state = self.COMPLETED

        self.machine.game.player[f"{villain_key}_state"] = self.COMPLETED

        # Keep villain_mode_running locked through the summary. The gameplay
        # mode itself is stopping now, but saucer starts / qualify drops should
        # stay blocked until villain_bookends finishes the summary.
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_mode_in_summary"] = 1
        self.machine.game.player["villain_current_key"] = villain_key
        self.machine.game.player["villain_current_name"] = villain_key
        self.machine.game.player["villain_mode_running_name"] = villain_key

        self.machine.events.post(
            "villain_gameplay_finished",
            villain_key=villain_key,
            villain_name=self.VILLAINS[villain_key]["name"],
            completed=1 if completed else 0,
            state=finish_state,
        )

        # Ask MPF to stop the active gameplay mode now. The mode YAML also has
        # the concrete complete/fail events in stop_events, but this keeps the
        # behavior explicit from the single progression pipeline.
        self.machine.events.post(f"stop_mode_{villain_key}")

        # Let mode_stop/widget/show cleanup happen before the summary widget is
        # displayed. This prevents gameplay lights/shows from overlapping the
        # bookend summary.
        self.delay.add(
            name=f"{villain_key}_summary_after_mode_stop",
            ms=100,
            callback=lambda: self._request_summary(villain_key),
        )

        # Recalculate counts for the widget, but do not open the mini-wizard
        # gate until the summary is done. Summary cleanup can reset Daily Bugle
        # state, so _summary_done performs the event-posting recalc.
        self._sync_chapter_ready_flags(post_events=False)
        self._restore_state()

    def _request_summary(self, villain_key):
        self.machine.events.post(
            "villain_bookend_summary_request",
            villain=villain_key,
            done_event=f"{villain_key}_mode_completed_summary",
        )

    def _summary_done(self, villain=None, **kwargs):
        """Release the villain lock after the bookend summary is finished.

        Gameplay modes are already stopped before the summary is shown. This is
        the one official point where case files, saucers, drops, and qualify
        state are reset and the saucer/start system is unlocked again.
        """
        # Mini-wizard summaries use their own concrete <mini>_summary_done
        # event to advance chapters. The generic bookend summary event is
        # posted before that concrete event, so handling it here would restore
        # the old chapter/mini-wizard state and can leave case-file lights
        # locked off when the summary is skipped with flipper cancel.
        if self._is_mini_wizard_key(villain):
            self.machine.events.post("villain_summary_generic_ignored_for_mini_wizard", mini_wizard=villain)
            return

        player = self.machine.game.player if self.machine.game else None

        if player:
            player["villain_mode_running"] = 0
            player["villain_mode_in_summary"] = 0
            player["villain_current_key"] = ""
            player["villain_current_name"] = ""
            player["villain_mode_running_name"] = ""

        self.machine.events.post("villain_full_cleanup", villain_key=villain, villain=villain)
        self.machine.events.post("villain_summary_cleanup_complete", villain_key=villain, villain=villain)
        self.machine.events.post("villain_mode_ended", villain_key=villain, villain=villain)

        # If that summary finished the fifth villain in the chapter, make the
        # chapter mini-wizard immediately available at the Daily Bugle VUK.
        #
        # Important: _villain_mode_finished() recalculates with post_events=False
        # before the summary so the status widget can show the updated chapter
        # count without opening the gate during the bookend. That means
        # chapter_mini_wizard_ready may already be 1 by the time we get here.
        # Reassert the Daily Bugle/VUK-ready state after summary cleanup even if
        # this is not a fresh 0->1 transition; otherwise no gate-open event is
        # posted and the player sees WIZ READY with a closed gate.
        self._check_chapter_complete()
        if (
            self._safe_int(player["chapter_mini_wizard_ready"], 0) == 1
            and self._safe_int(player["chapter_select_needed"], 0) == 0
            and self._safe_int(player["chapter_select_active"], 0) == 0
        ):
            self._mini_wizard_ready_at_daily_bugle(
                post_restore=False,
                reason="villain_summary_done",
            )
        self._restore_state()
        self._schedule_case_files_restore(reason="villain_summary_done")

    def _villain_completed(self, villain_key=None, **kwargs):
        # Compatibility hook for anything that still posts villain_played.
        self._villain_mode_finished(villain_key=villain_key, completed=True, **kwargs)

    def _check_chapter_complete(self):
        self._sync_chapter_ready_flags(post_events=True)

    def _mini_wizard_ready_at_daily_bugle(self, post_restore=True, **kwargs):
        if self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) != 1:
            return

        chapter = self._get_current_chapter()
        if not chapter:
            return

        mini_key = chapter["mini_wizard_key"]

        self.machine.game.player["mini_wizard_daily_bugle_ready"] = 1
        if self._normalize_state(self.machine.game.player[f"{mini_key}_state"]) != self.PLAYING:
            self.machine.game.player[f"{mini_key}_state"] = self.NOT_PLAYED

        self._schedule_mini_wizard_gate_open(reason=kwargs.get("reason", "mini_wizard_ready"))

        self.machine.events.post(
            "chapter_mini_wizard_lit_at_daily_bugle",
            chapter=chapter["key"],
            chapter_name=chapter["name"],
            mini_wizard_key=mini_key,
            mini_wizard_name=chapter["mini_wizard_name"],
        )

        if post_restore:
            self._restore_state()

    def _daily_bugle_hit(self, **kwargs):
        player = self.machine.game.player
        if self._safe_int(player["mini_wizard_daily_bugle_ready"], 0) != 1:
            return
        chapter = self._get_current_chapter()
        if not chapter:
            return
        mini_key = chapter["mini_wizard_key"]
        player["mini_wizard_daily_bugle_ready"] = 0
        player["mini_wizard_vuk_hold_active"] = 1
        player["mini_wizard_current_key"] = mini_key
        player[f"{mini_key}_state"] = self.PLAYING
        player["villain_mode_running"] = 1
        player["villain_current_key"] = mini_key
        player["villain_current_name"] = mini_key
        player["villain_mode_running_name"] = mini_key
        self._sync_mini_wizard_case_file_bonus()
        self.machine.events.post("case_files_clear_lights")
        self.machine.events.post(
            "chapter_mini_wizard_starting",
            chapter=chapter["key"],
            chapter_name=chapter["name"],
            mini_wizard_key=mini_key,
            mini_wizard_name=chapter["mini_wizard_name"],
            chapter_case_files_collected=player["chapter_case_files_collected"],
            case_file_bonus=player["mini_wizard_case_file_bonus"],
            jackpot_value=player["mini_wizard_jackpot_value"],
        )
        self.machine.events.post(
            "villain_bookend_intro_request",
            villain=mini_key,
            start_event=chapter["mini_wizard_event"],
        )
        self._restore_state()

    def _mini_wizard_intro_done(self, villain=None, **kwargs):
        """Release the VUK only after a mini-wizard intro is finished or skipped."""
        player = self.machine.game.player

        if player["mini_wizard_vuk_hold_active"] != 1:
            return

        mini_key = player["mini_wizard_current_key"]
        if not mini_key or villain != mini_key:
            return

        player["mini_wizard_vuk_hold_active"] = 0
        self.machine.events.post("mini_wizard_vuk_intro_done_release", mini_wizard=mini_key)
        self.machine.events.post("up_kick")

    def _mini_wizard_completed(self, mini_wizard=None, **kwargs):
        player = self.machine.game.player

        mini_key = mini_wizard or player["mini_wizard_current_key"]
        if not mini_key:
            self.machine.events.post("chapter_mini_wizard_completion_ignored_no_key")
            return

        chapter_number, chapter = self._chapter_for_mini_wizard(mini_key)
        if not chapter:
            self.machine.events.post("chapter_mini_wizard_completion_unknown", mini_wizard=mini_key)
            return

        if (
            self._safe_int(player[f"chapter_{chapter_number}_collected"], 0) == 1
            and self._safe_int(player["chapter_select_needed"], 0) == 1
        ):
            self._release_chapter_select_summary_hold(mini_wizard=mini_key)
            self.machine.events.post("chapter_mini_wizard_completion_ignored_duplicate", mini_wizard=mini_key)
            return

        self._release_chapter_select_summary_hold(mini_wizard=mini_key)

        player[f"{mini_key}_state"] = self.COMPLETED
        player[f"chapter_{chapter_number}_collected"] = 1
        player[f"chapter_{chapter_number}_unlocked"] = 1
        self._unlock_next_chapter_from_deck()

        self._clear_runtime_flow_flags()

        # The completed comic is now collected. Stop normal progression here and
        # make the next controlled ball-start/shooter-lane state open Chapter
        # Select instead of immediately moving into another chapter.
        player["selected_chapter"] = chapter_number
        player["villain_chapter"] = chapter_number
        player["chapter_select_needed"] = 1
        player["chapter_select_active"] = 0

        self._reset_chapter_case_file_bonus()
        self._recalculate_progression_from_states(post_events=False)

        self._post_global_cleanup_events(reason="mini_wizard_completed")
        self.machine.events.post("chapter_comic_collected", chapter_number=chapter_number, chapter_name=chapter["name"])
        self.machine.events.post("chapter_select_transition_ready", chapter_number=chapter_number, chapter_name=chapter["name"])
        self.machine.events.post("chapter_mini_wizard_ended", mini_wizard=mini_key)
        self.machine.events.post("villain_mode_ended", villain=mini_key, villain_key=mini_key)

        # Let the completed wizard/chapter transition drain safely. Chapter
        # Select will appear at the next ball start/shooter-lane state.
        self.machine.events.post("cmd_flippers_disable")
        self.machine.events.post("cmd_autofire_coils_disable")
        self.machine.events.post("timer_timer_up_post_hold_complete")

        self._restore_state()
        self._schedule_case_files_restore(reason="mini_wizard_completed")

    def _release_chapter_select_summary_hold(self, mini_wizard=None, **kwargs):
        player = self.machine.game.player

        if self._safe_int(player["chapter_select_waiting_for_summary"], 0) != 1:
            return

        player["chapter_select_waiting_for_summary"] = 0
        self.machine.events.post("chapter_select_summary_complete", mini_wizard=mini_wizard)

    def _start_final_wizard(self, **kwargs):
        if self._safe_int(self.machine.game.player["final_wizard_ready"], 0) != 1:
            return
        self.machine.game.player[f"{self.FINAL_WIZARD_KEY}_state"] = self.PLAYING
        self.machine.game.player["villain_current_key"] = self.FINAL_WIZARD_KEY
        self.machine.game.player["villain_current_name"] = self.FINAL_WIZARD_KEY
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_mode_running_name"] = self.FINAL_WIZARD_KEY
        self.machine.events.post("villain_started_set", villain_key=self.FINAL_WIZARD_KEY, villain=self.FINAL_WIZARD_KEY)
        self.machine.events.post("case_files_clear_lights")
        self.machine.events.post(
            "villain_bookend_intro_request",
            villain=self.FINAL_WIZARD_KEY,
            start_event=self.FINAL_WIZARD_EVENT,
        )
        self._restore_state()

    def _final_wizard_gameplay_finished(self, completed=True, **kwargs):
        """Resolve final wizard state."""
        player = self.machine.game.player
        if player["villain_current_key"] != self.FINAL_WIZARD_KEY:
            self.machine.events.post("final_wizard_finish_ignored_wrong_active_mode", current_key=player["villain_current_key"])
            return
        completed = bool(completed)
        player[f"{self.FINAL_WIZARD_KEY}_state"] = self.COMPLETED
        player["final_wizard_ready"] = 0
        player["villain_mode_running"] = 1
        player["villain_mode_in_summary"] = 1
        player["villain_current_key"] = self.FINAL_WIZARD_KEY
        player["villain_current_name"] = self.FINAL_WIZARD_KEY
        player["villain_mode_running_name"] = self.FINAL_WIZARD_KEY
        self.machine.events.post(
            "final_wizard_gameplay_finished",
            villain=self.FINAL_WIZARD_KEY,
            completed=1 if completed else 0,
        )
        self._restore_state()

    def _restore_state(self, **kwargs):
        self._check_chapter_widget_vars()
        available = self._get_available_villains()
        chapter = self._get_current_chapter()
        self.machine.events.post(
            "villain_progression_status",
            chapter_number=self.machine.game.player["villain_chapter"],
            chapter_key=chapter["key"] if chapter else "final_wizard",
            chapter_name=chapter["name"] if chapter else "Final Wizard",
            villains_played_this_chapter=self.machine.game.player["villains_played_this_chapter"],
            available_count=len(available),
            villain_keys=",".join(available),
            mini_wizard_ready=self.machine.game.player["chapter_mini_wizard_ready"],
            mini_wizard_daily_bugle_ready=self.machine.game.player["mini_wizard_daily_bugle_ready"],
            final_wizard_ready=self.machine.game.player["final_wizard_ready"],
            chapter_case_files_collected=self.machine.game.player["chapter_case_files_collected"],
            mini_wizard_case_file_bonus=self.machine.game.player["mini_wizard_case_file_bonus"],
            mini_wizard_jackpot_value=self.machine.game.player["mini_wizard_jackpot_value"],
        )
        self.machine.events.post("villain_chapter_status_changed")

    def _check_chapter_widget_vars(self):
        chapter = self._get_current_chapter()
        if not chapter:
            self.machine.game.player["chapter_current_key"] = "final_wizard"
            self.machine.game.player["chapter_current_name"] = "Final Wizard"
            self.machine.game.player["chapter_mini_wizard_key"] = self.FINAL_WIZARD_KEY
            self.machine.game.player["chapter_mini_wizard_name"] = self.FINAL_WIZARD_NAME
            self.machine.game.player["chapter_mini_wizard_state"] = self._display_state(self.machine.game.player[f"{self.FINAL_WIZARD_KEY}_state"], ready=self.machine.game.player["final_wizard_ready"] == 1)
            for index in range(1, 6):
                self.machine.game.player[f"chapter_villain_{index}_key"] = ""
                self.machine.game.player[f"chapter_villain_{index}_name"] = ""
                self.machine.game.player[f"chapter_villain_{index}_state"] = ""
            return

        self.machine.game.player["chapter_current_key"] = chapter["key"]
        self.machine.game.player["chapter_current_name"] = chapter["name"]
        self.machine.game.player["chapter_mini_wizard_key"] = chapter["mini_wizard_key"]
        self.machine.game.player["chapter_mini_wizard_name"] = chapter["mini_wizard_name"]
        self.machine.game.player["chapter_mini_wizard_state"] = self._display_state(
            self.machine.game.player[f"{chapter['mini_wizard_key']}_state"],
            ready=self.machine.game.player["chapter_mini_wizard_ready"] == 1,
        )

        for index, villain_key in enumerate(chapter["villains"], start=1):
            self.machine.game.player[f"chapter_villain_{index}_key"] = villain_key
            self.machine.game.player[f"chapter_villain_{index}_name"] = self.VILLAINS[villain_key]["name"]
            self.machine.game.player[f"chapter_villain_{index}_state"] = self._display_state(self._villain_state(villain_key))

    def _villain_state(self, villain_key):
        state = self._normalize_state(self.machine.game.player[f"{villain_key}_state"])
        if state == self.COMPLETED:
            return self.COMPLETED
        if state == self.PLAYING:
            return self.PLAYING
        return self.NOT_PLAYED

    def _normalize_state(self, state):
        if state is None:
            return self.NOT_PLAYED

        # New durable format is numeric: 0 not played, 1 playing, 2 completed.
        # Keep the string aliases here so older saved games / older patches do
        # not break if they still contain legacy text state values.
        try:
            value = int(state)
            if value == self.PLAYING:
                return self.PLAYING
            if value == self.COMPLETED:
                return self.COMPLETED
            return self.NOT_PLAYED
        except Exception:
            pass

        text = str(state).strip().lower().replace(" ", "_").replace("-", "_")
        if text in ("1", "playing", "play", "running"):
            return self.PLAYING
        if text in ("2", "completed", "complete", "done", "failed", "fail"):
            return self.COMPLETED
        return self.NOT_PLAYED

    def _display_state(self, state, ready=False):
        if ready:
            return "READY"
        state = self._normalize_state(state)
        if state == self.PLAYING:
            return "PLAYING"
        if state == self.COMPLETED:
            return "COMPLETED"
        return "NOT PLAYED"

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
