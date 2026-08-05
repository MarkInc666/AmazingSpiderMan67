from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Molemen(CaseFileMixin, Mode):
    """The Molemen: three-area, saucer-jackpot two-ball multiball."""

    POP_SCORE = 50_000
    POP_SCORE_BIGGER = 75_000
    CENTER_SCORE = 100_000
    CENTER_SCORE_BIGGER = 150_000
    JACKPOT_PER_BALL = 250_000
    JACKPOT_PER_BALL_BIGGER = 300_000
    POP_ADD_A_BALL_HITS = 3
    POP_ADD_A_BALL_HITS_MORE_JP = 2
    SAUCER_EJECT_MS = 2_000

    AREAS = {
        "left": {
            "display": "LEFT POP",
            "hits_var": "molemen_left_hits",
            "lit_var": "molemen_saucer_1_lit",
            "add_ready_var": "molemen_saucer_1_add_ball_ready",
            "add_used_var": "molemen_saucer_1_add_ball_used",
            "saucer": "saucer_1",
        },
        "center": {
            "display": "CENTER WEB",
            "hits_var": "molemen_center_hits",
            "lit_var": "molemen_saucer_2_lit",
            "add_ready_var": "molemen_saucer_2_add_ball_ready",
            "add_used_var": "molemen_saucer_2_add_ball_used",
            "saucer": "saucer_2",
        },
        "right": {
            "display": "RIGHT POP",
            "hits_var": "molemen_right_hits",
            "lit_var": "molemen_saucer_3_lit",
            "add_ready_var": "molemen_saucer_3_add_ball_ready",
            "add_used_var": "molemen_saucer_3_add_ball_used",
            "saucer": "saucer_3",
        },
    }

    SAUCER_TO_AREA = {
        "saucer_1": "left",
        "saucer_2": "center",
        "saucer_3": "right",
    }

    EJECT_EVENTS = {
        "saucer_1": "delayed_kickout_saucer_1",
        "saucer_2": "delayed_kickout_saucer_2",
        "saucer_3": "delayed_kickout_saucer_3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.mode_exiting = False
        self.grace_active = False

        self.case_files = self.get_case_file_bonuses()
        self.pop_score = self.POP_SCORE_BIGGER if self.has_case_file("bigger_jackpots") else self.POP_SCORE
        self.center_score = self.CENTER_SCORE_BIGGER if self.has_case_file("bigger_jackpots") else self.CENTER_SCORE
        self.jackpot_per_ball = (
            self.JACKPOT_PER_BALL_BIGGER
            if self.has_case_file("bigger_jackpots")
            else self.JACKPOT_PER_BALL
        )
        self.pop_add_ball_hits = (
            self.POP_ADD_A_BALL_HITS_MORE_JP
            if self.has_case_file("more_jackpots")
            else self.POP_ADD_A_BALL_HITS
        )
        self.opening_save_seconds = 25 if self.has_case_file("safety_net") else 15
        self.one_ball_grace_seconds = 10 if self.has_case_file("more_time") else 5
        self.shot_assist = self.has_case_file("shot_assist")

        self._reset_player_vars()
        self._register_handlers()
        self.publish_case_file_bonus_events("molemen")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "POP ADD-A-BALL IN 2 HITS"),
            ("bigger_jackpots", "BIGGER AREA AND SAUCER JACKPOTS"),
            ("more_time", "10 SECOND ONE-BALL GRACE"),
            ("safety_net", "25 SECOND OPENING SAVE"),
            ("shot_assist", "LEFT WEB ALSO COUNTS AS CENTER WEB"),
        ])

        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("molemen_startup_complete")
        self.machine.events.post(
            "show_mode_message_long",
            message_mode_title="THE MOLEMEN",
            message_mode_subtitle="BUILD SAUCER JACKPOTS",
        )
        self._update_status()

    def mode_stop(self, **kwargs):
        self.mode_exiting = True
        self.grace_active = False
        self.delay.remove("molemen_one_ball_grace")
        self.delay.remove("molemen_ball_added_message")
        for saucer in self.EJECT_EVENTS:
            self.delay.remove(f"molemen_eject_{saucer}")
        self.machine.events.post("molemen_clear_all_lights")
        self.machine.events.post("clear_saucers_delayed")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("hide_mode_status")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _register_handlers(self):
        self.add_mode_event_handler("s_pop_left_active", self._left_pop_hit)
        self.add_mode_event_handler("s_pop_right_active", self._right_pop_hit)
        self.add_mode_event_handler("s_web_target_mid_active", self._center_web_hit)
        if self.shot_assist:
            self.add_mode_event_handler("s_web_target_left_active", self._center_web_hit)

        self.add_mode_event_handler("s_saucer_1_active", self._saucer_1_hit)
        self.add_mode_event_handler("s_saucer_2_active", self._saucer_2_hit)
        self.add_mode_event_handler("s_saucer_3_active", self._saucer_3_hit)
        self.add_mode_event_handler("multiball_molemen_multiball_ended", self._multiball_ended)
        self.add_mode_event_handler("multiball_molemen_multiball_started", self._multiball_started)

        # Keep the rooftop closed even if another subsystem asks to open it.
        self.add_mode_event_handler("rooftop_diverter_open", self._force_gate_closed)
        self.add_mode_event_handler("open_rooftop_gate", self._force_gate_closed)

    def _reset_player_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["molemen_state"] = 1
        player["molemen_jackpots"] = 0
        player["molemen_biggest_jackpot"] = 0
        player["molemen_opening_save_seconds"] = self.opening_save_seconds
        player["molemen_one_ball_grace_seconds"] = self.one_ball_grace_seconds
        for data in self.AREAS.values():
            player[data["hits_var"]] = 0
            player[data["lit_var"]] = 0
            player[data["add_ready_var"]] = 0
            player[data["add_used_var"]] = 0

    def _left_pop_hit(self, **kwargs):
        self._area_hit("left")

    def _right_pop_hit(self, **kwargs):
        self._area_hit("right")

    def _center_web_hit(self, **kwargs):
        self._area_hit("center")

    def _area_hit(self, area):
        if self.mode_exiting:
            return
        player = self.machine.game.player
        data = self.AREAS[area]

        score = self.center_score if area == "center" else self.pop_score
        self._score(score)
        player[data["hits_var"]] += 1
        player[data["lit_var"]] = 1

        add_threshold = 1 if area == "center" else self.pop_add_ball_hits
        if player[data["add_used_var"]] == 0 and player[data["hits_var"]] >= add_threshold:
            player[data["add_ready_var"]] = 1
            self.machine.events.post(f"molemen_{data['saucer']}_add_ball_ready")

        self.machine.events.post(f"molemen_{data['saucer']}_jackpot_lit")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=f"{data['display']} HIT",
            message_mode_subtitle="SAUCER JACKPOT LIT",
            message_mode_value=score,
        )
        self._update_status()

    def _saucer_1_hit(self, **kwargs):
        self._handle_saucer("saucer_1")

    def _saucer_2_hit(self, **kwargs):
        self._handle_saucer("saucer_2")

    def _saucer_3_hit(self, **kwargs):
        self._handle_saucer("saucer_3")

    def _handle_saucer(self, saucer):
        if self.mode_exiting:
            self._eject_saucer(saucer)
            return

        area = self.SAUCER_TO_AREA[saucer]
        data = self.AREAS[area]
        player = self.machine.game.player

        if player[data["lit_var"]] != 1:
            self._eject_saucer(saucer)
            return

        balls = max(1, self._balls_in_play())
        value = self.jackpot_per_ball * balls
        self._score(value)
        player["molemen_jackpots"] += 1
        player["molemen_biggest_jackpot"] = max(int(player["molemen_biggest_jackpot"]), value)

        add_ball = player[data["add_ready_var"]] == 1 and player[data["add_used_var"]] == 0
        if add_ball:
            player[data["add_used_var"]] = 1
            player[data["add_ready_var"]] = 0
            self.machine.events.post("molemen_add_a_ball")
            self.delay.remove("molemen_ball_added_message")
            self.delay.add(name="molemen_ball_added_message", ms=2100, callback=self._show_ball_added)

        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="MOLEMEN JACKPOT",
            message_mode_subtitle=data["display"],
            message_mode_value=value,
        )
        self.machine.events.post("molemen_jackpot_collected", saucer=saucer, area=area, value=value)
        self._reset_area(area)
        self._eject_saucer(saucer)
        self._update_status()

    def _reset_area(self, area):
        player = self.machine.game.player
        data = self.AREAS[area]
        player[data["hits_var"]] = 0
        player[data["lit_var"]] = 0
        player[data["add_ready_var"]] = 0
        self.machine.events.post(f"molemen_{data['saucer']}_reset")

    def _show_ball_added(self):
        if not self.mode_exiting:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="BALL ADDED",
                message_mode_subtitle="MULTIBALL CONTINUES",
            )

    def _multiball_started(self, **kwargs):
        self.grace_active = False
        self.delay.remove("molemen_one_ball_grace")

    def _multiball_ended(self, **kwargs):
        if self.mode_exiting or self.grace_active:
            return
        self.grace_active = True
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="ONE BALL REMAINS",
            message_mode_subtitle="GRACE PERIOD",
            message_mode_seconds=self.one_ball_grace_seconds,
        )
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="ONE BALL GRACE",
            mode_status_value=f"{self.one_ball_grace_seconds} SEC",
        )
        self.delay.add(
            name="molemen_one_ball_grace",
            ms=self.one_ball_grace_seconds * 1000,
            callback=self._finish_grace,
        )

    def _finish_grace(self):
        if self.mode_exiting:
            return
        if self._balls_in_play() > 1:
            self.grace_active = False
            self._update_status()
            return
        self.mode_exiting = True
        self.machine.game.player["molemen_state"] = 2
        self.machine.events.post("molemen_mode_complete")

    def _force_gate_closed(self, **kwargs):
        if not self.mode_exiting:
            self.machine.events.post("rooftop_diverter_close")

    def _update_status(self):
        if self.mode_exiting or self.grace_active:
            return
        p = self.machine.game.player
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="BUILD SAUCER JACKPOTS",
            mode_status_value=(
                f"L {p['molemen_left_hits']}  "
                f"C {p['molemen_center_hits']}  "
                f"R {p['molemen_right_hits']}"
            ),
        )

    def _eject_saucer(self, saucer):
        event = self.EJECT_EVENTS.get(saucer)
        if not event:
            return
        self.delay.remove(f"molemen_eject_{saucer}")
        self.delay.add(
            name=f"molemen_eject_{saucer}",
            ms=self.SAUCER_EJECT_MS,
            callback=self.machine.events.post,
            event=event,
        )

    def _balls_in_play(self):
        if not self.machine.game:
            return 0
        return int(self.machine.game.balls_in_play or 0)

    def _score(self, points):
        if points <= 0:
            return
        player = self.machine.game.player
        player["score"] += points
        player["active_mode_points"] += points
