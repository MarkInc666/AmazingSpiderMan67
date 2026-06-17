from mpf.core.mode import Mode


class VillainProgression(Mode):
    """Single source of truth for villain chapters, states, and launches.

    Other modes should not keep their own villain lists or start villain modes
    directly. The intended flow is:

        villain_start.py decides that a physical shot is allowed to request a start
        villain_progression.py decides what that request means
        villain_select.py only shows/returns a selected key when choices are needed
        villain_progression.py starts the selected/default villain through bookends

    State wording is also prepared for a future Godot chapter widget:
        NOT PLAYED, PLAYING, COMPLETED
    """

    NOT_PLAYED = "NOT PLAYED"
    PLAYING = "PLAYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    READY = "READY"
    LIT = "LIT"

    CASE_FILE_KEYS = [
        "more_jackpots",
        "more_time",
        "bigger_jackpots",
        "safety_net",
        "shot_assist",
    ]
    CASE_FILE_MINI_WIZARD_BONUS = 25_000
    MINI_WIZARD_BASE_JACKPOT = 50_000

    CHAPTERS = [
        {
            "key": "classic_rogues",
            "name": "Classic Rogues",
            "villains": ['rhino', 'vulture', 'lizard', 'sandman', 'electro'],
            "mini_wizard_key": "sinister_surge",
            "mini_wizard_name": "Sinister Surge",
            "mini_wizard_event": "start_mode_sinister_surge",            
        },
        {
            "key": "masterminds",
            "name": "Masterminds",
            "villains": ['doc_ock', 'mysterio', 'goblin', 'scorpion', 'parafino'],
            "mini_wizard_key": "mastermind_trap",
            "mini_wizard_name": "Mastermind Trap",
            "mini_wizard_event": "start_mode_mastermind_trap",
        },
        {
            "key": "monsters",
            "name": "Monsters",
            "villains": ['centaur', 'cerberus', 'cyclops', 'reptilla', 'mole_man'],
            "mini_wizard_key": "monster_island_breakout",
            "mini_wizard_name": "Monster Island Breakout",
            "mini_wizard_event": "start_mode_monster_island_breakout",
        },
        {
            "key": "crime_wave",
            "name": "Crime Wave",
            "villains": ['enforcers', 'miss_trubble', 'fifth_avenue_phantom', 'frederick_foswell', 'blackwell'],
            "mini_wizard_key": "crime_wave_crackdown",
            "mini_wizard_name": "Crime Wave Crackdown",
            "mini_wizard_event": "start_mode_crime_wave_crackdown",
        },
        {
            "key": "weird_science",
            "name": "Weird Science",
            "villains": ['matto_magneto', 'doctor_manta', 'doctor_dumpty', 'doctor_cool', 'doctor_zapp'],
            "mini_wizard_key": "mad_science_meltdown",
            "mini_wizard_name": "Mad Science Meltdown",
            "mini_wizard_event": "start_mode_mad_science_meltdown",
        },
        {
            "key": "mystic_menace",
            "name": "Mystic Menace",
            "villains": ['fantastic_fakir', 'kotep', 'infinata', 'pardo', 'vulcan'],
            "mini_wizard_key": "fifth_dimension_curse",
            "mini_wizard_name": "Fifth Dimension Curse",
            "mini_wizard_event": "start_mode_fifth_dimension_curse",
        },
        {
            "key": "robot_rampage",
            "name": "Robot Rampage",
            "villains": ['spider_slayer', 'henry_smythe', 'blackbeard_robot', 'executioner_of_paris_robot', 'jesse_james_robot'],
            "mini_wizard_key": "night_of_the_robots",
            "mini_wizard_name": "Night of the Robots",
            "mini_wizard_event": "start_mode_night_of_the_robots",
        },
        {
            "key": "frozen_monster_oddities",
            "name": "Frozen / Monster Oddities",
            "villains": ['snowman_the_snowmen', 'metal_eating_monster', 'master_vine', 'blotto', 'pod'],
            "mini_wizard_key": "nature_strikes_back",
            "mini_wizard_name": "Nature Strikes Back",
            "mini_wizard_event": "start_mode_nature_strikes_back",
        },
        {
            "key": "crime_and_disguise",
            "name": "Crime & Disguise",
            "villains": ['noah_boddy', 'fiddler', 'fly_twins', 'charles_cameo', 'plotter'],
            "mini_wizard_key": "who_is_the_real_villain",
            "mini_wizard_name": "Who Is the Real Villain?",
            "mini_wizard_event": "start_mode_who_is_the_real_villain",
        },
        {
            "key": "time_history_outlaws",
            "name": "Time / History / Outlaws",
            "villains": ['juan_ponce_de_leon', 'devargas', 'koga', 'cowboy', 'desperado'],
            "mini_wizard_key": "time_tossed_showdown",
            "mini_wizard_name": "Time-Tossed Showdown",
            "mini_wizard_event": "start_mode_time_tossed_showdown",
        },
    ]

    VILLAINS = {
        "rhino": {"name": "Rhino", "chapter": 1, "start_event": "start_mode_rhino_bash"},
        "vulture": {"name": "Vulture", "chapter": 1, "start_event": "start_mode_vulture"},
        "lizard": {"name": "Lizard", "chapter": 1, "start_event": "start_mode_lizard"},
        "sandman": {"name": "Sandman", "chapter": 1, "start_event": "start_mode_sandman"},
        "electro": {"name": "Electro", "chapter": 1, "start_event": "start_mode_electro"},
        "doc_ock": {"name": "Doctor Octopus", "chapter": 2, "start_event": "start_mode_doc_ock"},
        "mysterio": {"name": "Mysterio", "chapter": 2, "start_event": "start_mode_mysterio"},
        "goblin": {"name": "Green Goblin", "chapter": 2, "start_event": "start_mode_goblin"},
        "scorpion": {"name": "Scorpion", "chapter": 2, "start_event": "start_mode_scorpion"},
        "parafino": {"name": "Parafino", "chapter": 2, "start_event": "start_mode_parafino"},
        "centaur": {"name": "Centaur", "chapter": 3, "start_event": "start_mode_centaur"},
        "cerberus": {"name": "Cerberus", "chapter": 3, "start_event": "start_mode_cerberus"},
        "cyclops": {"name": "Cyclops", "chapter": 3, "start_event": "start_mode_cyclops"},
        "reptilla": {"name": "Reptilla", "chapter": 3, "start_event": "start_mode_reptilla"},
        "mole_man": {"name": "Mole Man", "chapter": 3, "start_event": "start_mode_mole_man"},
        "enforcers": {"name": "Enforcers", "chapter": 4, "start_event": "start_mode_enforcers"},
        "miss_trubble": {"name": "Miss Trubble", "chapter": 4, "start_event": "start_mode_miss_trubble"},
        "fifth_avenue_phantom": {"name": "Fifth Avenue Phantom", "chapter": 4, "start_event": "start_mode_fifth_avenue_phantom"},
        "frederick_foswell": {"name": "Frederick Foswell", "chapter": 4, "start_event": "start_mode_frederick_foswell"},
        "blackwell": {"name": "Blackwell", "chapter": 4, "start_event": "start_mode_blackwell"},
        "matto_magneto": {"name": "Matto Magneto", "chapter": 5, "start_event": "start_mode_matto_magneto"},
        "doctor_manta": {"name": "Doctor Manta", "chapter": 5, "start_event": "start_mode_doctor_manta"},
        "doctor_dumpty": {"name": "Doctor Dumpty", "chapter": 5, "start_event": "start_mode_doctor_dumpty"},
        "doctor_cool": {"name": "Doctor Cool", "chapter": 5, "start_event": "start_mode_doctor_cool"},
        "doctor_zapp": {"name": "Doctor Zapp", "chapter": 5, "start_event": "start_mode_doctor_zapp"},
        "fantastic_fakir": {"name": "Fantastic Fakir", "chapter": 6, "start_event": "start_mode_fantastic_fakir"},
        "kotep": {"name": "Kotep", "chapter": 6, "start_event": "start_mode_kotep"},
        "infinata": {"name": "Infinata", "chapter": 6, "start_event": "start_mode_infinata"},
        "pardo": {"name": "Pardo", "chapter": 6, "start_event": "start_mode_pardo"},
        "vulcan": {"name": "Vulcan", "chapter": 6, "start_event": "start_mode_vulcan"},
        "spider_slayer": {"name": "Spider-Slayer", "chapter": 7, "start_event": "start_mode_spider_slayer"},
        "henry_smythe": {"name": "Henry Smythe", "chapter": 7, "start_event": "start_mode_henry_smythe"},
        "blackbeard_robot": {"name": "Blackbeard Robot", "chapter": 7, "start_event": "start_mode_blackbeard_robot"},
        "executioner_of_paris_robot": {"name": "Executioner of Paris Robot", "chapter": 7, "start_event": "start_mode_executioner_of_paris_robot"},
        "jesse_james_robot": {"name": "Jesse James Robot", "chapter": 7, "start_event": "start_mode_jesse_james_robot"},
        "snowman_the_snowmen": {"name": "Snowman / The Snowmen", "chapter": 8, "start_event": "start_mode_snowman_the_snowmen"},
        "metal_eating_monster": {"name": "Metal-Eating Monster", "chapter": 8, "start_event": "start_mode_metal_eating_monster"},
        "master_vine": {"name": "Master Vine", "chapter": 8, "start_event": "start_mode_master_vine"},
        "blotto": {"name": "Blotto", "chapter": 8, "start_event": "start_mode_blotto"},
        "pod": {"name": "Pod", "chapter": 8, "start_event": "start_mode_pod"},
        "noah_boddy": {"name": "Noah Boddy", "chapter": 9, "start_event": "start_mode_noah_boddy"},
        "fiddler": {"name": "Fiddler", "chapter": 9, "start_event": "start_mode_fiddler"},
        "fly_twins": {"name": "Fly Twins", "chapter": 9, "start_event": "start_mode_fly_twins"},
        "charles_cameo": {"name": "Charles Cameo", "chapter": 9, "start_event": "start_mode_charles_cameo"},
        "plotter": {"name": "Plotter", "chapter": 9, "start_event": "start_mode_plotter"},
        "juan_ponce_de_leon": {"name": "Juan Ponce de León", "chapter": 10, "start_event": "start_mode_juan_ponce_de_leon"},
        "devargas": {"name": "DeVargas", "chapter": 10, "start_event": "start_mode_devargas"},
        "koga": {"name": "Koga", "chapter": 10, "start_event": "start_mode_koga"},
        "cowboy": {"name": "Cowboy", "chapter": 10, "start_event": "start_mode_cowboy"},
        "desperado": {"name": "Desperado", "chapter": 10, "start_event": "start_mode_desperado"},
    }

    FINAL_WIZARD_KEY = "kingpin"
    FINAL_WIZARD_NAME = "Kingpin"
    FINAL_WIZARD_EVENT = "start_mode_kingpin"

    # These are the events posted by the individual villain modes when their
    # gameplay is finished. Progression owns the next step: mark state, stop the
    # gameplay mode, then ask villain_bookends to show the summary.
    COMPLETION_EVENTS = {
        "rhino_bash_complete": ("rhino", True),
        "rhino_mode_complete": ("rhino", True),
        "rhino_mode_failed": ("rhino", False),
        "vulture_mode_complete": ("vulture", True),
        "vulture_mode_failed": ("vulture", False),
        "lizard_mode_complete": ("lizard", True),
        "lizard_mode_failed": ("lizard", False),
        "sandman_mode_complete": ("sandman", True),
        "sandman_mode_failed": ("sandman", False),
        "electro_mode_complete": ("electro", True),
        "electro_mode_failed": ("electro", False),
        "doc_ock_mode_complete": ("doc_ock", True),
        "doc_ock_mode_failed": ("doc_ock", False),
        "mysterio_mode_complete": ("mysterio", True),
        "mysterio_mode_failed": ("mysterio", False),
        "goblin_mode_complete": ("goblin", True),
        "goblin_mode_failed": ("goblin", False),
        "scorpion_mode_complete": ("scorpion", True),
        "scorpion_mode_failed": ("scorpion", False),
        "parafino_mode_complete": ("parafino", True),
        "parafino_mode_failed": ("parafino", False),
        "centaur_mode_complete": ("centaur", True),
        "centaur_mode_failed": ("centaur", False),
        "cerberus_mode_complete": ("cerberus", True),
        "cerberus_mode_failed": ("cerberus", False),
        "cyclops_mode_complete": ("cyclops", True),
        "cyclops_mode_failed": ("cyclops", False),
        "reptilla_mode_complete": ("reptilla", True),
        "reptilla_mode_failed": ("reptilla", False),
        "mole_man_mode_complete": ("mole_man", True),
        "mole_man_mode_failed": ("mole_man", False),
        "enforcers_mode_complete": ("enforcers", True),
        "enforcers_mode_failed": ("enforcers", False),
        "miss_trubble_mode_complete": ("miss_trubble", True),
        "miss_trubble_mode_failed": ("miss_trubble", False),
        "fifth_avenue_phantom_mode_complete": ("fifth_avenue_phantom", True),
        "fifth_avenue_phantom_mode_failed": ("fifth_avenue_phantom", False),
        "frederick_foswell_mode_complete": ("frederick_foswell", True),
        "frederick_foswell_mode_failed": ("frederick_foswell", False),
        "blackwell_mode_complete": ("blackwell", True),
        "blackwell_mode_failed": ("blackwell", False),
        "matto_magneto_mode_complete": ("matto_magneto", True),
        "matto_magneto_mode_failed": ("matto_magneto", False),
        "doctor_manta_mode_complete": ("doctor_manta", True),
        "doctor_manta_mode_failed": ("doctor_manta", False),
        "doctor_dumpty_mode_complete": ("doctor_dumpty", True),
        "doctor_dumpty_mode_failed": ("doctor_dumpty", False),
        "doctor_cool_mode_complete": ("doctor_cool", True),
        "doctor_cool_mode_failed": ("doctor_cool", False),
        "doctor_zapp_mode_complete": ("doctor_zapp", True),
        "doctor_zapp_mode_failed": ("doctor_zapp", False),
        "fantastic_fakir_mode_complete": ("fantastic_fakir", True),
        "fantastic_fakir_mode_failed": ("fantastic_fakir", False),
        "kotep_mode_complete": ("kotep", True),
        "kotep_mode_failed": ("kotep", False),
        "infinata_mode_complete": ("infinata", True),
        "infinata_mode_failed": ("infinata", False),
        "pardo_mode_complete": ("pardo", True),
        "pardo_mode_failed": ("pardo", False),
        "vulcan_mode_complete": ("vulcan", True),
        "vulcan_mode_failed": ("vulcan", False),
        "spider_slayer_mode_complete": ("spider_slayer", True),
        "spider_slayer_mode_failed": ("spider_slayer", False),
        "henry_smythe_mode_complete": ("henry_smythe", True),
        "henry_smythe_mode_failed": ("henry_smythe", False),
        "blackbeard_robot_mode_complete": ("blackbeard_robot", True),
        "blackbeard_robot_mode_failed": ("blackbeard_robot", False),
        "executioner_of_paris_robot_mode_complete": ("executioner_of_paris_robot", True),
        "executioner_of_paris_robot_mode_failed": ("executioner_of_paris_robot", False),
        "jesse_james_robot_mode_complete": ("jesse_james_robot", True),
        "jesse_james_robot_mode_failed": ("jesse_james_robot", False),
        "snowman_the_snowmen_mode_complete": ("snowman_the_snowmen", True),
        "snowman_the_snowmen_mode_failed": ("snowman_the_snowmen", False),
        "metal_eating_monster_mode_complete": ("metal_eating_monster", True),
        "metal_eating_monster_mode_failed": ("metal_eating_monster", False),
        "master_vine_mode_complete": ("master_vine", True),
        "master_vine_mode_failed": ("master_vine", False),
        "blotto_mode_complete": ("blotto", True),
        "blotto_mode_failed": ("blotto", False),
        "pod_mode_complete": ("pod", True),
        "pod_mode_failed": ("pod", False),
        "noah_boddy_mode_complete": ("noah_boddy", True),
        "noah_boddy_mode_failed": ("noah_boddy", False),
        "fiddler_mode_complete": ("fiddler", True),
        "fiddler_mode_failed": ("fiddler", False),
        "fly_twins_mode_complete": ("fly_twins", True),
        "fly_twins_mode_failed": ("fly_twins", False),
        "charles_cameo_mode_complete": ("charles_cameo", True),
        "charles_cameo_mode_failed": ("charles_cameo", False),
        "plotter_mode_complete": ("plotter", True),
        "plotter_mode_failed": ("plotter", False),
        "juan_ponce_de_leon_mode_complete": ("juan_ponce_de_leon", True),
        "juan_ponce_de_leon_mode_failed": ("juan_ponce_de_leon", False),
        "devargas_mode_complete": ("devargas", True),
        "devargas_mode_failed": ("devargas", False),
        "koga_mode_complete": ("koga", True),
        "koga_mode_failed": ("koga", False),
        "cowboy_mode_complete": ("cowboy", True),
        "cowboy_mode_failed": ("cowboy", False),
        "desperado_mode_complete": ("desperado", True),
        "desperado_mode_failed": ("desperado", False),
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.villain_progression_logic_active = True
        self._ensure_player_vars()

        # Ball start is the one safe place to reassert progression-owned state.
        # Do not rely on modes that were stopping during ball_ending to have
        # received or handled every cleanup event.
        self._force_safe_ball_start_state()

        self._add_handlers()

        # Central saucer clearing lives here because villain_progression is
        # active during normal gameplay. This lets clear_saucers only pulse
        # saucer kickout coils when the matching saucer switch is actually active.
        self.add_mode_event_handler("clear_saucers", self._clear_saucers)
        self.add_mode_event_handler("clear_saucers_delayed", self._clear_saucers_delayed)

        self._restore_state()

    def mode_stop(self, **kwargs):
        # ball_ending can stop villain modes in any order. Progression owns the
        # player-state cleanup here so the next ball does not inherit stale locks.
        self._finalize_active_flow_on_mode_stop()
        self.villain_progression_logic_active = False
        super().mode_stop(**kwargs)

    def _force_safe_ball_start_state(self):
        """Reassert a sane progression state at the start of each ball.

        This intentionally does not reset permanent progress such as completed
        villains, completed mini-wizards, current chapter, or collected case
        files. It only cleans transient runtime state that may have been left
        behind by modes shutting down during ball_ending.
        """
        player = self.machine.game.player

        self._mark_stale_playing_items_failed()
        self._clear_runtime_flow_flags()
        self._clear_active_case_file_helpers()
        self._sync_chapter_ready_flags(post_events=False)

        # Make sure ball-start lights/hardware are not showing stale villain
        # state. These are global cleanup requests, not mode-specific requests.
        self._post_global_cleanup_events(reason="ball_start")

        self.machine.events.post(
            "villain_progression_ball_start_sanitized",
            chapter_number=player["villain_chapter"],
        )

    def _finalize_active_flow_on_mode_stop(self):
        """Force runtime cleanup when this mode stops at ball_ending.

        Individual villain modes may already be stopping and may not respond to
        events. This method updates progression-owned player vars directly and
        posts only global cleanup events.
        """
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return

        self._mark_stale_playing_items_failed()
        self._clear_runtime_flow_flags()
        self._clear_active_case_file_helpers()
        self._sync_chapter_ready_flags(post_events=False)
        self._post_global_cleanup_events(reason="ball_end")

    def _mark_stale_playing_items_failed(self):
        """Resolve any item that was still PLAYING when the ball ended.

        This is deliberately progression-owned. It does not ask the gameplay
        mode to fail itself because that mode may already be stopped.

        Villain attempts remain resolved by played state. Mini-wizards are
        different: once a mini-wizard has actually started, it is consumed for
        the game. If ball end stops it before its normal summary/completion
        event chain, progression still marks that mini-wizard complete and
        advances to the next chapter.
        """
        player = self.machine.game.player

        for villain_key, info in self.VILLAINS.items():
            if player[f"{villain_key}_state"] == self.PLAYING:
                player[f"{villain_key}_completed"] = 0
                player[f"{villain_key}_played"] = 1
                player[f"{villain_key}_state"] = self.FAILED
                self.machine.events.post(
                    "villain_gameplay_abandoned",
                    villain_key=villain_key,
                    villain_name=info["name"],
                )

        for chapter_number, chapter in enumerate(self.CHAPTERS, start=1):
            mini_key = chapter["mini_wizard_key"]
            if player[f"{mini_key}_state"] == self.PLAYING:
                self._consume_started_mini_wizard_on_ball_end(mini_key, chapter_number)

            # If the ball ended while Daily Bugle was lit for a mini-wizard,
            # it was not yet played. Return it to READY so the player can still
            # start the already-earned mini-wizard on the next ball.
            if player[f"{mini_key}_state"] == self.LIT:
                player[f"{mini_key}_state"] = self.READY

        if player["final_wizard_state"] == self.PLAYING:
            player["final_wizard_state"] = self.COMPLETED
            player["final_wizard_ready"] = 0
            self.machine.events.post("final_wizard_abandoned_but_consumed")

    def _consume_started_mini_wizard_on_ball_end(self, mini_key, chapter_number):
        """Treat a started mini-wizard as completed if ball end stops it."""
        player = self.machine.game.player

        if player[f"{mini_key}_completed"] == 1 and player["villain_chapter"] > chapter_number:
            return

        player[f"{mini_key}_completed"] = 1
        player[f"{mini_key}_state"] = self.COMPLETED
        player["mini_wizards_completed"] += 1
        player["villains_played_this_chapter"] = 0
        player["chapter_mini_wizard_ready"] = 0
        player["mini_wizard_daily_bugle_ready"] = 0
        player["villain_chapter"] = max(player["villain_chapter"], chapter_number + 1)
        self._reset_chapter_case_file_bonus()

        self.machine.events.post(
            "chapter_mini_wizard_abandoned_but_consumed",
            mini_wizard=mini_key,
            next_chapter=player["villain_chapter"],
        )

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

    def _post_global_cleanup_events(self, reason=""):
        self.machine.events.post("villain_full_cleanup", reason=reason)
        self.machine.events.post("case_files_clear_lights", reason=reason)
        self.machine.events.post("clear_villain_saucer_lights", reason=reason)
        self.machine.events.post("timer_timer_up_post_hold_complete", reason=reason)
        self.machine.events.post("villain_mode_ended", villain_key="", villain="", reason=reason)

    def _sync_chapter_ready_flags(self, post_events=True):
        """Recompute chapter/mini-wizard readiness from durable progress."""
        player = self.machine.game.player
        chapter = self._get_current_chapter()

        if chapter is None:
            player["chapter_mini_wizard_ready"] = 0
            player["mini_wizard_daily_bugle_ready"] = 0
            player["final_wizard_ready"] = 1
            player["final_wizard_state"] = self.READY
            if post_events:
                self.machine.events.post("final_wizard_ready")
            return

        player["final_wizard_ready"] = 0
        if player["final_wizard_state"] == self.READY:
            player["final_wizard_state"] = self.NOT_PLAYED

        resolved_count = 0
        for key in chapter["villains"]:
            if self._villain_state(key) in (self.COMPLETED, self.FAILED):
                resolved_count += 1

        player["villains_played_this_chapter"] = resolved_count
        mini_key = chapter["mini_wizard_key"]
        required = len(chapter["villains"])

        if resolved_count >= required and player[f"{mini_key}_completed"] == 0:
            was_ready = player["chapter_mini_wizard_ready"] == 1
            player["chapter_mini_wizard_ready"] = 1
            if player["mini_wizard_daily_bugle_ready"] == 1:
                player[f"{mini_key}_state"] = self.LIT
            elif player[f"{mini_key}_state"] != self.PLAYING:
                player[f"{mini_key}_state"] = self.READY

            if post_events and not was_ready:
                self.machine.events.post(
                    "chapter_mini_wizard_ready",
                    chapter=chapter["key"],
                    chapter_name=chapter["name"],
                    mini_wizard_key=mini_key,
                    mini_wizard_name=chapter["mini_wizard_name"],
                    mini_wizard_event=chapter["mini_wizard_event"],
                )
            return

        player["chapter_mini_wizard_ready"] = 0
        player["mini_wizard_daily_bugle_ready"] = 0
        if player[f"{mini_key}_completed"] == 0 and player[f"{mini_key}_state"] in (self.READY, self.LIT):
            player[f"{mini_key}_state"] = self.NOT_PLAYED

    SAUCER_EJECT_DELAY_MS = 750
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

        for saucer_number, (switch_name, kickout_event) in self.SAUCER_EJECTS.items():
            active = self.machine.switch_controller.is_active(self.machine.switches[switch_name])
            self.info_log("Saucer check %s active=%s", switch_name, active)

            if active:
                self.info_log("Posting %s from clear_saucers", kickout_event)
                self.machine.events.post(kickout_event)

    def _delayed_kickout_saucer(self, saucer_number, **kwargs):
        """Public delayed kickout event for modes that hold/release saucers."""
        if str(saucer_number) not in self.SAUCER_EJECTS:
            self.warning_log("Unknown delayed saucer kickout requested: %s", saucer_number)
            return

        delay_name = f"delayed_kickout_saucer_{saucer_number}"
        self.delay.remove(delay_name)
        self.delay.add(
            name=delay_name,
            ms=self.SAUCER_EJECT_DELAY_MS,
            callback=self._kickout_saucer_if_occupied,
            saucer_number=str(saucer_number),
        )

    def _kickout_saucer_if_occupied(self, saucer_number, **kwargs):
        switch_name, kickout_event = self.SAUCER_EJECTS[str(saucer_number)]
        active = self.machine.switch_controller.is_active(self.machine.switches[switch_name])
        self.info_log("Delayed saucer %s eject check %s active=%s", saucer_number, switch_name, active)

        if active:
            self.machine.events.post(kickout_event)
        else:
            self.machine.events.post("delayed_saucer_kickout_skipped_empty", saucer=saucer_number)

    def _add_handlers(self):
        # Public API for the rest of the game.
        self.add_mode_event_handler("villain_progression_request_start", self._request_start)
        self.add_mode_event_handler("villain_progression_request_choices", self._post_available_choices)
        self.add_mode_event_handler("villain_progression_start_default", self._start_default_villain)
        self.add_mode_event_handler("villain_progression_start_selected", self._start_selected_villain)
        self.add_mode_event_handler("villain_select_choice_made", self._start_selected_villain)
        self.add_mode_event_handler("villain_progression_start_final_wizard", self._start_final_wizard)
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
        self.add_mode_event_handler("chapter_mini_wizard_failed", self._mini_wizard_failed)

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
                f"{mini_key}_mode_failed",
                self._mini_wizard_gameplay_finished,
                mini_wizard=mini_key,
                completed=False,
            )
            self.add_mode_event_handler(
                f"{mini_key}_summary_done",
                self._mini_wizard_summary_done,
                mini_wizard=mini_key,
            )

        self.add_mode_event_handler("mini_wizard_start_ready_at_daily_bugle", self._mini_wizard_ready_at_daily_bugle)
        self.add_mode_event_handler("s_vuk_switch_active", self._daily_bugle_hit)
        self.add_mode_event_handler("villain_bookend_intro_done", self._mini_wizard_intro_done)

        # Delayed saucer eject API. Raw kickout_saucer_* events still exist for
        # explicit immediate coil tests/manual use, but gameplay modes should use
        # these so saucer releases don't stack on top of other high-current events.
        self.add_mode_event_handler("delayed_kickout_saucer_1", self._delayed_kickout_saucer, saucer_number="1")
        self.add_mode_event_handler("delayed_kickout_saucer_2", self._delayed_kickout_saucer, saucer_number="2")
        self.add_mode_event_handler("delayed_kickout_saucer_3", self._delayed_kickout_saucer, saucer_number="3")
        self.add_mode_event_handler("clear_saucers_now", self._clear_saucers_now)


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
        player[f"{mini_key}_completed"] = 1
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

    def _ensure_player_vars(self):
        defaults = {
            "villain_chapter": 1,
            "villains_played_this_chapter": 0,
            "villains_played_total": 0,
            "chapter_mini_wizard_ready": 0,
            "mini_wizard_daily_bugle_ready": 0,
            "final_wizard_ready": 0,
            "villain_current_key": "",
            "villain_current_name": "",
            "villain_mode_running": 0,
            "villain_mode_running_name": "",
            "villain_mode_in_summary": 0,
            "mini_wizard_current_key": "",
            "mini_wizard_vuk_hold_active": 0,
            "mini_wizards_completed": 0,
            "chapter_case_files_collected": 0,
            "current_villain_case_files_collected": 0,
            "mini_wizard_case_file_bonus_per_file": self.CASE_FILE_MINI_WIZARD_BONUS,
            "mini_wizard_case_file_bonus": 0,
            "mini_wizard_base_jackpot": self.MINI_WIZARD_BASE_JACKPOT,
            "mini_wizard_jackpot_value": self.MINI_WIZARD_BASE_JACKPOT,
            "villain_select_active": 0,
            "active_case_file_helper_count": 0,
            "active_case_file_helper_1": "",
            "active_case_file_helper_2": "",
            "active_case_file_helper_3": "",
            "active_case_file_helper_4": "",
            "active_case_file_helper_5": "",
            "final_wizard_state": self.NOT_PLAYED,
        }
        for name, value in defaults.items():
            if self._get_player_var(name, None) is None:
                self.machine.game.player[name] = value

        for key in self.VILLAINS:
            if self._get_player_var(f"{key}_played", None) is None:
                self.machine.game.player[f"{key}_played"] = 0
            if self._get_player_var(f"{key}_completed", None) is None:
                self.machine.game.player[f"{key}_completed"] = 0
            if self._get_player_var(f"{key}_state", None) is None:
                self.machine.game.player[f"{key}_state"] = self.NOT_PLAYED
            if self._get_player_var(f"{key}_case_files_counted_for_chapter", None) is None:
                self.machine.game.player[f"{key}_case_files_counted_for_chapter"] = 0

        self._sync_mini_wizard_case_file_bonus()

        for chapter in self.CHAPTERS:
            mini_key = chapter["mini_wizard_key"]
            if self._get_player_var(f"{mini_key}_completed", None) is None:
                self.machine.game.player[f"{mini_key}_completed"] = 0
            if self._get_player_var(f"{mini_key}_state", None) is None:
                self.machine.game.player[f"{mini_key}_state"] = self.NOT_PLAYED

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
        player["mini_wizard_case_file_bonus_per_file"] = self.CASE_FILE_MINI_WIZARD_BONUS
        player["mini_wizard_case_file_bonus"] = bonus
        player["mini_wizard_base_jackpot"] = self.MINI_WIZARD_BASE_JACKPOT
        player["mini_wizard_jackpot_value"] = self.MINI_WIZARD_BASE_JACKPOT + bonus

    def _add_villain_case_files_to_chapter_total(self, villain_key):
        """Bank this villain's Case Files into the current chapter mini-wizard bonus.

        Case Files are locked once a villain starts, and villain_full_cleanup
        resets the active Case File set later. So the correct accounting point
        is the progression-owned villain start path.
        """
        player = self.machine.game.player
        counted_var = f"{villain_key}_case_files_counted_for_chapter"

        if player[counted_var] == 1:
            self._sync_mini_wizard_case_file_bonus()
            return

        count = self._count_current_case_files()
        player["current_villain_case_files_collected"] = count
        player["chapter_case_files_collected"] = min(25, player["chapter_case_files_collected"] + count)
        player[counted_var] = 1
        self._sync_mini_wizard_case_file_bonus()

        self.machine.events.post(
            "chapter_case_files_bank_villain",
            villain_key=villain_key,
            case_files=count,
            chapter_case_files=player["chapter_case_files_collected"],
            bonus=player["mini_wizard_case_file_bonus"],
            jackpot=player["mini_wizard_jackpot_value"],
        )

        if count > 0:
            self.machine.events.post(
                "show_mode_message",
                title="CASE FILES BANKED",
                subtitle=f"{player['chapter_case_files_collected']} / 25  +{player['mini_wizard_case_file_bonus']:,}",
            )

    def _reset_chapter_case_file_bonus(self):
        """Reset the chapter-local Case File total after a mini-wizard/chapter ends."""
        player = self.machine.game.player
        player["chapter_case_files_collected"] = 0
        player["current_villain_case_files_collected"] = 0
        self._sync_mini_wizard_case_file_bonus()

        chapter = self._get_current_chapter()
        if chapter:
            for villain_key in chapter["villains"]:
                player[f"{villain_key}_case_files_counted_for_chapter"] = 0

        self.machine.events.post("chapter_case_file_bonus_reset")

    def _request_start(self, saucer=None, state=0, max_choices=None, source="", **kwargs):
        """Handle a villain start request from a physical shot.

        villain_start.py should call this instead of deciding chapter contents or
        starting villains itself.
        """
        state = self._safe_int(state, 0)
        if max_choices is None:
            max_choices = state
        max_choices = self._safe_int(max_choices, state)

        if self._safe_int(self.machine.game.player["final_wizard_ready"], 0) == 1:
            self.machine.events.post("villain_saucer_start_final_wizard", saucer=saucer, source=source)
            self._start_final_wizard()
            return

        if self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) == 1:
            self.machine.events.post("villain_saucer_lights_daily_bugle_for_mini_wizard", saucer=saucer, source=source)
            self._mini_wizard_ready_at_daily_bugle()
            # Saucer has done its job: light Daily Bugle and release the ball
            # so the player can shoot the VUK to start the mini-wizard.
            self.machine.events.post("clear_saucers_delayed")
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

            # If the missing-villain condition just readied the mini-wizard,
            # use this same saucer hit to light Daily Bugle and release the ball.
            if self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) == 1:
                self.machine.events.post("villain_saucer_lights_daily_bugle_for_mini_wizard", saucer=saucer, source=source)
                self._mini_wizard_ready_at_daily_bugle()

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

        # Set both the new state vars and the older *_played vars. The played
        # bit means "do not offer this villain again." Completion is tracked
        # separately with *_completed and *_state == COMPLETED.
        self.machine.game.player[f"{villain_key}_played"] = 1
        self.machine.game.player[f"{villain_key}_state"] = self.PLAYING
        self.machine.game.player["villain_current_key"] = villain_key
        self.machine.game.player["villain_current_name"] = villain_key
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_mode_running_name"] = villain_key

        self.info_log("VILLAIN START: %s state=%s played=%s", villain_key, self.machine.game.player[f"{villain_key}_state"], self.machine.game.player[f"{villain_key}_played"])

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

        completed = bool(completed)
        finish_state = self.COMPLETED if completed else self.FAILED

        self.machine.game.player[f"{villain_key}_completed"] = 1 if completed else 0
        self.machine.game.player[f"{villain_key}_played"] = 1
        self.machine.game.player[f"{villain_key}_state"] = finish_state

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

        self._check_chapter_complete()
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
        # Do this after villain_bookends has posted reset_daily_bugle_state so
        # the gate/open state is not immediately wiped out by summary cleanup.
        self._check_chapter_complete()
        if self.machine.game.player["chapter_mini_wizard_ready"] == 1:
            self._mini_wizard_ready_at_daily_bugle()

        self._restore_state()
        self._schedule_case_files_restore(reason="villain_summary_done")

    def _villain_completed(self, villain_key=None, **kwargs):
        # Compatibility hook for anything that still posts villain_played.
        self._villain_mode_finished(villain_key=villain_key, completed=True, **kwargs)

    def _check_chapter_complete(self):
        self._sync_chapter_ready_flags(post_events=True)

    def _mini_wizard_ready_at_daily_bugle(self, **kwargs):
        if self._safe_int(self.machine.game.player["chapter_mini_wizard_ready"], 0) != 1:
            return

        chapter = self._get_current_chapter()
        if not chapter:
            return

        mini_key = chapter["mini_wizard_key"]

        self.machine.game.player["mini_wizard_daily_bugle_ready"] = 1
        self.machine.game.player[f"{mini_key}_state"] = self.LIT

        self.machine.events.post("rooftop_diverter_open")
        self.machine.events.post("villain_mini_wizard_gate_opened")

        self.machine.events.post(
            "chapter_mini_wizard_lit_at_daily_bugle",
            chapter=chapter["key"],
            chapter_name=chapter["name"],
            mini_wizard_key=mini_key,
            mini_wizard_name=chapter["mini_wizard_name"],
        )

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
            "show_mode_message",
            title="CASE FILE BONUS",
            subtitle=f"{player['chapter_case_files_collected']} / 25  +{player['mini_wizard_case_file_bonus']:,}",
        )
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

        # Use the concrete mini-wizard key from the handler or the key recorded
        # when Daily Bugle/VUK started the mini-wizard. Do not fall back to the
        # current chapter here, because duplicate generic completion events can
        # arrive after the chapter has already advanced.
        mini_key = mini_wizard or player["mini_wizard_current_key"]
        if not mini_key:
            self.machine.events.post("chapter_mini_wizard_completion_ignored_no_key")
            return

        chapter_number, chapter = self._chapter_for_mini_wizard(mini_key)
        if not chapter:
            self.machine.events.post("chapter_mini_wizard_completion_unknown", mini_wizard=mini_key)
            return

        # Ignore duplicates from modes that post both <key>_mode_complete and
        # chapter_mini_wizard_completed.
        if player[f"{mini_key}_completed"] == 1 and player["villain_chapter"] > chapter_number:
            self.machine.events.post("chapter_mini_wizard_completion_ignored_duplicate", mini_wizard=mini_key)
            return

        player[f"{mini_key}_completed"] = 1
        player[f"{mini_key}_state"] = self.COMPLETED
        player["mini_wizards_completed"] += 1

        self._clear_runtime_flow_flags()

        # Move to the chapter after the mini-wizard's actual chapter. This is
        # safer than incrementing the currently-displayed chapter because the
        # current chapter can be stale during cleanup/duplicate events.
        player["villains_played_this_chapter"] = 0
        player["chapter_mini_wizard_ready"] = 0
        player["mini_wizard_daily_bugle_ready"] = 0
        player["villain_chapter"] = chapter_number + 1
        self._reset_chapter_case_file_bonus()

        next_chapter = self._get_current_chapter()
        if next_chapter is None:
            player["final_wizard_ready"] = 1
            player["final_wizard_state"] = self.READY
            self.machine.events.post("final_wizard_ready")
        else:
            player["final_wizard_ready"] = 0
            self.machine.events.post(
                "villain_chapter_started",
                chapter=next_chapter["key"],
                chapter_name=next_chapter["name"],
                chapter_number=player["villain_chapter"],
            )

        self._post_global_cleanup_events(reason="mini_wizard_completed")
        self.machine.events.post("chapter_mini_wizard_ended", mini_wizard=mini_key)
        self.machine.events.post("villain_mode_ended", villain=mini_key, villain_key=mini_key)
        self._restore_state()
        self._schedule_case_files_restore(reason="mini_wizard_completed")

    def _start_final_wizard(self, **kwargs):
        if self._safe_int(self.machine.game.player["final_wizard_ready"], 0) != 1:
            return
        self.machine.game.player["final_wizard_state"] = self.PLAYING
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
            self.machine.game.player["chapter_mini_wizard_state"] = self.machine.game.player["final_wizard_state"]
            for index in range(1, 6):
                self.machine.game.player[f"chapter_villain_{index}_key"] = ""
                self.machine.game.player[f"chapter_villain_{index}_name"] = ""
                self.machine.game.player[f"chapter_villain_{index}_state"] = ""
            return

        self.machine.game.player["chapter_current_key"] = chapter["key"]
        self.machine.game.player["chapter_current_name"] = chapter["name"]
        self.machine.game.player["chapter_mini_wizard_key"] = chapter["mini_wizard_key"]
        self.machine.game.player["chapter_mini_wizard_name"] = chapter["mini_wizard_name"]
        self.machine.game.player["chapter_mini_wizard_state"] = self.machine.game.player[f"{chapter['mini_wizard_key']}_state"]

        for index, villain_key in enumerate(chapter["villains"], start=1):
            self.machine.game.player[f"chapter_villain_{index}_key"] = villain_key
            self.machine.game.player[f"chapter_villain_{index}_name"] = self.VILLAINS[villain_key]["name"]
            self.machine.game.player[f"chapter_villain_{index}_state"] = self._villain_state(villain_key)

    def _villain_state(self, villain_key):
        state = self._get_player_var(f"{villain_key}_state") 
        if state == None:   
            state = self.NOT_PLAYED        
        if state in (self.PLAYING, self.COMPLETED, self.FAILED):
            return state
        if self._safe_int(self._get_player_var(f"{villain_key}_completed", 0), 0) == 1:
            return self.COMPLETED
        if self._safe_int(self._get_player_var(f"{villain_key}_played", 0), 0) == 1:
            return self.FAILED
        return self.NOT_PLAYED

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _player(self):
        if not self.machine.game:
            return None
        return self.machine.game.player

    def _get_player_var(self, name, default=0):
        player = self._player()
        if not player:
            return default

        try:
            return player[name]
        except (KeyError, TypeError):
            return getattr(player, name, default)

    def _set_player_var(self, name, value):
        player = self._player()
        if not player:
            return

        try:
            player[name] = value
        except TypeError:
            setattr(player, name, value)

    def _add_player_var(self, name, amount):
        self._set_player_var(name, self._get_player_var(name, 0) + amount)
