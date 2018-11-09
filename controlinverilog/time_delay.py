import jinja2


class TimeDelay(object):

    def __init__(self, name, dw, aw):

        self.aw = aw
        self.dw = dw

        context = {'name': name, 'dw': dw, 'aw': aw}

        loader = jinja2.PackageLoader('controlinverilog', 'templates')
        env = jinja2.Environment(loader=loader)
        template = env.get_template('delay.v')
        self.verilog = template.render(context)

    def print_summary(self):

        print('Delay formula (taps): <delay> - 1')
        print('Delay formula (s): (<delay> - 1)/<fexe>')
        print('Max delay (s): %d/<fexe>' % (2 ** self.aw))
        print('Data word length: %d' % self.dw)

    def print_verilog(self, filename=None):

        if filename is None:
            print(self.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.verilog)
