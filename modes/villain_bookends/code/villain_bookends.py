import time

from mpf.core.mode import Mode


class VillainBookends(Mode):

    INTRO_MS = 5000
    SUMMARY_MS = 6000
    WIZARD_INTRO_MS = 6000
    WIZARD_SUMMARY_MS = 7000
    CHAPTER_BONUS_MS = 6000
    COMIC_SUMMARY_MS = 3000
    COMIC_SUMMARY_VILLAINS = {
        "sinister_surge": 1,
        "mastermind_trap": 2,
        "trubble_unleashed": 3,
        "crime_wave": 4,
        "the_web_tightens": 5,
        "fifth_dimension_curse": 6,
        "mad_science_meltdown": 7,
        "nature_strikes_back": 8,
        "invasion_from_everywhere": 9,
        "who_is_the_real_villain": 10,
        "time_tossed_showdown": 11,
    }
    UNSKIPPABLE_SUMMARY_VILLAINS = {
        "sinister_surge",
        "mastermind_trap",
        "trubble_unleashed",
        "crime_wave",
        "fifth_dimension_curse",
        "mad_science_meltdown",
        "nature_strikes_back",
        "invasion_from_everywhere",
        "who_is_the_real_villain",
        "the_web_tightens",
        "time_tossed_showdown",
        "final_showdown",
    }

    VILLAINS = {
        'rhino': {
            'title': 'RHINO BASH',
            'intro_1': 'HIT THE POPS TO BUILD RAGE',
            'intro_2': 'OTHER SHOTS BUILD THE JACKPOT',
            'intro_3': 'COLLECT AT A OR B BEFORE OVERLOAD',
            'summary_title_complete': 'RHINO BASH COMPLETED',
            'summary_title_failed': 'RHINO BASH ENDED',
            'stat_1_label': 'BIGGEST JACKPOT',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'HIGHEST RAGE',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'rhino_state',
            'song': 'play_song_22',
        },
        'sandman': {
            'title': 'SHIFTING SANDS',
            'intro_1': 'HIT THE FLASHING DROP TARGET',
            'intro_2': 'CONSECUTIVE HITS INCREASE THE AWARD',
            'intro_3': 'COMPLETE THE RIGHT DROP BANK',
            'summary_title_complete': 'SHIFTING SANDS COMPLETED',
            'summary_title_failed': 'SHIFTING SANDS ENDED',
            'stat_1_label': 'DROP TARGETS HIT',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BEST STREAK',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'sandman_state',
            'song': 'play_song_80',
        },
        'vulture': {
            'title': 'VULTURE SKY ATTACK',
            'intro_1': 'REACH THE ROOFTOP',
            'intro_2': 'HIT UPPER TARGETS TO BUILD SPINNER VALUE',
            'intro_3': 'SPIN BEFORE THE TARGETS DIM',
            'summary_title_complete': 'VULTURE SKY ATTACK COMPLETED',
            'summary_title_failed': 'VULTURE SKY ATTACK ENDED',
            'stat_1_label': 'SPINS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'vulture_state',
            'song': 'play_song_10',
        },
        'lizard': {
            'title': 'ANTIDOTE HURRY UP',
            'intro_1': 'HIT BOTH POPS TO BUILD THE ANTIDOTE',
            'intro_2': 'DELIVER AT THE LEFT WEB BEFORE THE VALUE DROPS',
            'intro_3': 'HIT STAR FOR 10X SCORING',
            'summary_title_complete': 'ANTIDOTE HURRY UP COMPLETED',
            'summary_title_failed': 'ANTIDOTE HURRY UP ENDED',
            'stat_1_label': 'DELIVERIES',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BEST DELIVERY',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'lizard_state',
            'song': 'play_song_89',
        },
        'electro': {
            'title': 'ELECTRO POWER SURGE',
            'intro_1': 'FOLLOW THE MOVING SPARK',
            'intro_2': 'HIT THE LIT SHOT BEFORE THE SPARK MOVES',
            'intro_3': 'COLLECT THE FINAL SPARK FOR A SUPER JACKPOT',
            'summary_title_complete': 'ELECTRO POWER SURGE COMPLETED',
            'summary_title_failed': 'ELECTRO POWER SURGE ENDED',
            'stat_1_label': 'BEST SPARK',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPER JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'electro_state',
            'song': 'play_song_23',
        },
        'goblin': {
            'title': 'GOBLIN CHAOS',
            'intro_1': 'TWO-BALL CHAOS MULTIBALL',
            'intro_2': 'SHOOT SAUCERS TO BANK CHAOS AND START SAFE PLAY',
            'intro_3': 'FLASHING SHOTS BUILD CHAOS — SOLID SHOTS REDUCE IT',
            'summary_title_complete': 'GOBLIN CHAOS COMPLETED',
            'summary_title_failed': 'GOBLIN CHAOS ENDED',
            'stat_1_label': 'ATTACK TOTAL',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'CHAOS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'goblin_state',
            'song': 'play_song_7',
        },
        'doc_ock': {
            'title': 'DOC OCK LOCKDOWN',
            'intro_1': 'IN/OUTLANES OR LEFT BANK TO LOCK ARMS',
            'intro_2': 'SHOOT WEB TARGETS TO COLLECT JACKPOTS',
            'intro_3': 'SPIN THE SPINNERS TO BOOST THE MULTIPLIER',
            'summary_title_complete': 'DOC OCK LOCKDOWN COMPLETED',
            'summary_title_failed': 'DOC OCK LOCKDOWN ENDED',
            'stat_1_label': 'MOST ARMS LOCKED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'doc_ock_state',
            'song': 'play_song_18',
        },
        'mysterio': {
            'title': 'MYSTERIO ILLUSION',
            'intro_1': 'FIND THE REAL MYSTERIO',
            'intro_2': 'USE CLUES TO SEARCH LEFT, RIGHT OR UPPER',
            'intro_3': 'WRONG GUESSES REDUCE THE SUPER JACKPOT',
            'summary_title_complete': 'MYSTERIO REVEALED',
            'summary_title_failed': 'MYSTERIO ILLUSION ENDED',
            'stat_1_label': 'CLUES USED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPER JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'mysterio_state',
            'song': 'play_song_63',
        },
        'scorpion': {
            'title': "SCORPION'S STING",
            'intro_1': 'ROOFTOP SPINS BUILD THE STINGER JACKPOT',
            'intro_2': 'ROOF EXITS LIGHT DROP TARGETS OR POPS',
            'intro_3': 'HIT THE LIT SHOT TO COLLECT THE STING',
            'summary_title_complete': "SCORPION'S STING COMPLETED",
            'summary_title_failed': "SCORPION'S STING ENDED",
            'stat_1_label': 'STINGS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'scorpion_state',
            'song': 'play_song_72',
        },
        'parafino': {
            'title': "PARAFINO'S WAX INFERNO",
            'intro_1': 'HIT DROPS AND POPS TO HEAT THE ZONES',
            'intro_2': 'SHOOT SAUCERS TO COLLECT ZONE JACKPOTS',
            'intro_3': 'THREE HITS IN A ZONE LIGHTS ADD-A-BALL',
            'summary_title_complete': "PARAFINO'S WAX INFERNO COMPLETED",
            'summary_title_failed': "PARAFINO'S WAX INFERNO ENDED",
            'stat_1_label': 'ZONE HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'parafino_state',
            'song': 'play_song_19',
        },
        'cerberus': {
            'title': 'CERBERUS TRIPLE THREAT',
            'intro_1': 'LEFT DROPS LIGHT MATCHING SAUCER JACKPOTS',
            'intro_2': 'UPPER TARGETS LIGHT MATCHING JACKPOTS AT 2X',
            'intro_3': 'SPIN THE UPPER SPINNER TO BUILD JACKPOT VALUE',
            'summary_title_complete': 'CERBERUS TRIPLE THREAT COMPLETED',
            'summary_title_failed': 'CERBERUS TRIPLE THREAT ENDED',
            'stat_1_label': 'TARGETS HIT',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'cerberus_state',
            'song': 'play_song_29',
        },
        'vulcan': {
            'title': "VULCAN'S FURY",
            'intro_1': 'TWO-BALL ERUPTION MULTIBALL',
            'intro_2': 'UPPER TARGETS BUILD DROP TARGET JACKPOTS',
            'intro_3': 'RIGHT BANK, THEN UPPER TARGETS TO ADD A BALL',
            'summary_title_complete': "VULCAN'S FURY COMPLETED",
            'summary_title_failed': "VULCAN'S FURY ENDED",
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'vulcan_state',
            'song': 'play_song_64',
        },
        'diana': {
            'title': "DIANA'S ROOFTOP HUNT",
            'intro_1': 'FLIPPER PRESSES USE ARROWS',
            'intro_2': 'SPIN THE UPPER SPINNER TO ADD ARROWS',
            'intro_3': 'EITHER ROOF EXIT STARTS THE DROP TARGET HUNT',
            'summary_title_complete': "DIANA'S ROOFTOP HUNT COMPLETED",
            'summary_title_failed': "DIANA'S ROOFTOP HUNT ENDED",
            'stat_1_label': 'TOTAL HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BULLSEYES',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'diana_state',
            'song': 'play_song_30',
        },
        'cyclops': {
            'title': 'EYE OF THE CYCLOPS',
            'intro_1': 'LIMITED FLIPS',
            'intro_2': 'DROPS ADD FLIPS',
            'intro_3': 'CENTER WEB FOR 100K PER REMAINING FLIP',
            'summary_title_complete': 'EYE OF THE CYCLOPS COMPLETED',
            'summary_title_failed': 'EYE OF THE CYCLOPS ENDED',
            'stat_1_label': 'FLIPS JACKPOT',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': '',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'cyclops_state',
            'song': 'play_song_55',
        },
        'centaur': {
            'title': 'CHARGE OF THE CENTAUR',
            'intro_1': 'DROPS BUILD THE CENTAUR JACKPOT',
            'intro_2': 'FOUR DROPS OPEN THE ROOFTOP',
            'intro_3': 'EXIT LEFT, THEN HIT THE RIGHT RUBBER',
            'summary_title_complete': 'CHARGE OF THE CENTAUR COMPLETED',
            'summary_title_failed': 'CHARGE OF THE CENTAUR ENDED',
            'stat_1_label': 'DROP TARGETS DOWN',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'centaur_state',
            'song': 'play_song_31',
        },
        'fly_twins': {
            'title': 'DOUBLE TROUBLE',
            'intro_1': 'TWO-BALL ROOFTOP MULTIBALL',
            'intro_2': 'UPPER TARGETS LIGHT SAUCER JACKPOTS',
            'intro_3': 'UPPER SPINNER BUILDS VALUE — CATCH BOTH TWINS FOR SUPER',
            'summary_title_complete': 'DOUBLE TROUBLE COMPLETED',
            'summary_title_failed': 'DOUBLE TROUBLE ENDED',
            'stat_1_label': 'SUPER JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'fly_twins_state',
            'song': 'play_song_32',
        },
        'fifth_avenue_phantom': {
            'title': 'FIND THE PHANTOM',
            'intro_1': 'RIGHT DROPS REVEAL THE PHANTOM',
            'intro_2': 'HIT THE REVEALED SHOT BEFORE TIME RUNS OUT',
            'intro_3': 'MORE DROPS ADD TIME BUT REDUCE JACKPOT VALUE',
            'summary_title_complete': 'FIND THE PHANTOM COMPLETED',
            'summary_title_failed': 'FIND THE PHANTOM ENDED',
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'fifth_avenue_phantom_state',
            'song': 'play_song_60',
        },
        'enforcers': {
            'title': 'THE ENFORCERS',
            'intro_1': 'DROPS AND POPS LIGHT UPPER JACKPOTS',
            'intro_2': 'COLLECT AND SPIN TO BUILD UP OX',
            'intro_3': 'SUPER OX AT CENTER WEB',
            'summary_title_complete': 'THE ENFORCERS COMPLETED',
            'summary_title_failed': 'THE ENFORCERS ENDED',
            'stat_1_label': 'UPPER JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'OX SUPER VALUE',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'enforcers_state',
            'song': 'play_song_39',
        },
        'doctor_cool': {
            'title': 'DIAMOND HEIST',
            'intro_1': 'DROPS BUILD THE DIAMOND JACKPOT',
            'intro_2': 'COMPLETE RIGHT BANK TO EXPAND LIT SAUCERS',
            'intro_3': 'STAR FREEZES THE CHASE — COLLECT AT A LIT SAUCER',
            'summary_title_complete': 'DIAMOND HEIST COMPLETED',
            'summary_title_failed': 'DIAMOND HEIST ENDED',
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'DIAMOND BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'doctor_cool_state',
            'song': 'play_song_56',
        },
        'harley_clivendon': {
            'title': "CLIVENDON'S ROOFTOP RAMPAGE",
            'intro_1': 'LOCK A BALL IN A SAUCER DURING MULTIBALL',
            'intro_2': 'LIGHT FOUR OR MORE AREAS TO BUILD THE JACKPOT',
            'intro_3': 'COLLECT AT THE DAILY BUGLE VUK',
            'summary_title_complete': "CLIVENDON'S ROOFTOP RAMPAGE COMPLETED",
            'summary_title_failed': "CLIVENDON'S ROOFTOP RAMPAGE ENDED",
            'stat_1_label': 'VUK JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'harley_clivendon_state',
            'song': 'play_song_51',
        },
        'conquistador': {
            'title': "CONQUISTADOR'S CONQUEST",
            'intro_1': 'HIT ANY LEFT DROP TO OPEN THE ROOFTOP',
            'intro_2': 'SPIN TO FIND THE FOUNTAIN — UPPER TARGETS BUILD VALUE',
            'intro_3': 'COLLECT THE FOUNTAIN JACKPOT AT CENTER WEB',
            'summary_title_complete': "CONQUISTADOR'S CONQUEST COMPLETED",
            'summary_title_failed': "CONQUISTADOR'S CONQUEST ENDED",
            'stat_1_label': 'FOUNTAIN JACKPOT POINTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SPEED BONUS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'conquistador_state',
            'song': 'play_song_54',
        },
        'spider_slayer': {
            'title': 'SPIDER-SLAYER',
            'intro_1': 'HIT 15 LIT SHOTS TO EXPOSE THE SLAYER',
            'intro_2': 'COLLECT THE JACKPOT AT THE DAILY BUGLE VUK',
            'intro_3': 'COLLECT QUICKLY — JACKPOT VALUE DROPS',
            'summary_title_complete': 'SPIDER-SLAYER COMPLETED',
            'summary_title_failed': 'SPIDER-SLAYER ENDED',
            'stat_1_label': 'SLAYER JACKPOT',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'HUNT TIME',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'spider_slayer_state',
            'song': 'play_song_84',
        },
        'metal_eating_robot': {
            'title': 'METAL-EATING ROBOT',
            'intro_1': 'THE ROBOT ATTACKS PLAYFIELD ZONES',
            'intro_2': 'HIT FLASHING ZONES TO SAVE THEM',
            'intro_3': 'SAVE FOUR AND CLEAR ALL ACTIVE ATTACKS',
            'summary_title_complete': 'METAL-EATING ROBOT COMPLETED',
            'summary_title_failed': 'METAL-EATING ROBOT ENDED',
            'stat_1_label': 'ZONES SAVED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'ZONES DESTROYED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'metal_eating_robot_state',
            'song': 'play_song_88',
        },
        'fiddler': {
            'title': 'FIDDLER SAYS',
            'intro_1': 'SHOOT A SAUCER TO WATCH THE PATTERN',
            'intro_2': 'REPEAT THE NOTES IN ORDER',
            'intro_3': 'THREE FAILED PATTERNS END THE MODE',
            'summary_title_complete': 'FIDDLER SAYS COMPLETED',
            'summary_title_failed': 'FIDDLER SAYS ENDED',
            'stat_1_label': 'PATTERNS COMPLETED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'CORRECT NOTES HIT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'fiddler_state',
            'completion_var': 'active_mode_completed',
            'song': 'play_song_25',
        },
        'pardo': {
            'title': "PARDO'S PROWL",
            'intro_1': 'FIND THE SECRET SHOT',
            'intro_2': 'SPINNER BRIEFLY REVEALS THE CORRECT SHOT',
            'intro_3': 'A WRONG GUESS REDUCES JACKPOT VALUE',
            'summary_title_complete': "PARDO'S PROWL COMPLETED",
            'summary_title_failed': "PARDO'S PROWL ENDED",
            'stat_1_label': 'FIRST-GUESS JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SECOND-GUESS JACKPOTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'pardo_state',
            'completion_var': 'active_mode_completed',
            'song': 'play_song_53',
        },
        'fakir': {
            'title': "FAKIR'S RUBY REVEAL",
            'intro_1': 'TWO-BALL RUBY MULTIBALL',
            'intro_2': 'SAUCERS REVEAL RUBIES AT UPPER TARGETS',
            'intro_3': 'SPINNERS BUILD VALUE — THREE RUBIES LIGHT SUPER',
            'summary_title_complete': "FAKIR'S RUBY REVEAL COMPLETED",
            'summary_title_failed': "FAKIR'S RUBY REVEAL ENDED",
            'stat_1_label': 'RUBIES COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPER JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'fakir_state',
            'song': 'play_song_34',
        },
        'kotep': {
            'title': "KOTEP'S SCARLET CURSE",
            'intro_1': 'DEMONS APPEAR EVERY FOUR SECONDS',
            'intro_2': 'HIT FLASHING SHOTS TO DESTROY FOUR DEMONS',
            'intro_3': 'COLLECT THE SCEPTER SUPER AT THE DAILY BUGLE VUK',
            'summary_title_complete': "KOTEP'S SCARLET CURSE COMPLETED",
            'summary_title_failed': "KOTEP'S SCARLET CURSE ENDED",
            'stat_1_label': 'DEMONS DESTROYED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': '',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'kotep_state',
            'completion_var': 'active_mode_completed',
            'song': 'play_song_35',
        },
        'super_swami': {
            'title': "SUPER SWAMI'S SPELL",
            'intro_1': 'NEW YORK HAS GONE DARK',
            'intro_2': 'HIT ALL SIX CITY AREAS TO RESTORE POWER',
            'intro_3': 'RESTORE EACH AREA BEFORE ITS TIMER EXPIRES',
            'summary_title_complete': "SUPER SWAMI'S SPELL COMPLETED",
            'summary_title_failed': "SUPER SWAMI'S SPELL ENDED",
            'stat_1_label': 'AREAS RESTORED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'super_swami_state',
            'song': 'play_song_73',
        },
        'infinata': {
            'title': 'INFINITE INFINATA',
            'intro_1': 'HIT FLASHING SHOTS TO BANISH CREATURES',
            'intro_2': 'CLEAR THREE AREAS TO LIGHT THE SUPER',
            'intro_3': 'COLLECT THE SUPER AT ANY SAUCER',
            'summary_title_complete': 'INFINITE INFINATA COMPLETED',
            'summary_title_failed': 'INFINITE INFINATA ENDED',
            'stat_1_label': 'AREAS CLEARED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': '',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'infinata_state',
            'song': 'play_song_24',
        },
        'noah_boddy': {
            'title': 'NOBODY IN SIGHT',
            'intro_1': 'UPPER TARGETS REVEAL THE SECRET DROP',
            'intro_2': 'UPPER SPINNER BUILDS THE JACKPOT',
            'intro_3': 'HIT THE LAST STANDING DROP BEFORE TIME EXPIRES',
            'summary_title_complete': 'NOBODY IN SIGHT COMPLETED',
            'summary_title_failed': 'NOBODY IN SIGHT ENDED',
            'stat_1_label': 'UPPER SPINNER SPINS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'noah_boddy_state',
            'song': 'play_song_36',
        },
        'dr_magneto': {
            'title': "MAGNETO'S MAGNETIC MAYHEM",
            'intro_1': 'SLINGS AND INLANES LIGHT A AND B',
            'intro_2': 'COLLECT LIT A AND B, THEN HIT THE FLASHING POPS',
            'intro_3': 'COMPLETE BOTH POPS TO LIGHT CENTER WEB SUPER',
            'summary_title_complete': "MAGNETO'S MAGNETIC MAYHEM COMPLETED",
            'summary_title_failed': "MAGNETO'S MAGNETIC MAYHEM ENDED",
            'stat_1_label': 'CIRCUIT SHOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': '',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_magneto_state',
            'song': 'play_song_27',
        },
        'professor_pretorius': {
            'title': "PRETORIUS'S PERILOUS EXPERIMENT",
            'intro_1': 'HIT POPS AND DROPS TO COMPLETE REACTOR STATIONS',
            'intro_2': 'SPIN TO COOL THE REACTOR BEFORE IT OVERHEATS',
            'intro_3': 'COMPLETE FOUR STATIONS TO LIGHT THE VUK SUPER',
            'summary_title_complete': "PRETORIUS'S PERILOUS EXPERIMENT COMPLETED",
            'summary_title_failed': "PRETORIUS'S PERILOUS EXPERIMENT ENDED",
            'stat_1_label': 'REACTOR HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': '',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'professor_pretorius_state',
            'song': 'play_song_28',
        },
        'doctor_dumpty': {
            'title': "DUMPTY'S GREAT FALL",
            'intro_1': 'LEFT DROPS REVEAL LAUGHING GAS',
            'intro_2': 'CLEAR THREE GAS AREAS TO OPEN THE ROOFTOP',
            'intro_3': 'UPPER SPINNER BUILDS VALUE — UPPER TARGETS POP BALLOONS',
            'summary_title_complete': "DUMPTY'S GREAT FALL COMPLETED",
            'summary_title_failed': "DUMPTY'S GREAT FALL ENDED",
            'stat_1_label': 'BALLOONS POPPED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': '',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'doctor_dumpty_state',
            'song': 'play_song_37',
        },
        'dr_von_schlick': {
            'title': 'SLIPPERY SCHLICK',
            'intro_1': 'HIT THE ROAMING GREEN OIL SHOTS',
            'intro_2': 'COLLECT FIVE OIL PELLETS TO OPEN THE REACTOR',
            'intro_3': 'SHOOT THE DAILY BUGLE VUK TO FLOOD THE REACTOR',
            'summary_title_complete': 'SLIPPERY SCHLICK COMPLETED',
            'summary_title_failed': 'SLIPPERY SCHLICK ENDED',
            'stat_1_label': 'OIL PELLETS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': '',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_von_schlick_state',
            'song': 'play_song_8',
        },
        'clive_blotto': {
            'title': 'BLOTTO TAKEOVER',
            'intro_1': 'THE BLOTTO KEEPS SPREADING',
            'intro_2': 'SPINNERS SLOW THE SPREAD',
            'intro_3': 'CLEAR ALL AREAS',
            'summary_title_complete': 'BLOTTO TAKEOVER COMPLETED',
            'summary_title_failed': 'BLOTTO TAKEOVER ENDED',
            'stat_1_label': 'AREAS CLEARED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BLOTTO ATTACKS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'clive_blotto_state',
            'song': 'play_song_57',
        },
        'dr_zapp': {
            'title': 'ZAPP ATTACK',
            'intro_1': 'HIT A DROP IN EACH BANK TO OPEN THE ROOFTOP',
            'intro_2': 'SPIN TO COLLECT FLASHES',
            'intro_3': 'UPPER TARGETS INCREASE FLASH RATE',
            'summary_title_complete': 'ZAPP ATTACK COMPLETED',
            'summary_title_failed': 'ZAPP ATTACK ENDED',
            'stat_1_label': 'CAMERA FLASHES',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'UPPER SPINNER SPINS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_zapp_state',
            'song': 'play_song_38',
        },
        'bolton_boomer': {
            'title': 'DOUBLE CROSS',
            'intro_1': 'MULTIBALL TARGET ATTACK',
            'intro_2': 'HIT THE LIT TARGET, THEN LOCK A BALL IN A SAUCER',
            'intro_3': 'COLLECT THE SUPER AT THE DAILY BUGLE VUK',
            'summary_title_complete': 'DOUBLE CROSS COMPLETED',
            'summary_title_failed': 'DOUBLE CROSS ENDED',
            'stat_1_label': 'SUPER JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST SUPER JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'bolton_boomer_state',
            'song': 'play_song_94',
        },
        'snowman': {
            'title': "SNOWMAN'S COLD SNAP",
            'intro_1': 'HIT LEFT AND CENTER WEBS BEFORE TIME EXPIRES',
            'intro_2': 'SPIN THE LOWER SPINNER TO ZAP SNOWMAN',
            'intro_3': 'KEEP SPINNING FOR BONUS POINTS',
            'summary_title_complete': "SNOWMAN'S COLD SNAP COMPLETED",
            'summary_title_failed': "SNOWMAN'S COLD SNAP ENDED",
            'stat_1_label': 'BONUS SPINS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST SPIN VALUE',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'snowman_state',
            'song': 'play_song_2',
        },
        'plutonians': {
            'title': 'PLUTONIAN DEEP FREEZE',
            'intro_1': 'HIT FROZEN AREAS TO THAW THEM',
            'intro_2': 'UPPER TARGETS TEMPORARILY DISABLE THE FREEZE RAY',
            'intro_3': 'THAW ALL SIX AREAS AT ONCE',
            'summary_title_complete': 'PLUTONIAN DEEP FREEZE COMPLETED',
            'summary_title_failed': 'PLUTONIAN DEEP FREEZE ENDED',
            'stat_1_label': 'TOTAL THAWS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'FREEZE RAY BLOCKS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'plutonians_state',
            'song': 'play_song_47',
        },
        'dr_manta': {
            'title': "MANTA'S DEEP-SEA MENACE",
            'intro_1': 'LOCK THE FIRST BALL AT THE DAILY BUGLE VUK',
            'intro_2': 'LOCK THE SECOND BALL IN ANY SAUCER',
            'intro_3': 'SPINNERS BUILD VALUE — UPPER TARGETS COLLECT JACKPOTS',
            'summary_title_complete': "MANTA'S DEEP-SEA MENACE COMPLETED",
            'summary_title_failed': "MANTA'S DEEP-SEA MENACE ENDED",
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_manta_state',
            'song': 'play_song_40',
        },
        'doctor_atlantean': {
            'title': 'HIGHER GROUND',
            'intro_1': 'THE WATER LEVEL KEEPS RISING',
            'intro_2': 'UPPER TARGETS LOWER THE WATER — ROOF EXITS RAISE IT',
            'intro_3': 'LOWER THE WATER LEVEL TO ZERO',
            'summary_title_complete': 'HIGHER GROUND COMPLETED',
            'summary_title_failed': 'HIGHER GROUND ENDED',
            'stat_1_label': 'CONTROL PANEL JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SPINNER SPINS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'doctor_atlantean_state',
            'song': 'play_song_62',
        },
        'desperado': {
            'title': "DESPERADO'S LAST STAND",
            'intro_1': 'HIT ALL FIVE UNIQUE RIGHT DROP TARGETS',
            'intro_2': 'EACH ROUND ALLOWS ONE MORE SHOT',
            'intro_3': 'COMPLETE THE LEFT BANK TO ADD TEN SECONDS',
            'summary_title_complete': "DESPERADO'S LAST STAND COMPLETED",
            'summary_title_failed': "DESPERADO'S LAST STAND ENDED",
            'stat_1_label': 'RIGHT BANK HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'OUTLAWS CAUGHT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'desperado_state',
            'song': 'play_song_59',
        },
        'devargas': {
            'title': 'CITY OF GOLD',
            'intro_1': 'TWENTY GOLD SHOTS WILL APPEAR',
            'intro_2': 'HIT PULSING SHOTS BEFORE THEY EXPIRE',
            'intro_3': 'FASTER HITS COLLECT MORE GOLD',
            'summary_title_complete': 'CITY OF GOLD COMPLETED',
            'summary_title_failed': 'CITY OF GOLD ENDED',
            'stat_1_label': 'GOLD SHOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'GOLD BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'devargas_state',
            'song': 'play_song_46',
        },
        'molemen': {
            'title': 'UNDERGROUND UPRISING',
            'intro_1': 'TWO-BALL MOLEMEN MULTIBALL',
            'intro_2': 'POPS AND CENTER WEB LIGHT SAUCER JACKPOTS',
            'intro_3': 'MORE HITS LIGHT ADD-A-BALL AT THE SAUCERS',
            'summary_title_complete': 'UNDERGROUND UPRISING COMPLETED',
            'summary_title_failed': 'UNDERGROUND UPRISING ENDED',
            'stat_1_label': 'BIGGEST JACKPOT',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'molemen_state',
            'song': 'play_song_42',
        },
        'charles_cameo': {
            'title': 'IMPOSTOR SYNDROME',
            'intro_1': 'HIT THE LIT SHOT',
            'intro_2': 'HIT ITS MIRROR BEFORE TIME EXPIRES',
            'intro_3': 'COMPLETE THE FINAL WEB PAIR FOR THE SUPER',
            'summary_title_complete': 'IMPOSTOR SYNDROME COMPLETED',
            'summary_title_failed': 'IMPOSTOR SYNDROME ENDED',
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'charles_cameo_state',
            'song': 'play_song_70',
        },
        'brutus': {
            'title': 'BRUTUS BANK BUSTER',
            'intro_1': 'HIT A RIGHT DROP TO LURE BRUTUS',
            'intro_2': 'SHOOT ANY SAUCER BEFORE HE RETURNS',
            'intro_3': "DON'T HIT THE LEFT BANK",
            'summary_title_complete': 'BRUTUS BANK BUSTER COMPLETED',
            'summary_title_failed': 'BRUTUS BANK BUSTER ENDED',
            'stat_1_label': 'ARTWORK JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': '',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'brutus_state',
            'song': 'play_song_76',
        },
        'igor': {
            'title': "IGOR'S CHOICE",
            'intro_1': 'HIT FLASHING GREEN SHOTS FOR JACKPOTS',
            'intro_2': 'AVOID SOLID RED SHOTS',
            'intro_3': 'FIVE BAD SHOTS END THE MODE',
            'summary_title_complete': "IGOR'S CHOICE COMPLETED",
            'summary_title_failed': "IGOR'S CHOICE ENDED",
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'igor_state',
            'song': 'play_song_43',
        },
        'skymaster': {
            'title': 'AERIAL AMBUSH',
            'intro_1': 'DROP ALL EIGHT TARGETS IN ORDER',
            'intro_2': 'UPPER SPINNER DROPS THE NEXT TARGET',
            'intro_3': 'COMPLETE THE SEQUENCE TO LIGHT CENTER WEB SUPER',
            'summary_title_complete': 'AERIAL AMBUSH COMPLETED',
            'summary_title_failed': 'AERIAL AMBUSH ENDED',
            'stat_1_label': 'TARGETS COMPLETED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'WEB SUPERS COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'skymaster_state',
            'completion_var': 'skymaster_defeated',
            'song': 'play_song_9',
        },
        'conners_reptiles': {
            'title': 'REPTILE RAMPAGE',
            'intro_1': 'POPS REVEAL RAMPAGE JACKPOTS',
            'intro_2': 'COLLECT ALL SEVEN',
            'intro_3': 'SHOOT THE DAILY BUGLE FOR THE SWAMP SUPER',
            'summary_title_complete': 'REPTILE RAMPAGE COMPLETED',
            'summary_title_failed': 'REPTILE RAMPAGE ENDED',
            'stat_1_label': 'RAMPAGE JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SWAMP BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'conners_reptiles_state',
            'song': 'play_song_87',
        },
        'sir_galahad': {
            'title': 'KNIGHT MUST FALL',
            'intro_1': 'ENTER THE ROOFTOP AND CHOOSE AN EXIT',
            'intro_2': 'THE EXIT LIGHTS THE OPPOSITE DROP BANK',
            'intro_3': "HIT THE BANK'S CENTER TARGET BEFORE GALAHAD CHARGES",
            'summary_title_complete': 'KNIGHT MUST FALL COMPLETED',
            'summary_title_failed': 'KNIGHT MUST FALL ENDED',
            'stat_1_label': 'JOUST HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BULLSEYES',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'sir_galahad_state',
            'song': 'play_song_90',
        },
        'master_vine': {
            'title': 'THE TANGLED WEB',
            'intro_1': 'ENTER THE ROOFTOP TO START EACH WAVE',
            'intro_2': 'UPPER SPINNER LIGHTS VINE JACKPOTS',
            'intro_3': 'COLLECT THE LIT SHOTS TO CLEAR THREE WAVES',
            'summary_title_complete': 'THE TANGLED WEB COMPLETED',
            'summary_title_failed': 'THE TANGLED WEB ENDED',
            'stat_1_label': 'VINE JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'WAVES COMPLETED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'master_vine_state',
            'song': 'play_song_91',
        },
        'master_technician': {
            'title': "MASTER TECHNICIAN'S SHUTDOWN",
            'intro_1': 'DROPS BUILD SPINNER VALUE',
            'intro_2': 'STOP AT SEVEN AND SPIN TO SCORE',
            'intro_3': 'ALL EIGHT DOWN COSTS TEN SECONDS',
            'summary_title_complete': "MASTER TECHNICIAN'S SHUTDOWN COMPLETED",
            'summary_title_failed': "MASTER TECHNICIAN'S SHUTDOWN ENDED",
            'stat_1_label': 'SPINNER SPINS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SHORT CIRCUITS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'master_technician_state',
            'song': 'play_song_45',
        },
        'spider_men': {
            'title': 'SPIDERS FROM MARS',
            'intro_1': 'HIT SHOTS TO ALIGN THE RAY',
            'intro_2': 'FLIPPERS ROTATE THE ALIGNED LIGHTS',
            'intro_3': 'ALIGN ALL SIX BEFORE TIME EXPIRES',
            'summary_title_complete': 'SPIDERS FROM MARS COMPLETED',
            'summary_title_failed': 'SPIDERS FROM MARS ENDED',
            'stat_1_label': 'ALIGNMENT JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'FINE ADJUSTMENTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'spider_men_state',
            'song': 'play_song_33',
        },
        'von_rantenraven': {
            'title': 'SKY HARBOR ATTACK',
            'intro_1': 'SHOOT ANY SAUCER TO OPEN THE ROOFTOP',
            'intro_2': 'TEN FLIPS TO HIT THREE TARGETS',
            'intro_3': 'ALL THREE SCORES UNUSED FLIPS SUPER',
            'summary_title_complete': 'SKY HARBOR ATTACK COMPLETED',
            'summary_title_failed': 'SKY HARBOR ATTACK ENDED',
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'FLIPS REMAINING',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'von_rantenraven_state',
            'song': 'play_song_52',
        },
        'sinister_surge': {
            'title': 'SINISTER SURGE',
            'intro_1': 'TWO-BALL VILLAIN MULTIBALL',
            'intro_2': 'CLEAR VILLAIN STAGES FOR DAILY BUGLE JACKPOTS',
            'intro_3': 'CLEAR ALL FIVE TO START VICTORY LAPS',
            'summary_title_complete': 'SINISTER SURGE COMPLETED',
            'summary_title_failed': 'SINISTER SURGE ENDED',
            'stat_1_label': 'VILLAIN STAGES CLEARED',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'DAILY BUGLE JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'sinister_surge_state',
            'song': 'play_song_71',
        },
        'mastermind_trap': {
            'title': 'MASTERMIND TRAP',
            'intro_1': 'TWO-BALL VILLAIN MULTIBALL',
            'intro_2': 'PLAY THROUGH THREE COMBINED VILLAIN STAGES',
            'intro_3': 'EITHER WEB COLLECTS SUPER — VALUE DROPS QUICKLY',
            'summary_title_complete': 'MASTERMIND TRAP COMPLETED',
            'summary_title_failed': 'MASTERMIND TRAP ENDED',
            'stat_1_label': 'SCORING HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'mastermind_trap_state',
            'song': 'play_song_58',
        },
        'trubble_unleashed': {
            'title': 'TRUBBLE UNLEASHED',
            'intro_1': 'LEFT DROPS OPEN DIANA OR CENTAUR',
            'intro_2': 'UPPER TARGETS LIGHT SAUCER JACKPOTS',
            'intro_3': 'ALL THREE UPPER TARGETS LIGHT RIGHT EXIT ADD-A-BALL',
            'summary_title_complete': 'TRUBBLE UNLEASHED COMPLETED',
            'summary_title_failed': 'TRUBBLE UNLEASHED ENDED',
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'CYCLOPS JACKPOTS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'trubble_unleashed_state',
            'song': 'play_song_92',
        },
        'plotter': {
            'title': 'THE MASTER PLAN',
            'intro_1': 'POPS BUILD RUMORS',
            'intro_2': 'LOWER SPINNER LIGHTS A SAUCER',
            'intro_3': 'THREE SAUCER JACKPOTS LIGHT THE VUK SUPER',
            'summary_title_complete': 'THE MASTER PLAN COMPLETED',
            'summary_title_failed': 'THE MASTER PLAN ENDED',
            'stat_1_label': 'RUMORS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SAUCER JACKPOTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'plotter_state',
            'song': 'play_song_41',
        },
        'crime_wave': {
            'title': 'CRIME WAVE',
            'intro_1': 'LIGHT THREE AREAS TO OPEN THE ROOFTOP',
            'intro_2': 'ROOF EXITS COLLECT JACKPOTS — MORE AREAS BUILD VALUE',
            'intro_3': 'COLLECT WITH ALL FIVE LIT TO LIGHT A WEB SUPER',
            'summary_title_complete': 'CRIME WAVE COMPLETED',
            'summary_title_failed': 'CRIME WAVE ENDED',
            'stat_1_label': 'MOST AREAS LIT',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'crime_wave_state',
            'song': 'play_song_68',
        },
        'the_web_tightens': {
            'title': 'THE WEB TIGHTENS',
            'intro_1': 'LOCK A BALL AT THE DAILY BUGLE DURING MULTIBALL',
            'intro_2': 'SAUCERS START FIVE VILLAIN PHASES',
            'intro_3': 'PHASE WINS BUILD THE ROOFTOP SUPER JACKPOT',
            'summary_title_complete': 'THE WEB TIGHTENS COMPLETED',
            'summary_title_failed': 'THE WEB TIGHTENS ENDED',
            'stat_1_label': 'PHASES WON',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPER JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'the_web_tightens_state',
            'song': 'play_song_85',
        },
        'fifth_dimension_curse': {
            'title': 'FIFTH DIMENSION CURSE',
            'intro_1': 'KEEP ZONES LIT TO BUILD DAILY BUGLE JACKPOTS',
            'intro_2': 'PARK BALLS IN SAUCERS FOR UPPER RUBY JACKPOTS',
            'intro_3': 'SPINNER LIGHTS ADD-A-BALL — HIT THE FLASHING ROLLOVER',
            'summary_title_complete': 'FIFTH DIMENSION CURSE COMPLETED',
            'summary_title_failed': 'FIFTH DIMENSION CURSE ENDED',
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'RUBIES COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'fifth_dimension_curse_state',
            'song': 'play_song_48',
        },
        'mad_science_meltdown': {
            'title': 'MAD SCIENCE MELTDOWN',
            'intro_1': 'LEFT DROPS RELEASE GAS — LOWER SPINNER COOLS IT',
            'intro_2': 'HIT GREEN GAS ZONES TO COLLECT JACKPOTS',
            'intro_3': 'UPPER TARGETS REVEAL NOAH — HIT THE LAST RIGHT DROP',
            'summary_title_complete': 'MAD SCIENCE MELTDOWN COMPLETED',
            'summary_title_failed': 'MAD SCIENCE MELTDOWN ENDED',
            'stat_1_label': 'GAS JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'NOAH JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'mad_science_meltdown_state',
            'song': 'play_song_3',
        },
        'nature_strikes_back': {
            'title': 'NATURE STRIKES BACK',
            'intro_1': 'SPIN TO CHARGE — UPPER TARGETS LIGHT SAUCER ADD-A-BALL',
            'intro_2': 'CONNECT BOTH WEBS, THEN THAW ALL SIX ZONES',
            'intro_3': 'STAR CLEARS BLOCKS — STABILIZE THE CITY FOR DAILY BUGLE SUPER',
            'summary_title_complete': 'NATURE STRIKES BACK COMPLETED',
            'summary_title_failed': 'NATURE STRIKES BACK ENDED',
            'stat_1_label': 'SUPER JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'AREAS THAWED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'nature_strikes_back_state',
            'song': 'play_song_66',
        },
        'invasion_from_everywhere': {
            'title': 'LOST WORLD INVASION',
            'intro_1': 'LOCK A BALL AT THE DAILY BUGLE',
            'intro_2': 'COMPLETE VILLAIN PHASES TO LAUNCH THE ROOFTOP ATTACK',
            'intro_3': 'UPPER SPINNER BUILDS VALUE — UPPER TARGETS COLLECT JACKPOT',
            'summary_title_complete': 'LOST WORLD INVASION COMPLETED',
            'summary_title_failed': 'LOST WORLD INVASION ENDED',
            'stat_1_label': 'ROOFTOP TARGET HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'ATLANTEAN JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'invasion_from_everywhere_state',
            'song': 'play_song_96',
        },
        'who_is_the_real_villain': {
            'title': 'REAL VILLAIN?',
            'intro_1': 'HIT BOTH POPS — SAUCER REVEALS THE REAL SHOT',
            'intro_2': 'COMPLETE CAMEO, DESPERADO AND BRUTUS',
            'intro_3': 'SHOOT THE DAILY BUGLE FOR THE TIMED SUPER',
            'summary_title_complete': 'REAL VILLAIN? COMPLETED',
            'summary_title_failed': 'REAL VILLAIN? ENDED',
            'stat_1_label': 'CYCLES COMPLETED',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'SUPER JACKPOTS COLLECTED',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'who_is_the_real_villain_state',
            'song': 'play_song_49',
        },
        'time_tossed_showdown': {
            'title': 'TIME-TOSSED SHOWDOWN',
            'intro_1': 'THREE ERAS COLLIDE IN MULTIBALL',
            'intro_2': '12 FLIPS TO BUILD YOUR NEXT BATTLE',
            'intro_3': 'YOUR ROOFTOP EXIT CHOOSES THE VILLAIN',
            'summary_title_complete': 'TIME-TOSSED SHOWDOWN COMPLETED',
            'summary_title_failed': 'TIME-TOSSED SHOWDOWN ENDED',
            'stat_1_label': 'JACKPOTS COLLECTED',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'PHASES COMPLETED',
            'stat_2_var': 'active_mode_stat_1',
            'points_var': 'active_mode_points',
            'state_var': 'time_tossed_showdown_state',
            'song': 'play_song_50',
        },
        'final_showdown': {
            'title': 'KINGPIN',
            'intro_1': "CLEAR FIVE PHASES TO BREAK KINGPIN'S EMPIRE",
            'intro_2': 'LOWER SPINNER SELECTS THE NEXT PHASE',
            'intro_3': 'CLEAR ALL FIVE, THEN SHOOT THE DAILY BUGLE',
            'summary_title_complete': 'KINGPIN COMPLETED',
            'summary_title_failed': 'KINGPIN ENDED',
            'stat_1_label': 'PHASES COMPLETED',
            'stat_1_var': 'final_showdown_areas_cleared',
            'stat_2_label': 'JACKPOTS COLLECTED',
            'stat_2_var': 'final_showdown_jackpots',
            'points_var': 'active_mode_points',
            'state_var': 'final_showdown_state',
            'song': 'play_song_67',
        },
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.current_stage = None
        self.current_done_event = None
        self.current_villain = None
        self.current_summary_can_skip = False
        self.current_summary_skip_unlocked = False
        self.current_comic_chapter = None
        self.summary_vuk_release_pending = False
        self.machine.game.player["villain_summary_vuk_hold_active"] = 0
        # A terminal Jackpot/Super can post immediately before the mode-complete
        # event requests the summary. Keep that final award visible for a full
        # two seconds before the bookend replaces it.
        self.terminal_award_summary_deadline = 0.0
        self.pending_terminal_summary_request = None
        self.last_gameplay_message_time = 0.0

        self.add_mode_event_handler("villain_bookend_intro_request", self._intro_request)
        self.add_mode_event_handler("villain_bookend_summary_request", self._summary_request)
        self.add_mode_event_handler("flipper_cancel", self._skip_current_bookend)
        self.add_mode_event_handler("villain_bookend_intro_hold_request", self._intro_hold_request)
        self.add_mode_event_handler("villain_bookend_intro_hold_release", self._intro_hold_release)
        self.add_mode_event_handler("villain_summary_hold_vuk_until_done", self._hold_vuk_until_summary_done)
        self.add_mode_event_handler("villain_vuk_hold_start", self._start_vuk_hold)
        self.add_mode_event_handler(
            "villain_summary_transfer_vuk_to_mini_wizard",
            self._transfer_vuk_hold_to_mini_wizard,
        )
        self.add_mode_event_handler("villain_summary_hold_saucer_until_done", self._mark_terminal_award)
        self.add_mode_event_handler("villain_summary_delay_for_final_award", self._mark_terminal_award)
        self.add_mode_event_handler("show_mode_message", self._record_gameplay_message)
        self.add_mode_event_handler("show_mode_message_long", self._record_gameplay_message)
        self.add_mode_event_handler("show_mode_jackpot", self._record_gameplay_message)

    def _record_gameplay_message(self, **kwargs):
        """Remember when the active villain last presented a player message."""
        del kwargs
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return
        if not player["villain_mode_running"] or player["villain_mode_in_summary"]:
            return
        self.last_gameplay_message_time = time.monotonic()


    def _mark_terminal_award(self, **kwargs):
        """Guarantee two seconds of final Jackpot/Super presentation.

        Terminal device shots use their existing hold events. Other terminal
        shots explicitly post villain_summary_delay_for_final_award. Record a
        deadline here instead of adding a blind delay after mode completion, so
        the summary waits only for the remainder of the two-second window.
        """
        self.terminal_award_summary_deadline = time.monotonic() + 2.0

    def _hold_vuk_until_summary_done(self, **kwargs):
        """Hold a mode-ending VUK ball until the villain summary finishes.

        The winning mode owns the collect, but VillainBookends owns the exact
        end of the summary for both timeout and flipper speedup paths.
        """
        self._mark_terminal_award()
        self._start_vuk_hold()

    def _start_vuk_hold(self, **kwargs):
        """Interlock the physical VUK coil until the summary releases it."""
        self.summary_vuk_release_pending = True
        self.machine.game.player["villain_summary_vuk_hold_active"] = 1
        # The scoring mode may re-enable Daily Bugle as it stops. Keep Daily
        # Bugle disabled for the full summary so a VUK switch chatter cannot
        # schedule its normal 500 ms eject and defeat this hold.
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
        self.delay.reset(
            name="villain_summary_enforce_vuk_hold",
            ms=10,
            callback=self._enforce_vuk_summary_hold,
        )

    def _enforce_vuk_summary_hold(self):
        if not self.summary_vuk_release_pending:
            return
        self.machine.events.post("disable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")

    def _transfer_vuk_hold_to_mini_wizard(self, **kwargs):
        """Keep a fifth-villain VUK ball held for the chapter-wizard intro."""
        if not self.summary_vuk_release_pending:
            return
        self.summary_vuk_release_pending = False
        self.delay.remove("villain_summary_enforce_vuk_hold")
        self.delay.remove("villain_summary_restore_daily_bugle")
        self.machine.events.post("villain_summary_vuk_hold_transferred_to_mini_wizard")

    def _is_wizard(self, villain):
        return villain in self.UNSKIPPABLE_SUMMARY_VILLAINS

    def _set_wizard_chapter_roster(self, villain):
        """Use the exact definitions and display names used by the chapter panel.

        Snapshot machine variables so test harness starts and chapter transitions
        cannot leave this summary showing another chapter's roster.
        """
        progression = self.machine.modes.get("villain_progression")
        chapter = next((item for item in progression.CHAPTERS
                        if item["mini_wizard_key"] == villain), None) if progression else None
        number = self.COMIC_SUMMARY_VILLAINS.get(villain)
        self._set_machine_var("wizard_bookend_chapter", f"CHAPTER {number}" if number else "FINAL WIZARD")
        for index in range(1, 6):
            name = ""
            if chapter and index <= len(chapter["villains"]):
                key = chapter["villains"][index - 1]
                name = progression.VILLAINS[key]["name"]
            self._set_machine_var(f"wizard_bookend_villain_{index}", name)
        if number and not chapter:
            self.warning_log("Wizard chapter roster unavailable for %s", villain)

    def _intro_request(self, villain=None, start_event=None, **kwargs):
        if villain not in self.VILLAINS:
            self.warning_log("Unknown villain intro requested: %s", villain)
            return

        self.machine.events.post("play_song_14" if self._is_wizard(villain) else "play_villain_intro_music")
        self.machine.game.player["villain_mode_in_summary"] = False

        data = self.VILLAINS[villain]
        self.current_stage = "intro"
        self.current_villain = villain
        self.current_done_event = start_event

        # Mystery's START NEXT VILLAIN award can start Fiddler while its ball
        # is still in the Daily Bugle VUK. Cancel Mystery's normal delayed
        # eject so Fiddler can retain that ball through its WATCH phase.
        if villain == "fiddler" and self._vuk_is_occupied():
            self.machine.events.post("disable_daily_bugle_mystery")
            self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
            self.machine.events.post("cancel_vuk_eject_request")

        self._set_machine_var("villain_bookend_title", data["title"])
        self._set_machine_var("villain_bookend_line_1", data["intro_1"])
        self._set_machine_var("villain_bookend_line_2", data["intro_2"])
        self._set_machine_var("villain_bookend_line_3", data["intro_3"])
        self._set_machine_var("villain_bookend_footer", "HOLD BOTH FLIPPERS TO SKIP")

        self.machine.events.post("villain_bookend_summary_hide")
        self.machine.events.post("wizard_bookend_intro_show" if self._is_wizard(villain) else "villain_bookend_intro_show", villain=villain)

        self.delay.remove("villain_bookend_done")
        self.delay.add(
            name="villain_bookend_done",
            ms=self.WIZARD_INTRO_MS if self._is_wizard(villain) else self.INTRO_MS,
            callback=self._finish_current_bookend
        )

    @staticmethod
    def _safe_number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _format_summary_value(value):
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, int):
            return f"{value:,}"
        if isinstance(value, float) and value.is_integer():
            return f"{int(value):,}"
        return str(value)

    def _summary_request(
        self,
        villain=None,
        done_event=None,
        allow_skip=None,
        chapter_number=None,
        ensure_final_message_hold=False,
        **kwargs,
    ):
        if villain not in self.VILLAINS:
            self.warning_log("Unknown villain summary requested: %s", villain)
            return

        # Repeated completion events cannot restart an already-paid cash-out.
        if self.current_villain == villain and self.current_stage in ("chapter_bonus", "comic_summary"):
            return

        # Successful villain endings use the last gameplay-message timestamp,
        # so every final message gets a full two seconds without adding a
        # second blind delay to modes (such as Centaur) that already wait.
        if ensure_final_message_hold and self.last_gameplay_message_time > 0:
            self.terminal_award_summary_deadline = max(
                self.terminal_award_summary_deadline,
                self.last_gameplay_message_time + 2.0,
            )

        # Leave the final message or explicitly marked terminal award on screen
        # for the remainder of its two-second presentation window.
        remaining = self.terminal_award_summary_deadline - time.monotonic()
        if remaining > 0:
            self.pending_terminal_summary_request = {
                "villain": villain,
                "done_event": done_event,
                "allow_skip": allow_skip,
                "chapter_number": chapter_number,
                "ensure_final_message_hold": ensure_final_message_hold,
                **kwargs,
            }
            self.delay.reset(
                name="villain_terminal_award_summary_delay",
                ms=max(1, int(remaining * 1000 + 0.5)),
                callback=self._run_delayed_terminal_summary,
            )
            return

        self.terminal_award_summary_deadline = 0.0
        self.pending_terminal_summary_request = None
        self.delay.remove("villain_terminal_award_summary_delay")

        self.machine.events.post("play_song_21" if self._is_wizard(villain) else "play_villain_summary_music")
        self.machine.game.player["villain_mode_in_summary"] = True

        if self.summary_vuk_release_pending:
            self._enforce_vuk_summary_hold()

        data = self.VILLAINS[villain]
        state = self._get_player_value(data.get("state_var", ""), 0)
        completion_var = data.get("completion_var", "")
        if completion_var:
            completed = int(self._get_player_value(completion_var, 0)) == 1
        else:
            completed = int(state) == 2
        title = data["summary_title_complete"] if completed else data["summary_title_failed"]

        points = self._get_player_value(data["points_var"], 0)
        stat_count = 3 if villain in self.UNSKIPPABLE_SUMMARY_VILLAINS else int(self._get_player_value("active_mode_stat_count", 3) or 0)
        stat_1 = self._get_player_value(data["stat_1_var"], 0)
        stat_2 = self._get_player_value(data["stat_2_var"], 0)
        if villain == "spider_slayer":
            stat_2 = f"{self._safe_number(stat_2) / 10:.1f} SEC"

        comic_summary = villain in self.COMIC_SUMMARY_VILLAINS
        if comic_summary:
            if chapter_number is None:
                chapter_number = self.COMIC_SUMMARY_VILLAINS[villain]
            self.current_comic_chapter = int(chapter_number)
            self._set_player_comic_key(int(chapter_number))
            self._set_machine_var("wizard_summary_stamp_text", "COLLECTED")
        else:
            self.current_comic_chapter = None
            self._set_player_comic_key(0)
            self._set_machine_var("wizard_summary_stamp_text", "")

        self.current_stage = "summary"
        self.current_villain = villain
        self.current_done_event = done_event or f"{villain}_summary_done"
        if allow_skip is None:
            self.current_summary_can_skip = self._summary_can_be_skipped(villain)
        else:
            self.current_summary_can_skip = bool(allow_skip)

        self._set_machine_var("villain_bookend_title", title)
        if stat_count >= 2 and data.get('stat_1_label', ''):
            self._set_machine_var("villain_bookend_line_1", f"{data['stat_1_label']}: {self._format_summary_value(stat_1)}")
        else:
            self._set_machine_var("villain_bookend_line_1", "")
        stat_2_label = data.get('stat_2_label', '')
        if stat_count >= 3 and stat_2_label:
            self._set_machine_var("villain_bookend_line_2", f"{stat_2_label}: {self._format_summary_value(stat_2)}")
        else:
            self._set_machine_var("villain_bookend_line_2", "")
        self._set_machine_var("villain_bookend_line_3", f"TOTAL MODE POINTS: {points:,}")
        # Do not advertise or accept the double-flipper speedup until the
        # summary has been visible for at least two seconds. This gives the
        # final award callout/SFX a guaranteed minimum presentation window.
        self.current_summary_skip_unlocked = False
        self._set_machine_var("villain_bookend_footer", "")
        self.delay.remove("villain_summary_skip_unlock")
        if self.current_summary_can_skip:
            self.delay.add(
                name="villain_summary_skip_unlock",
                ms=2_000,
                callback=self._unlock_summary_skip,
            )

        self.machine.events.post("villain_bookend_intro_hide")
        # Snapshot the chapter roster before any progression or widget changes.
        if self._is_wizard(villain):
            self._set_machine_var("wizard_bookend_name", data["title"])
            self._set_machine_var("wizard_bookend_score", f"{points:,}")
            self._set_machine_var("wizard_bookend_result", title)
            self._set_wizard_chapter_roster(villain)
        summary_event = (
            "wizard_final_summary_show" if villain == "final_showdown"
            else "wizard_bookend_summary_show" if comic_summary
            else "villain_bookend_summary_show"
        )
        self.machine.events.post(summary_event, villain=villain)
        # Own the playfield lighting for the full summary so stopped gameplay-mode
        # shows cannot bleed through. Wizards use the slower six-second shutdown;
        # ordinary villains get a fast top-to-bottom neutral wipe, then hold dim.
        if villain in self.UNSKIPPABLE_SUMMARY_VILLAINS:
            self.machine.events.post("wizard_bookend_summary_shutdown_start", villain=villain)
        else:
            self.machine.events.post("villain_bookend_summary_wipe_start", villain=villain)

        self.delay.remove("villain_bookend_done")
        self.delay.add(
            name="villain_bookend_done",
            ms=self.WIZARD_SUMMARY_MS if comic_summary else self.SUMMARY_MS,
            callback=self._finish_current_bookend
        )


    def _run_delayed_terminal_summary(self):
        request = self.pending_terminal_summary_request
        self.pending_terminal_summary_request = None
        self.terminal_award_summary_deadline = 0.0
        if not request:
            return
        self._summary_request(**request)

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

        if not villain or villain not in self.VILLAINS:
            self.warning_log("No bookend intro found for current villain: %s", villain)
            return

        data = self.VILLAINS[villain]
        self._set_machine_var("villain_bookend_title", data["title"])
        self._set_machine_var("villain_bookend_line_1", data["intro_1"])
        self._set_machine_var("villain_bookend_line_2", data["intro_2"])
        self._set_machine_var("villain_bookend_line_3", data["intro_3"])
        self._set_machine_var("villain_bookend_footer", "RELEASE FLIPPER TO RETURN")

        self.machine.events.post("wizard_bookend_intro_show" if self._is_wizard(villain) else "villain_bookend_intro_show", villain=villain)

    def _intro_hold_release(self, **kwargs):
        self.machine.events.post("villain_bookend_intro_hide")

    def _skip_current_bookend(self, **kwargs):
        # Intros may always be skipped. Regular villain summaries may be sped up
        # only after their two-second minimum display window. Wizard/chapter-
        # transition summaries that are marked unskippable still run full length.
        if self.current_stage == "intro" or (
            self.current_stage == "summary"
            and self.current_summary_can_skip
            and self.current_summary_skip_unlocked
        ):
            self.delay.remove("villain_bookend_done")
            self.delay.remove("villain_summary_skip_unlock")
            self._finish_current_bookend()

    def _unlock_summary_skip(self):
        if self.current_stage != "summary" or not self.current_summary_can_skip:
            return
        self.current_summary_skip_unlocked = True
        self._set_machine_var("villain_bookend_footer", "HOLD BOTH FLIPPERS TO SPEED UP")

    def _summary_can_be_skipped(self, villain):
        if villain in self.UNSKIPPABLE_SUMMARY_VILLAINS:
            return False

        player = self.machine.game.player if self.machine.game else None
        if not player:
            return True

        try:
            if int(player["chapter_select_waiting_for_summary"]) == 1:
                return False
        except (KeyError, TypeError, ValueError):
            pass

        return True

    def _set_player_comic_key(self, value):
        """Set the Comic Collected selector on the current player."""
        if not self.machine.game or not self.machine.game.player:
            return
        self.machine.game.player["wizard_summary_comic_key"] = int(value)

    def _reassert_player_comic_key(self, chapter_number):
        """Reassert after the widget exists so GMC conditionals see a change."""
        self._set_player_comic_key(chapter_number)

    def _cash_out_wizard_bonus(self):
        """Pay the entire bonus bank once before showing its fixed snapshot."""
        player = self.machine.game.player
        bonus = self.machine.modes["bonus"]
        count = max(0, min(75, int(player["bonus_count"] or 0)))
        multiplier = max(1, min(5, int(player["bonus_multiplier"] or 1)))
        regular = count * 1000 * multiplier
        mode_values = [(name, label, max(0, int(player[name] or 0)))
                       for name, label, _consume in bonus.MODE_BONUS_ENTRIES]
        banked = sum(value for _name, _label, value in mode_values)
        held = max(0, int(player["held_bonus"] or 0))
        remaining = 0
        if self.current_villain == "final_showdown":
            if int(player["final_wizard_remaining_balls"] or 0) > 0:
                remaining = max(0, int(player["final_wizard_remaining_ball_bonus"] or 0))
            player["final_wizard_remaining_balls"] = 0
            player["final_wizard_remaining_ball_bonus"] = 0
        total = regular + banked + held + remaining

        # Consume the snapshot before any display/physical-release events.
        # HOLD BONUS is spent here; it cannot bank another copy of this payout.
        player["bonus_count"] = 0
        player["bonus_multiplier"] = 1
        player["held_bonus"] = 0
        player["hold_bonus"] = 0
        for name, _label, _value in mode_values:
            player[name] = 0
        player["score"] += total
        self.machine.events.post("bonus_lanes_cashout_reset")

        chapter = self.current_comic_chapter
        title = f"CHAPTER {chapter} BONUS" if chapter else "FINAL WIZARD BONUS"
        details = [f"{label}: {value:,}" for _name, label, value in mode_values if value]
        self._set_machine_var("wizard_bonus_title", title)
        self._set_machine_var("wizard_bonus_regular", f"REGULAR BONUS ({multiplier}X): {regular:,}")
        self._set_machine_var("wizard_bonus_modes", f"MODE BONUSES: {banked:,}")
        self._set_machine_var("wizard_bonus_held", f"HELD BONUS: {held:,}")
        self._set_machine_var("wizard_bonus_remaining", f"UNUSED BALLS: {remaining:,}" if remaining else "")
        self._set_machine_var("wizard_bonus_details", "\n".join(details) if details else "NO BANKED MODE BONUSES")
        self._set_machine_var("wizard_bonus_total", f"{total:,}")
        self._set_machine_var("wizard_bonus_score", f"PLAYER {player.number} SCORE: {int(player['score']):,}")
        self.machine.events.post("wizard_chapter_bonus_show", total=total)
        self.machine.events.post("wizard_bonus_cashout_awarded", total=total, regular=regular,
                                 mode_bonus=banked, held=held, remaining=remaining)

    def _finish_current_bookend(self):
        if not self.current_stage:
            return

        done_event = self.current_done_event
        villain = self.current_villain
        stage = self.current_stage
        starting_saucer = None
        starting_vuk = False

        # Keep the existing transition-ball hold until summary, cash-out,
        # and Comic Collected have all finished. The cash-out is atomic.
        if stage == "summary" and self._is_wizard(villain):
            self.current_stage = "chapter_bonus"
            self.machine.events.post("villain_bookend_summary_hide")
            self._cash_out_wizard_bonus()
            self.delay.reset(name="villain_bookend_done", ms=self.CHAPTER_BONUS_MS,
                             callback=self._finish_current_bookend)
            return

        if stage == "chapter_bonus":
            self.machine.events.post("wizard_chapter_bonus_hide")
            if villain not in self.COMIC_SUMMARY_VILLAINS:
                stage = "summary_paid"

        if stage == "chapter_bonus" and villain in self.COMIC_SUMMARY_VILLAINS:
            chapter_number = self.current_comic_chapter or self.COMIC_SUMMARY_VILLAINS[villain]
            self.machine.events.post("villain_bookend_summary_hide")
            # The score summary and full bonus cash-out are now finished, but
            # the three-second Comic COLLECTED cover has not started yet. Chapter
            # wizard physical-ball cleanup belongs at this boundary; the
            # caller's normal done_event intentionally remains deferred until
            # after the Comic screen so progression timing is unchanged.
            self.machine.events.post(
                "chapter_mini_wizard_score_summary_done",
                mini_wizard=villain,
                chapter_number=int(chapter_number),
            )
            # One Comic Collected widget owns all 11 chapter covers. The
            # selector is player-scoped. Clear it before creating the widget,
            # then reassert the chapter after the scene exists so GMC receives
            # a current-player variable change after instantiation.
            self._set_player_comic_key(0)
            self.machine.events.post(
                "wizard_comic_summary_show",
                villain=villain,
                chapter_number=chapter_number,
            )
            self.delay.reset(
                name="wizard_comic_summary_reassert_key",
                ms=25,
                callback=self._reassert_player_comic_key,
                chapter_number=int(chapter_number),
            )
            self.current_stage = "comic_summary"
            self.delay.remove("villain_bookend_done")
            self.delay.add(
                name="villain_bookend_done",
                ms=self.COMIC_SUMMARY_MS,
                callback=self._finish_current_bookend,
            )
            return

        if stage == "intro":
            data = self.VILLAINS[villain]
            if villain == "fiddler":
                starting_vuk = self._vuk_is_occupied()
                if starting_vuk:
                    self.machine.events.post("disable_daily_bugle_mystery")
                    self.machine.events.post("daily_bugle_cancel_vuk_delay_eject")
                    self.machine.events.post("cancel_vuk_eject_request")
                else:
                    starting_saucer = self._occupied_starting_saucer()
            self.machine.events.post(data["song"])
            self.machine.events.post("villain_bookend_intro_hide")
            self.machine.events.post("villain_bookend_intro_done", villain=villain)
        elif stage in ("summary", "summary_paid", "comic_summary"):
            self.machine.game.player["villain_mode_in_summary"] = False
            self.machine.events.post("reset_villain_locate")
            self.machine.events.post("reset_daily_bugle_state")
            if stage == "comic_summary":
                self.machine.events.post("wizard_comic_summary_hide")
            self.machine.events.post("villain_bookend_summary_hide")
            # Snapshot this before posting summary-done. Progression may
            # synchronously transfer the held VUK ball to a newly-qualified
            # chapter wizard, which clears summary_vuk_release_pending so the
            # normal up-kick below is intentionally skipped.
            summary_vuk_was_held = self.summary_vuk_release_pending
            self.machine.events.post(
                "villain_bookend_summary_done",
                villain=villain,
                summary_vuk_held=summary_vuk_was_held,
            )
            self.delay.remove("wizard_comic_summary_reassert_key")
            self._set_player_comic_key(0)
            self._set_machine_var("wizard_summary_stamp_text", "")
            if self.summary_vuk_release_pending:
                self.summary_vuk_release_pending = False
                self.delay.remove("villain_summary_enforce_vuk_hold")
                self.machine.game.player["villain_summary_vuk_hold_active"] = 0
                self.machine.events.post("up_kick")
                self.delay.reset(
                    name="villain_summary_restore_daily_bugle",
                    ms=1_200,
                    callback=self._restore_daily_bugle_after_vuk_release,
                )
            self.machine.events.post("villain_summary_release_saucer_holds")

        # A lower-saucer-started Fiddler uses that same held ball. A VUK start
        # still clears unrelated lower saucers; VUK ownership is handled above.
        # All other villains retain the shared post-intro saucer release.
        if not (stage == "intro" and villain == "fiddler" and starting_saucer):
            self.machine.events.post("clear_saucers_delayed")
        self.delay.remove("villain_summary_skip_unlock")
        self.current_stage = None
        self.current_villain = None
        self.current_done_event = None
        self.current_summary_can_skip = False
        self.current_summary_skip_unlocked = False
        self.current_comic_chapter = None

        if done_event:
            self.machine.events.post(
                done_event,
                villain=villain,
                starting_saucer=starting_saucer,
                starting_vuk=starting_vuk,
            )

    def _occupied_starting_saucer(self):
        """Return the occupied lower saucer number at the end of an intro."""
        for saucer_number in (1, 2, 3):
            switch_name = f"s_saucer_{saucer_number}"
            try:
                if self.machine.switch_controller.is_active(self.machine.switches[switch_name]):
                    return saucer_number
            except (KeyError, TypeError):
                continue
        return None

    def _vuk_is_occupied(self):
        """Return whether the Daily Bugle VUK currently contains a ball."""
        try:
            vuk_switch = self.machine.switches["s_vuk_switch"]
            return bool(self.machine.switch_controller.is_active(vuk_switch))
        except (KeyError, TypeError):
            return False

    def _restore_daily_bugle_after_vuk_release(self):
        player = self.machine.game.player if self.machine.game else None
        if player and int(player["villain_mode_running"]) == 1:
            return
        self.machine.events.post("enable_daily_bugle_mystery")
        self.machine.events.post("daily_bugle_restore_state")

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
