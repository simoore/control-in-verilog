import jinja2


class Saturation(object):

    def __init__(self,
                 name,
                 input_word_length=22,
                 input_frac_length=10,
                 output_word_length=16):

        context = {'name': name,
                   'iw': input_word_length,
                   'ow': output_word_length}

        self.cache = {'in_lo': -(2 ** (input_word_length - input_frac_length - 1)),
                      'in_hi': 2 ** (input_word_length - input_frac_length - 1) - 2 ** (-input_frac_length),
                      'out_lo': -(2 ** (output_word_length - input_frac_length - 1)),
                      'out_hi': 2 ** (output_word_length - input_frac_length - 1) - 2 ** (-input_frac_length),
                      'name': name}

        loader = jinja2.PackageLoader('controlinverilog', 'templates')
        env = jinja2.Environment(loader=loader)
        template = env.get_template('saturation.v')
        self.verilog = template.render(context)

    def print_summary(self):

        print('--- Saturation Module: %s ---' % self.cache['name'])
        print('Input Range: [%f, %f]' % (self.cache['in_lo'], self.cache['in_hi']))
        print('Output Range: [%f, %f]' % (self.cache['out_lo'], self.cache['out_hi']))

    def print_verilog(self, filename=None):

        if filename is None:
            print(self.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.verilog)
