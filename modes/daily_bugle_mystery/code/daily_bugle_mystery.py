import random
from mpf.core.mode import Mode


class DailyBugleMystery(Mode):
    """Daily Bugle Mystery / Scoop mode.

    Flow:
      1. Complete A+B.
      2. Rooftop gate opens.
      3. Shoot VUK to the rooftop.
      4. Rooftop spinner takes photos. Three photos lights Mystery.
      5. Left exit can hold the ball on the pop-up post for JJJ instructions.
      6. Right exit only plays the same instruction/callout, without the post.
      7. VUK collects Mystery when ready.

    Important change from the older version:
      A/B/mystery progress is restored from player vars when the mode starts,
      so the state can survive ball drains.
    """

    AB_DAILY_POINTS = 10000
    AB_DAILY_POINTS_UNLIT = 2000

    PHOTOS_NEEDED = 3
    LEFT_EXIT_HOLD_MS = 8000

    # Daily Bugle should not take over the rooftop gate while one of
    # these villain modes owns upper/VUK/gate access.
    GATE_PROTECTED_VILLAIN_MODES = {
        "vulture",
        "lizard",
        "electro",
        "doc_ock",
        "mysterio",
        "scorpion",
        "parafino",
        "centaur",
        "cerberus",
        "swamp_reptiles",
        "noah_boddy",
        "vulcan",
        "fifth_avenue_phantom",
    }

    EXTRA_BALL_LIGHT_AT = 3
    EXTRA_BALL_AWARD_AT = 7
    EXTRA_BALL_RIGHT_LIGHT_AT = 10

    PLACEHOLDER_AWARDS = [
        "mystery_award_ball_save",
        "mystery_award_start_super_spinner",
        "mystery_award_advance_bonus_multiplier",
        "mystery_award_collect_bonus",
        "mystery_award_hold_bonus",
        "mystery_award_start_super_pops",
        "mystery_award_million_points",
        "mystery_award_villain_start_ready",
    ]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.daily_bugle_enabled = True
        self.left_exit_hold_active = False

        self._ensure_player_vars()
        self._restore_runtime_state_from_player()
        self._add_handlers()
        self._restore_lights_and_widgets()

    def mode_stop(self, **kwargs):
        self.daily_bugle_enabled = False
        self._release_left_exit_hold(cancel_delay=True, reason="mode_stop")
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("daily_bugle_a_hit", self.a_rollover_hit)
        self.add_mode_event_handler("daily_bugle_b_hit", self.b_rollover_hit)
        self.add_mode_event_handler("daily_bugle_rooftop_spinner_hit", self.rooftop_spinner_hit)
        self.add_mode_event_handler("daily_bugle_rooftop_left_exit", self.rooftop_left_exit)
        self.add_mode_event_handler("daily_bugle_rooftop_right_exit", self.rooftop_right_exit)
        self.add_mode_event_handler("daily_bugle_vuk_collect_request", self.vuk_collect_request)
        self.add_mode_event_handler("daily_bugle_left_exit_hold_cancel", self.cancel_left_exit_hold)
        self.add_mode_event_handler("flipper_cancel", self.cancel_left_exit_hold)

        self.add_mode_event_handler("disable_daily_bugle_mystery", self.disable_db)
        self.add_mode_event_handler("enable_daily_bugle_mystery", self.enable_db)
        self.add_mode_event_handler("reset_daily_bugle_state", self.reset_cycle)
        self.add_mode_event_handler("daily_bugle_restore_state", self._restore_lights_and_widgets)

    def _ensure_player_vars(self):
        player = self.machine.game.player

        defaults = {
            "daily_bugle_mystery_count": 0,
            "daily_bugle_extra_balls_awarded": 0,

            # These are the persistent A/B/mystery state vars.
            "daily_bugle_a_hit": 0,
            "daily_bugle_b_hit": 0,
            "daily_bugle_ab_ready": 0,
            "daily_bugle_mystery_ready": 0,
            "daily_bugle_last_instruction_key": "",
            "daily_bugle_last_instruction_text": "",
            "daily_bugle_left_exit_hold_active": 0,
            "daily_bugle_pictures_taken": 0,
            "daily_bugle_pictures_needed": 3,
            "daily_bugle_pictures_taken_text": "PICS: 0/3",
        }

        for name, value in defaults.items():
            if name not in player:
                player[name] = value

    def _restore_runtime_state_from_player(self):
        player = self.machine.game.player

        self.a_hit = bool(player["daily_bugle_a_hit"])
        self.b_hit = bool(player["daily_bugle_b_hit"])
        self.mystery_ab_ready = bool(player["daily_bugle_ab_ready"])
        self.mystery_ready = bool(player["daily_bugle_mystery_ready"])
        self.rooftop_photos = self._safe_int(player["daily_bugle_rooftop_photos"], 0)

    def disable_db(self, **kwargs):
        self.daily_bugle_enabled = False
        self.reset_cycle(post_restore=False)
        self.machine.events.post("daily_bugle_mystery_stop_all")
        self.update_player_vars()
        self._restore_lights_and_widgets()

    def enable_db(self, **kwargs):
        self.daily_bugle_enabled = True
        self._restore_lights_and_widgets()

    def a_rollover_hit(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        player = self.machine.game.player

        if not self.a_hit:
            player["score"] += self.AB_DAILY_POINTS
            self.a_hit = True
            self.update_player_vars(post_widget_update=False)
            self.machine.events.post("daily_bugle_a_complete")
            self.check_ab_complete()
        else:
            player["score"] += self.AB_DAILY_POINTS_UNLIT
            self.machine.events.post("ab_rolledover_sfx")
            self.update_player_vars()

    def b_rollover_hit(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        player = self.machine.game.player

        if not self.b_hit:
            player["score"] += self.AB_DAILY_POINTS
            self.b_hit = True
            self.update_player_vars(post_widget_update=False)
            self.machine.events.post("daily_bugle_b_complete")
            self.check_ab_complete()
        else:
            player["score"] += self.AB_DAILY_POINTS_UNLIT
            self.machine.events.post("ab_rolledover_sfx")
            self.update_player_vars()

    def check_ab_complete(self):
        if not self.a_hit or not self.b_hit:
            self.update_player_vars()
            return

        if self.mystery_ab_ready:
            self.update_player_vars()
            return

        self.mystery_ab_ready = True
        self.update_player_vars(post_widget_update=False)

        self._post_rooftop_gate_open(reason="ab_complete")
        self.machine.events.post("daily_bugle_ab_complete")
        self.machine.events.post("daily_bugle_widget_update")

    def rooftop_spinner_hit(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        if not self.mystery_ab_ready:
            return

        if self.mystery_ready:
            self.update_player_vars()
            self.machine.events.post("daily_bugle_photo_hit_after_mystery_ready")
            return

        if self.rooftop_photos < self.PHOTOS_NEEDED:
            self.rooftop_photos += 1
            self._update_pictures_taken_text()

        self.update_player_vars(post_widget_update=False)

        self.machine.events.post(
            "daily_bugle_photo_collected",
            photos=self.rooftop_photos,
            photos_needed=self.PHOTOS_NEEDED,
        )
        self.machine.events.post(f"daily_bugle_photo_{self.rooftop_photos}")

        if self.rooftop_photos >= self.PHOTOS_NEEDED:
            self.mystery_ready = True
            self.update_player_vars(post_widget_update=False)
            self.machine.events.post("daily_bugle_photos_complete")
            self.machine.events.post("daily_bugle_mystery_ready")
        else:
            self.update_player_vars(post_widget_update=False)            

        # Open gate again so player can shoot back toward VUK/mystery collect,
        # unless a gate-protected villain mode owns upper/VUK access.
        self._post_rooftop_gate_open(reason="photo_collected")
        self.machine.events.post("daily_bugle_widget_update")

    def _update_pictures_taken_text(self):
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return

        pictures = self.rooftop_photos 
        #self._safe_int(player["daily_bugle_pictures_taken"], 0)
        needed = self._safe_int(player["daily_bugle_pictures_needed"], 3)

        player["daily_bugle_pictures_taken_text"] = f"PICS: {pictures}/{needed}"

        self.machine.events.post("daily_bugle_widget_update")

    def rooftop_left_exit(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        if not self.mystery_ab_ready:
            return

        instruction_key, instruction_text = self._post_rooftop_instruction(exit_side="left")
        self._start_left_exit_hold(instruction_key=instruction_key, instruction_text=instruction_text)

    def rooftop_right_exit(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        if not self.mystery_ab_ready:
            return

        # Right exit is only a callout/SFX route. It does not raise the post.
        self._post_rooftop_instruction(exit_side="right")

    def _post_rooftop_instruction(self, exit_side="unknown"):
        instruction_key, instruction_text = self._current_rooftop_instruction()

        player = self.machine.game.player
        player["daily_bugle_last_instruction_key"] = instruction_key
        player["daily_bugle_last_instruction_text"] = instruction_text

        self.machine.events.post(
            "daily_bugle_rooftop_instruction",
            instruction_key=instruction_key,
            instruction_text=instruction_text,
            exit_side=exit_side,
        )
        self.machine.events.post(f"daily_bugle_rooftop_instruction_{instruction_key}")
        self.machine.events.post(f"daily_bugle_rooftop_{exit_side}_instruction_{instruction_key}")
        self.machine.events.post("daily_bugle_widget_update")

        return instruction_key, instruction_text

    def _current_rooftop_instruction(self):
        if self._any_saucer_ready():
            return (
                "villain_ready",
                "Get to the saucers to fight your next villain.",
            )

        if self.mystery_ready:
            return (
                "bring_pics",
                "Let me see those pics. Bring them to my office.",
            )

        return (
            "more_pics",
            "Get back out there and take more pics.",
        )

    def _any_saucer_ready(self):
        player = self.machine.game.player

        for num in (1, 2, 3):
            try:
                state = player[f"saucer_{num}_state"]
            except Exception:
                state = 0

            if self._safe_int(state, 0) > 0:
                return True

        return False

    def _start_left_exit_hold(self, instruction_key=None, instruction_text=None):
        if self.left_exit_hold_active:
            self.delay.remove("daily_bugle_left_exit_hold_release")
        else:
            self.left_exit_hold_active = True
            self.machine.game.player["daily_bugle_left_exit_hold_active"] = 1
            self.machine.events.post("enable_up_post_event")
            self.machine.events.post(
                "daily_bugle_left_exit_hold_started",
                instruction_key=instruction_key,
                instruction_text=instruction_text,
            )

        self.delay.add(
            name="daily_bugle_left_exit_hold_release",
            ms=self.LEFT_EXIT_HOLD_MS,
            callback=self._release_left_exit_hold,
        )

    def cancel_left_exit_hold(self, **kwargs):
        if not self.left_exit_hold_active:
            return

        self.machine.events.post("daily_bugle_left_exit_hold_cancelled")
        self._release_left_exit_hold(cancel_delay=True, reason="flipper_cancel")

    def _release_left_exit_hold(self, cancel_delay=False, reason="timer"):
        if cancel_delay:
            self.delay.remove("daily_bugle_left_exit_hold_release")

        if not self.left_exit_hold_active:
            return

        self.left_exit_hold_active = False
        if self.machine.game:
            self.machine.game.player["daily_bugle_left_exit_hold_active"] = 0
        self.machine.events.post("timer_timer_up_post_hold_complete")
        self.machine.events.post("daily_bugle_left_exit_hold_released", reason=reason)

    def vuk_collect_request(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        player = self.machine.game.player
        if player["mini_wizard_daily_bugle_ready"] == 1 or player["mini_wizard_vuk_hold_active"] == 1:
            # Progression owns this VUK hit. Leave the ball held until the
            # mini-wizard bookend intro finishes or the player skips it.
            return

        if not self.mystery_ready:
            # VUK was hit but mystery is not ready. Kick up quickly for other uses.
            self.delay.add(
                name="daily_bugle_vuk_delay_eject",
                ms=500,
                callback=self.fire_vuk,
            )
            return

        # Mystery is ready. Hold briefly, award, then eject.
        self.collect_mystery()

    def collect_mystery(self):
        player = self.machine.game.player

        player["daily_bugle_mystery_count"] += 1
        count = player["daily_bugle_mystery_count"]

        self.machine.events.post("daily_bugle_mystery_collected")

        if count == self.EXTRA_BALL_LIGHT_AT:
            self.light_extra_ball()
        elif count == self.EXTRA_BALL_AWARD_AT:
            self.award_extra_ball()
        elif count == self.EXTRA_BALL_RIGHT_LIGHT_AT:
            self.light_right_extra_ball()
        else:
            self.award_pseudo_random_mystery()

        self.reset_cycle(post_restore=False)
        self.update_player_vars()

        self.delay.add(
            name="daily_bugle_vuk_delay_eject",
            ms=5000,
            callback=self.fire_vuk,
        )
        self._post_rooftop_gate_close(reason="mystery_collected")

    def _gate_control_blocked_by_villain(self):
        player = self.machine.game.player

        if player["villain_mode_running"] != 1:
            return False

        running_name = player["villain_mode_running_name"]
        return running_name in self.GATE_PROTECTED_VILLAIN_MODES

    def _post_rooftop_gate_open(self, reason="unknown"):
        if self._gate_control_blocked_by_villain():
            player = self.machine.game.player
            self.machine.events.post(
                "daily_bugle_gate_open_deferred",
                reason=reason,
                villain_mode=player["villain_mode_running_name"],
            )
            return

        self.machine.events.post("rooftop_diverter_open")

    def _post_rooftop_gate_close(self, reason="unknown"):
        if self._gate_control_blocked_by_villain():
            player = self.machine.game.player
            self.machine.events.post(
                "daily_bugle_gate_close_deferred",
                reason=reason,
                villain_mode=player["villain_mode_running_name"],
            )
            return

        self.machine.events.post("rooftop_diverter_close")

    def award_pseudo_random_mystery(self):
        player = self.machine.game.player
        valid_awards = list(self.PLACEHOLDER_AWARDS)

        # Try a handful of times to avoid awards that are not currently useful.
        for _ in range(20):
            award_event = random.choice(valid_awards)

            if award_event == "mystery_award_villain_start_ready":
                villain_mode_running = player["villain_mode_running"]
                villain_start_ready = player["villain_start_ready"]
                if villain_mode_running == 0 and villain_start_ready == 0:
                    self.machine.events.post(award_event)
                    return

            elif award_event == "mystery_award_hold_bonus":
                hold_bonus = player["hold_bonus"]
                if hold_bonus == 0:
                    self.machine.events.post(award_event)
                    return

            else:
                self.machine.events.post(award_event)
                return

        # Safe fallback if every random choice was filtered out.
        self.machine.events.post("mystery_award_million_points")

    def fire_vuk(self):
        self.machine.events.post("up_kick")

    def light_extra_ball(self):
        self.machine.events.post("mystery_award_light_extra_ball")

    def light_right_extra_ball(self):
        self.machine.events.post("mystery_award_light_right_extra_ball")

    def award_extra_ball(self):
        self.machine.events.post("mystery_award_award_extra_ball")

    def reset_cycle(self, post_restore=True, **kwargs):
        self.a_hit = False
        self.b_hit = False
        self.mystery_ab_ready = False
        self.mystery_ready = False
        self.rooftop_photos = 0
        self.update_player_vars()

        if post_restore:
            self._restore_lights_and_widgets()

    def update_player_vars(self, post_widget_update=True):
        player = self.machine.game.player

        player["daily_bugle_a_hit"] = int(self.a_hit)
        player["daily_bugle_b_hit"] = int(self.b_hit)
        player["daily_bugle_ab_ready"] = int(self.mystery_ab_ready)
        player["daily_bugle_mystery_ready"] = int(self.mystery_ready)

        if post_widget_update:
            self.machine.events.post("daily_bugle_widget_update")

    def _restore_lights_and_widgets(self, **kwargs):
        """Restore visuals from state without replaying hit animations."""

        self.machine.events.post("daily_bugle_mystery_stop_all")

        if self.mystery_ready:
            self.machine.events.post("daily_bugle_restore_mystery_ready")
        elif self.mystery_ab_ready:
            self.machine.events.post("daily_bugle_restore_ab_ready")
        else:
            if self.a_hit:
                self.machine.events.post("daily_bugle_a_restore_complete")
            else:
                self.machine.events.post("daily_bugle_a_restore_incomplete")

            if self.b_hit:
                self.machine.events.post("daily_bugle_b_restore_complete")
            else:
                self.machine.events.post("daily_bugle_b_restore_incomplete")

        self.machine.events.post("daily_bugle_widget_update")

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
