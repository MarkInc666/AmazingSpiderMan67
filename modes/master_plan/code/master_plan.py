import random
from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class MasterPlan(Mode):
    """The Plotter — Front Page Frame-Up.

    Pops build Rumours. Spinner converts 2 Rumours into Headlines at saucers.
    Collect 3 Headlines to light Master Plan VUK for Super. After each Super,
    Rumours start draining; pops can keep adding Rumours and the loop repeats
    until the Rumours run out.
    """

    MODE_KEY = "master_plan"
    DISPLAY_NAME = "The Plotter - Master Plan"

    SAUCERS = (1, 2, 3)

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_done = False
        self.rumours = 0
        self.total_rumours = 0
        self.conversions = 0
        self.headlines_lit = set()
        self.headlines_collected_cycle = 0
        self.total_headlines = 0
        self.super_lit = False
        self.super_collected = 0
        self.mode_points = 0
        self.drain_active = False
        self.back_page_lit = False
        self.last_super_value = 0

        self.case_files = self.get_case_file_bonuses()
        self.base_pop_value = 75_000 if self.has_case_file("bigger_jackpots") else 50_000
        self.base_spin_value = 150_000 if self.has_case_file("bigger_jackpots") else 100_000
        self.base_headline_value = 250_000 if self.has_case_file("bigger_jackpots") else 200_000
        self.drain_ms = 3000 if self.has_case_file("more_time") else 2000

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_completed"] = 1
        player[f"{self.MODE_KEY}_mode_points"] = 0
        player[f"{self.MODE_KEY}_rumours"] = 0
        player[f"{self.MODE_KEY}_total_rumours"] = 0
        player[f"{self.MODE_KEY}_conversions"] = 0
        player[f"{self.MODE_KEY}_headlines_lit"] = 0
        player[f"{self.MODE_KEY}_headlines_collected"] = 0
        player[f"{self.MODE_KEY}_super_value"] = self._super_value()
        player[f"{self.MODE_KEY}_super_collected"] = 0
        player[f"{self.MODE_KEY}_back_page_value"] = 0
        player[f"{self.MODE_KEY}_back_page_collected"] = 0
        player[f"{self.MODE_KEY}_drain_active"] = 0

        self.add_mode_event_handler("master_plan_pop_hit", self._pop_hit)
        self.add_mode_event_handler("master_plan_spinner_hit", self._spinner_hit)
        self.add_mode_event_handler("master_plan_saucer_1_hit", self._saucer_hit, saucer=1)
        self.add_mode_event_handler("master_plan_saucer_2_hit", self._saucer_hit, saucer=2)
        self.add_mode_event_handler("master_plan_saucer_3_hit", self._saucer_hit, saucer=3)
        self.add_mode_event_handler("master_plan_vuk_hit", self._vuk_hit)
        self.add_mode_event_handler("master_plan_back_page_hit", self._back_page_hit)
        self.add_mode_event_handler(f"{self.MODE_KEY}_complete_request", self._complete_mode)
        self.add_mode_event_handler(f"{self.MODE_KEY}_fail_request", self._complete_mode)

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        self.publish_case_file_bonus_events("master_plan")
        self.publish_active_case_file_helpers([
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("bigger_jackpots", "BIGGER FRONT PAGE VALUES"),
            ("more_time", "RUMOURS LAST LONGER"),
            ("shot_assist", "HEADLINE ASSIST ACTIVE"),
            ("more_jackpots", "BACK PAGE BONUS AVAILABLE"),
        ])

        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="FRONT PAGE FRAME-UP",
            message_mode_subtitle="POPS BUILD RUMOURS",
        )
        self._update_lights()
        self._sync_vars()

    def mode_stop(self, **kwargs):
        self.delay.remove("master_plan_rumour_drain")
        self.delay.remove("master_plan_back_page_timeout")
        self.clear_active_case_file_helpers()
        self.machine.events.post("master_plan_clear_lights")
        super().mode_stop(**kwargs)

    def _pop_hit(self, **kwargs):
        if self.mode_done:
            return

        self.rumours += 1
        self.total_rumours += 1
        self._score(self.base_pop_value)
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="RUMOUR ADDED",
            message_mode_subtitle=f"{self.rumours} RUMOURS",
        )
        self._sync_vars()

    def _spinner_hit(self, **kwargs):
        if self.mode_done or self.super_lit:
            return

        if len(self.headlines_lit) >= 3:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="SAUCERS FULL",
                message_mode_subtitle="COLLECT HEADLINES",
            )
            return

        if self.rumours < 2:
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="NEED RUMOURS",
                message_mode_subtitle="HIT POPS",
            )
            return

        open_saucers = [s for s in self.SAUCERS if s not in self.headlines_lit]
        if not open_saucers:
            return

        saucer = random.choice(open_saucers)
        self.rumours -= 2
        self.conversions += 1
        self.headlines_lit.add(saucer)
        self._score(self.base_spin_value)
        self.machine.events.post(
            "master_plan_headline_lit",
            saucer=saucer,
            headlines_lit=len(self.headlines_lit),
        )
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="HEADLINE PRINTED",
            message_mode_subtitle=f"SAUCER {saucer} LIT",
        )
        self._update_lights()
        self._sync_vars()

    def _saucer_hit(self, saucer, **kwargs):
        if self.mode_done:
            return

        self.machine.events.post(f"kickout_saucer_{saucer}")

        if saucer not in self.headlines_lit or self.super_lit:
            return

        self._collect_headline(saucer, assisted=False)

        if self.has_case_file("shot_assist") and len(self.headlines_lit) >= 1:
            # If two or more headlines were lit before collection, one remains now.
            assisted_saucer = sorted(self.headlines_lit)[0]
            self._collect_headline(assisted_saucer, assisted=True)

        self._check_super_lit()
        self._update_lights()
        self._sync_vars()

    def _collect_headline(self, saucer, assisted=False):
        if saucer not in self.headlines_lit:
            return

        self.headlines_lit.remove(saucer)
        self.headlines_collected_cycle += 1
        self.total_headlines += 1
        self._score(self.base_headline_value)
        self.machine.events.post(
            "master_plan_headline_collected",
            saucer=saucer,
            assisted=assisted,
            headlines_collected=self.headlines_collected_cycle,
        )
        if assisted:
            title = "SHOT ASSIST"
            subtitle = "EXTRA HEADLINE SCORED"
        else:
            title = "HEADLINE COLLECTED"
            subtitle = f"{self.headlines_collected_cycle} OF 3"
        self.machine.events.post("show_mode_message", message_mode_title=title, message_mode_subtitle=subtitle)

    def _check_super_lit(self):
        if self.super_lit:
            return

        if self.headlines_collected_cycle >= 3:
            self.super_lit = True
            self.last_super_value = self._super_value()
            self.machine.events.post("rooftop_diverter_open")
            self.machine.events.post("master_plan_super_lit", value=self.last_super_value)
            self.machine.events.post(
                "show_mode_jackpot",
                message_mode_title="SUPER LIT",
                message_mode_subtitle="SHOOT DAILY BUGLE VUK",
                message_mode_value=self.last_super_value,
            )

    def _vuk_hit(self, **kwargs):
        if self.mode_done:
            return

        if not self.super_lit:
            self.machine.events.post("up_kick")
            return

        value = self._super_value()
        self.last_super_value = value
        self.super_collected += 1
        self._score(value)
        self.super_lit = False
        self.headlines_collected_cycle = 0
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("up_kick")
        self.machine.events.post("master_plan_super_collected", value=value)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="FRONT PAGE SUPER",
            message_mode_subtitle="THE BIG MAN EXPOSED",
            message_mode_value=value,
        )

        if self.has_case_file("more_jackpots"):
            self._start_back_page_bonus(value)

        self._start_rumour_drain()
        self._update_lights()
        self._sync_vars()

    def _start_rumour_drain(self):
        self.drain_active = True
        self.delay.remove("master_plan_rumour_drain")
        self.delay.add(
            name="master_plan_rumour_drain",
            ms=self.drain_ms,
            callback=self._rumour_drain_tick,
        )

    def _rumour_drain_tick(self, **kwargs):
        if self.mode_done or not self.drain_active:
            return

        if self.rumours > 0:
            self.rumours -= 1
            self.machine.events.post(
                "show_mode_message",
                message_mode_title="FALSE RUMOUR",
                message_mode_subtitle=f"{self.rumours} LEFT",
            )
            self._sync_vars()

        if self.rumours <= 0:
            self._complete_mode()
            return

        self.delay.add(
            name="master_plan_rumour_drain",
            ms=self.drain_ms,
            callback=self._rumour_drain_tick,
        )

    def _start_back_page_bonus(self, super_value):
        self.back_page_lit = True
        back_page_value = super_value // 2
        self.machine.game.player[f"{self.MODE_KEY}_back_page_value"] = back_page_value
        self.machine.events.post("master_plan_back_page_lit", value=back_page_value)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="BACK PAGE BONUS",
            message_mode_subtitle="UPPER CENTER TARGET",
            message_mode_value=back_page_value,
        )
        self.delay.remove("master_plan_back_page_timeout")
        self.delay.add(
            name="master_plan_back_page_timeout",
            ms=10000,
            callback=self._back_page_timeout,
        )

    def _back_page_hit(self, **kwargs):
        if self.mode_done or not self.back_page_lit:
            return

        value = self.machine.game.player[f"{self.MODE_KEY}_back_page_value"]
        self.back_page_lit = False
        self.delay.remove("master_plan_back_page_timeout")
        self._score(value)
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_back_page_collected"] += 1
        self.machine.events.post("master_plan_back_page_collected", value=value)
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="BACK PAGE BONUS",
            message_mode_subtitle="EXTRA EDITION",
            message_mode_value=value,
        )
        self._update_lights()
        self._sync_vars()

    def _back_page_timeout(self, **kwargs):
        if self.mode_done:
            return
        self.back_page_lit = False
        self.machine.events.post("master_plan_back_page_expired")
        self.machine.events.post(
            "show_mode_message",
            message_mode_title="BACK PAGE MISSED",
            message_mode_subtitle="KEEP THE STORY ALIVE",
        )
        self._update_lights()
        self._sync_vars()

    def _super_value(self):
        return self.base_headline_value * 3

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points
        player[f"{self.MODE_KEY}_mode_points"] = self.mode_points

    def _complete_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("master_plan_rumour_drain")
        self.delay.remove("master_plan_back_page_timeout")
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_completed"] = 1 if self.super_collected > 0 else 0
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")

    def _fail_mode(self, **kwargs):
        if self.mode_done:
            return
        self.mode_done = True
        self.delay.remove("master_plan_rumour_drain")
        self.delay.remove("master_plan_back_page_timeout")
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_completed"] = 1
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post(f"{self.MODE_KEY}_mode_complete")

    def _update_lights(self):
        self.machine.events.post("master_plan_clear_lights")

        for saucer in self.headlines_lit:
            self.machine.events.post(f"master_plan_saucer_{saucer}_lit")

        if self.super_lit:
            self.machine.events.post("master_plan_super_lit_show")

        if self.back_page_lit:
            self.machine.events.post("master_plan_back_page_lit_show")

    def _sync_vars(self):
        player = self.machine.game.player
        player[f"{self.MODE_KEY}_mode_points"] = self.mode_points
        player[f"{self.MODE_KEY}_rumours"] = self.rumours
        player[f"{self.MODE_KEY}_total_rumours"] = self.total_rumours
        player[f"{self.MODE_KEY}_conversions"] = self.conversions
        player[f"{self.MODE_KEY}_headlines_lit"] = len(self.headlines_lit)
        player[f"{self.MODE_KEY}_headlines_collected"] = self.total_headlines
        player[f"{self.MODE_KEY}_cycle_headlines"] = self.headlines_collected_cycle
        player[f"{self.MODE_KEY}_super_value"] = self._super_value()
        player[f"{self.MODE_KEY}_super_collected"] = self.super_collected
        player[f"{self.MODE_KEY}_drain_active"] = 1 if self.drain_active else 0
