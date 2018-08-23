import wx
import re
import time
from threading import Lock
from threading import Thread
from bits.images import icon
from bits.Terminal import TerminalCtrl

EVT_SERIAL_DATA = wx.NewId()


def EVT_SERIAL(win, func):
    win.Connect(-1, -1, EVT_SERIAL_DATA, func)


class SerialEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_SERIAL_DATA)
        self.data = data


class _HotkeyDialog(wx.Dialog):
    def __init__(self, parent, id=wx.ID_ANY, title="Program Shortcuts",
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE, name=wx.DialogNameStr):
        super().__init__(parent, id, title, pos, size, style, name)
        paddingH = wx.BoxSizer(wx.HORIZONTAL)
        paddingL = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.VERTICAL)

        frame.SetIcon(icon.GetIcon())

        # Just to prove I can be nasty too...
        def add(ctrl):
            box.Add(ctrl, wx.EXPAND)

        def text(text):
            return wx.StaticText(self, label=text)

        add(text("The following shortkeys are defined"))
        add(text("for use in this program:"))
        add(text(""))
        add(text("CTRL-C: Copy"))
        add(text("CTRL-V: Paste"))
        add(text("CTRL-B: Break"))

        paddingL.Add(box, 1, wx.TOP | wx.BOTTOM, 10)
        paddingH.Add(paddingL, 1, wx.LEFT | wx.RIGHT, 20)
        self.SetSizer(paddingH)
        self.Centre()


