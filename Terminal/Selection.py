class Selection:
    _start = 0
    _end = 0

    def GetStart(self):
        return self._start

    def GetEnd(self):
        return self._end

    def SetStart(self, start):
        self._start = start

    def SetEnd(self, end):
        self._end = end

    def IsSelected(self, position=None):
        if self._end <= self._start:
            return False

        if position is not None:
            return self._end >= position and self._start <= position

        return True
