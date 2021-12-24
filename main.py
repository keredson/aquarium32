import datetime, time
import machine
import wifimgr


print('getting connection')
wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        time.sleep(60)  # you shall not pass :D


# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("ESP OK", wlan.ifconfig())


try:
  import pysolar.solar
  import pysolar.util
  import suncalc
  import urequests as requests
  import aquarium32
except MemoryError as e:
  print(e)
  machine.reset()

tank = aquarium32.Aquarium32()
tank.sim_day()
tank.run()
