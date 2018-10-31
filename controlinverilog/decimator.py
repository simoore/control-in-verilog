import jinja2


class Decimator(object):

    def __init__(self, freq_in, top, dw):

        self.freq_out = freq_in / (top + 1)
        self.dw = dw

        context = {'TOP': top, 'DW': dw}

        loader = jinja2.PackageLoader('controlinverilog', 'templates')
        env = jinja2.Environment(loader=loader)
        template = env.get_template('decimator.v')
        self.verilog = template.render(context)

    def print_summary(self):

        print('Output sampling frequency (Hz): %g' % self.freq_out)
        print('Data word length: %d' % self.dw)

    def print_verilog(self, filename=None):

        if filename is None:
            print(self.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.verilog)
