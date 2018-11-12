import re
from ..Base import Base


class sw65xx(Base):
    def execute(self):
        """ Written for Cisco 6500 sup 720 """

        self.prompt("Power on the device after clicking 'OK'.")

        # It may boot in Switch Processor mode... Prepare!
        # We will ignore it for now...

        # We are in Route Processor mode
        self.ewait('Cat6k-Sup\d+ platform with')
        self.send_break()

        self.ewait('rommon \\d{1,2} >')
        self.send('confreg 0x2142')
        self.ewait('rommon \\d{1,2} >')
        self.send('reset')

        out = self.ewait('|'.join(list(map(re.escape, [
            'initial configuration dialog? [yes/no]:',
            'Press RETURN to get started!'
        ]))))

        if not out.rfind('[yes/no]') == -1:
            self.send_raw('n')
            self.wait('Press RETURN to get started!')

        self.send_raw('\r')
        out = self.ewait('Router[#>]')

        if not out.rfind('Router>') == -1:
            self.send('enable')
            out = self.ewait('Router#|Password:')

        if not out.rfind('Password:') == -1:
            self.send_raw(self.ENTER)
            self.ewait('Router#')

        self.send('write erase')
        self.wait('Continue? [confirm]')
        self.send_raw('y')

        self.wait('Router#')
        self.send('delete const_nvram:/vlan.dat')  # erase vlan.dat
        out = self.ewait('|'.join(list(map(re.escape, [
            'Delete filename [vlan.dat]? ',
            'Delete const_nvram:/vlan.dat? [confirm]'
        ]))))

        if not out.rfind('[vlan.dat]?') == -1:
            self.send_raw('\r')
            self.wait('Delete const_nvram:/vlan.dat? [confirm]')

        self.send_raw('y')
        self.wait('Router#')

        self.send('configure terminal')
        self.wait('Router(config)#')
        self.send('config-register 0x2102')
        self.wait('Router(config)#')
