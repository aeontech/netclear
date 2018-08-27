from ..Base import Base


def u(str):
    print(str, end='')


class Force10(Base):
    def execute(self):
        """ Written for Dell Force10 """
        self.prompt("Power on the device after clicking 'OK'.")

        u(self.wait('Hit Esc key to interrupt autoboot:'))
        self.send_raw(self.ESC)
        u(self.wait('=>'))
        self.send('setenv stconfigignore true')
        u(self.wait('=>'))
        self.send('saveenv')
        u(self.wait('=>'))
        self.send('reset')

        u(self.wait('Starting Dell Networking OS'))
        u(self.ewait('Dell(?:-[a-zA-Z0-9]+)?>'))
        self.send('enable')
        u(self.ewait('Dell(?:-[a-zA-Z0-9]+)?#'))
        self.send('restore factory-defaults stack-unit all clear-all')
        u(self.wait('Confirm [yes/no]:'))
        self.send('yes')
        u(self.wait('Power-cycling'))
