import time, gc

try: 
  import machine
  ON_ESP32 = True
except ModuleNotFoundError:
  ON_ESP32 = False



if ON_ESP32:
  import uwifimgr
  wlan = uwifimgr.get_connection(dhcp_hostname='aquarium32')
  if wlan is None:
      print("Could not initialize the network connection.")
      while True:
          time.sleep(1)  # you shall not pass :D
  print("ESP OK", wlan.ifconfig())


import aquarium32

tank = aquarium32.Tank()
tank.locate() 
aquarium32.server.setup(tank)
tank.run_tank_and_server(port=80 if ON_ESP32 else 8080)
#aquarium32.server.run(port=80 if ON_ESP32 else 8080)
#aquarium32.server.run_daemon(port=80 if ON_ESP32 else 8080)
#while True: time.sleep(5)
#tank.main()

