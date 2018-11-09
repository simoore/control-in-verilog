import jinja2


def real2int(val, vf):
    """
    :param val:     The real number to convert to its signed integer representation.
    :param vf:      The fractional length.
    """
    return round(val * 2 ** vf)


def int2verilog(val, vw):
    """
    :param val: A signed integer to convert to a verilog literal.
    :param vw:  The word length of the constant value.
    """
    sign = '-' if val < 0 else ''
    s = ''.join((sign, str(vw), '\'sd', str(abs(val))))
    return s


class Integrator(object):

    def __init__(self, gain, ts, dw, df, cw, cf, min_, max_, name='integrator'):
        """
        gain      The analog integral gain.
        ts        The sampling period.
        dw        The signal word length.
        df        The signal fractional length.
        cw        The coefficient word length.
        cf        The coefficient fractional length.
        min_      The minimum analog saturation value.
        max_      The maximum analog saturation value.
        name      The name of the verilog module.
        """

        self.af = cf + df
        self.aw = cw + dw
        gd = float(gain) * ts / 2

        self.name = name
        self.dw = dw
        self.df = df
        self.real_max = max_
        self.real_min = min_
        self.cw = cw
        self.cf = cf
        self.ki = real2int(gd, cf)
        self.max = real2int(max_, self.af)
        self.min = real2int(min_, self.af)

        context = {
            'name': self.name,
            'DW': self.dw,
            'CW': self.cw,
            'CF': self.cf,
            'KI': int2verilog(self.ki, self.cw),
            'MAX': int2verilog(self.max, self.aw),
            'MIN': int2verilog(self.min, self.aw)
        }
        loader = jinja2.PackageLoader('controlinverilog', 'templates')
        env = jinja2.Environment(loader=loader)
        template = env.get_template('integrator.v')
        self.verilog = template.render(context)

    def print_summary(self):

        input_range = 2 ** (self.dw - self.df - 1)

        print('Module: %s' % self.name)
        print('Input/Output Range: [%g, %g]' % (-input_range, input_range))
        print('Saturation Range: [%g, %g]' % (self.real_min, self.real_max))
        print('parameter DW = %d;' % self.dw)
        print('parameter CW = %d;' % self.cw)
        print('parameter CF = %d;' % self.cf)
        print('parameter signed [CW-1:0] KI = %d;' % self.ki)
        print('parameter signed [IW-1:0] MAX = %d;' % self.max)
        print('parameter signed [IW-1:0] MIN = %d;' % self.min)

    def print_verilog(self, filename=None):

        if filename is None:
            print(self.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.verilog)
