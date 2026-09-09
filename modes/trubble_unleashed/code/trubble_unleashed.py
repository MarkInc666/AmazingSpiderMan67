from mpf.core.delays import DelayManager
from mpf.core.mode import Mode


class TrubbleUnleashed(Mode):
    """Chapter 3 wizard: repeatable scoring multiball until the main MB ends."""

    MODE_KEY = "trubble_unleashed"
    DISPLAY_NAME = "Trubble Unleashed"

    BASIC_DROP_SCORE = 25_000
    UPPER_TARGET_SCORE = 50_000
    UNLIT_SAUCER_SCORE = 25_000

    DIANA_BASE_JACKPOT = 1_000_000
    CERBERUS_BASE_JACKPOT = 1_000_000
    CENTAUR_BASE_JACKPOT = 500_000
    CENTAUR_SPINNER_STEP = 100_000
    CYCLOPS_JACKPOT = 1_000_000

    DIANA_FLIPS = 5
    CENTAUR_SECONDS = 5
    CYCLOPS_SECONDS = 10
    MAX_BALLS = 4
    SAUCER_EJECT_MS = 750
    RIGHT_BANK_STAGE_DELAY_MS = 500

    ALL_RIGHT_DROPS = (1, 2, 3, 4, 5)
    ALL_LEFT_DROPS = (1, 2, 3)
    SAUCER_BY_TARGET = {"left": 1, "center": 2, "right": 3}
    DIANA_TARGETS = {
        5: (1, 2, 3, 4, 5),
        4: (1, 2, 4, 5),
        3: (1, 3, 5),
        2: (2, 4),
        1: (3,),
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.delay = DelayManager(self.machine)
        self.mode_done = False
        self.mode_exiting = False
        self.mode_points = 0

        self.case_file_bonus = int(self._get("mini_wizard_case_file_bonus", 0) or 0)
        self.left_down = set()
        self.right_down = set()
        self.ignored_auto_right = set()
        self.preserve_right_bank_down = False
        self.parked_saucers = set()

        self.gate_open = False
        self.phase = None  # None, diana, centaur

        self.upper_targets_hit = set()
        self.lit_saucers = set()
        self.add_a_ball_qualified = False
        self.add_a_balls_awarded = 0

        self.diana_spin_value = 1
        self.diana_flips_left = 0
        self.diana_staged = False
        self.diana_targets = set()

        self.centaur_spinner_spins = 0
        self.upper_post_active = False
        self.centaur_staged = False
        self.centaur_timer_active = False
        self.centaur_seconds_left = 0

        self.cyclops_lit = False
        self.cyclops_seconds_left = 0

        self.diana_jackpots = 0
        self.centaur_jackpots = 0
        self.cerberus_jackpots = 0
        self.cyclops_jackpots = 0

        self._set("trubble_unleashed_state", 1)
        self._sync_vars()

        for target in self.ALL_LEFT_DROPS:
            self.add_mode_event_handler(
                f"trubble_unleashed_left_drop_{target}_hit", self._left_drop_hit, target=target
            )
        for target in self.ALL_RIGHT_DROPS:
            self.add_mode_event_handler(
                f"trubble_unleashed_right_drop_{target}_hit", self._right_drop_hit, target=target
            )
        for name in self.SAUCER_BY_TARGET:
            self.add_mode_event_handler(
                f"trubble_unleashed_upper_target_{name}_hit", self._upper_target_hit, target_name=name
            )
        for saucer in (1, 2, 3):
            self.add_mode_event_handler(
                f"trubble_unleashed_saucer_{saucer}_hit", self._saucer_hit, saucer=saucer
            )

        self.add_mode_event_handler("trubble_unleashed_left_bank_complete", self._left_bank_complete)
        self.add_mode_event_handler("trubble_unleashed_right_bank_complete", self._right_bank_complete)
        self.add_mode_event_handler("trubble_unleashed_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("trubble_unleashed_upper_spinner_hit", self._upper_spinner_hit)
        self.add_mode_event_handler("trubble_unleashed_upper_exit_left", self._upper_exit_left)
        self.add_mode_event_handler("trubble_unleashed_upper_exit_right", self._upper_exit_right)
        self.add_mode_event_handler("trubble_unleashed_centaur_rubber_hit", self._centaur_rubber_hit)
        self.add_mode_event_handler("trubble_unleashed_cyclops_hit", self._cyclops_hit)
        self.add_mode_event_handler("trubble_unleashed_flipper", self._flipper_hit)
        self.add_mode_event_handler("trubble_unleashed_post_hold_cancel", self._cancel_upper_post)
        self.add_mode_event_handler("trubble_unleashed_upper_playfield_entered", self._upper_playfield_entered)
        self.add_mode_event_handler("timer_timer_up_post_hold_complete", self._post_dropped)
        self.add_mode_event_handler("trubble_unleashed_multiball_ended", self._multiball_ended)

        self.machine.events.post("trubble_unleashed_setup")
        self.machine.events.post("trubble_unleashed_start_multiball")
        self._set_gate(False)
        self._update_upper_target_lights()
        self._update_saucer_lights()
        self._show_message("TRUBBLE UNLEASHED", "LEFT DROPS OPEN THE ROOF", reminder=True)
        self._schedule_ball_guard()

    def mode_stop(self, **kwargs):
        self.mode_exiting = True
        self.delay.clear()
        if self.upper_post_active:
            self.machine.events.post("drop_the_up_post")
            self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("trubble_unleashed_clear_all_lights")
        self.machine.events.post("trubble_unleashed_vuk_chase_stop")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("clear_saucers")
        self.machine.events.post("cancel_mode_message_reminder")
        super().mode_stop(**kwargs)

    # ------------------------------------------------------------------
    # Gate / phase qualification
    # ------------------------------------------------------------------

    def _left_drop_hit(self, target=None, **kwargs):
        if self._inactive():
            return
        self.left_down.add(int(target))
        self._score(self.BASIC_DROP_SCORE)
        self.machine.events.post("trubble_unleashed_left_drop_scored", target=target, value=self.BASIC_DROP_SCORE)
        self._set_gate(True)
        self._sync_vars()

    def _left_bank_complete(self, **kwargs):
        if self._inactive():
            return
        # Keep the completed bank down until the next VUK entry. All three down
        # is how the VUK selects Centaur instead of Diana.
        self.left_down.update(self.ALL_LEFT_DROPS)
        self._set_gate(True)

    def _set_gate(self, opened):
        opened = bool(opened)
        self.gate_open = opened
        if opened:
            self.machine.events.post("rooftop_diverter_open")
            self.machine.events.post("trubble_unleashed_gate_open_state")
            self.machine.events.post("trubble_unleashed_vuk_chase_start")
        else:
            self.machine.events.post("rooftop_diverter_close")
            self.machine.events.post("trubble_unleashed_gate_closed_state")
            self.machine.events.post("trubble_unleashed_vuk_chase_stop")

    def _vuk_hit(self, **kwargs):
        if self._inactive():
            return
        self._set_gate(False)

        if self.phase is None:
            if len(self.left_down) == 3:
                self._start_centaur()
            else:
                self._start_diana()
            self.left_down.clear()
            self.machine.events.post("drop_target_bank_dt_bank_left_reset")

        # VUK entry chooses/feeds the active rooftop phase; it is not the Add-a-Ball collect.
        self.machine.events.post("request_vuk_eject", delay_ms=1_000)

    # ------------------------------------------------------------------
    # Diana
    # ------------------------------------------------------------------

    def _start_diana(self):
        self._end_phase_visuals()
        self.phase = "diana"
        self.diana_spin_value = 1
        self.diana_flips_left = 0
        self.diana_staged = False
        self.diana_targets.clear()
        self.preserve_right_bank_down = False
        self.right_down.clear()
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("trubble_unleashed_right_bank_phase_start")
        self.machine.events.post("trubble_unleashed_diana_all_up")
        self._show_status("DIANA SPIN", self.diana_spin_value)
        self._sync_vars()

    def _stage_diana(self):
        if self.phase != "diana" or self.diana_staged:
            return
        self.diana_staged = True
        self.diana_flips_left = self.DIANA_FLIPS
        self.diana_targets = set(self.DIANA_TARGETS[self.diana_spin_value])
        self.ignored_auto_right.clear()
        self.right_down.clear()
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.machine.events.post("trubble_unleashed_diana_stage_clear")
        self.delay.reset(
            name="trubble_diana_stage",
            ms=self.RIGHT_BANK_STAGE_DELAY_MS,
            callback=self._drop_diana_non_targets,
        )
        self._show_status("DIANA FLIPS", self.diana_flips_left)
        self._sync_vars()

    def _drop_diana_non_targets(self):
        if self._inactive() or self.phase != "diana" or not self.diana_staged:
            return
        for target in self.ALL_RIGHT_DROPS:
            if target not in self.diana_targets:
                self._auto_drop_right_target(target)
        self._update_diana_target_lights()

    def _flipper_hit(self, **kwargs):
        if self._inactive() or self.phase != "diana" or not self.diana_staged:
            return
        if self.diana_flips_left <= 0:
            return
        self.diana_flips_left -= 1
        self._show_status("DIANA FLIPS", self.diana_flips_left)
        self._sync_vars()
        if self.diana_flips_left <= 0:
            self._finish_diana_miss()

    def _collect_diana(self, target):
        self.machine.events.post("hide_mode_status")
        value = self.DIANA_BASE_JACKPOT + self.case_file_bonus
        self.diana_jackpots += 1
        self._score(value)
        self.machine.events.post("trubble_unleashed_diana_jackpot", target=target, value=value)
        self._show_jackpot("DIANA JACKPOT", value, f"DROP {target}")
        self._light_cyclops()
        self.preserve_right_bank_down = True
        for remaining in sorted(self.diana_targets):
            if remaining != target and remaining not in self.right_down:
                self._auto_drop_right_target(remaining)
        self._finish_phase(reset_right_bank=False)

    def _finish_diana_miss(self):
        for target in sorted(self.diana_targets):
            if target not in self.right_down:
                self._auto_drop_right_target(target)
        self._show_message("DIANA ESCAPES", "OUT OF FLIPS")
        self._finish_phase(reset_right_bank=True)

    # ------------------------------------------------------------------
    # Centaur
    # ------------------------------------------------------------------

    def _start_centaur(self):
        self._end_phase_visuals()
        self.phase = "centaur"
        self.centaur_spinner_spins = 0
        self.upper_post_active = False
        self.centaur_staged = False
        self.centaur_timer_active = False
        self.centaur_seconds_left = 0
        self.preserve_right_bank_down = False
        self.machine.events.post("trubble_unleashed_right_bank_phase_start")
        self.machine.events.post("trubble_unleashed_centaur_targets")
        self._stage_centaur_drops()
        self._show_status("CENTAUR JACKPOT", self._centaur_value())
        self._sync_vars()

    def _upper_spinner_hit(self, **kwargs):
        if self._inactive():
            return
        if self.phase == "diana" and not self.diana_staged:
            self.diana_spin_value += 1
            if self.diana_spin_value > 5:
                self.diana_spin_value = 1
            self._show_status("DIANA SPIN", self.diana_spin_value)
            self._sync_vars()
            return
        if self.phase == "centaur" and not self.centaur_timer_active:
            self.centaur_spinner_spins += 1
            value = self._centaur_value()
            self.machine.events.post("trubble_unleashed_centaur_spinner", spins=self.centaur_spinner_spins, value=value)
            self._show_status("CENTAUR JACKPOT", value)
            self._sync_vars()

    def _centaur_value(self):
        return self.CENTAUR_BASE_JACKPOT + self.case_file_bonus + (
            self.centaur_spinner_spins * self.CENTAUR_SPINNER_STEP
        )

    def _start_centaur_post(self):
        if self.phase != "centaur" or self.upper_post_active or self.centaur_timer_active:
            return
        self.upper_post_active = True
        self.machine.events.post("enable_up_post_event")
        self._show_message("CENTAUR", "POST UP - READY THE RUBBER")
        self._sync_vars()

    def _post_dropped(self, **kwargs):
        if self._inactive() or not self.upper_post_active:
            return
        self.upper_post_active = False
        if self.phase != "centaur":
            self._sync_vars()
            return
        self.centaur_timer_active = True
        self.centaur_seconds_left = self.CENTAUR_SECONDS
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title="CENTAUR",
            message_mode_subtitle="HIT RIGHT RUBBER",
            message_mode_value=self._centaur_value(),
            message_mode_seconds=self.centaur_seconds_left,
        )
        self._schedule_centaur_tick()
        self._sync_vars()

    def _cancel_upper_post(self, **kwargs):
        if self._inactive() or not self.upper_post_active:
            return
        self.machine.events.post("drop_the_up_post")
        self.machine.events.post("timer_timer_up_post_hold_complete")

    def _stage_centaur_drops(self):
        if self._inactive() or self.phase != "centaur":
            return
        self.centaur_staged = True
        self.ignored_auto_right.clear()
        self.right_down.clear()
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        self.delay.reset(
            name="trubble_centaur_stage",
            ms=self.RIGHT_BANK_STAGE_DELAY_MS,
            callback=self._drop_centaur_non_targets,
        )

    def _drop_centaur_non_targets(self):
        if self._inactive() or self.phase != "centaur" or not self.centaur_staged:
            return
        # Leave the two outside targets standing to frame the Centaur rubber.
        # The three center inserts remain lit to identify the rubber shot.
        for target in (2, 3, 4):
            self._auto_drop_right_target(target)

    def _schedule_centaur_tick(self):
        if self.centaur_timer_active:
            self.delay.reset(name="trubble_centaur_tick", ms=1000, callback=self._centaur_tick)

    def _centaur_tick(self):
        if self._inactive() or not self.centaur_timer_active:
            return
        self.centaur_seconds_left -= 1
        self.machine.events.post(
            "update_mode_timer_status",
            mode_status_title="CENTAUR",
            mode_status_value=max(0, self.centaur_seconds_left),
        )
        self._sync_vars()
        if self.centaur_seconds_left <= 0:
            self.centaur_timer_active = False
            self._show_message("CENTAUR ESCAPES", "RUBBER MISSED")
            self._finish_phase(reset_right_bank=True)
            return
        self._schedule_centaur_tick()

    def _centaur_rubber_hit(self, **kwargs):
        if self._inactive() or self.phase != "centaur" or not self.centaur_timer_active:
            return
        self.centaur_timer_active = False
        self.delay.remove("trubble_centaur_tick")
        self.machine.events.post("hide_mode_status")
        value = self._centaur_value()
        self.centaur_jackpots += 1
        self._score(value)
        self.machine.events.post("trubble_unleashed_centaur_jackpot", value=value)
        self._show_jackpot("CENTAUR JACKPOT", value, "RIGHT RUBBER")
        self._light_cyclops()
        self.preserve_right_bank_down = True
        for target in self.ALL_RIGHT_DROPS:
            if target not in self.right_down:
                self._auto_drop_right_target(target)
        self._finish_phase(reset_right_bank=False)

    # ------------------------------------------------------------------
    # Shared right-bank / upper-exit handling
    # ------------------------------------------------------------------

    def _right_drop_hit(self, target=None, **kwargs):
        if self._inactive():
            return
        target = int(target)
        if target in self.ignored_auto_right:
            self.ignored_auto_right.discard(target)
            self.right_down.add(target)
            return

        self.right_down.add(target)
        if self.phase == "diana" and self.diana_staged and target in self.diana_targets:
            self._collect_diana(target)
            return

        self._score(self.BASIC_DROP_SCORE)
        self.machine.events.post("trubble_unleashed_right_drop_basic", target=target, value=self.BASIC_DROP_SCORE)
        if self.phase == "diana" and not self.diana_staged:
            self._update_diana_pre_stage_lights()
        self._sync_vars()

    def _right_bank_complete(self, **kwargs):
        if self._inactive():
            return
        if self.preserve_right_bank_down:
            return
        if (self.phase == "diana" and self.diana_staged) or self.phase == "centaur":
            return
        self.right_down.clear()
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        if self.phase == "diana":
            self.machine.events.post("trubble_unleashed_diana_all_up")

    def _upper_exit_left(self, **kwargs):
        if self._inactive():
            return
        if self.phase == "diana":
            self._stage_diana()
            if not self.upper_post_active:
                self.upper_post_active = True
                self.machine.events.post("enable_up_post_event")
        elif self.phase == "centaur":
            self._start_centaur_post()

    def _upper_playfield_entered(self, **kwargs):
        if self._inactive():
            return
        self.preserve_right_bank_down = False
        self.ignored_auto_right.clear()
        if self.phase == "centaur":
            self.centaur_staged = False
            self._stage_centaur_drops()
            return
        self.right_down.clear()
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")
        if self.phase == "diana":
            self.machine.events.post("trubble_unleashed_diana_all_up")

    def _upper_exit_right(self, **kwargs):
        if self._inactive() or not self.add_a_ball_qualified:
            return
        if self._balls_in_play() >= self.MAX_BALLS:
            self._show_message("ADD-A-BALL READY", "MAX 4 BALLS IN PLAY")
            return
        self.add_a_ball_qualified = False
        self.add_a_balls_awarded += 1
        self.machine.events.post("trubble_unleashed_add_a_ball")
        self.machine.events.post("trubble_unleashed_add_a_ball_awarded")
        self.machine.events.post("show_mode_message", message_mode_title="ADD-A-BALL", message_mode_subtitle="VULCAN")
        self.upper_targets_hit.clear()
        self._update_upper_target_lights()
        self._sync_vars()

    # ------------------------------------------------------------------
    # Cerberus + Vulcan upper-target systems
    # ------------------------------------------------------------------

    def _upper_target_hit(self, target_name=None, **kwargs):
        if self._inactive():
            return
        saucer = self.SAUCER_BY_TARGET[target_name]
        self.upper_targets_hit.add(target_name)
        self.lit_saucers.add(saucer)
        self._score(self.UPPER_TARGET_SCORE)
        self.machine.events.post("trubble_unleashed_saucer_lit", saucer=saucer, value=self._cerberus_value())
        if len(self.upper_targets_hit) == 3:
            self.add_a_ball_qualified = True
            self.machine.events.post("trubble_unleashed_add_a_ball_qualified")
            self._show_message("VULCAN ADD-A-BALL", "SHOOT RIGHT UPPER EXIT")
        self._update_upper_target_lights()
        self._update_saucer_lights()
        self._sync_vars()

    def _cerberus_value(self):
        return self.CERBERUS_BASE_JACKPOT + self.case_file_bonus

    def _saucer_hit(self, saucer=None, **kwargs):
        if self._inactive():
            self._kick_saucer(saucer)
            return
        saucer = int(saucer)
        if saucer in self.lit_saucers:
            self.lit_saucers.discard(saucer)
            value = self._cerberus_value()
            self.cerberus_jackpots += 1
            self._score(value)
            self.machine.events.post("trubble_unleashed_cerberus_jackpot", saucer=saucer, value=value)
            self._show_jackpot("CERBERUS JACKPOT", value, f"SAUCER {saucer}")
            self._light_cyclops()
            self._update_saucer_lights()
            if self._can_park_current_saucer():
                self.parked_saucers.add(saucer)
                self.machine.events.post("trubble_unleashed_saucer_parked", saucer=saucer)
            else:
                self._kick_saucer(saucer)
        else:
            self._score(self.UNLIT_SAUCER_SCORE)
            self.machine.events.post("trubble_unleashed_unlit_saucer", saucer=saucer)
            self._kick_saucer(saucer)
        self._sync_vars()

    # ------------------------------------------------------------------
    # Cyclops overlay
    # ------------------------------------------------------------------

    def _light_cyclops(self):
        self.cyclops_lit = True
        self.cyclops_seconds_left = self.CYCLOPS_SECONDS
        self.machine.events.post("trubble_unleashed_cyclops_lit")
        self.machine.events.post(
            "show_mode_countdown",
            message_mode_title="CYCLOPS",
            message_mode_subtitle="HIT CENTER WEB",
            message_mode_value=self.CYCLOPS_JACKPOT,
            message_mode_seconds=self.cyclops_seconds_left,
        )
        self._schedule_cyclops_tick()
        self._sync_vars()

    def _schedule_cyclops_tick(self):
        if self.cyclops_lit:
            self.delay.reset(name="trubble_cyclops_tick", ms=1000, callback=self._cyclops_tick)

    def _cyclops_tick(self):
        if self._inactive() or not self.cyclops_lit:
            return
        self.cyclops_seconds_left -= 1
        if self.cyclops_seconds_left <= 0:
            self.cyclops_lit = False
            self.machine.events.post("trubble_unleashed_cyclops_unlit")
            self.machine.events.post("hide_mode_status")
            self._sync_vars()
            return
        self.machine.events.post(
            "update_mode_timer_status",
            mode_status_title="CYCLOPS",
            mode_status_value=self.cyclops_seconds_left,
        )
        self._schedule_cyclops_tick()
        self._sync_vars()

    def _cyclops_hit(self, **kwargs):
        if self._inactive() or not self.cyclops_lit:
            return
        self.cyclops_lit = False
        self.delay.remove("trubble_cyclops_tick")
        self.machine.events.post("hide_mode_status")
        self.cyclops_jackpots += 1
        self._score(self.CYCLOPS_JACKPOT)
        self.machine.events.post("trubble_unleashed_cyclops_collected", value=self.CYCLOPS_JACKPOT)
        self._show_jackpot("CYCLOPS JACKPOT", self.CYCLOPS_JACKPOT, "CENTER WEB")
        self.machine.events.post("trubble_unleashed_cyclops_unlit")
        self._release_one_parked_saucer()
        self._sync_vars()

    # ------------------------------------------------------------------
    # Ball parking / lifecycle
    # ------------------------------------------------------------------

    def _schedule_ball_guard(self):
        if not self.mode_done:
            self.delay.reset(name="trubble_ball_guard", ms=250, callback=self._ball_guard)

    def _ball_guard(self):
        if self.mode_done:
            return
        if self.parked_saucers and self._playable_loose_balls() <= 0:
            saucer = sorted(self.parked_saucers)[0]
            self.parked_saucers.remove(saucer)
            self._kick_saucer(saucer, delay_ms=0)
        self._schedule_ball_guard()

    def _can_park_current_saucer(self):
        # Current ball is already physically in the saucer but not yet in parked_saucers.
        return (self._balls_in_play() - len(self.parked_saucers) - 1) >= 1

    def _playable_loose_balls(self):
        return max(0, self._balls_in_play() - len(self.parked_saucers))

    def _release_one_parked_saucer(self):
        if not self.parked_saucers:
            return
        saucer = sorted(self.parked_saucers)[0]
        self._kick_saucer(saucer, delay_ms=0)
        self.machine.events.post("trubble_unleashed_cyclops_released_saucer", saucer=saucer)

    def _kick_saucer(self, saucer, delay_ms=None):
        self.parked_saucers.discard(int(saucer))
        event = {
            1: "delayed_kickout_saucer_1",
            2: "delayed_kickout_saucer_2",
            3: "delayed_kickout_saucer_3",
        }.get(int(saucer))
        if not event:
            return
        if delay_ms is None:
            self.machine.events.post(event)
        elif delay_ms <= 0:
            self.machine.events.post(event, delay_ms=0)
        else:
            self.machine.events.post(event, delay_ms=delay_ms)

    def _multiball_ended(self, **kwargs):
        if not self.mode_done:
            self._complete_mode()

    def _complete_mode(self):
        if self.mode_done:
            return
        self.mode_done = True
        self.mode_exiting = True
        self._set("trubble_unleashed_state", 2)
        self.delay.clear()
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("trubble_unleashed_clear_all_lights")
        self.machine.events.post("trubble_unleashed_vuk_chase_stop")
        self._sync_vars()
        self.machine.events.post("trubble_unleashed_mode_complete")

    # ------------------------------------------------------------------
    # Lighting / phase helpers
    # ------------------------------------------------------------------

    def _finish_phase(self, reset_right_bank=False):
        if self.upper_post_active:
            self.upper_post_active = False
            self.machine.events.post("drop_the_up_post")
            self.machine.events.post("timer_timer_up_post_hold_complete")
        self.phase = None
        self.diana_staged = False
        self.diana_flips_left = 0
        self.diana_targets.clear()
        self.centaur_staged = False
        self.centaur_timer_active = False
        self.delay.remove("trubble_centaur_tick")
        self.delay.remove("trubble_centaur_stage")
        self.delay.remove("trubble_diana_stage")
        self._end_phase_visuals()
        if reset_right_bank:
            self.delay.reset(
                name="trubble_reset_right_bank",
                ms=500,
                callback=self._reset_right_bank,
            )
        if not self.cyclops_lit:
            self.machine.events.post("hide_mode_status")
        self._sync_vars()

    def _end_phase_visuals(self):
        self.machine.events.post("trubble_unleashed_right_bank_phase_stop")
        self.machine.events.post("trubble_unleashed_diana_stage_clear")
        self.machine.events.post("trubble_unleashed_centaur_targets_clear")

    def _reset_right_bank(self):
        self.preserve_right_bank_down = False
        self.right_down.clear()
        self.machine.events.post("drop_target_bank_dt_bank_right_reset")

    def _auto_drop_right_target(self, target):
        target = int(target)
        self.ignored_auto_right.add(target)
        self.right_down.add(target)
        self.machine.events.post(f"trubble_unleashed_drop_right_target_{target}")

    def _update_diana_pre_stage_lights(self):
        if self.phase != "diana" or self.diana_staged:
            return
        self.machine.events.post("trubble_unleashed_diana_stage_clear")
        for target in self.ALL_RIGHT_DROPS:
            if target not in self.right_down:
                self.machine.events.post(f"trubble_unleashed_diana_drop_{target}_on")

    def _update_diana_target_lights(self):
        self.machine.events.post("trubble_unleashed_diana_stage_clear")
        for target in sorted(self.diana_targets):
            self.machine.events.post(f"trubble_unleashed_diana_drop_{target}_on")

    def _update_upper_target_lights(self):
        self.machine.events.post("trubble_unleashed_upper_targets_clear")
        for name in self.SAUCER_BY_TARGET:
            if name in self.upper_targets_hit:
                self.machine.events.post(f"trubble_unleashed_upper_{name}_solid")
            else:
                self.machine.events.post(f"trubble_unleashed_upper_{name}_pulse")

    def _update_saucer_lights(self):
        self.machine.events.post("trubble_unleashed_clear_saucer_lights")
        for saucer in sorted(self.lit_saucers):
            self.machine.events.post(f"trubble_unleashed_saucer_{saucer}_lit")

    # ------------------------------------------------------------------
    # Display / score / state
    # ------------------------------------------------------------------

    def _show_status(self, title, value):
        self.machine.events.post("update_mode_status", mode_status_title=title, mode_status_value=value)

    def _show_message(self, title, subtitle="", value="", reminder=False):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
            reminder=reminder,
        )

    def _show_jackpot(self, title, value, subtitle=""):
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds="",
        )
        if "SUPER" in str(title).upper():
            self.machine.events.post("play_mode_super_jackpot")
        else:
            self.machine.events.post("play_mode_jackpot")

    def _score(self, points):
        if not points:
            return
        player = self.machine.game.player
        player["score"] += int(points)
        self.mode_points += int(points)
        self._sync_vars()

    def _sync_vars(self):
        jackpots = self.diana_jackpots + self.centaur_jackpots + self.cerberus_jackpots + self.cyclops_jackpots
        self._set("active_mode_points", self.mode_points)
        self._set("active_mode_hits", jackpots)
        self._set("active_mode_major_hits", self.add_a_balls_awarded)
        self._set("trubble_unleashed_saucer_jackpots", self.cerberus_jackpots)

    def _inactive(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return True
        return self.mode_done or self.mode_exiting or player["villain_mode_in_summary"] is True

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return int(self.machine.game.balls_in_play or 0)

    def _get(self, name, default=0):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return default
        try:
            return player[name]
        except KeyError:
            return default

    def _set(self, name, value):
        player = self.machine.game.player if self.machine.game else None
        if player is not None:
            player[name] = value
