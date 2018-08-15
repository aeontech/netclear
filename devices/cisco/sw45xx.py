import re
from ..Base import Base


class sw45xx(Base):
    def execute(self):
        """ Written for Cisco 4500-X """
        self.prompt("Power on the device after clicking 'OK'.")

        out = self.ewait('|'.join(list(map(re.escape, [
            'Type control-C to prevent autobooting.',
            'rommon'
        ]))))

        # Not all devices will autoboot, some go directly into rommon
        if not out.rfind('prevent autobooting') == -1:
            self.send_raw(self.CTRL_C)
            self.ewait('rommon \\d{1,2} >')

        self.configure_register()
        self.ewait('rommon \\d{1,2} >')
        self.send('set')
        out = self.ewait('rommon \\d{1,2} >')

        # Check for VS_SWITCH_NUMBER
        if not out.rfind('VS_SWITCH_NUMBER') == -1:
            self.send('unset VS_SWITCH_NUMBER')
            self.ewait('rommon \\d{1,2} >')

        self.send('reset')

        # Sent after the reset
        self.ewait('Resetting .......[\r\n]{1,2}rommon \\d{1,2} >|Signature v')

        # It *may* go back into rommon here
        print('wait...')
        out = self.ewait('|'.join([
            'Press RETURN to get started!',
            'rommon \\d{1,2} >'
        ]))
        print('found...')
        print('|'.join([
            'Press RETURN to get started!',
            'rommon \\d{1,2} >'
        ]))

        # It did go back into rommon - force a reboot
        if not out.rfind('rommon') == -1:
            self.send('boot')
            self.wait('Press RETURN to get started!')
        else:
            print('yep')

        self.send_raw('\r')
        out = self.ewait('Switch[#>]')

        if not out.rfind('Switch>') == -1:
            self.send('enable')
            out = self.ewait('Switch#|Password:')

        if not out.rfind('Password:') == -1:
            self.send_raw(self.ENTER)
            self.ewait('Switch#')

        self.send('write erase')
        self.wait('Continue? [confirm]')
        self.send_raw('y')
        self.wait('Switch#')
        self.send('erase cat4000_flash:')  # erase vlan.dat
        self.wait('Continue? [confirm]')
        self.send_raw('y')
        self.wait('Switch#')
        self.send('configure terminal')
        self.wait('Switch(config)#')
        self.send('no config-register')
        self.wait('Switch(config)#')

    def configure_register(self):
        self.send('confreg')
        self.ewait('change the configuration\\? y\\/n  \\[[yn]\\]:')
        self.send('y')
        self.ewait('"diagnostic mode"\\? y\\/n  \\[[yn]\\]:')
        self.send_raw(self.ENTER)
        self.ewait('"use net in IP bcast address"\\? y\\/n  \\[[yn]\\]:')
        self.send_raw(self.ENTER)
        self.ewait('"load rom after netboot fails"\\? y\\/n  \\[[yn]\\]:')
        self.send_raw(self.ENTER)
        self.ewait('"use all zero broadcast"\\? y\\/n  \\[[yn]\\]:')
        self.send_raw(self.ENTER)
        self.ewait('"break\\/abort has effect"\\? y\\/n  \\[[yn]\\]:')
        self.send_raw(self.ENTER)
        self.ewait('"ignore system config info"\\? y\\/n  \\[[yn]\\]:')
        self.send('y')
        self.ewait('change console baud rate\\? y\\/n  \\[[yn]\\]:')
        self.send_raw(self.ENTER)
        self.ewait('change the boot characteristics\\? y\\/n  \\[[yn]\\]:')
        self.send_raw(self.ENTER)
        self.ewait('save this configuration\\? y\\/n  \\[[yn]\\]:')
        self.send('y')
