import collections, datetime, math, os, re, sys, time

try: 
  import gc
  import machine
  import neopixel
  import ujson as json
  ON_ESP32 = True
except ImportError: 
  import json
  ON_ESP32 = False

import pysolar.solar
import pysolar.util
import suncalc
import uttp
import util


import aquarium32_server


MAX_RADIATION = 1500


Settings = collections.namedtuple('Settings', 'num_leds, lat, lng, sun_color', defaults=(None,None,None,None))
Color = collections.namedtuple('Color', 'r g b')

class Aquarium32:

  def __init__(self):
    print('Aquarium32')
    self.last_ntp_check = 0
    
    self.load_settings()

    self.lat, self.lng = util.DEFAULT_LAT, util.DEFAULT_LNG
    self.city = None
    self.region = None
    self.country = None
    
    self.sun = None
    self.sun_color = Color(255,255,255)
    self.moon = None
    self.when = None
    
    self.last_weather_update = 0
    self.clouds_3_hour_interval = []
    self.state = 'realtime'

    #self.num_leds = 144 * 2
    try:
      self.np = neopixel.NeoPixel(machine.Pin(13), self.num_leds)
    except NameError:
      # not in micropython / on esp32
      self.np = None
    
    self.clear()
          
    
    #pir = machine.Pin(0, machine.Pin.IN)
    #pir.irq(trigger=machine.Pin.IRQ_RISING, handler=self.handle_interrupt)
    
  def load_settings(self):
    try:
      with open('aquarium32_settings.json') as f:
        self.settings = Settings(**json.load(f))
        print('loaded', self.settings)
        self.lat, self.lng = self.settings.lat, self.settings.lng
        sun_color = self.settings.sun_color
        if sun_color:
          sun_color = sun_color.lstrip('#')
          if len(sun_color)==6:
            self.sun_color = Color(int(sun_color[0:2],16), int(sun_color[2:4],16), int(sun_color[4:6],16))
    except FileNotFoundError as e:
      self.settings = Settings()
    except Exception as e:
      self.settings = Settings()
      util.print_exception(e)
      
  
  @property
  def num_leds(self):
    return self.settings.num_leds or 144
    
  def clear(self):
    if self.np:
      for i in range(self.num_leds):
        self.np[i] = (0,0,0)
      self.np.write()
  
  def handle_interrupt(self, pin):
    print('handle_interrupt')
    self.sim_day()
    
  update_weather = util.update_weather
  ntp_check = util.ntp_check
  locate = util.locate
         

  def update_leds(self, now):
    self.ntp_check()
    self.update_weather()
    gc.collect()
    altitude = pysolar.solar.get_altitude(self.lat, self.lng, now)
    #print('altitude', altitude)
    azimuth = pysolar.solar.get_azimuth(self.lat, self.lng, now) - 90
    #print('azimuth', azimuth)
    radiation = pysolar.util.diffuse_underclear(self.lat, self.lng, now)
    #print('radiation', radiation)
    leds = radiation / MAX_RADIATION * self.num_leds
    #print('leds', leds)
    moon = suncalc.getMoonPosition(now, self.lat, self.lng)
    moon.update(suncalc.getMoonIllumination(now))
    self.when = now
    self.sun = {
      'altitude':altitude,
      'azimuth':azimuth,
      'radiation':radiation,
    }
    self.moon = {
      'altitude':moon['altitude'],
      'azimuth':moon['azimuth'],
      'fraction':moon['fraction'],
    }
    print(
      'at', now, now.timestamp(), gc.mem_free() if hasattr(gc, 'mem_free') else 'n/a', 
      'sun', self.sun, 'moon', self.moon
    )
    
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
      r = max(0,v*self.sun_color.r)
      g = max(0,v * min(self.sun_color.g, altitude*10))
      b = max(0,v * min(self.sun_color.b, (altitude-10)*10))

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
    orig_state = self.state
    self.state = 'sim_day'
    ts = start.timestamp()
    for i in range(24*60//step_mins):
      if self.state != 'sim_day': break
      try:
        self.update_leds(datetime.datetime.fromtimestamp(ts + i*60*step_mins))
      except MemoryError as e:
        util.print_exception(e)
    self.state = orig_state
  
  
  def main(self):
    if not self.lat or not self.lng: self.locate()
    while True:
      f = getattr(self, self.state)
      if f: f()
      self.clear()
      time.sleep(1)
    
  def realtime(self):
    self.state = 'realtime'
    while True:
      if self.state != 'realtime': break
      self.update_leds(datetime.datetime.now())
      time.sleep(1)

  def off(self):
    self.state = 'off'
    self.clear()
    while True:
      if self.state != 'off': break
      time.sleep(1)

  def full(self):
    self.state = 'full'
    if self.np:
      for i in range(self.num_leds):
        self.np[i] = (255,255,255)
      self.np.write()
    while True:
      if self.state != 'full': break
      time.sleep(1)
      
