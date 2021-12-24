import uasyncio as asyncio
import re

class HTTPRequest:

  def __init__(self, app, request_line):
    request_line = request_line.decode()
    self.app = app
    self.method, path, self.proto = request_line.split()
    path = path.split('?', 1)
    self.path = path[0]
    qs = path[1] if len(path)>1 else None
    self.params = dict(parse_qs(qs))
    print('%s:'%self.app.name, self.proto, self.method, self.path, self.params)


class HTTPResponse:

  def __init__(self, w):
    self.w = w
    
  def static_file(self, fn):
    with open(fn, 'r') as f:
      self.w.write(f)

  def start(self, status='200', headers={}):
    yield from self.w.awrite('HTTP/1.1 %s OK\r\n' % status)
    for k, v in headers.items():
      yield from self.w.awrite(k)
      yield from self.w.awrite(': ')
      yield from self.w.awrite(v)
      yield from self.w.awrite('\r\n')
    yield from self.w.awrite('\r\n')
  
  def write(self, v):
    yield from self.w.awrite(v)

  def close(self):
    print('...closing')
    yield from self.w.aclose()

class Route:

  def __init__(self, f, method, pattern):
    self.f = f
    self.method = method    
    if pattern.__class__.__name__=='ure':
      self.pattern = pattern
    else:
      self.pattern = re.compile(pattern)
      
  def handle(self, req, r, w, match):
    resp = HTTPResponse(w)
    ret = self.f()
    if isinstance(ret, str):
      yield from resp.start(headers={'Content-Type':'text/html; charset=utf-8'})
      yield from resp.write(ret)
      yield from resp.close()
    else: raise Exception('unknown response type:', ret)
    return True


class App:
  
  def __init__(self, name='μttp'):
    self.name = name
    self.routes = {}

  def get(self, pattern):
    return self.route(pattern, method='GET')
    
  def _get_routes(self, method):
    routes = self.routes.get(method)
    if routes is None:
      routes = []
      self.routes[method] = routes
    return routes
    
  def route(self, pattern, method='*'):
    def decorator(f):
      print('registering', f, 'to', pattern)
      self._get_routes(method).append(Route(f, method, pattern))
    return decorator
  
  def serve(self, loop, host, port):
    print('starting', self.name, 'on', '%s:%d' % (host, port))
    loop.create_task(asyncio.start_server(self.handle, host, port))
    loop.run_forever()

  def run(self, host='', port=8080):
    loop = asyncio.get_event_loop()
    self.serve(loop, host, port)
    loop.close()

  def run_daemon(self, host='', port=8080):
    import _thread  
    _thread.start_new_thread(self.run, (host, port))


  def handle(self, r, w):
    request_line = yield from r.readline()
    if request_line == b'':
      yield from w.aclose()
      return
    req = HTTPRequest(self, request_line)
    for route in _chain(self._get_routes(req.method), self._get_routes('*')):
      print('route', route, route.pattern)
      match = route.pattern.match(req.path)
      if match:
        yield from route.handle(req, r, w, match)
        break
    else:
      print('404')
    


DEFAULT = App()
get = DEFAULT.get
run = DEFAULT.run
run_daemon = DEFAULT.run_daemon


def parse_qs(qs):
  if qs: 
    for s in qs.split('&'):
      k, v = s.split('=')
      yield urldecode(k), urldecode(v)


DECODE_DICT = {'+':' ', '%20':' ', '%26':'&', '%23':'#'}
def urldecode(s):
  for k,v in DECODE_DICT.items():
    s = s.replace(k,v)
  return s
  
def _chain(*args):
  for l in args:
    for x in l:
      yield x
