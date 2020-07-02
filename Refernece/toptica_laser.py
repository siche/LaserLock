# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 10:57:55 2018

@author: IonTrap/JMHeinrich

this class represents the Toptica DLC pro laser controller
"""

import socket
import time
         
class toptica_laser(object):
    
    def __init__(self, ip_address, timeout = None, port = 1998):
        
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        
        try:
            self._socket = socket.socket()#socket.AF_INET, socket.SOCK_STREAM)
            
            if timeout is not None:
                self._socket.settimeout(timeout)
                
            self._socket.connect((ip_address, port))
            
            print('Toptica DLC pro at ip address ' + str(self.ip_address) + ' is online')
            

        except socket.error as e:
            print('connection to Toptica DLC pro at address' + str(ip_address) + ' FAILED!')
        
        # check for system health and print the response
        self._socket.send(("(param-ref 'system-health-txt)" + "\r\n").encode('utf-8'))
        
        time.sleep(0.1)
        
        self._socket.recv(256)
        
        
            
            
    def set_parameter(self, command, param):
        
        success = self._socket.send(("(param-set! '" + str(command) + " " + str(param) + ")" + "\r\n").encode('utf-8'))
        value = self._socket.recv(256)
        
        return success
        
    
    
    def read_parameter(self, command):
        
        # send request
        self._socket.send(("(param-ref '" + str(command) + ")" + "\r\n").encode('utf-8'))
        
        # wait and receive answer
        time.sleep(0.1)
        value = self._socket.recv(256)
        
        
        # received answer needs to be translated to string
        try:
            index_stop = value.rindex(b'\n> ')           
            try:
                index_start = value[:value.rindex(b'\n> ')].rindex(b'\n> ') + len('\n> ')
            except ValueError:
                index_start = 0
        except ValueError:
            print('Error parsing the answer')

        return (value[index_start:index_stop]).decode('utf-8')
    
    def get_voltage(self):
        vol = self.read_parameter('laser1:dl:pc:voltage-set')
        return float(vol)


    def set_voltage(self, vol):
        self.set_parameter('laser1:dl:pc:voltage-set', vol)
        
    