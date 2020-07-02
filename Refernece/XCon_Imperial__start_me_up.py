# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 17:29:59 2018

@author: IonTrap/JMHeinrich
"""

import sys
import time
from PyQt5 import QtWidgets, QtCore
import numpy as np
import pyqtgraph as pg

from XCon_Imperial_params import params
from XCon_Imperial_main import laser_control
from XCon_Imperial_GUI import Ui_XCon_Imperial

brush_background = (255,255,255,255)

blueBrush = (109,123,205,255)
blueBrush_alpha = (109,123,205,100)
bluePen = pg.mkPen(color = blueBrush, width = 2)

redBrush = (209,111,111,255)
redBrush_alpha = (209,111,111,100)
redPen = pg.mkPen(color = redBrush, width = 2)

blackBrush = (0,0,0,255)
blackPen = pg.mkPen(color = blackBrush, width = 2) 

labelstyle_L = {'color': '#000', 'font-size': '12pt'}

class window(Ui_XCon_Imperial):
    
    def __init__(self, dialog, laser_control):
        Ui_XCon_Imperial.__init__(self)
        self.setupUi(dialog)
        self.mainWindow = dialog
        print('initialising gui')



        self.pushButton_debug.clicked.connect(self.pushButton_debug_clicked)
        
        #---------------------------------------------------------------------#
        #--- SET DEFAULT PARAMETERS ------------------------------------------#
        #---------------------------------------------------------------------#
        self.spinBox_debug.setValue(params['debug']['number'])
        
        self.doubleSpinBox_lock_blue_1_k_p.setValue(params['lock']['blue_1']['k_p'])
        self.doubleSpinBox_lock_blue_1_k_p.setMaximum(params['lock']['blue_1']['k_p_max'])
        self.doubleSpinBox_lock_blue_1_k_i.setValue(params['lock']['blue_1']['k_i'])
        self.doubleSpinBox_lock_blue_1_k_i.setMaximum(params['lock']['blue_1']['k_i_max'])

        self.doubleSpinBox_lock_blue_2_k_p.setValue(params['lock']['blue_2']['k_p'])
        self.doubleSpinBox_lock_blue_2_k_p.setMaximum(params['lock']['blue_2']['k_p_max'])
        self.doubleSpinBox_lock_blue_2_k_i.setValue(params['lock']['blue_2']['k_i'])
        self.doubleSpinBox_lock_blue_2_k_i.setMaximum(params['lock']['blue_2']['k_i_max'])
        
        # Initialise dictionaries etc
        
        self.plots = {}
        
        self.base_freqs = {'blue_1': self.doubleSpinBox_blue_1_base.value(), 'blue_2': self.doubleSpinBox_blue_2_base.value()}
        self.offset_freqs = {'blue_1': self.doubleSpinBox_blue_1_offset.value(), 'blue_2': self.doubleSpinBox_blue_2_offset.value()}
        self.setpoint_freqs = {'blue_1': self.base_freqs['blue_1']+self.offset_freqs['blue_1']*1e-6, 'blue_2':  self.base_freqs['blue_2']+self.offset_freqs['blue_2']*1e-6}
        
        self.smooth_change_flags = {'blue_1': False, 'blue_2': False, 'red_1': False, 'red_2': False}
        
        self.smooth_change_params_blue_1 = {'initial offset': 0, 'final offset': 10, 'change time': 1, 'start time': 0}
        self.smooth_change_params = {'blue_1': self.smooth_change_params_blue_1.copy(), 'blue_2': self.smooth_change_params_blue_1.copy()}
        
        self.sawtooth_flag = False
        self.sawtooth_stop_flag = False
        self.sawtooth_stop_after_flag = False
        self.sawtooth_params = {'initial offset': 0, 'final offset': 10, 'time 1': 1, 'time 2': 1, 'reps': 1, 'reps completed': 0, 'start time': 0}
        
        #---------------------------------------------------------------------#
        #--- PLOTS AND PUSH BUTTONS FOR LASER BLUE 1 -----------------#
        #---------------------------------------------------------------------#
        self.plots['blue_1'] = pg.PlotWidget(name = 'widget_plot_nu_blue_1')
        self.plots['blue_1'].setBackground(background = brush_background)
        self.plots['blue_1'].setLabel('left', 'nu', units = '[THz]', **labelstyle_L)
        self.plots['blue_1'].setLabel('bottom', 'time', units = '', **labelstyle_L)
        self.plots['blue_1'].showGrid(x = True, y = True)
        
        self.verticalLayout_nu_laser_blue_1.addWidget(self.plots['blue_1'])
        
        self.label_blue_1_setpoint.setText(f'{self.setpoint_freqs["blue_1"]:.7f}')
        
        self.pushButton_lock_laser_blue_1_on.clicked.connect(self.lock_laser_on)
        self.pushButton_lock_laser_blue_1_off.clicked.connect(self.lock_laser_off)
        
        self.pushButton_set_base_blue_1.clicked.connect(self.set_base)
        
        self.pushButton_smooth_change_laser_blue_1_start.clicked.connect(self.start_smooth_scan)
        self.pushButton_smooth_change_laser_blue_1_stop.clicked.connect(self.stop_smooth_scan)
        
        self.doubleSpinBox_blue_1_base.valueChanged.connect(self.base_freq_changed)
        self.doubleSpinBox_blue_1_offset.valueChanged.connect(self.offset_freq_changed)
        
        self.doubleSpinBox_lock_blue_1_k_p.valueChanged.connect(self.k_p_changed)
        self.doubleSpinBox_lock_blue_1_k_i.valueChanged.connect(self.k_i_changed)
        #---------------------------------------------------------------------#

     


        #---------------------------------------------------------------------#
        #--- PLOTS, PUSH BUTTONS FOR LASER BLUE 2 -----------------#
        #---------------------------------------------------------------------#        
        self.plots['blue_2'] = pg.PlotWidget(name = 'widget_plot_nu_blue_2')
        self.plots['blue_2'].setBackground(background = brush_background)
        self.plots['blue_2'].setLabel('left', 'nu', units = '[THz]', **labelstyle_L)
        self.plots['blue_2'].setLabel('bottom', 'time', units = '', **labelstyle_L)
        self.plots['blue_2'].showGrid(x = True, y = True)
        
        self.verticalLayout_nu_laser_blue_2.addWidget(self.plots['blue_2'])
        #---------------------------------------------------------------------#
        self.label_blue_2_setpoint.setText(f'{self.setpoint_freqs["blue_2"]:.7f}')
        
        self.pushButton_lock_laser_blue_2_on.clicked.connect(self.lock_laser_on)
        self.pushButton_lock_laser_blue_2_off.clicked.connect(self.lock_laser_off)
        
        self.pushButton_smooth_change_laser_blue_2_start.clicked.connect(self.start_smooth_scan)
        self.pushButton_smooth_change_laser_blue_2_stop.clicked.connect(self.stop_smooth_scan)
        
        self.pushButton_set_base_blue_1.clicked.connect(self.set_base)
        
        self.doubleSpinBox_blue_2_base.valueChanged.connect(self.base_freq_changed)        
        self.doubleSpinBox_blue_2_offset.valueChanged.connect(self.offset_freq_changed)
        
        self.doubleSpinBox_lock_blue_2_k_p.valueChanged.connect(self.k_p_changed)
        self.doubleSpinBox_lock_blue_2_k_i.valueChanged.connect(self.k_i_changed)

        #---------------------------------------------------------------------#
        #--- PLOTS, PUSH BUTTONS FOR LASER RED 1 ------------------#
        #---------------------------------------------------------------------#        
        self.plot_nu_red_1 = pg.PlotWidget(name = 'widget_plot_nu_red_1')
        self.plot_nu_red_1.setBackground(background = brush_background)
        self.plot_nu_red_1.setLabel('left', 'nu', units = '[THz]', **labelstyle_L)
        self.plot_nu_red_1.setLabel('bottom', 'time', units = '', **labelstyle_L)
        self.plot_nu_red_1.showGrid(x = True, y = True)
        
        self.verticalLayout_nu_laser_red_1.addWidget(self.plot_nu_red_1)
        #---------------------------------------------------------------------#

        #---------------------------------------------------------------------#   
        self.pushButton_lock_laser_red_1_on.clicked.connect(self.pushButton_lock_laser_red_1_on_clicked)
        self.pushButton_lock_laser_red_1_off.clicked.connect(self.pushButton_lock_laser_red_1_off_clicked)
        
        self.pushButton_smooth_change_laser_red_1_start.clicked.connect(self.pushButton_smooth_change_laser_red_1_start_clicked)
        self.pushButton_smooth_change_laser_red_1_stop.clicked.connect(self.pushButton_smooth_change_laser_red_1_stop_clicked)
        #---------------------------------------------------------------------#


        
        
        #---------------------------------------------------------------------#
        #--- PLOTS, PUSH BUTTONS FOR LASER RED 2 ------------------#
        #---------------------------------------------------------------------#        
        self.plot_nu_red_2 = pg.PlotWidget(name = 'widget_plot_nu_red_2')
        self.plot_nu_red_2.setBackground(background = brush_background)
        self.plot_nu_red_2.setLabel('left', 'nu', units = '[THz]', **labelstyle_L)
        self.plot_nu_red_2.setLabel('bottom', 'time', units = '', **labelstyle_L)
        self.plot_nu_red_2.showGrid(x = True, y = True)
        
        self.verticalLayout_nu_laser_red_2.addWidget(self.plot_nu_red_2)
        #---------------------------------------------------------------------#

        #---------------------------------------------------------------------#   
        self.pushButton_lock_laser_red_2_on.clicked.connect(self.pushButton_lock_laser_red_2_on_clicked)
        self.pushButton_lock_laser_red_2_off.clicked.connect(self.pushButton_lock_laser_red_2_off_clicked)
        
        self.pushButton_smooth_change_laser_red_2_start.clicked.connect(self.pushButton_smooth_change_laser_red_2_start_clicked)
        self.pushButton_smooth_change_laser_red_2_stop.clicked.connect(self.pushButton_smooth_change_laser_red_2_stop_clicked)
        #---------------------------------------------------------------------#

        #---------------------------------------------------------------------#    



        #---------------------------------------------------------------------#
        #--- PUSH BUTTONS FOR SAWTOOTH ---------------------#
        #---------------------------------------------------------------------#         

        #---------------------------------------------------------------------#
        
        self.pushButton_sawtooth_start.clicked.connect(self.sawtooth_start)
        self.pushButton_sawtooth_stop.clicked.connect(self.sawtooth_stop)
        self.pushButton_sawtooth_stop_after.clicked.connect(self.sawtooth_stop_after)
        
        #---------------------------------------------------------------------#
        #--- SET UP TIMERS ---------------------#
        #---------------------------------------------------------------------#          
        
        # Plot updater
        self.timer_update_plots = QtCore.QTimer()
        self.timer_update_plots.setInterval(250)
        self.timer_update_plots.setTimerType(QtCore.Qt.PreciseTimer)
        self.timer_update_plots.timeout.connect(self.update_plots)
        self.timer_update_plots.start()
        
        # Setpoint updater
        self.timer_update_setpoints = QtCore.QTimer()
        self.timer_update_setpoints.setInterval(50)
        self.timer_update_setpoints.setTimerType(QtCore.Qt.PreciseTimer)
        self.timer_update_setpoints.timeout.connect(self.update_setpoints)
        self.timer_update_setpoints.start()
        
        # Sawtooth scanner
#        self.timer_t_dependent_plots_sawtooth = QtCore.QTimer()
#        self.timer_t_dependent_plots_sawtooth.setInterval(250)
#        self.timer_t_dependent_plots_sawtooth.setTimerType(QtCore.Qt.PreciseTimer)
#        self.timer_t_dependent_plots_sawtooth.timeout.connect(self.t_dependent_updates_sawtooth)
#        self.timer_t_dependent_plots_sawtooth.start()
        
        #---------------------------------------------------------------------#   
    ###########################################################################
    ###########################################################################
    ### THE FUNCTIONS FOR THE PUSH BUTTONS ####################################
    ###########################################################################
    ########################################################################### 
    
    def pushButton_debug_clicked(self):
        lc.debug_number = self.spinBox_debug.value()
        lc.debug_flag = True
        print(self.base_freqs, self.offset_freqs, self.setpoint_freqs)
    
    
    ###########################################################################
    ### FUNCTIONS FOR LASER BLUE 1 ############################################
    ###########################################################################           
    
    def get_spinBox(self, spinBox_name):
        return self.tab_3.findChild(QtWidgets.QDoubleSpinBox, spinBox_name)
    
    def get_label(self, label_name):
        return self.tab_3.findChild(QtWidgets.QLabel, label_name)
    
    ###########################################################################
    def lock_laser_on(self):
        laser_id = self.mainWindow.sender().property('laserID')
        lc.lock_laser_on(laser_id)                
        
    def lock_laser_off(self):
        laser_id = self.mainWindow.sender().property('laserID')
        lc.lock_laser_off(laser_id)
    
    #---
    
    def start_smooth_scan(self):
        laser_id = self.mainWindow.sender().property('laserID')
        if not self.smooth_change_flags[laser_id] and not self.sawtooth_flag:
            initial_offset = self.offset_freqs[laser_id]
            final_offset = self.get_spinBox(f'doubleSpinBox_{laser_id}_smooth_new_offset').value()
            change_time = self.get_spinBox(f'doubleSpinBox_{laser_id}_smooth_delta_t').value()
            start_time = time.monotonic()
            self.smooth_change_params[laser_id] =  {'initial offset': initial_offset, 'final offset': final_offset, 'change time': change_time, 'start time': start_time}
            self.smooth_change_flags[laser_id] = True
        else:
            print('already scanning')
    
    def stop_smooth_scan(self):
        laser_id = self.mainWindow.sender().property('laserID')
        self.smooth_change_flags[laser_id] = False
    
    #---
    
    def set_base(self):
        laser_id = self.mainWindow.sender().property('laserID')
        if not self.sawtooth_flag and not self.smooth_change_flags[laser_id]:
            self.get_spinBox(f'doubleSpinBox_{laser_id}_base').setValue(self.setpoint_freqs[laser_id])
            self.get_spinBox(f'doubleSpinBox_{laser_id}_offset').setValue(0)
    
    #--
    
    def sawtooth_start(self):
        if not self.sawtooth_flag and not any(self.smooth_change_flags.values()):
            self.sawtooth_params = {'initial offset blue 1': self.doubleSpinBox_sawtooth_blue_1_start_offset.value(),
                                    'final offset blue 1': self.doubleSpinBox_sawtooth_blue_1_end_offset.value(),
                                    'initial offset blue 2': self.doubleSpinBox_sawtooth_blue_2_start_offset.value(),
                                    'final offset blue 2': self.doubleSpinBox_sawtooth_blue_2_end_offset.value(),
                                    'time 1': self.doubleSpinBox_sawtooth_time_1.value(),
                                    'time 2': self.doubleSpinBox_sawtooth_time_2.value(),
                                    'reps': self.spinBox_sawtooth_total_reps.value(),
                                    'reps completed': 0,
                                    'start time': time.monotonic()}
            self.sawtooth_stop_flag = False
            self.sawtooth_stop_after_flag = False
            self.sawtooth_flag = True
        else:
            print('already scanning')
    
    def sawtooth_stop(self):
        if self.sawtooth_flag and not self.sawtooth_stop_after_flag:
            self.sawtooth_stop_flag = True
    
    def sawtooth_stop_after(self):
        if self.sawtooth_flag and not self.sawtooth_stop_flag:
            self.sawtooth_stop_after_flag = True
    
    #---
    
    def base_freq_changed(self):
        laser_id = self.mainWindow.sender().property('laserID')
        self.base_freqs[laser_id] = self.mainWindow.sender().value()
    
    def offset_freq_changed(self):
        laser_id = self.mainWindow.sender().property('laserID')
        self.offset_freqs[laser_id] = self.mainWindow.sender().value()
    
    #---
    
    def k_p_changed(self):
        laser_id = self.mainWindow.sender().property('laserID')
        lc.lock_pars[laser_id]['k_p'] = self.mainWindow.sender().value()

    def k_i_changed(self):
        laser_id = self.mainWindow.sender().property('laserID')
        lc.lock_pars[laser_id]['k_i'] = self.mainWindow.sender().value()
        
    ###########################################################################   
        
    ###########################################################################      
    
    def update_plots(self):
        self.update_laser_gui('blue_1')
        self.update_laser_gui('blue_2')
        self.t_dependent_updates_laser_red_1()
        self.t_dependent_updates_laser_red_2()
    
    def update_setpoints(self):
        # smooth change updates offset
        for laser_id in self.smooth_change_flags:
            if self.smooth_change_flags[laser_id]:
                current_time = time.monotonic() - self.smooth_change_params[laser_id]['start time']
                change_time = self.smooth_change_params[laser_id]['change time']
                initial_offset = self.smooth_change_params[laser_id]['initial offset']
                final_offset = self.smooth_change_params[laser_id]['final offset']
                if current_time >= change_time:
                    new_offset = final_offset
                    self.smooth_change_flags[laser_id] = False
                else:
                    new_offset = initial_offset + (current_time/change_time)*(final_offset - initial_offset)
                offset_spinBox = self.get_spinBox(f'doubleSpinBox_{laser_id}_offset')
                offset_spinBox.setValue(new_offset)     # this will automatically change offset_freqs
                    
        # sawtooth scan
        #{'initial offset': 0, 'final offset': 10, 'time 1': 1, 'time 2': 1, 'reps': 1, 'reps completed': 0 'start time': 0}
        if self.sawtooth_flag:
            if self.sawtooth_stop_flag:
                self.sawtooth_flag = False
                self.sawtooth_stop_flag = False
            else:
                current_time = time.monotonic() - self.sawtooth_params['start time']
                time_1 = self.sawtooth_params['time 1']
                time_2 = self.sawtooth_params['time 2']
                initial_offset_blue_1 = self.sawtooth_params['initial offset blue 1']
                final_offset_blue_1 = self.sawtooth_params['final offset blue 1']
                initial_offset_blue_2 = self.sawtooth_params['initial offset blue 2']
                final_offset_blue_2 = self.sawtooth_params['final offset blue 2']
                if current_time <= time_1:
                    new_offset_blue_1 = initial_offset_blue_1 + (current_time/time_1)*(final_offset_blue_1 - initial_offset_blue_1)
                    new_offset_blue_2 = initial_offset_blue_2 + (current_time/time_1)*(final_offset_blue_2 - initial_offset_blue_2)
                elif current_time <= (time_1 + time_2):
                    new_offset_blue_1 = final_offset_blue_1 + ( (current_time-time_1) /time_2)*(initial_offset_blue_1 - final_offset_blue_1)
                    new_offset_blue_2 = final_offset_blue_2 + ( (current_time-time_1) /time_2)*(initial_offset_blue_2 - final_offset_blue_2)
                else:   # current rep finished - check if last
                    self.sawtooth_params['start time'] = time.monotonic() # reset start time
                    if self.sawtooth_stop_after_flag:
                        self.sawtooth_flag = False
                        self.sawtooth_stop_after_flag = False
                    else:
                        self.sawtooth_params['reps completed'] += 1
                        if self.sawtooth_params['reps completed'] == self.sawtooth_params['reps']:
                            self.sawtooth_flag = False
                    new_offset_blue_1 = initial_offset_blue_1
                    new_offset_blue_2 = initial_offset_blue_2
                self.get_spinBox(f'doubleSpinBox_blue_1_offset').setValue(new_offset_blue_1)     # this will automatically change offset_freqs
                self.get_spinBox(f'doubleSpinBox_blue_2_offset').setValue(new_offset_blue_2)                    
        
            
        self.setpoint_freqs['blue_1'] = self.base_freqs['blue_1']+self.offset_freqs['blue_1']*1e-6
        self.label_blue_1_setpoint.setText(f'{self.setpoint_freqs["blue_1"]:.7f}')
        lc.nu_setpoint['blue_1'] = self.setpoint_freqs['blue_1']
        
        self.setpoint_freqs['blue_2'] = self.base_freqs['blue_2']+self.offset_freqs['blue_2']*1e-6
        self.label_blue_2_setpoint.setText(f'{self.setpoint_freqs["blue_2"]:.7f}')
        lc.nu_setpoint['blue_2'] = self.setpoint_freqs['blue_2']        
        
        
        
    def update_laser_gui(self, laser_id):
        self.get_label(f'label_nu_{laser_id}_is').setText(f'{lc.nu[laser_id]:.7f}')
        
        lock_status_label = self.get_label(f'label_lock_{laser_id}_status')
        if lc.lock_lasers[laser_id]:
            lock_status_label.setText('ON')
            lock_status_label.setStyleSheet('color: black')
        else:
            lock_status_label.setText('OFF')
            lock_status_label.setStyleSheet('color: red')
        
        plot = self.plots[laser_id]
        
        ydata = np.array(lc.nu_history[laser_id][-500:], dtype = float)
        setpoint = self.setpoint_freqs[laser_id]
        ydata[ydata<(setpoint-1e-3)]=np.NaN
        ydata[ydata>(setpoint+1e-3)]=np.NaN
        
        try:
            plot.plot(ydata,pen = blackPen, symbol = 'o', symbolBrush = blueBrush, name = f'nu_{laser_id}_was', clear = True)
        except Exception:
            pass

        #plot.enableAutoRange('y', 0.99)
        #nu_blue_1_upper = pg.PlotCurveItem([0,500],[755.186881,755.186881],pen = bluePen)
        #nu_blue_1_lower = pg.PlotCurveItem([0,500],[755.186879,755.186879],pen = bluePen)
        #nu_blue_1_fill = pg.FillBetweenItem(nu_blue_1_upper,nu_blue_1_lower,blueBrush_alpha)
        
        #self.plot_nu_blue_1.addItem(nu_blue_1_upper)
        #self.plot_nu_blue_1.addItem(nu_blue_1_lower)
        #self.plot_nu_blue_1.addItem(nu_blue_1_fill)        
    ###########################################################################    
        


    ###########################################################################
    ### FUNCTIONS FOR LASER BLUE 2 ############################################
    ###########################################################################           
        
    ###########################################################################        
    def pushButton_smooth_change_laser_blue_2_start_clicked(self):
        lc.nu_blue_2_smooth_want = float(self.doubleSpinBox_nu_blue_2_smooth_want.value())
        lc.nu_blue_2_smooth_delta_t = float(self.doubleSpinBox_nu_blue_2_smooth_delta_t.value())
        lc.smooth_change_laser_blue_2_start()

    def pushButton_smooth_change_laser_blue_2_stop_clicked(self):
        lc.smooth_change_laser_blue_2_stop()
    ###########################################################################   
 


    ###########################################################################
    ### FUNCTIONS FOR LASER RED 1 #############################################
    ###########################################################################           
        
    ###########################################################################
    def pushButton_lock_laser_red_1_on_clicked(self):
        lc.nu_red_1_want = float(self.doubleSpinBox_nu_red_1_want.value())
        lc.lock_laser_red_1_on()
        self.label_lock_red_1_status.setText('ON')
        self.label_lock_red_1_status.setStyleSheet('color: black')        
        
    def pushButton_lock_laser_red_1_off_clicked(self):
        lc.lock_laser_red_1_off()
        self.label_lock_red_1_status.setText('OFF')
        self.label_lock_red_1_status.setStyleSheet('color: red')
        
    def pushButton_smooth_change_laser_red_1_start_clicked(self):
        lc.nu_red_1_smooth_want = float(self.doubleSpinBox_nu_red_1_smooth_want.value())
        lc.nu_red_1_smooth_delta_t = float(self.doubleSpinBox_nu_red_1_smooth_delta_t.value())
        lc.smooth_change_laser_red_1_start()

    def pushButton_smooth_change_laser_red_1_stop_clicked(self):
        lc.smooth_change_laser_red_1_stop()
    ###########################################################################   
        
    ###########################################################################        
    def t_dependent_updates_laser_red_1(self):
        
        self.label_nu_red_1_is.setText(str(lc.nu_red_1_is))
        
#        self.doubleSpinBox_nu_blue_1_want.setValue(lc.nu_blue_1_want)
           
        lc.lock_red_1_alpha = float(self.doubleSpinBox_lock_red_1_alpha.value())
        lc.lock_red_1_beta = float(self.doubleSpinBox_lock_red_1_beta.value())
       
        try:
            self.plot_nu_red_1.plot(np.arange(500),lc.nu_red_1_was[-500:],pen = blackPen, symbol = 'o', symbolBrush = redBrush, name = 'nu_red_1_was', clear = True)
        except Exception:
            pass
            
        nu_red_1_upper = pg.PlotCurveItem([0,500],[346.000255,346.000255],pen = redPen)
        nu_red_1_lower = pg.PlotCurveItem([0,500],[346.000245,346.000245],pen = redPen)
        nu_red_1_fill = pg.FillBetweenItem(nu_red_1_upper,nu_red_1_lower,redBrush_alpha)
        
        self.plot_nu_red_1.addItem(nu_red_1_upper)
        self.plot_nu_red_1.addItem(nu_red_1_lower)
        self.plot_nu_red_1.addItem(nu_red_1_fill)        
    ###########################################################################   



    ###########################################################################
    ### FUNCTIONS FOR LASER RED 2 #############################################
    ###########################################################################           
        
    ###########################################################################
    def pushButton_lock_laser_red_2_on_clicked(self):
        lc.nu_red_2_want = float(self.doubleSpinBox_nu_red_2_want.value())
        lc.lock_laser_red_2_on()
        self.label_lock_red_2_status.setText('ON')
        self.label_lock_red_2_status.setStyleSheet('color: black')        
        
    def pushButton_lock_laser_red_2_off_clicked(self):
        lc.lock_laser_red_2_off()
        self.label_lock_red_2_status.setText('OFF')
        self.label_lock_red_2_status.setStyleSheet('color: red')
        
    def pushButton_smooth_change_laser_red_2_start_clicked(self):
        lc.nu_red_2_smooth_want = float(self.doubleSpinBox_nu_red_2_smooth_want.value())
        lc.nu_red_2_smooth_delta_t = float(self.doubleSpinBox_nu_red_2_smooth_delta_t.value())
        lc.smooth_change_laser_red_2_start()

    def pushButton_smooth_change_laser_red_2_stop_clicked(self):
        lc.smooth_change_laser_red_2_stop()
    ###########################################################################   
        
    ###########################################################################        
    def t_dependent_updates_laser_red_2(self):
        
        self.label_nu_red_2_is.setText(str(lc.nu_red_2_is))
        
#        self.doubleSpinBox_nu_blue_1_want.setValue(lc.nu_blue_1_want)
           
        lc.lock_red_2_alpha = float(self.doubleSpinBox_lock_red_2_alpha.value())
        lc.lock_red_2_beta = float(self.doubleSpinBox_lock_red_2_beta.value())
       
        try:
            self.plot_nu_red_2.plot(np.arange(500),lc.nu_red_2_was[-500:],pen = blackPen, symbol = 'o', symbolBrush = redBrush, name = 'nu_red_2_was', clear = True)
        except Exception:
            pass
            
        nu_red_2_upper = pg.PlotCurveItem([0,500],[350.862605,350.862605],pen = redPen)
        nu_red_2_lower = pg.PlotCurveItem([0,500],[350.862595,350.862595],pen = redPen)
        nu_red_2_fill = pg.FillBetweenItem(nu_red_2_upper,nu_red_2_lower,redBrush_alpha)
        
        self.plot_nu_red_2.addItem(nu_red_2_upper)
        self.plot_nu_red_2.addItem(nu_red_2_lower)
        self.plot_nu_red_2.addItem(nu_red_2_fill)        
    ###########################################################################   


    ###########################################################################        
#    def t_dependent_updates_sawtooth(self):
#       
#        lc.sawtooth_nu_blue_1_init = self.doubleSpinBox_sawtooth_nu_blue_1_init.value()
#        lc.sawtooth_nu_blue_1_detuned = self.doubleSpinBox_sawtooth_nu_blue_1_detuned.value()
#        lc.sawtooth_nu_blue_2_init = self.doubleSpinBox_sawtooth_nu_blue_2_init.value()
#        lc.sawtooth_nu_blue_2_detuned = self.doubleSpinBox_sawtooth_nu_blue_2_detuned.value()
#        lc.sawtooth_delta_t1 = self.doubleSpinBox_sawtooth_delta_t1.value()
#        lc.sawtooth_delta_t2 = self.doubleSpinBox_sawtooth_delta_t2.value()
#        lc.sawtooth_total_reps = self.spinBox_sawtooth_total_reps.value()
#        
#        lc.f_prepare_sawtooth_laser_blue_1_and_2()
#            
#        self.plot_sawtooth1.plot(lc.sawtooth_t_total,lc.sawtooth_nu1_total, order = 0, pen = bluePen, name = 'nu_sawtooth1', clear = True)
#        self.plot_sawtooth2.plot(lc.sawtooth_t_total,lc.sawtooth_nu2_total, order = 0, pen = bluePen, name = 'nu_sawtooth2', clear = True)
    ###########################################################################   

      
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    
    lc = laser_control()
    
    dialog_lc = QtWidgets.QMainWindow()
    
    programm_lc = window(dialog_lc,lc)
    dialog_lc.show()
    
    sys.exit(app.exec_())