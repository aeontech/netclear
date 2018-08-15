import re
import time
from ..Base import Base


class asa55xx(Base):
    def execute(self):
        """ Written for Cisco 5550 """
        self.prompt("Power on the device after clicking 'OK'.")

        self.wait('Use BREAK or ESC to interrupt boot.')

        # Let's send 3 breaks - just in case!
        for i in range(1, 3):
            self.send_break()

        self.ewait('rommon #\\d{1,2}>')
        self.send('confreg 0x41')
        self.ewait('rommon #\\d{1,2}>')
        self.send('boot')

        out = self.ewait('|'.join(list(map(re.escape, [
            "Type help or '?' for a list of available commands.",
            "Pre-configure Firewall now through interactive prompts [yes]?"
        ]))))

        if not out.rfind('Pre-configure Firewall') == -1:
            self.send('n')
            out = self.wait("Type help or '?' for a list of available commands.")

        # It could have been captured by the previous wait
        if out.rfind('ciscoasa') == -1:
            out = self.ewait('^ciscoasa[>#])$')

        # We probably aren't enabled
        if out.rfind('ciscoasa>'):
            self.send('en')
            self.wait('Password:')
            self.send_raw(self.ENTER)
            self.wait('ciscoasa#')

        self.send('write erase')
        out = self.wait('[confirm]')

        if out.rfind('[OK]') == -1:
            self.send_raw('y')
            out = self.wait('[OK]')

        if out.rfind('ciscoasa#') == -1:
            self.wait('ciscoasa#')

        self.send('configure terminal')
        out = self.ewait('|'.join(list(map(re.escape, [
            "Help to improve",
            'ciscoasa(config)# $'
        ]))))

        if not out.rfind('Help to improve the ASA platform') == -1:
            if out.rfind('[Y]es, [N]o, [A]sk later:') == -1:
                self.wait('[Y]es, [N]o, [A]sk later:')

            self.send('n')
            self.wait('ciscoasa(config)#')

        self.send('no config-register')
        self.wait('ciscoasa(config)#')
        time.sleep(1)
