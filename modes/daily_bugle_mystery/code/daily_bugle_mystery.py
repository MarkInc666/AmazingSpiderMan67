import random
from mpf.core.mode import Mode


class DailyBugleMystery(Mode):
    """Daily Bugle Mystery / Scoop mode.

    Flow:
      1. Complete A+B.
      2. Rooftop gate opens.
      3. Shoot VUK to the rooftop.
      4. Rooftop-spinner hits add to a persistent picture balance.
      5. Mystery costs progress from 1 through 10 pictures, then remain at 10.
      6. Left exit can hold the ball on the pop-up post for JJJ instructions.
      7. Right exit only plays the same instruction/callout, without the post.
      8. VUK collects Mystery when ready and spends the current picture cost.

    Important change from the older version:
      A/B/mystery progress is restored from player vars when the mode starts,
      so the state can survive ball drains.
    """

    AB_DAILY_POINTS = 10000
    AB_DAILY_POINTS_UNLIT = 2000

    MAX_PICTURE_COST = 10
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
        "conners_reptiles",
        "noah_boddy",
        "vulcan",
        "fifth_avenue_phantom",
        "dr_von_schlick",
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
        "mystery_award_start_next_villain",
        "mystery_award_random_case_file",
    ]

    AWARD_MESSAGES = {
        "mystery_award_ball_save": ("BALL SAVE", "LIT"),
        "mystery_award_start_super_spinner": ("SUPER SPINNER", "20 SECONDS"),
        "mystery_award_advance_bonus_multiplier": ("BONUS X", "ADVANCED"),
        "mystery_award_collect_bonus": ("BONUS", "COLLECTED"),
        "mystery_award_hold_bonus": ("HOLD BONUS", "AWARDED"),
        "mystery_award_start_super_pops": ("SUPER POPS", "20 SECONDS"),
        "mystery_award_million_points": ("MYSTERY AWARD", "1,000,000"),
        "mystery_award_villain_start_ready": ("VILLAIN READY", "SAUCERS MAXED"),
        "mystery_award_start_next_villain": ("START NEXT VILLAIN", "SEARCHING..."),
        "mystery_award_random_case_file": ("CASE FILE", "SEARCHING..."),
        "mystery_award_light_extra_ball": ("EXTRA BALL", "LIT"),
        "mystery_award_light_right_extra_ball": ("EXTRA BALL", "RIGHT BANK LIT"),
        "mystery_award_award_extra_ball": ("EXTRA BALL", "AWARDED"),
    }

    # Lightweight copy of the current chapter villain order. VillainProgression
    # remains the source of truth for actually starting modes; this is only used
    # to avoid selecting mystery awards that cannot do anything right now.
    CHAPTER_VILLAINS = {
        1: ('rhino', 'sandman', 'vulture', 'goblin', 'electro'),
        2: ('lizard', 'doc_ock', 'mysterio', 'scorpion', 'parafino'),
        3: ('cerberus', 'vulcan', 'diana', 'cyclops', 'centaur'),
        4: ('plotter', 'fly_twins', 'fifth_avenue_phantom', 'enforcers', 'doctor_cool'),
        5: ('harley_clivendon', 'conquistador', 'spider_slayer', 'metal_eating_robot', 'fiddler'),
        6: ('pardo', 'fakir', 'kotep', 'super_swami', 'infinata'),
        7: ('noah_boddy', 'dr_magneto', 'professor_pretorius', 'doctor_dumpty', 'dr_von_schlick'),
        8: ('clive_blotto', 'dr_zapp', 'bolton_boomer', 'snowman', 'plutonians'),
        9: ('dr_manta', 'igor', 'doctor_atlantean', 'devargas', 'molemen'),
        10: ('charles_cameo', 'brutus', 'desperado', 'skymaster', 'conners_reptiles'),
        11: ('sir_galahad', 'master_vine', 'master_technician', 'spider_men', 'von_rantenraven'),
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.daily_bugle_enabled = True
        self.left_exit_hold_active = False

        self._restore_runtime_state_from_player()
        self._add_handlers()
        self._restore_lights_and_widgets()

    def mode_stop(self, **kwargs):
        self.daily_bugle_enabled = False
        self.delay.remove("daily_bugle_widget_update_deferred")
        self.machine.events.post("daily_bugle_widget_remove")
        self._cancel_vuk_delay_eject()
        self._release_left_exit_hold(cancel_delay=True, reason="mode_stop")
        super().mode_stop(**kwargs)

    def _add_handlers(self):
        self.add_mode_event_handler("daily_bugle_a_hit", self.a_rollover_hit)
        self.add_mode_event_handler("daily_bugle_b_hit", self.b_rollover_hit)
        self.add_mode_event_handler("daily_bugle_sling_swap_request", self.sling_swap_ab)
        self.add_mode_event_handler("daily_bugle_rooftop_spinner_hit", self.rooftop_spinner_hit)
        self.add_mode_event_handler("daily_bugle_rooftop_left_exit", self.rooftop_left_exit)
        self.add_mode_event_handler("daily_bugle_rooftop_right_exit", self.rooftop_right_exit)
        self.add_mode_event_handler("daily_bugle_vuk_collect_request", self.vuk_collect_request)
        self.add_mode_event_handler("daily_bugle_cancel_vuk_delay_eject", self._cancel_vuk_delay_eject)
        self.add_mode_event_handler("daily_bugle_left_exit_hold_cancel", self.cancel_left_exit_hold)
        self.add_mode_event_handler("flipper_cancel", self.cancel_left_exit_hold)

        self.add_mode_event_handler("disable_daily_bugle_mystery", self.disable_db)
        self.add_mode_event_handler("enable_daily_bugle_mystery", self.enable_db)
        self.add_mode_event_handler("reset_daily_bugle_state", self.reset_cycle)
        self.add_mode_event_handler("daily_bugle_restore_state", self._restore_lights_and_widgets)

    def _restore_runtime_state_from_player(self):
        player = self.machine.game.player

        self.a_hit = bool(player["daily_bugle_a_hit"])
        self.b_hit = bool(player["daily_bugle_b_hit"])
        self.mystery_ab_ready = bool(player["daily_bugle_ab_ready"])
        self.rooftop_photos = self._safe_int(player["daily_bugle_pictures_taken"], 0)
        # Mystery requires both the current A+B access cycle and the current
        # escalating picture cost. Derive this instead of trusting a stale flag.
        self.mystery_ready = bool(
            self.mystery_ab_ready
            and self.rooftop_photos >= self._current_picture_cost()
        )
        self.update_player_vars(post_widget_update=False)

    def disable_db(self, **kwargs):
        # Suspend Daily Bugle activity without erasing earned A/B, photo,
        # or Mystery progress. Villain/wizard modes may disable the feature
        # temporarily and the existing state should resume afterward.
        self.daily_bugle_enabled = False
        self._cancel_vuk_delay_eject()
        self.machine.events.post("daily_bugle_mystery_stop_all")
        self.update_player_vars()
        self._restore_lights_and_widgets()

    def enable_db(self, **kwargs):
        self.daily_bugle_enabled = True
        self._restore_lights_and_widgets()

    def a_rollover_hit(self, **kwargs):
        if not self.daily_bugle_enabled or self._villain_ab_progress_paused():
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
        if not self.daily_bugle_enabled or self._villain_ab_progress_paused():
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

    def sling_swap_ab(self, **kwargs):
        """Swap a single completed A/B qualification light on a sling hit."""
        if (
            not self.daily_bugle_enabled
            or self._villain_ab_progress_paused()
            or self.mystery_ab_ready
            or self.mystery_ready
        ):
            return

        # Slings only move a single lit/completed letter. Neither or both lit
        # states are intentionally unchanged.
        if self.a_hit == self.b_hit:
            return

        self.a_hit, self.b_hit = self.b_hit, self.a_hit
        self.update_player_vars(post_widget_update=False)
        self._restore_lights_and_widgets()
        lit_letter = "A" if self.a_hit else "B"
        self.machine.events.post(
            "daily_bugle_ab_sling_swapped",
            lit_letter=lit_letter,
        )
        self.machine.events.post(
            "daily_bugle_ab_sling_swapped_to_a"
            if lit_letter == "A"
            else "daily_bugle_ab_sling_swapped_to_b"
        )

    def _villain_ab_progress_paused(self):
        """Return True while villain gameplay/progression owns the ball."""
        if not self.machine.game:
            return False
        return self._safe_int(
            self.machine.game.player["villain_mode_running"], 0
        ) == 1

    def check_ab_complete(self):
        if not self.a_hit or not self.b_hit:
            self.update_player_vars()
            return

        if self.mystery_ab_ready:
            self.update_player_vars()
            return

        self.mystery_ab_ready = True
        mystery_was_ready = self.mystery_ready
        self.mystery_ready = self.rooftop_photos >= self._current_picture_cost()
        self.update_player_vars(post_widget_update=False)

        self._post_rooftop_gate_open(reason="ab_complete")
        self.machine.events.post("daily_bugle_ab_complete")
        if self.mystery_ready and not mystery_was_ready:
            self.machine.events.post("daily_bugle_photos_complete")
            self.machine.events.post("daily_bugle_mystery_ready")
        self.machine.events.post("daily_bugle_widget_update")

    def rooftop_spinner_hit(self, **kwargs):
        if not self.daily_bugle_enabled:
            return

        # Rooftop pictures are always banked. A+B controls access to the
        # Daily Bugle Mystery, not whether the spinner can earn pictures.
        mystery_was_ready = self.mystery_ready
        self.rooftop_photos += 1
        picture_cost = self._current_picture_cost()
        self.mystery_ready = bool(
            self.mystery_ab_ready and self.rooftop_photos >= picture_cost
        )
        self.update_player_vars(post_widget_update=False)

        self.machine.events.post(
            "daily_bugle_photo_collected",
            photos=self.rooftop_photos,
            photos_needed=picture_cost,
        )
        self.machine.events.post(f"daily_bugle_photo_{self.rooftop_photos}")

        if self.mystery_ready and not mystery_was_ready:
            self.machine.events.post("daily_bugle_photos_complete")
            self.machine.events.post("daily_bugle_mystery_ready")
        elif mystery_was_ready:
            # Continue counting pictures even while an award is already ready.
            self.machine.events.post("daily_bugle_photo_hit_after_mystery_ready")

        # Once A+B has opened the Daily Bugle access cycle, keep the gate
        # available after a picture so the player can return to the VUK.
        # Before A+B, pictures still bank but do not open the gate.
        if self.mystery_ab_ready:
            self._post_rooftop_gate_open(reason="photo_collected")
        self.machine.events.post("daily_bugle_widget_update")

    def _update_pictures_taken_text(self):
        player = self.machine.game.player if self.machine.game else None

        if not player:
            return

        pictures = self._safe_int(self.rooftop_photos, 0)
        picture_cost = self._current_picture_cost()
        player["daily_bugle_pictures_taken"] = pictures
        player["daily_bugle_pictures_taken_text"] = (
            f"PICTURES TAKEN: {pictures}\nNEXT MYSTERY: {picture_cost}"
        )

        self._post_widget_update()

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

        # Spend the cost that applies before this collection increments the
        # Mystery count. Any surplus stays banked for the next A+B access cycle.
        picture_cost = self._current_picture_cost()
        self.rooftop_photos = max(0, self.rooftop_photos - picture_cost)

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
                # READY VILLAIN should max the three start saucers, but only
                # while normal villain progression is actually available. Do
                # not award it during wizard-ready, chapter-select, villain
                # select, or active-mode states.
                if self._can_ready_villain_award():
                    self._post_mystery_award(award_event)
                    return

            elif award_event == "mystery_award_start_next_villain":
                # START NEXT VILLAIN bypasses saucers entirely. Only choose it
                # when there is at least one unplayed villain in the current
                # chapter and no progression flow is already active.
                if self._can_start_next_villain_award():
                    self._post_mystery_award(award_event)
                    return

            elif award_event == "mystery_award_hold_bonus":
                hold_bonus = player["hold_bonus"]
                if hold_bonus == 0:
                    self._post_mystery_award(award_event)
                    return

            elif award_event == "mystery_award_random_case_file":
                # Case Files owns the actual random selection and collection.
                # Only offer this while Case Files are available and a file remains.
                if self._can_random_case_file_award():
                    self._post_mystery_award(award_event)
                    return

            else:
                self._post_mystery_award(award_event)
                return

        # Safe fallback if every random choice was filtered out.
        self._post_mystery_award("mystery_award_million_points")

    def _post_mystery_award(self, award_event):
        """Show a readable mystery award message, then post the award event."""
        # Case Files chooses the actual missing file, and villain progression
        # chooses the actual villain name. Let those owners publish the final
        # specific message instead of flashing a generic SEARCHING message first.
        if award_event not in (
            "mystery_award_random_case_file",
            "mystery_award_start_next_villain",
        ):
            self._post_mystery_award_message(award_event)
        self.machine.events.post(award_event)

    def _post_mystery_award_message(self, award_event):
        title, subtitle = self.AWARD_MESSAGES.get(award_event, ("MYSTERY AWARD", ""))
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
        )


    def _has_uncollected_case_file(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return False

        case_files = (
            "more_jackpots",
            "more_time",
            "bigger_jackpots",
            "safety_net",
            "shot_assist",
        )
        return any(
            self._safe_int(player[f"case_file_{key}_collected"], 0) == 0
            for key in case_files
        )

    def _can_random_case_file_award(self):
        return (
            not self._progression_award_blocked()
            and self._has_uncollected_case_file()
        )

    def _progression_award_blocked(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return True

        blocked_flags = (
            "villain_mode_running",
            "villain_select_active",
            "chapter_mini_wizard_ready",
            "mini_wizard_daily_bugle_ready",
            "mini_wizard_vuk_hold_active",
            "final_wizard_ready",
            "chapter_select_needed",
            "chapter_select_active",
        )
        return any(self._safe_int(player[name], 0) == 1 for name in blocked_flags)

    def _has_available_villain_in_current_chapter(self):
        player = self.machine.game.player if self.machine.game else None
        if not player:
            return False

        chapter_number = self._safe_int(player["villain_chapter"], 1)
        for villain_key in self.CHAPTER_VILLAINS.get(chapter_number, ()):
            if self._safe_int(player[f"{villain_key}_state"], 0) == 0:
                return True
        return False

    def _can_ready_villain_award(self):
        return (
            not self._progression_award_blocked()
            and self._has_available_villain_in_current_chapter()
        )

    def _can_start_next_villain_award(self):
        return (
            not self._progression_award_blocked()
            and self._has_available_villain_in_current_chapter()
        )


    def _cancel_vuk_delay_eject(self, **kwargs):
        """Cancel pending Daily Bugle VUK ejects so another mode can hold the VUK."""
        self.delay.remove("daily_bugle_vuk_delay_eject")

    def fire_vuk(self):
        self.machine.events.post("up_kick")

    def light_extra_ball(self):
        self._post_mystery_award("mystery_award_light_extra_ball")

    def light_right_extra_ball(self):
        self._post_mystery_award("mystery_award_light_right_extra_ball")

    def award_extra_ball(self):
        self._post_mystery_award("mystery_award_award_extra_ball")

    def reset_cycle(self, post_restore=True, **kwargs):
        # End only the current A+B access cycle. The picture balance is a
        # running player total and must survive awards, balls, and mode resets.
        self.a_hit = False
        self.b_hit = False
        self.mystery_ab_ready = False
        self.mystery_ready = False
        self.update_player_vars()

        if post_restore:
            self._restore_lights_and_widgets()

    def _current_picture_cost(self):
        """Return the next Mystery cost: 1 through 10, then 10 thereafter."""
        if not self.machine.game:
            return 1
        collected = self._safe_int(
            self.machine.game.player["daily_bugle_mystery_count"], 0
        )
        return min(collected + 1, self.MAX_PICTURE_COST)

    def update_player_vars(self, post_widget_update=True):
        player = self.machine.game.player
        picture_cost = self._current_picture_cost()

        player["daily_bugle_a_hit"] = int(self.a_hit)
        player["daily_bugle_b_hit"] = int(self.b_hit)
        player["daily_bugle_ab_ready"] = int(self.mystery_ab_ready)
        player["daily_bugle_mystery_ready"] = int(self.mystery_ready)
        player["daily_bugle_pictures_taken"] = self._safe_int(self.rooftop_photos, 0)
        player["daily_bugle_pictures_needed"] = picture_cost
        player["daily_bugle_pictures_taken_text"] = (
            f"PICTURES TAKEN: {player['daily_bugle_pictures_taken']}\n"
            f"NEXT MYSTERY: {picture_cost}"
        )

        if post_widget_update:
            self._post_widget_update()

    def _post_widget_update(self):
        if not getattr(self, "daily_bugle_enabled", False):
            return
        self.machine.events.post("daily_bugle_widget_update")
        self.delay.remove("daily_bugle_widget_update_deferred")
        self.delay.add(
            name="daily_bugle_widget_update_deferred",
            ms=50,
            callback=self._post_deferred_widget_update,
        )

    def _post_deferred_widget_update(self):
        if getattr(self, "daily_bugle_enabled", False):
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

        self._post_widget_update()

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
