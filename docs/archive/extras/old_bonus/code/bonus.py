from mpf.modes.bonus.code.bonus import Bonus as MpfBonus


class Bonus(MpfBonus):

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        # set up the bonus light buckets

        # 1. Get the total bonus from the player variable
        total = self.machine.game.player['bonus_count'] # Assuming 0-75
        
        # 2. Define your light values in descending order
        lights = [20, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        
        # 3. Calculate which buckets are "full"
        remaining = total
        for val in lights:
            if remaining >= val:
                self.machine.game.player[f'bonus_{val}k_lit'] = 1
                remaining -= val
            else:
                self.machine.game.player[f'bonus_{val}k_lit'] = 0



