from mpf.core.mode import Mode


class ExtraBall(Mode):
    """Shared extra-ball presentation plus Daily Bugle VUK ownership."""

    DAILY_BUGLE_NEWSPAPER_REVEAL_MS = 3000
    EXTRA_BALL_PRESENTATION_MS = 6000

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)
        if self.machine.game:
            self.machine.game.player["extra_ball_vuk_hold_active"] = 0
        self.add_mode_event_handler(
            "mystery_extra_ball_award", self._maybe_claim_daily_bugle_vuk
        )
        self.add_mode_event_handler(
            "mystery_extra_ball_direct_award", self._maybe_claim_daily_bugle_vuk
        )

    def mode_stop(self, **kwargs):
        self.delay.remove("daily_bugle_extra_ball_takeover")
        self.delay.remove("daily_bugle_extra_ball_finish")
        if self.machine.game:
            self.machine.game.player["extra_ball_vuk_hold_active"] = 0
        super().mode_stop(**kwargs)

    def _maybe_claim_daily_bugle_vuk(self, **kwargs):
        if not self.machine.game:
            return
        player = self.machine.game.player
        if int(player["daily_bugle_vuk_hold_active"] or 0) != 1:
            return

        # The extra-ball award fires/reveals at 3s. Claim the parked VUK ball
        # immediately, but let the newspaper remain visible for another 3s.
        player["extra_ball_vuk_hold_active"] = 1
        self.machine.events.post("extra_ball_vuk_ownership_claimed")
        self.delay.reset(
            name="daily_bugle_extra_ball_takeover",
            ms=self.DAILY_BUGLE_NEWSPAPER_REVEAL_MS,
            callback=self._start_daily_bugle_extra_ball_presentation,
        )

    def _start_daily_bugle_extra_ball_presentation(self):
        if not self.machine.game:
            return
        player = self.machine.game.player
        if int(player["extra_ball_vuk_hold_active"] or 0) != 1:
            return
        self.machine.events.post("daily_bugle_extra_ball_presentation_start")
        self.delay.reset(
            name="daily_bugle_extra_ball_finish",
            ms=self.EXTRA_BALL_PRESENTATION_MS,
            callback=self._finish_daily_bugle_extra_ball_presentation,
        )

    def _finish_daily_bugle_extra_ball_presentation(self):
        if not self.machine.game:
            return
        player = self.machine.game.player
        if int(player["extra_ball_vuk_hold_active"] or 0) != 1:
            return
        player["extra_ball_vuk_hold_active"] = 0
        self.machine.events.post("daily_bugle_extra_ball_presentation_complete")
        self.machine.events.post("request_vuk_eject")
