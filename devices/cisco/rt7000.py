import re
from ..Base import Base


class rt7000(Base):
    def execute(self):
        """ Written for Cisco 7304 """
        self.prompt("Power on the device after clicking 'OK'.")

        self.wait('Initializing ATS monitor library')
        self.send_break()
        self.ewait('rommon \\d{1,2} >')
        self.send('confreg 0x2142')
        self.ewait('rommon \\d{1,2} >')
        self.send('reset')

        out = self.ewait('|'.join(list(map(re.escape, [
            'initial configuration dialog? [yes/no]:',
            'Press RETURN to get started!'
        ]))))

        if out.rfind('get started!') == -1:
            self.send('n')
            self.wait('Press RETURN to get started!')

        self.send_raw('\r\n')
        out = self.ewait('Router[>#]')

        if out.rfind('Router#') == -1:
            self.send('enable')
            self.wait('Router#')

        for cfg in ['startup', 'private', 'underlying']:
            self.send('delete nvram:/%s-config' % cfg)
            self.wait('Delete filename [%s-config]?' % cfg)
            self.send('')

            self.wait('Delete nvram:/%s-config? [confirm]')
            self.send('y')

            self.wait('Router#')

        self.send('config terminal')
        self.wait('Router(config)#')
        self.send('config-register 0x2102')
        self.wait('Router(config)#')