class Base:
    _app = None
    _comms = None
    _wxObj = None
    _tLock = None
    _thread = None
    _terminal = None
    _lastbuffer = ''

    _closing = False

    CTRL_C = '\x03'
    ESC = '\x1B'
    ENTER = '\n'

    # Key map
    map = {}

    def __init__(self):
        keys = (
            "BACK", "TAB", "RETURN", "ESCAPE", "SPACE", "DELETE", "START",
            "LBUTTON", "RBUTTON", "CANCEL", "MBUTTON", "CLEAR", "PAUSE",
            "CAPITAL", 0, 0, "END", "HOME", "LEFT", "UP", "RIGHT", "DOWN",
            "SELECT", "PRINT", "EXECUTE", "SNAPSHOT", "INSERT", "HELP",
            "NUMPAD0", "NUMPAD1", "NUMPAD2", "NUMPAD3", "NUMPAD4", "NUMPAD5",
            "NUMPAD6", "NUMPAD7", "NUMPAD8", "NUMPAD9", "MULTIPLY", "ADD",
            "SEPARATOR", "SUBTRACT", "DECIMAL", "DIVIDE", "F1", "F2", "F3",
            "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13",
            "F14", "F15", "F16", "F17", "F18", "F19", "F20", "F21", "F22",
            "F23", "F24", "NUMLOCK", "SCROLL", "PAGEUP", "PAGEDOWN",
            "NUMPAD_SPACE", "NUMPAD_TAB", "NUMPAD_ENTER", "NUMPAD_F1",
            "NUMPAD_F2", "NUMPAD_F3", "NUMPAD_F4", "NUMPAD_HOME",
            "NUMPAD_LEFT", "NUMPAD_UP", "NUMPAD_RIGHT", "NUMPAD_DOWN",
            0, "NUMPAD_PAGEUP", 0, "NUMPAD_PAGEDOWN", "NUMPAD_END",
            "NUMPAD_BEGIN", "NUMPAD_INSERT", "NUMPAD_DELETE", "NUMPAD_EQUAL",
            "NUMPAD_MULTIPLY", "NUMPAD_ADD", "NUMPAD_SEPARATOR",
            "NUMPAD_SUBTRACT", "NUMPAD_DECIMAL", "NUMPAD_DIVIDE"
        )

        for i in keys:
            if i is 0:
                continue

            self.map[getattr(wx, "WXK_" + i)] = i

        for i in ("SHIFT", "ALT", "CONTROL", "MENU"):
            self.map[getattr(wx, "WXK_" + i)] = ''

    def getCommsPort(self):
        return self._comms

    def setCommsPort(self, communications):
        self._comms = communications

    def run(self):
        self._tLock = Lock()
        self._thread = Thread(target=self.do_execute)
        self._thread.start()
        self.setup()

    def execute(self):
        raise NotImplementedError()

    def do_execute(self):
        self._tLock.acquire()
        self.execute()
        self.prompt("All done!")

    def setup(self):
        self.do_create_gui()

    def do_create_gui(self):
        classname = self.__class__.__name__

        app = wx.App.Get()
        AppTitle = "%s: %s" % (self._comms.port, classname)
        size = wx.Size(700, 450)
        frame = wx.Frame(None, title=AppTitle, size=size)
        panel = wx.Panel(frame)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Configure Menu
        fileMenu = wx.Menu()
        copyitem = fileMenu.Append(wx.ID_COPY, "&Copy\tCtrl-C")
        pasteitem = fileMenu.Append(wx.ID_PASTE, "&Paste\tCtrl-V")
        fileMenu.AppendSeparator()
        brkitem = fileMenu.Append(wx.ID_ANY, "&Break\tCtrl-B")
        fileMenu.AppendSeparator()
        quititem = fileMenu.Append(wx.ID_EXIT, "&Quit")

        helpMenu = wx.Menu()
        hotkeyitem = helpMenu.Append(wx.ID_ANY, "Program &Shortcuts")

        menubar = wx.MenuBar()
        menubar.Append(fileMenu, '&File')
        menubar.Append(helpMenu, '&Help')
        frame.SetMenuBar(menubar)

        self._terminal = TerminalCtrl(panel)
        self._terminal.SetSpacing(0)
        self._terminal.SetWrap(True)

        sizer.Add(self._terminal, 1, wx.EXPAND)
        panelSizer.Add(panel, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        frame.SetSizer(panelSizer)
        frame.SetMinSize(wx.Size(313, 260))
        frame.Show()

        # Set up accelerators
        accelC = wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)
        accelV = wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('V'), wx.ID_PASTE)
        accelB = wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('B'), brkitem.GetId())
        accel = wx.AcceleratorTable([accelC, accelV, accelB])
        frame.SetAcceleratorTable(accel)

        # Bind on window events
        frame.Bind(wx.EVT_CLOSE, self.onClose)
        self._terminal.Bind(wx.EVT_CHAR, self.onChar, self._terminal)

        # Bind Menu handlers
        frame.Bind(wx.EVT_MENU, self.onClose, quititem)
        frame.Bind(wx.EVT_MENU, self.showHotkeys, hotkeyitem)
        frame.Bind(wx.EVT_MENU, lambda e: self.onCopy(), copyitem)
        frame.Bind(wx.EVT_MENU, lambda e: self.onPaste(), pasteitem)
        frame.Bind(wx.EVT_MENU, lambda e: self.send_break(), brkitem)

        # Register for events from Serial Communications thread
        EVT_SERIAL(frame, self.onSerialData)

        # Ensure the terminal has focus
        self._terminal.SetFocus()

        self._wxObj = frame
        self._tLock.release()
        app.MainLoop()

    def showHotkeys(self, event):
        dlg = _HotkeyDialog(self._wxObj)
        dlg.ShowModal()

    def onClose(self, event):
        self._closing = True
        self._thread.join()
        self._wxObj.Destroy()
        wx.App.Get().ExitMainLoop()

    def onSerialData(self, event):
        self._terminal.AddChars(event.data)

    def onChar(self, event):
        code = event.GetUnicodeKey()

        if code == wx.WXK_NONE:
            code = event.GetKeyCode()

        if (not 27 < code < 256) or event.HasAnyModifiers():
            # So we don't consume the event
            event.Skip()
            return

        print("CHAR:%d" % code)

    def onCopy(self):
        if not wx.TheClipboard.Open():
            return

        selected = self._terminal.GetSelected()
        wx.TheClipboard.SetData(wx.TextDataObject(selected))
        wx.TheClipboard.Close()

    def onPaste(self):
        if not wx.TheClipboard.Open():
            return

        text = wx.TextDataObject()
        success = wx.TheClipboard.GetData(text)

        wx.TheClipboard.Close()

        if not success:
            return

        self.send_raw(text.GetText())

    def prompt(self, message, caption="KillSwitch Notification"):
        style = wx.OK | wx.OK_DEFAULT | wx.STAY_ON_TOP | wx.ICON_INFORMATION

        dialog = wx.MessageDialog(None, message, caption, style)
        dialog.ShowModal()
        dialog.Destroy()

    # Serial communications
    def send_break(self):
        return self._comms.send_break(0.4)

    def send(self, message):
        return self.send_raw(message + self.ENTER)

    def send_raw(self, message):
        message = message.encode('utf-8')
        return self._comms.write(message)

    def wait(self, message):
        buffer = ''
        bufflen = 0

        while True:
            if self._closing:
                raise SystemExit()

            data = self._comms.read(1024).decode()
            datalen = len(data)

            if datalen > 0:
                buffer += data
                bufflen += datalen

                # update buffer
                wx.PostEvent(self._wxObj, SerialEvent(data))

                pos = (self._lastbuffer + buffer).rfind(message)
                if (pos is not -1):
                    self._lastbuffer = buffer[pos+len(message):]
                    break

        return buffer

    def ewait(self, expression):
        buffer = ''
        bufflen = 0

        expr = re.compile(expression)

        while True:
            if self._closing:
                raise SystemExit()

            data = self._comms.read(1024).decode()
            datalen = len(data)

            if datalen > 0:
                buffer += data
                bufflen += datalen

                # update buffer
                wx.PostEvent(self._wxObj, SerialEvent(data))

                search = expr.search(self._lastbuffer + buffer)
                if (search is not None):
                    self._lastbuffer = buffer[search.span()[1]:]
                    break

        return buffer
