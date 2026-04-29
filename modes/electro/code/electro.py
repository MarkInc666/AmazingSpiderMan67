from mpf.core.mode import Mode


class Electro(Mode):

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.current_shot = 1
        self.disabled = set()

        self.add_mode_event_handler("electro_start_spark", self.start_spark)
        self.add_mode_event_handler("electro_spark_timeout", self.spark_timeout)

        for shot_num in range(1, 7):
            self.add_mode_event_handler(
                f"electro_shot_{shot_num}_request",
                self.shot_request,
                shot_num=shot_num
            )

    def start_spark(self, **kwargs):
        self.current_shot = self.next_enabled_shot(start_after=0)

        if self.current_shot is None:
            self.machine.events.post("electro_mode_complete")
            return

        self.light_current_shot()
        self.machine.events.post("electro_spark_timer_start")

    def shot_request(self, shot_num, **kwargs):
        if shot_num != self.current_shot:
            return

        # 6th disabled spark = Super Jackpot
        if len(self.disabled) == 5:
            self.machine.events.post("electro_award_super_jackpot")
        else:
            self.machine.events.post("electro_award_jackpot")

        self.disabled.add(shot_num)
        self.machine.events.post("electro_spark_hit_show")

        if len(self.disabled) >= 6:
            self.machine.events.post("electro_mode_complete")
            return

        self.advance_spark()

    def spark_timeout(self, **kwargs):
        self.machine.events.post("electro_spark_out_show")

        # Last remaining spark timed out = mode ends
        if len(self.disabled) >= 5:
            self.machine.events.post("electro_mode_complete")
            return

        self.advance_spark()

    def advance_spark(self):
        next_shot = self.next_enabled_shot(start_after=self.current_shot)

        if next_shot is None:
            self.machine.events.post("electro_mode_complete")
            return

        self.current_shot = next_shot
        self.light_current_shot()
        self.machine.events.post("electro_spark_timer_start")

    def next_enabled_shot(self, start_after):
        shots = [1, 2, 3, 4, 5, 6]

        if start_after in shots:
            index = shots.index(start_after) + 1
        else:
            index = 0

        ordered = shots[index:] + shots[:index]

        for shot in ordered:
            if shot not in self.disabled:
                return shot

        return None

    def light_current_shot(self):
        self.machine.events.post(f"electro_light_shot_{self.current_shot}")
