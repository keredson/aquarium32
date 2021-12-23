import unittest

from datetime import datetime
import suncalc
from aquarium32 import Aquarium32

noon = suncalc.getTimes(datetime(2021,6,21), 37.7749, -122.4194)['solarNoon']
dawn = suncalc.getTimes(datetime(2021,6,21), 37.7749, -122.4194)['dawn']
sunrise = suncalc.getTimes(datetime(2021,6,21), 37.7749, -122.4194)['sunrise']
sunset = suncalc.getTimes(datetime(2021,6,21), 37.7749, -122.4194)['sunset']


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
        tank.main(datetime(2021, 12, 21, 12, 30, 14, 55739))
        tank.sim_day(datetime(2021, 6, 12, 0, 0, 0))



if __name__ == '__main__':
    unittest.main()

'''
from datetime import datetime
import suncalc
suncalc.getTimes(datetime.now(), 37.7749, -122.4194)
suncalc.getPosition(datetime.now(), 37.7749, -122.4194)
from aquarium32 import Aquarium32
tank = Aquarium32()
tank.main(datetime(2021, 12, 21, 20, 0, 14, 55739))
tank.sim_day(datetime(2021, 6, 20, 0, 0, 0))

'''
