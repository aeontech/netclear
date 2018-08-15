#!/usr/bin/env python3

from __future__ import print_function

import wx
import locale
from bits import helpers
from bits import netserial
from devices import devices
from bits.prompt import Prompt
from serial.serialutil import SerialException

locale.setlocale(locale.LC_ALL, '')

options = ['%s' % x for x in helpers.get_serial_ports()]
supported = helpers.get_supported_devices()

wx.App()

selected = Prompt("Choose Communications Port")
selected.setComms(options)
selected.setDevices(supported)
selected.display()

# Open serial communications
port = selected.get('comms')
baud = selected.get('baud')

try:
    cereal = netserial.Serial(port, baud, timeout=0.1)
except SerialException as ex:
    dialog = wx.MessageDialog(None, 'Serial Error: {0}'.format(ex))
    dialog.ShowModal()
    dialog.Destroy()

    raise SystemExit()

# Choose device type and get instance of device
chosen = selected.get('device')
device = devices.get(chosen)
device = device()

# Give comms to the device and start running commands
device.setCommsPort(cereal)
device.run()

# Close our serial communications
cereal.close()
