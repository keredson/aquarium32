import collections, gc, re, sys
try:
  import machine
  import ntptime
  import ujson as json
  import neopixel
  ON_ESP32 = True
except ModuleNotFoundError: 
  ON_ESP32 = False
  import json
import time
import urequests as requests


NTP_CHECK_INTERVAL_SECONDS = 60*60*24*7
WEATHER_UPDATE_INTERVAL_SECONDS = 60*60*24
DEFAULT_LAT, DEFAULT_LNG = 39.8283, -98.5795

SETTINGS_FIELDS = {
  'num_leds': None,
  'lat': None,
  'lng': None,
  'sun_color': None,
  'skip_weather': None,
  'sim_date': None,
}

Settings = collections.namedtuple('Settings', list(SETTINGS_FIELDS.keys()))
Color = collections.namedtuple('Color', 'r g b')


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

def ntp_check(self):
  if not ON_ESP32:
    return
  if self.last_ntp_check==0 or time.time() - self.last_ntp_check > NTP_CHECK_INTERVAL_SECONDS:
    print('ntp_check...')
    try:
      ntptime.settime()
      self.last_ntp_check = time.time()
    except Exception as e:
      print('ntp_check', e)
      
def locate(self):
  if not ON_ESP32:
    return
  try:
    gc.collect()
    resp = requests.get(url='http://www.geoplugin.net/json.gp')
    data = resp.json()
    print('geo', data)
    self.lat = float(data.get('geoplugin_latitude', DEFAULT_LAT))
    self.lng = float(data.get('geoplugin_longitude', DEFAULT_LNG))
    self.city = data.get('geoplugin_city')
    self.region = data.get('geoplugin_regionName')
    self.country = data.get('geoplugin_countryName')
  except Exception as e:
    sys.print_exception(e)

def print_exception(e):
  if hasattr(sys, 'print_exception'):
    sys.print_exception(e)
  else:
    print('print_exception', e)
    
def load_settings(self):
  try:
    with open('aquarium32_settings.json') as f:
      print('found aquarium32_settings.json')
      settings = dict(SETTINGS_FIELDS)
      settings.update(json.load(f))
      self.settings = Settings(**settings)
      print('loaded', self.settings)
      if self.settings.lat: self.lat = self.settings.lat
      if self.settings.lng: self.lng = self.settings.lng
      sun_color = self.settings.sun_color
      if sun_color:
        sun_color = sun_color.lstrip('#')
        if len(sun_color)==6:
          self.sun_color = Color(int(sun_color[0:2],16), int(sun_color[2:4],16), int(sun_color[4:6],16))
  except OSError as e:
    print('aquarium32_settings.json not found, loading defaults')
    self.settings = Settings(None,None,None,None,None,None)
  except Exception as e:
    self.settings = Settings(None,None,None,None,None,None)
    print_exception(e)
  try:
    self.np = neopixel.NeoPixel(machine.Pin(13), self.num_leds)
  except NameError as e:
    print_exception(e)
    self.np = None

