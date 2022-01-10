import uttp
import uttp.react
import datetime
import json
from . import util
import pysolar.util

STATIC_PATH = 'aquarium32/static/'


def setup(tank):

  uttp.react.init(jsx_path=STATIC_PATH)
  
  @uttp.get('/')
  def index(req):
    yield uttp.header('Cache-Control', 'max-age=%i' % 604800)
    with open(STATIC_PATH+'index.html') as f:
      yield f

  @uttp.get('/static/<fn>')
  def static_file(req, fn):
    fn = STATIC_PATH+fn
    yield from uttp.file(fn, max_age=None)

  @uttp.post('/set_state')
  def set_state(req):
    state = req.json().get('state')
    if state:
      tank.state = state
      yield 'ok'
    else:
      yield uttp.status(400)

  @uttp.post('/set_sun')
  def set_state(req):
    sun = req.json().get('sun')
    if sun:
      sun['radiation'] = pysolar.util.diffuse_underclear_from_altitude(sun['altitude'])
      tank.sun = sun
      yield sun
    else:
      yield uttp.status(400)

  @uttp.post('/set_moon')
  def set_state(req):
    moon = req.json().get('moon')
    if moon:
      tank.moon = moon
      yield moon
    else:
      yield uttp.status(400)

  @uttp.post('/set_weather')
  def set_state(req):
    cloudiness = req.json().get('cloudiness')
    if cloudiness:
      tank._cloudiness = float(cloudiness)
      yield {}
    else:
      yield uttp.status(400)

  @uttp.get('/status.json')
  def status(req):
    yield {
      'cloudiness': tank.calc_cloudiness(datetime.datetime.now()),
      'lat': tank.lat,
      'lng': tank.lng,
      'city': tank.city,
      'region': tank.region,
      'country': tank.country,
      'num_leds': tank.num_leds,
      'sun': tank.sun,
      'moon': tank.moon,
      'when': str(tank.when),
      'state': tank.state,
    }
  
  @uttp.post('/settings.json')
  def save_settings(req):
    new_settings = req.json()
    if new_settings.get('sim_day')=='':
      new_settings['sim_day'] = None
    if new_settings.get('light_span'):
      new_settings['light_span'] = int(new_settings['light_span'])
    if new_settings.get('max_radiation'):
      new_settings['max_radiation'] = int(new_settings['max_radiation'])
    with open('aquarium32_settings.json','w') as f:
      json.dump(new_settings, f)
    util.load_settings(tank)
    yield 'ok'

  @uttp.get('/settings.json')
  def settings(req):
    yield {k:getattr(tank.settings, k) for k in util.SETTINGS_FIELDS.keys()}
     
def run(host='0.0.0.0', port=80):
  return uttp.run(host=host, port=port)

def run_daemon(host='0.0.0.0', port=80):
  return uttp.run_daemon(host=host, port=port)
  
  #uttp.run_daemon()
  #uttp.run()

