from mpf.core.mode import Mode


class BonusLanes(Mode):

    MAX_BONUS_COUNT = 75
    BONUS_ADD_VALUE = 1
    MAX_MULTIPLIER = 5

    LANE_LIGHTS = {
        1: "l_left_outlane",
        2: "l_left_inlane",
        3: "l_right_inlane",
        4: "l_right_outlane",
    }

    BONUS_LIGHTS = [
        (20, "l_20k"),
        (10, "l_10k"),
        (9, "l_9k"),
        (8, "l_8k"),
        (7, "l_7k"),
        (6, "l_6k"),
        (5, "l_5k"),
        (4, "l_4k"),
        (3, "l_3k"),
        (2, "l_2k"),
        (1, "l_1k"),
    ]

    BONUS_X_LIGHTS = {
        2: "l_2x",
        3: "l_3x",
        4: "l_4x",
        5: "l_5x",
    }


    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.completed = [False, False, False, False]
        self.center_web_lit = False
        self.left_web_lit = False

        self.add_mode_event_handler("bonus_lanes_start", self.blane_start)
        self.add_mode_event_handler("bonus_count_add", self.add_bonus_count)
        self.add_mode_event_handler("bonus_lanes_rotate_left", self.rotate_left)
        self.add_mode_event_handler("bonus_lanes_rotate_right", self.rotate_right)

        for lane in range(1, 5):
            self.add_mode_event_handler(
                f"bonus_lane_{lane}_hit",
                self.lane_hit,
                lane=lane
            )

        self.add_mode_event_handler("bonus_center_web_request", self.center_web_hit)
        self.add_mode_event_handler("bonus_left_web_request", self.left_web_hit)
        self.add_mode_event_handler("bonus_center_web_timeout", self.center_web_timeout)
        self.add_mode_event_handler("bonus_left_web_timeout", self.left_web_timeout)
        
        self.add_mode_event_handler(
            "bonus_left_bank_complete",
            self.add_bonus_count,
            amount=3
        )

        self.add_mode_event_handler(
            "bonus_right_bank_complete",
            self.add_bonus_count,
            amount=5
        )     

        self.add_mode_event_handler("custom_bonus_base_tick", self.update_bonus_lights)        
        

    def blane_start(self, **kwargs):
        player = self.machine.game.player

        player["bonus_count"] = 0
        player["bonus_multiplier"] = 1

        self.refresh_lane_lights()

    def add_bonus_count(self, amount=None, **kwargs):

        if amount is None:
            amount = self.BONUS_ADD_VALUE

        player = self.machine.game.player
        current = player["bonus_count"]

        if current < self.MAX_BONUS_COUNT:
            player["bonus_count"] = min(
                self.MAX_BONUS_COUNT,
                current + amount
            )
            
        self.update_bonus_lights()            

    def rotate_left(self, **kwargs):
        self.completed = self.completed[1:] + self.completed[:1]
        self.refresh_lane_lights()

    def rotate_right(self, **kwargs):
        self.completed = self.completed[-1:] + self.completed[:-1]
        self.refresh_lane_lights()

    def lane_hit(self, lane, **kwargs):
        index = lane - 1

        if self.completed[index]:
            return

        self.completed[index] = True
        self.refresh_lane_lights()

        if all(self.completed):
            self.light_center_web()

    def light_center_web(self):
        self.center_web_lit = True
        self.left_web_lit = False
        self.machine.events.post("bonus_center_web_lit")

    def center_web_hit(self, **kwargs):
        if not self.center_web_lit:
            self.add_bonus_count()
            return

        self.center_web_lit = False
        self.left_web_lit = True

        self.machine.events.post("bonus_center_web_collected")
        self.machine.events.post("bonus_left_web_lit")

    def left_web_hit(self, **kwargs):
        if not self.left_web_lit:
            self.add_bonus_count()
            return

        self.left_web_lit = False
        self.advance_bonus_multiplier()

        self.completed = [False, False, False, False]
        self.refresh_lane_lights()

        self.machine.events.post("bonus_left_web_collected")

    def advance_bonus_multiplier(self):
        player = self.machine.game.player
        current = player["bonus_multiplier"]

        if current < self.MAX_MULTIPLIER:
            player["bonus_multiplier"] = current + 1

        self.update_bonus_lights()            


    def center_web_timeout(self, **kwargs):
        self.center_web_lit = False

    def left_web_timeout(self, **kwargs):
        self.left_web_lit = False

    def refresh_lane_lights(self):
        for lane, light_name in self.LANE_LIGHTS.items():
            light = self.machine.lights.get(light_name)

            if not light:
                continue

            if self.completed[lane - 1]:
                light.on(color="white")
            else:
                light.off()

        self.machine.events.post("bonus_show_lanes")
        
        
    def update_bonus_lights(self, **kwargs):
        player = self.machine.game.player
        bonus_count = player["bonus_count"]

        remaining = min(bonus_count, 75)

        # Turn all bonus lights off first
        for value, light_name in self.BONUS_LIGHTS:
            light = self.machine.lights.get(light_name)
            if light:
                light.off()

        # Light additive combo
        for value, light_name in self.BONUS_LIGHTS:
            if remaining >= value:
                light = self.machine.lights.get(light_name)
                if light:
                    light.on(color="white")
                remaining -= value

        player = self.machine.game.player
        mx = player["bonus_multiplier"]

        for value, light_name in self.BONUS_X_LIGHTS.items():
            light = self.machine.lights.get(light_name)                
            if light:
                if value == mx:
                    light.on(color="white")
                else:
                    light.off()




        