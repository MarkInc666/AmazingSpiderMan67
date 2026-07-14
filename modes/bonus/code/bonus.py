from mpf.core.mode import Mode
from mpf.modes.bonus.code.bonus import Bonus as MpfBonus


class Bonus(MpfBonus):
    """ASM67 clean end-of-ball bonus sequence.

    Presentation rules:
      * Bonus slide appears first with player score visible.
      * Regular bonus buckets count from low to high once per multiplier cycle.
      * Each shown bucket is added to score immediately.
      * Multiplier lamps 2X-5X go out after their cycle is counted.
      * Mode/chapter bonuses are shown after a longer pause and scored as shown.
    """

    BONUS_BUCKETS_DESC = [
        (20, 20000, "20K", "l_20k"),
        (10, 10000, "10K", "l_10k"),
        (9, 9000, "9K", "l_9k"),
        (8, 8000, "8K", "l_8k"),
        (7, 7000, "7K", "l_7k"),
        (6, 6000, "6K", "l_6k"),
        (5, 5000, "5K", "l_5k"),
        (4, 4000, "4K", "l_4k"),
        (3, 3000, "3K", "l_3k"),
        (2, 2000, "2K", "l_2k"),
        (1, 1000, "1K", "l_1k"),
    ]

    MODE_BONUS_ENTRIES = [
        ("held_bonus", "HELD BONUS", True),
        ("vulture_bonus", "VULTURE FLIGHT", False),
        ("goblin_bonus", "GOBLIN CHAOS", False),
        ("vulcan_bonus", "VULCAN ERUPTION", False),
        ("diamond_bonus", "DIAMOND SMUGGLERS", False),
        ("super_swami_bonus", "SUPER SWAMI", False),
        ("dumpty_bonus", "DUMPTY DEVICES", False),
        ("radiation_bonus", "RADIATION RAMPAGE", False),
        ("plutonians_bonus", "THE PLUTONIANS", False),
        ("swamp_bonus", "SWAMP REPTILES", False),
        ("technician_bonus", "TECHNICIAN TRAP", False),
    ]

    MULTIPLIER_LIGHTS = {
        2: "l_2x",
        3: "l_3x",
        4: "l_4x",
        5: "l_5x",
    }

    INTRO_DELAY_MS = 700
    BUCKET_STEP_MS = 160
    NEXT_CYCLE_DELAY_MS = 260
    MODE_PAGE_DELAY_MS = 1100
    MODE_STEP_MS = 850
    FINAL_SCORE_HOLD_MS = 2500

    def mode_start(self, **kwargs):
        # Do not call MpfBonus.mode_start(); that would run stock bonus math.
        Mode.mode_start(self, **kwargs)

        self._player = self.machine.game.player
        self._bonus_running = True

        self.machine.events.post("bonus_start", ball=self._player["ball"])

        # Let other ball_ending handlers finish banking values before the
        # visible bonus count snapshots the player's bonus vars.
        self.delay.add(
            name="asm_bonus_begin_sequence",
            ms=100,
            callback=self._begin_bonus_sequence,
        )

    def _begin_bonus_sequence(self):
        self._lit_buckets = self._build_lit_bucket_list()
        self._regular_total = 0
        self._final_total = 0
        self._mode_entries = []
        self._mode_index = 0
        self._bucket_index = 0
        self._current_pass = 1
        self._bonus_multiplier = max(1, min(5, int(self._player["bonus_multiplier"])))
        self._hold_bonus_earned = bool(self._player["hold_bonus"])

        self._show_bonus_entry("bonus_title", "BONUS", "")

        self.delay.add(
            name="asm_bonus_start_regular",
            ms=self.INTRO_DELAY_MS,
            callback=self._start_regular_or_mode_bonus,
        )

    def _build_lit_bucket_list(self):
        remaining = min(int(self._player["bonus_count"]), 75)
        lit = []

        for bucket_count, bucket_value, bucket_text, light_name in self.BONUS_BUCKETS_DESC:
            if remaining >= bucket_count:
                lit.append((bucket_count, bucket_value, bucket_text, light_name))
                remaining -= bucket_count

        # Count visibly from lowest to highest.
        return list(reversed(lit))

    def _start_regular_or_mode_bonus(self):
        if self._lit_buckets:
            self._start_regular_pass()
        else:
            self._finish_regular_bonus()

    def _start_regular_pass(self):
        self._bucket_index = 0
        self._relight_lit_bonus_buckets()

        if self._current_pass > 1:
            self._show_bonus_entry(
                "bonus_title",
                "{}X BONUS".format(self._current_pass),
                "",
            )
        else:
            self._show_bonus_entry("bonus_title", "BONUS", "")

        self.delay.add(
            name="asm_bonus_first_bucket",
            ms=self.BUCKET_STEP_MS,
            callback=self._count_next_bonus_bucket,
        )

    def _count_next_bonus_bucket(self):
        if self._bucket_index >= len(self._lit_buckets):
            self._finish_regular_pass()
            return

        _, bucket_value, bucket_text, light_name = self._lit_buckets[self._bucket_index]

        self._player["score"] += bucket_value
        self._regular_total += bucket_value
        self._final_total += bucket_value

        self._show_bonus_entry("regular_bucket", bucket_text, bucket_value)
        self.machine.events.post(
            "asm_bonus_bucket_counted",
            bucket=bucket_text,
            value=bucket_value,
            total=self._regular_total,
        )
        self.machine.events.post("bonus_light_{}_off".format(light_name))

        self._bucket_index += 1
        self.delay.add(
            name="asm_bonus_next_bucket",
            ms=self.BUCKET_STEP_MS,
            callback=self._count_next_bonus_bucket,
        )

    def _finish_regular_pass(self):
        self._turn_off_multiplier_light_for_pass(self._current_pass)
        self._current_pass += 1

        if self._current_pass <= self._bonus_multiplier:
            self.delay.add(
                name="asm_bonus_next_regular_pass",
                ms=self.NEXT_CYCLE_DELAY_MS,
                callback=self._start_regular_pass,
            )
        else:
            self.delay.add(
                name="asm_bonus_finish_regular",
                ms=self.MODE_PAGE_DELAY_MS,
                callback=self._finish_regular_bonus,
            )

    def _finish_regular_bonus(self):
        self._turn_off_all_bonus_bucket_lights()
        self.delay.add(
            name="asm_bonus_start_mode_page",
            ms=0,
            callback=self._start_mode_bonus_page,
        )

    def _start_mode_bonus_page(self):
        self._mode_entries = self._build_mode_entries()
        self._mode_index = 0

        if not self._mode_entries:
            self.delay.add(
                name="asm_bonus_finalize_no_modes",
                ms=self.MODE_PAGE_DELAY_MS,
                callback=self._handle_hold_bonus,
            )
            return

        self._show_bonus_entry("mode_title", "MODE BONUS", "")
        self.delay.add(
            name="asm_bonus_first_mode_entry",
            ms=self.MODE_PAGE_DELAY_MS,
            callback=self._count_next_mode_entry,
        )

    def _build_mode_entries(self):
        entries = []
        for var_name, text, consume_after_award in self.MODE_BONUS_ENTRIES:
            try:
                value = int(self._player[var_name])
            except (KeyError, TypeError, ValueError):
                value = 0

            if value > 0:
                entries.append((var_name, text, value, consume_after_award))
        return entries

    def _count_next_mode_entry(self):
        if self._mode_index >= len(self._mode_entries):
            self.delay.add(
                name="asm_bonus_finalize",
                ms=self.MODE_PAGE_DELAY_MS,
                callback=self._handle_hold_bonus,
            )
            return

        var_name, text, value, consume_after_award = self._mode_entries[self._mode_index]

        self._player["score"] += value
        self._final_total += value

        self._show_bonus_entry("mode_bonus", text, value)
        self.machine.events.post(
            "asm_bonus_mode_counted",
            bonus_name=text,
            value=value,
            total=self._final_total,
        )

        if consume_after_award:
            self._player[var_name] = 0

        self._mode_index += 1
        self.delay.add(
            name="asm_bonus_next_mode_entry",
            ms=self.MODE_STEP_MS,
            callback=self._count_next_mode_entry,
        )

    def _handle_hold_bonus(self):
        if self._hold_bonus_earned:
            if self._is_last_ball():
                self._player["score"] += self._final_total
                self._player["held_bonus"] = 0
                self._show_bonus_entry("hold_bonus", "HOLD BONUS", self._final_total)
                self.machine.events.post("asm_hold_bonus_awarded", total=self._final_total)
            else:
                self._player["held_bonus"] = self._final_total
                self._show_bonus_entry("bonus_held", "BONUS HELD", self._final_total)
                self.machine.events.post("asm_bonus_held", total=self._final_total)
        else:
            self._player["held_bonus"] = 0

        self._player["hold_bonus"] = 0
        self._reset_regular_bonus_state()

        self.machine.events.post("asm_bonus_total_awarded", total=self._final_total)
        self._show_bonus_entry("final_score_hold", "PLAYER SCORE", int(self._player["score"]))

        self.delay.add(
            name="asm_bonus_finish",
            ms=self.FINAL_SCORE_HOLD_MS,
            callback=self._finish_bonus,
        )

    def _reset_regular_bonus_state(self):
        self._player["bonus_count"] = 0
        self._player["bonus_multiplier"] = 1
        self._turn_off_all_bonus_bucket_lights()
        self._turn_off_all_multiplier_lights()

    def _relight_lit_bonus_buckets(self):
        for _, _, _, light_name in self._lit_buckets:
            self.machine.events.post("bonus_light_{}_on".format(light_name))

    def _turn_off_all_bonus_bucket_lights(self):
        for _, _, _, light_name in self.BONUS_BUCKETS_DESC:
            self.machine.events.post("bonus_light_{}_off".format(light_name))

    def _turn_off_multiplier_light_for_pass(self, bonus_pass):
        light_name = self.MULTIPLIER_LIGHTS.get(bonus_pass)
        if light_name:
            self.machine.events.post("bonus_light_{}_off".format(light_name))

    def _turn_off_all_multiplier_lights(self):
        for light_name in self.MULTIPLIER_LIGHTS.values():
            self.machine.events.post("bonus_light_{}_off".format(light_name))

    def _show_bonus_entry(self, entry, text, score):
        self.machine.events.post(
            "bonus_entry",
            entry=entry,
            text=text,
            score=score,
        )

    def _is_last_ball(self):
        try:
            return int(self._player["ball"]) >= int(self.machine.config["game"]["balls_per_game"])
        except (KeyError, TypeError, ValueError):
            return False

    def _finish_bonus(self):
        # Let MPF's mode wait queue be cleared by the mode lifecycle.
        # Clearing it manually here can double-clear and raise "Not locked".
        self.stop()
