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

import serial,sys
from _thread import allocate_lock
import struct

class ViscaControl():
    
    DEBUG = False
    
    REGISTER_NAMES = {'mode': b'\x72'}
    
    REGISTER_VALUES = { b'\x72':
        { b'\x01' : '1080i/59.94',
          #b'\x02' : 'Reserved',
          b'\x03' : 'NTSC Analog',
          b'\x04' : '1080i/50',
          b'\x05' : 'PAL Analog',
          b'\x06' : '1080p/29.97',
          #b'\x07' : 'Reserved',
          b'\x08' : '1080p/25',
          b'\x09' : '720p/59.94',
          #b'\x0A' : 'Reserved',
          #b'\x0B' : 'Reserved',
          b'\x0C' : '720p/50',
          #b'\x0D' : 'Reserved',
          b'\x0E' : '720p/29.97',
          #b'\x0F' : 'Reserved',
          #b'\x10' : 'Reserved',
          b'\x11' : '720p/25',
          #b'\x12' : 'Reserved',
          b'\x13' : '1080p/59.94',
          b'\x14' : '1080p/50',
        }
        }
    
    OPTICAL_ZOOM_SETTINGS = [
        b'\x00\x00\x00\x00',
        b'\x01\x06\x0A\x01',
        b'\x02\x00\x06\x03',
        b'\x02\x06\x02\x08',
        b'\x02\x0A\x01\x0D',
        b'\x02\x0D\x01\x03',
        b'\x02\x0F\x06\x0D',
        b'\x03\x01\x06\x01',
        b'\x03\x03\x00\x0D',
        b'\x03\x04\x08\x06',
        b'\x03\x05\x0D\x07',
        b'\x03\x07\x00\x09',
        b'\x03\x08\x02\x00',
        b'\x03\x09\x02\x00',
        b'\x03\x0A\x00\x0A',
        b'\x03\x0A\x0D\x0D',
        b'\x03\x0B\x09\x0C',
        b'\x03\x0C\x04\x06',
        b'\x03\x0C\x0D\x0C',
        b'\x03\x0D\x06\x00',
        b'\x03\x0D\x0D\x04',
        b'\x03\x0E\x03\x09',
        b'\x03\x0E\x09\x00',
        b'\x03\x0E\x0D\x0C',
        b'\x03\x0F\x01\x0E',
        b'\x03\x0F\x05\x07',
        b'\x03\x0F\x08\x0A',
        b'\x03\x0F\x0B\x06',
        b'\x03\x0F\x0D\x0C',
        b'\x04\x00\x00\x00'
        ]

    DIGITAL_ZOOM_SETTINGS = [
        b'\x04\x00\x00\x00',
        b'\x06\x00\x00\x00',
        b'\x06\x0A\x08\x00',
        b'\x07\x00\x00\x00',
        b'\x07\x03\x00\x00',
        b'\x07\x05\x04\x00',
        b'\x07\x06\x0C\x00',
        b'\x07\x08\x00\x00',
        b'\x07\x08\x0C\x00',
        b'\x07\x09\x08\x00',
        b'\x07\x0A\x00\x00',
        b'\x07\x0A\x0C\x00',
        ]
        
    ZOOM_SETTINGS = OPTICAL_ZOOM_SETTINGS + DIGITAL_ZOOM_SETTINGS[1:]
    ZOOM_SETTINGS_INT = None

    __instance = None
    started = False
    def __new__(cls):
        if ViscaControl.__instance is None:
            ViscaControl.__instance = object.__new__(cls)
        return ViscaControl.__instance


    def __init__(self,portname="/dev/ttyACM1", timeout=1):
        if self.started:
            return

        self.portname = portname
        self.timeout = timeout
        
    def start(self):
        if self.started:
            return

        self.ZOOM_SETTINGS_INT = [ struct.unpack('>I', a)[0] for a in self.ZOOM_SETTINGS]
            
        self.serialport=None
        self.mutex = allocate_lock()
        self.portname=self.portname
        self.open_port(self.timeout)
            
        while True:
            try:
                self.cmd_adress_set()
                self.started = True
                break
            except Exception as e:
                print ("exception during serial init %s. Retrying..." %e)
                self.mutex.release()
                pass

    def open_port(self, timeout):

        self.mutex.acquire()

        if (self.serialport == None):
            try:
                self.serialport = serial.Serial(self.portname,9600,timeout=timeout,stopbits=1,bytesize=8,rtscts=False, dsrdtr=False)
                self.serialport.flushInput()
            except Exception as e:
                print ("Exception opening serial port '%s' for display: %s\n" % (self.portname,e))
                raise e
                self.serialport = None
        
        self.serialport.reset_input_buffer()
        self.serialport.reset_output_buffer()

        self.mutex.release()

    def dump(self,packet,title=None):
        if not packet or len(packet)==0 or not self.DEBUG:
            return

        header=packet[0]
        term=packet[-1]
        qq=packet[1]

        sender = (header&0b01110000)>>4
        broadcast = (header&0b1000)>>3
        recipient = (header&0b0111)

        if broadcast:
            recipient_s="*"
        else:
            recipient_s=str(recipient)

        print ("-----")
        
        if title:
            print ("packet (%s) [%d => %s] len=%d: %s" % (title,sender,recipient_s,len(packet),packet))
        else:
            print ("packet [%d => %s] len=%d: %s" % (sender,recipient_s,len(packet),packet))

        print (" QQ.........: %02x" % qq)

        if qq==0x01:
            print ("              (Command)")
        if qq==0x09:
            print ("              (Inquiry)")

        if len(packet)>3:
            rr=(packet[2])
            print (" RR.........: %02x" % rr)

            if rr==0x00:
                print ("              (Interface)")
            if rr==0x04:
                print ("              (Camera [1])")
            if rr==0x06:
                print ("              (Pan/Tilter)")

        if len(packet)>4:
            data=packet[3:-1]
            print (" Data.......: %s" % data)
        else:
            print (" Data.......: None")

        if not term==0xff:
            print ("ERROR: Packet not terminated correctly")
            return

        if len(packet)==3 and ((qq & 0b11110000)>>4)==4:
            socketno = (qq & 0b1111)
            print (" packet: ACK for socket %02x" % socketno)

        if len(packet)==3 and ((qq & 0b11110000)>>4)==5:
            socketno = (qq & 0b1111)
            print (" packet: COMPLETION for socket %02x" % socketno)

        if len(packet)>3 and ((qq & 0b11110000)>>4)==5:
            socketno = (qq & 0b1111)
            ret=packet[2:-1]
            print (" packet: COMPLETION for socket %02x, data=%s" % (socketno,ret))

        if len(packet)==4 and ((qq & 0b11110000)>>4)==6:
            print (" packet: ERROR!")

            socketno = (qq & 0b00001111)
            errcode  = packet[2]

            #these two are special, socket is zero and has no meaning:
            if errcode==0x02 and socketno==0:
                print ("        : Syntax Error")
            if errcode==0x03 and socketno==0:
                print ("        : Command Buffer Full")


            if errcode==0x04:
                print ("        : Socket %i: Command canceled" % socketno)

            if errcode==0x05:
                print ("        : Socket %i: Invalid socket selected" % socketno)

            if errcode==0x41:
                print ("        : Socket %i: Command not executable" % socketno)

        if len(packet)==3 and qq==0x38:
            print ("Network Change - we should immedeately issue a renumbering!")


    def recv_packet(self,extra_title=None):
        # read up to 16 bytes until 0xff
        packet=b''
        count=0
        while count<16:
            s=self.serialport.read(1)
            if s:
                count+=1
                packet=packet+bytes(s)
            else:
                print ("ERROR: Timeout waiting for reply")
                self.serialport.reset_input_buffer()
                self.serialport.reset_output_buffer()
                #break
            if s==b'\xff':
                break

        if extra_title:
            self.dump(packet,"recv: %s" % extra_title)
        else:
            self.dump(packet,"recv")
        
        if packet == []:
            import pdb;pdb.set_trace()
        return packet

    def _write_packet(self,packet):

        if not self.serialport.isOpen():
            sys.exit(1)

        # lets see if a completion message or someting
        # else waits in the buffer. If yes dump it.
        if self.serialport.inWaiting():
            self.recv_packet("ignored")

        self.serialport.write(packet)
        self.dump(packet,"sent")
        
    def _raw_send(self, b_packet):
        if not self.serialport.isOpen():
            sys.exit(1)

        # lets see if a completion message or someting
        # else waits in the buffer. If yes dump it.
        if self.serialport.inWaiting():
            self.recv_packet("ignored")

        self.serialport.write(b_packet)



    def send_packet(self,recipient,data):
        """
        according to the documentation:

        |------packet (3-16 bytes)---------|

         header     message      terminator
         (1 byte)  (1-14 bytes)  (1 byte)

        | X | X . . . . .  . . . . . X | X |

        header:                  terminator:
        1 s2 s1 s0 0 r2 r1 r0     0xff

        with r,s = recipient, sender msb first

        for broadcast the header is 0x88!

        we use -1 as recipient to send a broadcast!

        """

        # we are the controller with id=0
        sender = 0

        if recipient==-1:
            #broadcast:
            rbits=0x8
        else:
            # the recipient (address = 3 bits)
            rbits=recipient & 0b111

        sbits=(sender & 0b111)<<4

        header=0b10000000 | sbits | rbits

        terminator=0xff

        #import pdb;pdb.set_trace()
        packet=bytes([header])+data+bytes([terminator])

        self.mutex.acquire()

        self._write_packet(packet)

        reply = self.recv_packet()

        if reply[-1] != 0xff:
            print ("received packet not terminated correctly: %s" % reply)
            reply=None

        self.mutex.release()

        return reply


    def send_broadcast(self,data):
        # shortcut
        return self.send_packet(-1,data)



    def i2v(self,value):
        """
        return word as dword in visca format
        packets are not allowed to be 0xff
        so for numbers the first nibble is 0000
        and 0xfd gets encoded into 0x0f 0x0xd
        """
        ms = (value &  0b1111111100000000) >> 8
        ls = (value &  0b0000000011111111)
        p=(ms&0b11110000)>>4
        r=(ls&0b11110000)>>4
        q=ms&0b1111
        s=ls&0b1111

        return bytes([p,q,r,s])



    def cmd_adress_set(self):
        """
        starts enumerating devices, sends the first adress to use on the bus
        reply is the same packet with the next free adress to use
        """

        #address of first device. should be 1:
        first=1

        data = b'\x30'+bytes([first])
        #import pdb;pdb.set_trace()
        reply = self.send_broadcast(data) # set address

        if not reply:
            print ("No reply from the bus.")
            #sys.exit(1)
            self.mutex.release()
            raise "Timeout on write"

        if len(reply)!=4 or reply[-1]!=0xff:
            print ("ERROR enumerating devices")
            sys.exit(1)
        if reply[0] != 0x88:
            print ("ERROR: expecting broadcast answer to an enumeration request")
            sys.exit(1)
        address = (reply[2])

        d=address-first
        print ("debug: found %i devices on the bus" % d)

        if d==0:
            sys.exit(1)


    def cmd_if_clear_all(self):
        reply=self.send_broadcast( b'\x01\x00\x01') # interface clear all
        if not reply[1:]==b'\x01\x00\x01\xff':
            print ("ERROR clearing all interfaces on the bus!")
            sys.exit(1)

        print ("debug: all interfaces clear")


    def cmd_cam(self,device,subcmd):
        packet=b'\x01\x04'+subcmd
        reply = self.send_packet(device,packet)
        #FIXME: check returned data here and retransmit?

        return reply

    def cmd_pt(self,device,subcmd):
        packet=b'\x01\x06'+subcmd
        reply = self.send_packet(device,packet)
        #FIXME: check returned data here and retransmit?

        return reply

    def get_data_from_inquiry(self, packet):
        return packet[2:-1]

    # ----------------------- Setters -------------------------------------


    # POWER control

    def cmd_cam_power(self,device,onoff):
        if onoff:
            pwr=b'\x00\x02'
        else:
            pwr=b'\x00\x03'
        return self.cmd_cam(device,pwr)

    def cmd_cam_power_on(self,device):
        return self.cmd_cam_power(device,True)

    def cmd_cam_power_off(self,device):
        return self.cmd_cam_power(device,False)


    #FIXME
    def cmd_cam_auto_power_off(self,device,time=0):
        """
        time = minutes without command until standby
        0: disable
        0xffff: 65535 minutes
        """
        subcmd=b"\x40"+self.i2v(time)
        return #self.cmd_cam(device,subcmd)


    # ZOOM control

    def cmd_cam_zoom_stop(self,device):
        subcmd=b"\x07\x00"
        print('stopping zoom')
        return self.cmd_cam(device,subcmd)

    def cmd_cam_zoom_tele(self,device):
        subcmd=b"\x07\x02"
        return self.cmd_cam(device,subcmd)

    def cmd_cam_zoom_wide(self,device):
        subcmd=b"\x07\x03"
        return self.cmd_cam(device,subcmd)


    def cmd_cam_zoom_tele_speed(self,device,speed):
        """
        zoom in with speed = 0..7
        """
        sbyte=0x20+(speed&0b111)
        subcmd=b"\x07"+bytes([sbyte])
        return self.cmd_cam(device,subcmd)

    def cmd_cam_zoom_wide_speed(self,device,speed):
        """
        zoom in with speed = 0..7
        """
        sbyte=0x30+(speed&0b111)
        subcmd=b"\x07"+bytes([sbyte])
        return self.cmd_cam(device,subcmd)
        
    def cmd_cam_zoom_direct(self,device,zoom):
        zoom_index=zoom-1
        if zoom_index in range(len(self.ZOOM_SETTINGS)):
            subcmd=b"\x47"+self.ZOOM_SETTINGS[zoom_index]
            return self.cmd_cam(device,subcmd)
        else:
            print('something wrong in direct zoom values')

    #Digital Zoom control on/off
    def cmd_cam_dzoom(self,device,state):
        if state:
            subcmd=b"\x06\x02"
        else:
            subcmd=b"\x06\x03"

        return self.cmd_cam(device,subcmd)

    def cmd_cam_dzoom_on(self,device):
        return self.cmd_cam_dzoom(device,True)

    def cmd_cam_dzoom_off(self,device):
        return self.cmd_cam_dzoom(device,False)


    # mirror
    def cmd_cam_lr_reverse(self,device,mode):
        subcmd=b"\x61"+bytes([mode])
        return self.cmd_cam(device,subcmd)

    def cmd_cam_lr_reverse_on(self,device):
        return self.cmd_cam_lr_reverse(device,0x02)

    def cmd_cam_lr_reverse_off(self,device):
        return self.cmd_cam_lr_reverse(device,0x03)
        
    # flip
    def cmd_cam_ud_reverse(self,device,mode):
        subcmd=b"\x66"+bytes([mode])
        return self.cmd_cam(device,subcmd)

    def cmd_cam_ud_reverse_on(self,device):
        return self.cmd_cam_ud_reverse(device,0x02)

    def cmd_cam_ud_reverse_off(self,device):
        return self.cmd_cam_ud_reverse(device,0x03)
        
    # Image Stabilization
    def cmd_cam_stabilization(self,device,mode):
        subcmd=b"\x34"+bytes([mode])
        return self.cmd_cam(device,subcmd)

    def cmd_cam_stabilization_on(self,device):
        return self.cmd_cam_stabilization(device,0x02)

    def cmd_cam_stabilization_off(self,device):
        return self.cmd_cam_stabilization(device,0x03)
        
    # Backlight compensation
    
    def cmd_cam_backlight_set(self, device, mode):
        subcmd=b'\x33'+bytes([mode])
        return self.cmd_cam(device, subcmd)
        
    def cmd_cam_backlight_off(self, device):
        return self.cmd_cam_backlight_set(device, 0x03)
        
    def cmd_cam_backlight_on(self, device):
        return self.cmd_cam_backlight_set(device, 0x02)
        
        
    # High Resolution
    
    def cmd_cam_hires_set(self, device, mode):
        subcmd=b'\x52'+bytes([mode])
        return self.cmd_cam(device, subcmd)
        
    def cmd_cam_hires_off(self, device):
        return self.cmd_cam_hires_set(device, 0x03)
        
    def cmd_cam_hires_on(self, device):
        return self.cmd_cam_hires_set(device, 0x02)
    
    # Picture Effect
    
    def cmd_cam_effect_negative(self, device):
        subcmd = b'\x63\x02'
        return self.cmd_cam(device,subcmd)
        pass
        
    def cmd_cam_effect_blackwhite(self, device):
        subcmd = b'\x63\x04'
        return self.cmd_cam(device,subcmd)
        pass
        
    def cmd_cam_effect_off(self, device):
        subcmd = b'\x63\x00'
        return self.cmd_cam(device,subcmd)
        pass
        
    # Aperture Control
    def cmd_cam_aperture_control(self,device,mode):
        step=b'\x1F'
        subcmd=b'\x1F\x02'+bytes([mode])+bytes([step])
        return self.cmd_cam(device,subcmd)
        
    def cmd_cam_aperture_control_up(self,device):
        return self.cmd_cam_aperture_control(device, 0x02)
        
    def cmd_cam_aperture_control_down(self,device):
        return self.cmd_cam_aperture_control(device, 0x03)
        
    def cmd_cam_aperture_control_direct(self, device, level):
        #expecting level to be controllable on 16 level. The values 
        # however range from 0x00 to 0xFF so I expect each step to be
        # 0x10 wide. 
        if level not in range (1,17):
            return False
        
        level_01=b'\x00'
        level_02=bytes([level-1])
                
        subcmd=b'\x1F\x42\x00\x00'+level_01+level_02
        return self.cmd_cam(device,subcmd)
        
    def cmd_cam_aperture_control_reset(self,device):
        subcmd=b"\x1F\x02\x00\x00"
        return self.cmd_cam(device,subcmd)
        
    def cmd_cam_register_set(self, device, register_bytes, value):
        print(' Someone called set register !!! ')
        value01 = ( value[0] & 0b11110000 ) >> 4
        value02 = value[0] & 0b00001111
        subcmd=b'\x24'+register_bytes+bytes([value01])+bytes([value02])
        return self.cmd_cam(device,subcmd)
        
        
    # --------------------- Getters --------------------------------------

    def cmd_inquiry(self,device,subcmd):
        packet=b'\x09\x04'+subcmd
        reply = self.send_packet(device,packet)
        #FIXME: check returned data here and retransmit?
        return reply
        
    def keep_trying_to_get_zoom_position(self, device):
        reply = b''
        position = b''
        max_retries = 5
        retries = 0
        while len(position) != 4 and retries<max_retries:
            subcmd=b'\x47'
            reply = self.cmd_inquiry(device, subcmd)
            position = self.get_data_from_inquiry(reply)    
            
            #Sometimes the command just returns COMPLETION with no data.
            # In this case, we can use stop zoom cmd that kindly seems
            # to return the zoom position
            if len(position) != 4:
                print('got position %s, stopping zoom speed and trying again' % position)
                reply = self.cmd_cam_zoom_stop(device)
                position = self.get_data_from_inquiry(reply)    
                print('now got position %s, is this good?' % position)
                
            #try again, this happens when you switch from zoom speed
            # to zoom absolute
            retries =+1
            
        return position
        
    def inquiry_precise_zoom_position(self, device):
        position = self.keep_trying_to_get_zoom_position(device)
        if len(position) != 4:
            return None

        #number between 0x00000000 and 0x40000000
        pos_int = struct.unpack('>I', position)[0]
        return pos_int

    def inquiry_combined_zoom_pos(self, device):
        self.DEBUG = True
        position = self.keep_trying_to_get_zoom_position(device)
        if len(position) != 4:
            return None
            
        try:
            pos = self.ZOOM_SETTINGS.index(position)
        except:
            print('Zoom position is not in the 1-41x range, getting %s' % (position))
            #in this case we have to convert everything to an integer
            # perform comparisons and then return the closest value
            #This can happen if someone uses tele/wide zoom commands
            #import pdb;pdb.set_trace()
            pos_int = struct.unpack('>I', position)[0]

            pos = self.ZOOM_SETTINGS.index(struct.pack('>I',takeClosest(self.ZOOM_SETTINGS_INT, pos_int)))

            print('Returning approximate position %d for position %s' % ((pos+1), position))
            #self.cmd_cam_zoom_direct(device, pos+1)

        self.DEBUG = False
        return pos
        
    def inquiry_mirror_mode(self, device):
        subcmd=b'\x61'
        reply = self.cmd_inquiry(device, subcmd)
        mode = self.get_data_from_inquiry(reply)
        if mode == b'\x02':
            return True
        if mode == b'\x03':
            return False
            
    def inquiry_flip_mode(self, device):
        subcmd=b'\x66'
        reply = self.cmd_inquiry(device, subcmd)
        mode = self.get_data_from_inquiry(reply)
        if mode == b'\x02':
            return True
        if mode == b'\x03':
            return False
            
    def inquiry_negative_mode(self,device):
        subcmd=b'\x63'
        reply = self.cmd_inquiry(device, subcmd)
        mode = self.get_data_from_inquiry(reply)
        if mode == b'\x02':
            return True
        else:
            return False
            
    def inquiry_blackwhite_mode(self,device):
        subcmd=b'\x63'
        reply = self.cmd_inquiry(device, subcmd)
        mode = self.get_data_from_inquiry(reply)
        if mode == b'\x04':
            return True
        else:
            return False
            
    def inquiry_backlight_mode(self, device):
        subcmd=b'\x33'
        reply = self.cmd_inquiry(device, subcmd)
        mode = self.get_data_from_inquiry(reply)
        if mode == b'\x02':
            return True
        elif mode == b'\x03':
            return False
            
    def inquiry_hires_mode(self, device):
        subcmd=b'\x52'
        reply = self.cmd_inquiry(device, subcmd)
        mode = self.get_data_from_inquiry(reply)
        if mode == b'\x02':
            return True
        elif mode == b'\x03':
            return False
            
    def inquiry_image_stabilization(self,device):
        subcmd=b'\x34'
        reply = self.cmd_inquiry(device, subcmd)
        mode = self.get_data_from_inquiry(reply)
        if mode == b'\x02':
            return True
        elif mode == b'\x03':
            return False
        elif mode == b'\x00':
            return 'Hold'
            
    def inquiry_stablezoom(self,device):
        return False
        
    def inquiry_register(self, device, register):
        subcmd=b'\x24'+register
        reply = self.cmd_inquiry(device, subcmd)
        mode = self.get_data_from_inquiry(reply)
        value = bytes([(mode[0]&0b00001111)<<4 | mode[1]&0b00001111])
        return self.REGISTER_VALUES[register][value]
        
        
        
    # --------------------- NOT TESTED FROM NOW ON -----------------------

    # freeze
    def cmd_cam_freeze(self,device,mode):
        subcmd=b"\x62"+bytes([mode])
        return self.cmd_cam(device,subcmd)

    def cmd_cam_freeze_on(self,device):
        return self.cmd_cam_freeze(device,0x02)

    def cmd_cam_freeze_off(self,device):
        return self.cmd_cam_freeze(device,0x03)



    # Picture Effects
    def cmd_cam_picture_effect(self,device,mode):
        subcmd=b"\x63"+bytes([mode])
        return self.cmd_cam(device,subcmd)

    def cmd_cam_picture_effect_off(self,device):
        return self.cmd_cam_picture_effect(device,0x00)

    def cmd_cam_picture_effect_pastel(self,device):
        return self.cmd_cam_picture_effect(device,0x01)

    def cmd_cam_picture_effect_negart(self,device):
        return self.cmd_cam_picture_effect(device,0x02)

    def cmd_cam_picture_effect_sepa(self,device):
        return self.cmd_cam_picture_effect(device,0x03)

    def cmd_cam_picture_effect_bw(self,device):
        return self.cmd_cam_picture_effect(device,0x04)

    def cmd_cam_picture_effect_solarize(self,device):
        return self.cmd_cam_picture_effect(device,0x05)

    def cmd_cam_picture_effect_mosaic(self,device):
        return self.cmd_cam_picture_effect(device,0x06)

    def cmd_cam_picture_effect_slim(self,device):
        return self.cmd_cam_picture_effect(device,0x07)

    def cmd_cam_picture_effect_stretch(self,device):
        return self.cmd_cam_picture_effect(device,0x08)



    # Digital Effect

    def cmd_cam_digital_effect(self,device,mode):
        subcmd=b"\x64"+bytes([mode])
        return self.cmd_cam(device,subcmd)

    def cmd_cam_digital_effect_off(self,device):
        return self.cmd_cam_digital_effect(device,0x00)

    def cmd_cam_digital_effect_still(self,device):
        return self.cmd_cam_digital_effect(device,0x01)

    def cmd_cam_digital_effect_flash(self,device):
        return self.cmd_cam_digital_effect(device,0x02)

    def cmd_cam_digital_effect_lumi(self,device):
        return self.cmd_cam_digital_effect(device,0x03)

    def cmd_cam_digital_effect_trail(self,device):
        return self.cmd_cam_digital_effect(device,0x04)


    def cmd_cam_digital_effect_level(self,device,level):
        subcmd=b"\x65"+bytes( [0b00111111 & level])
        return self.cmd_cam(device,subcmd)


    # memory of settings including position
    def cmd_cam_memory(self,device,func,num):
        if num>5:
            num=5
        if func<0 or func>2:
            return
        print ("DEBUG: cam_memory command")
        subcmd=b"\x3f"+bytes([func])+bytes( [0b0111 & num])
        return self.cmd_cam(device,subcmd)


    #FIXME; Can only be executed when motion has stopped!!!
    def cmd_cam_memory_reset(self,device,num):
        return self.cmd_cam_memory(device,0x00,num)

    def cmd_cam_memory_set(self,device,num):
        return self.cmd_cam_memory(device,0x01,num)

    def cmd_cam_memory_recall(self,device,num):
        return self.cmd_cam_memory(device,0x02,num)


    # Datascreen control

    def cmd_datascreen(self,device,func):
        subcmd=b'\x06'+bytes([func])
        return self.cmd_pt(device,subcmd)

    def cmd_datascreen_on(self,device):
        return self.cmd_datascreen(device,0x02)

    def cmd_datascreen_off(self,device):
        return self.cmd_datascreen(device,0x03)

    def cmd_datascreen_toggle(self,device):
        return self.cmd_datascreen(device,0x10)

from bisect import bisect_left

def takeClosest(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
       return after
    else:
       return before
