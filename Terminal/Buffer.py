import re

from .Selection import Selection

class Line:
    _contents = None
    _wrap = False
    _limit = 80
    _lines = None

    def __init__(self, contents=''):
        self._contents = contents
        self._lines = []

        self._process()

    def __str__(self):
        return self._contents

    def __getitem__(self, key):
        return self._contents[key]

    def __setitem__(self, key, value):
        self._contents[key] = value
        self._process()

    def __delitem__(self, key):
        del self._contents[key]
        self._process()

    def __contains__(self, item):
        return item in self._contents

    def __len__(self):
        return len(self._contents)

    def __add__(self, value):
        buff = self()
        buff._contents = self._contents + value
        buff._process()

        return buff

    def __radd__(self, value):
        buff = self()
        buff._contents = value + self._contents
        buff._process()

        return buff

    def __iadd__(self, value):
        self._contents += value
        self._process()

        return self

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n >= len(self._lines):
            raise StopIteration

        last = self.n
        self.n += 1

        return self._lines[last]

    def GetWrap(self):
        return self._wrap

    def SetWrap(self, wrap):
        self._wrap = wrap

        self._process()

    def GetLimit(self):
        return self._limit

    def SetLimit(self, limit):
        self._limit = limit

        self._process()

    def _process(self):
        if not self.GetWrap():
            return

        limit = self.GetLimit()
        self._lines = []

        lineLen = len(self._contents.rstrip())

        for i in range(math.ceil(lineLen/limit)):
            start = i * limit
            end = min((i + 1) * limit, lineLen)

            self._lines.append(self._contents[start:end])

        # This was just an empty line
        if not self._lines:
            self._lines = ['']


class Text:
    _contents = None
    _wrap = False
    _lines = None
    _limit = 80
    _selection = Selection()
    _c2iCache = {}
    _i2cCache = {}
    _numRows = None

    _re_esc = None

    def __init__(self, contents=''):
        self._re_esc = re.compile('\b')

        self._contents = contents
        self._lines = []
        self._process()

    def __str__(self):
        return self._contents

    def __getitem__(self, key):
        return self._contents[key]

    def __setitem__(self, key, value):
        self._contents[key] = value
        self._process()

    def __delitem__(self, key):
        del self._contents[key]
        self._process()

    def __contains__(self, item):
        return item in self._contents

    def __len__(self):
        return len(self._contents)

    def __add__(self, value):
        buff = self()
        buff._contents = self._contents + value
        buff._selection = self._selection
        buff._process()

        return buff

    def __radd__(self, value):
        buff = self()
        buff._contents = value + self._contents
        buff._selection = self._selection
        buff._process()

        return buff

    def __iadd__(self, value):
        self._contents += value
        self._process()

        return self

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n >= len(self._lines):
            raise StopIteration

        last = self.n
        self.n += 1

        return self._lines[last]

    def GetWrap(self):
        return self._wrap

    def SetWrap(self, wrap):
        if self._wrap == wrap:
            return

        self._wrap = wrap
        self.InvalidateCache()
        self._updateLines()

    def GetLimit(self):
        return self._limit

    def SetLimit(self, limit):
        if self._limit == limit:
            return

        self._limit = limit
        self.InvalidateCache()
        self._updateLines()

    def GetSelection(self):
        return self._selection

    def SetSelection(self, selection):
        self._selection = selection

    def SetSelectionStart(self, start):
        assert start >= 0, "Selection start must be 0 or above. '%d' must " \
                           "be greater than or equal to 0." % (start)
        self._selection.SetStart(start)

    def SetSelectionEnd(self, end):
        assert end <= len(self), "Selection end must not exceed the buffer " \
                                 "length. '%d' must be less than or equal " \
                                 "to %d." % (end, len(self))
        self._selection.SetEnd(end)

    def GetNumLines(self):
        return len(self._lines)

    def GetNumRows(self):
        if self._numRows is None:
            rows = 0

            for line in self._lines:
                for wrap in line:
                    rows += 1

            self._numRows = rows

        return self._numRows

    def GetLineForRow(self, row):
        lineNo = 1

        for line in self._lines:
            for wrap in line:
                if row == lineNo:
                    return wrap

                lineNo += 1

    def InvalidateCache(self):
        self._numRows = None
        self._c2iCache = {}
        self._i2cCache = {}

    def _process(self):
        self.InvalidateCache()
        self._processText()
        self._processLines()

    def _processText(self):
        contents = self._contents
        index = 0

        while 1:
            index = self._re_esc.search(contents, index)

            if index is None:
                break

            index = index.span()[0]

            # Backspace character
            if contents[index] == '\b':
                contents = contents[:index-1] + contents[index+1:]
                index -= 1

        self._contents = contents

    def _processLines(self):
        del self._lines
        self._lines = []

        for line in self._contents.splitlines(True):
            lineObj = _LineBuffer(line)
            self._lines.append(lineObj)

        self._updateLines()

    def _updateLines(self):
        wrap = self.GetWrap()
        limit = self.GetLimit()

        for line in self._lines:
            line.SetWrap(wrap)
            line.SetLimit(limit)

    def CursorToIndex(self, col, row):
        index = 0
        lineNo = 0
        numRows = self.GetNumRows()

        assert row > 0, 'Row "%d" below one' % row
        assert row <= numRows, 'Row "%d" greater than total rows %d' % \
                               (row, numRows)
        assert col >= 0, 'Column "%d" invalid' % col

        # Caching!
        if "%d-%d" % (col, row) in self._c2iCache:
            return self._c2iCache["%d-%d" % (col, row)]

        for i in range(len(self._lines)):
            lineLen = len(str(self._lines[i]))

            for wrap in self._lines[i]:
                wrapLen = len(wrap)
                lineLen -= wrapLen
                lineNo += 1

                if not lineNo == row:
                    index += wrapLen
                    continue

                m = min(col, wrapLen)
                index += m
                lineLen -= m
                break

            if lineNo == row:
                break
            else:
                index += lineLen
        else:
            raise RuntimeError('Reached end of buffer')

        self._c2iCache["%d-%d" % (col, row)] = index

        return index

    def IndexToCursor(self, index):
        row = 1
        col = 0
        counted = 0         # Number of indexes counted
        limit = self.GetLimit()

        assert index >= 0, 'Invalid index position "%d".' % index
        assert index <= len(self), 'Invalid index position "%d".' % index

        # Caching!
        if index in self._i2cCache:
            return self._i2cCache[index]

        for lineNo in range(len(self._lines)):
            lineLen = len(self._lines[lineNo])
            lineEnd = lineLen - len(str(self._lines[lineNo]).rstrip())

            # If index is beyond this line, add and skip
            if counted + lineLen < index:
                counted += lineLen

                if (self.GetWrap()):
                    numLines = math.ceil((lineLen - lineEnd) / limit)

                    # If the line is empty, we still want to add a line.
                    # Enforce a minimum of one line here.
                    row += max(1, numLines)
                else:
                    row += 1

                continue

            for wrap in self._lines[lineNo]:
                wrapLen = len(wrap)

                # Another wrapped row, no match
                if (counted + wrapLen) < index:
                    counted += wrapLen
                    row += 1
                    continue

                col = index - counted
                counted += col
                break


            if counted >= index:
                break

        else:
            raise RuntimeError('Reached end of buffer')

        self._i2cCache[index] = col, row

        return col, row
