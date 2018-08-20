import wx
import re
import math
from wx.lib.scrolledpanel import ScrolledPanel


class _TextSelection:
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


class _LineBuffer:
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


class _TextBuffer:
    _contents = None
    _wrap = False
    _lines = None
    _limit = 80
    _selection = _TextSelection()
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
        self._selection.SetStart(start)

    def SetSelectionEnd(self, end):
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
        assert col >= 0, 'Column "%d" invalid' % row

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

        self._c2iCache["%d-%d" % (col, row)] = index

        return index

    def IndexToCursor(self, index):
        row = 1
        col = 0
        total = 0
        limit = self.GetLimit()

        if index < 0 or index > len(self):
            raise IndexError('Invalid index position "%d".' % index)

        # Caching!
        if index in self._i2cCache:
            return self._i2cCache[index]

        for lineNo in range(len(self._lines)):
            lineLen = len(self._lines[lineNo])
            lineEnd = lineLen - len(str(self._lines[lineNo]).rstrip())

            if total >= index:
                break

            # If index is beyond this line, add and skip
            if total + lineLen <= index:
                total += lineLen

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

                if (total + wrapLen) < index:
                    total += wrapLen
                    row += 1
                    continue

                col = index - total
                total += col
                break

        self._i2cCache[index] = col, row

        return col, row


