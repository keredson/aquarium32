import datetime, sys, time, gc

try: 
  import machine
  ON_ESP32 = True
except ModuleNotFoundError:
  ON_ESP32 = False


class FakeAquarium:
  last_weather_update = None
  lat = 1
  lng = 2
  city = 'city'
  region = 'region'
  country = 'country'
  num_leds = 44
  sun = {'radiation': -198.5947497388359, 'altitude': -9.633951103195921, 'azimuth': 155.7704619322661}
  moon = {'fraction': 0.599242271558743, 'altitude': -0.6178916635846572, 'azimuth': 3.092506780433276}
  when = datetime.datetime.now()

tank = FakeAquarium()
import aquarium32_server, uttp
aquarium32_server.setup(tank)
uttp.run(port=80 if ON_ESP32 else 8080)



