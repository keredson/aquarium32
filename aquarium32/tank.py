import collections, datetime, math, os, random, re, sys, time

import uasyncio as asyncio

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
from . import update_led_strip




DATE_RE = re.compile(r'(\d{4})-(\d{2})-(\d{2})')




class Tank:

  def __init__(self):
    print('Aquarium32')
    self.last_ntp_check = 0
    
    self.sun_color = util.Color(255,255,255)
    self._cloudiness = 0
    self.nps = {}
    self.stars = {}

    util.load_settings(self)

    self.lat, self.lng = None, None
    self.city = None
    self.region = None
    self.country = None
    
    self.sun = None
    self.moon = None
    self.when = None
    self.last_updated_leds = 0
    
    self.last_weather_update = 0
    self.last_update_positions = 0
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
  def max_radiation(self):
    return self.settings.max_radiation or 1500
    
  def calc_cloudiness(self, now):
    if self.state=='manual': return self._cloudiness
    if not self.clouds_3_hour_interval: return 0
    cloud_i = int((now.timestamp() - self.last_weather_update)/60/60/3)
    cloudiness = self.clouds_3_hour_interval[max(0,min(cloud_i, len(self.clouds_3_hour_interval)-1))]
    return cloudiness
    
    
  def clear(self):
    for pin, np in self.nps.items():
      self.stars[pin] = []
      for i in range(np.n):
        np[i] = (0,0,0)
      np.write()
  
  def handle_interrupt(self, pin):
    print('handle_interrupt')
    self.sim_day()
    
  update_weather = util.update_weather
  ntp_check = util.ntp_check
  locate = util.locate
         
  def _calc_led_index(self, azimuth, num_leds, light_span):
    return azimuth / light_span * num_leds + num_leds/2
         
  def update_positions(self, now):
    if self.last_update_positions and abs(now.timestamp() - self.last_update_positions) < 60*3:
      return
    self.last_update_positions = now.timestamp()
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
      'sun:', self.sun, 'moon:', self.moon, 'postion:', (self.latitude, self.longitude), 'at:', now, 'free mem: %ib'%gc.mem_free() if hasattr(gc, 'mem_free') else 'n/a', 
    )

  def update_leds(self, now, skip_weather=None):
    sun = self.sun
    moon = self.moon
    for strip in self.settings.strips or []:
      self.update_led_strip(now, strip, skip_weather=None)
    for np in self.nps.values():
      np.write()

  update_led_strip = update_led_strip.update_led_strip
  
  async def sim_day(self, start = None, step_mins = 10):
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
      await asyncio.sleep(1)
    self.state = 'realtime'
  
  
  async def main(self):
    if not self.lat or not self.lng: self.locate()
    while True:
      f = getattr(self, self.state)
      if f: await f()
      self.clear()
      await asyncio.sleep(1)
    
  async def realtime(self):
    self.last_updated_leds = 0
    while True:
      if self.state != 'realtime': break
      if not self.last_updated_leds or time.time()-self.last_updated_leds > 60:
        self.last_updated_leds = time.time()
        self.ntp_check()
        now = datetime.datetime.now()
        self.update_positions(now)
        self.update_leds(now)
        self.update_weather()
      await asyncio.sleep(1)

  async def twinkle(self):
    while True:
      for k, np in self.nps.items():
        stars = self.stars.get(k)
        if stars:
          i = stars[int(random.random()*len(stars))]
          brightness = int(random.random()*25)
          np[i] = brightness, brightness, brightness
          np.write()
      await asyncio.sleep_ms(500)

  async def manual(self):
    self.last_updated_leds = 0
    while True:
      if self.state != 'manual': break
      if not self.last_updated_leds:
        self.last_updated_leds = time.time()
        self.update_leds(datetime.datetime.now())
      await asyncio.sleep(1)

  async def off(self):
    self.clear()
    while True:
      if self.state != 'off': break
      await asyncio.sleep(1)

  async def full(self):
    for pin, np in self.nps.items():
      self.stars[pin] = []
      for i in range(np.n):
        np[i] = (255,255,255)
      np.write()
    while True:
      if self.state != 'full': break
      await asyncio.sleep(1)
  
  def run_tank_and_server(self, host='0.0.0.0', port=80):
    loop = asyncio.get_event_loop()
    loop.create_task(self.heartbeat())
    loop.create_task(self.twinkle())
    loop.create_task(uttp.DEFAULT._serve(host, port))
    loop.create_task(self.main())
    loop.run_forever()

  async def heartbeat(self, ):
    while True:
      print('heartbeat', 'state', self.state, 'free mem: %ib'%gc.mem_free() if hasattr(gc, 'mem_free') else 'n/a')
      await asyncio.sleep(10)
    
      
