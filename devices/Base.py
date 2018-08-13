import wx
import os  # We don't really need this
import sys
from bits.Terminal import TerminalCtrl


class Base:
    _comms = None

    CTRL_C = '\x03'

    def __init__(self):
        pass

    def getCommsPort(self):
        return self._comms

    def setCommsPort(self, communications):
        self._comms = communications

    def run(self):
        raise NotImplementedError()

    def setup(self):
        classname = self.__class__.__name__

        app = wx.App()
        size = wx.Size(700, 450)
        frame = wx.Frame(None, title="NetClear: %s" % classname, size=size)
        sizer = wx.BoxSizer(wx.VERTICAL)

        cmd = TerminalCtrl(frame)
        cmd.SetSpacing(0)
        cmd.SetWrap(True)

        cmd.AddChars('A abcdefghijklmnopqrstuvwxyz  abcdefghijklmnopqrstuvwxyz'
                     '  abcdefghijklmnopqrstuvwxyz  abcdefghijklmnopqrstuvwxyz'
                     '  abcdefghijklmnopqrstuvwxyz  abcdefghijklmnopqrstuvwxyz'
                     + os.linesep)
        cmd.AddChars('B 12345678901234567890123456' + os.linesep)

        frame.Bind(wx.EVT_CLOSE, lambda e: frame.Destroy() and sys.exit())

        sizer.Add(cmd, 1, wx.EXPAND)
        frame.SetSizer(sizer)
        frame.SetMinSize(wx.Size(313, 260))
        frame.Show()

        app.MainLoop()

    def myprompt(self, msg, cap="netclear"):
        styl = wx.OK | wx.OK_DEFAULT | wx.STAY_ON_TOP | wx.ICON_HAND
        wx.MessageDialog(message=msg, caption=cap, style=styl)
