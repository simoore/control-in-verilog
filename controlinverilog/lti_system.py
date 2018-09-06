from math import ceil, floor, log
import numpy as np
import scipy.signal as signal
import jinja2
from . import mechatronics


class LtiSystem:
    
    def __init__(self, name, fs, sys, iw=16, if_=14, of=14, sf=14, 
                 output_norm=1, state_norm=349.298, stages=1):
        """
        Contructs the verilog code implementing an LTI system.
        
        Parameters
        ----------
        name : string
            The name of module.
        fs : float
            The sampling frequency.
        sys : tuple of ndarray
            The state space representation of an analog system that is to be
            implemented in verilog.
        iw : int
            Input word length.
        if_ : int
            Input fractional length.
        of : int
            Output fractional length.
        sf : int 
            State fraction length.
        stages : int
            The length of the pipelined in the adder for the matrix 
            multiplications.
        """
        
        self.name = name
        self.ts = 1/fs
        self.iw = iw
        self.if_ = if_
        self.of = of
        self.sf = sf
        self._stages = stages
        
        if isinstance(sys, signal.StateSpace) is True:
            self.sysa = (sys.A, sys.B, sys.C, sys.D)
        else:
            self.sysa = sys
        
        self._set_coefficient_format(cw=16, cf=15)
        self._set_signal_format(output_norm, state_norm)
        self._set_system()
        self._gen_template_vars()

        # Generate verilog code.
        context = {'name': name,
                   'iw': self.iw,
                   'ow': self.ow,
                   'sw': self.sw,
                   'cw': self.cw,
                   'cf': self.cf,
                   'del': self.del_par,
                   'params': self.params,
                   'sig_ins': self.sig_in,
                   'sig_outs': self.sig_out,
                   'sig_u': self.sig_u,
                   'sig_x': self.sig_x,
                   'sig_x_long': self.sig_x_long,
                   'sig_dx': self.sig_dx,
                   'sig_y_long': self.sig_y_long,
                   'sig_prods': self.sig_prods,
                   'input_buffers': self.input_buffers,
                   'state_buffers': self.state_buffers,
                   'outputs': self.outputs,
                   'prods': self.prods,
                   'deltas': self.deltas,
                   'adder': self.adder}
        
        loader = jinja2.PackageLoader('controlinverilog', 'templates')
        env = jinja2.Environment(loader=loader, trim_blocks=True, 
                                 lstrip_blocks=True)
        template = env.get_template('lti_system.v')
        self.verilog = template.render(context)
        

    def _set_coefficient_format(self, cw, cf):
        # TODO: Determine an automated fashion to set these variables.
        self.cw = cw
        self.cf = cf
        
        
    def _set_signal_format(self, output_norm, state_norm):
        # TODO: automatrically calculate the norms.
        
