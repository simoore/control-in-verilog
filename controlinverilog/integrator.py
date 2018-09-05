from .helpers import real2int, int2verilog
import jinja2


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
        
        
    def print_parameters(self):
        
        print('Module: %s' % self.name)
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
        