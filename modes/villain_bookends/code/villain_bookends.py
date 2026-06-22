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
            "state_var": "rhino_state",
            "song": "play_song_22",
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
            "state_var": "sandman_state",
            "song": "play_song_8",
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
            "state_var": "vulture_state",
            "song": "play_song_10",
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
            "state_var": "electro_state",
            "song": "play_song_23",
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
            "state_var": "goblin_state",
            "song": "play_song_7",
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
            "state_var": "mysterio_state",
            "song": "play_song_24",
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
            "state_var": "scorpion_state",
            "song": "play_song_25",
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
            "state_var": "doc_ock_state",
            "song": "play_song_18",
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
            "state_var": "lizard_state",
            "song": "play_song_4",
        },

        "parafino": {
            "title": "PARAFINO",
            "intro_1": "Parafino's wax traps the city.",
            "intro_2": "Build zone jackpots with drops and pops.",
            "intro_3": "Cash saucers. Three hits lights add-a-ball.",
            "summary_title_complete": "PARAFINO DEFEATED",
            "summary_title_failed": "PARAFINO ESCAPED",
            "stat_1_label": "ZONE HITS",
            "stat_1_var": "parafino_zone_hits",
            "stat_2_label": "JACKPOTS",
            "stat_2_var": "parafino_total_jackpots",
            "points_var": "parafino_mode_points",
            "state_var": "parafino_state",
            "song": "play_song_19",
        },

        "centaur": {
            "title": "CENTAUR CHARGE",
            "intro_1": "Drop targets build the Centaur Jackpot.",
            "intro_2": "Four drops open the gate to the roof.",
            "intro_3": "Exit left and hit the staged rubber shot.",
            "summary_title_complete": "CENTAUR TRAPPED",
            "summary_title_failed": "CENTAUR ESCAPED",
            "stat_1_label": "DROPS DOWN",
            "stat_1_var": "centaur_drops_down",
            "stat_2_label": "BEST JACKPOT",
            "stat_2_var": "centaur_best_jackpot",
            "points_var": "centaur_mode_points",
            "state_var": "centaur_state",
            "song": "play_song_14",
        },

        "cerberus": {
            "title": "CERBERUS",
            "intro_1": "Hit upper targets to wake the three heads.",
            "intro_2": "Lit saucers collect Jackpots.",
            "intro_3": "The matching saucer scores 2X.",
            "summary_title_complete": "CERBERUS DEFEATED",
            "summary_title_failed": "CERBERUS ESCAPED",
            "stat_1_label": "TARGETS",
            "stat_1_var": "cerberus_targets_hit",
            "stat_2_label": "JACKPOTS",
            "stat_2_var": "cerberus_jackpots_collected",
            "points_var": "cerberus_mode_points",
            "state_var": "cerberus_state",
            "song": "play_song_9",
        },

        "cyclops": {
            "title": "CYCLOPS",
            "intro_1": "The center web target is the Cyclops Eye.",
            "intro_2": "You have limited flips. Drops add flips.",
            "intro_3": "Hit the Eye for remaining flips x 100K.",
            "summary_title_complete": "CYCLOPS DEFEATED",
            "summary_title_failed": "CYCLOPS ESCAPED",
            "stat_1_label": "BEST JACKPOT",
            "stat_1_var": "cyclops_best_jackpot",
            "stat_2_label": "FLIPS LEFT",
            "stat_2_var": "cyclops_flips_remaining",
            "points_var": "cyclops_mode_points",
            "state_var": "cyclops_state",
            "song": "play_song_14",
        },

        "swamp_reptiles": {
            "title": "SWAMP REPTILES",
            "intro_1": "Swamp Reptiles are loose in the city.",
            "intro_2": "Hit pops to light Rampage Jackpots.",
            "intro_3": "Collect the Super Jackpot at the saucer.",
            "summary_title_complete": "REPTILES CAPTURED",
            "summary_title_failed": "REPTILES ESCAPED",
            "stat_1_label": "RAMPAGE JPS",
            "stat_1_var": "swamp_reptiles_jackpots_collected",
            "stat_2_label": "POP HITS",
            "stat_2_var": "swamp_reptiles_pop_hits",
            "points_var": "swamp_reptiles_mode_points",
            "state_var": "swamp_reptiles_state",
            "song": "play_song_14",
        },

        "master_technician": {
            "title": "MASTER TECHNICIAN",
            "intro_1": "Drop targets set the spinner value.",
            "intro_2": "Build the circuit, then rip the spinner.",
            "intro_3": "Complete a bank before the system shorts out.",
            "summary_title_complete": "TECHNICIAN STOPPED",
            "summary_title_failed": "TECHNICIAN ESCAPED",
            "stat_1_label": "SPINNER VALUE",
            "stat_1_var": "master_technician_spinner_value",
            "stat_2_label": "MULTIPLIER",
            "stat_2_var": "master_technician_multiplier",
            "points_var": "master_technician_mode_points",
            "state_var": "master_technician_state",
            "song": "play_song_14",
        },

        "noah_boddy": {
            "title": "FIND THE MOLE MAN",
            "intro_1": "Get to the rooftops and search for the hidden target.",
            "intro_2": "Upper targets knock down false hiding places.",
            "intro_3": "Hit the secret drop target before time runs out.",
            "summary_title_complete": "MOLE MAN FOUND",
            "summary_title_failed": "MOLE MAN ESCAPED",
            "stat_1_label": "UPPER HITS",
            "stat_1_var": "noah_boddy_upper_target_hits",
            "stat_2_label": "BEST JACKPOT",
            "stat_2_var": "noah_boddy_best_jackpot",
            "points_var": "noah_boddy_mode_points",
            "state_var": "noah_boddy_state",
            "song": "play_song_14",
        },

        "enforcers": {
            "title": "ENFORCERS / OX",
            "intro_1": "Work three crime zones: drops, pops, and right bank.",
            "intro_2": "Zone hits light upper target jackpots up to 5X.",
            "intro_3": "Collect all three, then hit the center web for OX.",
            "summary_title_complete": "THE GANG IS BROKEN",
            "summary_title_failed": "OX GOT AWAY",
            "stat_1_label": "UPPER JPS",
            "stat_1_var": "enforcers_upper_jackpots",
            "stat_2_label": "OX SUPER",
            "stat_2_var": "enforcers_ox_super_value",
            "points_var": "enforcers_mode_points",
            "state_var": "enforcers_state",
            "song": "play_song_14",
        },

        "trubble_unleashed": {
            "title": "DIANA",
            "intro_1": "Diana has taken aim from the shadows.",
            "intro_2": "Find the safe shot and avoid the trap.",
            "intro_3": "Hit the correct target before her arrows land.",
            "summary_title_complete": "DIANA DEFEATED",
            "summary_title_failed": "DIANA ESCAPED",
            "stat_1_label": "GOOD SHOTS",
            "stat_1_var": "trubble_unleashed_correct_shots",
            "stat_2_label": "WRONG SHOTS",
            "stat_2_var": "trubble_unleashed_incorrect_shots",
            "points_var": "trubble_unleashed_mode_points",
            "state_var": "trubble_unleashed_state",
            "song": "play_song_14",
        },

        "fifth_avenue_phantom": {
            "title": "FIFTH AVENUE PHANTOM",
            "intro_1": "Drop the right bank to reveal the Phantom.",
            "intro_2": "Catch him while the hidden shot is lit.",
            "intro_3": "Early catches score bigger jackpots.",
            "summary_title_complete": "PHANTOM CAPTURED",
            "summary_title_failed": "PHANTOM VANISHED",
            "stat_1_label": "JACKPOTS",
            "stat_1_var": "fifth_avenue_phantom_jackpots",
            "stat_2_label": "BEST JACKPOT",
            "stat_2_var": "fifth_avenue_phantom_best_jackpot",
            "points_var": "fifth_avenue_phantom_mode_points",
            "state_var": "fifth_avenue_phantom_state",
            "song": "play_song_14",
        },

        "master_plan": {
            "title": "RED DOG MELVIN",
            "intro_1": "Red Dog is causing street-level trouble.",
            "intro_2": "Build rumours and chase him through the city.",
            "intro_3": "Expose the scheme at the Daily Bugle.",
            "summary_title_complete": "RED DOG STOPPED",
            "summary_title_failed": "RED DOG GOT AWAY",
            "stat_1_label": "HEADLINES",
            "stat_1_var": "master_plan_headlines_collected",
            "stat_2_label": "SUPERS",
            "stat_2_var": "master_plan_super_collected",
            "points_var": "master_plan_mode_points",
            "state_var": "master_plan_state",
            "song": "play_song_14",
        },

        "doctor_dumpty": {
            "title": "PROFESSOR PRETORIS",
            "intro_1": "Pretoris is shrinking the city.",
            "intro_2": "Solve the shot puzzle before the ray fires.",
            "intro_3": "Beat the sequence and restore the landmark.",
            "summary_title_complete": "PRETORIS STOPPED",
            "summary_title_failed": "PRETORIS ESCAPED",
            "stat_1_label": "JACKPOTS",
            "stat_1_var": "doctor_dumpty_jackpots",
            "stat_2_label": "MISSED SHOTS",
            "stat_2_var": "doctor_dumpty_missed_shots",
            "points_var": "doctor_dumpty_mode_points",
            "state_var": "doctor_dumpty_state",
            "song": "play_song_14",
        },


        "dr_magneto": {
            "title": "MATTO MAGNETO",
            "intro_1": "Magnetic pull / moving shot",
            "intro_2": "Magnet beam pulls lit shot around playfield; spinner stabilizes.",
            "intro_3": "Chapter 5: Weird Science.",
            "summary_title_complete": "MATTO MAGNETO DEFEATED",
            "summary_title_failed": "MATTO MAGNETO ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "dr_magneto_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "dr_magneto_major_hits",
            "points_var": "dr_magneto_mode_points",
            "state_var": "dr_magneto_state",
            "song": "play_song_27",
        },

        "dr_manta": {
            "title": "DOCTOR MANTA",
            "intro_1": "Underwater trap / saucer hold",
            "intro_2": "Manta traps ball in saucers; escape by hitting lit rescue shots.",
            "intro_3": "Chapter 5: Weird Science.",
            "summary_title_complete": "DOCTOR MANTA DEFEATED",
            "summary_title_failed": "DOCTOR MANTA ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "dr_manta_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "dr_manta_major_hits",
            "points_var": "dr_manta_mode_points",
            "state_var": "dr_manta_state",
            "song": "play_song_28",
        },

        "doctor_dumpty": {
            "title": "DOCTOR DUMPTY",
            "intro_1": "Fragile sequence",
            "intro_2": "Build fragile egg value with careful sequence; wrong shot cracks.",
            "intro_3": "Chapter 5: Weird Science.",
            "summary_title_complete": "DOCTOR DUMPTY DEFEATED",
            "summary_title_failed": "DOCTOR DUMPTY ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "doctor_dumpty_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "doctor_dumpty_major_hits",
            "points_var": "doctor_dumpty_mode_points",
            "state_var": "doctor_dumpty_state",
            "song": "play_song_7",
        },

        "doctor_cool": {
            "title": "DOCTOR COOL",
            "intro_1": "Freeze timers / thaw shots",
            "intro_2": "Shots freeze one by one; hit thaw shots to restore them and cash.",
            "intro_3": "Chapter 5: Weird Science.",
            "summary_title_complete": "DOCTOR COOL DEFEATED",
            "summary_title_failed": "DOCTOR COOL ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "doctor_cool_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "doctor_cool_major_hits",
            "points_var": "doctor_cool_mode_points",
            "state_var": "doctor_cool_state",
            "song": "play_song_8",
        },

        "dr_zap": {
            "title": "DOCTOR ZAPP",
            "intro_1": "Electric chain",
            "intro_2": "Chain electricity through shot groups; each correct chain step.",
            "intro_3": "Chapter 5: Weird Science.",
            "summary_title_complete": "DOCTOR ZAPP DEFEATED",
            "summary_title_failed": "DOCTOR ZAPP ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "dr_zap_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "dr_zap_major_hits",
            "points_var": "dr_zap_mode_points",
            "state_var": "dr_zap_state",
            "song": "play_song_9",
        },

        "fakir": {
            "title": "FANTASTIC FAKIR",
            "intro_1": "Animal control / rhythm",
            "intro_2": "Fakir controls animals; hit rhythm shots in order to break.",
            "intro_3": "Chapter 6: Mystic Menace.",
            "summary_title_complete": "FANTASTIC FAKIR DEFEATED",
            "summary_title_failed": "FANTASTIC FAKIR ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "fakir_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "fakir_major_hits",
            "points_var": "fakir_mode_points",
            "state_var": "fakir_state",
            "song": "play_song_10",
        },

        "scarlet_sorcerer": {
            "title": "SCARLET SORCERER",
            "intro_1": "The Scarlet Sorcerer summons strange magic.",
            "intro_2": "Hit the lit mystic shots to break the spell.",
            "intro_3": "Complete the pattern before the curse spreads.",
            "summary_title_complete": "SORCERER DEFEATED",
            "summary_title_failed": "SORCERER ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "scarlet_sorcerer_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "scarlet_sorcerer_major_hits",
            "points_var": "scarlet_sorcerer_mode_points",
            "state_var": "scarlet_sorcerer_state",
            "song": "play_song_11",
        },

        "infinata": {
            "title": "SUPER SWAMI",
            "intro_1": "The Super Swami bends minds across the city.",
            "intro_2": "Follow the moving shot and break his control.",
            "intro_3": "Complete the sequence to stop the trance.",
            "summary_title_complete": "SWAMI DEFEATED",
            "summary_title_failed": "SWAMI ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "infinata_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "infinata_major_hits",
            "points_var": "infinata_mode_points",
            "state_var": "infinata_state",
            "song": "play_song_12",
        },

        "pardo": {
            "title": "PARDO",
            "intro_1": "Performance / mind control",
            "intro_2": "Pardo presents acts; each act uses a different small shot set,.",
            "intro_3": "Chapter 6: Mystic Menace.",
            "summary_title_complete": "PARDO DEFEATED",
            "summary_title_failed": "PARDO ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "pardo_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "pardo_major_hits",
            "points_var": "pardo_mode_points",
            "state_var": "pardo_state",
            "song": "play_song_13",
        },

        "vulcan": {
            "title": "VULCAN",
            "intro_1": "Heat / forge",
            "intro_2": "Build heat at spinner/pops, then forge jackpot at lit target.",
            "intro_3": "Chapter 6: Mystic Menace.",
            "summary_title_complete": "VULCAN DEFEATED",
            "summary_title_failed": "VULCAN ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "vulcan_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "vulcan_major_hits",
            "points_var": "vulcan_mode_points",
            "state_var": "vulcan_state",
            "song": "play_song_15",
        },

        "spider_slayer": {
            "title": "RADIATION SPECIALIST",
            "intro_1": "Radiation is spreading across the city.",
            "intro_2": "Hit the charged shots to contain it.",
            "intro_3": "Finish the sequence before the warning peaks.",
            "summary_title_complete": "RADIATION CONTAINED",
            "summary_title_failed": "RADIATION ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "spider_slayer_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "spider_slayer_major_hits",
            "points_var": "spider_slayer_mode_points",
            "state_var": "spider_slayer_state",
            "song": "play_song_15",
        },

        "henry_smythe": {
            "title": "DOCTOR ATLANTEAN",
            "intro_1": "Doctor Atlantean rules from a city above.",
            "intro_2": "Hit sky shots to bring the city down.",
            "intro_3": "Complete the attack before he escapes.",
            "summary_title_complete": "ATLANTEAN DEFEATED",
            "summary_title_failed": "ATLANTEAN ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "henry_smythe_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "henry_smythe_major_hits",
            "points_var": "henry_smythe_mode_points",
            "state_var": "henry_smythe_state",
            "song": "play_song_16",
        },

        "blackbeard_robot": {
            "title": "SKY MASTER",
            "intro_1": "Sky Master attacks from above the clouds.",
            "intro_2": "Find the moving flight path.",
            "intro_3": "Hit the lit shots and ground his aircraft.",
            "summary_title_complete": "SKY MASTER GROUNDED",
            "summary_title_failed": "SKY MASTER ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "blackbeard_robot_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "blackbeard_robot_major_hits",
            "points_var": "blackbeard_robot_mode_points",
            "state_var": "blackbeard_robot_state",
            "song": "play_song_17",
        },

        "executioner_of_paris_robot": {
            "title": "THE ANTARCTICANS",
            "intro_1": "The Antarcticans strike from the ice.",
            "intro_2": "Hit rescue shots before the freeze spreads.",
            "intro_3": "Finish the sequence and escape the trap.",
            "summary_title_complete": "ANTARCTICANS STOPPED",
            "summary_title_failed": "ANTARCTICANS ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "executioner_of_paris_robot_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "executioner_of_paris_robot_major_hits",
            "points_var": "executioner_of_paris_robot_mode_points",
            "state_var": "executioner_of_paris_robot_state",
            "song": "play_song_18",
        },

        "jesse_james_robot": {
            "title": "THE PLUTONIANS",
            "intro_1": "The Plutonians have landed.",
            "intro_2": "Hit invasion shots before they reposition.",
            "intro_3": "Stop the attack and save the city.",
            "summary_title_complete": "PLUTONIANS REPELLED",
            "summary_title_failed": "PLUTONIANS ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "jesse_james_robot_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "jesse_james_robot_major_hits",
            "points_var": "jesse_james_robot_mode_points",
            "state_var": "jesse_james_robot_state",
            "song": "play_song_19",
        },

        "snowman": {
            "title": "THE SNOWMAN",
            "intro_1": "The Snowman is freezing the city.",
            "intro_2": "Thaw frozen shots with spinner and targets.",
            "intro_3": "Break the freeze before time runs out.",
            "summary_title_complete": "SNOWMAN MELTED",
            "summary_title_failed": "SNOWMAN ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "snowman_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "snowman_major_hits",
            "points_var": "snowman_mode_points",
            "state_var": "snowman_state",
            "song": "play_song_20",
        },

        "metal_eating_monster": {
            "title": "THE ICE MONSTER",
            "intro_1": "The Ice Monster blocks the city in frozen chaos.",
            "intro_2": "Hit thaw shots to open scoring.",
            "intro_3": "Collect the jackpot before everything freezes.",
            "summary_title_complete": "ICE MONSTER STOPPED",
            "summary_title_failed": "ICE MONSTER ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "metal_eating_monster_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "metal_eating_monster_major_hits",
            "points_var": "metal_eating_monster_mode_points",
            "state_var": "metal_eating_monster_state",
            "song": "play_song_21",
        },

        "master_vine": {
            "title": "MASTER VINE",
            "intro_1": "Spreading vines / hold shots",
            "intro_2": "Vines spread across shots; clear vine shots before they lock out.",
            "intro_3": "Chapter 8: Frozen / Monster Oddities.",
            "summary_title_complete": "MASTER VINE DEFEATED",
            "summary_title_failed": "MASTER VINE ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "master_vine_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "master_vine_major_hits",
            "points_var": "master_vine_mode_points",
            "state_var": "master_vine_state",
            "song": "play_song_22",
        },

        "blotto": {
            "title": "BRUTUS",
            "intro_1": "Brutus is guarding the hideout.",
            "intro_2": "Break through his cover with lit shots.",
            "intro_3": "Finish the fight before he blocks the route.",
            "summary_title_complete": "BRUTUS BEATEN",
            "summary_title_failed": "BRUTUS ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "blotto_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "blotto_major_hits",
            "points_var": "blotto_mode_points",
            "state_var": "blotto_state",
            "song": "play_song_23",
        },

        "frog_ghosts": {
            "title": "FROG GHOSTS",
            "intro_1": "Frog Ghosts are loose from the Fifth Dimension.",
            "intro_2": "Hit the haunted shots before they move.",
            "intro_3": "Clear the ghosts and seal the rift.",
            "summary_title_complete": "GHOSTS BANISHED",
            "summary_title_failed": "GHOSTS VANISHED",
            "stat_1_label": "HITS",
            "stat_1_var": "frog_ghosts_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "frog_ghosts_major_hits",
            "points_var": "frog_ghosts_mode_points",
            "state_var": "frog_ghosts_state",
            "song": "play_song_24",
        },

        "noah_boddy": {
            "title": "NOAH BODDY",
            "intro_1": "Invisible target / clues",
            "intro_2": "Noah vanishes; spinner/targets reveal silhouette; hit true.",
            "intro_3": "Chapter 9: Crime & Disguise.",
            "summary_title_complete": "NOAH BODDY DEFEATED",
            "summary_title_failed": "NOAH BODDY ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "noah_boddy_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "noah_boddy_major_hits",
            "points_var": "noah_boddy_mode_points",
            "state_var": "noah_boddy_state",
            "song": "play_song_25",
        },

        "diamond_smugglers": {
            "title": "DIAMOND SMUGGLERS",
            "intro_1": "The smugglers are moving diamonds across town.",
            "intro_2": "Hit crime shots to expose the route.",
            "intro_3": "Collect the diamonds before they vanish.",
            "summary_title_complete": "SMUGGLERS BUSTED",
            "summary_title_failed": "SMUGGLERS ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "diamond_smugglers_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "diamond_smugglers_major_hits",
            "points_var": "diamond_smugglers_mode_points",
            "state_var": "diamond_smugglers_state",
            "song": "play_song_26",
        },

        "human_flies": {
            "title": "HUMAN FLIES",
            "intro_1": "The Human Flies are framing Spider-Man.",
            "intro_2": "Hit paired wall-crawler shots before they move.",
            "intro_3": "Clear both flies to stop the frame-up.",
            "summary_title_complete": "HUMAN FLIES CAUGHT",
            "summary_title_failed": "HUMAN FLIES ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "human_flies_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "human_flies_major_hits",
            "points_var": "human_flies_mode_points",
            "state_var": "human_flies_state",
            "song": "play_song_27",
        },

        "charles_cameo": {
            "title": "CHARLES CAMEO",
            "intro_1": "Disguise / copycat",
            "intro_2": "Cameo copies another villain’s shot pattern; identify and shoot.",
            "intro_3": "Chapter 9: Crime & Disguise.",
            "summary_title_complete": "CHARLES CAMEO DEFEATED",
            "summary_title_failed": "CHARLES CAMEO ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "charles_cameo_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "charles_cameo_major_hits",
            "points_var": "charles_cameo_mode_points",
            "state_var": "charles_cameo_state",
            "song": "play_song_28",
        },

        "master_plan": {
            "title": "PLOTTER",
            "intro_1": "Planned sequence",
            "intro_2": "Plotter lays out a 3-shot plan; follow it exactly to collect.",
            "intro_3": "Chapter 9: Crime & Disguise.",
            "summary_title_complete": "PLOTTER DEFEATED",
            "summary_title_failed": "PLOTTER ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "master_plan_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "master_plan_major_hits",
            "points_var": "master_plan_mode_points",
            "state_var": "master_plan_state",
            "song": "play_song_7",
        },

        "juan_ponce_de_leon": {
            "title": "DR. VON SCHLICK",
            "intro_1": "Von Schlick has slicked the playfield.",
            "intro_2": "Control the sequence before shots slip away.",
            "intro_3": "Finish the pattern to end the oil scheme.",
            "summary_title_complete": "SCHLICK STOPPED",
            "summary_title_failed": "SCHLICK ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "juan_ponce_de_leon_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "juan_ponce_de_leon_major_hits",
            "points_var": "juan_ponce_de_leon_mode_points",
            "state_var": "juan_ponce_de_leon_state",
            "song": "play_song_8",
        },

        "devargas": {
            "title": "THE FLY",
            "intro_1": "The Fly crawls across the city walls.",
            "intro_2": "Track the moving shot and cut him off.",
            "intro_3": "Catch him before he slips away.",
            "summary_title_complete": "FLY CAUGHT",
            "summary_title_failed": "FLY ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "devargas_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "devargas_major_hits",
            "points_var": "devargas_mode_points",
            "state_var": "devargas_state",
            "song": "play_song_9",
        },

        "koga": {
            "title": "EIGOR",
            "intro_1": "Eigor is smashing through the city.",
            "intro_2": "Hit heavy shots to wear him down.",
            "intro_3": "Collect the jackpot before he escapes.",
            "summary_title_complete": "EIGOR STOPPED",
            "summary_title_failed": "EIGOR ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "koga_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "koga_major_hits",
            "points_var": "koga_mode_points",
            "state_var": "koga_state",
            "song": "play_song_10",
        },

        "cowboy": {
            "title": "PHANTOM FROM THE DEPTHS OF TIME",
            "intro_1": "The Phantom rises from another age.",
            "intro_2": "Follow the time-tossed shots.",
            "intro_3": "Complete the sequence before he fades away.",
            "summary_title_complete": "PHANTOM DEFEATED",
            "summary_title_failed": "PHANTOM ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "cowboy_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "cowboy_major_hits",
            "points_var": "cowboy_mode_points",
            "state_var": "cowboy_state",
            "song": "play_song_11",
        },

        "desperado": {
            "title": "GRAND EMPEROR",
            "intro_1": "The Grand Emperor commands from deep space.",
            "intro_2": "Hit the invasion shots in order.",
            "intro_3": "Stop the command signal before it completes.",
            "summary_title_complete": "EMPEROR DEFEATED",
            "summary_title_failed": "EMPEROR ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "desperado_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "desperado_major_hits",
            "points_var": "desperado_mode_points",
            "state_var": "desperado_state",
            "song": "play_song_12",
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
            "state_var": "kingpin_state",
            "song": "play_song_3",
        },
    }

    # MINI_WIZARD_BOOKENDS_ADDED
    # Temporary mini-wizard bookends. These use the same intro/summary system
    # as villain modes so chapter transitions feel consistent.
    VILLAINS.update({
        "sinister_surge": {
            "title": "SINISTER SURGE",
            "intro_1": "Chapter 1 mini-wizard multiball.",
            "intro_2": "Keep the balls alive through the surge.",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "SINISTER SURGE CLEARED",
            "summary_title_failed": "SINISTER SURGE LOST",
            "stat_1_label": "HITS",
            "stat_1_var": "sinister_surge_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "sinister_surge_state",
            "points_var": "sinister_surge_mode_points",
            "state_var": "sinister_surge_state",
            "song": "play_song_22",
        },
        "mastermind_trap": {
            "title": "MASTERMIND TRAP",
            "intro_1": "Chapter 2 mini-wizard multiball.",
            "intro_2": "Escape the trap while multiball runs.",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "MASTERMIND TRAP CLEARED",
            "summary_title_failed": "MASTERMIND TRAP LOST",
            "stat_1_label": "HITS",
            "stat_1_var": "mastermind_trap_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "mastermind_trap_state",
            "points_var": "mastermind_trap_mode_points",
            "state_var": "mastermind_trap_state",
            "song": "play_song_18",
        },
        "trubble_unleashed": {
            "title": "TRUBBLE UNLEASHED",
            "intro_1": "Chapter 3 mini-wizard multiball.",
            "intro_2": "Miss Trubble has the monsters loose!",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "TRUBBLE CONTAINED",
            "summary_title_failed": "TRUBBLE RUNS WILD",
            "stat_1_label": "HITS",
            "stat_1_var": "trubble_unleashed_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "trubble_unleashed_state",
            "points_var": "trubble_unleashed_mode_points",
            "state_var": "trubble_unleashed_state",
            "song": "play_song_14",
        },
        "crime_wave_crackdown": {
            "title": "CRIME WAVE CRACKDOWN",
            "intro_1": "Chapter 4 mini-wizard multiball.",
            "intro_2": "Clean up the city during multiball.",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "CRIME WAVE STOPPED",
            "summary_title_failed": "CRIME WAVE CONTINUES",
            "stat_1_label": "HITS",
            "stat_1_var": "crime_wave_crackdown_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "crime_wave_crackdown_state",
            "points_var": "crime_wave_crackdown_mode_points",
            "state_var": "crime_wave_crackdown_state",
            "song": "play_song_7",
        },
        "mad_science_meltdown": {
            "title": "MAD SCIENCE MELTDOWN",
            "intro_1": "Chapter 5 mini-wizard multiball.",
            "intro_2": "Keep the lab under control.",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "MELTDOWN STOPPED",
            "summary_title_failed": "MELTDOWN SPREADS",
            "stat_1_label": "HITS",
            "stat_1_var": "mad_science_meltdown_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "mad_science_meltdown_state",
            "points_var": "mad_science_meltdown_mode_points",
            "state_var": "mad_science_meltdown_state",
            "song": "play_song_15",
        },
        "fifth_dimension_curse": {
            "title": "FIFTH DIMENSION CURSE",
            "intro_1": "Chapter 6 mini-wizard multiball.",
            "intro_2": "Break the curse during multiball.",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "CURSE BROKEN",
            "summary_title_failed": "CURSE ESCAPES",
            "stat_1_label": "HITS",
            "stat_1_var": "fifth_dimension_curse_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "fifth_dimension_curse_state",
            "points_var": "fifth_dimension_curse_mode_points",
            "state_var": "fifth_dimension_curse_state",
            "song": "play_song_16",
        },
        "night_of_the_robots": {
            "title": "NIGHT OF THE ROBOTS",
            "intro_1": "Chapter 7 mini-wizard multiball.",
            "intro_2": "Fight back against the robot wave.",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "ROBOTS DEFEATED",
            "summary_title_failed": "ROBOTS ADVANCE",
            "stat_1_label": "HITS",
            "stat_1_var": "night_of_the_robots_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "night_of_the_robots_state",
            "points_var": "night_of_the_robots_mode_points",
            "state_var": "night_of_the_robots_state",
            "song": "play_song_17",
        },
        "nature_strikes_back": {
            "title": "NATURE STRIKES BACK",
            "intro_1": "Chapter 8 mini-wizard multiball.",
            "intro_2": "Hold off the monster oddities.",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "NATURE CONTAINED",
            "summary_title_failed": "NATURE BREAKS LOOSE",
            "stat_1_label": "HITS",
            "stat_1_var": "nature_strikes_back_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "nature_strikes_back_state",
            "points_var": "nature_strikes_back_mode_points",
            "state_var": "nature_strikes_back_state",
            "song": "play_song_20",
        },
        "who_is_the_real_villain": {
            "title": "WHO IS THE REAL VILLAIN?",
            "intro_1": "Chapter 9 mini-wizard multiball.",
            "intro_2": "Unmask the chaos while multiball runs.",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "VILLAIN REVEALED",
            "summary_title_failed": "VILLAIN VANISHED",
            "stat_1_label": "HITS",
            "stat_1_var": "who_is_the_real_villain_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "who_is_the_real_villain_state",
            "points_var": "who_is_the_real_villain_mode_points",
            "state_var": "who_is_the_real_villain_state",
            "song": "play_song_21",
        },
        "time_tossed_showdown": {
            "title": "TIME-TOSSED SHOWDOWN",
            "intro_1": "Chapter 10 mini-wizard multiball.",
            "intro_2": "Survive the final time-tossed brawl.",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "SHOWDOWN WON",
            "summary_title_failed": "SHOWDOWN LOST",
            "stat_1_label": "HITS",
            "stat_1_var": "time_tossed_showdown_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "time_tossed_showdown_state",
            "points_var": "time_tossed_showdown_mode_points",
            "state_var": "time_tossed_showdown_state",
            "song": "play_song_23",
        },
    })

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
        
        self.machine.events.post("play_song_14")

        self.machine.game.player["villain_mode_in_summary"] = False

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
        
        self.machine.events.post("play_song_21")

        self.machine.game.player["villain_mode_in_summary"] = True

        data = self.VILLAINS[villain]
        state = self._get_player_value(data.get("state_var", ""), 0)
        completed = int(state) == 2

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
        if self.current_stage in ("intro", "summary"):
            return

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
            data = self.VILLAINS[villain]
            song = data["song"]
            self.machine.events.post(f"{song}")
            self.machine.events.post("villain_bookend_intro_hide")
            self.machine.events.post("villain_bookend_intro_done", villain=villain)
        elif stage == "summary":
            # Gameplay has already stopped before the summary is shown. The
            # summary finishing only does cleanup and releases the next qualify
            # flow.
            self.machine.game.player["villain_mode_in_summary"] = False
            self.machine.events.post("reset_villain_locate")
            self.machine.events.post("reset_daily_bugle_state")
            self.machine.events.post("reset_drops")
            self.machine.events.post("drop_target_bank_dt_bank_left_reset")
            self.machine.events.post("drop_target_bank_dt_bank_right_reset")
            self.machine.events.post("villain_bookend_summary_hide")
            self.machine.events.post("villain_bookend_summary_done", villain=villain)
            
        self.machine.events.post("clear_saucers_delayed")
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

