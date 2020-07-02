# -*- coding: utf-8 -*-
"""
Created on Thu Nov 15 18:02:31 2018

@author: IonTrap
"""

import ctypes


class HFError(RuntimeError):
    """Generic HighFinesse wavemeter error."""

class WS(object):
    """
    WS precision wavemeter.
    """
    def __init__(self, lib_path=None, idx=0):
        object.__init__(self)

        self.dll=ctypes.windll.LoadLibrary('C:\\Windows\\System32\\wlmData.dll')
        self.dll.Instantiate.restype=ctypes.c_long
        self.dll.Instantiate.argtypes=[ctypes.c_long,ctypes.c_long,ctypes.c_long,ctypes.c_long]
        self.dll.GetFrequencyNum.restype=ctypes.c_double
        self.dll.GetFrequencyNum.argtypes=[ctypes.c_long,ctypes.c_double]
        self.dll.GetExposureModeNum.restype=ctypes.c_bool
        self.dll.GetExposureModeNum.argtypes=[ctypes.c_long,ctypes.c_bool]
        self.dll.SetExposureModeNum.restype=ctypes.c_long
        self.dll.SetExposureModeNum.argtypes=[ctypes.c_long,ctypes.c_bool]
        self.dll.GetExposureNum.restype=ctypes.c_long
        self.dll.GetExposureNum.argtypes=[ctypes.c_long,ctypes.c_long,ctypes.c_long]
        self.dll.SetExposureNum.restype=ctypes.c_long
        self.dll.SetExposureNum.argtypes=[ctypes.c_long,ctypes.c_long,ctypes.c_long]
        self.idx=idx
        self.open()

    def open(self):
        self.dll.Instantiate(-1,0,0,0)
    def close(self):
        pass

    def __enter__(self):
        return self
    def __exit__(self, *args, **vargs):
        return False
    
    _GetFunc_err={  0:"ErrNoValue: No value",
                            -1:"ErrNoSignal: No signal detected",
                            -2:"ErrBadSignal: No calculable signal detected",
                            -3:"ErrLowSignal: Signal too small / underexposed",
                            -4:"ErrBigSignal: Signal too big / overexposed",
                            -5:"ErrWlmMissing: Wavelength meter is not active", 
                            -6:"ErrNotAvailable: Function is not available", 
                            -8:"ErrNoPulse: Signal can't be separated into pulses", 
                            -7:"InfNothingChanged",
                            -13:"ErrDiv0", 
                            -14:"ErrOutOfRange", 
                            -15:"ErrUnitNotAvaliable"}
    def _check_getfunc_error(self, func_name, err):
        if err>=0:
            return
        if err in self._GetFunc_err:
            raise HFError("{} returned error: {} ({})".format(func_name,err,self._GetFunc_err[err]))
        else:
            raise HFError("{} returned unknown error: {}".format(func_name,err))
    _SetFunc_err={  0:"ResERR_NoErr: No error",
                    -1:"ResERR_WlmMissing: Wavelength meter is not active",
                    -2:"ResERR_CouldNotSet: Could not set value which should be accessible (contact Angstrom)",
                    -3:"ResERR_ParmOutOfRange: Parameter is out of range",
                    -4:"ResERR_WlmOutOfResources: Wavelength meter is out of memory or resources (contact Angstrom if persists)",
                    -5:"ResERR_WlmInternalError: Wavelength meter internal error (contact Angstrom)", 
                    -6:"ResERR_NotAvailable: Parameter setting is not available for this wavelength meter version", 
                    -7:"ResERR_WlmBusy: Wavelength meter is busy with another function (contact Angstrom if persists)", 
                    -8:"ResERR_NotInMeasurementMode: Call is not allowed in measurement mode", 
                    -9:"ResERR_OnlyInMeasurementMode: Call is only allowed in measurement mode", 
                    -10:"ResERR_ChannelNotAvailable: Given channel is not available for this device", 
                    -11:"ResERR_ChannelTemporarilyNotAvailable: Given channel is generally available, but the device is not in switch mode", 
                    -12:"ResERR_CalOptionNotAvailable: Wavelength meter does not dispose of this calibration option", 
                    -13:"ResERR_CalWavelengthOutOfRange: The given calibration wavelength is out of its allowed range", 
                    -14:"ResERR_BadCalibrationSignal: The given wavelength does not match the connected calibration laser or its signal is of bad quality", 
                    -15:"ResERR_UnitNotAvailable: This is not a proper result unit"}
    def _check_setfunc_error(self, func_name, err):
        if err>0:
            return
        if err in self._SetFunc_err:
            raise HFError("{} returned error: {} ({})".format(func_name,err,self._SetFunc_err[err]))
        else:
            raise HFError("{} returned unknown error: {}".format(func_name,err))
    def get_frequency(self, return_exp_error=True):
        res=self.dll.GetFrequencyNum(self.idx,0.)
        if int(res)<=0:
            err=int(res)
            if return_exp_error:
                if err==-3:
                    return "under"
                if err==-4:
                    return "over"
            self._check_getfunc_error("GetFrequencyNum",err)
        return res*1E12

    def get_exposure_mode(self):
        return self.dll.GetExposureModeNum(self.idx,0)
    def set_exposure_mode(self, auto_exposure=True):
        err=self.dll.GetExposureModeNum(self.idx,1 if auto_exposure else 0)
        self._check_setfunc_error("SetExposureModeNum",err)
        return self.get_exposure_mode()

    def get_exposure(self, sensor=1):
        exposure=self.dll.GetExposureNum(self.idx,sensor,0)
        self._check_getfunc_error("GetExposureNum",exposure)
        return exposure
    def set_exposure(self, exposure, sensor=1):
        err=self.dll.SetExposureNum(self.idx,sensor,exposure)
        self._check_setfunc_error("SetExposureNum",err)
        return self.get_exposure()