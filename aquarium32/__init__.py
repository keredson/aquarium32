import gc, machine, sys

try: 
  import machine
  ON_ESP32 = True
except ModuleNotFoundError:
  ON_ESP32 = False

def mem_free():
  if ON_ESP32: return gc.mem_free()
  else: return -1

if ON_ESP32:
  from . import datetime
  sys.modules['datetime'] = datetime

try:
  # pre-load all imports so they don't OOM when aquarium32 uses them
  print('mem_free at start', mem_free())
  import uttp
  gc.collect()
  print('mem_free after uttp', mem_free())
  import pysolar.solar
  gc.collect()
  print('mem_free after pysolar.solar', mem_free())
  import pysolar.util
  gc.collect()
  print('mem_free after pysolar.util', mem_free())
  import suncalc
  gc.collect()
  print('mem_free after suncalc', mem_free())
  from . import util
  gc.collect()
  print('mem_free after util', mem_free())
  gc.collect()
  print('mem_free after collect', mem_free())
  from . import tank
  Tank = tank.Tank
  gc.collect()
  print('mem_free after aquarium32.tank', mem_free())
  from . import server
  gc.collect()
  print('mem_free after aquarium32.server', mem_free())
except MemoryError as e:
  print(e)
  sys.print_exception(e)
  #time.sleep(5)
  # try again
  machine.reset()