# CONSISTENT_ROSTER_ALIASES
VillainBookends.VILLAINS.update({
    "diana": {
        "title": "DIANA",
        "intro_1": "Diana takes aim with Trubble's arrows.",
        "intro_2": "Find the safe shots and avoid the trap.",
        "intro_3": "Complete the pattern before Diana fires.",
        "summary_title_complete": "DIANA DEFEATED",
        "summary_title_failed": "DIANA ESCAPED",
        "stat_1_label": "ROUNDS",
        "stat_1_var": "diana_rounds_completed",
        "stat_2_label": "MISSES",
        "stat_2_var": "diana_wrong_total",
        "points_var": "diana_mode_points",
        "state_var": "diana_state",
        "song": "play_song_26",
    },
    "trubble_unleashed": {
        "title": "TRUBBLE UNLEASHED",
        "intro_1": "Miss Trubble has unleashed her creations.",
        "intro_2": "Solve the puzzle before the monsters overrun the city.",
        "intro_3": "Chapter case files set the jackpot values.",
        "summary_title_complete": "TRUBBLE STOPPED",
        "summary_title_failed": "TRUBBLE ESCAPED",
        "stat_1_label": "ROUNDS",
        "stat_1_var": "trubble_unleashed_rounds_completed",
        "stat_2_label": "MISSES",
        "stat_2_var": "trubble_unleashed_wrong_total",
        "points_var": "trubble_unleashed_mode_points",
        "state_var": "trubble_unleashed_state",
        "song": "play_song_26",
    },
    "diamond_smugglers": {
        "title": "DIAMOND SMUGGLERS",
        "intro_1": "The smugglers are moving diamonds across town.",
        "intro_2": "Hit crime shots to expose the route.",
        "intro_3": "Collect the diamonds before they vanish.",
        "summary_title_complete": "SMUGGLERS BUSTED",
        "summary_title_failed": "SMUGGLERS ESCAPED",
        "stat_1_label": "HITS",
        "stat_1_var": "diamond_smugglers_hits",
        "stat_2_label": "MAJOR HITS",
        "stat_2_var": "diamond_smugglers_major_hits",
        "points_var": "diamond_smugglers_mode_points",
        "state_var": "diamond_smugglers_state",
        "song": "play_song_26",
    },
    "final_showdown": {
        "title": "FINAL SHOWDOWN",
        "intro_1": "The citywide crime wave reaches its peak.",
        "intro_2": "Clear every area and collect Daily Bugle jackpots.",
        "intro_3": "Finish the final battle to save the city.",
        "summary_title_complete": "FINAL SHOWDOWN WON",
        "summary_title_failed": "FINAL SHOWDOWN LOST",
        "stat_1_label": "AREAS CLEARED",
        "stat_1_var": "final_showdown_areas_cleared",
        "stat_2_label": "JACKPOTS",
        "stat_2_var": "final_showdown_jackpots",
        "points_var": "final_showdown_mode_points",
        "state_var": "final_showdown_state",
        "song": "play_song_3",
    },
})
