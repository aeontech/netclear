import wx
from ..Base import Base


class asa55xx(Base):
    def run(self):
        self.setup()

        self.prompt("Power on the device then click 'OK'.")

        self.serial.send_break()
        self.serial.wait('rommon 1 >')
        self.serial.send('confreg')
        self.serial.wait('')
