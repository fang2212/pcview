class Road(object):
    lanes = {}
    slope = 0
    cross_slope = 0

    def update_slope(self, pitch):
        self.slope = 0.1* pitch + 0.9*self.slope

    def update_cross_slope(self, roll):
        self.cross_slope = 0.1 * roll + 0.9 * self.cross_slope