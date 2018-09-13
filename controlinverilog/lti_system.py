import math
import numpy as np
import scipy.signal as signal
import jinja2
from . import mechatronics


class LtiSystem(object):
    
    def __init__(self, name, fs, sys, iw=16, if_=14, of=14, sf=14, 
                 n_add=3, operator='delta', scaling_method='hinf'):
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
        operator : 'delta' | 'shift'
            The operator employed in the state equations.
        scaling_method : 'hinf' | 'h2' | 'overshoot' | 'safe'
            The method to calculate the word growth of the state and output
            signals.
        """
        
        if mechatronics.is_asymtotically_stable(sys) is False:
            raise ValueError('The system must be asymtotically stable.')
        
        self.name = name
        self.dt = 1.0/fs
        self.iw = iw
        self.if_ = if_
        self.of = of
        self.sf = sf
        self.n_add = n_add
        self.operator = operator
        self.scaling_method = scaling_method
        
        if isinstance(sys, signal.StateSpace) is True:
            self.sysa = (sys.A, sys.B, sys.C, sys.D)
        else:
            self.sysa = sys
        
        self.set_system()
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
        

    def set_coefficient_format(self, sys, delta=None):
        # TODO: Determine an automated fashion to set these variables.
        
        cf=15
        # A, B, C, D = sys
        
        # Find the maximum coefficient to determine the size integer word 
        # length.
        max_coeff = max(map(lambda x: np.amax(np.abs(x)), sys[:3]))
        int_w = math.ceil(math.log2(max_coeff))
        
        # Find largest coefficient.
        
        self.cf = cf
        self.cw = 1 + int_w + self.cf
        
        
    def set_signal_format(self, sys, delta):
        """Set the word length of the output, state and intermediate registers.
        
        sys : tuple of ndarray
            A state space discrete time to be coded in verilog. The 
            coefficients are in their full precision values in the final
            realization.
        delta : float | None
            The delta parameter when using the delta operator, None if using
            the shift operator.
        """
        
        funcs = {'hinf': mechatronics.norm_hinf_discrete_siso,
                 'h2': mechatronics.norm_h2_discrete_siso,
                 'overshoot': lambda x: mechatronics.overshoot(x, 1.0),
                 'safe': lambda x: mechatronics.safe_gain(x, 1.0)}
        
        if self.scaling_method not in funcs:
            raise ValueError('Invalid scaling_method parameter for LtiSystem.')
        func = funcs[self.scaling_method]
        
        A, B, C, D = sys
        self.order = A.shape[0]
        self.n_inputs = B.shape[1]
        self.n_outputs = C.shape[0]
        
        # Convert delta operator to shift operator for simulation.
        if delta is not None:
            A, B = (np.identity(self.order) + delta * A), delta * B   
            
        # The equivalent single input system where all inputs are equal.
        B = B @ np.ones((self.n_inputs, 1))
        
        # The norm from the single input to each state.
        self.state_norms = np.zeros(self.order)
        for i in range(self.order):
            c = np.zeros((1, self.order))
            c[0, i] = 1
            sys_state = (A, B, c, np.zeros((1, 1)));
            self.state_norms[i] = func(sys_state)
        state_norm = np.amax(self.state_norms)
        
        # The norm from the single input to each output.
        self.output_norms = np.zeros(self.n_outputs)
        for i in range(self.n_outputs):
            c = C[[i], :]
            d = D[[i], :]
            sys_state = (A, B, c, d)
            self.output_norms[i] = func(sys_state)
        output_norm = np.amax(self.output_norms)
                
        no = math.ceil(math.log(output_norm, 2))
        ns = math.ceil(math.log(state_norm, 2))

        self.ow = self.iw + no + self.of - self.if_
        self.sw = self.iw + ns + self.sf - self.if_
        self.rw = self.cw + self.sw - 1
        self.rf = self.cf + self.sf

                
    def set_system(self):
        """Computes parameters for verilog code generation.
        """
        
        # step 1 - discretization using the bilinear transform
        tup = signal.cont2discrete(self.sysa, self.dt, method='bilinear')
        sysd = tup[0:4]
        
        # step 2 - convert to balanced realization
        sysb = mechatronics.balanced_realization_discrete(sysd)
        
        # step 3 - convert to delta operator
        if self.operator == 'delta':
            sysm, delta = self.sys_to_delta(sysb)
        elif self.operator == 'shift':
            sysm, delta = sysb, None
        else:
            ValueError('Invalid operator parameter for LtiSystem.')
        
        # step 4 - convert to fixed point 
        self.set_coefficient_format(sysm)
        self.set_signal_format(sysm, delta)
        sysf = self.sys_to_fixed(sysm)
        
        # step 5 - set attributes used in verilog code generation
        A, B, C, D = sysf
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.del_par = None if delta is None else int(math.log(1 / delta, 2))
        
        
    def sys_to_delta(self, sys):
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
        range_ = 1 # 2 ** (self.cw - self.cf - 1)
        alpha = max([np.amax(np.abs(A1)), np.amax(B * B), np.amax(C * C)])
        delta = 2 ** (-math.floor(math.log2(range_ / alpha)))
        
        # TODO: raise exception if delta value greater > 1
        
        # transform system
        AM = A1 / delta
        BM = B / np.sqrt(delta)
        CM = C / np.sqrt(delta)
        
        sysdelta = (AM, BM, CM, D)
        return sysdelta, delta
    
    
    def sys_to_fixed(self, sys):
        """
        """
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
        
        print()
        for i, n in enumerate(self.state_norms):
            print('The norm from input to state x%d is %g' % (i, n))
            
        for i, n in enumerate(self.output_norms):
            print('The norm from input to output y%d is %g' % (i, n))
        