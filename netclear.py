#!/usr/bin/env python3

from __future__ import print_function

import serial
import locale
import helpers
import devices
from prompt import Prompt

locale.setlocale(locale.LC_ALL, '')

options  = ['%s' % x for x in helpers.get_serial_ports()]
devices  = helpers.get_supported_devices()

selected = Prompt("Choose Communications Port")
selected.setComms(options)
selected.setDevices(devices)
selected.display()

# Open serial communications
port   = selected.get('comms')
baud   = selected.get('baud')
cereal = serial.Serial(port, baud)

# Choose device type and get instance of device
chosen = selected.get('device')
device = devices.get(chosen)

# Give comms to the device and start running commands
device.setCommsPort(cereal)
device.run()

# Close our serial communications
cereal.close()
