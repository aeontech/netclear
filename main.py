#!/usr/bin/env python3

from __future__ import print_function

import locale
from bits import helpers
from bits import netserial
from bits.prompt import Prompt
from devices import devices

locale.setlocale(locale.LC_ALL, '')

options = ['%s' % x for x in helpers.get_serial_ports()]
supported = helpers.get_supported_devices()

# selected = Prompt("Choose Communications Port")
# selected.setComms(options)
# selected.setDevices(supported)
# selected.display()

# Open serial communications
port = "COM5"  # selected.get('comms')
baud = 9600  # selected.get('baud')
cereal = netserial.Serial(port, baud)

# Choose device type and get instance of device
chosen = "cisco.asa55xx"  # selected.get('device')
device = devices.get(chosen)
device = device()

# Give comms to the device and start running commands
device.setCommsPort(cereal)
device.run()

# Close our serial communications
cereal.close()
