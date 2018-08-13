import sys
import importlib


def exists(name):
    if sys.version_info[0] is not 3:
        raise EnvironmentError('Python v%d is not supported' %
                               sys.version_info[0])

    if sys.version_info[1] < 4:
        loader = importlib.find_loader(name)
    else:
        from importlib import util
        loader = importlib.util.find_spec(name, package="devices")

    return loader is not None


def include(name):
    return importlib.import_module(name)


def get(name):
    if not exists("devices.%s" % name):
        raise LookupError('Device "%s" not supported' % name)

    module = include("devices.%s" % name)
    return getattr(module, name.split('.')[-1])
