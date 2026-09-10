import random

from mpf.core.delays import DelayManager
from mpf.core.mode import Mode


class MadScienceMeltdown(Mode):
    """Chapter 7 wizard: repeatable gas and Noah jackpots until multiball ends."""

    MODE_KEY = "mad_science_meltdown"
    DISPLAY_NAME = "Mad Science Meltdown"

    GAS_BASE_JACKPOT = 500_000
    NOAH_BASE_JACKPOT = 500_000
    NOAH_SPINNER_STEP = 100_000
    GAS_RED_SCORE = 25_000
    GAS_YELLOW_SCORE = 50_000
    MAX_BALLS = 4
    MAX_PARKED_BALLS = 2
    MAGNETO_SECONDS = 10
    VUK_EJECT_MS = 1_000
    RIGHT_DROP_PENDING_MS = 1_500
    BANK_RESET_MS = 600

    GAS_ZONES = (
        "left_web",
        "center_web",
        "left_pop",
        "right_pop",
        "left_sling",
        "right_sling",
    )
    GAS_LABELS = {
        "left_web": "LEFT WEB",
        "center_web": "CENTER WEB",
        "left_pop": "LEFT POP",
        "right_pop": "RIGHT POP",
        "left_sling": "LEFT SLING",
        "right_sling": "RIGHT SLING",
    }
    GAS_LEVELS = {"red": 3, "yellow": 2, "green": 1}
    GAS_COLORS = {3: "red", 2: "yellow", 1: "green"}

    LEFT_DROPS = (1, 2, 3)
    RIGHT_DROPS = (1, 2, 3, 4, 5)
    UPPER_TARGETS = ("left", "center", "right")

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.mode_exiting = False
        self.mode_points = 0

        self.case_file_bonus = self._safe_int(self._get("mini_wizard_case_file_bonus", 0), 0)
        self.gas_states = {zone: 0 for zone in self.GAS_ZONES}
        self.gas_jackpots = 0
        self.noah_jackpots = 0
        self.noah_spinner_spins = 0

        self.left_down = set()
        self.left_bank_resetting = True
        self.right_down = set()
        self.programmatic_right_pending = set()
        self.right_bank_resetting = True
        self.noah_revealed = False

        self.parked_saucers = set()
        self.a_collected = False
        self.b_collected = False
        self.magneto_ready = False
        self.magneto_seconds_left = 0
        self.gate_open = False

        self._set(f"{self.MODE_KEY}_state", 1)
        self._set("mini_wizard_current_key", self.MODE_KEY)
        self._set("active_mode_points", 0)
        self._set("active_mode_hits", 0)
        self._set("active_mode_major_hits", 0)

        for target in self.LEFT_DROPS:
            self.add_mode_event_handler(
                f"{self.MODE_KEY}_left_drop_{target}_hit",
                self._left_drop_hit,
                target=target,
            )
        for target in self.RIGHT_DROPS:
            self.add_mode_event_handler(
                f"{self.MODE_KEY}_right_drop_{target}_hit",
                self._right_drop_hit,
                target=target,
            )
        for target in self.UPPER_TARGETS:
            self.add_mode_event_handler(
                f"{self.MODE_KEY}_upper_target_{target}_hit",
                self._upper_target_hit,
                target=target,
            )
        for zone in self.GAS_ZONES:
            self.add_mode_event_handler(
                f"{self.MODE_KEY}_gas_{zone}_hit",
                self._gas_zone_hit,
                zone=zone,
            )
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(
                f"{self.MODE_KEY}_saucer_{saucer}_hit",
                self._saucer_hit,
                saucer=saucer,
            )

        self.add_mode_event_handler(f"{self.MODE_KEY}_left_bank_complete", self._left_bank_complete)
        self.add_mode_event_handler(f"{self.MODE_KEY}_right_bank_complete", self._right_bank_complete)
        self.add_mode_event_handler(f"{self.MODE_KEY}_lower_spinner_hit", self._lower_spinner_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_upper_spinner_hit", self._upper_spinner_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_a_hit", self._a_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_b_hit", self._b_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_center_web_hit", self._center_web_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._complete_mode)

        self.machine.events.post("chapter_mini_wizard_started", mini_wizard=self.MODE_KEY)
        self.machine.events.post(f"{self.MODE_KEY}_setup")
        self.machine.events.post(f"{self.MODE_KEY}_start_multiball")
        self._set_gate(True)
        self._schedule_bank_reset_finished("left")
        self._schedule_bank_reset_finished("right")
        self._refresh_all_gas_lights()
        self._refresh_noah_lights()
        self._refresh_magneto_lights()
        self._refresh_saucer_lights()
        self._show_message(
            "MAD SCIENCE MELTDOWN",
            "LEFT DROPS RELEASE GAS - SPINNER COOLS",
            reminder=True,
        )
        self._schedule_ball_guard()
        self._sync_vars()
        self._update_status()

    def mode_stop(self, **kwargs):
        self.mode_exiting = True
        self.delay.clear()
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post(f"{self.MODE_KEY}_clear_all_lights")
        self.machine.events.post(f"{self.MODE_KEY}_vuk_chase_stop")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        if self.machine.game and self._get("mini_wizard_current_key", "") == self.MODE_KEY:
            self._set("mini_wizard_current_key", "")
        super().mode_stop(**kwargs)

    # ------------------------------------------------------------------
    # Gas release, cooling and collection
    # ------------------------------------------------------------------

    def _left_drop_hit(self, target=None, **kwargs):
        if self._inactive() or self.left_bank_resetting or target is None:
            return
        target = int(target)
        if target in self.left_down:
            return
        self.left_down.add(target)
        self._release_gas_zone()
        self._sync_vars()
        self._update_status()

    def _left_bank_complete(self, **kwargs):
        if self._inactive() or self.left_bank_resetting:
            return

        # Switch ordering can vary by hardware. Guarantee that all three target
        # closures release exactly one gas area each before the bank resets.
        for target in self.LEFT_DROPS:
            if target not in self.left_down:
                self.left_down.add(target)
                self._release_gas_zone()

        self._set_gate(False)
        self.left_bank_resetting = True
        self.left_down.clear()
        self.machine.events.post("drop_target_bank_dt_bank_left_reset")
        self._schedule_bank_reset_finished("left")
        self._show_message("GAS BANK COMPLETE", "ROOFTOP GATE CLOSED")
        self._sync_vars()
        self._update_status()

    def _release_gas_zone(self):
        available = [zone for zone, level in self.gas_states.items() if level == 0]
        if not available:
            self._show_message("GAS MAXIMUM", "COOL AND COLLECT ACTIVE ZONES")
            return None

        zone = random.choice(available)
        self.gas_states[zone] = self.GAS_LEVELS["red"]
        self.machine.events.post(
            f"{self.MODE_KEY}_gas_released",
            zone=zone,
            zone_label=self.GAS_LABELS[zone],
        )
        self._refresh_gas_light(zone)
        self._show_message("GAS RELEASED", f"{self.GAS_LABELS[zone]} RED")
        return zone

    def _lower_spinner_hit(self, **kwargs):
        if self._inactive():
            return
        cooled = []
        for zone, level in self.gas_states.items():
            if level > self.GAS_LEVELS["green"]:
                self.gas_states[zone] = level - 1
                cooled.append(zone)
                self._refresh_gas_light(zone)

        if cooled:
            green = sum(1 for level in self.gas_states.values() if level == self.GAS_LEVELS["green"])
            self.machine.events.post(f"{self.MODE_KEY}_gas_cooled", zones=tuple(cooled), green=green)
            self._show_message("GAS COOLED", f"{green} GREEN - COLLECT JACKPOTS")
            self._sync_vars()
            self._update_status()

    def _gas_zone_hit(self, zone=None, **kwargs):
        if self._inactive() or zone not in self.gas_states:
            return 0
        level = self.gas_states[zone]
        if level <= 0:
            return 0

        if level == self.GAS_LEVELS["red"]:
            self._score(self.GAS_RED_SCORE)
            self._show_message("RED GAS", self.GAS_LABELS[zone], self.GAS_RED_SCORE)
            return self.GAS_RED_SCORE

        if level == self.GAS_LEVELS["yellow"]:
            self._score(self.GAS_YELLOW_SCORE)
            self._show_message("YELLOW GAS", self.GAS_LABELS[zone], self.GAS_YELLOW_SCORE)
            return self.GAS_YELLOW_SCORE

        value = self.GAS_BASE_JACKPOT + self.case_file_bonus
        self.gas_states[zone] = 0
        self.gas_jackpots += 1
        self._score(value)
        self.machine.events.post(
            f"{self.MODE_KEY}_gas_jackpot_collected",
            zone=zone,
            zone_label=self.GAS_LABELS[zone],
            value=value,
        )
        self._refresh_gas_light(zone)
        self._show_jackpot("GAS JACKPOT", value, self.GAS_LABELS[zone])
        if not self._active_gas_count() and not self.noah_revealed:
            self._set_gate(True)
        self._sync_vars()
        self._update_status()
        return value

    # ------------------------------------------------------------------
    # Noah Boddy right-bank search and upper-spinner build
    # ------------------------------------------------------------------

    def _upper_target_hit(self, target=None, **kwargs):
        if self._inactive() or self.right_bank_resetting or self.noah_revealed:
            return
        standing = self._standing_right_targets()
        if len(standing) <= 1:
            self._reveal_noah_if_ready()
            return

        target_to_drop = random.choice(standing)
        self._drop_right_programmatically(target_to_drop)
        self.machine.events.post(
            f"{self.MODE_KEY}_false_location_eliminated",
            target=target_to_drop,
            remaining=len(self._standing_right_targets()),
        )
        self._show_message("NOAH SEARCH", f"{len(self._standing_right_targets())} LOCATIONS LEFT")
        self._reveal_noah_if_ready()
        self._sync_vars()
        self._update_status()

    def _drop_right_programmatically(self, target):
        if target in self.right_down:
            return
        self.right_down.add(target)
        self.programmatic_right_pending.add(target)
        self.delay.reset(
            name=f"{self.MODE_KEY}_programmatic_right_{target}",
            ms=self.RIGHT_DROP_PENDING_MS,
            callback=self._clear_programmatic_right_pending,
            target=target,
        )
        self.machine.events.post(f"{self.MODE_KEY}_drop_right_target_{target}")
        self._refresh_noah_lights()

    def _clear_programmatic_right_pending(self, target=None, **kwargs):
        if target is not None:
            self.programmatic_right_pending.discard(int(target))

    def _right_drop_hit(self, target=None, **kwargs):
        if self._inactive() or self.right_bank_resetting or target is None:
            return
        target = int(target)
        if target in self.programmatic_right_pending:
            self.programmatic_right_pending.discard(target)
            self.delay.remove(f"{self.MODE_KEY}_programmatic_right_{target}")
            return
        if target in self.right_down:
            return

        if self.noah_revealed and target in self._standing_right_targets():
            self.right_down.add(target)
            self._collect_noah_jackpot(target)
            return

        self.right_down.add(target)
        self.machine.events.post(
            f"{self.MODE_KEY}_lower_false_location_eliminated",
            target=target,
            remaining=len(self._standing_right_targets()),
        )
        self._show_message("FALSE LOCATION", f"{len(self._standing_right_targets())} LOCATIONS LEFT")
        self._refresh_noah_lights()
        self._reveal_noah_if_ready()
        self._sync_vars()
        self._update_status()

    def _right_bank_complete(self, **kwargs):
        if self._inactive() or self.right_bank_resetting:
            return
        # A normal cycle should collect Noah on the fifth target. If an unusual
        # switch order reaches bank-down first, collect the current built value
        # and rebuild the bank rather than leaving the mode stuck.
        if self.noah_revealed:
            self._collect_noah_jackpot(target=0)
        else:
            self._reset_noah_round()

    def _reveal_noah_if_ready(self):
        standing = self._standing_right_targets()
        if self.noah_revealed or len(standing) != 1:
            return
        self.noah_revealed = True
        noah_target = standing[0]
        self._set_gate(False)
        self.machine.events.post(f"{self.MODE_KEY}_noah_revealed", target=noah_target)
        self._show_message("NOAH REVEALED", f"HIT RIGHT TARGET {noah_target}")
        self._refresh_noah_lights()

    def _upper_spinner_hit(self, **kwargs):
        if self._inactive():
            return
        self.noah_spinner_spins += 1
        value = self._noah_unmultiplied_value()
        self.machine.events.post(
            f"{self.MODE_KEY}_noah_jackpot_increased",
            spins=self.noah_spinner_spins,
            value=value,
        )
        self._show_message("NOAH JACKPOT BUILDS", "UPPER SPINNER", value)
        self._sync_vars()
        self._update_status()

    def _collect_noah_jackpot(self, target=None):
        if self._inactive():
            return
        multiplier = 1 + min(len(self.parked_saucers), self.MAX_PARKED_BALLS)
        value = self._noah_unmultiplied_value() * multiplier
        self.noah_jackpots += 1
        self._score(value)
        self.machine.events.post(
            f"{self.MODE_KEY}_noah_jackpot_collected",
            target=target,
            value=value,
            multiplier=multiplier,
        )
        self._show_jackpot("NOAH BODDY JACKPOT", value, f"{multiplier}X CONTAINMENT")
        self._release_all_parked_saucers()
        self._reset_noah_round()
        self._sync_vars()
        self._update_status()

    def _reset_noah_round(self):
        self.noah_revealed = False
        self.noah_spinner_spins = 0
        self.right_down.clear()
        self.programmatic_right_pending.clear()
        for target in self.RIGHT_DROPS:
            self.delay.remove(f"{self.MODE_KEY}_programmatic_right_{target}")
        self.right_bank_resetting = True
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self._schedule_bank_reset_finished("right")
        if self._active_gas_count():
            self._set_gate(False)
        else:
            self._set_gate(True)
        self._refresh_noah_lights()

    def _standing_right_targets(self):
        return [target for target in self.RIGHT_DROPS if target not in self.right_down]

    def _noah_unmultiplied_value(self):
        return self.NOAH_BASE_JACKPOT + self.case_file_bonus + (
            self.noah_spinner_spins * self.NOAH_SPINNER_STEP
        )

    # ------------------------------------------------------------------
    # Magneto A/B and center-web Add-a-Ball
    # ------------------------------------------------------------------

    def _a_hit(self, **kwargs):
        self._magneto_letter_hit("a")

    def _b_hit(self, **kwargs):
        self._magneto_letter_hit("b")

    def _magneto_letter_hit(self, letter):
        if self._inactive() or self.magneto_ready:
            return
        if letter == "a":
            self.a_collected = True
        elif letter == "b":
            self.b_collected = True
        else:
            return

        if self.a_collected and self.b_collected:
            self._qualify_magneto_award()
        else:
            self._show_message("MAGNETO CIRCUIT", f"{letter.upper()} COMPLETE")
            self._refresh_magneto_lights()
            self._sync_vars()

    def _qualify_magneto_award(self):
        self.magneto_ready = True
        self.magneto_seconds_left = self.MAGNETO_SECONDS
        self.machine.events.post(f"{self.MODE_KEY}_magneto_ready")
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title="MAGNETO ADD-A-BALL",
            message_mode_subtitle="CENTER WEB: ADD-A-BALL OR 1M",
            message_mode_value="",
            message_mode_seconds=self.magneto_seconds_left,
        )
        self._refresh_magneto_lights()
        self._schedule_magneto_tick()
        self._sync_vars()

    def _schedule_magneto_tick(self):
        if self.magneto_ready:
            self.delay.reset(
                name=f"{self.MODE_KEY}_magneto_tick",
                ms=1_000,
                callback=self._magneto_tick,
            )

    def _magneto_tick(self):
        if self._inactive() or not self.magneto_ready:
            return
        self.magneto_seconds_left -= 1
        if self.magneto_seconds_left <= 0:
            self.machine.events.post(f"{self.MODE_KEY}_magneto_expired")
            self._show_message("MAGNETO EXPIRED", "COMPLETE A + B AGAIN")
            self._reset_magneto()
            return
        self.machine.events.post(
            "update_mode_timer_status",
            mode_status_title="MAGNETO ADD-A-BALL",
            mode_status_value=self.magneto_seconds_left,
        )
        self._schedule_magneto_tick()
        self._sync_vars()

    def _center_web_hit(self, **kwargs):
        if self._inactive() or not self.magneto_ready:
            return
        self.delay.remove(f"{self.MODE_KEY}_magneto_tick")
        if self._balls_in_play() < self.MAX_BALLS:
            self.machine.events.post(f"{self.MODE_KEY}_add_a_ball")
            self.machine.events.post(f"{self.MODE_KEY}_magneto_add_a_ball_collected")
            self._show_message("ADD-A-BALL", "MAGNETO CIRCUIT COMPLETE")
        else:
            self._score(1_000_000)
            self.machine.events.post(f"{self.MODE_KEY}_magneto_points_collected", value=1_000_000)
            self._show_message("MAGNETO BONUS", "FOUR BALLS ACTIVE", 1_000_000)
        self._reset_magneto()

    def _reset_magneto(self):
        self.delay.remove(f"{self.MODE_KEY}_magneto_tick")
        self.a_collected = False
        self.b_collected = False
        self.magneto_ready = False
        self.magneto_seconds_left = 0
        self.machine.events.post("hide_mode_status")
        self.machine.events.post(f"{self.MODE_KEY}_magneto_reset")
        self._refresh_magneto_lights()
        self._refresh_gas_light("center_web")
        self._sync_vars()
        self._update_status()

    # ------------------------------------------------------------------
    # Saucer containment and lifecycle
    # ------------------------------------------------------------------

    def _saucer_hit(self, saucer=None, **kwargs):
        if saucer is None:
            return
        saucer = int(saucer)
        if self._inactive():
            self._kick_saucer(saucer)
            return
        if saucer in self.parked_saucers:
            return

        if self._can_park_current_saucer():
            self.parked_saucers.add(saucer)
            multiplier = 1 + len(self.parked_saucers)
            self.machine.events.post(
                f"{self.MODE_KEY}_saucer_parked",
                saucer=saucer,
                parked=len(self.parked_saucers),
                multiplier=multiplier,
            )
            self._show_message("OIL CONTAINED", f"NOAH JACKPOT {multiplier}X")
        else:
            self._kick_saucer(saucer)
        self._refresh_saucer_lights()
        self._sync_vars()
        self._update_status()

    def _can_park_current_saucer(self):
        if len(self.parked_saucers) >= self.MAX_PARKED_BALLS:
            return False
        return (self._balls_in_play() - len(self.parked_saucers) - 1) >= 1

    def _schedule_ball_guard(self):
        if not self.mode_done:
            self.delay.reset(
                name=f"{self.MODE_KEY}_ball_guard",
                ms=250,
                callback=self._ball_guard,
            )

    def _ball_guard(self):
        if self.mode_done:
            return
        if self.parked_saucers and self._playable_loose_balls() <= 0:
            saucer = sorted(self.parked_saucers)[0]
            self._kick_saucer(saucer, delay_ms=0)
            self.machine.events.post(f"{self.MODE_KEY}_deadlock_release", saucer=saucer)
            self._refresh_saucer_lights()
            self._sync_vars()
        self._schedule_ball_guard()

    def _release_all_parked_saucers(self):
        for index, saucer in enumerate(sorted(self.parked_saucers)):
            self._kick_saucer(saucer, delay_ms=index * 250)
        self.parked_saucers.clear()
        self._refresh_saucer_lights()

    def _kick_saucer(self, saucer, delay_ms=None):
        saucer = int(saucer)
        self.parked_saucers.discard(saucer)
        if delay_ms is None:
            delay_ms = 0
        self.machine.events.post(
            "request_saucer_eject",
            saucer_number=saucer,
            delay_ms=max(0, int(delay_ms)),
        )

    def _playable_loose_balls(self):
        return max(0, self._balls_in_play() - len(self.parked_saucers))

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        try:
            return int(self.machine.game.balls_in_play)
        except (TypeError, ValueError, AttributeError):
            return 0

    def _vuk_hit(self, **kwargs):
        if not self._inactive():
            self.machine.events.post("request_vuk_eject", delay_ms=self.VUK_EJECT_MS)

    # ------------------------------------------------------------------
    # Gate, lights, display and completion
    # ------------------------------------------------------------------

    def _set_gate(self, opened):
        opened = bool(opened)
        self.gate_open = opened
        if opened:
            self.machine.events.post("rooftop_diverter_open")
            self.machine.events.post(f"{self.MODE_KEY}_vuk_chase_start")
        else:
            self.machine.events.post("rooftop_diverter_close")
            self.machine.events.post(f"{self.MODE_KEY}_vuk_chase_stop")

    def _schedule_bank_reset_finished(self, bank):
        self.delay.reset(
            name=f"{self.MODE_KEY}_{bank}_bank_reset",
            ms=self.BANK_RESET_MS,
            callback=self._bank_reset_finished,
            bank=bank,
        )

    def _bank_reset_finished(self, bank=None, **kwargs):
        if bank == "left":
            self.left_bank_resetting = False
        elif bank == "right":
            self.right_bank_resetting = False
            self._refresh_noah_lights()

    def _refresh_all_gas_lights(self):
        for zone in self.GAS_ZONES:
            self._refresh_gas_light(zone)

    def _refresh_gas_light(self, zone):
        self.machine.events.post(f"{self.MODE_KEY}_gas_{zone}_clear")
        level = self.gas_states.get(zone, 0)
        if level:
            color = self.GAS_COLORS[level]
            self.machine.events.post(f"{self.MODE_KEY}_gas_{zone}_{color}")

    def _refresh_noah_lights(self):
        self.machine.events.post(f"{self.MODE_KEY}_noah_lights_clear")
        if self.right_bank_resetting:
            return
        standing = self._standing_right_targets()
        for target in standing:
            if self.noah_revealed and len(standing) == 1:
                self.machine.events.post(f"{self.MODE_KEY}_noah_target_{target}")
            else:
                self.machine.events.post(f"{self.MODE_KEY}_right_target_{target}_standing")
        if not self.noah_revealed:
            self.machine.events.post(f"{self.MODE_KEY}_upper_targets_ready")

    def _refresh_magneto_lights(self):
        self.machine.events.post(f"{self.MODE_KEY}_magneto_lights_clear")
        if self.magneto_ready:
            self.machine.events.post(f"{self.MODE_KEY}_center_web_ready")
            return
        if self.a_collected:
            self.machine.events.post(f"{self.MODE_KEY}_a_collected")
        else:
            self.machine.events.post(f"{self.MODE_KEY}_a_ready")
        if self.b_collected:
            self.machine.events.post(f"{self.MODE_KEY}_b_collected")
        else:
            self.machine.events.post(f"{self.MODE_KEY}_b_ready")

    def _refresh_saucer_lights(self):
        self.machine.events.post(f"{self.MODE_KEY}_saucer_lights_clear")
        for saucer in self.parked_saucers:
            self.machine.events.post(f"{self.MODE_KEY}_saucer_{saucer}_parked_light")

    def _active_gas_count(self):
        return sum(1 for level in self.gas_states.values() if level > 0)

    def _update_status(self):
        if self.magneto_ready:
            return
        red = sum(1 for level in self.gas_states.values() if level == self.GAS_LEVELS["red"])
        yellow = sum(1 for level in self.gas_states.values() if level == self.GAS_LEVELS["yellow"])
        green = sum(1 for level in self.gas_states.values() if level == self.GAS_LEVELS["green"])
        multiplier = 1 + min(len(self.parked_saucers), self.MAX_PARKED_BALLS)
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="GAS R/Y/G - NOAH JP",
            mode_status_value=f"{red}/{yellow}/{green} - {self._noah_multiplied_value(multiplier):,}",
        )

    def _noah_multiplied_value(self, multiplier=None):
        if multiplier is None:
            multiplier = 1 + min(len(self.parked_saucers), self.MAX_PARKED_BALLS)
        return self._noah_unmultiplied_value() * multiplier

    def _show_message(self, title, subtitle="", value="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            reminder=reminder,
        )

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
        )
        self.machine.events.post("play_mode_jackpot")
        self.machine.events.post("reset_mode_message_reminder")

    def _score(self, points):
        points = self._safe_int(points, 0)
        if points <= 0 or not self.machine.game:
            return
        self.machine.game.player["score"] += points
        self.mode_points += points
        self._set("active_mode_points", self.mode_points)

    def _sync_vars(self):
        red = sum(1 for level in self.gas_states.values() if level == self.GAS_LEVELS["red"])
        yellow = sum(1 for level in self.gas_states.values() if level == self.GAS_LEVELS["yellow"])
        green = sum(1 for level in self.gas_states.values() if level == self.GAS_LEVELS["green"])
        self._set("active_mode_points", self.mode_points)
        self._set("active_mode_hits", self.gas_jackpots + self.noah_jackpots)
        self._set("active_mode_major_hits", self.noah_jackpots)
        self._set(f"{self.MODE_KEY}_case_file_bonus", self.case_file_bonus)
        self._set(f"{self.MODE_KEY}_jackpot_value", self._noah_unmultiplied_value())
        self._set(f"{self.MODE_KEY}_gas_jackpots", self.gas_jackpots)
        self._set(f"{self.MODE_KEY}_noah_jackpots", self.noah_jackpots)
        self._set(f"{self.MODE_KEY}_active_gas_zones", self._active_gas_count())
        self._set(f"{self.MODE_KEY}_gas_red", red)
        self._set(f"{self.MODE_KEY}_gas_yellow", yellow)
        self._set(f"{self.MODE_KEY}_gas_green", green)
        self._set(f"{self.MODE_KEY}_parked_balls", len(self.parked_saucers))
        self._set(f"{self.MODE_KEY}_magneto_seconds", self.magneto_seconds_left)

    def _multiball_ended(self, **kwargs):
        self._complete_mode()

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.mode_exiting = True
        self.delay.clear()
        self._set(f"{self.MODE_KEY}_state", 2)
        self._sync_vars()
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.machine.events.post(f"{self.MODE_KEY}_clear_all_lights")
        self.machine.events.post(f"{self.MODE_KEY}_vuk_chase_stop")
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")

    def _inactive(self):
        return self.mode_done or self.mode_exiting or not self.machine.game

    def _get(self, key, default=0):
        if not self.machine.game:
            return default
        try:
            return self.machine.game.player[key]
        except (KeyError, TypeError):
            return default

    def _set(self, key, value):
        if self.machine.game:
            self.machine.game.player[key] = value

    @staticmethod
    def _safe_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
