class Base:
    _comms = None

    def __init__(self):
        pass

    def getCommsPort():
        return self._comms

    def setCommsPort(communications):
        self._comms = communications

    def run():
        raise NotImplementedError()
