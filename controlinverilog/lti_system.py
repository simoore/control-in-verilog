import math
import numpy as np
import scipy.signal as signal
import jinja2

from . import mechatronics


class LtiSystem:
    
    def __init__(self, name, fs, sys, iw=16, if_=14, of=14, sf=14, 
                 output_norm=1, state_norm=349.298, n_add=3):
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
        n_add : int
            The number of additions that can be simulataneously performed in 
            one cycle.
        """
        
        self.name = name
        self.ts = 1/fs
        self.iw = iw
        self.if_ = if_
        self.of = of
        self.sf = sf
        self.n_add = n_add
        
        if isinstance(sys, signal.StateSpace) is True:
            self.sysa = (sys.A, sys.B, sys.C, sys.D)
        else:
            self.sysa = sys
        
        self._set_coefficient_format(cw=16, cf=15)
        self._set_signal_format(output_norm, state_norm)
        self._set_system()
        self.gen_template_vars()

        # Generate verilog code.
        context = {'name': name,
                   'iw': self.iw,
                   'ow': self.ow,
                   'sw': self.sw,
                   'cw': self.cw,
                   'cf': self.cf,
                   'del': self.del_par,
                   'params': self.params,
                   'sig_in': self.sig_in,
                   'sig_out': self.sig_out,
                   'sig_u': self.sig_u,
                   'sig_x': self.sig_x,
                   'sig_x_long': self.sig_x_long,
                   'sig_dx': self.sig_dx,
                   'sig_y_long': self.sig_y_long,
                   'sig_prod': self.sig_prod,
                   'sig_add': self.sig_add,
                   'input_buffers': self.input_buffers,
                   'state_buffers': self.state_buffers,
                   'outputs': self.outputs,
                   'prods': self.prods,
                   'deltas': self.deltas,
                   'adders': self.adders}
        
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
        
        no = math.ceil(math.log(output_norm, 2))
        ns = math.ceil(math.log(state_norm, 2))

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
        self.del_par = int(math.log(1 / delta, 2))
        
        
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
        delta = 2 ** (-math.floor(math.log(range_ / alpha, 2)))
        
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
    
    
    def gen_template_vars(self):
        
        def name_signal(name, index):
            return '_'.join((name, str(index + 1)))
        
        vfunc = np.vectorize(name_signal)
        
        ind_in = np.arange(self.n_inputs)
        ind_out = np.arange(self.n_outputs)
        ind_order = np.arange(self.order)
        
        self.sig_in = vfunc('sig_in', ind_in)
        self.sig_out = vfunc('sig_out', ind_out)
        self.sig_u = vfunc('u', ind_in)
        self.sig_x_long = vfunc('x_long', ind_order)
        self.sig_x = vfunc('x', ind_order)
        self.sig_dx = vfunc('dx', ind_order)
        self.sig_y_long = vfunc('y_long', ind_out)
        
        self.input_buffers = zip(self.sig_u, self.sig_in)
        self.state_buffers = zip(self.sig_x, self.sig_x_long)
        self.outputs = zip(self.sig_out, self.sig_y_long)
        self.deltas = zip(self.sig_x_long, self.sig_dx)
        
        self.params = []
        self.sig_prod = []
        self.prods = []
        self.adders = []
        self.sig_add = []
        
        axs = self.gen_matrix(self.A, 'A', 'ax', self.sig_x)
        bus = self.gen_matrix(self.B, 'B', 'bu', self.sig_u)
        cxs = self.gen_matrix(self.C, 'C', 'cx', self.sig_x)
        dus = self.gen_matrix(self.D, 'D', 'du', self.sig_u)
        self.gen_adder_ce()
        self.gen_adder(axs, bus, self.sig_dx, 'sumS')
        self.gen_adder(cxs, dus, self.sig_y_long, 'sumO')
        
        
    def gen_matrix(self, mat, par_name, reg_name, inp):
        
        def name_elem(name, r, c):
            return '_'.join((name, str(r + 1), str(c + 1)))
        
        def sig_prod_elem(r, c):
            return name_elem(reg_name, r, c)
        
        def prod_elem(r, c):
            return {'name': name_elem(par_name, r, c), 
                    'value': int(mat[r, c])}
        
        v2 = np.vectorize(sig_prod_elem)
        v3 = np.vectorize(prod_elem)
        sig_prod = np.fromfunction(v2, mat.shape, dtype=int)
        params = np.fromfunction(v3, mat.shape, dtype=int)
        
        def prod_elem(row, col):
            return {'o': sig_prod[row, col], 
                    'a': params[row, col]['name'], 
                    'b': inp[col]}
            
        v4 = np.vectorize(prod_elem)
        prods = np.fromfunction(v4, mat.shape, dtype=int)
        
        self.params.extend(params.ravel())
        self.sig_prod.extend(sig_prod.ravel())
        self.prods.extend(prods.ravel())
        return sig_prod


    def gen_adder_ce(self):
        
        n_inp = self.order + self.n_inputs
        n_stages = math.ceil(math.log(n_inp, self.n_add))
        ce = ['_'.join(('ce_add', str(ii))) for ii in range(1, n_stages)]
        ce.insert(0, 'ce_mul')
        ce.append('ce_out')
        self.adders.extend(list(zip(ce[1:], ce[:-1])))
        

    def gen_adder(self, state_terms, input_terms, output_terms, reg_name):
 
        n_add = self.n_add
        n_inp = self.order + self.n_inputs
        n_stages = math.ceil(math.log(n_inp, n_add))
        n_eqn = len(output_terms)
        
        def name_reg(x, y, z):
            return '_'.join((reg_name, str(x), str(y), str(z)))
        
        for ii in range(n_eqn):
            terms = np.concatenate((state_terms[ii, :], input_terms[ii, :]))
            for jj in range(n_stages):
                size = min(n_add, len(terms))
                n_terms = (len(terms) - 1) // size + 1
                terms = np.array_split(terms, n_terms)
                terms = [' + '.join(n) for n in terms]
                if jj == n_stages - 1:
                    new_terms = [output_terms[ii]]
                else:
                   index = np.arange(n_terms)
                   new_terms = [name_reg(ii, jj, kk) for kk in index]   
                   self.sig_add.extend(new_terms)
                self.adders.extend(list(zip(new_terms, terms)))
                terms = new_terms
        
        
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
        