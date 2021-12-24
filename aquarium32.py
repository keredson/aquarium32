import time
import math
import datetime
import re

try: 
  import gc
  import machine
  import neopixel
  import ntptime
  import urequests as requests
  import ujson as json
except ImportError: 
  # not running on esp32
  import requests
  import json

import pysolar.solar
import pysolar.util
import suncalc


import aquarium32_server


MAX_RADIATION = 1500


NTP_CHECK_INTERVAL_SECONDS = 60*60*24*7
WEATHER_UPDATE_INTERVAL_SECONDS = 60*60*24

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
    
    self.last_weather_update = 0
    self.clouds_3_hour_interval = []

    self.num_leds = 144
    self.led_length = 1000 # mm
    try:
      self.np = neopixel.NeoPixel(machine.Pin(13), self.num_leds)
    except NameError:
      # not in micropython / on esp32
      self.np = None
      
    aquarium32_server.start(self)
    
    self.locate()
    
    #pir = machine.Pin(0, machine.Pin.IN)
    #pir.irq(trigger=machine.Pin.IRQ_RISING, handler=self.handle_interrupt)
    
  
  def handle_interrupt(self, pin):
    print('handle_interrupt')
    self.sim_day()
  
  
  def update_weather(self):
    if self.last_weather_update==0 or time.time() - self.last_weather_update > WEATHER_UPDATE_INTERVAL_SECONDS:
      try:
        print('update_weather...')
        gc.collect()
        resp = requests.get(url='http://www.7timer.info/bin/civil.php?lon=%f&lat=%f&output=json' % (self.lat, self.lng))

        # manually parse json because of memory limitations
        self.clouds_3_hour_interval = []
        b = resp.raw.read(256)
        while b:
          while m := re.search(r'["]cloudcover["]\s?:\s?(\d+)',b):
            self.clouds_3_hour_interval.append((int(m.group(1))-1)/8)
            b = b[b.index(m.group(0)) + len(m.group(0)):]
          b = b[-32:] + resp.raw.read(256)
          if len(b)<=32: break
        print('self.clouds_3_hour_interval', self.clouds_3_hour_interval)
        self.last_weather_update = time.time()
      except Exception as e:
        print('update_weather', e)
      
      
  def locate(self):
    try:
      resp = requests.get(url='http://www.geoplugin.net/json.gp')
      data = resp.json()
      print('geo', data)
      self.lat = float(data.get('geoplugin_latitude', DEFAULT_LAT))
      self.lng = float(data.get('geoplugin_longitude', DEFAULT_LNG))
      self.city = data.get('geoplugin_city')
      self.region = data.get('geoplugin_regionName')
      self.country = data.get('geoplugin_countryName')
    except Exception as e:
      print('locate', e)
    
  
  def ntp_check(self):
    if self.last_ntp_check==0 or time.time() - self.last_ntp_check > NTP_CHECK_INTERVAL_SECONDS:
      print('ntp_check...')
      try:
        ntptime.settime()
        self.last_ntp_check = time.time()
      except Exception as e:
        print('ntp_check', e)
        

  def main(self, now):
    self.ntp_check()
    self.update_weather()
    gc.collect()
    print('at', now, now.timestamp())
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
    moon_altitude = moon['altitude']
    moon_fraction = moon['fraction']
    moon_azimuth = moon['azimuth']
    del moon
    
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
      

      brightness = (max(0, min(i+1, stop) - max(i,start)) for i in range(self.num_leds))
    else:
      brightness = (0 for i in range(self.num_leds))
      

    moon_brightness = max(0, math.sin(moon_altitude) * moon_fraction)
    print('moon_brightness', moon_brightness)
    moon_led = int(round(moon_azimuth / math.pi * self.num_leds + self.num_leds/2))
    moon_led = max(0, min(moon_led, self.num_leds-1))
    print('moon_led', moon_led)
        
    def f(i, v):
      r = max(0,v*255)
      g = max(0,v * min(255, altitude*10))
      b = max(0,v * min(255, (altitude-10)*10))

      if moon_brightness and abs(moon_led-i)<3:
        r = max(0, moon_brightness * min(255, 2*math.degrees(moon_altitude)))
        g = r
        b = max(0, min(255, moon_brightness*255))

      # clouds
      if self.clouds_3_hour_interval:
        cloud_i = int((now.timestamp() - self.last_weather_update)/60/60/3)
        cloudiness = self.clouds_3_hour_interval[max(0,min(cloud_i, len(self.clouds_3_hour_interval)-1))]
        cloud_step = now.timestamp()/10
        cloud_wave = (1+math.sin((cloud_step+i)/16))/2
        cloud_factor = 1 - cloudiness * cloud_wave
        
        # cap at 95% reduction
        cloud_factor = .05 + .95*cloud_factor
        r = r*cloud_factor
        g = g*cloud_factor
        b = b*cloud_factor

      return int(round(r)), int(round(g)), int(round(b))
    
    np = (f(i, v) for i, v in enumerate(brightness))

    if self.np:
      for i, color in enumerate(np):
        r, g, b = color
        self.np[i] = color
      self.np.write()

  
  def sim_day(self, start = datetime.datetime(2021,9,20,2,15,0), step_mins = 5):
    ts = start.timestamp()
    for i in range(24*60//step_mins):
      self.main(datetime.datetime.fromtimestamp(ts + i*60*step_mins))
    
    
  def run(self):
    while True:
      self.main(datetime.datetime.now())
      time.sleep(5)
      
