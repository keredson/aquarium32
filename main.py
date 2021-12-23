import time
import wifimgr


print('getting connection')
wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        time.sleep(60)  # you shall not pass :D


# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("ESP OK", wlan.ifconfig())


import aquarium32

aquarium32.Aquarium32().run()
