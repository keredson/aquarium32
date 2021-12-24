import uttp


def start(tank):
  
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
    yield from uttp.file('static/'+fn)
    
  
  #uttp.run_daemon()
  uttp.run()

