import collections, datetime, math, os, random, re, sys, time

try: 
  import gc
  import machine
  import ujson as json
  ON_ESP32 = True
except ImportError: 
  import json
  ON_ESP32 = False

import pysolar.solar
import pysolar.util
import suncalc
import uttp
from . import util




DATE_RE = re.compile(r'(\d{4})-(\d{2})-(\d{2})')




class Tank:

  def __init__(self):
    print('Aquarium32')
    self.last_ntp_check = 0
    
    self.np = None
    self.sun_color = util.Color(255,255,255)
    self._cloudiness = 0

    util.load_settings(self)

    self.lat, self.lng = None, None
    self.city = None
    self.region = None
    self.country = None
    
    self.sun = None
    self.moon = None
    self.when = None
    
    self.last_weather_update = 0
    self.clouds_3_hour_interval = []
    self.state = 'realtime'

    self.clear()
          
    
    #pir = machine.Pin(0, machine.Pin.IN)
    #pir.irq(trigger=machine.Pin.IRQ_RISING, handler=self.handle_interrupt)
    
      
  
  @property
  def latitude(self):
    return util.DEFAULT_LAT if self.lat is None else self.lat
    
  @property
  def longitude(self):
    return util.DEFAULT_LNG if self.lng is None else self.lng
    
  @property
  def num_leds(self):
    return self.settings.num_leds or 144
    
  @property
  def light_span(self):
    return self.settings.light_span or 180
    
  @property
  def max_radiation(self):
    return self.settings.max_radiation or 1500
    
  def calc_cloudiness(self, now):
    if self.state=='manual': return self._cloudiness
    if not self.clouds_3_hour_interval: return 0
    cloud_i = int((now.timestamp() - self.last_weather_update)/60/60/3)
    cloudiness = self.clouds_3_hour_interval[max(0,min(cloud_i, len(self.clouds_3_hour_interval)-1))]
    return cloudiness
    
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
         
  def _calc_led_index(self, azimuth):
    return azimuth / self.light_span * self.num_leds + self.num_leds/2
         
  def update_positions(self, now):
    gc.collect()
    m = DATE_RE.match(self.settings.sim_date) if self.settings.sim_date else None
    if m:
      now = datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), now.hour, now.minute, now.second)      
    
    altitude = pysolar.solar.get_altitude(self.latitude, self.longitude, now)
    #print('altitude', altitude)
    azimuth = pysolar.solar.get_azimuth(self.latitude, self.longitude, now) - 180
    #print('azimuth', azimuth)
    radiation = pysolar.util.diffuse_underclear(self.latitude, self.longitude, now)
    #print('radiation', radiation)
    moon = suncalc.getMoonPosition(now, self.latitude, self.longitude)
    moon.update(suncalc.getMoonIllumination(now))
    self.when = now
    self.sun = {
      'altitude':altitude,
      'azimuth':azimuth,
      'radiation':radiation,
    }
    self.moon = {
      'altitude':moon['altitude'],
      'azimuth':math.degrees(moon['azimuth']),
      'fraction':moon['fraction'],
    }
    print(
      'state', self.state, 'postion:', (self.latitude, self.longitude), 'at:', now, 'free mem: %ib'%gc.mem_free() if hasattr(gc, 'mem_free') else 'n/a', 
    )

  def update_leds(self, now, skip_weather=None):
    sun = self.sun
    moon = self.moon
    print(
      'sun:', self.sun, 'moon:', self.moon
    )
    
    if sun['radiation'] > 0:
      leds = sun['radiation'] / self.max_radiation * self.num_leds
      sun_center = self._calc_led_index(self.sun['azimuth'])
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
      

    moon_brightness = max(0, math.sin(moon['altitude']) * moon['fraction'])
    moon_led = self._calc_led_index(self.moon['azimuth'])
    moon_led = max(0, min(moon_led, self.num_leds-1))
        
    def f(i, v, cloudiness):
      r = max(0,v*self.sun_color.r)
      g = max(0,v * min(self.sun_color.g, sun['altitude']*10))
      b = max(0,v * min(self.sun_color.b, (sun['altitude']-10)*10))

      # stars
      if sun['radiation'] < 0:
        twinkle = random.random()*10 < 1
        if twinkle:
          r = g = b = int(random.random()*25)

      if moon_brightness and abs(moon_led-i)<3:
        r = max(0, moon_brightness * min(255, 2*math.degrees(moon['altitude'])))
        g = r
        b = max(0, min(255, moon_brightness*255))

      # clouds
      if not skip_weather:
        cloud_step = now.timestamp()
        cloud_wave = (1+math.sin((cloud_step+i)/12))/2
        cloud_factor = 1 - cloudiness * cloud_wave
        #print('cloud_factor', cloud_factor)
        
        # cap at 95% reduction
        cloud_factor = .05 + .95*cloud_factor
        r = r*cloud_factor
        g = g*cloud_factor
        b = b*cloud_factor

      return int(round(r)), int(round(g)), int(round(b))
    
    cloudiness = self.calc_cloudiness(now)
    print('cloudiness',cloudiness)
    np = (f(i, v, cloudiness) for i, v in enumerate(brightness))
    
    if self.np:
      for i, color in enumerate(np):
        r, g, b = color
        self.np[i] = color
        #print(self.np[i], end='')
      #print()

      self.np.write()

  
  def sim_day(self, start = None, step_mins = 10):
    if start is None:
      start = datetime.datetime.now()
    ts = start.timestamp()
    for i in range(24*60//step_mins):
      if self.state != 'sim_day': break
      try:
        when = datetime.datetime.fromtimestamp(ts + i*60*step_mins)
        self.update_positions(when)
        self.update_leds(when, skip_weather=True)
      except MemoryError as e:
        util.print_exception(e)
    self.state = 'realtime'
  
  
  def main(self):
    if not self.lat or not self.lng: self.locate()
    while True:
      f = getattr(self, self.state)
      if f: f()
      self.clear()
      time.sleep(1)
    
  def realtime(self):
    while True:
      if self.state != 'realtime': break
      self.ntp_check()
      now = datetime.datetime.now()
      self.update_positions(now)
      self.update_leds(now)
      self.update_weather()
      time.sleep(1)

  def manual(self):
    while True:
      if self.state != 'manual': break
      self.update_leds(datetime.datetime.now())
      time.sleep(1)

  def off(self):
    self.clear()
    while True:
      if self.state != 'off': break
      time.sleep(1)

  def full(self):
    if self.np:
      for i in range(self.num_leds):
        self.np[i] = (255,255,255)
      self.np.write()
    while True:
      if self.state != 'full': break
      time.sleep(1)
      
