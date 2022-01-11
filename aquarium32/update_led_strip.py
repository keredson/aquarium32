import math, random
from . import util



def update_led_strip(self, now, strip, skip_weather=None):
  sun = self.sun
  moon = self.moon
  leds_desc = (strip.get('leds') or '0').strip().split('-')
  if len(leds_desc)==1:
    start_led = 1
    stop_led = int(leds_desc[0])
  else:
    start_led = int(leds_desc[0])
    stop_led = int(leds_desc[1])
  num_leds = stop_led - start_led + 1
  light_span = strip.get('light_span') or 180
  reverse = strip.get('reversed')
  
  if sun['radiation'] > 0:
    leds = sun['radiation'] / self.max_radiation * num_leds
    sun_center = self._calc_led_index(self.sun['azimuth'], num_leds, light_span)
    start = sun_center - leds/2
    stop = sun_center + leds/2
    if start < 0:
      stop -= start
      start = 0
    elif stop > num_leds:
      start -= stop - num_leds
      stop = num_leds
    

    brightness = (max(0, min(i+1, stop) - max(i,start)) for i in range(num_leds))
  else:
    brightness = (0 for i in range(num_leds))
    

  moon_brightness = max(0, math.sin(moon['altitude']) * moon['fraction'])
  moon_led = self._calc_led_index(self.moon['azimuth'], num_leds, light_span)
  moon_led = max(0, min(moon_led, num_leds-1))
  moon_altitude = moon['altitude']
  
  sun_altitude = sun['altitude']
  cloud_step = now.timestamp()
  
  stars = []
  self.stars[strip['pin']] = stars
  
  def f(i, v, cloudiness):

    r = max(0, v*self.sun_color.r)
    g = max(0, v * min(self.sun_color.g, sun_altitude*10))
    b = max(0, v * min(self.sun_color.b, (sun_altitude-10)*10))

    if moon_brightness and abs(moon_led-i)<4:
      r = max(r, moon_brightness * min(255, 2*math.degrees(moon_altitude)))
      g = r
      b = max(b, min(255, moon_brightness*255))

    # clouds
    if not skip_weather:
      cloud_wave = (1+math.sin((cloud_step+i)/12))/2
      cloud_factor = 1 - cloudiness * cloud_wave
      #print('cloud_factor', cloud_factor)
      
      # cap at 95% reduction
      cloud_factor = .05 + .95*cloud_factor
      r = r*cloud_factor
      g = g*cloud_factor
      b = b*cloud_factor

    return r,g,b
  
  cloudiness = self.calc_cloudiness(now)
  color_gen = (f(i, v, cloudiness) for i, v in enumerate(brightness))
  np = self.nps.get(strip['pin'])
  
  random.seed(now.day)
  for i, color in enumerate(color_gen):
    r, g, b = color
    np_i = start_led - 1 + num_leds - i - 1 if reverse else i + start_led - 1

    # stars
    if r==0 and g==0 and b==0 and random.random()<.1:
      r = g = b = int(random.random()*25)
      stars.append(np_i)

    if np:
      np[np_i] = int(round(r)), int(round(g)), int(round(b))

