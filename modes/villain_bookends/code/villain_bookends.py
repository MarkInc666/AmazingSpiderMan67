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
            "completed_var": "sandman_completed",
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
            "completed_var": "vulture_completed",
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
            "completed_var": "electro_completed",
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
            "completed_var": "goblin_completed",
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
            "completed_var": "mysterio_completed",
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
            "completed_var": "scorpion_completed",
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
            "completed_var": "doc_ock_completed",
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
            "completed_var": "lizard_completed",
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
            "completed_var": "parafino_completed",
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
            "completed_var": "centaur_completed",
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
            "completed_var": "cerberus_completed",
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
            "completed_var": "cyclops_completed",
            "song": "play_song_14",
        },

        "reptilla": {
            "title": "REPTILLA",
            "intro_1": "Reptilla is tearing through the city!",
            "intro_2": "Hit pops to light Rampage Jackpots.",
            "intro_3": "Collect the Super Jackpot at saucer 2.",
            "summary_title_complete": "REPTILLA CAPTURED",
            "summary_title_failed": "REPTILLA ESCAPED",
            "stat_1_label": "RAMPAGE JPS",
            "stat_1_var": "reptilla_jackpots_collected",
            "stat_2_label": "POP HITS",
            "stat_2_var": "reptilla_pop_hits",
            "points_var": "reptilla_mode_points",
            "completed_var": "reptilla_completed",
            "song": "play_song_14",
        },

        "mole_man": {
            "title": "FIND THE MOLE MAN",
            "intro_1": "Get to the rooftops and search for the hidden target.",
            "intro_2": "Upper targets knock down false hiding places.",
            "intro_3": "Hit the secret drop target before time runs out.",
            "summary_title_complete": "MOLE MAN FOUND",
            "summary_title_failed": "MOLE MAN ESCAPED",
            "stat_1_label": "UPPER HITS",
            "stat_1_var": "mole_man_upper_target_hits",
            "stat_2_label": "BEST JACKPOT",
            "stat_2_var": "mole_man_best_jackpot",
            "points_var": "mole_man_mode_points",
            "completed_var": "mole_man_completed",
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
            "completed_var": "enforcers_completed",
            "song": "play_song_14",
        },

        "miss_trubble": {
            "title": "MISS TRUBBLE",
            "intro_1": "Three shots look the same.",
            "intro_2": "Spinner reveals the good shot.",
            "intro_3": "Seven wrong choices and she escapes.",
            "summary_title_complete": "MISS TRUBBLE DEFEATED",
            "summary_title_failed": "MISS TRUBBLE ESCAPED",
            "stat_1_label": "GOOD SHOTS",
            "stat_1_var": "miss_trubble_correct_shots",
            "stat_2_label": "WRONG SHOTS",
            "stat_2_var": "miss_trubble_incorrect_shots",
            "points_var": "miss_trubble_mode_points",
            "completed_var": "miss_trubble_completed",
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
            "completed_var": "fifth_avenue_phantom_completed",
            "song": "play_song_14",
        },

        "frederick_foswell": {
            "title": "FREDERICK FOSWELL",
            "intro_1": "Pops build rumours around the Daily Bugle.",
            "intro_2": "Spinner prints headlines at the saucers.",
            "intro_3": "Collect three headlines, then shoot the VUK.",
            "summary_title_complete": "THE BIG MAN EXPOSED",
            "summary_title_failed": "FOSWELL GOT AWAY",
            "stat_1_label": "HEADLINES",
            "stat_1_var": "frederick_foswell_headlines_collected",
            "stat_2_label": "SUPERS",
            "stat_2_var": "frederick_foswell_super_collected",
            "points_var": "frederick_foswell_mode_points",
            "completed_var": "frederick_foswell_completed",
            "song": "play_song_14",
        },

        "blackwell": {
            "title": "BLACKWELL",
            "intro_1": "Blackwell predicts your next move.",
            "intro_2": "Hit each lit shot before the timer expires.",
            "intro_3": "Spinner adds time. Beat the whole sequence.",
            "summary_title_complete": "BLACKWELL OUTSMARTED",
            "summary_title_failed": "BLACKWELL GOT AWAY",
            "stat_1_label": "JACKPOTS",
            "stat_1_var": "blackwell_jackpots",
            "stat_2_label": "MISSED SHOTS",
            "stat_2_var": "blackwell_missed_shots",
            "points_var": "blackwell_mode_points",
            "completed_var": "blackwell_completed",
            "song": "play_song_14",
        },


        "matto_magneto": {
            "title": "MATTO MAGNETO",
            "intro_1": "Magnetic pull / moving shot",
            "intro_2": "Magnet beam pulls lit shot around playfield; spinner stabilizes.",
            "intro_3": "Chapter 5: Weird Science.",
            "summary_title_complete": "MATTO MAGNETO DEFEATED",
            "summary_title_failed": "MATTO MAGNETO ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "matto_magneto_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "matto_magneto_major_hits",
            "points_var": "matto_magneto_mode_points",
            "completed_var": "matto_magneto_completed",
            "song": "play_song_27",
        },

        "doctor_manta": {
            "title": "DOCTOR MANTA",
            "intro_1": "Underwater trap / saucer hold",
            "intro_2": "Manta traps ball in saucers; escape by hitting lit rescue shots.",
            "intro_3": "Chapter 5: Weird Science.",
            "summary_title_complete": "DOCTOR MANTA DEFEATED",
            "summary_title_failed": "DOCTOR MANTA ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "doctor_manta_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "doctor_manta_major_hits",
            "points_var": "doctor_manta_mode_points",
            "completed_var": "doctor_manta_completed",
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
            "completed_var": "doctor_dumpty_completed",
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
            "completed_var": "doctor_cool_completed",
            "song": "play_song_8",
        },

        "doctor_zapp": {
            "title": "DOCTOR ZAPP",
            "intro_1": "Electric chain",
            "intro_2": "Chain electricity through shot groups; each correct chain step.",
            "intro_3": "Chapter 5: Weird Science.",
            "summary_title_complete": "DOCTOR ZAPP DEFEATED",
            "summary_title_failed": "DOCTOR ZAPP ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "doctor_zapp_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "doctor_zapp_major_hits",
            "points_var": "doctor_zapp_mode_points",
            "completed_var": "doctor_zapp_completed",
            "song": "play_song_9",
        },

        "fantastic_fakir": {
            "title": "FANTASTIC FAKIR",
            "intro_1": "Animal control / rhythm",
            "intro_2": "Fakir controls animals; hit rhythm shots in order to break.",
            "intro_3": "Chapter 6: Mystic Menace.",
            "summary_title_complete": "FANTASTIC FAKIR DEFEATED",
            "summary_title_failed": "FANTASTIC FAKIR ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "fantastic_fakir_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "fantastic_fakir_major_hits",
            "points_var": "fantastic_fakir_mode_points",
            "completed_var": "fantastic_fakir_completed",
            "song": "play_song_10",
        },

        "kotep": {
            "title": "KOTEP",
            "intro_1": "Curse / relics",
            "intro_2": "Collect relic shots to weaken curse; wrong shots strengthen curse.",
            "intro_3": "Chapter 6: Mystic Menace.",
            "summary_title_complete": "KOTEP DEFEATED",
            "summary_title_failed": "KOTEP ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "kotep_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "kotep_major_hits",
            "points_var": "kotep_mode_points",
            "completed_var": "kotep_completed",
            "song": "play_song_11",
        },

        "infinata": {
            "title": "INFINATA",
            "intro_1": "Dimension loop",
            "intro_2": "Shots loop through dimensions; hit sequence to escape loop and.",
            "intro_3": "Chapter 6: Mystic Menace.",
            "summary_title_complete": "INFINATA DEFEATED",
            "summary_title_failed": "INFINATA ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "infinata_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "infinata_major_hits",
            "points_var": "infinata_mode_points",
            "completed_var": "infinata_completed",
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
            "completed_var": "pardo_completed",
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
            "completed_var": "vulcan_completed",
            "song": "play_song_15",
        },

        "spider_slayer": {
            "title": "SPIDER-SLAYER",
            "intro_1": "Target priority / robot attack",
            "intro_2": "Robot locks onto shot groups; hit priority target before attack.",
            "intro_3": "Chapter 7: Robot Rampage.",
            "summary_title_complete": "SPIDER-SLAYER DEFEATED",
            "summary_title_failed": "SPIDER-SLAYER ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "spider_slayer_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "spider_slayer_major_hits",
            "points_var": "spider_slayer_mode_points",
            "completed_var": "spider_slayer_completed",
            "song": "play_song_15",
        },

        "henry_smythe": {
            "title": "HENRY SMYTHE",
            "intro_1": "Builder / repair cycle",
            "intro_2": "Smythe repairs disabled robot systems unless repair shots are.",
            "intro_3": "Chapter 7: Robot Rampage.",
            "summary_title_complete": "HENRY SMYTHE DEFEATED",
            "summary_title_failed": "HENRY SMYTHE ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "henry_smythe_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "henry_smythe_major_hits",
            "points_var": "henry_smythe_mode_points",
            "completed_var": "henry_smythe_completed",
            "song": "play_song_16",
        },

        "blackbeard_robot": {
            "title": "BLACKBEARD ROBOT",
            "intro_1": "Pirate plunder",
            "intro_2": "Robot pirate steals jackpot value; hit lit plunder shots to take.",
            "intro_3": "Chapter 7: Robot Rampage.",
            "summary_title_complete": "BLACKBEARD ROBOT DEFEATED",
            "summary_title_failed": "BLACKBEARD ROBOT ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "blackbeard_robot_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "blackbeard_robot_major_hits",
            "points_var": "blackbeard_robot_mode_points",
            "completed_var": "blackbeard_robot_completed",
            "song": "play_song_17",
        },

        "executioner_of_paris_robot": {
            "title": "EXECUTIONER OF PARIS ROBOT",
            "intro_1": "Countdown execution",
            "intro_2": "A countdown threatens jackpot value; hit rescue shots to delay.",
            "intro_3": "Chapter 7: Robot Rampage.",
            "summary_title_complete": "EXECUTIONER OF PARIS ROBOT DEFEATED",
            "summary_title_failed": "EXECUTIONER OF PARIS ROBOT ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "executioner_of_paris_robot_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "executioner_of_paris_robot_major_hits",
            "points_var": "executioner_of_paris_robot_mode_points",
            "completed_var": "executioner_of_paris_robot_completed",
            "song": "play_song_18",
        },

        "jesse_james_robot": {
            "title": "JESSE JAMES ROBOT",
            "intro_1": "Quickdraw",
            "intro_2": "Lit target appears briefly; hit before it moves to win quickdraw.",
            "intro_3": "Chapter 7: Robot Rampage.",
            "summary_title_complete": "JESSE JAMES ROBOT DEFEATED",
            "summary_title_failed": "JESSE JAMES ROBOT ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "jesse_james_robot_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "jesse_james_robot_major_hits",
            "points_var": "jesse_james_robot_mode_points",
            "completed_var": "jesse_james_robot_completed",
            "song": "play_song_19",
        },

        "snowman_the_snowmen": {
            "title": "SNOWMAN / THE SNOWMEN",
            "intro_1": "Freeze / thaw",
            "intro_2": "Snowmen freeze shots; thaw with spinner/upper shots before.",
            "intro_3": "Chapter 8: Frozen / Monster Oddities.",
            "summary_title_complete": "SNOWMAN / THE SNOWMEN DEFEATED",
            "summary_title_failed": "SNOWMAN / THE SNOWMEN ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "snowman_the_snowmen_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "snowman_the_snowmen_major_hits",
            "points_var": "snowman_the_snowmen_mode_points",
            "completed_var": "snowman_the_snowmen_completed",
            "song": "play_song_20",
        },

        "metal_eating_monster": {
            "title": "METAL-EATING MONSTER",
            "intro_1": "Destruction / repair",
            "intro_2": "Monster eats metal targets; hit repair shots or lose scoring.",
            "intro_3": "Chapter 8: Frozen / Monster Oddities.",
            "summary_title_complete": "METAL-EATING MONSTER DEFEATED",
            "summary_title_failed": "METAL-EATING MONSTER ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "metal_eating_monster_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "metal_eating_monster_major_hits",
            "points_var": "metal_eating_monster_mode_points",
            "completed_var": "metal_eating_monster_completed",
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
            "completed_var": "master_vine_completed",
            "song": "play_song_22",
        },

        "blotto": {
            "title": "BLOTTO",
            "intro_1": "Cover / reveal",
            "intro_2": "Blotto covers shots with ink; hit reveal shots to uncover jackpot.",
            "intro_3": "Chapter 8: Frozen / Monster Oddities.",
            "summary_title_complete": "BLOTTO DEFEATED",
            "summary_title_failed": "BLOTTO ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "blotto_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "blotto_major_hits",
            "points_var": "blotto_mode_points",
            "completed_var": "blotto_completed",
            "song": "play_song_23",
        },

        "pod": {
            "title": "POD",
            "intro_1": "Rolling pod hazard",
            "intro_2": "Pods roll between upper targets; hit active pod to stop spread.",
            "intro_3": "Chapter 8: Frozen / Monster Oddities.",
            "summary_title_complete": "POD DEFEATED",
            "summary_title_failed": "POD ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "pod_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "pod_major_hits",
            "points_var": "pod_mode_points",
            "completed_var": "pod_completed",
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
            "completed_var": "noah_boddy_completed",
            "song": "play_song_25",
        },

        "fiddler": {
            "title": "FIDDLER",
            "intro_1": "Rhythm / moving target",
            "intro_2": "Fiddler plays rhythm; hit shots in beat/order to build and.",
            "intro_3": "Chapter 9: Crime & Disguise.",
            "summary_title_complete": "FIDDLER DEFEATED",
            "summary_title_failed": "FIDDLER ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "fiddler_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "fiddler_major_hits",
            "points_var": "fiddler_mode_points",
            "completed_var": "fiddler_completed",
            "song": "play_song_26",
        },

        "fly_twins": {
            "title": "FLY TWINS",
            "intro_1": "Paired shots / double jackpot",
            "intro_2": "Two fly shots are lit; hit both within window for double jackpot.",
            "intro_3": "Chapter 9: Crime & Disguise.",
            "summary_title_complete": "FLY TWINS DEFEATED",
            "summary_title_failed": "FLY TWINS ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "fly_twins_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "fly_twins_major_hits",
            "points_var": "fly_twins_mode_points",
            "completed_var": "fly_twins_completed",
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
            "completed_var": "charles_cameo_completed",
            "song": "play_song_28",
        },

        "plotter": {
            "title": "PLOTTER",
            "intro_1": "Planned sequence",
            "intro_2": "Plotter lays out a 3-shot plan; follow it exactly to collect.",
            "intro_3": "Chapter 9: Crime & Disguise.",
            "summary_title_complete": "PLOTTER DEFEATED",
            "summary_title_failed": "PLOTTER ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "plotter_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "plotter_major_hits",
            "points_var": "plotter_mode_points",
            "completed_var": "plotter_completed",
            "song": "play_song_7",
        },

        "juan_ponce_de_leon": {
            "title": "JUAN PONCE DE LEÓN",
            "intro_1": "Fountain / timer reset",
            "intro_2": "Value drains until fountain shot is hit; fountain resets timer.",
            "intro_3": "Chapter 10: Time / History / Outlaws.",
            "summary_title_complete": "JUAN PONCE DE LEÓN DEFEATED",
            "summary_title_failed": "JUAN PONCE DE LEÓN ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "juan_ponce_de_leon_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "juan_ponce_de_leon_major_hits",
            "points_var": "juan_ponce_de_leon_mode_points",
            "completed_var": "juan_ponce_de_leon_completed",
            "song": "play_song_8",
        },

        "devargas": {
            "title": "DEVARGAS",
            "intro_1": "Gold chase",
            "intro_2": "Gold value moves between shots; collect trails then cash city.",
            "intro_3": "Chapter 10: Time / History / Outlaws.",
            "summary_title_complete": "DEVARGAS DEFEATED",
            "summary_title_failed": "DEVARGAS ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "devargas_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "devargas_major_hits",
            "points_var": "devargas_mode_points",
            "completed_var": "devargas_completed",
            "song": "play_song_9",
        },

        "koga": {
            "title": "KOGA",
            "intro_1": "Limited flips / mind control",
            "intro_2": "Start with limited flips; correct mind-control shots restore.",
            "intro_3": "Chapter 10: Time / History / Outlaws.",
            "summary_title_complete": "KOGA DEFEATED",
            "summary_title_failed": "KOGA ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "koga_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "koga_major_hits",
            "points_var": "koga_mode_points",
            "completed_var": "koga_completed",
            "song": "play_song_10",
        },

        "cowboy": {
            "title": "COWBOY",
            "intro_1": "Quickdraw / single target",
            "intro_2": "One target lights for a short quickdraw; hit it to build showdown.",
            "intro_3": "Chapter 10: Time / History / Outlaws.",
            "summary_title_complete": "COWBOY DEFEATED",
            "summary_title_failed": "COWBOY ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "cowboy_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "cowboy_major_hits",
            "points_var": "cowboy_mode_points",
            "completed_var": "cowboy_completed",
            "song": "play_song_11",
        },

        "desperado": {
            "title": "DESPERADO",
            "intro_1": "Outlaw chase / bounty",
            "intro_2": "Chase moves around playfield; collect bounties then final saucer.",
            "intro_3": "Chapter 10: Time / History / Outlaws.",
            "summary_title_complete": "DESPERADO DEFEATED",
            "summary_title_failed": "DESPERADO ESCAPED",
            "stat_1_label": "HITS",
            "stat_1_var": "desperado_hits",
            "stat_2_label": "MAJOR HITS",
            "stat_2_var": "desperado_major_hits",
            "points_var": "desperado_mode_points",
            "completed_var": "desperado_completed",
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
            "completed_var": "kingpin_completed",
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
            "stat_2_var": "sinister_surge_completed",
            "points_var": "sinister_surge_mode_points",
            "completed_var": "sinister_surge_completed",
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
            "stat_2_var": "mastermind_trap_completed",
            "points_var": "mastermind_trap_mode_points",
            "completed_var": "mastermind_trap_completed",
            "song": "play_song_18",
        },
        "monster_island_breakout": {
            "title": "TRUBBLE UNLEASHED",
            "intro_1": "Chapter 3 mini-wizard multiball.",
            "intro_2": "Miss Trubble has the monsters loose!",
            "intro_3": "Multiball end shows the chapter summary.",
            "summary_title_complete": "TRUBBLE CONTAINED",
            "summary_title_failed": "TRUBBLE RUNS WILD",
            "stat_1_label": "HITS",
            "stat_1_var": "monster_island_breakout_hits",
            "stat_2_label": "CHAPTER MB",
            "stat_2_var": "monster_island_breakout_completed",
            "points_var": "monster_island_breakout_mode_points",
            "completed_var": "monster_island_breakout_completed",
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
            "stat_2_var": "crime_wave_crackdown_completed",
            "points_var": "crime_wave_crackdown_mode_points",
            "completed_var": "crime_wave_crackdown_completed",
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
            "stat_2_var": "mad_science_meltdown_completed",
            "points_var": "mad_science_meltdown_mode_points",
            "completed_var": "mad_science_meltdown_completed",
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
            "stat_2_var": "fifth_dimension_curse_completed",
            "points_var": "fifth_dimension_curse_mode_points",
            "completed_var": "fifth_dimension_curse_completed",
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
            "stat_2_var": "night_of_the_robots_completed",
            "points_var": "night_of_the_robots_mode_points",
            "completed_var": "night_of_the_robots_completed",
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
            "stat_2_var": "nature_strikes_back_completed",
            "points_var": "nature_strikes_back_mode_points",
            "completed_var": "nature_strikes_back_completed",
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
            "stat_2_var": "who_is_the_real_villain_completed",
            "points_var": "who_is_the_real_villain_mode_points",
            "completed_var": "who_is_the_real_villain_completed",
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
            "stat_2_var": "time_tossed_showdown_completed",
            "points_var": "time_tossed_showdown_mode_points",
            "completed_var": "time_tossed_showdown_completed",
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