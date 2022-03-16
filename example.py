#! /usr/bin/env python
# -*- coding: utf8 -*-
#
#    PyVisca-3 Implementation of the Visca serial protocol in python3
#    based on PyVisca (Copyright (C) 2013  Florian Streibelt 
#    pyvisca@f-streibelt.de).
#
#    Author: Giacomo Benelli benelli.giacomo@aerialtronics.com
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 2 only.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#    USA

"""PyVisca-3 by Giacomo Benelli <benelli.giacomo@gmail.com>"""

#
# This is used for testing the functionality while developing,
# expect spaghetti code... this applied for the original author and 
# for me too... :)
#
import time,sys
from pyviscalib import ViscaControl
from  time import sleep
import threading

class Test():

    def __init__(self):
        self._exit = False
        self.v=ViscaControl(portname='/dev/serial/by-id/usb-Twiga_TWIGACam-if03-port0')
                
        self.v.start()

        self.v.cmd_address_set()

        self.v.cmd_if_clear_all()

        self.CAM = 1
        
        self.read_thread_t = threading.Thread(target = self.continuous_read)
        self.write_thread_t = threading.Thread(target = self.continuous_write)
        
    def start(self):
        self.read_thread_t.start()
        self.write_thread_t.start()
    
    def stop(self):
        print('Quitting Test')
        self._exit = True
        self.read_thread_t.join()
        self.write_thread_t.join()
        
    def continuous_read(self):
        while not self._exit:
            zl = self.v.inquiry_combined_zoom_pos(self.CAM)
            print('Got zoomlevel %d' % zl)
            time.sleep(0.01)
            
    def continuous_write(self):
        while not self._exit:
            self.v.cmd_cam_zoom_tele_speed(self.CAM, 7)
            time.sleep(2)
            self.v.cmd_cam_zoom_stop(self.CAM)
            self.v.cmd_cam_zoom_wide_speed(self.CAM, 7)
            time.sleep(2)


if __name__ == '__main__':
    try:
        t=Test()
        t.start()
        while True:
            sleep(1)
    except KeyboardInterrupt:
        t.stop()
        sys.exit(1)


