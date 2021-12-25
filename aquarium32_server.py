import uttp
import uttpreact


def setup(tank):
  
  @uttp.get(r'/hello')
  def hello():
    yield 'hello '
    yield uttp.request.params.get('name', 'world')

  @uttp.get(r'/')
  def index():
    with open('static/index.html') as f:
      yield f

  @uttp.get(r'/<fn>')
  def static_file(fn):
    fn = 'static/'+fn
    try:
      with open(fn) as f:
        if fn.endswith('.jsx'):
          yield uttp.header('Content-Type', 'application/javascript')
        yield f
    except OSError:
      yield uttp.status(404)

  
  #uttp.run_daemon()
  #uttp.run()

