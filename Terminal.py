import os
import wx
import math


def profile(fnc):
    import cProfile
    import pstats
    import io

    def inner(*args, **kwargs):
        pr = cProfile.Profile()

        pr.enable()
        retval = fnc(*args, **kwargs)
        pr.disable()

        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())

        return retval
    return inner


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


class _TextBuffer:
    _contents = None
    _lines = None
    _selection = _TextSelection()

    def __init__(self, contents=''):
        self._contents = contents
        self._lines = contents.split(os.linesep)

    def __str__(self):
        return self._contents

    def __getitem__(self, key):
        return self._contents[key]

    def __setitem__(self, key, value):
        self._contents[key] = value
        self._lines = self._contents.split(os.linesep)

    def __delitem__(self, key):
        del self._contents[key]
        self._lines = self._contents.split(os.linesep)

    def __contains__(self, item):
        return item in self._contents

    def __len__(self):
        return len(self._contents)

    def __add__(self, value):
        buff = self()
        buff._contents = self._contents + value
        buff._lines = buff._contents.split(os.linesep)
        buff._selection = self._selection

        return buff

    def __radd__(self, value):
        buff = self()
        buff._contents = value + self._contents
        buff._lines = buff._contents.split(os.linesep)
        buff._selection = self._selection

        return buff

    def __iadd__(self, value):
        self._contents += value
        self._lines = self._contents.split(os.linesep)
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
        return False

    def SetWrap(self, wrap):
        raise RuntimeError('Can\'t set wrapping for the text buffer!')

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

    def CursorToIndex(self, col, row):
        index = 0
        lineSepLen = len(os.linesep)

        for lineNo in range(len(self._lines)):
            length = len(self._lines[lineNo])

            if not lineNo == row:
                index += length + lineSepLen
                continue

            index += min(col, length)
            break

        return index

    def IndexToCursor(self, index):
        parts = self._contents[0:index].split(os.linesep)

        row = len(parts)
        col = len(parts[-1])

        return (col, row)


class _BufferLayout(_TextBuffer):
    _wrap = False
    _limit = 80

    def __init__(self, contents=''):
        super().__init__(contents)
        self._processLines()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._processLines()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._processLines()

    def __contains__(self, item):
        return item in self._contents

    def __add__(self, value):
        buff = super().__add__(value)
        buff._processLines()

        return buff

    def __radd__(self, value):
        buff = super().__radd__(value)
        buff._processLines()

        return buff

    def __iadd__(self, value):
        super().__iadd__(value)
        self._processLines()

        return self

    def _processLines(self):
        if not self.GetWrap():
            return

        limit = self.GetLimit()
        self._lines = []

        for line in self._contents.split(os.linesep):
            lineLen = len(line)

            for i in range(math.ceil(lineLen/limit)):
                start = i * limit
                end = min((i + 1) * limit, lineLen)

                self._lines.append(line[start:end])

    def GetWrap(self):
        return self._wrap

    def SetWrap(self, wrap):
        self._wrap = wrap

    def GetLimit(self):
        return self._limit

    def SetLimit(self, limit):
        self._limit = limit
        self._processLines()

    def IndexToCursor(self, index):
        if not self.GetWrap():
            return super().IndexToCursor(index)

        row = 0
        limit = self.GetLimit()
        parts = self._contents[0:index].split(os.linesep)

        for line in parts:
            row += math.ceil(len(line) / limit)

        col = len(parts[-1]) % limit

        if col is 0:
            row += 1

        return (col, row)


