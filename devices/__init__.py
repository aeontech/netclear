import sys
import importlib

def exists(name):
    if sys.version_info[0] is not 3:
        raise EnvironmentError('Python v%d is not supported' % sys.version_info[0])

    if sys.version_info[1] < 4:
        loader = importlib.find_loader(name)
    else:
        loader = importlib.util.find_spec(name)

    return loader is not None

def include(name):
    importlib.import_module(name)

def get(name):
    if not exists(name):
        raise LookupError('Device "%s" not supported' % name)

    include(name)

    return name()
