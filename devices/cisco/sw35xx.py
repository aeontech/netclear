import re
from ..Base import Base


class sw35xx(Base):
    def execute(self):
        """ Written for Cisco 3560 """

        self.prompt("After clicking OK, hold the MODE button and power on the "
                    "device. After a brief period, the indicator light on the "
                    "front of the device will stop flashing, only then may you"
                    " release the MODE button.")

        self.wait('switch: ')
        self.send('set')
        while 1:
            out = self.ewait('|'.join(list(map(re.escape, [
                'switch: ',
                '-- MORE --'
            ]))))

            if out.rfind('-- MORE --') == -1:
                break

            if out.rfind('SWITCH_NUMBER=') <> -1:
                self.send('unset SWITCH_NUMBER')
                break

        self.send('flash_init')
        while 1:
            out = self.ewait('|'.join(list(map(re.escape, [
                'switch: ',
                '-- MORE --'
            ]))))

            if out.rfind('-- MORE --') == -1:
                break

            self.send_raw(' ')

        self.send('del flash:/config.text')
        self.wait('delete "flash:/config.text" (y/n)?')
        self.send("y")
        out = self.ewait('|'.join(list(map(re.escape, [
            'File "flash:/config.text" deleted',
            'File "flash:/config.text" not deleted'
        ]))))

        if out.rfind('switch:') == -1:
            self.wait('switch:')

        self.send('del flash:/vlan.dat')
        self.wait('delete "flash:/vlan.dat" (y/n)?')
        self.send("y")
        out = self.ewait('|'.join(list(map(re.escape, [
            'File "flash:/vlan.dat" deleted',
            'File "flash:/vlan.dat" not deleted'
        ]))))

        if out.rfind('switch:') == -1:
            self.wait('switch:')
