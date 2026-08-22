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
            "saucer": "saucer_1",
        },
        "center": {
            "display": "CENTER WEB",
            "saucer": "saucer_2",
        },
        "right": {
            "display": "RIGHT POP",
            "saucer": "saucer_3",
        },
    }

    SAUCER_TO_AREA = {
        "saucer_1": "left",
        "saucer_2": "center",
        "saucer_3": "right",
    }

    SAUCER_NUMBERS = {
        "saucer_1": "1",
        "saucer_2": "2",
        "saucer_3": "3",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.reset_active_mode_summary(stat_count=3)
        self.mode_exiting = False
        self.jackpots_collected = 0
        self.biggest_jackpot = 0

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
        self.add_a_ball_save_seconds = 15 if self.has_case_file("more_time") else 10
        self.shot_assist = self.has_case_file("shot_assist")

        self._reset_player_vars()
        self._register_handlers()
        self.publish_case_file_bonus_events("molemen")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "POP ADD-A-BALL IN 2 HITS"),
            ("bigger_jackpots", "BIGGER AREA AND SAUCER JACKPOTS"),
            ("more_time", "15 SECOND SAVE AFTER ADD-A-BALL"),
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
        self.delay.remove("molemen_ball_added_message")
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

        # Keep the rooftop closed even if another subsystem asks to open it.
        self.add_mode_event_handler("rooftop_diverter_open", self._force_gate_closed)
        self.add_mode_event_handler("open_rooftop_gate", self._force_gate_closed)

    def _reset_player_vars(self):
        player = self.machine.game.player
        player["active_mode_points"] = 0
        player["molemen_state"] = 1
        player["active_mode_stat_1"] = self.biggest_jackpot
        player["active_mode_stat_2"] = self.jackpots_collected
        player["molemen_opening_save_seconds"] = self.opening_save_seconds
        player["molemen_add_a_ball_save_seconds"] = self.add_a_ball_save_seconds
        self.area_state = {
            area: {"hits": 0, "lit": False, "add_ready": False, "add_used": False}
            for area in self.AREAS
        }

    def _left_pop_hit(self, **kwargs):
        self._area_hit("left")

    def _right_pop_hit(self, **kwargs):
        self._area_hit("right")

    def _center_web_hit(self, **kwargs):
        self._area_hit("center")

    def _area_hit(self, area):
        if self.mode_exiting:
            return
        data = self.AREAS[area]
        state = self.area_state[area]

        score = self.center_score if area == "center" else self.pop_score
        self._score(score)
        state["hits"] += 1
        state["lit"] = True

        add_threshold = 1 if area == "center" else self.pop_add_ball_hits
        if not state["add_used"] and state["hits"] >= add_threshold:
            state["add_ready"] = True
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
        state = self.area_state[area]

        if not state["lit"]:
            self._eject_saucer(saucer)
            return

        balls = max(1, self._balls_in_play())
        value = self.jackpot_per_ball * balls
        self._score(value)
        self.jackpots_collected += 1
        self.biggest_jackpot = max(self.biggest_jackpot, value)
        player["active_mode_stat_1"] = self.biggest_jackpot
        player["active_mode_stat_2"] = self.jackpots_collected

        add_ball = state["add_ready"] and not state["add_used"]
        if add_ball:
            state["add_used"] = True
            state["add_ready"] = False
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
        data = self.AREAS[area]
        state = self.area_state[area]
        state["hits"] = 0
        state["lit"] = False
        state["add_ready"] = False
        self.machine.events.post(f"molemen_{data['saucer']}_reset")

    def _show_ball_added(self):
        if not self.mode_exiting:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="BALL ADDED",
                message_mode_subtitle="MULTIBALL CONTINUES",
            )

    def _multiball_ended(self, **kwargs):
        if self.mode_exiting:
            return
        self.mode_exiting = True
        self.machine.game.player["molemen_state"] = 2
        self.machine.events.post("molemen_mode_complete")

    def _force_gate_closed(self, **kwargs):
        if not self.mode_exiting:
            self.machine.events.post("rooftop_diverter_close")

    def _update_status(self):
        if self.mode_exiting:
            return
        self.machine.events.post(
            "show_mode_status",
            mode_status_title="BUILD SAUCER JACKPOTS",
            mode_status_value=(
                f"L {self.area_state['left']['hits']}  "
                f"C {self.area_state['center']['hits']}  "
                f"R {self.area_state['right']['hits']}"
            ),
        )

    def _eject_saucer(self, saucer):
        saucer_number = self.SAUCER_NUMBERS.get(saucer)
        if saucer_number is None:
            return
        self.machine.events.post(
            "request_saucer_eject",
            saucer_number=saucer_number,
            delay_ms=self.SAUCER_EJECT_MS,
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
