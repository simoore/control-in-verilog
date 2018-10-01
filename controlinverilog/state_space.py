import numpy as np
import scipy.linalg as linalg
import scipy.signal as signal

class StateSpace(object):
    
    def __init__(self, A, B, C, D, dt=None, delta=None):
        """
        Parameters
        ----------
        dt : None | float
            The sampling period of the system. None for a continous time system.
        delta : None | float
            The scaling parameter for the delta operator. None when using the 
            shift operator.
        """
        self.params = (A, B, C, D)
        self.dt = dt
        self.delta = delta
        self.n_input = B.shape[1]
        self.n_output = C.shape[0]
        self.n_order = A.shape[0]
        
        
    def __neg__(self):
        
        A, B, C, D = self.params
        return StateSpace(A, B, -C, -D, self.dt, self.delta)
    
    
    def __add__(self, other):
        """Two systems can be combined in parallel if they have the same
        number of inputs and outputs, and the same sampling frequency and 
        operator.
        """
        
        if not isinstance(other, StateSpace):
            raise TypeError('Second operand must be controlinverilog.StateSpace')
        if (self.n_input != other.n_input):
            raise ValueError('Systems must have the same number of inputs')
        if (self.n_output != other.n_output):
            raise ValueError('Systems must have the same number of outputs')
        if (self.dt != other.dt):
            raise ValueError('Systems must have the same sampling frequency')
        if (self.delta != other.delta):
            raise ValueError('Systems must have the same state update operator')
        
        A1, B1, C1, D1 = self.params
        A2, B2, C2, D2 = other.params
        A = linalg.block_diag(A1, A2)
        B = np.vstack((B1, B2))
        C = np.hstack((C1, C2))
        D = D1 + D2
    
        return StateSpace(A, B, C, D, self.dt, self.delta)
    
    
    def __sub__(self, other):
        
        return self + (-other)
    
    
    def is_continuous(self):
        return self.dt is None and self.delta is None
    
    
    def is_shift(self):
        return self.dt is not None and self.delta is None
    
    
    def is_delta(self):
        return self.dt is not None and self.delta is not None
    
    
    def is_siso(self):
        """Returns True if the system is SISO else False.
        """
        return (self.n_input == 1 and self.n_output == 1)
    
    
    def poles(self):
        """Returns the eigenvalues of the system.
        """
        A, _, _, _ = self.params
        e, _ = linalg.eig(A)
        return e
    
    
    def transfer_function(self, p):
        """Evaluate the transfer function at the complex number 'p'.
        """
        A, B, C, D = self.params
        return C @ linalg.inv(p*np.identity(self.n_order) - A) @ B + D
        
    
    def transform_params(self, func):
        """Creates a new system with the function `func` applied to each 
        state space matrix.
        """
        mats = [func(mat) for mat in self.params]
        A, B, C, D = mats
        return StateSpace(A, B, C, D, self.dt, self.delta)
    
    
    def static_gain(self):
        
        if self.is_continuous():
            return self.transfer_function(0)
        elif self.is_shift():
            return self.transfer_function(1)
        elif self.is_delta():
            return self.transfer_function(0)
        
        msg = 'System neither continuous, shift, or delta type.'
        raise ValueError(msg)
        
        
    def cont2shift(self, dt):
        
        if not self.is_continuous():
            msg = 'System must be continuous to call this function.'
            raise ValueError(msg)
            
        tup = signal.cont2discrete(self.params, dt, method='bilinear')
        A, B, C, D = tup[0:4]
        return StateSpace(A, B, C, D, dt=dt)
        
    
    def delta2shift(self):
        
        if not self.is_delta():
            msg = 'System must use the delta operator to call this function.'
            raise ValueError(msg)
            
        A, B, C, D = self.params
        A = (np.identity(self.n_order) + self.delta * A)  
        B = self.delta * B
        return StateSpace(A, B, C, D, dt=self.dt, delta=self.delta)
        
        
    def is_asymtotically_stable(self):
        """Determines if the system is asymtotically stable.
        
        Returns
        -------
        is_asymtotically_stable : boolean
            True is stable, else False.
        """
        e = self.poles()
        if self.is_continuous():
            return np.all(np.real(e) < 0)
        elif self.is_shift():
            return np.all(np.abs(e) < 1)
        elif self.is_delta():
            return np.all(np.abs(1 + self.delta*e) < 1)
        
        msg = 'System neither continuous, shift, or delta type.'
        raise ValueError(msg)
        