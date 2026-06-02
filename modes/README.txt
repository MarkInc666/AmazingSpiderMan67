Spider-Man System Build 2

Included modes:

1. case_files
   - Lower spinner cycles Case File target every 3 spins.
   - Right 5-bank collects Case Files.
   - All 5 Case Files add Wizard Prep.
   - Individual Case Files clear when villain_mode_started posts.

2. villain_progression
   - Tracks chapters and played villains.
   - Starts default or selected villains.
   - Marks chapter mini-wizard ready after 5 villains.

3. qualify_system
   - 3-bank drop targets advance corresponding saucer states.
   - Saucer state persists between balls.
   - Saucer states reset after villain start/end.
   - Bank resets after all 3 drops are hit.
   - Star advances all saucers if all 3 saucers are already state 1+.

4. villain_start
   - Saucers decide points/start/select/mini-wizard/final wizard.
   - State 0 = points only.
   - State 1 = start one available villain.
   - State 2-5 = start carousel with up to that many villains.
   - If only one playable villain is available, skips carousel and starts it.

Important placeholders to replace:

case_files.yaml:
- s_lower_spinner_active
- s_right_bank_drop_1_active through s_right_bank_drop_5_active

qualify_system.yaml:
- s_left_3bank_drop_active
- s_center_3bank_drop_active
- s_right_3bank_drop_active
- s_star_active

villain_start.yaml:
- s_left_saucer_active
- s_center_saucer_active
- s_right_saucer_active

Also replace all show names with your actual shows/lights.
