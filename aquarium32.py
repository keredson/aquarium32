import time
import math
import datetime

try: 
  import machine
  import neopixel
  import ntptime
  import urequests as requests
except ImportError: 
  # not running on esp32
  import requests

import pysolar.solar
import pysolar.util
import suncalc

MAX_RADIATION = 1500


NTP_CHECK_INTERVAL_SECONDS = 60*60*24*7

DEFAULT_LAT, DEFAULT_LNG = 39.8283, -98.5795
DEFAULT_LOCATION = 'USA'

class Aquarium32:

  def __init__(self):
    print('Aquarium32')
    self.last_ntp_check = 0

    self.lat, self.lng = DEFAULT_LAT, DEFAULT_LNG
    self.city = None
    self.region = None
    self.country = None

    self.num_leds = 144
    self.led_length = 1000 # mm
    try:
      self.np = neopixel.NeoPixel(machine.Pin(13), self.num_leds)
    except NameError:
      # not in micropython / on esp32
      self.np = None
    self.locate()
      
      
  def locate(self):
    resp = requests.get(url='http://www.geoplugin.net/json.gp')
    data = resp.json()
    print('geo', data)
    self.lat = float(data.get('geoplugin_latitude', DEFAULT_LAT))
    self.lng = float(data.get('geoplugin_longitude', DEFAULT_LNG))
    self.city = data.get('geoplugin_city')
    self.region = data.get('geoplugin_regionName')
    self.country = data.get('geoplugin_countryName')
    
  
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
    moon = suncalc.getMoonPosition(now, self.lat, self.lng)
    moon.update(suncalc.getMoonIllumination(now))
    print('moon', moon)
    
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

      brightness = [max(0, min(i+1, stop) - max(i,start)) for i in range(self.num_leds)]    
    else:
      brightness = [0 for i in range(self.num_leds)]    

    print('brightness', brightness)

    moon_brightness = max(0, math.sin(moon['altitude']) * moon['fraction'])
    print('moon_brightness', moon_brightness)
    moon_led = int(round(moon['azimuth'] / math.pi * self.num_leds + self.num_leds/2))
    moon_led = max(0, min(moon_led, self.num_leds-1))
    print('moon_led', moon_led)

    if self.np:
      for i, v in enumerate(brightness):
        r = max(0,int(round(v*255)))
        g = max(0,int(round(v * min(255, altitude*10))))
        b = max(0,int(round(v * min(255, (altitude-10)*10))))
        self.np[i] = (r,g,b)
      if moon_brightness:
        r = max(0,int(round(moon_brightness * min(255, math.degrees(moon['altitude'])))))
        g = r #max(0,int(round(moon_brightness * min(255, (math.degrees(moon['altitude'])-10)*10))))
        b = max(0,int(round(moon_brightness*255)))
        self.np[moon_led] = (r,g,b)
      self.np.write()

  
  def sim_day(self, start, step_mins = 10):
    ts = start.timestamp()
    for i in range(24*60//step_mins):
      self.main(datetime.datetime.fromtimestamp(ts + i*60*step_mins))
    
    
  def run(self):
    while True:
      self.main(datetime.datetime.now())
      time.sleep(60)
