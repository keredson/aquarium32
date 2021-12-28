import uttp
import uttpreact
import datetime
import json
import util
import pysolar.util


def setup(tank):

  uttpreact.init()
  
  @uttp.get('/hello')
  def hello(req):
    yield 'hello '
    yield uttp.request.params.get('name', 'world')

  @uttp.get('/')
  def index(req):
    with open('static/index.html') as f:
      yield f

  @uttp.get('/static/<fn>')
  def static_file(req, fn):
    fn = 'static/'+fn
    yield from uttp.file(fn)

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

  @uttp.get('/status.json')
  def status(req):
    yield {
      'clouds': None,
      'last_weather_update': str(datetime.datetime.fromtimestamp(tank.last_weather_update)) if tank.last_weather_update else None,
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
    if new_settings.get('light_span')=='':
      new_settings['light_span'] = None
    if 'light_span' in new_settings:
      new_settings['light_span'] = int(new_settings['light_span'])
    with open('aquarium32_settings.json','w') as f:
      json.dump(new_settings, f)
    util.load_settings(tank)
    yield 'ok'

  @uttp.get('/settings.json')
  def settings(req):
    yield {k:getattr(tank.settings, k) for k in util.SETTINGS_FIELDS.keys()}
     
  
  #uttp.run_daemon()
  #uttp.run()

