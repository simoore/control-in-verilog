import math
import numpy as np
import scipy.signal as signal
from . import mechatronics


class LtiSystem:
    
    def __init__(self, name, fs, sys, iw=16, if_=14, of=14, sf=14):
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
        self.sysa = sys
        
        self._set_format()
        self._set_system()
        
        
    def _set_format(self):
        # TODO: automatrically calculate the norms
        #no = math.ceil(math.log(output_norm, 2))
        #ns = math.ceil(math.log(state_norm, 2))
        no = 6
        ns = 9
        self.cw = 16
        self.cf = 15
        self.ow = self.iw + no + self.of - self.if_
        self.sw = self.iw + ns + self.sf - self.if_
        self.rw = self.cw + self.sw - 1
        self.rf = self.cf + self.sf

                
    def _set_system(self):
        """Generate verilog code for an continuous-time lti system.
    
        Parameters
        ----------
        sys : tuple of ndarray
            A tuple describing the system (A, B, C, D).
        """
        
        # step 1 - discretization using the bilinear transform
        sysa = (self.sysa.A, self.sysa.B, self.sysa.C, self.sysa.D)
        tup = signal.cont2discrete(sysa, self.ts, method='bilinear')
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
        alpha = max([np.amax(np.abs(A1)), np.amax(B * B), np.amax(C * C)])
        delta = 2 ** (-math.floor(math.log(1 / alpha, 2)))
        
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
        