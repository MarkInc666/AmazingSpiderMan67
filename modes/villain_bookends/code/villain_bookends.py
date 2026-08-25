from mpf.core.mode import Mode


class VillainBookends(Mode):

    INTRO_MS = 5000
    SUMMARY_MS = 6000
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
            'intro_1': 'Build Rage Value with Pops.',
            'intro_2': 'All Switches Stock up Rage',
            'intro_3': 'Collect Jackpots at B',
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
            'intro_1': 'Hit flashing drops.',
            'intro_2': 'Sequence earns more points.',
            'intro_3': 'Beat him before reset.',
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
            'intro_1': 'Reach the rooftop.',
            'intro_2': 'Hit Targets to Build Value.',
            'intro_3': 'Spin to collect before it decays.',
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
            'intro_1': 'Make serum at STAR.',
            'intro_2': 'Deliver to the left web.',
            'intro_3': 'Hurry before it decays.',
            'summary_title_complete': 'GREEN LIZARD CURED',
            'summary_title_failed': 'GREEN LIZARD ESCAPED',
            'stat_1_label': 'DELIVERIES',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BEST VALUE',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'lizard_state',
            'song': 'play_song_4',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Follow the moving spark.
        #   intro_2: Hit each charged shot before time runs out.
        #   intro_3: The final spark awards Super Jackpot.
        'electro': {
            'title': 'ELECTRO',
            'intro_1': 'Follow the spark.',
            'intro_2': 'Hit charged JACKPOT shots.',
            'intro_3': 'Final spark is a Super.',
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
            'intro_1': 'Chaos multiball.',
            'intro_2': 'Saucers bank CHAOS and start SAFE play.',
            'intro_3': 'Flashing builds it. Solid shots reduce it.',
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
            'intro_1': 'Lock arms with lanes.',
            'intro_2': 'Web shots score JACKPOTS',
            'intro_3': 'Spin to boost X and light WEBS.',
            'summary_title_complete': 'DOC OCK DEFEATED',
            'summary_title_failed': 'DOC OCK ESCAPED',
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
            'intro_1': 'Find the real Mysterio.',
            'intro_2': 'Wrong shots decrease JACKPOT',
            'intro_3': 'Clues reveal the SUPER JACKPOT.',
            'summary_title_complete': 'MYSTERIO DEFEATED',
            'summary_title_failed': 'MYSTERIO ESCAPED',
            'stat_1_label': 'CLUES USED',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOT',
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
            'intro_1': 'Upper spinner builds venom.',
            'intro_2': 'Exit the Roof to Left or Right',
            'intro_3': 'Hit staged drop for Venom JACKPOT.',
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
            'intro_1': 'Wax traps the city.',
            'intro_2': 'Drops and Pops melt the wax.',
            'intro_3': 'ADD-A-BALL and JACKPOTS at Saucers.',
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
            'intro_1': 'Wake Heads with upper targets.',
            'intro_2': 'Lit Saucers score JACKPOTS',
            'intro_3': 'Flashing Saucers score double.',
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
            'intro_1': 'Eruption multiball.',
            'intro_2': 'Spinners build RIGHT DROP JACKPOT.',
            'intro_3': 'Upper Targets for ADD-A-BALL.',
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
            'intro_1': 'Diana takes aim.',
            'intro_2': 'LEFT ROOF EXIT for UPPOST shot.',
            'intro_3': 'Limited flips to make shots',
            'summary_title_complete': 'DIANA DEFEATED',
            'summary_title_failed': 'DIANA ESCAPED',
            'stat_1_label': 'ROUNDS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MISSES',
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
            'intro_1': 'Eye is center web.',
            'intro_2': 'Flips are limited.',
            'intro_3': 'Drops add flips.',
            'summary_title_complete': 'CYCLOPS DEFEATED',
            'summary_title_failed': 'CYCLOPS ESCAPED',
            'stat_1_label': 'BEST JP',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'FLIPS LEFT',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'cyclops_state',
            'song': 'play_song_3',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Drop targets build the Centaur Jackpot.
        #   intro_2: Four drops open the gate to the roof.
        #   intro_3: Exit left and hit the staged rubber shot.
        #   stat_1_label: DROPS DOWN
        'centaur': {
            'title': 'CENTAUR CHARGE',
            'intro_1': 'Drops build JP.',
            'intro_2': 'Four drops open roof.',
            'intro_3': 'Exit left for final.',
            'summary_title_complete': 'CENTAUR CHARGE TRAPPED',
            'summary_title_failed': 'CENTAUR CHARGE ESCAPED',
            'stat_1_label': 'DROPS',
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
            'intro_1': 'Stop the frame-up.',
            'intro_2': 'Hit paired shots.',
            'intro_3': 'Clear both flies.',
            'summary_title_complete': 'THE FLY TWINS CAUGHT',
            'summary_title_failed': 'THE FLY TWINS ESCAPED',
            'stat_1_label': 'AREAS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MAJORS',
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
            'title': '5TH AVE PHANTOM',
            'intro_1': 'Drop right bank.',
            'intro_2': 'Reveal the hideout.',
            'intro_3': 'Catch him fast.',
            'summary_title_complete': '5TH AVE PHANTOM CAUGHT',
            'summary_title_failed': '5TH AVE PHANTOM VANISHED',
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
            'intro_1': 'Battle Cowboy and Ox.',
            'intro_2': 'Light upper jackpots.',
            'intro_3': 'Hit OX at center web.',
            'summary_title_complete': 'GANG BROKEN',
            'summary_title_failed': 'OX GOT AWAY',
            'stat_1_label': 'UPPER JPS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'OX SUPER',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'enforcers_state',
            'song': 'play_song_33',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Hit drops to build the Diamond Jackpot.
        #   intro_2: Complete the 5-bank to start saucer chase.
        #   intro_3: Star rollover lights all saucers briefly.
        #   stat_2_label: BONUS BANKED
        'doctor_cool': {
            'title': 'DOCTOR COOL',
            'intro_1': 'Drops build frozen diamonds.',
            'intro_2': '5-bank starts the shipment chase.',
            'intro_3': 'STAR freezes all three saucers.',
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
            'title': 'HARLEY CLIVENDON', 'intro_1': 'Clivendon holds the city.', 'intro_2': 'Lock a ball in a saucer.', 'intro_3': 'Light four areas, then hit the VUK.',
            'summary_title_complete': 'CLIVENDON STOPPED', 'summary_title_failed': 'CLIVENDON ESCAPED',
            'stat_1_label': 'VUK JACKPOTS', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'HARLEY JACKPOTS', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'harley_clivendon_state', 'song': 'play_song_51',
        },
        'conquistador': {
            'title': 'THE CONQUISTADOR', 'intro_1': 'Hit any left drop.', 'intro_2': 'Spin to find the Fountain.', 'intro_3': 'Build and collect at center web.',
            'summary_title_complete': 'FOUNTAIN FOUND', 'summary_title_failed': 'FOUNTAIN NOT FOUND',
            'stat_1_label': 'FOUNTAIN JP', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'SPEED BONUS', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'conquistador_state', 'song': 'play_song_54',
        },
        'spider_slayer': {
            'title': 'SPIDER-SLAYER', 'intro_1': 'The Slayer is tracking you.', 'intro_2': 'Hit lit shots to expose it.', 'intro_3': 'Destroy it at the Daily Bugle.',
            'summary_title_complete': 'SLAYER DESTROYED', 'summary_title_failed': 'SLAYER ESCAPED',
            'stat_1_label': 'SLAYER JP', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'HUNT TIME', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'spider_slayer_state', 'song': 'play_song_55',
        },
        'metal_eating_robot': {
            'title': 'METAL MONSTER', 'intro_1': 'Eight city zones are in danger.', 'intro_2': 'A new attack begins every five seconds.', 'intro_3': 'Save four before three are destroyed.',
            'summary_title_complete': 'CITY SAVED', 'summary_title_failed': 'CITY DESTROYED',
            'stat_1_label': 'ZONES SAVED', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'DESTROYED', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'metal_eating_robot_state', 'song': 'play_song_58',
        },
        'fiddler': {
            'title': 'FIDDLER', 'intro_1': 'Watch the flashing notes.', 'intro_2': 'Repeat each melody in order.', 'intro_3': 'Three wrong notes and Fiddler escapes.',
            'summary_title_complete': 'FIDDLER SILENCED', 'summary_title_failed': 'FIDDLER ESCAPED',
            'stat_1_label': 'ROUND', 'stat_1_var': 'active_mode_stat_1', 'stat_2_label': 'NOTES HIT', 'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points', 'state_var': 'fiddler_state', 'completion_var': 'active_mode_completed', 'song': 'play_song_50',
        },
        'pardo': {
            'title': 'PARDO',
            'intro_1': 'Five chances. Three correct shots win.',
            'intro_2': 'Spinner reveals the true shot.',
            'intro_3': 'Choose the correct shot from three.',
            'summary_title_complete': 'PARDO DEFEATED',
            'summary_title_failed': 'PARDO ESCAPED',
            'stat_1_label': 'GOOD SHOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'WRONG SHOTS',
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
            'intro_1': 'The Fantastic Fakir begins his Ruby Heist.',
            'intro_2': 'Saucer reveals upper ruby.',
            'intro_3': '3 Rubies light Super.',
            'summary_title_complete': 'FANTASTIC FAKIR DEFEATED',
            'summary_title_failed': 'FANTASTIC FAKIR ESCAPED',
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
            'intro_1': 'Demons appear every 4 seconds.',
            'intro_2': 'Destroy all four lit demons.',
            'intro_3': 'Then shoot the VUK for the scepter.',
            'summary_title_complete': 'KOTEP DEFEATED',
            'summary_title_failed': 'KOTEP ESCAPED',
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
            'intro_1': 'New York has gone dark.',
            'intro_2': 'Hit each playfield area.',
            'intro_3': 'Restore all 6 before time expires.',
            'summary_title_complete': 'SWAMI DEFEATED',
            'summary_title_failed': 'SWAMI ESCAPED',
            'stat_1_label': 'AREAS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BANKED',
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
            'intro_1': 'Infinata invades from the Fifth Dimension.',
            'intro_2': 'Clear each green creature area.',
            'intro_3': 'Then shoot a saucer Super.',
            'summary_title_complete': 'INFINATA DEFEATED',
            'summary_title_failed': 'INFINATA ESCAPED',
            'stat_1_label': 'AREAS',
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
            'intro_1': 'Noah Boddy vanished.',
            'intro_2': 'Use upper clues.',
            'intro_3': 'Find the true drop.',
            'summary_title_complete': 'NOAH BODDY FOUND',
            'summary_title_failed': 'NOAH BODDY ESCAPED',
            'stat_1_label': 'SPINNER SPINS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'INVISIBLE FORTUNE',
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
            'intro_1': 'Slings and inlanes light A / B.',
            'intro_2': 'Collect A / B, then hit its pop.',
            'intro_3': 'Both pops light center web Super.',
            'summary_title_complete': 'DR. MAGNETO DEFEATED',
            'summary_title_failed': 'DR. MAGNETO ESCAPED',
            'stat_1_label': 'CIRCUIT SHOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'SUPERS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_magneto_state',
            'song': 'play_song_27',
        },
        # ORIGINAL DISPLAY TEXT:
        #   title: PROFESSOR PRETORIS
        #   intro_1: Pretoris is shrinking the city.
        #   intro_2: Solve the shot puzzle before the ray fires.
        #   intro_3: Beat the sequence and restore the landmark.
        #   stat_2_label: MAJOR HITS
        'professor_pretorius': {
            'title': 'PROFESSOR PRETORIS',
            'intro_1': 'The reactor is overheating.',
            'intro_2': 'Spin to flood it blue.',
            'intro_3': 'Then hit the web Super.',
            'summary_title_complete': 'PROFESSOR PRETORIS STOPPED',
            'summary_title_failed': 'PROFESSOR PRETORIS ESCAPED',
            'stat_1_label': 'BANDS FLOODED',
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
            'intro_1': 'Build without cracks.',
            'intro_2': 'Wrong shots break it.',
            'intro_3': 'Cash before it falls.',
            'summary_title_complete': 'DOCTOR DUMPTY DEFEATED',
            'summary_title_failed': 'DOCTOR DUMPTY ESCAPED',
            'stat_1_label': 'JACKPOTS',
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
            'intro_1': 'Slick shots slide.',
            'intro_2': 'Control the pattern.',
            'intro_3': 'End the oil scheme.',
            'summary_title_complete': 'SCHLICK STOPPED',
            'summary_title_failed': 'SCHLICK ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MAJORS',
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
            'intro_1': 'Blotto is spreading.',
            'intro_2': 'Spin down the meter.',
            'intro_3': 'Clear infected areas.',
            'summary_title_complete': 'BLOTTO CONTAINED',
            'summary_title_failed': 'BLOTTO ESCAPED',
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
            'intro_1': 'Zap chains shots.',
            'intro_2': 'Follow the charge.',
            'intro_3': 'Break the circuit.',
            'summary_title_complete': 'DOCTOR ZAPP DEFEATED',
            'summary_title_failed': 'DOCTOR ZAPP ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MAJORS',
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
            'intro_1': 'Thunder hides crimes.',
            'intro_2': 'Follow the storm.',
            'intro_3': 'Stop the next strike.',
            'summary_title_complete': 'THUNDER RUMBLE STOPPED',
            'summary_title_failed': 'BOLTON AND BOOMER ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MAJORS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'bolton_boomer_state',
            'song': 'play_song_58',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The Snowman is freezing the city.
        #   intro_2: Thaw frozen shots with spinner and targets.
        #   intro_3: Break the freeze before time runs out.
        #   stat_2_label: MAJOR HITS
        'snowman': {
            'title': 'THE SNOWMAN',
            'intro_1': 'Snowman freezes all.',
            'intro_2': 'Thaw frozen shots.',
            'intro_3': 'Break the freeze.',
            'summary_title_complete': 'SNOWMAN MELTED',
            'summary_title_failed': 'SNOWMAN ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MAJORS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'snowman_state',
            'song': 'play_song_39',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The Plutonians blocks the city in frozen chaos.
        #   intro_2: Hit thaw shots to open scoring.
        #   intro_3: Collect the jackpot before everything freezes.
        #   stat_2_label: MAJOR HITS
        'plutonians': {
            'title': 'THE PLUTONIANS',
            'intro_1': 'Ice blocks the city.',
            'intro_2': 'Hit thaw shots.',
            'intro_3': 'Restore their escape.',
            'summary_title_complete': 'PLUTONIANS STOPPED',
            'summary_title_failed': 'PLUTONIANS STRANDED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MAJORS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'plutonians_state',
            'song': 'play_song_42',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Dr. Manta traps the city beneath the waves.
        #   intro_2: Escape saucer traps with lit rescue shots.
        #   intro_3: Collect the jackpot before he dives again.
        #   stat_2_label: MAJOR HITS
        'dr_manta': {
            'title': 'DR. MANTA',
            'intro_1': 'Manta dives deep.',
            'intro_2': 'Escape saucer traps.',
            'intro_3': 'Hit rescue shots.',
            'summary_title_complete': 'DR. MANTA DEFEATED',
            'summary_title_failed': 'DR. MANTA ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MAJORS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'dr_manta_state',
            'song': 'play_song_40',
        },
        'doctor_atlantean': {
            'title': 'DOCTOR ATLANTEAN',
            'intro_1': 'Manhattan is sinking.',
            'intro_2': 'Hit pulsing roof targets.',
            'intro_3': 'Raise the city before it is lost.',
            'summary_title_complete': 'MANHATTAN RISES!',
            'summary_title_failed': 'MANHATTAN IS LOST!',
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
            'intro_1': 'Desperado rides again.',
            'intro_2': 'Track five outlaws.',
            'intro_3': 'Left bank adds time.',
            'summary_title_complete': 'DESPERADO CAPTURED',
            'summary_title_failed': 'DESPERADO ESCAPED',
            'stat_1_label': 'BANK HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'OUTLAWS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'desperado_state',
            'song': 'play_song_59',
        },
        'devargas': {
            'title': 'DEVARGAS',
            'intro_1': 'The City of Gold awaits.',
            'intro_2': 'Hit the pulsing shots.',
            'intro_3': 'Take all the gold you can.',
            'summary_title_complete': 'GOLD SECURED',
            'summary_title_failed': 'GOLD SECURED',
            'stat_1_label': 'GOLD SHOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'DEVARGAS GOLD',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'devargas_state',
            'song': 'play_song_52',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Molemen strike from the ice.
        #   intro_2: Hit rescue shots before the freeze spreads.
        #   intro_3: Finish the sequence and escape the trap.
        #   stat_2_label: MAJOR HITS
        'molemen': {
            'title': 'THE MOLEMEN',
            'intro_1': 'Molemen rise below.',
            'intro_2': 'Build the three saucers.',
            'intro_3': 'Keep the multiball alive.',
            'summary_title_complete': 'THE MOLEMEN STOPPED',
            'summary_title_failed': 'THE MOLEMEN ESCAPED',
            'stat_1_label': 'BIGGEST JP',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'molemen_state',
            'song': 'play_song_42',
        },
        'charles_cameo': {
            'title': 'CHARLES CAMEO',
            'intro_1': 'Shoot the lit side.',
            'intro_2': 'Then shoot its mirror.',
            'intro_3': 'Finish at the webs.',
            'summary_title_complete': 'CHARLES CAMEO DEFEATED',
            'summary_title_failed': 'CHARLES CAMEO ESCAPED',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JP',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'charles_cameo_state',
            'song': 'play_song_70',
        },
        'brutus': {
            'title': 'BRUTUS',
            'intro_1': 'Brutus guards the artwork.',
            'intro_2': 'Hit a right drop to lure him.',
            'intro_3': 'Then shoot any saucer.',
            'summary_title_complete': 'BRUTUS BEATEN',
            'summary_title_failed': 'BRUTUS ESCAPED',
            'stat_1_label': 'ARTWORK',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BIGGEST JP',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'brutus_state',
            'song': 'play_song_76',
        },
        'igor': {
            'title': 'IGOR',
            'intro_1': 'Hit flashing green shots.',
            'intro_2': 'Avoid solid red defenses.',
            'intro_3': 'Five bad shots end the mode.',
            'summary_title_complete': "IGOR'S DEFENSES WIN",
            'summary_title_failed': "IGOR'S DEFENSES WIN",
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
            'intro_1': 'DROP ALL 8 TARGETS IN ORDER.',
            'intro_2': 'UPPER SPINNER DROPS THE NEXT.',
            'intro_3': 'WRONG TARGET RESETS ITS BANK.',
            'summary_title_complete': 'SKYMASTER GROUNDED',
            'summary_title_failed': 'SKYMASTER ESCAPED',
            'stat_1_label': 'TARGETS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'WEB JACKPOTS',
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
            'intro_1': 'Reptiles run wild.',
            'intro_2': 'Pops light jackpots.',
            'intro_3': 'Saucer scores Super.',
            'summary_title_complete': 'REPTILES CAPTURED',
            'summary_title_failed': 'REPTILES ESCAPED',
            'stat_1_label': 'RAMPAGE JPS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BANKED',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'conners_reptiles_state',
            'song': 'play_song_44',
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
            'intro_1': 'Enter the rooftop and choose an exit.',
            'intro_2': 'Each exit stages the opposite drop bank.',
            'intro_3': 'Aim for the center before Galahad charges.',
            'summary_title_complete': 'KNIGHT MUST FALL',
            'summary_title_failed': 'JOUST INTERRUPTED',
            'stat_1_label': 'JOUST HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'BULLSEYES',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'sir_galahad_state',
            'song': 'play_song_57',
        },
        'master_vine': {
            'title': 'MASTER VINE',
            'intro_1': 'Attack the vine upstairs.',
            'intro_2': 'Spinner spreads new growth.',
            'intro_3': 'Clear three vine waves.',
            'summary_title_complete': 'MASTER VINE DEFEATED',
            'summary_title_failed': 'MASTER VINE ESCAPED',
            'stat_1_label': 'VINE JPS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'WAVES',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'master_vine_state',
            'song': 'play_song_53',
        },
        'master_technician': {
            'title': 'MASTER TECHNICIAN',
            'intro_1': 'Drops boost the spinner.',
            'intro_2': 'Stop at seven and spin.',
            'intro_3': 'All eight costs ten seconds.',
            'summary_title_complete': 'TIME EXPIRED',
            'summary_title_failed': 'CIRCUIT INTERRUPTED',
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
            'intro_1': 'Align the Homeworld Ray.',
            'intro_2': 'Flippers rotate the lights.',
            'intro_3': 'Hit pulsing shots.',
            'summary_title_complete': 'THE SPIDER-MEN RETURN HOME',
            'summary_title_failed': 'PROTON TEST ACTIVATED',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'FINE ADJUSTMENTS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'spider_men_state',
            'song': 'play_song_74',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: The Baron Von Rantenraven commands the final attack.
        #   intro_2: Hit invasion shots in order.
        #   intro_3: Stop the command signal before it completes.
        #   stat_2_label: MAJOR HITS
        'von_rantenraven': {
            'title': 'BARON VON RANTENRAVEN',
            'intro_1': 'Emperor commands all.',
            'intro_2': 'Identity to be chosen.',
            'intro_3': 'Stop the signal.',
            'summary_title_complete': 'BARON VON RANTENRAVEN DEFEATED',
            'summary_title_failed': 'BARON VON RANTENRAVEN ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_stat_1',
            'stat_2_label': 'MAJORS',
            'stat_2_var': 'active_mode_stat_2',
            'points_var': 'active_mode_points',
            'state_var': 'von_rantenraven_state',
            'song': 'play_song_46',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Chapter 1 mini-wizard multiball.
        #   intro_2: Collect surge jackpots and survive.
        #   intro_3: Chapter case files raise the values.
        'sinister_surge': {
            'title': 'SINISTER SURGE',
            'intro_1': 'Mini-wizard MB.',
            'intro_2': 'Clear surge areas.',
            'intro_3': 'Case files boost value.',
            'summary_title_complete': 'SINISTER SURGE CLEARED',
            'summary_title_failed': 'SINISTER SURGE LOST',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'sinister_surge_state',
            'points_var': 'active_mode_points',
            'state_var': 'sinister_surge_state',
            'song': 'play_song_50',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Chapter 2 mini-wizard multiball.
        #   intro_2: Escape the masterminds while multiball runs.
        #   intro_3: Chapter case files raise the values.
        'mastermind_trap': {
            'title': 'MASTERMIND TRAP',
            'intro_1': 'Mastermind multiball.',
            'intro_2': 'Complete trap shots.',
            'intro_3': 'All traps light Super.',
            'summary_title_complete': 'MASTERMIND TRAP CLEARED',
            'summary_title_failed': 'MASTERMIND TRAP LOST',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'mastermind_trap_state',
            'points_var': 'active_mode_points',
            'state_var': 'mastermind_trap_state',
            'song': 'play_song_47',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Miss Trubble has unleashed her creations.
        #   intro_2: Use roof targets, saucers, and staged drops.
        #   intro_3: Survive multiball as long as you can.
        'trubble_unleashed': {
            'title': 'TRUBBLE UNLEASHED',
            'intro_1': 'Trubble unleashed!',
            'intro_2': 'Hit targets/saucers.',
            'intro_3': 'Stage drops for value.',
            'summary_title_complete': 'TRUBBLE CONTAINED',
            'summary_title_failed': 'TRUBBLE RUNS WILD',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'trubble_unleashed_jackpots_collected',
            'stat_2_label': 'STAGED HITS',
            'stat_2_var': 'trubble_unleashed_staged_hits',
            'points_var': 'active_mode_points',
            'state_var': 'trubble_unleashed_state',
            'song': 'play_song_47',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Decode the Plotter’s scheme.
        #   intro_2: Build headlines and cash Daily Bugle supers.
        #   intro_3: Chapter case files raise the values.
        'plotter': {
            'title': "THE PLOTTER",
            'intro_1': 'Pops build rumors.',
            'intro_2': 'Lower spinner reveals a scheme.',
            'intro_3': 'Stop three, then shoot the VUK.',
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
            'intro_1': 'Light the five crime areas.',
            'intro_2': 'Three lit areas open the roof.',
            'intro_3': 'Upper exits collect jackpots.',
            'summary_title_complete': 'CRIME WAVE STOPPED',
            'summary_title_failed': 'CRIME WAVE CONTINUES',
            'stat_1_label': 'AREAS LIT',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'crime_wave_state',
            'song': 'play_song_43',
        },
        # ORIGINAL DISPLAY TEXT:
        #   intro_1: Chapter 7 mini-wizard multiball.
        #   intro_2: Break the curse during multiball.
        #   intro_3: Chapter case files raise the values.

        'the_web_tightens': {
            'title': 'THE WEB TIGHTENS',
            'intro_1': 'Five hidden threats return.',
            'intro_2': 'Survive The Web Tightens multiball.',
            'intro_3': 'Every case file boosts jackpots.',
            'summary_title_complete': 'THE WEB BROKEN',
            'summary_title_failed': 'THE WEB TIGHTENS',
            'stat_1_label': 'HITS', 'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE', 'stat_2_var': 'the_web_tightens_state',
            'points_var': 'active_mode_points', 'state_var': 'the_web_tightens_state', 'song': 'play_song_38',
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
            'song': 'play_song_56',
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
            'song': 'play_song_44',
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
            'song': 'play_song_55',
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
            'song': 'play_song_23',
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
            'song': 'play_song_3',
        },
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.current_stage = None
        self.current_done_event = None
        self.current_villain = None
        self.current_summary_can_skip = False
        self.summary_vuk_release_pending = False

        self.add_mode_event_handler("villain_bookend_intro_request", self._intro_request)
        self.add_mode_event_handler("villain_bookend_summary_request", self._summary_request)
        self.add_mode_event_handler("flipper_cancel", self._skip_current_bookend)
        self.add_mode_event_handler("villain_bookend_intro_hold_request", self._intro_hold_request)
        self.add_mode_event_handler("villain_bookend_intro_hold_release", self._intro_hold_release)
        self.add_mode_event_handler("villain_summary_hold_vuk_until_done", self._hold_vuk_until_summary_done)


    def _hold_vuk_until_summary_done(self, **kwargs):
        """Hold a mode-ending VUK ball until the villain summary finishes.

        The winning mode owns the collect, but VillainBookends owns the exact
        end of the summary for both timeout and flipper speedup paths.
        """
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

    def _summary_request(self, villain=None, done_event=None, allow_skip=None, **kwargs):
        if villain not in self.VILLAINS:
            self.warning_log("Unknown villain summary requested: %s", villain)
            return

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
        footer = "HOLD BOTH FLIPPERS TO SPEED UP" if self.current_summary_can_skip else ""
        self._set_machine_var("villain_bookend_footer", footer)

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
        # Intros may always be skipped. Regular villain summaries may be sped up.
        # Wizard/chapter-transition summaries must run their full duration so the
        # controlled drain and chapter select setup have time to complete.
        if self.current_stage == "intro" or (self.current_stage == "summary" and self.current_summary_can_skip):
            self.delay.remove("villain_bookend_done")
            self._finish_current_bookend()

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

    def _finish_current_bookend(self):
        if not self.current_stage:
            return

        done_event = self.current_done_event
        villain = self.current_villain
        stage = self.current_stage

        if stage == "intro":
            data = self.VILLAINS[villain]
            self.machine.events.post(data["song"])
            self.machine.events.post("villain_bookend_intro_hide")
            self.machine.events.post("villain_bookend_intro_done", villain=villain)
        elif stage == "summary":
            self.machine.game.player["villain_mode_in_summary"] = False
            self.machine.events.post("reset_villain_locate")
            self.machine.events.post("reset_daily_bugle_state")
            self.machine.events.post("villain_bookend_summary_hide")
            self.machine.events.post("villain_bookend_summary_done", villain=villain)
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

        self.machine.events.post("clear_saucers_delayed")
        self.current_stage = None
        self.current_villain = None
        self.current_done_event = None
        self.current_summary_can_skip = False

        if done_event:
            self.machine.events.post(done_event, villain=villain)

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
