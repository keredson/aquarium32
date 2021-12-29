import sys, time, gc

try: 
  import machine
  ON_ESP32 = True
except ModuleNotFoundError:
  ON_ESP32 = False

if ON_ESP32: print('mem_free', gc.mem_free())

if ON_ESP32:
  import _datetime
  sys.modules['datetime'] = _datetime
  import datetime
  import urequests as requests


if ON_ESP32:
  import uwifimgr
  wlan = uwifimgr.get_connection(dhcp_hostname='aquarium32')
  if wlan is None:
      print("Could not initialize the network connection.")
      while True:
          time.sleep(1)  # you shall not pass :D
  print("ESP OK", wlan.ifconfig())


try:
  # pre-load all imports so they don't OOM when aquarium32 uses them
  if ON_ESP32: print('mem_free after wifimgr', gc.mem_free())
  import pysolar.solar
  if ON_ESP32: print('mem_free after pysolar.solar', gc.mem_free())
  import pysolar.util
  if ON_ESP32: print('mem_free after pysolar.util', gc.mem_free())
  import suncalc
  if ON_ESP32: print('mem_free after suncalc', gc.mem_free())
  import uttp
  if ON_ESP32: print('mem_free after uttp', gc.mem_free())
  import util
  if ON_ESP32: print('mem_free after util', gc.mem_free())
  gc.collect()
  if ON_ESP32: print('mem_free after collect', gc.mem_free())
  import aquarium32
  if ON_ESP32: print('mem_free after aquarium32', gc.mem_free())
  gc.collect()
  import aquarium32_server
  if ON_ESP32: print('mem_free after aquarium32_server', gc.mem_free())
except MemoryError as e:
  print(e)
  sys.print_exception(e)
  #time.sleep(5)
  # try again
  machine.reset()


tank = aquarium32.Aquarium32()
tank.locate()
aquarium32_server.setup(tank)
uttp.run_daemon(port=80 if ON_ESP32 else 8080)
#uttp.run(port=80 if ON_ESP32 else 8080)
tank.main()

