import os
import wx
import sys

from .images import icon

class Prompt:
    _title = None
    _comms = None
    _devs = None

    _bauds = [
        '9600',
        # '19200',
        '38400',
        # '57600',
        '115200'
    ]

    settings = {
        'comms':  None,
        'baud':   None,
        'device': None
    }

    def __init__(self, title):
        self._title = title

    def setComms(self, communications):
        self._comms = communications

    def setDevices(self, devices):
        self._devs = devices

    def get(self, setting):
        return self.settings[setting]

    def display(self):
        if self._comms is None:
            raise RuntimeError("No comms ports provided!")

        if self._devs is None:
            raise RuntimeError("No devices provided!")

        app = wx.App()
        size = wx.Size(350, 330)
        style = wx.DEFAULT_FRAME_STYLE & ~(wx.MAXIMIZE_BOX | wx.RESIZE_BORDER)
        frame = _PromptFrame(None, title=self._title, size=size, style=style)
        panel = wx.Panel(frame)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        frame.SetIcon(icon.GetIcon())

        # Create widgets
        comms_label = wx.StaticText(panel, label="Port")
        bauds_label = wx.StaticText(panel, label="Baud Rate")

        comms = wx.Choice(panel, choices=self._comms, style=wx.EXPAND)
        bauds = wx.Choice(panel, choices=self._bauds, style=wx.EXPAND)
        comms.SetSelection(0)
        bauds.SetSelection(0)
        self.settings['comms'] = self._comms[0]
        self.settings['baud'] = self._bauds[0]

        tree = _TreeWidget(panel)
        tree.setData(self._devs)

        submit = wx.Button(panel, label="Let's Go!")
        cancel = wx.Button(panel, label="Quit")

        # Create sizers
        grid = wx.FlexGridSizer(2, 2, 2)
        grid.Add(comms_label, 0)
        grid.Add(bauds_label, 0)
        grid.Add(comms, 1, wx.EXPAND)
        grid.Add(bauds, 1, wx.EXPAND)

        btns = wx.FlexGridSizer(2, 1, 2)
        btns.Add(cancel, 1, wx.EXPAND)
        btns.Add(submit, 1, wx.EXPAND)

        sizer.Add(grid, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, 5)
        sizer.Add(tree, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btns, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.LEFT | wx.BOTTOM, 5)
        panelSizer.Add(panel, 1, wx.EXPAND)

        # Add sizers to frame
        panel.SetSizer(sizer)
        frame.SetSizer(panelSizer)
        frame.SetMinSize(wx.Size(300, 250))
        frame.Show()

        # Add bindings
        frame.Bind(wx.EVT_BUTTON, lambda e: frame.Close(False),  cancel)
        frame.Bind(wx.EVT_BUTTON, lambda e: self.onSubmit(app, frame), submit)
        frame.Bind(wx.EVT_CHOICE, self.onComms,  comms)
        frame.Bind(wx.EVT_CHOICE, self.onBauds,  bauds)
        frame.Bind(wx.EVT_TREE_SEL_CHANGED, lambda e: self.onTree(e, tree),
                   tree)

        app.MainLoop()

    def onSubmit(self, app, frame):
        if self.get('device') is None:
            dlg = wx.MessageDialog(frame, "No device was selected. Please "
                             "select a device.", style=wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        frame.Close(True)
        app.ExitMainLoop()

    def onComms(self, event):
        self.settings['comms'] = event.GetString()

    def onBauds(self, event):
        self.settings['baud'] = int(event.GetString())

    def onTree(self, event, tree):
        item = tree.GetSelection()
        self.settings['device'] = tree.GetItemData(item)


class _PromptFrame(wx.Frame):
    _ver = '0.1-alpha'

    def __init__(self, *args, **kwargs):
        super(__class__, self).__init__(*args, **kwargs)

        # Reset background
        self.SetBackgroundColour(wx.NullColour)

        # Create a menu bar
        self.CreateMenuBar()

        # Create a status bar
        self.CreateStatusBar()
        self.SetStatusText("Aeontech KillSwitch v%s" % self._ver)

    def CreateMenuBar(self):
        """
        This will create a menu with items for multiple functions.
        """

        file = wx.Menu()
        exitItem = file.Append(wx.ID_EXIT)

        help = wx.Menu()
        issueItem = help.Append(-1, "Report &Issue\tCtrl-I", "Report an issue")
        aboutItem = help.Append(wx.ID_ABOUT)

        # Make the menu bar add the menus to it
        bar = wx.MenuBar()
        bar.Append(file, "&File")
        bar.Append(help, "&Help")

        self.SetMenuBar(bar)

        self.Bind(wx.EVT_MENU, self.onClose, exitItem)
        self.Bind(wx.EVT_MENU, self.onIssue, issueItem)
        self.Bind(wx.EVT_MENU, self.onAbout, aboutItem)
        self.Bind(wx.EVT_CLOSE, self.onExit)

    def onClose(self, event):
        self.Close(False)

    def onExit(self, event):
        self.Destroy()

        # Veto had to be inverted... Thanks wxWindows
        event.SetCanVeto(not event.CanVeto())
        if not event.CanVeto():
            sys.exit()

    def onIssue(self, event):
        wx.MessageBox("Not yet implemented... Talk to Shane!",
                      "Report an Issue",
                      wx.OK | wx.ICON_INFORMATION)

    def onAbout(self, event):
        ver = self._ver

        wx.MessageBox("KillSwitch v%s\n\n"
                      "This program was created to aid in the secure "
                      "factory reset of networked devices, without prior "
                      "technical understanding of specific hardware." % ver,
                      "About KillSwitch v%s" % ver,
                      wx.OK | wx.ICON_INFORMATION)


class _TreeWidget(wx.TreeCtrl):
    def setData(self, data):
        root = self.AddRoot('Devices')
        lvl1 = {}

        for i in data:
            make, model = i.split(os.sep)

            if make not in lvl1:
                lvl1[make] = self.AppendItem(root, make)
                self.SetItemData(lvl1[make], '-')

            item = self.AppendItem(lvl1[make], model)
            self.SetItemData(item, "%s.%s" % (make, model))

        self.Expand(root)

        # Add bindings to ensure that the make can not be selected
        self.GetParent().Bind(wx.EVT_TREE_SEL_CHANGING, self.onChange, self)

    def onChange(self, event):
        item = event.GetItem()
        data = self.GetItemData(item)

        if data is '-' or data is None:
            event.Veto()
