import re
from ..Base import Base


class sw65xx(Base):
    def execute(self):
        """ Written for Cisco 6509 sup 720 """

        self.prompt("Power on the device after clicking 'OK'.")

        self.wait('Autoboot executing command: "boot')
        self.send_break()
        self.ewait('rommon \\d{1,2} >')
        self.send('confreg 0x2142')
        self.ewait('rommon \\d{1,2} >')
        self.send('reset')

        out = self.ewait('|'.join(list(map(re.escape, [
            'initial configuration dialog? [yes/no]:',
            'Press RETURN to get started!'
        ]))))
