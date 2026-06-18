from mpf.core.mode import Mode
from modes.common.case_file_mixin import CaseFileMixin
from mpf.core.delays import DelayManager
import random

# rollovers to lock arms (1 to 4)
# spinner increases JP multiplier, enables jackpot
# collect JP = base*spins*(5-locks) (resets spins)
# JP collect adds breakout targets (to avoid)
# breakout targets release an arm
# after 2 jackpots, timed arm release starts
# all arms released, mode ends
"""
    "title": "DOC OCK",
    "intro_1": "Lock tentacle arms with rollovers.",
    "intro_2": "Shoot web targets for Jackpot.",
    "intro_3": "Spinner increases the multiplier.",
    "summary_title_complete": "DOC OCK DEFEATED",
    "summary_title_failed": "DOC OCK ESCAPED",
    "stat_1_label": "ARMS LOCKED",
    "stat_1_var": "doc_ock_max_arms_locked",
    "stat_2_label": "JACKPOTS",
    "stat_2_var": "doc_ock_jackpots",
    "points_var": "doc_ock_mode_points",
    "completed_var": "doc_ock_completed",
"""
class doc_ock(CaseFileMixin, Mode):

    JACKPOTS_BEFORE_TIMED_RELEASE = 2
    DEFAULT_ARM_RELEASE_DELAY_MS = 10_000
    MORE_TIME_ARM_RELEASE_DELAY_ADD_MS = 2_000
    TIMED_RELEASE_DELAY_NAME = "doc_ock_timed_release"
    MAX_BREAKOUT_TARGETS = 6

    LANE_LIGHTS = {
        1: "l_left_outlane",
        2: "l_left_inlane",
        3: "l_right_inlane",
        4: "l_right_outlane",
    }
    

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.delay = DelayManager(self.machine)
        self.doc_ock_arm_release_delay_ms = self.DEFAULT_ARM_RELEASE_DELAY_MS
        self.timed_release_running = False

        self.doc_ock_jackpot_unlit_value = 25000       
        self.doc_ock_jackpot_base_value = 100000
        self.doc_ock_jackpot_spinner_multi = 1
        self.doc_ock_arm_locked_score = 50000
        self.doc_ock_arm_relocked_score = 10000

        # Start with one arm already disabled/locked.
        # False = free, True = locked
        self.locked_arms = [True, False, False, False]

        self.jackpot_lit = 1
        self.jackpots_collected = 0
        self.active_breakouts = set()
        self.doc_ock_max_arms_locked = 1
        self.doc_ock_jackpots = 0
        self.doc_ock_mode_points = 0
        self.first_jackpot_maxed = False
        
        self.case_files = self.get_case_file_bonuses()
        self._apply_case_file_bonuses()
        self.publish_case_file_bonus_events("doc_ock")
        self.publish_active_case_file_helpers([
            ("more_jackpots", "EXTRA BREAKOUT JACKPOT AVAILABLE"),
            ("bigger_jackpots", "BIGGER DOC OCK JACKPOTS"),
            ("more_time", "ARM RELEASE DELAYED"),
            ("safety_net", "10 SECOND BALL SAVE ACTIVE"),
            ("shot_assist", "EXTRA ARM LOCKED"),
        ])

        self.add_mode_event_handler("doc_ock_spinner_hit", self.doc_ock_spinner)
        self.add_mode_event_handler("doc_ock_start_arms", self.doc_ock_start_arms)
        self.add_mode_event_handler("doc_ock_rotate_left", self.rotate_left)
        self.add_mode_event_handler("doc_ock_rotate_right", self.rotate_right)
        self.add_mode_event_handler("doc_ock_jackpot_request", self.jackpot_request)
        self.add_mode_event_handler("doc_ock_start_timed_release", self.start_timed_release)
        self.add_mode_event_handler("doc_ock_stop_timed_release", self.stop_timed_release)

        for arm in [1, 2, 3, 4]:
            self.add_mode_event_handler(
                f"doc_ock_arm_{arm}_hit",
                self.arm_hit,
                arm=arm
            )

        for breakout in [1, 2, 3, 4, 5, 6]:
            self.add_mode_event_handler(
                f"doc_ock_breakout_{breakout}_request",
                self.breakout_hit,
                breakout=breakout
            )
            
        self.update_player_vars()

        self.machine.events.post("rooftop_diverter_close")
        self.machine.events.post("doc_ock_startup_complete")
        self.machine.events.post("show_mode_message", message_mode_title="LOCK THE ARMS", message_mode_subtitle="ROLLOVERS THEN WEB TARGETS")


    def mode_stop(self, **kwargs):
        self.stop_timed_release()
        self.clear_active_case_file_helpers()
        super().mode_stop(**kwargs)

    def _apply_case_file_bonuses(self):
        if self.has_case_file("more_jackpots"):
            self.JACKPOTS_BEFORE_TIMED_RELEASE += 2

        if self.has_case_file("bigger_jackpots"):
            self.doc_ock_jackpot_base_value += 100000

        if self.has_case_file("more_time"):
            self.doc_ock_arm_release_delay_ms += self.MORE_TIME_ARM_RELEASE_DELAY_ADD_MS

        if self.has_case_file("safety_net"):
            self.machine.events.post("start_case_file_ball_save")

        if self.has_case_file("shot_assist"):
            self.first_jackpot_maxed = True

    def doc_ock_start_arms(self, **kwargs):
        self.refresh_lane_lights()
        self.check_jackpot_lit()

    def doc_ock_spinner(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return
        self.jackpot_lit = 1
        self.check_jackpot_lit()
        self.doc_ock_jackpot_spinner_multi = self.doc_ock_jackpot_spinner_multi + 1
        self.update_player_vars()
        
        self.machine.events.post(
            "doc_ock_spinner_multiplier_increased",
            multiplier=self.doc_ock_jackpot_spinner_multi
        )
        self.machine.events.post("show_mode_message", message_mode_title="SPINNER MULTIPLIER", message_mode_subtitle="DOC OCK JACKPOT", message_mode_value=f"{self.doc_ock_jackpot_spinner_multi}X")

    def rotate_left(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return
        self.locked_arms = self.locked_arms[1:] + self.locked_arms[:1]
        self.refresh_lane_lights()

    def rotate_right(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return
        self.locked_arms = self.locked_arms[-1:] + self.locked_arms[:-1]
        self.refresh_lane_lights()

    def refresh_lane_lights(self):
        for arm in [1, 2, 3, 4]:
            if self.locked_arms[arm-1]:
                self.machine.events.post(f"doc_ock_arm_{arm}_solid")
            else:
                self.machine.events.post(f"doc_ock_arm_{arm}_pulse")

    def arm_hit(self, arm, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return
        self.jackpot_lit = 1        
        #already locked
        if self.locked_arms[arm-1]:
            self.machine.game.player["score"] += self.doc_ock_arm_relocked_score
            self.doc_ock_mode_points += self.doc_ock_arm_relocked_score
            self.machine.events.post("show_mode_message", message_mode_title="ARM ALREADY LOCKED", message_mode_subtitle="KEEP BUILDING JACKPOT")
            return

        self.machine.game.player["score"] += self.doc_ock_arm_locked_score
        self.doc_ock_mode_points += self.doc_ock_arm_locked_score

        self.locked_arms[arm-1] = True
        self.refresh_lane_lights()

        self.doc_ock_max_arms_locked += 1
        self.machine.game.player["doc_ock_max_arms_locked"] = self.doc_ock_max_arms_locked

        self.machine.events.post("doc_ock_arm_locked_score")
        self.machine.events.post("show_mode_message", message_mode_title="ARM LOCKED", message_mode_subtitle=f"{sum(self.locked_arms)} ARMS LOCKED")
        #self.check_jackpot_lit()
        self.update_player_vars()        

    def check_jackpot_lit(self):
        if sum(self.locked_arms) > 0:
            self.machine.events.post("doc_ock_jackpot_lit")

    def jackpot_request(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return
        if self.jackpot_lit == 0:
            self.machine.events.post("doc_ock_jackpot_not_lit")
            self.machine.events.post("show_mode_message", message_mode_title="LOCK ARMS FIRST", message_mode_subtitle="WEB TARGET NOT READY")
            self.machine.game.player["score"] += self.doc_ock_jackpot_unlit_value
            self.doc_ock_mode_points += self.doc_ock_jackpot_unlit_value
            return
            
        locked = sum(self.locked_arms)
        if locked <= 0:
            return

        jp_value = self.doc_ock_jackpot_base_value * (5-locked) * self.doc_ock_jackpot_spinner_multi
        
        if self.first_jackpot_maxed == True:
            self.first_jackpot_maxed = False
            jp_value = self.doc_ock_jackpot_base_value * 100  #maxed value 

        self.machine.game.player["score"] += jp_value
        self.machine.game.player["doc_ock_last_jackpot"] = jp_value
        self.doc_ock_mode_points += jp_value
        self.machine.game.player["doc_ock_mode_points"] = self.doc_ock_mode_points

        self.doc_ock_jackpots += 1
        self.machine.game.player["doc_ock_jackpots"] = self.doc_ock_jackpots
    
        self.machine.events.post("doc_ock_jackpot_award")
        self.machine.events.post("show_mode_jackpot", message_mode_title="DOC OCK JACKPOT", message_mode_subtitle="TENTACLE LOCKDOWN", message_mode_value=jp_value)
        #self.machine.events.post("doc_ock_jackpot_collected")

        self.doc_ock_jackpot_spinner_multi = 1
        self.jackpots_collected += 1
        self.jackpot_lit = 0

        self.spawn_breakout_target()
        self.update_player_vars()        

        if self.jackpots_collected >= self.JACKPOTS_BEFORE_TIMED_RELEASE:
            self.machine.events.post("doc_ock_start_timed_release")

        self.check_mode_over()

    def spawn_breakout_target(self):
        if len(self.active_breakouts) >= self.MAX_BREAKOUT_TARGETS:
            return

        available = [1, 2, 3, 4, 5, 6]
        random.shuffle(available)

        for target in available:
            if target not in self.active_breakouts:
                self.active_breakouts.add(target)
                self.machine.events.post(f"doc_ock_breakout_{target}_lit")
                self.machine.events.post("show_mode_message", message_mode_title="BREAKOUT LIT", message_mode_subtitle=f"TARGET {target}")
                return

    def breakout_hit(self, breakout, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True: return

        if breakout not in self.active_breakouts:
            return

        self.release_random_locked_arm()
        self.update_player_vars()                
        self.machine.events.post("doc_ock_breakout_hit")
        self.machine.events.post("show_mode_message", message_mode_title="ARM RELEASED", message_mode_subtitle="LOCK IT AGAIN")
        self.check_mode_over()

    def start_timed_release(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True:
            return

        if self.jackpots_collected < self.JACKPOTS_BEFORE_TIMED_RELEASE:
            return

        if sum(self.locked_arms) <= 0:
            return

        self.timed_release_running = True
        self.machine.game.player["doc_ock_arm_release_delay_ms"] = self.doc_ock_arm_release_delay_ms
        self.machine.game.player["doc_ock_arm_release_delay_seconds"] = self.doc_ock_arm_release_delay_ms / 1000
        self.machine.events.post(
            "doc_ock_timed_release_started",
            delay_ms=self.doc_ock_arm_release_delay_ms,
            delay_seconds=self.doc_ock_arm_release_delay_ms / 1000,
        )
        self.machine.events.post("show_mode_countdown", message_mode_title="TIMED RELEASE", message_mode_subtitle="ARM BREAKING FREE", message_mode_seconds=int(self.doc_ock_arm_release_delay_ms / 1000))
        self.delay.remove(self.TIMED_RELEASE_DELAY_NAME)
        self.delay.add(
            name=self.TIMED_RELEASE_DELAY_NAME,
            ms=self.doc_ock_arm_release_delay_ms,
            callback=self.timed_release,
        )

    def stop_timed_release(self, **kwargs):
        self.timed_release_running = False
        if hasattr(self, "delay"):
            self.delay.remove(self.TIMED_RELEASE_DELAY_NAME)

    def timed_release(self, **kwargs):
        if self.machine.game.player["villain_mode_in_summary"] == True:
            self.stop_timed_release()
            return

        if self.jackpots_collected < self.JACKPOTS_BEFORE_TIMED_RELEASE:
            self.stop_timed_release()
            return

        if not self.timed_release_running:
            return

        released = self.release_random_locked_arm()

        if not released:
            self.stop_timed_release()
            self.check_mode_over()
            return

        self.update_player_vars()
        self.machine.events.post("doc_ock_timed_release_complete")
        self.machine.events.post("doc_ock_breakout_hit")
        self.machine.events.post("show_mode_message", message_mode_title="ARM RELEASED", message_mode_subtitle="DOC OCK BREAKS FREE")

        if self.check_mode_over():
            self.stop_timed_release()
            return

        self.start_timed_release()

    def release_random_locked_arm(self):
        locked = [i for i, val in enumerate(self.locked_arms) if val]

        if not locked:
            return False

        arm = random.choice(locked)
        self.locked_arms[arm] = False
        self.refresh_lane_lights()
        return True

    def check_mode_over(self):
        if sum(self.locked_arms) <= 0:
            self.machine.events.post("doc_ock_mode_complete")
            self.machine.events.post("doc_ock_stop_timed_release")
            return True
        return False

    def update_player_vars(self):
        player = self.machine.game.player

        player["doc_ock_locked_arms"] = sum(self.locked_arms)
        player["doc_ock_spinner_multi"] = self.doc_ock_jackpot_spinner_multi
        player["doc_ock_jackpots_collected"] = self.jackpots_collected
        player["doc_ock_active_breakouts"] = len(self.active_breakouts)

        player["doc_ock_next_jackpot"] = self.calculate_next_jackpot()

        self.machine.events.post(
            "doc_ock_next_jackpot_changed",
            value=player["doc_ock_next_jackpot"],
            locked_arms=player["doc_ock_locked_arms"],
            multiplier=player["doc_ock_spinner_multi"],
            jackpot_lit=self.jackpot_lit,
        )
    
    def calculate_next_jackpot(self):
        locked = sum(self.locked_arms)

        if locked <= 0:
            return 0

        if self.jackpot_lit == 0:
            return 0

        return (
            self.doc_ock_jackpot_base_value
            * (5 - locked)
            * self.doc_ock_jackpot_spinner_multi
        )