from wlm import hf_wlm
from toptica_laser import toptica_laser 
import time

# configuration for lasers
label = '935'
ip= '192.168.1.9'
des_fre = 935.180200
channel = 4

# storage voltage and wavelength
data_len = 1200
time_interval = 0.05
wlm_data = [None]*data_len
vol_data = [None]*data_len 

# initialize laser and wavemeter
wlm = hf_wlm()
laser = toptica_laser(ip)

def pid(vol,fre, des):
    # vol: the voltage of the piezo
    # fre: frequency of laser
    # des: destination frequency
    # vol_int = sum(vol)
    k_p = -0.1
    # k_i = 0
    # k_d = 0
    delta_vol = k_p*(des-fre)*1000
    return delta_vol

while True:
    # update data
    wlm_temp = wlm.get_wavelength(channel)
    wlm_data = wlm_data[1:]+[wlm_temp]
    print('Wavelength is %fnm' % wlm_temp)

    # STOP when laser or wavemeter is off
    if (wlm_temp < 0 or not laser.status):
        break
    vol_temp = laser.get_voltage()
    print('voltage is %f' % vol_temp)
    vol_data = vol_data[1:]+[vol_temp]
    
    #print('voltage is %f' % vol_temp)
    delta_vol = pid(vol_temp, wlm_temp, des_fre)
    print('delta_vol is %f' % delta_vol)
    while (delta_vol > 0.5 or delta_vol < -0.5):
        print('volatge gap is too big, please check data setting')
        delta_vol = delta_vol/2

    new_vol =  delta_vol + vol_temp
    laser.set_voltage(new_vol)
    time.sleep(time_interval*40)
    # pid

print('laser or wavelengthmeter turned off')
