import datetime, sys, time, gc

try: 
  import machine
  ON_ESP32 = True
except ModuleNotFoundError:
  ON_ESP32 = False


if ON_ESP32:
  import wifimgr
  print('getting connection')
  wlan = wifimgr.get_connection()
  if wlan is None:
      print("Could not initialize the network connection.")
      while True:
          time.sleep(60)  # you shall not pass :D
  print("ESP OK", wlan.ifconfig())

#import aquarium32_server, uttp
#aquarium32_server.setup(None)
#uttp.run(port=80 if ON_ESP32 else 8080)


try:
  # pre-load all imports so they don't OOM when aquarium32 uses them
  import pysolar.solar
  import pysolar.util
  import suncalc
  import urequests as requests
  import uttp
  import aquarium32_server
  import util
  gc.collect()
  import aquarium32
except MemoryError as e:
  print(e)
  sys.print_exception(e)
  #time.sleep(5)
  # try again
  machine.reset()

tank = aquarium32.Aquarium32()
#tank.sim_day()
tank.run()

