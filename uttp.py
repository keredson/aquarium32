import socket
import re
import time
import sys
import io

import json

if hasattr(time, 'ticks_ms'): _ticks_ms = time.ticks_ms
else: _ticks_ms = lambda: int(time.time() * 1000)

class Request:

  def __init__(self, app, f):
    request_line = f.readline().decode()
    self.app = app
    self._f = f
    if not request_line: raise Exception('empty request')
    self.method, path, self.proto = request_line.split()
    path = path.split('?', 1)
    self.path = path[0]

    if self.method=='GET':
      qs = path[1] if len(path)>1 else None
      self.params = dict(parse_qs(qs))
    else:
      self.params = {}

    self.headers = {}
    while header_line := f.readline():
      if header_line == b'\r\n': break
      k, v = header_line.decode().strip().split(': ')
      self.headers[k] = v

    print('%s:'%self.app.name, self.proto, self.method, self.path, self.params)
    
  def json(self):
    length = int(self.headers['Content-Length'])
    post_data = self._f.read(length)
    print('post_data', post_data)
    assert self.headers['Content-Type'] == 'application/json'
    return json.loads(post_data)
    


class Response:

  def __init__(self, f):
    self.f = f
    self.sent_status = False
    self.sent_content_type = False
    self.started_body = False
    self.handled_by = None
    
  def _pre_write(self):
    if not self.sent_status:
      self.start(status(200))
    if not self.sent_content_type:
      self.send_header(header('Content-Type', 'text/html; charset=utf-8'))
    if not self.started_body:
      self.f.write(b'\r\n')
      self.started_body = True
          
  def write(self, d):
    self._pre_write()
    if isinstance(d, str): d = d.encode()
    self.f.write(d)
   
  def send_header(self, h):
    if not self.sent_status:
      self.start(status(200))
    if h.k=='Content-Type': self.sent_content_type = True
    self.f.write(h.k.encode())
    self.f.write(': '.encode())
    self.f.write(h.v.encode())
    self.f.write(b'\r\n')

  def send_headers(self, headers):
    for k, v in headers.items():
      self.send_header(header(k, v))

  def start(self, status):
    self.started_at = _ticks_ms()
    self.status_line = '↳ HTTP/1.1 %i %s\r\n' % (status.code, status.reason)
    self.f.write(self.status_line.encode())
    self.sent_status = True
  
  def end(self):
    took_ms = _ticks_ms() - self.started_at
    print(self.status_line.strip(), '<=', self.handled_by.original_pattern if self.handled_by else '(not handled)', 'in %ims' % took_ms)
  


class Route:

  def __init__(self, f, method, pattern):
    self.original_pattern = pattern
    self.f = f
    self.method = method
    if pattern.__class__.__name__=='ure':
      self.pattern = pattern
    else:
      _pattern = re.sub(r'<\w+>', '([^/]+)', pattern)+'$'
      self.pattern = re.compile(_pattern)
      
  def handle(self, request, response, match):
    f = response.f
    args = [request]
    while True:
      try: args.append(match.group(len(args)))
      except IndexError: break # no more args
    for ret in self.f(*args):
      if isinstance(ret, status):
        response.start(ret)
      elif isinstance(ret, header):
        response.send_header(ret)
      elif isinstance(ret, str):
        response.write(ret)
      elif isinstance(ret, dict):
        response.send_header(header('Content-Type', 'application/json'))
        response._pre_write()
        json.dump(ret, f)
      elif 'io.TextIOWrapper' in repr(ret):
        while b:=ret.read(256):
          response.write(b)
      elif 'io.BufferedReader' in repr(ret):
        while b:=ret.read(256):
          response.write(b)
      elif 'io.FileIO' in repr(ret):
        while b:=ret.read(256):
          response.write(b)
      else: raise Exception('unknown response type:', ret)
    response.end()


class App:
  
  def __init__(self, name='μttp'):
    self.name = name
    self.routes = {}

  def get(self, pattern):
    return self.route(pattern, method='GET')
    
  def post(self, pattern):
    return self.route(pattern, method='POST')
    
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
        _print_exception(e)
      finally:
        f.close()
        cl.close()
      
  def run_daemon(self, host='0.0.0.0', port=80):
    import _thread  
    _thread.start_new_thread(self.run, (host, port))


  def handle(self, f):
    request = Request(self, f)
    response = Response(f)
    for route in _chain(self._get_routes(request.method), self._get_routes('*')):
      match = route.pattern.match(request.path)
      if match:
        response.handled_by = route
        route.handle(request, response, match)
        break
    else:
      response.start(status=status(404))
    

class status:
  def __init__(self, code=200, reason=None):
    self.code = code
    self.reason = reason or DEFAULT_CODE_REASONS.get(code, 'Other')

class header:
  def __init__(self, k, v):
    self.k = k
    self.v = v
    
    
DEFAULT_CODE_REASONS = {
  200: 'OK',
  404: 'Not Found',
}

DEFAULT = App()
get = DEFAULT.get
post = DEFAULT.post
run = DEFAULT.run
run_daemon = DEFAULT.run_daemon


EXT_MIME_TYPES = {
  'html':'text/html; charset=utf-8',
  'js':'application/javascript',
  'jsx':'text/jsx',
  'jpg':'image/jpeg',
  'jpeg':'image/jpeg',
}


def file(fn, max_age=604800):
  ext = None
  if '.' in fn:
    ext = fn[fn.index('.')+1:].lower()
    print(fn, ext)
  mime_type = EXT_MIME_TYPES.get(ext)
  try:
    with open(fn,'rb') as f:
      if mime_type:
        yield header('Content-Type', mime_type)
      if max_age is not None:
        yield header('Cache-Control', 'max-age=%i' % max_age)
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

def _print_exception(e):
  if hasattr(sys, 'print_exception'):
    sys.print_exception(e)
  else:
    print('print_exception', e)
    import traceback
    traceback.print_exc()

