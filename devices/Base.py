import wx
import re
import time
from threading import Thread
from bits.Terminal import TerminalCtrl

EVT_SERIAL_DATA = wx.NewId()


def EVT_SERIAL(win, func):
    win.Connect(-1, -1, EVT_SERIAL_DATA, func)


class SerialEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_SERIAL_DATA)
        self.data = data


class Base:
    _app = None
    _comms = None
    _wxObj = None
    _thread = None
    _terminal = None
    _lastbuffer = ''

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
        self._thread = Thread(target=self.do_execute)
        self._thread.start()
        self.setup()

    def execute(self):
        raise NotImplementedError()

    def do_execute(self):
        # We just block until we can execute
        while self._wxObj is None:
            time.sleep(0.1)

        self.execute()

        self.prompt("All done!")

    def setup(self):
        self.do_create_gui()

    def do_create_gui(self):
        classname = self.__class__.__name__

        app = wx.App.Get()
        size = wx.Size(700, 450)
        frame = wx.Frame(None, title="NetClear: %s" % classname, size=size)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._terminal = TerminalCtrl(frame)
        self._terminal.SetSpacing(0)
        self._terminal.SetWrap(True)

        frame.Bind(wx.EVT_CLOSE, lambda e: self.onClose(e, frame, app))
#        self._terminal.Bind(wx.EVT_CHAR, self.onChar, self._terminal)
        self._terminal.Bind(wx.EVT_KEY_DOWN, self.onKeyDown, self._terminal)

        EVT_SERIAL(frame, self.onSerialData)

        sizer.Add(self._terminal, 1, wx.EXPAND)
        frame.SetSizer(sizer)
        frame.SetMinSize(wx.Size(313, 260))
        frame.Show()

        self._wxObj = frame
        app.MainLoop()

    def onClose(self, event, frame, app):
        if self._thread.isAlive():
            self._thread._Thread_stop()

        frame.Destroy()
        app.ExitMainLoop()

    def onSerialData(self, event):
        self._terminal.AddChars(event.data)

    def onKeyDown(self, event):
        # if 27 < event.GetKeyCode() < 256 and not event.HasAnyModifiers():
        #     event.Skip()
        #     return

        key = self._GetKeyPress(event)

        switcher = {
            'Ctrl+B': lambda: self.send_break(),
            'Ctrl+O': lambda: print(self._terminal.GetValue()),
            'RETURN': lambda: self.send_raw(self.ENTER),
        }

        if key in switcher:
            switcher.get(key)()

    def onChar(self, event):
        code = event.GetKeyCode()

        if not 27 < code < 256:
            print('CHAR could not be processed for %d' % code)
            return

        print("CHAR:%d" % code)

    def _GetKeyPress(self, event):
        keycode = event.GetKeyCode()
        keyname = self.map.get(keycode, None)
        modifiers = ""

        for mod, ch in ((event.ControlDown(), 'Ctrl+'),
                        (event.AltDown(),     'Alt+'),
                        (event.ShiftDown(),   'Shift+'),
                        (event.MetaDown(),    'Meta+')):
            if mod:
                modifiers += ch

        if keyname is None:
            if 27 < keycode < 256:
                keyname = chr(keycode)
            else:
                keyname = "(%s)unknown" % keycode

        return modifiers + keyname

    def _handle_key(self, event):
        char = event.GetKeyCode()

        if not 27 < char < 256:
            return

        char = chr(char)
        char = char.upper() if event.ShiftDown() else char.lower()

        self.send_raw(char)

    def prompt(self, message, caption="netclear"):
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
