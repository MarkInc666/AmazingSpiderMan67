from mpf.core.mode import Mode


class Parafino(Mode):

    MAX_HEAT = 3
    COOL_DELAY_MS = 5000
    MELTDOWN_JACKPOT_BASE = 500000

    ZONES = ["left", "center", "right"]

    SAUCER_BY_ZONE = {
        "left": 1,
        "center": 2,
        "right": 3,
    }

    ZONE_BY_SAUCER = {
        1: "left",
        2: "center",
        3: "right",
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.heat = {
            "left": 0,
            "center": 0,
            "right": 0,
        }

        # Saucer add-a-ball can be earned only once per zone.
        self.add_a_ball_earned = {
            "left": False,
            "center": False,
            "right": False,
        }

        # Saucer is currently lit and waiting to be collected.
        self.saucer_lit = {
            "left": False,
            "center": False,
            "right": False,
        }

        self.meltdown_lit = False

        self.add_mode_event_handler("parafino_start", self.start_para)

        self.add_mode_event_handler("parafino_left_heat_hit", self.heat_hit, zone="left")
        self.add_mode_event_handler("parafino_center_heat_hit", self.heat_hit, zone="center")
        self.add_mode_event_handler("parafino_right_heat_hit", self.heat_hit, zone="right")

        self.add_mode_event_handler("parafino_saucer_1_hit", self.saucer_hit, saucer=1)
        self.add_mode_event_handler("parafino_saucer_2_hit", self.saucer_hit, saucer=2)
        self.add_mode_event_handler("parafino_saucer_3_hit", self.saucer_hit, saucer=3)

        self.add_mode_event_handler("parafino_spinner_hit", self.spinner_hit)

    def start_para(self, **kwargs):
        for zone in self.ZONES:
            self.post_heat_event(zone)
        self.update_player_vars()

    def heat_hit(self, zone, **kwargs):
        if self.heat[zone] < self.MAX_HEAT:
            self.heat[zone] += 1

        self.post_heat_event(zone)
        self.schedule_cooling(zone)
        self.check_add_a_ball(zone)
        self.check_meltdown()
        self.update_player_vars()

    def schedule_cooling(self, zone):
        self.delay.remove(f"parafino_cool_{zone}")
        self.delay.add(
            name=f"parafino_cool_{zone}",
            ms=self.COOL_DELAY_MS,
            callback=self.cool_zone,
            zone=zone
        )

    def cool_zone(self, zone):
        if self.heat[zone] > 0:
            self.heat[zone] -= 1

        self.post_heat_event(zone)

        if self.heat[zone] > 0:
            self.schedule_cooling(zone)

        self.check_meltdown()
        self.update_player_vars()

    def check_add_a_ball(self, zone):
        if self.heat[zone] < self.MAX_HEAT:
            return

        if self.add_a_ball_earned[zone]:
            return

        if self.saucer_lit[zone]:
            return

        self.saucer_lit[zone] = True

        saucer = self.SAUCER_BY_ZONE[zone]
        self.machine.events.post(f"parafino_{zone}_saucer_lit")
        self.machine.events.post(f"parafino_saucer_{saucer}_ready")

    def saucer_hit(self, saucer, **kwargs):
        zone = self.ZONE_BY_SAUCER[saucer]

        if not self.saucer_lit[zone]:
            return

        self.saucer_lit[zone] = False

        if self.add_a_ball_earned[zone] == False:
            self.machine.events.post(f"parafino_add_a_ball_{saucer}")
            self.add_a_ball_earned[zone] = True
            
        self.machine.events.post(f"parafino_saucer_{saucer}_collected")            

        self.update_player_vars()

    def check_meltdown(self):
        all_maxed = all(self.heat[zone] >= self.MAX_HEAT for zone in self.ZONES)

        if all_maxed and not self.meltdown_lit:
            self.meltdown_lit = True
            self.machine.events.post("parafino_meltdown_lit")
            return

        if not all_maxed and self.meltdown_lit:
            self.meltdown_lit = False
            self.machine.events.post("parafino_meltdown_unlit")

    def spinner_hit(self, **kwargs):
        if not self.meltdown_lit:
            return

        balls = self.get_balls_in_play()
        jackpot = self.MELTDOWN_JACKPOT_BASE * balls

        self.award_score(jackpot)

        player = self.machine.game.player
        player["parafino_meltdown_jackpot"] = jackpot

        self.machine.events.post("parafino_meltdown_collected")
        self.machine.events.post("parafino_mode_complete")

    def post_heat_event(self, zone):
        zheat = self.heat[zone]
        self.machine.events.post(f"parafino_{zone}_heat_{zheat}")

    def get_balls_in_play(self):
        game = self.machine.game

        balls = getattr(game, "balls_in_play", 1)

        if callable(balls):
            balls = balls()

        if not balls or balls < 1:
            balls = 1

        if balls > 4:
            balls = 4

        return balls

    def award_score(self, value):
        self.machine.game.player["score"] += value

    def update_player_vars(self):
        player = self.machine.game.player

        player["parafino_left_heat"] = self.heat["left"]
        player["parafino_center_heat"] = self.heat["center"]
        player["parafino_right_heat"] = self.heat["right"]

        player["parafino_left_add_a_ball_earned"] = int(self.add_a_ball_earned["left"])
        player["parafino_center_add_a_ball_earned"] = int(self.add_a_ball_earned["center"])
        player["parafino_right_add_a_ball_earned"] = int(self.add_a_ball_earned["right"])

        player["parafino_balls_in_play"] = self.get_balls_in_play()
        player["parafino_meltdown_lit"] = int(self.meltdown_lit)