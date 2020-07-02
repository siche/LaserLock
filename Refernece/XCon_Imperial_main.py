# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 11:14:51 2018

@author: IonTrap/JMHeinrich

class to read the frequencies from the wavemeter and control the piezo voltage
on the two toptica digital laser controllers (= dlc). reading wavemeter data
and writing dlc piezo voltage enables digital locking of the two red and blue
lasers.

this class contains in total 29 functions:

--- WAVEMETER -----------------------------------------------------------------
-   def get_data_HF_WM(self):
    read the frequencies of the lasers blue 1 and 2, and red 1 and 2
-------------------------------------------------------------------------------

--- LASER *COLOR* *NUMBER*, with *COLOR* = blue, red and *NUMBER* = 1, 2 ------

THE 6 FUNCTIONS BELOW EXIST FOR EACH LASER ---> 24 FUNCTIONS
THE FUNCTIONS ARE IDENTICAL FOR EACH LASER ---> UNDERSTAND ONE, UNDERSTAND ALL!

-   def f_lock_laser_*COLOR*_*NUMBER*(self):
    function to lock the laser with a PI controller
    
-   def lock_laser_*COLOR*_*NUMBER*_on(self):
    needed to start the thread of function above
    
-   def lock_laser_*COLOR*_*NUMBER*_off(self):
    needed to terminate the thread/stop the lock
    
-   def f_smooth_change_laser_*COLOR*_*NUMBER*(self):
    changes the frequency smoothley between the current frequency and a target
    frequency by changing the setpoint of the PI lock
    
-   def smooth_change_laser_*COLOR*_*NUMBER*_start(self):
    needed to start the thread of the function above
    
-   def smooth_change_laser_*COLOR*_*NUMBER*_stop(self):
    needed to terminate the thread/stop the smooth detuning
-------------------------------------------------------------------------------

--- SAWTOOTH DETUNING OF THE BLUE LASERS --------------------------------------
-   def f_prepare_sawtooth_laser_blue_1_and_2(self):
    
