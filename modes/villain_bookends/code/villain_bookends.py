import time

from mpf.core.mode import Mode


class VillainBookends(Mode):

    INTRO_MS = 5000
    SUMMARY_MS = 6000
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
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Build Rage with pop bumper hits.
        #   intro_2: Cash Berserk jackpots at the B rollover.
        #   intro_3: Bigger rage means bigger jackpots.
        #   stat_1_label: BEST JACKPOT
        'rhino': {
            'title': 'RHINO BASH',
            'intro_1': 'POPS BUILD RAGE VALUE',
            'intro_2': 'SWITCHES ADD TO JACKPOT',
            'intro_3': 'COLLECT AT A OR B BEFORE OVERLOAD',
            'summary_title_complete': 'RHINO BASH DEFEATED',
            'summary_title_failed': 'RHINO BASH ESCAPED',
            'stat_1_label': 'Biggest Jackpot',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BEST RAGE',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'rhino_state',
            'song': 'play_song_22',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Shoot the flashing drop target.
        #   intro_2: Hit drops in sequence for bigger value.
        #   intro_3: Complete the run before Sandman reforms.
        'sandman': {
            'title': 'SANDMAN',
            'intro_1': 'HIT THE FLASHING DROP',
            'intro_2': 'CONSECUTIVE HITS SCORE BIGGER',
            'intro_3': 'CLEAR THREE BANKS TO DEFEAT SANDMAN',
            'summary_title_complete': 'SANDMAN DEFEATED',
            'summary_title_failed': 'SANDMAN ESCAPED',
            'stat_1_label': 'DROPS HIT',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BEST RUN',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'sandman_state',
            'song': 'play_song_80',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Get to the rooftop.
        #   intro_2: Hit upper targets to raise spinner value.
        #   intro_3: Spin fast before the targets decay.
        #   stat_2_label: BONUS BANKED
        'vulture': {
            'title': 'VULTURE',
            'intro_1': 'REACH THE ROOFTOP',
            'intro_2': 'UPPER TARGETS BUILD SPINNER VALUE',
            'intro_3': 'SPIN BEFORE THE TARGETS DIM',
            'summary_title_complete': 'VULTURE DEFEATED',
            'summary_title_failed': 'VULTURE ESCAPED',
            'stat_1_label': 'SPINS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'vulture_state',
            'song': 'play_song_10',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Create the antidote at the star rollover.
        #   intro_2: Deliver it to the lit web targets.
        #   intro_3: Move fast before the serum value drains.
        'lizard': {
            'title': 'GREEN LIZARD',
            'intro_1': 'HIT BOTH POPS TO BUILD THE SERUM',
            'intro_2': 'DELIVER AT LEFT WEB BEFORE VALUE DECAYS',
            'intro_3': 'STAR ARMS 10X DURING DELIVERY',
            'summary_title_complete': 'GREEN LIZARD CURED',
            'summary_title_failed': 'GREEN LIZARD ESCAPED',
            'stat_1_label': 'DELIVERIES',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BEST VALUE',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'lizard_state',
            'song': 'play_song_89',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Follow the moving spark.
        #   intro_2: Hit each charged shot before time runs out.
        #   intro_3: The final spark awards Super Jackpot.
        'electro': {
            'title': 'ELECTRO',
            'intro_1': 'FOLLOW THE MOVING SPARK',
            'intro_2': 'HIT EACH LIT SHOT BEFORE IT MOVES',
            'intro_3': 'FINAL SPARK IS THE SUPER JACKPOT',
            'summary_title_complete': 'ELECTRO DEFEATED',
            'summary_title_failed': 'ELECTRO ESCAPED',
            'stat_1_label': 'BEST SPARK',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPER JP',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'electro_state',
            'song': 'play_song_23',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Goblin attacks in chaos multiball.
        #   intro_2: Flashing shots build value. Solid shots cash in.
        #   intro_3: Saucers can rest the battle and bank bonus.
        #   stat_2_label: BONUS BANKED
        'goblin': {
            'title': 'GREEN GOBLIN',
            'intro_1': 'CHAOS MULTIBALL',
            'intro_2': 'SAUCERS BANK CHAOS AND START SAFE PLAY',
            'intro_3': 'FLASHING BUILDS — SOLID REDUCES',
            'summary_title_complete': 'GOBLIN DEFEATED',
            'summary_title_failed': 'GOBLIN ESCAPED',
            'stat_1_label': 'ATTACK TOTAL',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'CHAOS SCORED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'goblin_state',
            'song': 'play_song_7',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Lock tentacle arms with rollovers.
        #   intro_2: Shoot web targets for jackpots.
        #   intro_3: Spinner increases the multiplier.
        'doc_ock': {
            'title': 'DOCTOR OCTOPUS',
            'intro_1': 'LANES AND LEFT BANK LOCK ARMS',
            'intro_2': 'WEB SHOTS SCORE JACKPOTS',
            'intro_3': 'SPINNERS BOOST THE MULTIPLIER',
            'summary_title_complete': 'DOCTOR OCTOPUS DEFEATED',
            'summary_title_failed': 'DOCTOR OCTOPUS ESCAPED',
            'stat_1_label': 'ARMS LOCKED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'doc_ock_state',
            'song': 'play_song_18',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Find the real Mysterio.
        #   intro_2: Wrong shots lower the jackpot value.
        #   intro_3: Use clues to find the Super shot.
        'mysterio': {
            'title': 'MYSTERIO',
            'intro_1': 'FIND THE REAL MYSTERIO',
            'intro_2': 'CLUES POINT LEFT, RIGHT OR UPPER',
            'intro_3': 'WRONG GUESSES REDUCE THE SUPER',
            'summary_title_complete': 'MYSTERIO DEFEATED',
            'summary_title_failed': 'MYSTERIO ESCAPED',
            'stat_1_label': 'CLUES USED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPER JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'mysterio_state',
            'song': 'play_song_63',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Build Venom with the upper spinner.
        #   intro_2: Choose your exit to stage the attack.
        #   intro_3: Hit the staged drop before time runs out.
        'scorpion': {
            'title': 'SCORPION',
            'intro_1': 'ROOFTOP SPINS BUILD STINGER JACKPOT',
            'intro_2': 'EXIT LEFT OR RIGHT TO STAGE DROPS',
            'intro_3': 'HIT FLASHING DROP TARGET FOR JACKPOT',
            'summary_title_complete': 'SCORPION DEFEATED',
            'summary_title_failed': 'SCORPION ESCAPED',
            'stat_1_label': 'STINGS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JP',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'scorpion_state',
            'song': 'play_song_72',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Parafino's wax traps the city.
        #   intro_2: Build zone jackpots with drops and pops.
        #   intro_3: Cash saucers. Three hits lights add-a-ball.
        'parafino': {
            'title': 'PARAFINO',
            'intro_1': 'HIT DROPS AND POPS TO HEAT ZONES',
            'intro_2': 'SAUCERS COLLECT ZONE JACKPOTS',
            'intro_3': 'THREE ZONE HITS LIGHT ADD-A-BALL',
            'summary_title_complete': 'PARAFINO DEFEATED',
            'summary_title_failed': 'PARAFINO ESCAPED',
            'stat_1_label': 'ZONE HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'parafino_state',
            'song': 'play_song_19',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Hit upper targets to wake the three heads.
        #   intro_2: Lit saucers collect jackpots.
        #   intro_3: The matching saucer scores double.
        'cerberus': {
            'title': 'CERBERUS',
            'intro_1': 'DROPS LIGHT MATCHING SAUCERS',
            'intro_2': 'UPPER TARGETS LIGHT THEM AT 2X',
            'intro_3': 'COLLECT THREE JACKPOTS TO DEFEAT',
            'summary_title_complete': 'CERBERUS DEFEATED',
            'summary_title_failed': 'CERBERUS ESCAPED',
            'stat_1_label': 'TARGETS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'cerberus_state',
            'song': 'play_song_29',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Multiball erupts across the playfield.
        #   intro_2: Spinners build the Vulcan Jackpot.
        #   intro_3: Right drops collect. Upper targets add balls.
        #   stat_2_label: BONUS BANKED
        'vulcan': {
            'title': 'VULCAN',
            'intro_1': 'ERUPTION MULTIBALL',
            'intro_2': 'UPPER TARGETS BUILD DROP VALUE',
            'intro_3': 'TARGET ADDS BALLS AFTER DROP BANK',
            'summary_title_complete': 'VULCAN DEFEATED',
            'summary_title_failed': 'VULCAN ESCAPED',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'vulcan_state',
            'song': 'play_song_64',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Diana takes aim with Trubble's arrows.
        #   intro_2: Use the post-release timed shot.
        #   intro_3: Hit the arrow target before time runs out.
        'diana': {
            'title': 'DIANA',
            'intro_1': 'FLIPPERS USE ARROWS',
            'intro_2': 'UPPER SPINNER ADDS ARROWS',
            'intro_3': 'EITHER EXIT STARTS THE DROP HUNT',
            'summary_title_complete': 'DIANA DEFEATED',
            'summary_title_failed': 'DIANA ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BULLSEYES',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'diana_state',
            'song': 'play_song_30',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The center web target is the Cyclops Eye.
        #   intro_2: You have limited flips. Drops add flips.
        #   intro_3: Hit the Eye for remaining flips x 100K.
        'cyclops': {
            'title': 'CYCLOPS',
            'intro_1': 'FLIPPERS USE LIMITED FLIPS',
            'intro_2': 'DROPS ADD 3 — RUBBERS ADD 1',
            'intro_3': 'CENTER WEB SCORES 100,000 PER FLIP LEFT',
            'summary_title_complete': 'CYCLOPS DEFEATED',
            'summary_title_failed': 'CYCLOPS ESCAPED',
            'stat_1_label': 'BEST JP',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'FLIPS LEFT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'cyclops_state',
            'song': 'play_song_55',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Drop targets build the Centaur Jackpot.
        #   intro_2: Four drops open the gate to the roof.
        #   intro_3: Exit left and hit the staged rubber shot.
        #   stat_1_label: DROPS DOWN
        'centaur': {
            'title': 'CENTAUR CHARGE',
            'intro_1': 'DROPS BUILD CENTAUR JACKPOT',
            'intro_2': 'FOUR DROPS OPEN THE ROOFTOP',
            'intro_3': 'EXIT LEFT THEN HIT THE RIGHT RUBBER',
            'summary_title_complete': 'CENTAUR CHARGE TRAPPED',
            'summary_title_failed': 'CENTAUR CHARGE ESCAPED',
            'stat_1_label': 'DROPS DOWN',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BEST JP',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'centaur_state',
            'song': 'play_song_31',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Skymaster Brothers are framing Spider-Man.
        #   intro_2: Hit paired wall-crawler shots before they move.
        #   intro_3: Clear both flies to stop the frame-up.
        #   stat_2_label: MAJOR HITS
        'fly_twins': {
            'title': 'THE FLY TWINS',
            'intro_1': 'ROOFTOP MULTIBALL',
            'intro_2': 'UPPER TARGETS LIGHT SAUCER JACKPOTS',
            'intro_3': 'SPINNER BUILDS — CATCH BOTH FOR SUPER',
            'summary_title_complete': 'THE FLY TWINS CAUGHT',
            'summary_title_failed': 'THE FLY TWINS ESCAPED',
            'stat_1_label': 'ROUNDS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'fly_twins_state',
            'song': 'play_song_32',
        },
        # ORIGINAL DISPLAY TEXT:
        #   title: FIFTH AVENUE PHANTOM
        #   intro_1: Drop the right bank to reveal the Phantom.
        #   intro_2: Catch him while the hidden shot is lit.
        #   intro_3: Early catches score bigger jackpots.
        #   summary_title_complete: PHANTOM CAPTURED
        'fifth_avenue_phantom': {
            'title': 'THE FIFTH AVENUE PHANTOM',
            'intro_1': 'RIGHT DROPS REVEAL PHANTOM LOCATION',
            'intro_2': 'HIT IT BEFORE TIME RUNS OUT',
            'intro_3': 'MORE DROPS ADD TIME BUT REDUCE VALUE',
            'summary_title_complete': 'THE FIFTH AVENUE PHANTOM CAUGHT',
            'summary_title_failed': 'THE FIFTH AVENUE PHANTOM VANISHED',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BEST JP',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'fifth_avenue_phantom_state',
            'song': 'play_song_60',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Work the crime zones: drops, pops, and right bank.
        #   intro_2: Zone hits light upper-target jackpots.
        #   intro_3: Collect all three, then hit OX at center web.
        #   summary_title_complete: THE GANG IS BROKEN
        'enforcers': {
            'title': 'THE ENFORCERS',
            'intro_1': 'DROPS AND POPS LIGHT UPPER JACKPOTS',
            'intro_2': 'COLLECT ALL THREE THEN HIT CENTER WEB',
            'intro_3': 'UPPER SPINNER BUILDS THE OX SUPER',
            'summary_title_complete': 'GANG BROKEN',
            'summary_title_failed': 'OX GOT AWAY',
            'stat_1_label': 'UPPER JPS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'OX SUPER',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'enforcers_state',
            'song': 'play_song_39',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Hit drops to build the Diamond Jackpot.
        #   intro_2: Complete the 5-bank to start saucer chase.
        #   intro_3: Star rollover lights all saucers briefly.
        #   stat_2_label: BONUS BANKED
        'doctor_cool': {
            'title': 'DOCTOR COOL',
            'intro_1': 'DROP TARGETS BUILD DIAMOND JACKPOT',
            'intro_2': 'COMPLETE DROPS TO ADD DIAMONDS',
            'intro_3': 'STAR FREEZES LIT SAUCERS FOR COLLECT',
            'summary_title_complete': 'DOCTOR COOL DEFEATED',
            'summary_title_failed': 'DIAMONDS SMUGGLED AWAY',
            'stat_1_label': 'SHIPMENTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'DIAMONDS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'doctor_cool_state',
            'song': 'play_song_56',
        },
        'harley_clivendon': {
            'title': 'HARLEY CLIVENDON', 'intro_1': 'LOCK A BALL DURING MULTIBALL', 'intro_2': 'LIGHT AREAS TO BUILD JACKPOT', 'intro_3': 'COLLECT JACKPOT AT DAILY BUGLE',
            'summary_title_complete': 'HARLEY CLIVENDON MODE COMPLETE', 'summary_title_failed': 'HARLEY CLIVENDON MODE COMPLETE',
            'stat_1_label': 'VUK JACKPOTS', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'BONUS BANKED', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'harley_clivendon_state', 'song': 'play_song_51',
        },
        'conquistador': {
            'title': 'THE CONQUISTADOR', 'intro_1': 'HIT ANY LEFT DROP TO OPEN ROOFTOP', 'intro_2': 'SPIN TO LOCATE, TARGETS BUILD', 'intro_3': 'FOUNTAIN JACKPOT AT CENTER WEB',
            'summary_title_complete': 'CONQUISTADOR COMPLETE', 'summary_title_failed': 'CONQUISTADOR COMPLETE',
            'stat_1_label': 'FOUNTAIN JACKPOTS', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'SPEED BONUS', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'conquistador_state', 'song': 'play_song_54',
        },
        'spider_slayer': {
            'title': 'SPIDER-SLAYER', 'intro_1': 'HIT 15 LIT SHOTS TO EXPOSE IT', 'intro_2': 'COLLECT JACKPOT AT DAILY BUGLE', 'intro_3': 'BEFORE TIME EXPIRES',
            'summary_title_complete': 'SPIDER-SLAYER MODE COMPLETE', 'summary_title_failed': 'SPIDER-SLAYER MODE COMPLETE',
            'stat_1_label': 'SLAYER JACKPOT', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'HUNT TIME', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'spider_slayer_state', 'song': 'play_song_84',
        },
        'metal_eating_robot': {
            'title': 'THE METAL-EATING ROBOT', 'intro_1': 'ZONE ATTACKS EVERY 5 SECONDS', 'intro_2': 'HIT FLASHING ZONES TO SAVE THEM', 'intro_3': 'SAVE 4 BEFORE 3 ARE DESTROYED',
            'summary_title_complete': 'THE METAL-EATING ROBOT MODE COMPLETE', 'summary_title_failed': 'THE METAL-EATING ROBOT MODE COMPLETE',
            'stat_1_label': 'ZONES SAVED', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'ZONES DESTROYED', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'metal_eating_robot_state', 'song': 'play_song_88',
        },
        'fiddler': {
            'title': 'FIDDLER', 'intro_1': 'SHOOT A SAUCER TO WATCH THE PATTERN', 'intro_2': 'REPEAT THE NOTES IN ORDER', 'intro_3': '3 WRONG PATTERNS ENDS THE MODE',
            'summary_title_complete': 'FIDDLER MODE COMPLETE', 'summary_title_failed': 'FIDDLER MODE COMPLETE',
            'stat_1_label': 'PATTERNS', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'NOTES HIT', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'fiddler_state', 'completion_var': 'active_mode_completed', 'song': 'play_song_25',
        },
        'pardo': {
            'title': 'PARDO',
            'intro_1': 'GUESS THE SECRET SHOT',
            'intro_2': 'SPINNER REVEALS THE RIGHT ONE',
            'intro_3': 'LESS POINTS FOR 2ND GUESSES',
            'summary_title_complete': 'PARDO MODE COMPLETE',
            'summary_title_failed': 'PARDO MODE COMPLETE',
            'stat_1_label': '1ST-GUESS JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': '2ND-GUESS JACKPOTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'pardo_state',
            'completion_var': 'active_mode_completed',
            'song': 'play_song_53',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Two-ball multiball: the saucers hide fake rubies.
        #   intro_2: Lock a saucer ball to open the roof and reveal the real ruby.
        #   intro_3: Collect three Ruby Jackpots, then the fourth reveal is Super.
        'fakir': {
            'title': 'THE FANTASTIC FAKIR',
            'intro_1': 'MULTIBALL RUBY HEIST',
            'intro_2': 'SAUCERS REVEAL UPPER RUBIES',
            'intro_3': 'SPINNERS BUILD RUBY JACKPOTS',
            'summary_title_complete': 'FANTASTIC FAKIR MODE COMPLETE',
            'summary_title_failed': 'FANTASTIC FAKIR MODE COMPLETE',
            'stat_1_label': 'RUBIES',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPERS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'fakir_state',
            'song': 'play_song_34',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The Kotep summons strange magic.
        #   intro_2: Hit the lit mystic shots to break the spell.
        #   intro_3: Complete the pattern before the curse spreads.
        #   stat_2_label: MAJOR HITS
        'kotep': {
            'title': 'KOTEP',
            'intro_1': 'DEMONS APPEAR EVERY 4 SECONDS',
            'intro_2': 'DESTROY 4 FLASHING DEMONS',
            'intro_3': 'COLLECT SCEPTER SUPER AT DAILY BUGLE',
            'summary_title_complete': 'KOTEP MODE COMPLETE',
            'summary_title_failed': 'KOTEP MODE COMPLETE',
            'stat_1_label': 'DEMONS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPERS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'kotep_state',
            'completion_var': 'active_mode_completed',
            'song': 'play_song_35',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The Super Swami bends minds across the city.
        #   intro_2: Follow the moving shot and break his control.
        #   intro_3: Complete the sequence to stop the trance.
        #   stat_2_label: BONUS BANKED
        'super_swami': {
            'title': 'SUPER SWAMI',
            'intro_1': 'NEW YORK HAS GONE DARK',
            'intro_2': 'HIT EACH OF THE 6 CITY AREAS',
            'intro_3': 'RESTORE THEM BEFORE TIME EXPIRES',
            'summary_title_complete': 'SUPER SWAMI MODE COMPLETE',
            'summary_title_failed': 'SUPER SWAMI MODE COMPLETE',
            'stat_1_label': 'AREAS RESTORED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'super_swami_state',
            'song': 'play_song_73',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Frog Ghosts slip through the Fifth Dimension.
        #   intro_2: Hit the haunted shots before they move.
        #   intro_3: Clear the ghosts and seal the rift.
        #   stat_2_label: MAJOR HITS
        'infinata': {
            'title': 'INFINATA',
            'intro_1': 'HIT FLASHING SHOTS TO BANISH CREATURES',
            'intro_2': 'CLEAR 3 CREATURE AREAS',
            'intro_3': 'COLLECT SUPER AT ANY SAUCER',
            'summary_title_complete': 'INFINATA MODE COMPLETE',
            'summary_title_failed': 'INFINATA MODE COMPLETE',
            'stat_1_label': 'AREAS CLEARED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPERS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'infinata_state',
            'song': 'play_song_24',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Noah Boddy vanishes from sight.
        #   intro_2: Use upper clues to find the hidden target.
        #   intro_3: Hit the true drop before he disappears.
        #   stat_1_label: UPPER HITS
        'noah_boddy': {
            'title': 'DR. NOAH BODDY',
            'intro_1': 'REACH ROOFTOP TO BEGIN THE SEARCH',
            'intro_2': 'UPPER TARGETS REVEAL THE SECRET DROP',
            'intro_3': 'HIT DROP FOR SPINNER JACKPOT',
            'summary_title_complete': 'DR. NOAH BODDY MODE COMPLETE',
            'summary_title_failed': 'DR. NOAH BODDY MODE COMPLETE',
            'stat_1_label': 'SPINNER SPINS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'noah_boddy_state',
            'song': 'play_song_36',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Magnetic force pulls shots around the city.
        #   intro_2: Use the spinner to stabilize the field.
        #   intro_3: Cash the lit shot before it moves.
        #   stat_2_label: MAJOR HITS
        'dr_magneto': {
            'title': 'DR. MAGNETO',
            'intro_1': 'SLINGS AND INLANES LIGHT A AND B',
            'intro_2': 'COLLECT A AND B THEN HIT MATCHING POPS',
            'intro_3': 'BOTH POPS LIGHT CENTER WEB SUPER',
            'summary_title_complete': 'DR. MAGNETO MODE COMPLETE',
            'summary_title_failed': 'DR. MAGNETO MODE COMPLETE',
            'stat_1_label': 'CIRCUIT SHOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPERS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_magneto_state',
            'song': 'play_song_27',
        },
        # ORIGINAL DISPLAY TEXT:
        #   title: PROFESSOR PRETORIUS
        #   intro_1: Pretorius is shrinking the city.
        #   intro_2: Solve the shot puzzle before the ray fires.
        #   intro_3: Beat the sequence and restore the landmark.
        #   stat_2_label: MAJOR HITS
        'professor_pretorius': {
            'title': 'PROFESSOR PRETORIUS',
            'intro_1': 'HIT POPS AND DROPS TO RUN THE REACTOR',
            'intro_2': 'SPINNER COOLS IT BEFORE OVERHEAT',
            'intro_3': '4 STATIONS LIGHT DAILY BUGLE SUPER',
            'summary_title_complete': 'PROFESSOR PRETORIUS MODE COMPLETE',
            'summary_title_failed': 'PROFESSOR PRETORIUS MODE COMPLETE',
            'stat_1_label': 'REACTOR HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPERS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'professor_pretorius_state',
            'song': 'play_song_28',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Doctor Dumpty has a fragile plan.
        #   intro_2: Build value without cracking the sequence.
        #   intro_3: Wrong shots break the egg.
        'doctor_dumpty': {
            'title': 'DOCTOR DUMPTY',
            'intro_1': 'LEFT DROPS REVEAL LAUGHING GAS',
            'intro_2': 'CLEAR 3 GAS AREAS TO OPEN ROOFTOP',
            'intro_3': 'SPINNER BUILDS — UPPER TARGETS POP BALLOONS',
            'summary_title_complete': 'DOCTOR DUMPTY MODE COMPLETE',
            'summary_title_failed': 'DOCTOR DUMPTY MODE COMPLETE',
            'stat_1_label': 'BALLOONS POPPED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MISSES',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'doctor_dumpty_state',
            'song': 'play_song_37',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Von Schlick has slicked the playfield.
        #   intro_2: Control the sequence before shots slip away.
        #   intro_3: Finish the pattern to end the oil scheme.
        #   stat_2_label: MAJOR HITS
        'dr_von_schlick': {
            'title': 'DR. VON SCHLICK',
            'intro_1': 'HIT THE ROAMING GREEN SHOTS',
            'intro_2': '5 SHOTS OPENS THE REACTOR',
            'intro_3': 'FLOOD REACTOR AT DAILY BUGLE FOR SUPER',
            'summary_title_complete': 'DR. VON SCHLICK MODE COMPLETE',
            'summary_title_failed': 'DR. VON SCHLICK MODE COMPLETE',
            'stat_1_label': 'OIL PELLETS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPERS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_von_schlick_state',
            'song': 'play_song_8',
        },
        # ORIGINAL DISPLAY TEXT:
        #   title: CLIVE AND BLOTTO
        #   intro_1: Clive unleashes the shape-changing Blotto.
        #   intro_2: Hit containment shots before it spreads.
        #   intro_3: Trap the creature and stop the rampage.
        #   stat_2_label: BONUS BANKED
        'clive_blotto': {
            'title': 'CLIVE AND BLOTTO',
            'intro_1': 'BLOTTO METER IS ON THE RISE',
            'intro_2': 'SPINNERS LOWER THE METER',
            'intro_3': 'CLEAR INFECTED AREAS — EMPTY METER WINS',
            'summary_title_complete': 'CLIVE AND BLOTTO MODE COMPLETE',
            'summary_title_failed': 'CLIVE AND BLOTTO MODE COMPLETE',
            'stat_1_label': 'AREAS CLEARED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BLOTTO ATTACKS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'clive_blotto_state',
            'song': 'play_song_57',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Dr. Zap chains electricity across shots.
        #   intro_2: Follow the lit charge pattern.
        #   intro_3: Break the circuit before it overloads.
        #   stat_2_label: MAJOR HITS
        'dr_zapp': {
            'title': 'DOCTOR ZAPP',
            'intro_1': 'HIT A TARGET IN EACH BANK',
            'intro_2': 'UPPER TARGETS MULTIPLY THE FLASHES',
            'intro_3': 'UPPER SPINNER COLLECTS SPINS',
            'summary_title_complete': 'DOCTOR ZAPP MODE COMPLETE',
            'summary_title_failed': 'DOCTOR ZAPP MODE COMPLETE',
            'stat_1_label': 'CAMERA FLASHES',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SPINNER SPINS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_zapp_state',
            'song': 'play_song_38',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Bolton and Boomer hide their robberies inside a violent storm.
        #   intro_2: Follow the thunder and stop the next strike.
        #   intro_3: Break up the scheme before the storm passes.
        #   stat_2_label: MAJOR HITS
        'bolton_boomer': {
            'title': 'BOLTON AND BOOMER',
            'intro_1': 'MULTIBALL TARGET ATTACK',
            'intro_2': 'HIT LIT TARGET THEN LOCK A SAUCER',
            'intro_3': 'COLLECT SUPER AT DAILY BUGLE',
            'summary_title_complete': 'BOLTON AND BOOMER MODE COMPLETE',
            'summary_title_failed': 'BOLTON AND BOOMER MODE COMPLETE',
            'stat_1_label': 'SUPERS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST SUPER',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'bolton_boomer_state',
            'song': 'play_song_94',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The Snowman is freezing the city.
        #   intro_2: Thaw frozen shots with spinner and targets.
        #   intro_3: Break the freeze before time runs out.
        #   stat_2_label: MAJOR HITS
        'snowman': {
            'title': 'THE SNOWMAN',
            'intro_1': 'CONNECT LEFT AND CENTER WEBS',
            'intro_2': 'HIT LOWER SPINNER TO DEFEAT SNOWMAN',
            'intro_3': 'KEEP SPINNING FOR BONUS POINTS',
            'summary_title_complete': 'THE SNOWMAN MODE COMPLETE',
            'summary_title_failed': 'THE SNOWMAN MODE COMPLETE',
            'stat_1_label': 'BONUS SPINS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST SPIN',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'snowman_state',
            'song': 'play_song_2',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The Plutonians blocks the city in frozen chaos.
        #   intro_2: Hit thaw shots to open scoring.
        #   intro_3: Collect the jackpot before everything freezes.
        #   stat_2_label: MAJOR HITS
        'plutonians': {
            'title': 'THE PLUTONIANS',
            'intro_1': 'THAW ALL SIX FROZEN AREAS',
            'intro_2': 'UPPER TARGETS DISABLE THE FREEZE RAY',
            'intro_3': 'KEEP THEM THAWED TO WIN',
            'summary_title_complete': 'THE PLUTONIANS MODE COMPLETE',
            'summary_title_failed': 'THE PLUTONIANS MODE COMPLETE',
            'stat_1_label': 'TOTAL THAWS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'RAY BLOCKS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'plutonians_state',
            'song': 'play_song_47',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Dr. Manta traps the city beneath the waves.
        #   intro_2: Escape saucer traps with lit rescue shots.
        #   intro_3: Collect the jackpot before he dives again.
        #   stat_2_label: MAJOR HITS
        'dr_manta': {
            'title': 'DR. MANTA',
            'intro_1': 'LOCK BALL 1 AT DAILY BUGLE',
            'intro_2': 'LOCK BALL 2 IN ANY SAUCER',
            'intro_3': 'SPINNERS BUILD UPPER TARGET JACKPOTS',
            'summary_title_complete': 'DR. MANTA MODE COMPLETE',
            'summary_title_failed': 'DR. MANTA MODE COMPLETE',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_manta_state',
            'song': 'play_song_40',
        },
        'doctor_atlantean': {
            'title': 'DOCTOR ATLANTEAN',
            'intro_1': 'WATER LEVEL IS ON THE RISE',
            'intro_2': 'UPPER TARGETS LOWER, EXITS RAISE IT',
            'intro_3': 'REACH ZERO TO WIN',
            'summary_title_complete': 'DOCTOR ATLANTEAN MODE COMPLETE',
            'summary_title_failed': 'DOCTOR ATLANTEAN MODE COMPLETE',
            'stat_1_label': 'CONTROL JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SPINNER SPINS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'doctor_atlantean_state',
            'song': 'play_song_62',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Desperado attacks from above the clouds.
        #   intro_2: Find the moving flight path.
        #   intro_3: Hit the lit shots and ground his aircraft.
        #   stat_2_label: MAJOR HITS
        'desperado': {
            'title': 'DESPERADO',
            'intro_1': 'HIT 5 UNIQUE RIGHT DROP TARGETS',
            'intro_2': 'EACH ROUND ALLOWS ONE MORE SHOT',
            'intro_3': 'LEFT BANK ADDS 10 SECONDS',
            'summary_title_complete': 'DESPERADO MODE COMPLETE',
            'summary_title_failed': 'DESPERADO MODE COMPLETE',
            'stat_1_label': 'BANK HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'OUTLAWS CAUGHT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'desperado_state',
            'song': 'play_song_59',
        },
        'devargas': {
            'title': 'DEVARGAS',
            'intro_1': '20 GOLD SHOTS WILL APPEAR',
            'intro_2': 'HIT PULSING SHOTS BEFORE THEY EXPIRE',
            'intro_3': 'FASTER HITS SCORE MORE GOLD',
            'summary_title_complete': 'DEVARGAS MODE COMPLETE',
            'summary_title_failed': 'DEVARGAS MODE COMPLETE',
            'stat_1_label': 'GOLD SHOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'GOLD BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'devargas_state',
            'song': 'play_song_46',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Molemen strike from the ice.
        #   intro_2: Hit rescue shots before the freeze spreads.
        #   intro_3: Finish the sequence and escape the trap.
        #   stat_2_label: MAJOR HITS
        'molemen': {
            'title': 'THE MOLEMEN',
            'intro_1': 'MULTIBALL MOLEMEN ATTACK',
            'intro_2': 'POPS AND CENTER WEB LIGHT SAUCER JACKPOTS',
            'intro_3': 'MORE HITS LIGHTS ADD-A-BALL',
            'summary_title_complete': 'THE MOLEMEN MODE COMPLETE',
            'summary_title_failed': 'THE MOLEMEN MODE COMPLETE',
            'stat_1_label': 'BIGGEST JACKPOT',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'molemen_state',
            'song': 'play_song_42',
        },
        'charles_cameo': {
            'title': 'CHARLES CAMEO',
            'intro_1': 'HIT THE LIT SHOT',
            'intro_2': 'HIT ITS MIRROR BEFORE TIME EXPIRES',
            'intro_3': 'COMPLETE ALL PAIRS FOR WEB SUPER',
            'summary_title_complete': 'CHARLES CAMEO MODE COMPLETE',
            'summary_title_failed': 'CHARLES CAMEO MODE COMPLETE',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'charles_cameo_state',
            'song': 'play_song_70',
        },
        'brutus': {
            'title': 'BRUTUS',
            'intro_1': 'HIT RIGHT DROP TO LURE BRUTUS',
            'intro_2': 'SHOOT ANY SAUCER BEFORE HE RETURNS',
            'intro_3': 'COLLECT 3 ARTWORK JACKPOTS',
            'summary_title_complete': 'BRUTUS MODE COMPLETE',
            'summary_title_failed': 'BRUTUS MODE COMPLETE',
            'stat_1_label': 'ARTWORK JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'brutus_state',
            'song': 'play_song_76',
        },
        'igor': {
            'title': 'IGOR',
            'intro_1': 'HIT FLASHING GREEN SHOTS',
            'intro_2': 'AVOID SOLID RED SHOTS',
            'intro_3': '5 BAD SHOTS ENDS THE MODE',
            'summary_title_complete': 'IGOR MODE COMPLETE',
            'summary_title_failed': 'IGOR MODE COMPLETE',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JACKPOT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'igor_state',
            'song': 'play_song_43',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Skymaster crawls across the city walls.
        #   intro_2: Track the moving shot and cut him off.
        #   intro_3: Catch him before he slips away.
        #   stat_2_label: MAJOR HITS
        'skymaster': {
            'title': 'SKYMASTER',
            'intro_1': 'DROP ALL 8 TARGETS IN ORDER',
            'intro_2': 'UPPER SPINNER DROPS THE NEXT',
            'intro_3': 'WRONG TARGET RESETS ITS BANK',
            'summary_title_complete': 'SKYMASTER MODE COMPLETE',
            'summary_title_failed': 'SKYMASTER MODE COMPLETE',
            'stat_1_label': 'TARGETS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'WEB SUPERS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'skymaster_state',
            'completion_var': 'skymaster_defeated',
            'song': 'play_song_9',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Conner's Reptiles are loose in the city.
        #   intro_2: Hit pops to light Rampage Jackpots.
        #   intro_3: Collect the Super Jackpot at the saucer.
        #   stat_2_label: BONUS BANKED
        'conners_reptiles': {
            'title': "CONNER'S REPTILES",
            'intro_1': 'POPS REVEAL RAMPAGE JACKPOTS',
            'intro_2': 'COLLECT ALL 7 RAMPAGE JACKPOTS',
            'intro_3': 'SHOOT VUK FOR SWAMP SUPER',
            'summary_title_complete': "CONNER'S REPTILES MODE COMPLETE",
            'summary_title_failed': "CONNER'S REPTILES MODE COMPLETE",
            'stat_1_label': 'RAMPAGE JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SWAMP BONUS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'conners_reptiles_state',
            'song': 'play_song_87',
        },
        # ORIGINAL DISPLAY TEXT:
        #   title: PHANTOM FROM THE DEPTHS OF TIME
        #   intro_1: The Phantom rises from another age.
        #   intro_2: Follow the time-tossed shots.
        #   intro_3: Complete the sequence before he fades away.
        #   summary_title_complete: PHANTOM DEFEATED
        #   summary_title_failed: PHANTOM ESCAPED
        #   stat_2_label: MAJOR HITS
        'sir_galahad': {
            'title': 'SIR GALAHAD',
            'intro_1': 'ENTER ROOFTOP AND CHOOSE AN EXIT',
            'intro_2': 'EXIT LIGHTS OPPOSITE DROP BANK',
            'intro_3': 'AIM FOR CENTER BEFORE GALAHAD CHARGES',
            'summary_title_complete': 'SIR GALAHAD MODE COMPLETE',
            'summary_title_failed': 'SIR GALAHAD MODE COMPLETE',
            'stat_1_label': 'JOUST HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BULLSEYES',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'sir_galahad_state',
            'song': 'play_song_90',
        },
        'master_vine': {
            'title': 'MASTER VINE',
            'intro_1': 'ENTER ROOFTOP TO START EACH WAVE',
            'intro_2': 'UPPER SPINNER LIGHTS VINE JACKPOTS',
            'intro_3': 'COLLECT LIT SHOTS — CLEAR 3 WAVES',
            'summary_title_complete': 'MASTER VINE MODE COMPLETE',
            'summary_title_failed': 'MASTER VINE MODE COMPLETE',
            'stat_1_label': 'VINE JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'WAVES',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'master_vine_state',
            'song': 'play_song_91',
        },
        'master_technician': {
            'title': 'MASTER TECHNICIAN',
            'intro_1': 'DROPS BUILD SPINNER VALUE',
            'intro_2': 'STOP AT 7 AND SHOOT SPINNER',
            'intro_3': 'ALL 8 DOWN COSTS 10 SECONDS',
            'summary_title_complete': 'MASTER TECHNICIAN MODE COMPLETE',
            'summary_title_failed': 'MASTER TECHNICIAN MODE COMPLETE',
            'stat_1_label': 'SPINNER HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SHORT CIRCUITS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'master_technician_state',
            'song': 'play_song_45',
        },
        'spider_men': {
            'title': 'THE SPIDER-MEN',
            'intro_1': 'LIGHT THE SHOTS TO ALIGN THE RAY',
            'intro_2': 'FLIPPERS ROTATE THE LIGHTS',
            'intro_3': 'LIGHT ALL 6 BEFORE TIME EXPIRES',
            'summary_title_complete': 'THE SPIDER-MEN MODE COMPLETE',
            'summary_title_failed': 'THE SPIDER-MEN MODE COMPLETE',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'FINE ADJUSTMENTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'spider_men_state',
            'song': 'play_song_33',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The Baron Von Rantenraven commands the final attack.
        #   intro_2: Hit invasion shots in order.
        #   intro_3: Stop the command signal before it completes.
        #   stat_2_label: MAJOR HITS
        'von_rantenraven': {
            'title': 'BARON VON RANTENRAVEN',
            'intro_1': 'SAUCER OPENS THE ROOF',
            'intro_2': 'TEN FLIPS TO HIT THREE TARGETS',
            'intro_3': 'THIRD TARGET SCORES THE SUPER',
            'summary_title_complete': 'BARON VON RANTENRAVEN MODE COMPLETE',
            'summary_title_failed': 'BARON VON RANTENRAVEN MODE COMPLETE',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'FLIPS LEFT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'von_rantenraven_state',
            'song': 'play_song_52',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Chapter 1 mini-wizard multiball.
        #   intro_2: Collect surge jackpots and survive.
        #   intro_3: Chapter case files raise the values.
        'sinister_surge': {
            'title': 'SINISTER SURGE',
            'intro_1': 'MULTIBALL VILLAIN BATTLE',
            'intro_2': 'CLEAR EACH VILLAIN STAGE',
            'intro_3': 'FOR DAILY BUGLE JACKPOTS',
            'summary_title_complete': 'SINISTER SURGE CLEARED',
            'summary_title_failed': 'SINISTER SURGE LOST',
            'stat_1_label': 'AREAS CLEARED',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'sinister_surge_state',
            'song': 'play_song_71',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Chapter 2 mini-wizard multiball.
        #   intro_2: Escape the masterminds while multiball runs.
        #   intro_3: Chapter case files raise the values.
        'mastermind_trap': {
            'title': 'MASTERMIND TRAP',
            'intro_1': 'MULTIBALL VILLAIN BATTLE',
            'intro_2': 'CLEAR THREE COMBINED VILLAIN STAGES',
            'intro_3': 'EITHER WEB COLLECTS THE TIMED SUPER',
            'summary_title_complete': 'MASTERMIND TRAP CLEARED',
            'summary_title_failed': 'MASTERMIND TRAP LOST',
            'stat_1_label': 'SCORING HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'mastermind_trap_state',
            'song': 'play_song_58',
        },
        # Trubble Unleashed is a looping scoring multiball. Left drops open the
        # roof; VUK entry selects Diana/Centaur while Cerberus/Vulcan/Cyclops
        # remain available throughout. The wizard ends only when multiball ends.
        'trubble_unleashed': {
            'title': 'TRUBBLE UNLEASHED',
            'intro_1': 'MULTIBALL VILLAIN BATTLE',
            'intro_2': 'LEFT DROPS OPEN DIANA OR CENTAUR',
            'intro_3': 'UPPER TARGETS LIGHT SAUCERS / ADD-A-BALL',
            'summary_title_complete': 'TRUBBLE UNLEASHED',
            'summary_title_failed': 'TRUBBLE UNLEASHED',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'SUPERS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'trubble_unleashed_state',
            'song': 'play_song_92',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Decode the Plotter’s scheme.
        #   intro_2: Build headlines and cash Daily Bugle supers.
        #   intro_3: Chapter case files raise the values.
        'plotter': {
            'title': "THE PLOTTER",
            'intro_1': 'POPS BUILD RUMORS',
            'intro_2': 'LOWER SPINNER LIGHTS A SAUCER',
            'intro_3': '3 SAUCER SCHEMES OPENS VUK SUPER',
            'summary_title_complete': 'THE PLOTTER EXPOSED',
            'summary_title_failed': 'PLOTTER ESCAPED',
            'stat_1_label': 'RUMORS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SCHEMES',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'plotter_state',
            'song': 'play_song_41',
        },
        'crime_wave': {
            'title': 'CRIME WAVE',
            'intro_1': 'MULTIBALL CRIME WAVE',
            'intro_2': 'LIGHT 3 AREAS TO OPEN THE ROOFTOP',
            'intro_3': 'VUK OR UPPER EXIT SCORES JACKPOT',
            'summary_title_complete': 'CRIME WAVE STOPPED',
            'summary_title_failed': 'CRIME WAVE CONTINUES',
            'stat_1_label': 'MOST AREAS LIT',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'crime_wave_state',
            'song': 'play_song_68',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Chapter 7 mini-wizard multiball.
        #   intro_2: Break the curse during multiball.
        #   intro_3: Chapter case files raise the values.

        'the_web_tightens': {
            'title': 'THE WEB TIGHTENS',
            'intro_1': 'Two-ball multiball. Lock one at the Daily Bugle.',
            'intro_2': 'Saucers start five villain phases.',
            'intro_3': 'Phase wins build a rooftop Super Jackpot.',
            'summary_title_complete': 'THE WEB BROKEN',
            'summary_title_failed': 'THE WEB TIGHTENS',
            'stat_1_label': 'PHASES WON', 'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPERS', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'the_web_tightens_state', 'song': 'play_song_85',
        },
        'fifth_dimension_curse': {
            'title': 'FIFTH DIMENSION CURSE',
            'intro_1': 'Three-ball multiball.',
            'intro_2': 'Keep six city zones bright.',
            'intro_3': 'VUK collects zone jackpots.',
            'summary_title_complete': 'CURSE BROKEN',
            'summary_title_failed': 'CURSE ESCAPES',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'fifth_dimension_curse_jackpots',
            'stat_2_label': 'ADD-A-BALLS',
            'stat_2_var': 'fifth_dimension_curse_add_a_balls',
            'points_var': 'active_mode_points',
            'state_var': 'fifth_dimension_curse_state',
            'song': 'play_song_48',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Chapter 6 mini-wizard multiball.
        #   intro_2: Keep the lab under control.
        #   intro_3: Chapter case files raise the values.
        'mad_science_meltdown': {
            'title': 'MAD SCIENCE MELTDOWN',
            'intro_1': 'Lab meltdown MB.',
            'intro_2': 'Control experiments.',
            'intro_3': 'Case files boost value.',
            'summary_title_complete': 'MELTDOWN STOPPED',
            'summary_title_failed': 'MELTDOWN SPREADS',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'mad_science_meltdown_state',
            'points_var': 'active_mode_points',
            'state_var': 'mad_science_meltdown_state',
            'song': 'play_song_3',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Chapter 7 mini-wizard multiball.
        #   intro_2: Contain the elemental chaos.
        #   intro_3: Chapter case files raise the values.
        'nature_strikes_back': {
            'title': 'NATURE STRIKES BACK',
            'intro_1': 'Nature attacks.',
            'intro_2': 'Contain chaos shots.',
            'intro_3': 'Case files boost value.',
            'summary_title_complete': 'NATURE CONTAINED',
            'summary_title_failed': 'NATURE BREAKS LOOSE',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'nature_strikes_back_state',
            'points_var': 'active_mode_points',
            'state_var': 'nature_strikes_back_state',
            'song': 'play_song_66',
        },
        # ORIGINAL DISPLAY TEXT:
        #   title: INVASION FROM EVERYWHERE
        #   intro_1: Chapter 8 mini-wizard multiball.
        #   intro_2: Fight the lost-world invaders.
        #   intro_3: Chapter case files raise the values.
        'invasion_from_everywhere': {
            'title': 'LOST WORLD INVASION',
            'intro_1': 'Invasion multiball.',
            'intro_2': 'Stop the invasion from everywhere.',
            'intro_3': 'Case files boost value.',
            'summary_title_complete': 'INVASION STOPPED',
            'summary_title_failed': 'INVASION CONTINUES',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'invasion_from_everywhere_state',
            'points_var': 'active_mode_points',
            'state_var': 'invasion_from_everywhere_state',
            'song': 'play_song_96',
        },
        # ORIGINAL DISPLAY TEXT:
        #   title: WHO IS THE REAL VILLAIN?
        #   intro_1: Chapter 9 mini-wizard multiball.
        #   intro_2: Unmask the chaos while multiball runs.
        #   intro_3: Chapter case files raise the values.
        'who_is_the_real_villain': {
            'title': 'REAL VILLAIN?',
            'intro_1': 'Unmask the villain.',
            'intro_2': 'Hit chaos shots.',
            'intro_3': 'Case files boost value.',
            'summary_title_complete': 'VILLAIN REVEALED',
            'summary_title_failed': 'VILLAIN VANISHED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'who_is_the_real_villain_state',
            'points_var': 'active_mode_points',
            'state_var': 'who_is_the_real_villain_state',
            'song': 'play_song_49',
        },
        # ORIGINAL DISPLAY TEXT:
        #   title: TIME-TOSSED SHOWDOWN
        #   intro_1: Chapter 10 mini-wizard multiball.
        #   intro_2: Survive the time-tossed brawl.
        #   intro_3: Chapter case files raise the values.
        'time_tossed_showdown': {
            'title': 'TIME SHOWDOWN',
            'intro_1': 'Time-tossed battle.',
            'intro_2': 'Survive multiball.',
            'intro_3': 'Case files boost value.',
            'summary_title_complete': 'SHOWDOWN WON',
            'summary_title_failed': 'SHOWDOWN LOST',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'time_tossed_showdown_state',
            'points_var': 'active_mode_points',
            'state_var': 'time_tossed_showdown_state',
            'song': 'play_song_50',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The citywide battle reaches its peak.
        #   intro_2: Clear areas and collect Daily Bugle jackpots.
        #   intro_3: Finish the final battle to save the city.
        #   stat_1_label: AREAS CLEARED
        'final_showdown': {
            'title': 'KINGPIN',
            'intro_1': 'Kingpin controls the city.',
            'intro_2': 'Break his criminal empire.',
            'intro_3': 'Defeat Kingpin in multiball.',
            'summary_title_complete': 'KINGPIN DEFEATED',
            'summary_title_failed': 'KINGPIN RULES',
            'stat_1_label': 'AREAS',
            'stat_1_var': 'final_showdown_areas_cleared',
            'stat_2_label': 'JACKPOTS',
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
        # A terminal Jackpot/Super can post immediately before the mode-complete
        # event requests the summary. Keep that final award visible for a full
        # two seconds before the bookend replaces it.
        self.terminal_award_summary_deadline = 0.0
        self.pending_terminal_summary_request = None

        self.add_mode_event_handler("villain_bookend_intro_request", self._intro_request)
        self.add_mode_event_handler("villain_bookend_summary_request", self._summary_request)
        self.add_mode_event_handler("flipper_cancel", self._skip_current_bookend)
        self.add_mode_event_handler("villain_bookend_intro_hold_request", self._intro_hold_request)
        self.add_mode_event_handler("villain_bookend_intro_hold_release", self._intro_hold_release)
        self.add_mode_event_handler("villain_summary_hold_vuk_until_done", self._hold_vuk_until_summary_done)
        self.add_mode_event_handler(
            "villain_summary_transfer_vuk_to_mini_wizard",
            self._transfer_vuk_hold_to_mini_wizard,
        )
        self.add_mode_event_handler("villain_summary_hold_saucer_until_done", self._mark_terminal_award)
        self.add_mode_event_handler("villain_summary_delay_for_final_award", self._mark_terminal_award)


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
        self.summary_vuk_release_pending = True
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

    def _intro_request(self, villain=None, start_event=None, **kwargs):
        if villain not in self.VILLAINS:
            self.warning_log("Unknown villain intro requested: %s", villain)
            return

        self.machine.events.post("play_song_14")
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
        self.machine.events.post("villain_bookend_intro_show", villain=villain)

        self.delay.remove("villain_bookend_done")
        self.delay.add(
            name="villain_bookend_done",
            ms=self.INTRO_MS,
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

    def _summary_request(self, villain=None, done_event=None, allow_skip=None, chapter_number=None, **kwargs):
        if villain not in self.VILLAINS:
            self.warning_log("Unknown villain summary requested: %s", villain)
            return

        # Leave an explicitly marked terminal award on screen for a minimum of
        # two seconds before the summary starts.
        remaining = self.terminal_award_summary_deadline - time.monotonic()
        if remaining > 0:
            self.pending_terminal_summary_request = {
                "villain": villain,
                "done_event": done_event,
                "allow_skip": allow_skip,
                "chapter_number": chapter_number,
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

        self.machine.events.post("play_song_21")
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
        self._set_machine_var("villain_bookend_line_3", f"POINTS: {points:,}")
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
        # Chapter wizards use two distinct bookends: first the normal mode
        # summary with score/stats, then a dedicated Comic COLLECTED screen.
        # Do not substitute the Comic widget for the summary.
        self.machine.events.post("villain_bookend_summary_show", villain=villain)
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
            ms=self.SUMMARY_MS,
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

        self.machine.events.post("villain_bookend_intro_show", villain=villain)

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

    def _finish_current_bookend(self):
        if not self.current_stage:
            return

        done_event = self.current_done_event
        villain = self.current_villain
        stage = self.current_stage
        starting_saucer = None
        starting_vuk = False

        # A chapter wizard gets a full six-second score/stat summary followed
        # by a three-second fixed-cover Comic COLLECTED screen. Progression and
        # the caller's done_event are held until both bookends have completed.
        if stage == "summary" and villain in self.COMIC_SUMMARY_VILLAINS:
            chapter_number = self.current_comic_chapter or self.COMIC_SUMMARY_VILLAINS[villain]
            self.machine.events.post("villain_bookend_summary_hide")
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
        elif stage in ("summary", "comic_summary"):
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
