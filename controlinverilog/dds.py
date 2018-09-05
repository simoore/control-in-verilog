import numpy as np
import jinja2


class DDS(object):
    
    def __init__(self, name):
        
        self.n_phase = 24
        self.n_amplitude = 16
        self.n_sine = 8
        self.n_fine = 6
        self.n_fine_amplitude = 8
        self.n_fine_fractional = 14
        context = {'name': name}
         
        loader = jinja2.PackageLoader('controlinverilog', 'templates')
        env = jinja2.Environment(loader=loader)
        template = env.get_template('dds.v')
        self.verilog = template.render(context)
    
    
    def calc_freqword(self, f_exe=122.88e6, f_dds=50e3):
        
        freqword = np.round(f_dds/f_exe * 2**self.n_phase)
        print('localparam [23:0] FREQWORD = %d' % freqword)
        
        
    def calc_phase(self, angle_deg=90):
        
        phaseword = np.round(angle_deg/360 * 2**self.n_phase)
        print('localparam [23:0] PHASE = %d' % phaseword)
        
        
    def generate_sine_lut(self):
        
        n_vals = 2**self.n_sine
        alpha = np.pi / 2 / n_vals
        n_frac = self.n_amplitude - 1
        
        angles = np.arange(n_vals) * alpha
        reals = 0.999 * np.sin(angles)
        fixed = np.round(reals * 2**n_frac)
        
        tup = (self.n_amplitude, self.n_amplitude-1)
        print('// The fine LUT format is s(%d,%d)' % tup)
        for ii, vv in enumerate(fixed):
            print('sin_lut[%d] = %d;' % (ii, vv))
        
        
    def generate_fine_lut(self):
        
        n_vals = 2**self.n_fine
        beta = np.pi / 2 / 2**self.n_sine
        alpha = beta / n_vals
        scale = 2**(self.n_fine_amplitude-1) / np.sin(beta)
        n_frac = np.floor(np.log2(scale))
        
        angles = np.arange(n_vals) * alpha
        reals = 0.999 * np.sin(angles)
        fixed = np.round(2**n_frac * reals)
        
        tup = (self.n_fine_amplitude, n_frac)
        print('// The fine LUT format is s(%d,%d)' % tup)
        for ii, vv in enumerate(fixed):
            print('fine_lut[%d] = %d;' % (ii, vv))
            
        
    def print_verilog(self, filename=None):
        
        if filename is None:
            print(self.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.verilog)
