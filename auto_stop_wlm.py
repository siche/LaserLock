# auto stop wlm after 0:00 

import time
from wlm  import hf_wlm 

# calclate time now
# convert to local time
def get_now():
    seconds = time.time()+8*3600
    today_seconds = seconds % (24*3600)
    today_hour = today_seconds // 3600
    return int(today_hour)
# today_min = (today_seconds % 3600) // 60

# initialize the wavelengthmeter
wm = hf_wlm()

# auto stop wavelengthmeter when stop hour come
stop_hour = 0
while True:
    if (get_now() == stop_hour and wm.get_status()):
        wm.stop()
        print('WaveLenghtMetr is turned off')
    time.sleep(5*60)
        