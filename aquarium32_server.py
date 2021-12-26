import uttp
import uttpreact
import datetime


def setup(tank):

  uttpreact.init()
  
  @uttp.get('/hello')
  def hello():
    yield 'hello '
    yield uttp.request.params.get('name', 'world')

  @uttp.get('/')
  def index():
    with open('static/index.html') as f:
      yield f

  @uttp.get('/static/<fn>')
  def static_file(fn):
    fn = 'static/'+fn
    try:
      with open(fn) as f:
        if fn.endswith('.jsx'):
          yield uttp.header('Content-Type', 'application/javascript')
        yield f
    except OSError:
      yield uttp.status(404)

  @uttp.post('/set_state')
  def set_state():
    state = uttp.request.params.get('state')
    if state:
      tank.state = state
      yield 'ok'
    else:
      yield uttp.status(400)

  @uttp.get('/status.json')
  def status():
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
  
  #uttp.run_daemon()
  #uttp.run()