#        output_norm = mechatronics.norm_hinf(sys)
#        order = mechatronics.order(sys)
#        A, B, _, _ = sys
#        
#        nn = np.zeros(order)
#        for i in range(order):
#            c = np.zeros((1, order))
#            c[0, i] = 1
#            sys_state = (A, B, c, np.zeros((1, 1)));
#            nn[i] = mechatronics.norm_hinf(sys_state)
#            print('The inf norm from input to state x%d is %g\n' % (i, nn))
#        state_norm = np.amax(nn)
#        
#        print('Output norm %g' % output_norm)
#        print('State norm %g' % state_norm)
        
        no = ceil(log(output_norm, 2))
        ns = ceil(log(state_norm, 2))

        self.ow = self.iw + no + self.of - self.if_
        self.sw = self.iw + ns + self.sf - self.if_
        self.rw = self.cw + self.sw - 1
        self.rf = self.cf + self.sf

                
    def _set_system(self):
        """Generate verilog code parameters for the LTI system.
    
        Parameters
        ----------
        sys : tuple of ndarray
            A tuple describing the system (A, B, C, D).
        """
        
        # step 1 - discretization using the bilinear transform
        tup = signal.cont2discrete(self.sysa, self.ts, method='bilinear')
        sysd = tup[0:4]
        
        # step 2 - convert to balanced realization
        sysb = mechatronics.balanced_realization_discrete(sysd)
        
        # step 3 - convert to delta operator
        sysm, delta = self._sys_to_delta(sysb)
        
        # step 4 - convert to fixed point 
        sysf = self._sys_to_fixed(sysm)
        
        # step 5 - set attributes used in verilog code generation
        A, B, C, D = sysf
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.order = A.shape[0]
        self.n_inputs = B.shape[1]
        self.n_outputs = C.shape[0]
        self.del_par = int(log(1 / delta, 2))
        
        
    def _sys_to_delta(self, sys):
        """Converts the operator of a system from the shift operator to the 
        delta operator. The delta parameter is automatrically chosen to scale 
        the coefficients to fit in the range (-1,1). In addition it is set to a 
        power of two for ease of implementation. Note, the D matrix isn't 
        scaled and may lie out of the range (-1,1).
        
        Parameters
        ----------
        sys : tuple of ndarray
            The system parameters (A, B, C, D).
            
        Returns
        -------
        sysdelta : tuple of ndarray
            The coefficients of the delta operator system (A, B, C, D).
        delta : float
            The calculated delta parameter.
        """
        
        # convert A matrix to delta form
        A, B, C, D = sys
        order = A.shape[0]
        A1 = A - np.identity(order)
        
        # choose delta parameter
        range_ = 2 ** (self.cw - self.cf - 1)
        alpha = max([np.amax(np.abs(A1)), np.amax(B * B), np.amax(C * C)])
        delta = 2 ** (-floor(log(range_ / alpha, 2)))
        
        # transform system
        AM = A1 / delta
        BM = B / np.sqrt(delta)
        CM = C / np.sqrt(delta)
        
        sysdelta = (AM, BM, CM, D)
        return sysdelta, delta
    
    
    def _sys_to_fixed(self, sys):
        
        scale = 2 ** self.cf
        sysf = tuple([np.round(scale * mat) for mat in list(sys)])
        return sysf
    
    
    def _gen_template_vars(self):
        
        f2 = lambda x, y: ''.join((x, str(y + 1)))
        
        self.sig_in = [f2('sig_in', n) for n in range(self.n_inputs)]
        self.sig_out = [f2('sig_out', n) for n in range(self.n_outputs)]
        self.sig_u = [f2('u', n) for n in range(self.n_inputs)]
        self.sig_x_long = [f2('x_long', n) for n in range(self.order)]
        self.sig_x = [f2('x', n) for n in range(self.order)]
        self.sig_dx = [f2('dx', n) for n in range(self.order)]
        self.sig_y_long = [f2('y_long', n) for n in range(self.n_outputs)]
        
        self.input_buffers = zip(self.sig_u, self.sig_in)
        self.state_buffers = zip(self.sig_x, self.sig_x_long)
        self.outputs = zip(self.sig_out, self.sig_y_long)
        self.deltas = zip(self.sig_x_long, self.sig_dx)
        
        self.params = []
        self.sig_prods = []
        self.prods = []
        self.adder = []
        
        self._gen_matrix(self.A, 'A', 'ax', 'x')
        self._gen_matrix(self.B, 'B', 'bu', 'u')
        self._gen_matrix(self.C, 'C', 'cx', 'x')
        self._gen_matrix(self.D, 'D', 'du', 'u')
        self._gen_adder()
        
        
    def _gen_matrix(self, mat, par_name, reg_name, inp_name):

        for r, c in np.ndindex(mat.shape):
            n1 = ''.join((par_name, str(r + 1), '_', str(c + 1)))
            n2 = ''.join((reg_name, str(r + 1), '_', str(c + 1)))
            n3 = ''.join((inp_name, str(c + 1)))
            val = int(mat[r, c])
            self.sig_prods.append(n2)
            self.params.append({'name': n1, 'value': val})
            self.prods.append({'o': n2, 'a': n1, 'b': n3})
            
    
    def _gen_adder(self):
        """
        The V2 adder is pipelined. It is also defined by the maximum number of 
        terms to add in one cycle, rather than the number of stages.
        """

        #comp = 6 # The number of terms to add.
        #n_add = 3 # The max number of terms to add.
 
        n_operands = [5]
        n_operands = [3, 2] 
        
        # TODO: calculate this matrix.
        
        # TODO: Add clock enable.
        
        def helper(n_eqn, slbl, ilbl, offset, sig_result):
        
            f1 = lambda x, y, z: ''.join((x, str(y + 1), '_', str(z + 1)))
            f2 = lambda x, y, z: ''.join(('sum', str(x), str(y), str(z)))
            
            for ii in range(n_eqn):
                state_terms = [f1(slbl, ii, jj) for jj in range(self.order)]
                input_terms = [f1(ilbl, ii, jj) for jj in range(self.n_inputs)]
                terms = state_terms + input_terms
                for jj, size in enumerate(n_operands):
                    terms = [' + '.join(terms[kk:kk+size]) 
                             for kk in range(0, len(terms), size)]
                    if jj == len(n_operands)-1:
                        new_terms = [sig_result[ii]]
                    else:
                        new_terms = [f2(ii + offset, jj, kk) 
                                     for kk in range(len(terms))]    
                    self.adder.extend(list(zip(new_terms, terms)))
                    terms = new_terms
        
        helper(self.order, 'ax', 'bu', 0, self.sig_dx)
        helper(self.n_outputs, 'cx', 'du', self.order, self.sig_y_long)
        
        
    def print_verilog(self, filename=None):
        
        if filename is None:
            print(self.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.verilog)
    
    
    def print_summary(self):
        
        print('LTI System Formats:')
        print('Input word length (IW): s(%d,%d)' % (self.iw, self.if_))
        print('Output word length (OW): s(%d,%d)' % (self.ow, self.of))
        print('State word length (SW): s(%d,%d)' % (self.sw, self.sf))
        print('Register word length (RW): s(%d,%d)' % (self.rw, self.rf))
        print('Coefficient word length (CW): s(%d,%d)' % (self.cw, self.cf))
        