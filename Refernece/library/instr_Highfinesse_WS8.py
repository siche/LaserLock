# -*- coding: utf-8 -*-
"""
Created on Wed Nov  7 16:49:12 2018

@author: IonTrap/JMHeinrich
"""

import ctypes



class HighFinesse_WM(object):
    
    def __init__(self):
        
        ''' loads the dll-library of the wavemeter ''' 
        self.dll_HF = ctypes.windll.LoadLibrary('C:\\Windows\\System32\\wlmData.dll')
        
        ''' declare the ctypes for arguments and return values of the
            wavemeter '''    
        self.dll_HF.GetTemperature.restype = ctypes.c_double
            
        self.dll_HF.GetFrequencyNum.restype = ctypes.c_double
        self.dll_HF.GetFrequencyNum.argtype = ctypes.c_double
        
        self.dll_HF.ControlWLM.restype = ctypes.c_long
        self.dll_HF.ControlWLM.argtypes = [ctypes.c_long,ctypes.c_long,ctypes.c_long]   

        ''' check if the wavemeter is online and accessible ''' 
        test_temp = self.get_temperature()
        
        if test_temp == -1005.0:
            print('wavemeter WS8 is OFFLINE')
            print('---> to fix, start the commercial software "Wavelength Meter"')
        else:
            print('wavemeter WS8 is online')



    def get_temperature(self):
        '''implemented as first test function to speak to the wavemeter.
           returns the temperature
           '''        
        
        temperature = self.dll_HF.GetTemperature()
        
        return temperature
    
    
    def get_frequency(self, channel):
        '''takes the channel number channel as input and returns the measured
           frequency at that channel'''
           
        frequency = self.dll_HF.GetFrequencyNum(channel)
        
        return frequency  