import os
import glob
import platform
from serial.tools import list_ports

def get_serial_ports():
    sys = platform.system()

    if sys is 'Linux' or sys is 'Cygwin':
        return _get_serial_ports_linux()
    elif sys is 'Windows':
        return _get_serial_ports_windows()
    elif sys is 'Darwin':
        pass

    raise EnvironmentError('Unsupported platform "%s"' % platform.system())

def _get_serial_ports_windows():
    return [port.device for port in list_ports.comports()]

def _get_serial_ports_linux():
    return []

def get_supported_devices():
    devices = glob.glob('devices/*/*.py')

    mask = "devices%s" % os.sep
    devices = [x.replace(mask, '').replace('.py', '') for x in devices]

    return list(filter(lambda x: x.find('__init__') is -1, devices))