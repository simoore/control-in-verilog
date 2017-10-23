import veriloggen as vg
from helpers import real2int, int2verilog


def test_integrator():
    ki = 2.4366e+05
    ts = 1/122.88e6
    ki_integrator = Integrator(ki, ts, 16, 14, 16, 16, -1.5, 1.5)
    ki_integrator.to_console()
    ki_integrator.to_verilog()
        

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
        gd = gain * ts / 2
        
        self.name = name
        self.dw = dw
        self.cw = cw
        self.cf = cf
        self.ki = real2int(gd, cf)
        self.max = real2int(max_, self.af)
        self.min = real2int(min_, self.af)
        
        self.init_statements = []
        self._add_header()
        self._add_input_buffer()
        self._add_logic()
        self._add_output_buffer()
        self.mod.Initial(self.init_statements)
        self.verilog = self.mod.to_verilog()
        
        
    def _add_header(self):
        
        self.mod = vg.core.module.Module(self.name)
        self.dw_par = self.mod.Parameter('DW', self.dw)
        self.cw_par = self.mod.Parameter('CW', self.cw)
        self.cf_par = self.mod.Parameter('CF', self.cf)
        self.iw_par = self.mod.Parameter('IW', self.dw_par + self.cw_par)
        self.ki_par = self.mod.Parameter('KI', self.ki, width=self.cw_par, signed=True)
        self.max_par = self.mod.Parameter('MAX', self.max, width=self.iw_par, signed=True)
        self.min_par = self.mod.Parameter('MIN', self.min, width=self.iw_par, signed=True)
        
        # Input and output signals.
        self.clk = self.mod.Input('clk')
        self.ce_in = self.mod.Input('ce_in')
        self.sig_in = self.mod.Input('sig_in', self.dw_par, signed=True)
        self.ce_out = self.mod.OutputReg('ce_out')
        self.sig_out = self.mod.Output('sig_out', self.dw_par, signed=True)
        
        # Internal signals.
        self.ce_buf = self.mod.Reg('ce_buf')
        self.overflow = self.mod.Wire('overflow')
        self.un = self.mod.Reg('un', width=self.dw_par, signed=True)
        self.yn = self.mod.Reg('yn', width=self.iw_par, signed=True)
        self.xn = self.mod.Reg('xn', width=self.iw_par, signed=True)
        self.kiun = self.mod.Wire('kiun', width=self.iw_par)
        self.yn_ovf = self.mod.Wire('yn_ovf', width=self.iw_par)
        
        # Initial values of registers.
        self.init_statements.append(self.ce_buf.write(0))
        self.init_statements.append(self.un.write(0))
        self.init_statements.append(self.yn.write(0))
        self.init_statements.append(self.xn.write(0))
        self.init_statements.append(self.ce_out.write(0))
        
        
    def _add_input_buffer(self):
        
        inp_buf = vg.seq.seq.Seq(self.mod, 'input_buffer', self.clk)
        inp_buf.add(self.ce_buf.write(self.ce_in))
        buf_statement = self.un.write(self.sig_in)
        inp_buf.If(self.ce_in).add(buf_statement)
        
        
    def _add_logic(self):
        
        self.kiun.assign(self.ki_par * self.un)
        self.yn_ovf.assign(self.yn + self.xn + self.kiun)
        max_term = self.yn_ovf > self.max_par
        min_term = self.yn_ovf < self.min_par
        op = vg.core.vtypes.Lor(max_term, min_term)
        self.overflow.assign(op)
        upper = self.dw_par + self.cf_par - 1
        yn_slice = vg.core.vtypes.Slice(self.yn, upper, self.cf_par)
        self.sig_out.assign(yn_slice)
        
        
    def _add_output_buffer(self):
        
        out_buf = vg.seq.seq.Seq(self.mod, 'output_buffer', self.clk)
        out_buf.add(self.ce_out.write(self.ce_buf))
        xn_statement = self.xn.write(self.sig_in)
        op = vg.core.vtypes.Mux(self.overflow, self.yn, self.yn_ovf)
        yn_statement = self.yn.write(op)
        out_buf.If(self.ce_in).add((xn_statement, yn_statement))
        
        
    def print_parameters(self):
        
        print('parameter DW = %d;' % self.dw)
        print('parameter CW = %d;' % self.cw)
        print('parameter CF = %d;' % self.cf)
        print('parameter KI = %s;' % int2verilog(self.ki, self.cw))
        print('parameter MAX = %s;' % int2verilog(self.max, self.aw))
        print('parameter MIN = %s;' % int2verilog(self.min, self.aw))
        
        
    def print_verilog(self):
        
        print(self.verilog)
        
        
if __name__ == '__main__':
    test_integrator()