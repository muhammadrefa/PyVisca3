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

def main():

	from pyviscalib.visca import Visca
	from  time import sleep

	v=Visca()

	v.cmd_adress_set()

	v.cmd_if_clear_all()

	CAM=1

#	v.cmd_cam_power_off(CAM)

	v.cmd_cam_power_on(CAM)

	v.cmd_cam_auto_power_off(CAM,2)

	v.cmd_datascreen_on(CAM)


	sleep(1)
	v.cmd_cam_zoom_tele(CAM)
	sleep(2)
	v.cmd_cam_zoom_stop(CAM)
	sleep(3)
    
	v.cmd_cam_zoom_wide(CAM)
	sleep(2)
	v.cmd_cam_zoom_stop(CAM)
	sleep(3)

	v.cmd_cam_power_off(CAM)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass


