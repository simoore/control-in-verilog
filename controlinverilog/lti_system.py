import math
import numpy as np
import scipy.signal as signal
from . import mechatronics


class LtiSystem:
    
    def __init__(self, name, fs, sys, iw=16, if_=14, of=14, sf=14, 
                 output_norm=1, state_norm=349.298):
        """
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
        """
        
        self.name = name
        self.ts = 1/fs
        self.iw = iw
        self.if_ = if_
        self.of = of
        self.sf = sf
        
        if isinstance(sys, signal.StateSpace) is True:
            self.sysa = (sys.A, sys.B, sys.C, sys.D)
        else:
            self.sysa = sys
        
        self._set_coefficient_format(cw=16, cf=15)
        self._set_signal_format(output_norm, state_norm)
        self._set_system()
        
        
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
        self.ninputs = B.shape[1]
        self.noutputs = C.shape[0]
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
    
    
    def print_format(self):
        
        print('LTI System Formats:')
        print('Input word length (IW): s(%d,%d)' % (self.iw, self.if_))
        print('Output word length (OW): s(%d,%d)' % (self.ow, self.of))
        print('State word length (SW): s(%d,%d)' % (self.sw, self.sf))
        print('Register word length (RW): s(%d,%d)' % (self.rw, self.rf))
        print('Coefficient word length (CW): s(%d,%d)' % (self.cw, self.cf))
        