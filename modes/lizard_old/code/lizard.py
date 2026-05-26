from mpf.core.mode import Mode
"""
    "title": "THE LIZARD MAN",
    "intro_1": "Create the antidote at the star rollover.",
    "intro_2": "Get it to Lizard Man at the lit web targets.",
    "intro_3": "Move fast before the value drains.",
    "summary_title_complete": "LIZARD MAN CURED",
    "summary_title_failed": "LIZARD MAN ESCAPED",
    "stat_1_label": "DELIVERIES",
    "stat_1_var": "lizard_deliveries",
    "stat_2_label": "BEST VALUE",
    "stat_2_var": "lizard_best_delivery_value",
    "points_var": "lizard_mode_points",
    "completed_var": "lizard_completed",
"""

class Lizard(Mode):

    DELIVERY_SEQUENCE = [
        "left",
        "center",
        "left",
        "center"
    ]

    TARGET_LIGHT_EVENTS = {
        "left": "lizard_light_left_web",
        "center": "lizard_light_center_web",
        "left": "lizard_light_left_web",
        "center": "lizard_light_center_web"
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.add_mode_event_handler(
            "lizard_delivery_request_left",
            self.delivery_request,
            target="left"
        )

        self.add_mode_event_handler(
            "lizard_delivery_request_center",
            self.delivery_request,
            target="center"
        )

        self.add_mode_event_handler(
            "lizard_light_delivery_target",
            self.light_next_target
        )
        self.machine.events.post("rooftop_diverter_close")


    def current_target(self):
        player = self.machine.game.player

        deliveries = player["lizard_deliveries"]

        if deliveries >= len(self.DELIVERY_SEQUENCE):
            return None

        return self.DELIVERY_SEQUENCE[deliveries]

    def delivery_request(self, target=None, **kwargs):
        player = self.machine.game.player

        if player["lizard_serum_ready"] == 0:
            return

        required_target = self.current_target()

        if required_target != target:
            return

        self.machine.events.post("lizard_serum_delivered")
        self.machine.events.post("lizard_delivery_timer_stop")

        deliveries_after = player["lizard_deliveries"] + 1

        if deliveries_after >= len(self.DELIVERY_SEQUENCE):
            self.machine.events.post("lizard_mode_complete")
            return

        self.machine.events.post("lizard_light_serum_location")
        #self.machine.events.post("lizard_light_delivery_target")

    def light_next_target(self, **kwargs):
        target = self.current_target()

        if not target:
            return

        event = self.TARGET_LIGHT_EVENTS.get(target)

        if event:
            self.machine.events.post(event)