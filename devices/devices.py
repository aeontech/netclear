import sys
import importlib

# Now we include all devices... Thanks, PyInstaller!
import devices.cisco.asa55xx
import devices.cisco.rt7000
import devices.cisco.sw29xx
import devices.cisco.sw35xx
import devices.cisco.sw37xx
import devices.cisco.sw45xx
import devices.cisco.sw49xx
import devices.dell.Force10

def get(name):
    registered = {
        'cisco.asa55xx': devices.cisco.asa55xx.asa55xx,
        'cisco.rt7000': devices.cisco.rt7000.rt7000,
        'cisco.sw29xx': devices.cisco.sw29xx.sw29xx,
        'cisco.sw35xx': devices.cisco.sw35xx.sw35xx,
        'cisco.sw37xx': devices.cisco.sw37xx.sw37xx,
        'cisco.sw45xx': devices.cisco.sw45xx.sw45xx,
        'cisco.sw49xx': devices.cisco.sw49xx.sw49xx,
        'dell.Force10': devices.dell.Force10.Force10,
    }

    if name in registered:
        return registered[name]

    raise LookupError('Device "%s" not supported' % name)
