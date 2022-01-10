import socket
import re
import time
import sys
import io
import json
import gc

import uasyncio as asyncio
import uasyncio.core
import uselect as select

try: 
  import machine
  ON_ESP32 = True
except ModuleNotFoundError:
  ON_ESP32 = False

if hasattr(time, 'ticks_ms'): _ticks_ms = time.ticks_ms
else: _ticks_ms = lambda: int(time.time() * 1000)

BUFFER_SIZE = 128
IS_UASYNCIO_V3 = hasattr(asyncio, "__version__") and asyncio.__version__ >= (3,)

class Request:

  def __init__(self, app, f):
    self.app = app
    self._f = f
  
  async def start(self):
    request_line = (await self._f.readline()).decode()
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
    while header_line := await self._f.readline():
      if header_line == b'\r\n': break
      k, v = header_line.decode().strip().split(': ')
      self.headers[k] = v

    if 'Content-Length' in self.headers:
      length = int(self.headers['Content-Length'])
      if length:
        self._post_data = await self._f.read(length)
  
    print('%s:'%self.app.name, self.proto, self.method, self.path, self.params)
    
  def json(self):
    print('post_data', self._post_data)
    assert self.headers['Content-Type'] == 'application/json'
    return json.loads(self._post_data)


class Response:

  def __init__(self, f):
    self.f = f
    self.sent_status = False
    self.sent_content_type = False
    self.started_body = False
    self.handled_by = None
    
  async def _pre_write(self):
    if not self.sent_status:
      await self.start(status(200))
    if not self.sent_content_type:
      await self.send_header(header('Content-Type', 'text/html; charset=utf-8'))
    if not self.started_body:
      await self.f.awrite(b'\r\n')
      self.started_body = True
          
  async def write(self, d):
    await self._pre_write()
    if isinstance(d, str): d = d.encode()
    await self.f.awrite(d)
   
  async def send_header(self, h):
    if not self.sent_status:
      await self.start(status(200))
    if h.k=='Content-Type': self.sent_content_type = True
    await self.f.awrite(h.k.encode())
    await self.f.awrite(': '.encode())
    await self.f.awrite(h.v.encode())
    await self.f.awrite(b'\r\n')

  async def send_headers(self, headers):
    for k, v in headers.items():
      await self.send_header(header(k, v))

  async def start(self, status):
    self.started_at = _ticks_ms()
    self.status_line = '↳ HTTP/1.0 %i %s\r\n' % (status.code, status.reason)
    await self.f.awrite(self.status_line.encode())
    print('xxxxxxxxxxxx')
    self.sent_status = True
  
  async def end(self):
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
      
  async def handle(self, request, response, match):
    f = response.f
    args = [request]
    while True:
      try: args.append(match.group(len(args)))
      except IndexError: break # no more args
    for ret in self.f(*args):
      if isinstance(ret, status):
        await response.start(ret)
      elif isinstance(ret, header):
        await response.send_header(ret)
      elif isinstance(ret, str):
        await response.write(ret)
      elif isinstance(ret, dict):
        await response.send_header(header('Content-Type', 'application/json'))
        await response._pre_write()
        await _json_dump_async(ret, f)
        #await response.write(json.dumps(ret))
      elif 'io.TextIOWrapper' in repr(ret):
        while b:=ret.read(BUFFER_SIZE):
          await response.write(b)
      elif 'io.BufferedReader' in repr(ret):
        while b:=ret.read(BUFFER_SIZE):
          await response.write(b)
      elif 'io.FileIO' in repr(ret):
        while b:=ret.read(BUFFER_SIZE):
          await response.write(b)
      else: raise Exception('unknown response type:', ret)
    await response.end()
    
    
async def _json_dump_async(o, f):
  if isinstance(o, dict):
    await f.awrite('{')
    first = True
    for k,v in o.items():
      if not first: await f.awrite(',')
      else: first = False
      await _json_dump_async(k, f)
      await f.awrite(':')
      await _json_dump_async(v, f)
    await f.awrite('}')
  elif isinstance(o, list):
    await f.awrite('[')
    for i, x in enumerate(o):
      await _json_dump_async(x, f)
      if i!=len(o)-1:
        await f.awrite(',')
    await f.awrite(']')
  else:
    await f.awrite(json.dumps(o))


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
  
  async def _serve(self, host='0.0.0.0', port=80):
    addr = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)[0][-1]
    s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s_sock.setblocking(False)
    s_sock.bind(addr)
    s_sock.listen(16)
    poller = select.poll()
    poller.register(s_sock, select.POLLIN)
    loop = asyncio.get_event_loop()

    print('starting', self.name, 'on', addr)
    while True:
      res = poller.poll(1)
      if res:
        c_sock, _ = s_sock.accept()
        loop.create_task(self.handle(c_sock))
      await asyncio.sleep(1)


  async def handle(self, sock):
    sreader = asyncio.StreamReader(sock)
    swriter = asyncio.StreamWriter(sock, {})
    print('Got connection from client')
    try:
      request = Request(self, sreader)
      await request.start()
      response = Response(swriter)
      for route in _chain(self._get_routes(request.method), self._get_routes('*')):
        match = route.pattern.match(request.path)
        if match:
          response.handled_by = route
          await route.handle(request, response, match)
          break
      else:
        await response.start(status=status(404))
        print('xxxxxxxxxxxx2')
    except OSError:
        pass
    print('Client {} disconnect')
    sock.close()

    

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

