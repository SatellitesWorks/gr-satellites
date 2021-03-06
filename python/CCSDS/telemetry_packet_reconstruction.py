#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Athanasios Theocharis <athatheoc@gmail.com>
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

from gnuradio import gr
import pmt
from . import telemetry
from . import space_packet
import array

class telemetry_packet_reconstruction(gr.basic_block):
    """
    docstring for block telemetry_packet_reconstruction
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="telemetry_packet_reconstruction",
            in_sig=[],
            out_sig=[])

        self.space_packet = []
        self.length_of_space_packet = 0
        ##################################################
        # Blocks
        ##################################################
        self.message_port_register_in(pmt.intern('in'))
        self.set_msg_handler(pmt.intern('in'), self.handle_msg)
        self.message_port_register_out(pmt.intern('out'))

    def handle_msg(self, msg_pmt):
        msg = pmt.cdr(msg_pmt)
        if not pmt.is_u8vector(msg):
            print("[ERROR] Received invalid message type. Expected u8vector")
            return
        packet = bytearray(pmt.u8vector_elements(msg))
        size = len(packet) - 6
        try:
            header = telemetry.PrimaryHeader.parse(packet[:])
            if header.ocf_flag == 1:
                size -= 4
        except:
            print("Could not decode telemetry packet")
            return

        parsed = telemetry.FullPacket.parse(packet[:], size=size)

        payload = parsed.payload
        #The number 6 is used here, because that's the length of the Primary Header.
        #todo: Add a variable for this
        while len(payload) != 0:
            if len(self.space_packet) < 6:
                left = 6 - len(self.space_packet)
                self.space_packet.extend(payload[:left])
                payload = payload[left:]
            if len(self.space_packet) >= 6:
                self.length_of_space_packet = space_packet.PrimaryHeader.parse(bytearray(self.space_packet)).data_length
                left = self.length_of_space_packet + 6 - len(self.space_packet)
                self.space_packet.extend(payload[:left])
                payload = payload[left:]
                if 6 + self.length_of_space_packet == len(self.space_packet):
                    self.sendPacket()

    def sendPacket(self):
        packet = self.space_packet
        packet = array.array('B', packet[:])
        packet = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(packet), packet))
        self.message_port_pub(pmt.intern('out'), packet)
        self.length_of_space_packet = 0
        self.space_packet = []