class TerminalCtrl(ScrolledPanel):
    _buffer = None
    _metrics = None
    _lineSpacing = 0
    _overlay = None

    _scrollPos = None
    _scrollbarFollowText = True

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.TAB_TRAVERSAL,
                 name=wx.ControlNameStr):

        # Disallow borders
        style &= ~(wx.BORDER_DEFAULT | wx.BORDER_SIMPLE | wx.BORDER_SUNKEN) & \
                 ~(wx.BORDER_RAISED | wx.BORDER_STATIC | wx.BORDER_THEME)

        style |= wx.BORDER_NONE
        style |= wx.WANTS_CHARS

        # Set initial buffer - This must be performed before calling __init__
        # on the parent class
        self._buffer = _TextBuffer()

        # Initial scroll position - required for best client size, which is
        # called upon window creation. Set to buffer index 0
        self._scrollPos = 0

        super().__init__(parent, id, pos, size, style, name)

        self.SetFont(wx.Font(pointSize=13, family=wx.FONTFAMILY_TELETYPE,
                     style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_LIGHT))

        # Set initial colouring
        back = self.GetBackgroundColour()
        self.SetBackgroundColour(self.GetForegroundColour())
        self.SetForegroundColour(back)

        # This will be our text selection overlay
        self._overlay = wx.Overlay()

        # Set up scrolling
        self.EnableScrolling(True, True)

        self.Bind(wx.EVT_PAINT, self._OnPaint)
        self.Bind(wx.EVT_SIZE,  self._OnSize)
        self.Bind(wx.EVT_SCROLLWIN, self._OnScroll)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self._OnEraseBackground)

        self.Bind(wx.EVT_LEFT_DOWN, self._OnMouseDown)
        self.Bind(wx.EVT_MOTION, self._OnMouseMove)
        self.Bind(wx.EVT_LEFT_UP, self._OnMouseUp)

        self._OnSize(None)

    def AddChars(self, chars):
        self._buffer += chars

        # Now we must recalculate
        self.InvalidateBestSize()
        self.Refresh()

    # As per wx.TextEntry
    def GetValue(self):
        return self._buffer

    def SetFont(self, font):
        super().SetFont(font)

        # Now we must recalculate
        self.InvalidateMetrics()
        self.InvalidateBestSize()
        self.Refresh()

    def SetFontSize(self, size):
        font = self.GetFont()
        font.SetPointSize(size)
        self.SetFont(font)

    def GetFontSize(self):
        return self.GetFont().GetPointSize()

    def SetSpacing(self, spacing):
        self._lineSpacing = spacing

        # Now we must recalculate
        self.InvalidateBestSize()
        self.Refresh()

    def GetSpacing(self):
        return self._lineSpacing

    def SetWrap(self, wrap=None):
        self._buffer.SetWrap(wrap)

        # Now we must recalculate
        self.InvalidateBestSize()
        self.Refresh()

    def GetWrap(self):
        return self._buffer.GetWrap()

    def SetSelectionStart(self, start):
        self._buffer.SetSelectionStart(start)

    def SetSelectionEnd(self, end):
        self._buffer.SetSelectionEnd(end)

    def GetSelected(self):
        selection = self._buffer.GetSelection()
        start = selection.GetStart()
        end = selection.GetEnd()

        return self._buffer[start:end]

    def DoGetBestClientSize(self):
        textWidth, textHeight = self.GetTextMetrics()
        spacing = self.GetSpacing()

        buflen = self._buffer.GetNumRows()
        height = (textHeight + spacing) * buflen
        width = 0
        scrollbarWidth = wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y)

        if not self.GetWrap():
            for line in self._buffer:
                width = max(width, len(line))

        if self.GetWrap() or width == 0:
            width, _ = self.GetParent().ClientSize
            width = math.floor((width - scrollbarWidth) / textWidth)

        if height == 0:
            _, height = self.GetParent().ClientSize

        # Refresh scrollbar size
        if self.GetWrap():
            self.ShowScrollbars(False, True)
            self.EnableScrolling(False, True)
        else:
            self.ShowScrollbars(True, True)
            self.EnableScrolling(True, True)

        self.SetScrollbars(textWidth, textHeight + spacing, width, buflen, True)

        # If we are to scroll with the text, update the scroll index to
        # appropriate index
        if self._scrollbarFollowText and buflen > 0:
            visRows = self.GetNumVisibleRows()

            rowAtTop = buflen - visRows
            rowAtTop = max(1, rowAtTop)

            self._scrollPos = self._buffer.CursorToIndex(0, rowAtTop)

        if buflen == 0:
            scrollPos = 0, 1
        else:
            scrollPos = self._buffer.IndexToCursor(self._scrollPos)

        # Adjust from 1-based rows to 0-based
        scrollPos = scrollPos[0], scrollPos[1] - 1

        self.Scroll(scrollPos)

        width = (width * textWidth)

        return wx.Size(width, height)

    # Invalidates then immediatelt re-calculates best size
    def InvalidateBestSize(self):
        super().InvalidateBestSize()
        BestSize = self.GetBestSize()
        self.CacheBestSize(BestSize)

    def InvalidateMetrics(self):
        self._metrics = None

    def LogicalToBuffer(self, point):
        textWidth, textHeight = self.GetTextMetrics()
        spacing = self.GetSpacing()

        row = math.ceil(point.y / (textHeight + spacing))
        col = math.floor(point.x / textWidth)

        line = self._buffer.GetLineForRow(row)
        lineLen = len(line)
        col = min(lineLen - 1, col)

        return col, row

    def BufferToLogical(self, col, row):
        textWidth, textHeight = self.GetTextMetrics()
        spacing = self.GetSpacing()

        x = textWidth * col
        y = (textHeight + spacing) * (row-1)

        return wx.Point(x, y)

    def GetTextMetrics(self):
        if self._metrics is None:
            dc = wx.ScreenDC()
            dc.SetFont(self.GetFont())

            textWidth, textHeight, descent, leading = dc.GetFullTextExtent('#')

            self._metrics = (textWidth, textHeight)

        return self._metrics

    def GetNumVisibleRows(self):
        _, textHeight = self.GetTextMetrics()
        lineHeight = textHeight + self.GetSpacing()
        _, screenHeight = self.GetClientSize()

        return math.floor(screenHeight / lineHeight)

    def _Draw(self, dc):
        backColor = self.GetBackgroundColour()
        backBrush = wx.Brush(backColor, wx.SOLID)
        dc.SetBackground(backBrush)
        dc.Clear()

        foreColor = self.GetForegroundColour()
        dc.SetTextForeground(foreColor)
        dc.SetFont(self.GetFont())

        textWidth, textHeight = self.GetTextMetrics()

        lineNo = 0
        for line in self._buffer:
            for wrap in line:
                lineNo += 1
                _, y = self.BufferToLogical(0, lineNo)

                dc.DrawText(str(wrap), 0, y)

        self._DrawSelection(dc)

    def _DrawSelection(self, dc):
        selection = self._buffer.GetSelection()
        self._overlay.Reset()

        if not selection.IsSelected():
            return

        highBackColor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        highBackBrush = wx.Brush(highBackColor, wx.SOLID)
        highForeColor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)

        startIdx = selection.GetStart()
        endIdx = selection.GetEnd()
        selStart = self._buffer.IndexToCursor(startIdx)
        selEnd = self._buffer.IndexToCursor(endIdx)

        odc = wx.DCOverlay(self._overlay, dc)
        odc.Clear()

        dc.SetBackground(highBackBrush)
        dc.SetTextForeground(highForeColor)

        # Calculate locations
        left = self.BufferToLogical(selStart[0], selStart[1])
        textWidth, lineHeight = self.GetTextMetrics()

        for row in range(selStart[1], selEnd[1] + 1):
            line = self._buffer.GetLineForRow(row)

            lineLen = len(line)

            if row == selStart[1]:
                startX, startY = left
                line = line[selStart[0]:]
            else:
                startX, startY = 0, (row - 1) * lineHeight

            if row == selEnd[1]:
                end = selEnd[0]

                if row == selStart[1]:
                    line = line[0:end - selStart[0]]
                else:
                    line = line[0:end]
            else:
                end = lineLen

            endX, _ = self.BufferToLogical(end, row)

            # If this is the end of a line, add to the selection
            if (lineLen == 0 or line[-1] == '\r' or line[-1] == '\n') and \
                    not row == selEnd[1]:
                endX += textWidth * 0.5

            width, height = endX - startX, lineHeight

            rect = wx.Rect(startX, startY, width + 1, height)
            dc.DrawRectangle(rect)
            dc.DrawText(line, startX, startY)

        # To ensure the overlay is destroyed before the device context
        del odc

    def _OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        self.PrepareDC(dc)
        self._Draw(dc)

    def _OnSize(self, event):
        textWidth, textHeight = self.GetTextMetrics()
        wW, _ = self.VirtualSize

        if not self.GetWrap():
            return

        self._buffer.SetLimit(math.floor(wW / textWidth))

        if self.GetWrap():
            self.InvalidateBestSize()

    def _OnScroll(self, event):
        evtType = event.GetEventType()
        currScroll = self._buffer.IndexToCursor(self._scrollPos)

        # Adjust from 1-based rows to 0-based
        currScroll = currScroll[0], currScroll[1] - 1

        currPos = currScroll[0] if event.GetOrientation() == wx.HORIZONTAL \
                                else currScroll[1]

        # A few helper variables for the following lambdas
        numRows = self._buffer.GetNumRows()
        numVisibleRows = self.GetNumVisibleRows()
        maxScroll = max(0, numRows - numVisibleRows)

        handlers = {
             wx.EVT_SCROLLWIN_TOP.evtType[0]: lambda:
                event.SetPosition(0)
            ,wx.EVT_SCROLLWIN_BOTTOM.evtType[0]: lambda:
                event.SetPosition(maxScroll)
            ,wx.EVT_SCROLLWIN_LINEUP.evtType[0]: lambda:
                event.SetPosition(max(0, currPos - 1))
            ,wx.EVT_SCROLLWIN_LINEDOWN.evtType[0]: lambda:
                event.SetPosition(min(maxScroll, currPos + 1))
            ,wx.EVT_SCROLLWIN_PAGEUP.evtType[0]: lambda:
                # Can this be applied to PAGELEFT?
                event.SetPosition(max(0, currPos - numVisibleRows))
            ,wx.EVT_SCROLLWIN_PAGEDOWN.evtType[0]: lambda:
                # Can this be applied to PAGERIGHT?
                event.SetPosition(min(maxScroll, currPos + numVisibleRows))
            ,wx.EVT_SCROLLWIN_THUMBTRACK.evtType[0]: lambda:
                0 == 0  # GetPosition is set appropriately
            ,wx.EVT_SCROLLWIN_THUMBRELEASE.evtType[0]: lambda:
                0 == 0  # GetPosition is set appropriately
        }

        # Set GetPosition appropriately
        handlers[evtType]()

        if event.GetOrientation() == wx.HORIZONTAL:
            currScroll = event.GetPosition(), currScroll[1]

        if event.GetOrientation() == wx.VERTICAL:
            currScroll = currScroll[0], event.GetPosition()

        # +1 because currScroll is 1-based not 0-based
        if (numRows - currScroll[1] - numVisibleRows + 1) <= 0:
            self._scrollbarFollowText = True
        else:
            self._scrollbarFollowText = False

        self.Scroll(currScroll)
        # Adjust from 0-based rows to 1-based
        currScroll = currScroll[0], currScroll[1] + 1
        currScroll = self._buffer.CursorToIndex(currScroll[0], currScroll[1])
        self._scrollPos = currScroll

    def _OnEraseBackground(self, event):
        # This is intentionally blank
        pass

    def _OnMouseDown(self, event):
        self.CaptureMouse()

        maxY = self.GetTextMetrics()[1] * self._buffer.GetNumRows()

        pos = self.CalcUnscrolledPosition(event.GetPosition())
        pos = wx.Point(pos[0], max(1, pos[1]))

        # If we have moved the mouse past the end of the document
        # we should select the rest of the document
        if pos.y > maxY:
            index = len(str(self._buffer).rstrip()) - 1
        else:
            col, row = self.LogicalToBuffer(pos)
            index = self._buffer.CursorToIndex(col, row)

        self._buffer.SetSelectionStart(0)
        self._buffer.SetSelectionEnd(0)

        self._dragStart = index

        self.Refresh()

    def _OnMouseMove(self, event):
        if event.Dragging() and event.LeftIsDown():
            maxY = self.GetTextMetrics()[1] * self._buffer.GetNumRows()

            pos = self.CalcUnscrolledPosition(event.GetPosition())
            pos = wx.Point(pos[0], max(1, pos[1]))

            # If we have moved the mouse past the end of the document
            # we should select the rest of the document
            if pos.y > maxY:
                index = len(str(self._buffer).rstrip()) - 1
            else:
                col, row = self.LogicalToBuffer(pos)
                index = self._buffer.CursorToIndex(col, row)

            if self._dragStart < index:
                self._buffer.SetSelectionStart(self._dragStart)
                self._buffer.SetSelectionEnd(index + 1)
            else:
                self._buffer.SetSelectionStart(index)
                self._buffer.SetSelectionEnd(self._dragStart + 1)

            self.Refresh()

    def _OnMouseUp(self, event):
        if self.HasCapture():
            self.ReleaseMouse()