class TerminalCtrl(wx.Control):
    _buffer = None
    _canvas = None
    _metrics = None
    _lineSpacing = 0

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, validator=wx.DefaultValidator,
                 name=wx.ControlNameStr):

        # Disallow borders
        style &= ~(wx.BORDER_DEFAULT | wx.BORDER_SIMPLE | wx.BORDER_SUNKEN) & \
                 ~(wx.BORDER_RAISED | wx.BORDER_STATIC | wx.BORDER_THEME)

        style |= wx.BORDER_NONE

        super().__init__(parent, id, pos, size, style, validator, name)

        super().SetFont(wx.Font(pointSize=13, family=wx.FONTFAMILY_TELETYPE,
                        style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_LIGHT))

        # Set initial buffer
        self._buffer = _BufferLayout()
        self._buffer.SetSelectionStart(100)
        self._buffer.SetSelectionEnd(206)

        # Set canvas
        size = wx.Size(5, 5)
        canvas_style = wx.BORDER_NONE | wx.NO_FULL_REPAINT_ON_RESIZE
        self._canvas = wx.ScrolledCanvas(self, style=canvas_style, size=size)

        # Set initial colouring
        back = self.GetBackgroundColour()
        self.SetBackgroundColour(self.GetForegroundColour())
        self.SetForegroundColour(back)

        # Set up scrolling
        self._canvas.EnableScrolling(True, True)

        self.Bind(wx.EVT_PAINT, self._OnPaint)
        self.Bind(wx.EVT_SIZE,  self._OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self._OnEraseBackground)

        self._canvas.Bind(wx.EVT_LEFT_DOWN, self._OnMouseDown)
        self._canvas.Bind(wx.EVT_MOTION, self._OnMouseMove)

        self._OnSize(None)

    def AddChars(self, chars):
        self._buffer += chars

        # Now we must recalculate
        self.InvalidateBestSize()
        self.Refresh()

    def SetFont(self, font):
        self.SetFont(font)

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

    def DoGetBestClientSize(self):
        dc = wx.ScreenDC()
        dc.SetFont(self.GetFont())

        textWidth, textHeight = self.GetTextMetrics()
        spacing = self.GetSpacing()

        buflen = self._buffer.GetNumLines()
        height = (textHeight + spacing) * buflen
        width = 0
        scrollbarWidth = wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y)

        if self.GetWrap():
            width, _ = self.GetParent().ClientSize
            width = math.floor((width - scrollbarWidth) / textWidth)
        else:
            for line in self._buffer:
                width = max(width, len(line))

        # Refresh scrollbar size
        if self.GetWrap():
            self._canvas.ShowScrollbars(False, True)
        else:
            self._canvas.ShowScrollbars(True, True)

        self._canvas.SetScrollbars(textWidth, textHeight + spacing,
                                   width, buflen, 0)

        width = (width * textWidth)  # - scrollbarWidth
        return wx.Size(width, height)

    def InvalidateMetrics(self):
        self._metrics = None

    # As per wx.TextEntry
    def GetValue(self):
        return self._buffer

    def LogicalToBuffer(self, point):
        textWidth, textHeight = self.GetTextMetrics()
        spacing = self.GetSpacing()

        row = math.ceil(point.y / (textHeight + spacing))
        col = math.floor(point.x / textWidth)

        return (col, row)

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

    def _Draw(self, dc):
        backColor = self.GetBackgroundColour()
        backBrush = wx.Brush(backColor, wx.SOLID)
        dc.SetBackground(backBrush)
        dc.Clear()

        foreColor = self.GetForegroundColour()
        dc.SetTextForeground(foreColor)
        dc.SetFont(self.GetFont())

        highBackColor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        highBackBrush = wx.Brush(highBackColor, wx.SOLID)
        highForeColor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)

        textWidth, textHeight = self.GetTextMetrics()
        selection = self._buffer.GetSelection()
        sS = selection.GetStart()
        sE = selection.GetEnd()

        lineNo = 0
        for line in self._buffer:
            lineNo += 1
            start = self._buffer.CursorToIndex(lineNo, 0)
            # end = start + len(line)
            end = self._buffer.CursorToIndex(lineNo+1, 0)
            _, y = self.BufferToLogical(0, lineNo)

            if selection.IsSelected():
                if sS >= start and sS < end:  # Selection starts on this line
                    dc.SetBackground(highBackBrush)
                    dc.SetTextForeground(highForeColor)

                if sE >= start and sE < end:  # Selection ends on this line
                    pass
                    # dc.SetBackground(backBrush)
                    # dc.SetTextForeground(foreColor)

            dc.DrawText(line, 0, y)

#        highlight = False
#        list = []
#        coords = []
#
#        for char in range(len(self._buffer)):
#            col, row = self._buffer.IndexToCursor(char)
#
#            if highlight is not self._buffer.GetSelection().IsSelected(char):
#                # Flush list
#                dc.DrawTextList(list, coords, foreColor, backColor)
#
#                highlight = self._buffer.GetSelection().IsSelected(char)
#                tempColor = backColor
#                backColor = foreColor
#                backBrush = wx.Brush(backColor, wx.SOLID)
#                foreColor = tempColor
#
#            list.append(self._buffer[char])
#            coords.append(self.BufferToLogical(col, row))
#
#        dc.DrawTextList(list, coords, foreColor, backColor)

    def _OnPaint(self, event):
        dc = wx.BufferedPaintDC(self._canvas)
        self._canvas.PrepareDC(dc)
        self._Draw(dc)

    def _OnSize(self, event):
        textWidth, textHeight = self.GetTextMetrics()
        fullWinWidth, fullWinHeight = self.ClientSize
        self._canvas.SetSize(wx.Size(fullWinWidth, fullWinHeight))

        wW = fullWinWidth - wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y)

        if not self.GetWrap():
            return

        self._buffer.SetLimit(math.floor(wW / textWidth))

        if self.GetWrap():
            self.InvalidateBestSize()

    def _OnEraseBackground(self, event):
        # This is intentionally blank
        pass

    def _OnMouseDown(self, event):
        pos = event.GetPosition()
        x, y = self.LogicalToBuffer(pos)
        index = self._buffer.CursorToIndex(x, y)

        self._buffer.SetSelectionStart(index)

    def _OnMouseMove(self, event):
        if event.Dragging() and event.LeftIsDown():
            pos = event.GetPosition()
            x, y = self.LogicalToBuffer(pos)
            index = self._buffer.CursorToIndex(x, y)

            self._buffer.SetSelectionEnd(index)

            self.Refresh()
