# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 18:20:00 2019

@author: IonTrap
"""

#--- Parameters for the laser lock program ---#

pars_debug = {'number': 50}

pars_lock_blue_1 = {'k_p': 100, 'k_p_max': 1e5,
                    'k_i': 200, 'k_i_max': 1e3}

pars_lock_blue_2 = {'k_p': 100, 'k_p_max': 1e5,
                    'k_i': 200, 'k_i_max': 1e3}

pars_lock = {'blue_1': pars_lock_blue_1, 'blue_2': pars_lock_blue_2}

params = {'debug': pars_debug, 'lock':pars_lock}