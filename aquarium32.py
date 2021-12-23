import time
import math

try: 
  import machine
  import _datetime as datetime
  import neopixel
  import ntptime
except ImportError: 
  # not running on esp32
  import datetime

import pysolar.solar
import pysolar.util

MAX_RADIATION = 1500


NTP_CHECK_INTERVAL_SECONDS = 60*60*24*7

class Aquarium32:

  def __init__(self):
    print('Aquarium32')
    self.last_ntp_check = 0
    self.lat, self.lng = 37.7749, -122.4194
    self.num_leds = 144
    self.led_length = 1000 # mm
    try:
      self.np = neopixel.NeoPixel(machine.Pin(13), self.num_leds)
    except NameError:
      # not in micropython / on esp32
      self.np = None
  
  def ntp_check(self):
    if time.time() - self.last_ntp_check > NTP_CHECK_INTERVAL_SECONDS:
      try:
        ntptime.settime()
        self.last_ntp_check = time.time()
      except Exception as e:
        print(e)
        
      


  def main(self, now):
    self.ntp_check()
    print('at', now)
    altitude = pysolar.solar.get_altitude(self.lat, self.lng, now)
    print('altitude', altitude)
    azimuth = pysolar.solar.get_azimuth(self.lat, self.lng, now) - 90
    print('azimuth', azimuth)
    radiation = pysolar.util.diffuse_underclear(self.lat, self.lng, now)
    print('radiation', radiation)
    leds = radiation / MAX_RADIATION * self.num_leds
    print('leds', leds)
    
    if radiation > 0:
      sun_center = azimuth / 180 * self.num_leds
      start = sun_center - leds/2
      stop = sun_center + leds/2
      if start < 0:
        stop -= start
        start = 0
      elif stop > self.num_leds:
        start -= stop - self.num_leds
        stop = self.num_leds
      print('start', start, 'stop', stop)

      brightness = [int(round(max(0, min(i+1, stop) - max(i,start))*255)) for i in range(self.num_leds)]    
    else:
      brightness = [0 for i in range(self.num_leds)]    

    print('brightness', brightness)

    if self.np:
      for i, v in enumerate(brightness):
        self.np[i] = (v,v,v)
      self.np.write()

    return
    

    sun_led = int(round(sun['azimuth'] / math.pi * self.num_leds + self.num_leds/2))

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
  
  def sim_day(self, start, step_mins = 10):
    ts = start.timestamp()
    for i in range(24*60//step_mins):
      self.main(datetime.datetime.fromtimestamp(ts + i*60*step_mins))
      #time.sleep(seconds/(24*60))
    
    
  def run(self):
    while True:
      self.main(datetime.datetime.now())
      time.sleep(60)
