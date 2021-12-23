import time
import datetime
import math

import machine
import neopixel
try: import ntptime
except: pass
import suncalc


NTP_CHECK_INTERVAL_SECONDS = 60*60*24*7

SUMMER_SOLSTICE = datetime.datetime(2021,12,21)
WINTER_SOLSTICE = datetime.datetime(2021,6,20)

SUN_WIDTH = 0 #0.0872665 # rad

class Aquarium32:

  def __init__(self):
    print('Aquarium32')
    self.last_ntp_check = 0
    self.lat, self.lng = 37.7749, -122.4194
    self.num_leds = 144
    self.led_length = 1000 # mm
    self.tank_width = 457 # mm
    self.led_width = self.led_length / self.num_leds
    self.max_altitude = max([suncalc.getPosition(suncalc.getTimes(d, self.lat, self.lng)['solarNoon'], self.lat, self.lng)['altitude'] for d in [SUMMER_SOLSTICE,WINTER_SOLSTICE]])
    print('max_altitude', self.max_altitude)
    self.np = neopixel.NeoPixel(machine.Pin(13), self.num_leds)
    
  
  def ntp_check(self):
    if time.time() - self.last_ntp_check > NTP_CHECK_INTERVAL_SECONDS:
      try:
        ntptime.settime()
        self.last_ntp_check = time.time()
      except Exception as e:
        print(e)

  def calc_brightness(self, body):
    altitude_brightness = max(0, math.sin((body['altitude']+SUN_WIDTH) / self.max_altitude * math.pi/2))
    azimuth_brightness = abs(math.cos(body['azimuth']))
    brightness = altitude_brightness * azimuth_brightness
    return brightness
        
  def main(self, now):
    self.ntp_check()
    print('at', now)
    sun = suncalc.getPosition(now, self.lat, self.lng)
    moon = suncalc.getMoonPosition(now, self.lat, self.lng)
    moon.update(suncalc.getMoonIllumination(now))
    #moon.update(suncalc.getMoonTimes(now, self.lat, self.lng))
    print('sun', sun)
    print('moon', moon)

    led_lng_offsets = (-(x-self.num_leds/2+.5)/self.num_leds*2*10 for x in range(self.num_leds))
#    print('led_lng_offsets', list(led_lng_offsets))
    sun_brightness = (self.calc_brightness(suncalc.getPosition(now, self.lat, self.lng+offset)) for offset in led_lng_offsets)
    brightness = [int(round(x*255)) for x in sun_brightness]

    moon_brightness = int(round(self.calc_brightness(moon) * moon['fraction'] * 255))
    print('moon_brightness', moon_brightness)
    moon_led = int(round(moon['azimuth'] / math.pi * self.num_leds + self.num_leds/2))
    if moon_led<0 or moon_led>=self.num_leds:
      moon_led = None
    print('moon_led', moon_led)
    if moon_led is not None:
      brightness[moon_led] = min(255, brightness[moon_led] + moon_brightness)
    print('brightness', brightness)
    for i, v in enumerate(brightness):
      self.np[i] = (v,v,v)
    self.np.write()
  
  def sim_day(self, start, seconds = 24, step_mins=1):
    ts = start.timestamp()
    for i in range(24*60//step_mins):
      self.main(datetime.datetime.fromtimestamp(ts + i*60*step_mins))
      #time.sleep(seconds/(24*60))
    
    
  def run(self):
    while True:
      self.main(datetime.datetime.now())
      time.sleep(60)