-   def f_sawtooth_laser_blue_1_and_2(self):
-   def sawtooth_laser_blue_1_and_2_on(self):
-   def sawtooth_laser_blue_1_and_2_off(self):   
-------------------------------------------------------------------------------
"""

import time
import numpy as np
import threading
from apscheduler.schedulers.qt import QtScheduler

from library.instr_Toptica_DLC_pro import Toptica_DLC_pro
from library.instr_Highfinesse_WS8 import HighFinesse_WM

from XCon_Imperial_params import params







class laser_control(object):
    def __init__(self):
        
        #---------------------------------------------------------------------#
        #--- GLOBAL PARAMETERS AND VARIABLES ---------------------------------#
        #---------------------------------------------------------------------#
        
        #--- FREQUENCY Parameters --------------------------------------------#
        self.nu_blue_1_was, self.nu_blue_2_was, self.nu_red_1_was, self.nu_red_2_was = [0]*500, [0]*500, [0]*500, [0]*500
        self.nu_history = {'blue_1': [0]*500, 'blue_2': [0]*500, 'red_1': [0]*500, 'red_2': [0]*500}
        
        self.nu_blue_1_is, self.nu_blue_2_is, self.nu_red_1_is, self.nu_red_2_is = 0.0, 0.0, 0.0, 0.0
        self.nu = {'blue_1': 0, 'blue_2': 0, 'red_1': 0, 'red_2': 0}
        self.nu_prev = self.nu.copy()
        
        self.nu_blue_1_want, self.nu_blue_2_want, self.nu_red_1_want, self.nu_red_2_want = 755.186770, 0.0, 0.0, 0.0
        self.nu_setpoint = self.nu.copy()
        
        self.nu_blue_1_smooth_flag, self.nu_blue_2_smooth_flag, self.nu_red_1_smooth_flag, self.nu_red_2_smooth_flag = 1, 1, 1, 1
        self.nu_blue_1_smooth_want, self.nu_blue_2_smooth_want, self.nu_red_1_smooth_want, self.nu_red_2_smooth_want = 755.186770, 0.0, 0.0, 0.0
        self.nu_blue_1_smooth_delta_t, self.nu_blue_2_smooth_delta_t, self.nu_red_1_smooth_delta_t, self.nu_red_2_smooth_delta_t = 10.0, 10.0, 10.0, 10.0
        
        self.nu_smooth_increment = 0.000001
        #---------------------------------------------------------------------#
        
        #--- PIEZO Parameters ------------------------------------------------#
        self.nu_blue_1_piezo_set, self.nu_blue_2_piezo_set, self.nu_red_1_piezo_set, self.nu_red_2_piezo_set = 0.0, 0.0, 0.0, 0.0
        #---------------------------------------------------------------------#
        
        #--- LOCKING Parameters ----------------------------------------------#
        self.lock_blue_1 = False
        self.lock_lasers = {'blue_1': False, 'blue_2': False, 'red_1': False, 'red_2': False}
        self.lock_blue_2_flag, self.lock_red_1_flag, self.lock_red_2_flag = 1, 1, 1
        
        self.lock_blue_1_alpha, self.lock_blue_2_alpha, self.lock_red_1_alpha, self.lock_red_2_alpha = 20., 20., 20., 20.    
        self.lock_blue_1_beta, self.lock_blue_2_beta, self.lock_red_1_beta, self.lock_red_2_beta = 15., 15., 15., 15.
        
        default_lock_pars = {'k_p': 20, 'k_i': 20}
        self.lock_pars = {'blue_1': default_lock_pars.copy(), 'blue_2': default_lock_pars.copy(),
                          'red_1': default_lock_pars.copy(), 'red_2': default_lock_pars.copy()}
        
        self.lock_blue_1_Integral, self.lock_blue_2_Integral, self.lock_red_1_Integral, self.lock_red_2_Integral = 0.0, 0.0, 0.0, 0.0   
        
        self.errors_previous = {'blue_1': 0, 'blue_2': 0, 'red_1': 0, 'red_2': 0}
      
        #Lock error counters
        self.lock_blue_1_count, self.lock_blue_2_count, self.lock_red_1_count, self.lock_red_2_count = 0, 0, 0, 0
        self.lock_count = {'blue_1': 0, 'blue_2': 0, 'red_1': 0, 'red_2': 0}
        #---------------------------------------------------------------------#

        #--- SAWTOOTH Parameters ---------------------------------------------#
        self.sawtooth_flag = 1
        self.sawtooth_nu_blue_1_init = 755.186880
        self.sawtooth_nu_blue_1_detuned = 755.186780
        self.sawtooth_nu_blue_2_init = 755.258220
        self.sawtooth_nu_blue_2_detuned = 755.258120
        self.sawtooth_delta_t1 = 1.5
        self.sawtooth_delta_t2 = 0.75
        self.sawtooth_t_incr = 0.05
        self.sawtooth_total_reps = 1
        
        self.sawtooth_t_total = []
        self.sawtooth_nu1_total = []
        self.sawtooth_nu2_total = []
        #---------------------------------------------------------------------#
        
        #--- Debug vars ------------------------------------------------------#
        self.debug_flag = False
        self.debug_number = 10

        #---------------------------------------------------------------------#
        #---------------------------------------------------------------------#
        #---------------------------------------------------------------------#


        
        #---------------------------------------------------------------------#
        #--- CREATE INSTANCES OF WM AND LASER CONTROLLERS --------------------#
        #---------------------------------------------------------------------#
        
        #---------------------------------------------------------------------#
        self.HF_WM = HighFinesse_WM()
        #---------------------------------------------------------------------#
        
        #---------------------------------------------------------------------#
        self.T_DLC_blues = Toptica_DLC_pro('192.168.0.2')
        self.lock_blue_1_piezo_volt_set = float(self.T_DLC_blues.read_parameter('laser1:dl:pc:voltage-set'))
        self.lock_blue_2_piezo_volt_set = float(self.T_DLC_blues.read_parameter('laser2:dl:pc:voltage-set'))
        #---------------------------------------------------------------------#
        self.lock_blue_1_piezo_volt_init = self.lock_blue_1_piezo_volt_set
        self.lock_blue_2_piezo_volt_init = self.lock_blue_2_piezo_volt_set
        #---------------------------------------------------------------------#
        self.T_DLC_reds = Toptica_DLC_pro('192.168.0.3')
        self.lock_red_1_piezo_volt_set = float(self.T_DLC_reds.read_parameter('laser1:dl:pc:voltage-set'))
        self.lock_red_2_piezo_volt_set = float(self.T_DLC_reds.read_parameter('laser2:dl:pc:voltage-set'))
        #---------------------------------------------------------------------#
        self.lock_red_1_piezo_volt_init = self.lock_red_1_piezo_volt_set
        self.lock_red_2_piezo_volt_init = self.lock_red_2_piezo_volt_set
        
        self.piezo_volt = {'blue_1': self.lock_blue_1_piezo_volt_set, 'blue_2': self.lock_blue_2_piezo_volt_set,
                           'red_1': self.lock_red_1_piezo_volt_set, 'red_2': self.lock_red_2_piezo_volt_set}
        
        #---------------------------------------------------------------------#
        #---------------------------------------------------------------------#
        #---------------------------------------------------------------------#
        
        
        
        #---------------------------------------------------------------------#
        #--- SCHEDULE ITERATIVE JOBS TO GET DATA FROM WM ---------------------#
        #---------------------------------------------------------------------#    
        
        #---------------------------------------------------------------------#
        self.program_scheduler = QtScheduler()
        self.program_scheduler.start()
        #---------------------------------------------------------------------#
        
        #---------------------------------------------------------------------#
        self.program_scheduler.add_job(self.control_loop, 'interval', seconds = 0.05, id='id_update_wm_data')
        #---------------------------------------------------------------------#

        #---------------------------------------------------------------------#
        #---------------------------------------------------------------------#
        #---------------------------------------------------------------------#
        
        

    ###########################################################################
    ###########################################################################
    ### THE FUNCTIONS BASED ON THE TWO OBJECTS WM AND TLC #####################
    ###########################################################################
    ###########################################################################  

    #-- MAIN CONTROL LOOP ----------------------------------------------------#
    def control_loop(self):
        self.get_data_HF_WM()
        
        if self.lock_lasers['blue_1']:
            self.lock_laser('blue_1')
        if self.lock_lasers['blue_2']:
            self.lock_laser('blue_2')

    ###########################################################################
    ### FUNCTION TO GET THE WAVEMETER DATA ####################################
    ###########################################################################    
    #--- get the data for the WS8 wavemeter ----------------------------------#       
    def get_data_HF_WM(self):
        '''
            reads the frequencies on the four wavemeter channels 1,2,3,4.
            transforms them from THz to 100kHz (integers) and back to THz
            
            appends the values to a list to monitor the time dependence of the
            frequency
        '''
        
        self.nu_red_1_is = int(self.HF_WM.get_frequency(3) * 10**7)/10**7
        self.nu_red_2_is = int(self.HF_WM.get_frequency(4) * 10**7)/10**7
        
        self.nu['blue_1'] = self.HF_WM.get_frequency(1)
        self.nu['blue_2'] = self.HF_WM.get_frequency(2)
        
        self.nu_history['blue_1'].append(self.nu['blue_1'])
        self.nu_history['blue_2'].append(self.nu['blue_2'])
        
        self.nu_blue_1_was.append(self.nu_blue_1_is)
        self.nu_blue_2_was.append(self.nu_blue_2_is)
        self.nu_red_1_was.append(self.nu_red_1_is)
        self.nu_red_2_was.append(self.nu_red_2_is)
    #-------------------------------------------------------------------------#
    ###########################################################################
    ###########################################################################
    ###########################################################################

    
    
    ###########################################################################
    ### FUNCTIONS FOR LASER BLUE 1 ############################################
    ###########################################################################
    #--- function to lock laser ---------------------------------------#
    def lock_laser_setup(self, laser_id):
        if laser_id == 'blue_2':
            self.debug_flag = False
            self.debug_counter = 0
            
        self.errors_previous[laser_id] = 0.0
    

        

    def lock_laser(self, laser_id):
        
        '''
            a PI controller is
            implemented, with gains alpha for the proportional and beta for the
            integral part.
            
            the if statement at the end ensures that there are no big jumps in
            the piezo voltage, which might be applied otherwise if there is
            mode jumping in the laser. for too big voltage jumps the lock
            breaks.
        '''

        nu_is = self.nu[laser_id]
        nu_wanted = self.nu_setpoint[laser_id]
        
        error = nu_wanted - nu_is
        error_previous = self.errors_previous[laser_id]
        self.errors_previous[laser_id] = error
        
        k_p = self.lock_pars[laser_id]['k_p']
        k_i = self.lock_pars[laser_id]['k_i']
        
        #------------------------------------------------#
                   
        # proportional part -----------------------------#
        P_part = k_p * (error - error_previous)
        #------------------------------------------------#
        
        # integral part ---------------------------------#
        I_part = k_i * error
        #------------------------------------------------#

        # prop + in + current set voltage ---------------#
        new_piezo_value = P_part + I_part + self.piezo_volt[laser_id]
        #------------------------------------------------#
        
        
        # debug information -----------------------------#
        if laser_id == 'blue_2':        # restricted to blue 2 for now
            if self.debug_flag: 
                if self.debug_counter == 0:
                    self.t0 = time.monotonic()
                    print(f'initial nu: {nu_is}')
                    print(f'initial piezo value: {self.lock_blue_2_piezo_volt_set}' )
                    print(f'k_p: {k_p}, k_i: {k_i}')
                    
                    self.summed_ms_error = 0.0
                    self.debug_counter = 1
                    self.errors = np.zeros(self.debug_number)     # this will cause issues if self.debug_number is updated during debugging...
                elif self.debug_counter <= self.debug_number:
                    print(f'time: {(time.monotonic()-self.t0):.2}, nu: {nu_is}, error: {error*1e6:.8}MHz')
                    print(f'  prop: {P_part:.8}, int: {I_part:.8}, new pzt value: {new_piezo_value:.8}')
                    
                    self.errors[self.debug_counter-1] = error
                    self.summed_ms_error += error**2
                    self.debug_counter += 1
                else:
                    rmserror = np.sqrt( self.summed_ms_error/self.debug_counter )
                    print(f'rms error: {rmserror*1e6} MHz')
                    stddev = np.std(self.errors)
                    print(f'std error: {stddev*1e6} MHz')
                    self.debug_flag = False
                    self.debug_counter = 0
        
        # restrict voltage jumps
        if -1 <= (P_part + I_part) <= 1:
            self.set_piezo(new_piezo_value, laser_id)
            self.piezo_volt[laser_id] = new_piezo_value
            self.lock_count[laser_id] = 0
            
        else:
            if self.lock_count[laser_id] < 10:
                self.lock_count[laser_id] += 1
                pass
            else:
                print(f'break lock for laser {laser_id}, delta in piezo voltage too large!')
                self.lock_lasers[laser_id] = False
                self.lock_count[laser_id] = 0
    #-------------------------------------------------------------------------#

    def set_piezo(self, piezo_value, laser_id):
        if laser_id == 'blue_1':
            self.T_DLC_blues.set_parameter('laser1:dl:pc:voltage-set', piezo_value)
        elif laser_id == 'blue_2':
            self.T_DLC_blues.set_parameter('laser2:dl:pc:voltage-set', piezo_value)
        
        
    def lock_laser_on(self, laser_id):
        
        if not self.lock_lasers[laser_id]:
            self.lock_laser_setup(laser_id)
            self.lock_lasers[laser_id] = True
            print(f'Lock for laser {laser_id} turned ON')
        else:
            print(f'{laser_id} lock already engaged')  
    
    def lock_laser_off(self, laser_id):
        print(f'Lock for laser {laser_id} turned OFF')
        self.lock_lasers[laser_id] = False
    #-------------------------------------------------------------------------#
    
    
    
    #--- function to smoothley detune laser blue 1 ---------------------------#
    def f_smooth_change_laser_blue_1(self):
        '''
            function to smoothley tune laser blue 1 between two frequencies.
            takes nu_start and nu_stop, and the time delay in between. stepsize
            is fixed to 1MHz.
            
            the function first creates a list with the intermediate frequency
            values and the sleep time in between the steps. then it updates the
            wanted frequency using the set point frequency of the lock, and
            waits for the duration of the sleep time.
        '''
        
        laser_id = 'blue_1'
        
        nu_start_MHz = int(self.nu[laser_id] * 10**6)
        nu_stop_MHz = int(self.nu_blue_1_smooth_want * 10**6)
        nu_incr_MHz = int(self.nu_smooth_increment * 10**6)
        delta_t = self.nu_blue_1_smooth_delta_t
        
        if nu_start_MHz < nu_stop_MHz:
            nu_list_MHz = np.arange(nu_start_MHz + nu_incr_MHz, nu_stop_MHz + nu_incr_MHz, nu_incr_MHz)
        elif nu_start_MHz > nu_stop_MHz:
            nu_list_MHz = np.arange(nu_stop_MHz, nu_start_MHz + nu_incr_MHz, nu_incr_MHz)
            nu_list_MHz = nu_list_MHz[::-1]
            
        nu_list = nu_list_MHz/10**6
        
        t_increment = delta_t/float(len(nu_list))
        
        for i in range(len(nu_list)):
            
            if self.nu_blue_1_smooth_flag == 0:
                self.nu_setpoint[laser_id] = nu_list[i]
                                
                time.sleep(t_increment)
                
            else:
                break
    #-------------------------------------------------------------------------#  
        
    #--- start thread calling function to smoothley detune laser blue 1 ------#
    def smooth_change_laser_blue_1_start(self):
        '''
            function which starts the thread with the function of the smooth
            change of the frequency for laser blue 1
        '''
        
        print('smooth change laser blue 1 STARTED')
        
        self.nu_blue_1_smooth_flag = 0

        thread_smooth_change_blue_1 = threading.Thread(target = self.f_smooth_change_laser_blue_1)         
        thread_smooth_change_blue_1.start()
    #-------------------------------------------------------------------------#

    #--- start thread calling function to smoothley detune laser blue 1 ------#
    def smooth_change_laser_blue_1_stop(self):
        '''
            function which terminates the thread with the function of the
            smooth change of the frequency for laser blue 1
        '''
        
        print('smooth change laser blue 1 STOPPED')
        
        self.nu_blue_1_smooth_flag = 1
    #-------------------------------------------------------------------------#        
    ###########################################################################
    ###########################################################################
    ###########################################################################
    
    
    
    
    
    
    
    #--- function to smoothley detune laser blue 1 ---------------------------#
    def f_smooth_change_laser_blue_2(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        laser_id = 'blue_2'
        
        nu_start_MHz = int(self.nu[laser_id] * 10**6)
        nu_stop_MHz = int(self.nu_blue_2_smooth_want * 10**6)
        nu_incr_MHz = int(self.nu_smooth_increment * 10**6)
        delta_t = self.nu_blue_2_smooth_delta_t
        
        if nu_start_MHz < nu_stop_MHz:
            nu_list_MHz = np.arange(nu_start_MHz + nu_incr_MHz, nu_stop_MHz + nu_incr_MHz, nu_incr_MHz)
        elif nu_start_MHz > nu_stop_MHz:
            nu_list_MHz = np.arange(nu_stop_MHz, nu_start_MHz + nu_incr_MHz, nu_incr_MHz)
            nu_list_MHz = nu_list_MHz[::-1]
            
        nu_list = nu_list_MHz/10**6
        
        t_increment = delta_t/float(len(nu_list))
        
        for i in range(len(nu_list)):
            
            if self.nu_blue_2_smooth_flag == 0:
            
                self.nu_setpoint[laser_id] = nu_list[i]
                                
                time.sleep(t_increment)
                
            else:
                break
    #-------------------------------------------------------------------------#  
        
    #--- start thread calling function to smoothley detune laser blue 1 ------#
    def smooth_change_laser_blue_2_start(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('smooth change laser blue 2 STARTED')
        
        self.nu_blue_2_smooth_flag = 0

        thread_smooth_change_blue_2 = threading.Thread(target = self.f_smooth_change_laser_blue_2)         
        thread_smooth_change_blue_2.start()
    #-------------------------------------------------------------------------#

    #--- start thread calling function to smoothley detune laser blue 1 ------#
    def smooth_change_laser_blue_2_stop(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('smooth change laser blue 2 STOPPED')
        
        self.nu_blue_2_smooth_flag = 1
    #-------------------------------------------------------------------------# 
    ###########################################################################
    ###########################################################################
    ###########################################################################


    ###########################################################################
    ### FUNCTIONS FOR LASER RED 1 #############################################
    ###########################################################################
    #--- function to lock laser red 1 ----------------------------------------#
    def f_lock_laser_red_1(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        while self.lock_red_1_flag == 0:
            
            # copy parameters to be fixed for this iteration #
            nu_is = self.nu_red_1_is
            nu_wanted = self.nu_red_1_want
            
            nu_error = nu_wanted - nu_is
            
            alpha = self.lock_red_1_alpha
            beta = self.lock_red_1_beta
            #------------------------------------------------#
                       
            # proportional part -----------------------------#
            P_part = alpha * nu_error
            #------------------------------------------------#
            
            # integral part ---------------------------------#
            I_part = beta * self.lock_red_1_Integral
            self.lock_red_1_Integral += nu_error
            #------------------------------------------------#

            # prop + in + current set voltage ---------------#
            PI = P_part + I_part + self.lock_red_1_piezo_volt_set
            #------------------------------------------------#
            
            # sleep time - to be synchronized with data gathering from wm #
            time.sleep(0.05)
            #------------------------------------------------#
            
            # restrict voltage jumps NEEDS TO BE DONE MORE CLEVER!
            if self.lock_red_1_piezo_volt_init - 5 <= PI <= self.lock_red_1_piezo_volt_init + 5:

                self.T_DLC_reds.set_parameter('laser1:dl:pc:voltage-set', PI)
                self.lock_red_1_piezo_volt_set = PI
                self.lock_red_1_count = 0
                
            else:
                if self.lock_red_1_count < 10:
                    self.lock_red_1_count += 1
                    pass
                else:
                    print('break lock for laser red 1, delta in piezo voltage too large!')
                    self.lock_red_1_flag = 1
                    self.lock_red_1_count = 0
    #-------------------------------------------------------------------------#           
                
    #--- start thread calling function to lock laser blue 1 ------------------#        
    def lock_laser_red_1_on(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('lock laser red 1 turned ON')
        
        self.lock_red_1_flag = 0

        thread_lock_red_1 = threading.Thread(target = self.f_lock_laser_red_1)         
        thread_lock_red_1.start()
    #-------------------------------------------------------------------------#   
        
    #--- stop thread calling function to lock laser blue 1 -------------------#    
    def lock_laser_red_1_off(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('lock laser red 1 turned OFF')
        
        self.lock_red_1_flag = 1
    #-------------------------------------------------------------------------#
    
    
    
    #--- function to smoothley detune laser blue 1 ---------------------------#
    def f_smooth_change_laser_red_1(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        nu_start_MHz = int(self.nu_red_1_is * 10**6)
        nu_stop_MHz = int(self.nu_red_1_smooth_want * 10**6)
        nu_incr_MHz = int(self.nu_smooth_increment * 10**6)
        delta_t = self.nu_red_1_smooth_delta_t
        
        if nu_start_MHz < nu_stop_MHz:
            nu_list_MHz = np.arange(nu_start_MHz + nu_incr_MHz, nu_stop_MHz + nu_incr_MHz, nu_incr_MHz)
        elif nu_start_MHz > nu_stop_MHz:
            nu_list_MHz = np.arange(nu_stop_MHz, nu_start_MHz + nu_incr_MHz, nu_incr_MHz)
            nu_list_MHz = nu_list_MHz[::-1]
            
        nu_list = nu_list_MHz/10**6
        
        t_increment = delta_t/float(len(nu_list))
        
        for i in range(len(nu_list)):
            
            if self.nu_red_1_smooth_flag == 0:
            
                self.nu_red_1_want = nu_list[i]
                                
                time.sleep(t_increment)
                
            else:
                break
    #-------------------------------------------------------------------------#  
        
    #--- start thread calling function to smoothley detune laser blue 1 ------#
    def smooth_change_laser_red_1_start(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('smooth change laser red 1 STARTED')
        
        self.nu_red_1_smooth_flag = 0

        thread_smooth_change_red_1 = threading.Thread(target = self.f_smooth_change_laser_red_1)         
        thread_smooth_change_red_1.start()
    #-------------------------------------------------------------------------#

    #--- start thread calling function to smoothley detune laser blue 1 ------#
    def smooth_change_laser_red_1_stop(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('smooth change laser red 1 STOPPED')
        
        self.nu_red_1_smooth_flag = 1
    #-------------------------------------------------------------------------# 
    ###########################################################################
    ###########################################################################
    ###########################################################################




    ###########################################################################
    ### FUNCTIONS FOR LASER RED 2 #############################################
    ###########################################################################
    #--- function to lock laser red 1 ----------------------------------------#
    def f_lock_laser_red_2(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        while self.lock_red_2_flag == 0:
            
            # copy parameters to be fixed for this iteration #
            nu_is = self.nu_red_2_is
            nu_wanted = self.nu_red_2_want
            
            nu_error = nu_wanted - nu_is
            
            alpha = self.lock_red_2_alpha
            beta = self.lock_red_2_beta
            #------------------------------------------------#
                       
            # proportional part -----------------------------#
            P_part = alpha * nu_error
            #------------------------------------------------#
            
            # integral part ---------------------------------#
            I_part = beta * self.lock_red_2_Integral
            self.lock_red_2_Integral += nu_error
            #------------------------------------------------#

            # prop + in + current set voltage ---------------#
            PI = P_part + I_part + self.lock_red_2_piezo_volt_set
            #------------------------------------------------#
            
            # sleep time - to be synchronized with data gathering from wm #
            time.sleep(0.05)
            #------------------------------------------------#
            
            # restrict voltage jumps NEEDS TO BE DONE MORE CLEVER!
            if self.lock_red_2_piezo_volt_init - 5 <= PI <= self.lock_red_2_piezo_volt_init + 5:

                self.T_DLC_reds.set_parameter('laser2:dl:pc:voltage-set', PI)
                self.lock_red_2_piezo_volt_set = PI
                self.lock_red_2_count = 0
                
            else:
                if self.lock_red_2_count < 10:
                    self.lock_red_2_count += 1
                    pass
                else:
                    print('break lock for laser red 2, delta in piezo voltage too large!')
                    self.lock_red_2_flag = 1
                    self.lock_red_2_count = 0
    #-------------------------------------------------------------------------#           
                
    #--- start thread calling function to lock laser blue 1 ------------------#        
    def lock_laser_red_2_on(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('lock laser red 2 turned ON')
        
        self.lock_red_2_flag = 0

        thread_lock_red_2 = threading.Thread(target = self.f_lock_laser_red_2)         
        thread_lock_red_2.start()
    #-------------------------------------------------------------------------#   
        
    #--- stop thread calling function to lock laser blue 1 -------------------#    
    def lock_laser_red_2_off(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('lock laser red 2 turned OFF')
        
        self.lock_red_2_flag = 1
    #-------------------------------------------------------------------------#
    
    
    
    #--- function to smoothley detune laser blue 1 ---------------------------#
    def f_smooth_change_laser_red_2(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        nu_start_MHz = int(self.nu_red_2_is * 10**6)
        nu_stop_MHz = int(self.nu_red_2_smooth_want * 10**6)
        nu_incr_MHz = int(self.nu_smooth_increment * 10**6)
        delta_t = self.nu_red_2_smooth_delta_t
        
        if nu_start_MHz < nu_stop_MHz:
            nu_list_MHz = np.arange(nu_start_MHz + nu_incr_MHz, nu_stop_MHz + nu_incr_MHz, nu_incr_MHz)
        elif nu_start_MHz > nu_stop_MHz:
            nu_list_MHz = np.arange(nu_stop_MHz, nu_start_MHz + nu_incr_MHz, nu_incr_MHz)
            nu_list_MHz = nu_list_MHz[::-1]
            
        nu_list = nu_list_MHz/10**6
        
        t_increment = delta_t/float(len(nu_list))
        
        for i in range(len(nu_list)):
            
            if self.nu_red_2_smooth_flag == 0:
            
                self.nu_red_2_want = nu_list[i]
                                
                time.sleep(t_increment)
                
            else:
                break
    #-------------------------------------------------------------------------#  
        
    #--- start thread calling function to smoothley detune laser blue 1 ------#
    def smooth_change_laser_red_2_start(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('smooth change laser red 2 STARTED')
        
        self.nu_red_2_smooth_flag = 0

        thread_smooth_change_red_2 = threading.Thread(target = self.f_smooth_change_laser_red_2)         
        thread_smooth_change_red_2.start()
    #-------------------------------------------------------------------------#

    #--- start thread calling function to smoothley detune laser blue 1 ------#
    def smooth_change_laser_red_2_stop(self):
        '''
            for explanation see same function for laser blue 1
        '''
        
        print('smooth change laser red 2 STOPPED')
        
        self.nu_red_2_smooth_flag = 1
    #-------------------------------------------------------------------------# 
    ###########################################################################
    ###########################################################################
    ###########################################################################



    ###########################################################################
    ###########################################################################
    ###########################################################################
    #--- function prepare lists for sawtooth detuning laser blue 1 -----------#
    def f_prepare_sawtooth_laser_blue_1_and_2(self):
        '''
            this function takes the initial and detuned (target) values for the
            frequencies of the two blue lasers, and the two timesteps delta_t1
            and delta_t2 which characterise the time to detune and the time to
            come back to the starting frequency
        '''
        
        nu1_init_MHz = self.sawtooth_nu_blue_1_init
        nu1_detuned_MHz = self.sawtooth_nu_blue_1_detuned
        nu2_init_MHz = self.sawtooth_nu_blue_2_init
        nu2_detuned_MHz = self.sawtooth_nu_blue_2_detuned
        
        delta_t1 = self.sawtooth_delta_t1
        delta_t2 = self.sawtooth_delta_t2
        
        t_incr = self.sawtooth_t_incr
        
        total_reps = self.sawtooth_total_reps
        

        delta_t1_list = np.arange(0.00, delta_t1 + t_incr, t_incr)
        delta_t2_list = np.arange(delta_t1 + t_incr, delta_t1 + delta_t2 + t_incr, t_incr)
        
        nu1_t1_list = np.linspace(nu1_init_MHz, nu1_detuned_MHz, len(delta_t1_list))
        nu1_t2_list = np.linspace(nu1_detuned_MHz, nu1_init_MHz, len(delta_t2_list))
        
        nu2_t1_list = np.linspace(nu2_init_MHz, nu2_detuned_MHz, len(delta_t1_list))
        nu2_t2_list = np.linspace(nu2_detuned_MHz, nu2_init_MHz, len(delta_t2_list))

        delta_t_list = np.concatenate([delta_t1_list, delta_t2_list])
        nu1_list = np.concatenate([nu1_t1_list, nu1_t2_list])
        nu2_list = np.concatenate([nu2_t1_list, nu2_t2_list])
        
        t_tot = []
        nu1_tot = []
        nu2_tot = []
        for i in range(total_reps):
            temp_delta_t_list = delta_t_list + i*(delta_t1+delta_t2+t_incr)
            temp_nu1_list = nu1_list[:]
            temp_nu2_list = nu2_list[:]
            
            t_tot.append(temp_delta_t_list)
            nu1_tot.append(temp_nu1_list)
            nu2_tot.append(temp_nu2_list)
            
        self.sawtooth_t_total = np.concatenate(t_tot)
        self.sawtooth_nu1_total = np.concatenate(nu1_tot)
        self.sawtooth_nu2_total = np.concatenate(nu2_tot)
    #-------------------------------------------------------------------------#



    #--- function prepare lists for sawtooth detuning laser blue 1 -----------#
    def f_sawtooth_laser_blue_1_and_2(self):
    
        t_list = self.sawtooth_t_total
        nu_1_list = self.sawtooth_nu1_total
        nu_2_list = self.sawtooth_nu2_total
        
        sleep_time = t_list[1] - t_list[0]

        for i in range(len(t_list)):
            if self.sawtooth_flag == 0:
                self.nu_setpoint['blue_1'] = nu_1_list[i]
                self.nu_setpoint['blue_2'] = nu_2_list[i]
                time.sleep(sleep_time)
            else:
                self.sawtooth_flag = 1
                break
    #-------------------------------------------------------------------------#

    #--- start thread calling function to sawtooth lasers 1 and 2 ------------#        
    def sawtooth_laser_blue_1_and_2_on(self):
        
        print('sawtooth laser blue 1 and 2 turned ON')
        
        self.sawtooth_flag = 0

        thread_sawtooth = threading.Thread(target = self.f_sawtooth_laser_blue_1_and_2)         
        thread_sawtooth.start()
    #-------------------------------------------------------------------------#   
        
    #--- stop thread calling function to sawtooth lasers 1 and 2 -------------#    
    def sawtooth_laser_blue_1_and_2_off(self):
        
        print('sawtooth laser blue 1 and 2 turned OFF')
        
        self.sawtooth_flag = 1
    #-------------------------------------------------------------------------#
    ###########################################################################
    ###########################################################################
    ###########################################################################