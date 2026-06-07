from mpf.core.mode import Mode


class VillainStart(Mode):
    """Physical villain start request handler.

    This mode owns saucer/start-shot behavior only. It does not know the villain
    chapter lists and it does not start villain modes directly. It forwards valid
    start attempts to villain_progression, which is the source of truth.
    """

    SAUCERS = ["saucer_1", "saucer_2", "saucer_3"]

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        self.villain_start_logic_active = True
        self._ensure_player_vars()
        self._add_handlers()

    def mode_stop(self, **kwargs):
        self.villain_start_logic_active = False
        super().mode_stop(**kwargs)

    def _ensure_player_vars(self):
        defaults = {
            "villain_mode_running": 0,
            "villain_current_name": "",
            "villain_mode_running_name": "",
            "villain_chapter": 1,
            "chapter_mini_wizard_ready": 0,
            "final_wizard_ready": 0,
        }
        for name, value in defaults.items():
            if name not in self.machine.game.player:
                self.machine.game.player[name] = value

    def _add_handlers(self):
        self.add_mode_event_handler("saucer_1_hit", self._saucer_hit, saucer="saucer_1")
        self.add_mode_event_handler("saucer_2_hit", self._saucer_hit, saucer="saucer_2")
        self.add_mode_event_handler("saucer_3_hit", self._saucer_hit, saucer="saucer_3")
        self.add_mode_event_handler("villain_started_set", self._villain_started)
        self.add_mode_event_handler("villain_mode_started", self._villain_started)
        self.add_mode_event_handler("villain_mode_ended", self._villain_mode_ended)
        self.add_mode_event_handler("chapter_mini_wizard_completed", self._villain_mode_ended)
        self.add_mode_event_handler("villain_select_cancelled", self._villain_select_cancelled)
        self.add_mode_event_handler("villain_start_request_failed", self._villain_start_request_failed)

    def _villain_started(self, villain_key=None, villain_name=None, villain=None, **kwargs):
        key = villain_key or villain or villain_name or self._player_var("villain_current_name", "")
        self.villain_start_logic_active = False
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_current_name"] = key
        self.machine.game.player["villain_mode_running_name"] = key
        self.machine.events.post("clear_villain_saucer_lights")

    def _villain_mode_ended(self, **kwargs):
        self._unlock_start_logic()

    def _villain_select_cancelled(self, **kwargs):
        if self._player_var("villain_current_name", "") == "villain_select":
            self._unlock_start_logic()

    def _villain_start_request_failed(self, **kwargs):
        if self._player_var("villain_current_name", "") in ("villain_select", "villain_start"):
            self._unlock_start_logic()

    def _unlock_start_logic(self):
        self.villain_start_logic_active = True
        self.machine.game.player["villain_mode_running"] = 0
        self.machine.game.player["villain_current_name"] = ""
        self.machine.game.player["villain_mode_running_name"] = ""

    def _saucer_hit(self, saucer=None, **kwargs):
        if saucer not in self.SAUCERS:
            return
        if self._player_var("villain_mode_running") == 1:
            self.machine.events.post("villain_saucer_ignored_mode_running", saucer=saucer)
            return
        if not self.villain_start_logic_active:
            self.machine.events.post("villain_saucer_ignored_start_locked", saucer=saucer)
            return

        state = self._safe_int(self._player_var(f"{saucer}_state", 0), 0)
        should_lock = (
            state > 0
            or self._safe_int(self._player_var("final_wizard_ready", 0), 0) == 1
            or self._safe_int(self._player_var("chapter_mini_wizard_ready", 0), 0) == 1
        )

        if should_lock:
            self._lock_saucers_for_start()

        self.machine.events.post(
            "villain_progression_request_start",
            saucer=saucer,
            source="saucer",
            state=state,
            max_choices=state,
        )

    def _lock_saucers_for_start(self):
        self.villain_start_logic_active = False
        self.machine.game.player["villain_mode_running"] = 1
        self.machine.game.player["villain_current_name"] = "villain_select"
        self.machine.game.player["villain_mode_running_name"] = "villain_select"
        self.machine.events.post("clear_villain_saucer_lights")

    def _player_var(self, name, default=0):
        try:
            return self.machine.game.player[name]
        except Exception:
            return default

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default
