import socket
import re
import time
import sys
import io

class Request:

  def __init__(self, app, f):
    request_line = f.readline().decode()
    self.app = app
    self.method, path, self.proto = request_line.split()
    path = path.split('?', 1)
    self.path = path[0]
    qs = path[1] if len(path)>1 else None
    self.params = dict(parse_qs(qs))

    self.headers = {}
    while header_line := f.readline():
      if header_line == b'\r\n': break
      k, v = header_line.decode().strip().split(': ')
      self.headers[k] = v

    print('%s:'%self.app.name, self.proto, self.method, self.path, self.params)


class Response:

  def __init__(self, f):
    self.f = f
    self.sent_status = False
    self.sent_content_type = False
    self.started_body = False
          
  def write(self, d):
    if not self.sent_status:
      self.start(status(200))
    if not self.sent_content_type:
      self.send_header('Content-Type', 'text/html; charset=utf-8')
    if not self.started_body:
      self.f.write('\r\n')
      self.started_body = True
    self.f.write(d)
   
  def send_header(self, k, v):
    if k=='Content-Type': self.sent_content_type = True
    self.f.write(k)
    self.f.write(': ')
    self.f.write(v)
    self.f.write('\r\n')

  def send_headers(self, headers):
    for k, v in headers.items():
      self.send_header(k, v)

  def start(self, status):
    status_line = 'HTTP/1.0 %i %s\r\n' % (status.code, status.reason)
    self.f.write(status_line)
    print(status_line.strip())
    self.sent_status = True
    return
    for k, v in headers.items():
      self.f.write(k)
      self.f.write(': ')
      self.f.write(v)
      self.f.write('\r\n')
    self.f.write('\r\n')
  


class Route:

  def __init__(self, f, method, pattern):
    self.f = f
    self.method = method    
    if pattern.__class__.__name__=='ure':
      self.pattern = pattern
    else:
      _pattern = re.sub(r'<\w+>', '([^/]+)', pattern)+'$'
      self.pattern = re.compile(_pattern)
      
  def handle(self, match):
    global request, response
    f = response.f
    args = []
    while True:
      try: args.append(match.group(len(args)+1))
      except IndexError: break # no more args
    for ret in self.f(*args):
      if isinstance(ret, status):
        response.start(ret)
      elif isinstance(ret, str):
        response.write(ret)
      elif repr(ret)=='<io.TextIOWrapper>':
        while b:=ret.read(256):
          response.write(b)
      else: raise Exception('unknown response type:', ret)


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
      print('registering:', method, pattern)
      self._get_routes(method).append(Route(f, method, pattern))
    return decorator
  
  def serve(self, loop, host, port):
    print('starting', self.name, 'on', '%s:%d' % (host, port))
    loop.create_task(asyncio.start_server(self.handle, host, port))
    loop.run_forever()

  def run(self, host='0.0.0.0', port=80):
    addr = socket.getaddrinfo(host, port)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print('starting', self.name, 'on', addr)
    while True:
      cl, addr = s.accept()
      f = cl.makefile('rwb', 0)
      try:
        self.handle(f)
      except Exception as e:
        print('failed:', e)
        sys.print_exception(e)
      finally:
        #f.close()
        cl.close()
      
  def run_daemon(self, host='0.0.0.0', port=80):
    import _thread  
    _thread.start_new_thread(self.run, (host, port))


  def handle(self, f):
    global request, response
    request = Request(self, f)
    response = Response(f)
    for route in _chain(self._get_routes(request.method), self._get_routes('*')):
      match = route.pattern.match(request.path)
      if match:
        route.handle(match)
        break
    else:
      response.start(status=404)
    request = None
    response = None
    

class status:
  def __init__(self, code=200, reason='OK'):
    self.code = code
    self.reason = reason
    

DEFAULT = App()
get = DEFAULT.get
run = DEFAULT.run
run_daemon = DEFAULT.run_daemon

request = None
response = None


def file(fn):
  print('fn', fn)
  try:
    with open(fn) as f:
      yield f
  except OSError:
    yield status(404)


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
