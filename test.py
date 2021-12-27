import unittest

from datetime import datetime
import suncalc
from aquarium32 import Aquarium32



class TestSunCalc(unittest.TestCase):

    def test_datetime(self):
        datetime.now()

    def test_suncalc(self):
        now = datetime(2017, 9, 6, 6, 4, 29, 213367)
        print(suncalc.getTimes(now, 37.7749, -122.4194))
        print(suncalc.getPosition(now, 37.7749, -122.4194))
        print(suncalc.getMoonIllumination(now))
        print(suncalc.getMoonPosition(now, 37.7749, -122.4194))
        solstice_noon = suncalc.getTimes(datetime(2021,6,21), 37.7749, -122.4194)['solarNoon']
#        print('xxx',suncalc.getPosition(suncalc.getTimes(solstice_noon, 37.7749, -122.4194))
        print('xxx',suncalc.getPosition(suncalc.getTimes(datetime(2021,12,21), 37.7749, -122.4194)['night'], 37.7749, -122.4194))


class TestAquarium32(unittest.TestCase):

    def test_datetime(self):
        tank = Aquarium32()
        tank.update_leds(datetime(2021, 6, 21, 18, 0, 0, 0))
#        for i in range(24):
#          for j in [0,15,30,45]:
#            tank.main(datetime(2021, 6, 21, i, j, 0, 0))
        #tank.sim_day(datetime(2021, 6, 12, 0, 0, 0))



if __name__ == '__main__':
    unittest.main()

'''
import suncalc
suncalc.getTimes(datetime.now(), 37.7749, -122.4194)
suncalc.getPosition(datetime.now(), 37.7749, -122.4194)


from datetime import datetime
from aquarium32 import Aquarium32
tank = Aquarium32()
tank.main(datetime(2021, 12, 21, 20, 0, 14, 55739))
tank.sim_day(datetime(2021, 6, 20, 0, 0, 0))

'''
