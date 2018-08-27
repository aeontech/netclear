import wx
import math
from wx.lib.scrolledpanel import ScrolledPanel

from .Selection import Selection
from .Buffer import Text as Buffer


class Terminal(ScrolledPanel):
    _buffer = None
    _metrics = None
    _lineSpacing = 0
    _overlay = None

    _scrollPos = None
    _scrollbarFollowText = True

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, name=wx.ControlNameStr):

        # Disallow borders
        style &= ~(wx.BORDER_DEFAULT | wx.BORDER_SIMPLE | wx.BORDER_SUNKEN) & \
                 ~(wx.BORDER_RAISED | wx.BORDER_STATIC | wx.BORDER_THEME)

        # Disallow TAB_TRAVERSAL
        style &= ~wx.TAB_TRAVERSAL

        style |= wx.BORDER_NONE
        style |= wx.WANTS_CHARS

        # Set initial buffer - This must be performed before calling __init__
        # on the parent class
        self._buffer = Buffer()

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

            # +1 to convert to 1-based
            rowAtTop = buflen - visRows + 1
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
        col = min(max(0, lineLen - 1), col)

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
            if (len(line) == 0 or line[-1] == '\r' or line[-1] == '\n') and \
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
        self.DoPrepareDC(dc)
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
        if (numRows - currScroll[1] - numVisibleRows - 1) <= 0:
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

        maxSel = len(str(self._buffer).rstrip())
        maxY = self.GetTextMetrics()[1] * self._buffer.GetNumRows()

        pos = self.CalcUnscrolledPosition(event.GetPosition())
        pos = wx.Point(pos[0], max(1, pos[1]))

        # If we have moved the mouse past the end of the document
        # we should select the rest of the document
        if pos.y > maxY:
            index = maxSel - 1
        else:
            col, row = self.LogicalToBuffer(pos)
            index = self._buffer.CursorToIndex(col, row)
            index = min(maxSel, index)

        self._buffer._selection.SetStart(0)
        self._buffer._selection.SetEnd(0)

        self._dragStart = max(0, index)

        self.Refresh()

    def _OnMouseMove(self, event):
        if event.Dragging() and event.LeftIsDown():
            maxSel = len(str(self._buffer).rstrip())
            maxY = self.GetTextMetrics()[1] * self._buffer.GetNumRows()

            pos = self.CalcUnscrolledPosition(event.GetPosition())
            pos = wx.Point(pos[0], max(1, pos[1]))

            # If we have moved the mouse past the end of the document
            # we should select the rest of the document
            if pos.y > maxY:
                index = maxSel
            else:
                col, row = self.LogicalToBuffer(pos)
                col = max(0, col)
                row = min(row, self._buffer.GetNumRows())
                index = self._buffer.CursorToIndex(col, row)

            index = max(0, index)

            if self._dragStart < index:
                # Drag forwards
                self._buffer.SetSelectionStart(self._dragStart)
                self._buffer.SetSelectionEnd(min(maxSel, index + 1))
            else:
                # Drag backwards
                self._buffer.SetSelectionStart(index)
                self._buffer.SetSelectionEnd(min(maxSel, self._dragStart + 1))

            self.Refresh()

    def _OnMouseUp(self, event):
        if self.HasCapture():
            self.ReleaseMouse()
