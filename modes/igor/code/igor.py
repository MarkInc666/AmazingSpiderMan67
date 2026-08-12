import random

from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin


class Igor(CaseFileMixin, Mode):
    """Igor: an endless precision/avoidance score attack.

    Each authored set has one flashing-green Jackpot shot and nearby solid-red
    defense shots. Any scored shot immediately chooses a different set. The
    mode ends on the fifth bad shot (seventh with More Jackpots) or ball drain.
    """

    MODE_KEY = "igor"
    DISPLAY_NAME = "Igor"

    STARTING_JACKPOT = 100_000
    JACKPOT_STEP = 25_000
    BIGGER_JACKPOT_STEP = 50_000
    BAD_SHOT_SCORE = 25_000
    NORMAL_BAD_SHOT_LIMIT = 5
    MORE_JACKPOTS_BAD_SHOT_LIMIT = 7
    FINAL_MESSAGE_MS = 2_000

    SHOT_SETS = {
        1: {
            "good": "right_bank",
            "bad": ("pops",),
        },
        2: {
            "good": "center_web",
            "bad": ("pops",),
        },
        3: {
            "good": "upper_center",
            "bad": ("upper_left", "upper_right"),
        },
        4: {
            "good": "spinner",
            "bad": ("left_web", "right_bank"),
        },
        5: {
            "good": "left_bank",
            "bad": ("left_web", "spinner", "pops"),
        },
    }

    SHOT_GROUPS = (
        "right_bank",
        "left_bank",
        "pops",
        "center_web",
        "upper_center",
        "upper_left",
        "upper_right",
        "spinner",
        "left_web",
    )

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.mode_done = False
        self.current_set = None
        self.jackpots = 0
        self.bad_shots = 0
        self.mode_points = 0
        self.biggest_jackpot = 0
        self.next_jackpot = self.STARTING_JACKPOT
        self.shot_assist_available = False

        self.case_files = self.get_case_file_bonuses()
        self.jackpot_step = (
            self.BIGGER_JACKPOT_STEP
            if self.has_case_file("bigger_jackpots")
            else self.JACKPOT_STEP
        )
        self.bad_shot_limit = (
            self.MORE_JACKPOTS_BAD_SHOT_LIMIT
            if self.has_case_file("more_jackpots")
            else self.NORMAL_BAD_SHOT_LIMIT
        )
        self.shot_assist_available = self.has_case_file("shot_assist")
        self.ball_save_seconds = self._ball_save_seconds()

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 1
        self._sync_vars()

        self.publish_case_file_bonus_events(self.MODE_KEY)
        self.publish_active_case_file_helpers([
            ("more_jackpots", "7 BAD SHOTS BEFORE IGOR WINS"),
            ("bigger_jackpots", "JACKPOTS GROW BY 50K"),
            ("more_time", "BALL SAVE EXTENDED TO 20 SECONDS"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "FIRST BAD SHOT BECOMES A JACKPOT"),
        ])

        for group in self.SHOT_GROUPS:
            self.add_mode_event_handler(
                f"igor_{group}_hit",
                self._shot_hit,
                group=group,
            )

        self.add_mode_event_handler("igor_complete_request", self._finish_mode)
        self.add_mode_event_handler("igor_fail_request", self._begin_defeat)

        self.machine.events.post("igor_startup_complete")
        if self.ball_save_seconds > 0:
            self.machine.events.post("igor_enable_ball_save")

        self._select_next_set()
        self._show_message(
            "IGOR'S DEFENSES",
            "FLASHING GREEN IS GOOD",
            reminder=True,
        )

    def mode_stop(self, **kwargs):
        self.delay.remove("igor_final_message")
        self.machine.events.post("igor_all_shot_lights_off")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("hide_mode_status")
        self.machine.events.post("cancel_mode_message_reminder")
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _ball_save_seconds(self):
        if self.has_case_file("more_time"):
            return 20
        if self.has_case_file("safety_net"):
            return 10
        return 0

    def _shot_hit(self, group, **kwargs):
        if self.mode_done or self.current_set is None:
            return

        shot_set = self.SHOT_SETS[self.current_set]
        if group == shot_set["good"]:
            self._collect_jackpot(group)
        elif group in shot_set["bad"]:
            if self.shot_assist_available:
                self.shot_assist_available = False
                self.machine.events.post(
                    "igor_case_file_shot_assist_used",
                    group=group,
                )
                self._collect_jackpot(group, assisted=True)
            else:
                self._collect_bad_shot(group)
        else:
            return

        if not self.mode_done:
            self._select_next_set()

    def _collect_jackpot(self, group, assisted=False):
        award = self.next_jackpot
        self._score(award)
        self.jackpots += 1
        self.biggest_jackpot = max(self.biggest_jackpot, award)
        self.next_jackpot += self.jackpot_step
        self._sync_vars()

        self.machine.events.post(
            "igor_jackpot_awarded",
            group=group,
            value=award,
            jackpots=self.jackpots,
            assisted=int(assisted),
        )
        self.machine.events.post(
            "show_mode_jackpot",
            message_mode_title="JACKPOT",
            message_mode_subtitle="SHOT ASSIST" if assisted else "",
            message_mode_value=award,
            message_mode_seconds="",
        )

    def _collect_bad_shot(self, group):
        self._score(self.BAD_SHOT_SCORE)
        self.bad_shots += 1
        self._sync_vars()

        self.machine.events.post(
            "igor_bad_shot_awarded",
            group=group,
            value=self.BAD_SHOT_SCORE,
            bad_shots=self.bad_shots,
            bad_shot_limit=self.bad_shot_limit,
        )

        if self.bad_shots >= self.bad_shot_limit:
            self._begin_defeat()
            return

        self._show_message(
            "BAD SHOT",
            f"{self.bad_shots} / {self.bad_shot_limit}",
            value=self.BAD_SHOT_SCORE,
        )

    def _select_next_set(self):
        choices = [
            set_number
            for set_number in self.SHOT_SETS
            if set_number != self.current_set
        ]
        self.current_set = random.choice(choices)
        shot_set = self.SHOT_SETS[self.current_set]

        self.machine.events.post("igor_all_shot_lights_off")
        self.machine.events.post(f"igor_good_{shot_set['good']}")
        for group in shot_set["bad"]:
            self.machine.events.post(f"igor_bad_{group}")

        if self.current_set == 3:
            self.machine.events.post("rooftop_diverter_open")
        else:
            self.machine.events.post("rooftop_diverter_close")

        self.machine.events.post(
            "igor_shot_set_selected",
            set_number=self.current_set,
            good_group=shot_set["good"],
            bad_groups=",".join(shot_set["bad"]),
        )
        self._update_status()

    def _begin_defeat(self, **kwargs):
        if self.mode_done:
            return

        self.mode_done = True
        self.machine.events.post("igor_all_shot_lights_off")
        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("hide_mode_status")
        self._sync_vars(update_status=False)
        self._show_message("IGOR'S DEFENSES WIN", "", seconds="2")
        self.delay.add(
            name="igor_final_message",
            ms=self.FINAL_MESSAGE_MS,
            callback=self._finish_mode,
        )

    def _finish_mode(self, **kwargs):
        if not self.mode_done:
            self.mode_done = True

        player = self.machine.game.player
        player[f"{self.MODE_KEY}_state"] = 2
        self._sync_vars(update_status=False)
        self.machine.events.post("igor_mode_complete")

    def _score(self, points):
        player = self.machine.game.player
        player["score"] += points
        self.mode_points += points

    def _sync_vars(self, update_status=True):
        player = self.machine.game.player
        player["active_mode_points"] = self.mode_points
        player["active_mode_hits"] = self.jackpots
        player["active_mode_major_hits"] = self.bad_shots
        player["igor_biggest_jackpot"] = self.biggest_jackpot
        player["igor_ball_save_seconds"] = self.ball_save_seconds
        if update_status and not self.mode_done:
            self._update_status()

    def _update_status(self):
        self.machine.events.post(
            "show_mode_status",
            mode_status_title=f"NEXT JACKPOT {self.next_jackpot:,}",
            mode_status_value=f"BAD SHOTS {self.bad_shots} / {self.bad_shot_limit}",
        )

    def _show_message(
        self,
        title,
        subtitle="",
        value="",
        seconds="",
        reminder=False,
    ):
        self.machine.events.post(
            "show_mode_message",
            message_mode_title=title,
            message_mode_subtitle=subtitle,
            message_mode_value=value,
            message_mode_seconds=seconds,
            reminder=reminder,
        )
