"""
Module to work with Angstrom WS7 wavelength meter
"""

import argparse
import ctypes, os, sys, random, time

class hf_wlm(object):

    def __init__(self, dllpath="C:\Windows\System32\wlmData.dll", debug=False):
        """
        Wavelength meter class.
        Argument: Optional path to the dll. Default: "C:\Windows\System32\wlmData.dll"
        """
        self.channels = []
        self.dllpath = dllpath
        self.debug = debug
        if not debug:
            self.dll = ctypes.WinDLL(dllpath)
            self.dll.GetWavelengthNum.restype = ctypes.c_double
            self.dll.GetFrequencyNum.restype = ctypes.c_double
            self.dll.GetSwitcherMode.restype = ctypes.c_long
            self.dll.Instantiate.restype = ctypes.c_long
    # function used to monitor the state of wavelengthmeter

    def get_status(self):
        status = self.dll.Instantiate(ctypes.c_long(-1)),ctypes.c_long(0),ctypes.c_long(0),ctypes.c_long(0)
        return (status[0] > 0)

    def start(self):
        self.dll.Operation(ctypes.c_int(2))

    def start_app(self):
        cmd = "\"C:\Program Files (x86)\HighFinesse\Wavelength Meter WS8 4019\wlm_ws8.exe\""
        value = os.system(cmd)
        print(value)
        time.sleep(5)
        self.start()

    def stop(self):
        # is_closed = True
        if self.get_status():
            self.dll.Operation(ctypes.c_int(0))

    def exit_app(self):
        cmd = 'taskkill /F /IM wlm_ws8.exe'
        os.system(cmd)

    def get_exposuremode(self):
        if not self.debug:
            return (self.dll.GetExposureMode(ctypes.c_bool(0))==1)
        else:
            return True

    def set_exposuremode(self, b):
        if not self.debug:
            return self.dll.SetExposureMode(ctypes.c_bool(b))
        else:
            return 0

    def get_wavelength(self, channel=1):
        if not self.debug:
            return self.dll.GetWavelengthNum(ctypes.c_long(channel), ctypes.c_double(0))
        else:
            wavelengths = [460.8618, 689.2643, 679.2888, 707.2016, 460.8618*2, 0, 0, 0]
            if channel>5:
                return 0
            return wavelengths[channel-1] + channel * random.uniform(0,0.0001)

    def get_frequency(self, channel=1):
        # if channel<0 or channel>8:
        #    warning.warn('channel out of range')
        if not self.debug:
            return self.dll.GetFrequencyNum(ctypes.c_long(channel), ctypes.c_double(0))
        else:
            return 38434900

    def get_all(self):
        return {
            "debug": self.debug,
            "wavelength": self.get_wavelength(),
            "frequency": self.get_frequency(),
            "exposureMode": self.get_exposuremode()
        }

    @property
    def wavelengths(self):
        return [self.get_wavelength(i+1) for i in range(8)]

    @property
    def wavelength(self):
        return self.get_wavelength(1)

    @property
    def switcher_mode(self):
        if not self.debug:
        	return self.dll.GetSwitcherMode(ctypes.c_long(0))
        else:
            return 0

    @switcher_mode.setter
    def switcher_mode(self, mode):
        if not self.debug:
        	self.dll.SetSwitcherMode(ctypes.c_long(int(mode)))
        else:
            pass

if __name__ == '__main__':

    # command line arguments parsing
    parser = argparse.ArgumentParser(description='Reads out wavelength values from the High Finesse Angstrom WS7 wavemeter.')
    parser.add_argument('--debug', dest='debug', action='store_const',
                        const=True, default=False,
                        help='runs the script in debug mode simulating wavelength values')
    parser.add_argument('channels', metavar='ch', type=int, nargs='*',
                        help='channel to get the wavelength, by default all channels from 1 to 8',
                        default=range(1,8))

    args = parser.parse_args()

    wlm = WavelengthMeter(debug=args.debug)

    for i in args.channels:
        print("Wavelength at channel %d:\t%.4f nm" % (i, wlm.wavelengths[i]))

    print(wlm.wavelengths[1:6:2])
    # old_mode = wlm.switcher_mode

    # wlm.switcher_mode = True

    # print(wlm.wavelengths)
    # time.sleep(0.1)
    # print(wlm.wavelengths)

    # wlm.switcher_mode = old_mode