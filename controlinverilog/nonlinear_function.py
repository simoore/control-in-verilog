import jinja2
from math import ceil, log
import numpy as np


class NonlinearFunction(object):

    def __init__(self, name, func, input_word_length, input_frac_length):
        """
        Parameters
        ----------
        name : string
            The name of the verilog module.
        func : function: ndarray -> ndarray
            The function to be implemented in a lookup table in verilog. This parameter is function pointer. Its only
            input is an ndarray and it must return an ndarray of the same length.
        input_word_length : int
            The input word length. This value along with the fraction word length parameter sets the input domain of
            the function.
        input_frac_length : int
            The input fractional length.
        """
        self.func = func
        self.iw = input_word_length
        self.if_ = input_frac_length
        self.name = name
        self._set_parameters()

        context = {
            'NAME': self.name,
            'IW': self.iw,
            'OW': self.ow,
            'N_RAM': self.n_ram,
            'RAM': self.ram
        }
        loader = jinja2.PackageLoader('controlinverilog', 'templates')
        env = jinja2.Environment(loader=loader)
        template = env.get_template('nonlinear_function.v')
        self.verilog = template.render(context)

    def _set_parameters(self):
        xfix = np.arange(2 ** self.iw)
        xtwo = np.where(xfix >= 2 ** (self.iw - 1), xfix - 2 ** self.iw, xfix)
        x = 2 ** -self.if_ * xtwo
        y = self.func(x)
        self.xmax = np.amax(x)
        self.xmin = np.amin(x)
        self.ymax = np.amax(y)
        self.ymin = np.amin(y)
        ynorm = max((abs(self.ymax), abs(self.ymin)))
        self.of = self.if_
        self.ow = ceil(log(ynorm, 2)) + self.of + 1
        self.ram = np.around(2 ** self.of * y).astype(int)
        self.n_ram = len(self.ram)

    def print_summary(self):
        print('Input format is s(%d,%d)' % (self.iw, self.if_))
        print('Output format is s(%d,%d)' % (self.ow, self.of))
        print('The input range is: %g to %g' % (self.xmin, self.xmax))
        print('The output range is: %g to %g' % (self.ymin, self.ymax))

    def print_verilog(self, filename=None):
        if filename is None:
            print(self.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.verilog)
