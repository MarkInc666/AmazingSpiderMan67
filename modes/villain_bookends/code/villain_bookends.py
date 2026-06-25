from mpf.core.mode import Mode


class VillainBookends(Mode):

    INTRO_MS = 5000
    SUMMARY_MS = 6000

    VILLAINS = {
        'rhino': {
            'title': 'RHINO BASH',
            'intro_1': 'Build Rage with pop bumper hits.',
            'intro_2': 'Cash Berserk jackpots at the B rollover.',
            'intro_3': 'Bigger rage means bigger jackpots.',
            'summary_title_complete': 'RHINO DEFEATED',
            'summary_title_failed': 'RHINO ESCAPED',
            'stat_1_label': 'BEST JACKPOT',
            'stat_1_var': 'rhino_best_jackpot_value',
            'stat_2_label': 'BEST RAGE',
            'stat_2_var': 'rhino_best_rage_stage',
            'points_var': 'active_mode_points',
            'state_var': 'rhino_state',
            'song': 'play_song_22',
        },
        'sandman': {
            'title': 'SANDMAN',
            'intro_1': 'Shoot the flashing drop target.',
            'intro_2': 'Hit drops in sequence for bigger value.',
            'intro_3': 'Complete the run before Sandman reforms.',
            'summary_title_complete': 'SANDMAN DEFEATED',
            'summary_title_failed': 'SANDMAN ESCAPED',
            'stat_1_label': 'DROPS HIT',
            'stat_1_var': 'sandman_total_drops',
            'stat_2_label': 'BEST RUN',
            'stat_2_var': 'sandman_best_run',
            'points_var': 'active_mode_points',
            'state_var': 'sandman_state',
            'song': 'play_song_8',
        },
        'vulture': {
            'title': 'VULTURE',
            'intro_1': 'Get to the rooftop.',
            'intro_2': 'Hit upper targets to raise spinner value.',
            'intro_3': 'Spin fast before the targets decay.',
            'summary_title_complete': 'VULTURE DEFEATED',
            'summary_title_failed': 'VULTURE ESCAPED',
            'stat_1_label': 'SPINS',
            'stat_1_var': 'vulture_spins',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'vulture_bonus',
            'points_var': 'active_mode_points',
            'state_var': 'vulture_state',
            'song': 'play_song_10',
        },
        'lizard': {
            'title': 'THE LIZARD',
            'intro_1': 'Create the antidote at the star rollover.',
            'intro_2': 'Deliver it to the lit web targets.',
            'intro_3': 'Move fast before the serum value drains.',
            'summary_title_complete': 'LIZARD CURED',
            'summary_title_failed': 'LIZARD ESCAPED',
            'stat_1_label': 'DELIVERIES',
            'stat_1_var': 'lizard_deliveries_made',
            'stat_2_label': 'BEST VALUE',
            'stat_2_var': 'lizard_best_delivery_value',
            'points_var': 'active_mode_points',
            'state_var': 'lizard_state',
            'song': 'play_song_4',
        },
        'electro': {
            'title': 'ELECTRO',
            'intro_1': 'Follow the moving spark.',
            'intro_2': 'Hit each charged shot before time runs out.',
            'intro_3': 'The final spark awards Super Jackpot.',
            'summary_title_complete': 'ELECTRO DEFEATED',
            'summary_title_failed': 'ELECTRO ESCAPED',
            'stat_1_label': 'BEST SPARK',
            'stat_1_var': 'electro_best_spark',
            'stat_2_label': 'SUPER JP',
            'stat_2_var': 'electro_super_jackpot',
            'points_var': 'active_mode_points',
            'state_var': 'electro_state',
            'song': 'play_song_23',
        },
        'goblin': {
            'title': 'GREEN GOBLIN',
            'intro_1': 'Goblin attacks in chaos multiball.',
            'intro_2': 'Flashing shots build value. Solid shots cash in.',
            'intro_3': 'Saucers can rest the battle and bank bonus.',
            'summary_title_complete': 'GOBLIN DEFEATED',
            'summary_title_failed': 'GOBLIN ESCAPED',
            'stat_1_label': 'ATTACK TOTAL',
            'stat_1_var': 'goblin_attacks_value',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'goblin_bonus',
            'points_var': 'active_mode_points',
            'state_var': 'goblin_state',
            'song': 'play_song_7',
        },
        'doc_ock': {
            'title': 'DOCTOR OCTOPUS',
            'intro_1': 'Lock tentacle arms with rollovers.',
            'intro_2': 'Shoot web targets for jackpots.',
            'intro_3': 'Spinner increases the multiplier.',
            'summary_title_complete': 'DOC OCK DEFEATED',
            'summary_title_failed': 'DOC OCK ESCAPED',
            'stat_1_label': 'ARMS LOCKED',
            'stat_1_var': 'doc_ock_max_arms_locked',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'doc_ock_jackpots',
            'points_var': 'active_mode_points',
            'state_var': 'doc_ock_state',
            'song': 'play_song_18',
        },
        'mysterio': {
            'title': 'MYSTERIO',
            'intro_1': 'Find the real Mysterio.',
            'intro_2': 'Wrong shots lower the jackpot value.',
            'intro_3': 'Use clues to find the Super shot.',
            'summary_title_complete': 'MYSTERIO DEFEATED',
            'summary_title_failed': 'MYSTERIO ESCAPED',
            'stat_1_label': 'CLUES USED',
            'stat_1_var': 'mysterio_clues_used',
            'stat_2_label': 'JACKPOT',
            'stat_2_var': 'mysterio_jackpot_value',
            'points_var': 'active_mode_points',
            'state_var': 'mysterio_state',
            'song': 'play_song_24',
        },
        'scorpion': {
            'title': 'SCORPION',
            'intro_1': 'Build Venom with the upper spinner.',
            'intro_2': 'Choose your exit to stage the attack.',
            'intro_3': 'Hit the staged drop before time runs out.',
            'summary_title_complete': 'SCORPION DEFEATED',
            'summary_title_failed': 'SCORPION ESCAPED',
            'stat_1_label': 'STINGS',
            'stat_1_var': 'scorpion_stings',
            'stat_2_label': 'BIGGEST JP',
            'stat_2_var': 'scorpion_biggest_jackpot',
            'points_var': 'active_mode_points',
            'state_var': 'scorpion_state',
            'song': 'play_song_25',
        },
        'parafino': {
            'title': 'PARAFINO',
            'intro_1': "Parafino's wax traps the city.",
            'intro_2': 'Build zone jackpots with drops and pops.',
            'intro_3': 'Cash saucers. Three hits lights add-a-ball.',
            'summary_title_complete': 'PARAFINO DEFEATED',
            'summary_title_failed': 'PARAFINO ESCAPED',
            'stat_1_label': 'ZONE HITS',
            'stat_1_var': 'parafino_zone_hits',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'parafino_total_jackpots',
            'points_var': 'active_mode_points',
            'state_var': 'parafino_state',
            'song': 'play_song_19',
        },
        'cerberus': {
            'title': 'CERBERUS',
            'intro_1': 'Hit upper targets to wake the three heads.',
            'intro_2': 'Lit saucers collect jackpots.',
            'intro_3': 'The matching saucer scores double.',
            'summary_title_complete': 'CERBERUS DEFEATED',
            'summary_title_failed': 'CERBERUS ESCAPED',
            'stat_1_label': 'TARGETS',
            'stat_1_var': 'cerberus_targets_hit',
            'stat_2_label': 'JACKPOTS',
            'stat_2_var': 'cerberus_jackpots_collected',
            'points_var': 'active_mode_points',
            'state_var': 'cerberus_state',
            'song': 'play_song_9',
        },
        'vulcan': {
            'title': 'VULCAN',
            'intro_1': 'Multiball erupts across the playfield.',
            'intro_2': 'Spinners build the Vulcan Jackpot.',
            'intro_3': 'Right drops collect. Upper targets add balls.',
            'summary_title_complete': 'VULCAN DEFEATED',
            'summary_title_failed': 'VULCAN ESCAPED',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'vulcan_jackpots_collected',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'vulcan_bonus',
            'points_var': 'active_mode_points',
            'state_var': 'vulcan_state',
            'song': 'play_song_15',
        },
        'diana': {
            'title': 'DIANA',
            'intro_1': "Diana takes aim with Trubble's arrows.",
            'intro_2': 'Use the post-release timed shot.',
            'intro_3': 'Hit the arrow target before time runs out.',
            'summary_title_complete': 'DIANA DEFEATED',
            'summary_title_failed': 'DIANA ESCAPED',
            'stat_1_label': 'ROUNDS',
            'stat_1_var': 'diana_rounds_completed',
            'stat_2_label': 'MISSES',
            'stat_2_var': 'diana_wrong_total',
            'points_var': 'active_mode_points',
            'state_var': 'diana_state',
            'song': 'play_song_26',
        },
        'cyclops': {
            'title': 'CYCLOPS',
            'intro_1': 'The center web target is the Cyclops Eye.',
            'intro_2': 'You have limited flips. Drops add flips.',
            'intro_3': 'Hit the Eye for remaining flips x 100K.',
            'summary_title_complete': 'CYCLOPS DEFEATED',
            'summary_title_failed': 'CYCLOPS ESCAPED',
            'stat_1_label': 'BEST JP',
            'stat_1_var': 'cyclops_best_jackpot',
            'stat_2_label': 'FLIPS LEFT',
            'stat_2_var': 'cyclops_flips_remaining',
            'points_var': 'active_mode_points',
            'state_var': 'cyclops_state',
            'song': 'play_song_14',
        },
        'centaur': {
            'title': 'CENTAUR CHARGE',
            'intro_1': 'Drop targets build the Centaur Jackpot.',
            'intro_2': 'Four drops open the gate to the roof.',
            'intro_3': 'Exit left and hit the staged rubber shot.',
            'summary_title_complete': 'CENTAUR TRAPPED',
            'summary_title_failed': 'CENTAUR ESCAPED',
            'stat_1_label': 'DROPS DOWN',
            'stat_1_var': 'centaur_drops_down',
            'stat_2_label': 'BEST JP',
            'stat_2_var': 'centaur_best_jackpot',
            'points_var': 'active_mode_points',
            'state_var': 'centaur_state',
            'song': 'play_song_14',
        },
        'kingpin': {
            'title': 'KINGPIN',
            'intro_1': 'Kingpin is running the Crime Wave.',
            'intro_2': 'Clear areas and collect Daily Bugle jackpots.',
            'intro_3': 'Use add-a-ball to keep the operation alive.',
            'summary_title_complete': 'KINGPIN DEFEATED',
            'summary_title_failed': 'KINGPIN ESCAPED',
            'stat_1_label': 'AREAS CLEARED',
            'stat_1_var': 'kingpin_areas_cleared',
            'stat_2_label': 'MAX BALLS',
            'stat_2_var': 'kingpin_max_balls',
            'points_var': 'active_mode_points',
            'state_var': 'kingpin_state',
            'song': 'play_song_3',
        },
        'human_flies': {
            'title': 'HUMAN FLIES',
            'intro_1': 'The Human Flies are framing Spider-Man.',
            'intro_2': 'Hit paired wall-crawler shots before they move.',
            'intro_3': 'Clear both flies to stop the frame-up.',
            'summary_title_complete': 'HUMAN FLIES CAUGHT',
            'summary_title_failed': 'HUMAN FLIES ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'human_flies_state',
            'song': 'play_song_27',
        },
        'fifth_avenue_phantom': {
            'title': 'FIFTH AVENUE PHANTOM',
            'intro_1': 'Drop the right bank to reveal the Phantom.',
            'intro_2': 'Catch him while the hidden shot is lit.',
            'intro_3': 'Early catches score bigger jackpots.',
            'summary_title_complete': 'PHANTOM CAPTURED',
            'summary_title_failed': 'PHANTOM VANISHED',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'fifth_avenue_phantom_jackpots',
            'stat_2_label': 'BEST JP',
            'stat_2_var': 'fifth_avenue_phantom_best_jackpot',
            'points_var': 'active_mode_points',
            'state_var': 'fifth_avenue_phantom_state',
            'song': 'play_song_14',
        },
        'enforcers': {
            'title': 'ENFORCERS / OX',
            'intro_1': 'Work the crime zones: drops, pops, and right bank.',
            'intro_2': 'Zone hits light upper-target jackpots.',
            'intro_3': 'Collect all three, then hit OX at center web.',
            'summary_title_complete': 'THE GANG IS BROKEN',
            'summary_title_failed': 'OX GOT AWAY',
            'stat_1_label': 'UPPER JPS',
            'stat_1_var': 'enforcers_upper_jackpots',
            'stat_2_label': 'OX SUPER',
            'stat_2_var': 'enforcers_ox_super_value',
            'points_var': 'active_mode_points',
            'state_var': 'enforcers_state',
            'song': 'play_song_14',
        },
        'diamond_smugglers': {
            'title': 'DIAMOND SMUGGLERS',
            'intro_1': 'Hit drops to build the Diamond Jackpot.',
            'intro_2': 'Complete the 5-bank to start saucer chase.',
            'intro_3': 'Star rollover lights all saucers briefly.',
            'summary_title_complete': 'SMUGGLERS BUSTED',
            'summary_title_failed': 'SMUGGLERS ESCAPED',
            'stat_1_label': 'SHIPMENTS',
            'stat_1_var': 'active_mode_major_hits',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'diamond_bonus',
            'points_var': 'active_mode_points',
            'state_var': 'diamond_smugglers_state',
            'song': 'play_song_26',
        },
        'pardo': {
            'title': 'PARDO',
            'intro_1': 'Pardo commands a mystic performance.',
            'intro_2': 'Complete the moving act shots.',
            'intro_3': 'Break the control before the act changes.',
            'summary_title_complete': 'PARDO DEFEATED',
            'summary_title_failed': 'PARDO ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'pardo_state',
            'song': 'play_song_13',
        },
        'fakir': {
            'title': 'THE FAKIR',
            'intro_1': 'The Fakir hides the real target.',
            'intro_2': 'Spinner briefly reveals the true shot.',
            'intro_3': 'Wrong shots feed the illusion.',
            'summary_title_complete': 'FAKIR DEFEATED',
            'summary_title_failed': 'FAKIR ESCAPED',
            'stat_1_label': 'GOOD SHOTS',
            'stat_1_var': 'fakir_correct_shots',
            'stat_2_label': 'WRONG SHOTS',
            'stat_2_var': 'fakir_incorrect_shots',
            'points_var': 'active_mode_points',
            'state_var': 'fakir_state',
            'song': 'play_song_10',
        },
        'scarlet_sorcerer': {
            'title': 'SCARLET SORCERER',
            'intro_1': 'The Scarlet Sorcerer summons strange magic.',
            'intro_2': 'Hit the lit mystic shots to break the spell.',
            'intro_3': 'Complete the pattern before the curse spreads.',
            'summary_title_complete': 'SORCERER DEFEATED',
            'summary_title_failed': 'SORCERER ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'scarlet_sorcerer_state',
            'song': 'play_song_11',
        },
        'super_swami': {
            'title': 'SUPER SWAMI',
            'intro_1': 'The Super Swami bends minds across the city.',
            'intro_2': 'Follow the moving shot and break his control.',
            'intro_3': 'Complete the sequence to stop the trance.',
            'summary_title_complete': 'SWAMI DEFEATED',
            'summary_title_failed': 'SWAMI ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'super_swami_state',
            'song': 'play_song_12',
        },
        'frog_ghosts': {
            'title': 'FROG GHOSTS',
            'intro_1': 'Frog Ghosts slip through the Fifth Dimension.',
            'intro_2': 'Hit the haunted shots before they move.',
            'intro_3': 'Clear the ghosts and seal the rift.',
            'summary_title_complete': 'GHOSTS BANISHED',
            'summary_title_failed': 'GHOSTS VANISHED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'frog_ghosts_state',
            'song': 'play_song_24',
        },
        'noah_boddy': {
            'title': 'DR. NOAH BODDY',
            'intro_1': 'Noah Boddy vanishes from sight.',
            'intro_2': 'Use upper clues to find the hidden target.',
            'intro_3': 'Hit the true drop before he disappears.',
            'summary_title_complete': 'NOAH BODDY FOUND',
            'summary_title_failed': 'NOAH BODDY ESCAPED',
            'stat_1_label': 'UPPER HITS',
            'stat_1_var': 'noah_boddy_upper_target_hits',
            'stat_2_label': 'BEST JP',
            'stat_2_var': 'noah_boddy_best_jackpot',
            'points_var': 'active_mode_points',
            'state_var': 'noah_boddy_state',
            'song': 'play_song_25',
        },
        'dr_magneto': {
            'title': 'DR. MAGNETO',
            'intro_1': 'Magnetic force pulls shots around the city.',
            'intro_2': 'Use the spinner to stabilize the field.',
            'intro_3': 'Cash the lit shot before it moves.',
            'summary_title_complete': 'DR. MAGNETO DEFEATED',
            'summary_title_failed': 'DR. MAGNETO ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'dr_magneto_state',
            'song': 'play_song_27',
        },
        'professor_pretoris': {
            'title': 'PROFESSOR PRETORIS',
            'intro_1': 'Pretoris is shrinking the city.',
            'intro_2': 'Solve the shot puzzle before the ray fires.',
            'intro_3': 'Beat the sequence and restore the landmark.',
            'summary_title_complete': 'PRETORIS STOPPED',
            'summary_title_failed': 'PRETORIS ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'professor_pretoris_state',
            'song': 'play_song_28',
        },
        'doctor_dumpty': {
            'title': 'DOCTOR DUMPTY',
            'intro_1': 'Doctor Dumpty has a fragile plan.',
            'intro_2': 'Build value without cracking the sequence.',
            'intro_3': 'Wrong shots break the egg.',
            'summary_title_complete': 'DOCTOR DUMPTY DEFEATED',
            'summary_title_failed': 'DOCTOR DUMPTY ESCAPED',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'doctor_dumpty_jackpots',
            'stat_2_label': 'MISSES',
            'stat_2_var': 'doctor_dumpty_missed_shots',
            'points_var': 'active_mode_points',
            'state_var': 'doctor_dumpty_state',
            'song': 'play_song_7',
        },
        'dr_von_schlick': {
            'title': 'DR. VON SCHLICK',
            'intro_1': 'Von Schlick has slicked the playfield.',
            'intro_2': 'Control the sequence before shots slip away.',
            'intro_3': 'Finish the pattern to end the oil scheme.',
            'summary_title_complete': 'SCHLICK STOPPED',
            'summary_title_failed': 'SCHLICK ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'dr_von_schlick_state',
            'song': 'play_song_8',
        },
        'radiation_specialist': {
            'title': 'RADIATION SPECIALIST',
            'intro_1': 'Radiation is spreading across the city.',
            'intro_2': 'Hit charged shots to contain it.',
            'intro_3': 'Finish the sequence before the warning peaks.',
            'summary_title_complete': 'RADIATION CONTAINED',
            'summary_title_failed': 'RADIATION ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'radiation_bonus',
            'points_var': 'active_mode_points',
            'state_var': 'radiation_specialist_state',
            'song': 'play_song_15',
        },
        'dr_zap': {
            'title': 'DR. ZAP',
            'intro_1': 'Dr. Zap chains electricity across shots.',
            'intro_2': 'Follow the lit charge pattern.',
            'intro_3': 'Break the circuit before it overloads.',
            'summary_title_complete': 'DR. ZAP DEFEATED',
            'summary_title_failed': 'DR. ZAP ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'dr_zap_state',
            'song': 'play_song_9',
        },
        'doctor_cool': {
            'title': 'DOCTOR COOL',
            'intro_1': 'Doctor Cool freezes timers and shots.',
            'intro_2': 'Thaw the lit shots with spinner and targets.',
            'intro_3': 'Cash the jackpot before everything freezes.',
            'summary_title_complete': 'DOCTOR COOL DEFEATED',
            'summary_title_failed': 'DOCTOR COOL ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'doctor_cool_state',
            'song': 'play_song_8',
        },
        'snowman': {
            'title': 'THE SNOWMAN',
            'intro_1': 'The Snowman is freezing the city.',
            'intro_2': 'Thaw frozen shots with spinner and targets.',
            'intro_3': 'Break the freeze before time runs out.',
            'summary_title_complete': 'SNOWMAN MELTED',
            'summary_title_failed': 'SNOWMAN ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'snowman_state',
            'song': 'play_song_20',
        },
        'ice_monster': {
            'title': 'THE ICE MONSTER',
            'intro_1': 'The Ice Monster blocks the city in frozen chaos.',
            'intro_2': 'Hit thaw shots to open scoring.',
            'intro_3': 'Collect the jackpot before everything freezes.',
            'summary_title_complete': 'ICE MONSTER STOPPED',
            'summary_title_failed': 'ICE MONSTER ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'ice_monster_state',
            'song': 'play_song_21',
        },
        'dr_manta': {
            'title': 'DR. MANTA',
            'intro_1': 'Dr. Manta traps the city beneath the waves.',
            'intro_2': 'Escape saucer traps with lit rescue shots.',
            'intro_3': 'Collect the jackpot before he dives again.',
            'summary_title_complete': 'DR. MANTA DEFEATED',
            'summary_title_failed': 'DR. MANTA ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'dr_manta_state',
            'song': 'play_song_28',
        },
        'doctor_atlantean': {
            'title': 'DOCTOR ATLANTEAN',
            'intro_1': 'Doctor Atlantean rules from a lost city.',
            'intro_2': 'Hit sky shots to bring the city down.',
            'intro_3': 'Complete the attack before he escapes.',
            'summary_title_complete': 'ATLANTEAN DEFEATED',
            'summary_title_failed': 'ATLANTEAN ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'doctor_atlantean_state',
            'song': 'play_song_16',
        },
        'sky_master': {
            'title': 'SKY MASTER',
            'intro_1': 'Sky Master attacks from above the clouds.',
            'intro_2': 'Find the moving flight path.',
            'intro_3': 'Hit the lit shots and ground his aircraft.',
            'summary_title_complete': 'SKY MASTER GROUNDED',
            'summary_title_failed': 'SKY MASTER ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'sky_master_state',
            'song': 'play_song_17',
        },
        'plutonians': {
            'title': 'THE PLUTONIANS',
            'intro_1': 'The Plutonians have landed.',
            'intro_2': 'Hit invasion shots before they reposition.',
            'intro_3': 'Stop the attack and save the city.',
            'summary_title_complete': 'PLUTONIANS REPELLED',
            'summary_title_failed': 'PLUTONIANS ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'plutonian_bonus',
            'points_var': 'active_mode_points',
            'state_var': 'plutonians_state',
            'song': 'play_song_19',
        },
        'antarcticans': {
            'title': 'THE ANTARCTICANS',
            'intro_1': 'The Antarcticans strike from the ice.',
            'intro_2': 'Hit rescue shots before the freeze spreads.',
            'intro_3': 'Finish the sequence and escape the trap.',
            'summary_title_complete': 'ANTARCTICANS STOPPED',
            'summary_title_failed': 'ANTARCTICANS ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'antarcticans_state',
            'song': 'play_song_18',
        },
        'charles_cameo': {
            'title': 'CHARLES CAMEO',
            'intro_1': 'Charles Cameo hides behind disguises.',
            'intro_2': 'Identify the real shot pattern.',
            'intro_3': 'Shoot the true villain before he changes roles.',
            'summary_title_complete': 'CHARLES CAMEO DEFEATED',
            'summary_title_failed': 'CHARLES CAMEO ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'charles_cameo_state',
            'song': 'play_song_28',
        },
        'brutus': {
            'title': 'BRUTUS',
            'intro_1': 'Brutus is guarding the hideout.',
            'intro_2': 'Break through his cover with lit shots.',
            'intro_3': 'Finish the fight before he blocks the route.',
            'summary_title_complete': 'BRUTUS BEATEN',
            'summary_title_failed': 'BRUTUS ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'brutus_state',
            'song': 'play_song_23',
        },
        'eigor': {
            'title': 'EIGOR',
            'intro_1': 'Eigor is smashing through the city.',
            'intro_2': 'Hit heavy shots to wear him down.',
            'intro_3': 'Collect the jackpot before he escapes.',
            'summary_title_complete': 'EIGOR STOPPED',
            'summary_title_failed': 'EIGOR ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'eigor_state',
            'song': 'play_song_10',
        },
        'the_fly': {
            'title': 'THE FLY',
            'intro_1': 'The Fly crawls across the city walls.',
            'intro_2': 'Track the moving shot and cut him off.',
            'intro_3': 'Catch him before he slips away.',
            'summary_title_complete': 'FLY CAUGHT',
            'summary_title_failed': 'FLY ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'the_fly_state',
            'song': 'play_song_9',
        },
        'swamp_reptiles': {
            'title': 'SWAMP REPTILES',
            'intro_1': 'Swamp Reptiles are loose in the city.',
            'intro_2': 'Hit pops to light Rampage Jackpots.',
            'intro_3': 'Collect the Super Jackpot at the saucer.',
            'summary_title_complete': 'REPTILES CAPTURED',
            'summary_title_failed': 'REPTILES ESCAPED',
            'stat_1_label': 'RAMPAGE JPS',
            'stat_1_var': 'swamp_reptiles_jackpots_collected',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'swamp_bonus',
            'points_var': 'active_mode_points',
            'state_var': 'swamp_reptiles_state',
            'song': 'play_song_14',
        },
        'phantom_from_depths_of_time': {
            'title': 'PHANTOM FROM THE DEPTHS OF TIME',
            'intro_1': 'The Phantom rises from another age.',
            'intro_2': 'Follow the time-tossed shots.',
            'intro_3': 'Complete the sequence before he fades away.',
            'summary_title_complete': 'PHANTOM DEFEATED',
            'summary_title_failed': 'PHANTOM ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'phantom_from_depths_of_time_state',
            'song': 'play_song_11',
        },
        'master_vine': {
            'title': 'MASTER VINE',
            'intro_1': 'Master Vine spreads across the playfield.',
            'intro_2': 'Clear vine shots before they lock out.',
            'intro_3': 'Stop the growth before it covers the city.',
            'summary_title_complete': 'MASTER VINE DEFEATED',
            'summary_title_failed': 'MASTER VINE ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'master_vine_state',
            'song': 'play_song_22',
        },
        'master_technician': {
            'title': 'MASTER TECHNICIAN',
            'intro_1': 'Drop targets set the spinner value.',
            'intro_2': 'Build the circuit, then rip the spinner.',
            'intro_3': 'Complete a bank before the system shorts out.',
            'summary_title_complete': 'TECHNICIAN STOPPED',
            'summary_title_failed': 'TECHNICIAN ESCAPED',
            'stat_1_label': 'SPINNER VALUE',
            'stat_1_var': 'master_technician_spinner_value',
            'stat_2_label': 'BONUS BANKED',
            'stat_2_var': 'technician_bonus',
            'points_var': 'active_mode_points',
            'state_var': 'master_technician_state',
            'song': 'play_song_14',
        },
        'micro_men': {
            'title': 'MICRO-MEN',
            'intro_1': 'The Micro-Men attack from every direction.',
            'intro_2': 'Hit tiny targets before they scatter.',
            'intro_3': 'Clear the swarm and restore the scale.',
            'summary_title_complete': 'MICRO-MEN STOPPED',
            'summary_title_failed': 'MICRO-MEN ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'micro_men_state',
            'song': 'play_song_12',
        },
        'grand_emperor': {
            'title': 'GRAND EMPEROR',
            'intro_1': 'The Grand Emperor commands the final attack.',
            'intro_2': 'Hit invasion shots in order.',
            'intro_3': 'Stop the command signal before it completes.',
            'summary_title_complete': 'EMPEROR DEFEATED',
            'summary_title_failed': 'EMPEROR ESCAPED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'MAJOR HITS',
            'stat_2_var': 'active_mode_major_hits',
            'points_var': 'active_mode_points',
            'state_var': 'grand_emperor_state',
            'song': 'play_song_12',
        },
        'sinister_surge': {
            'title': 'SINISTER SURGE',
            'intro_1': 'Chapter 1 mini-wizard multiball.',
            'intro_2': 'Collect surge jackpots and survive.',
            'intro_3': 'Chapter case files raise the values.',
            'summary_title_complete': 'SINISTER SURGE CLEARED',
            'summary_title_failed': 'SINISTER SURGE LOST',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'sinister_surge_state',
            'points_var': 'active_mode_points',
            'state_var': 'sinister_surge_state',
            'song': 'play_song_22',
        },
        'mastermind_trap': {
            'title': 'MASTERMIND TRAP',
            'intro_1': 'Chapter 2 mini-wizard multiball.',
            'intro_2': 'Escape the masterminds while multiball runs.',
            'intro_3': 'Chapter case files raise the values.',
            'summary_title_complete': 'MASTERMIND TRAP CLEARED',
            'summary_title_failed': 'MASTERMIND TRAP LOST',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'mastermind_trap_state',
            'points_var': 'active_mode_points',
            'state_var': 'mastermind_trap_state',
            'song': 'play_song_18',
        },
        'trubble_unleashed': {
            'title': 'TRUBBLE UNLEASHED',
            'intro_1': 'Miss Trubble has unleashed her creations.',
            'intro_2': 'Use roof targets, saucers, and staged drops.',
            'intro_3': 'Survive multiball as long as you can.',
            'summary_title_complete': 'TRUBBLE CONTAINED',
            'summary_title_failed': 'TRUBBLE RUNS WILD',
            'stat_1_label': 'JACKPOTS',
            'stat_1_var': 'trubble_unleashed_jackpots_collected',
            'stat_2_label': 'STAGED HITS',
            'stat_2_var': 'trubble_unleashed_staged_hits',
            'points_var': 'active_mode_points',
            'state_var': 'trubble_unleashed_state',
            'song': 'play_song_14',
        },
        'master_plan': {
            'title': 'THE PLOTTER - MASTER PLAN',
            'intro_1': 'Decode the Plotter’s scheme.',
            'intro_2': 'Build headlines and cash Daily Bugle supers.',
            'intro_3': 'Chapter case files raise the values.',
            'summary_title_complete': 'MASTER PLAN EXPOSED',
            'summary_title_failed': 'PLOTTER ESCAPED',
            'stat_1_label': 'HEADLINES',
            'stat_1_var': 'master_plan_headlines_collected',
            'stat_2_label': 'SUPERS',
            'stat_2_var': 'master_plan_super_collected',
            'points_var': 'active_mode_points',
            'state_var': 'master_plan_state',
            'song': 'play_song_14',
        },
        'fifth_dimension_curse': {
            'title': 'FIFTH DIMENSION CURSE',
            'intro_1': 'Chapter 5 mini-wizard multiball.',
            'intro_2': 'Break the curse during multiball.',
            'intro_3': 'Chapter case files raise the values.',
            'summary_title_complete': 'CURSE BROKEN',
            'summary_title_failed': 'CURSE ESCAPES',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'fifth_dimension_curse_state',
            'points_var': 'active_mode_points',
            'state_var': 'fifth_dimension_curse_state',
            'song': 'play_song_16',
        },
        'mad_science_meltdown': {
            'title': 'MAD SCIENCE MELTDOWN',
            'intro_1': 'Chapter 6 mini-wizard multiball.',
            'intro_2': 'Keep the lab under control.',
            'intro_3': 'Chapter case files raise the values.',
            'summary_title_complete': 'MELTDOWN STOPPED',
            'summary_title_failed': 'MELTDOWN SPREADS',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'mad_science_meltdown_state',
            'points_var': 'active_mode_points',
            'state_var': 'mad_science_meltdown_state',
            'song': 'play_song_15',
        },
        'nature_strikes_back': {
            'title': 'NATURE STRIKES BACK',
            'intro_1': 'Chapter 7 mini-wizard multiball.',
            'intro_2': 'Contain the elemental chaos.',
            'intro_3': 'Chapter case files raise the values.',
            'summary_title_complete': 'NATURE CONTAINED',
            'summary_title_failed': 'NATURE BREAKS LOOSE',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'nature_strikes_back_state',
            'points_var': 'active_mode_points',
            'state_var': 'nature_strikes_back_state',
            'song': 'play_song_20',
        },
        'invasion_from_everywhere': {
            'title': 'INVASION FROM EVERYWHERE',
            'intro_1': 'Chapter 8 mini-wizard multiball.',
            'intro_2': 'Fight the lost-world invaders.',
            'intro_3': 'Chapter case files raise the values.',
            'summary_title_complete': 'INVASION STOPPED',
            'summary_title_failed': 'INVASION CONTINUES',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'invasion_from_everywhere_state',
            'points_var': 'active_mode_points',
            'state_var': 'invasion_from_everywhere_state',
            'song': 'play_song_19',
        },
        'who_is_the_real_villain': {
            'title': 'WHO IS THE REAL VILLAIN?',
            'intro_1': 'Chapter 9 mini-wizard multiball.',
            'intro_2': 'Unmask the chaos while multiball runs.',
            'intro_3': 'Chapter case files raise the values.',
            'summary_title_complete': 'VILLAIN REVEALED',
            'summary_title_failed': 'VILLAIN VANISHED',
            'stat_1_label': 'HITS',
            'stat_1_var': 'active_mode_hits',
            'stat_2_label': 'STATE',
            'stat_2_var': 'who_is_the_real_villain_state',
            'points_var': 'active_mode_points',
            'state_var': 'who_is_the_real_villain_state',
            'song': 'play_song_21',
        },
        'time_tossed_showdown': {
            'title': 'TIME-TOSSED SHOWDOWN',
            'intro_1': 'Chapter 10 mini-wizard multiball.',
            'intro_2': 'Survive the time-tossed brawl.',
            'intro_3': 'Chapter case files raise the values.',
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
        'final_showdown': {
            'title': 'FINAL SHOWDOWN',
            'intro_1': 'The citywide battle reaches its peak.',
            'intro_2': 'Clear areas and collect Daily Bugle jackpots.',
            'intro_3': 'Finish the final battle to save the city.',
            'summary_title_complete': 'FINAL SHOWDOWN WON',
            'summary_title_failed': 'FINAL SHOWDOWN LOST',
            'stat_1_label': 'AREAS CLEARED',
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

        self.add_mode_event_handler("villain_bookend_intro_request", self._intro_request)
        self.add_mode_event_handler("villain_bookend_summary_request", self._summary_request)
        self.add_mode_event_handler("flipper_cancel", self._skip_current_bookend)
        self.add_mode_event_handler("villain_bookend_intro_hold_request", self._intro_hold_request)
        self.add_mode_event_handler("villain_bookend_intro_hold_release", self._intro_hold_release)

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
        self._set_machine_var("villain_bookend_line_1", f"{data['stat_1_label']}: {stat_1}")
        self._set_machine_var("villain_bookend_line_2", f"{data['stat_2_label']}: {stat_2}")
        self._set_machine_var("villain_bookend_line_3", f"POINTS: {points:,}")
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
            self.machine.events.post(data["song"])
            self.machine.events.post("villain_bookend_intro_hide")
            self.machine.events.post("villain_bookend_intro_done", villain=villain)
        elif stage == "summary":
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
