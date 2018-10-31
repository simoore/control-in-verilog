import numpy as np
import scipy.linalg as linalg
import scipy.signal as signal


class StateSpace(object):

    def __init__(self, cofs, dt=None, delta=None):
        """
        Parameters
        ----------
        dt : None | float
            The sampling period of the system. None for a continous time system.
        delta : None | float
            The scaling parameter for the delta operator. None when using the shift operator.
        """
        mat_a, mat_b, mat_c, _ = cofs
        self.cofs = cofs
        self.dt = dt
        self.delta = delta
        self.n_input = mat_b.shape[1]
        self.n_output = mat_c.shape[0]
        self.n_order = mat_a.shape[0]

    def __neg__(self):

        mat_a, mat_b, mat_c, mat_d = self.cofs
        return StateSpace((mat_a, mat_b, -mat_c, -mat_d), self.dt, self.delta)

    def __add__(self, other):
        """Two systems can be combined in parallel if they have the same number of inputs and outputs, and the same
        sampling frequency and operator.
        """

        if not isinstance(other, StateSpace):
            raise TypeError(
                'Second operand must be controlinverilog.StateSpace')
        if self.n_input != other.n_input:
            raise ValueError('Systems must have the same number of inputs')
        if self.n_output != other.n_output:
            raise ValueError('Systems must have the same number of outputs')
        if self.dt != other.dt:
            raise ValueError('Systems must have the same sampling frequency')
        if self.delta != other.delta:
            raise ValueError('Systems must have the same state update operator')

        a1, b1, c1, d1 = self.cofs
        a2, b2, c2, d2 = other.cofs
        a = linalg.block_diag(a1, a2)
        b = np.vstack((b1, b2))
        c = np.hstack((c1, c2))
        d = d1 + d2

        return StateSpace((a, b, c, d), self.dt, self.delta)

    def __sub__(self, other):

        return self + (-other)

    def is_continuous(self):
        return self.dt is None and self.delta is None

    def is_shift(self):
        return self.dt is not None and self.delta is None

    def is_delta(self):
        return self.dt is not None and self.delta is not None

    def is_siso(self):
        """
        Returns True if the system is SISO else False.
        """
        return self.n_input == 1 and self.n_output == 1

    def poles(self):
        """
        Returns the eigenvalues of the system.
        """
        a, _, _, _ = self.cofs
        e, _ = linalg.eig(a)
        return e

    def eval_transfer_function(self, p):
        """
        Evaluate the transfer function at the complex number 'p'.
        """
        a, b, c, d = self.cofs
        return c @ linalg.inv(p * np.identity(self.n_order) - a) @ b + d

    # def transform_params(self, func):
    #     """Creates a new system with the function `func` applied to each
    #     state space matrix.
    #     """
    #     mats = [func(mat) for mat in self.cofs]
    #     return StateSpace(mats, self.dt, self.delta)

    def quantized_system(self, cf):
        """
        Returns a system with quantized coefficients. It doesn't consider the word length only the fractional length.
        This function is only relevent for coefficient fractional lengths greater than 0.
        """
        if cf <= 0:
            raise ValueError('Valid output for cf > 0.')

        scale = 2 ** cf
        mats = [np.around(scale * mat) / scale for mat in self.cofs]
        sys_q = StateSpace(mats, self.dt, self.delta)
        return sys_q

    def fixed_point_system(self, cf):
        scale = 2 ** cf
        mats = [np.around(scale * mat) for mat in self.cofs]
        sys_fixed = StateSpace(mats, self.dt, self.delta)
        return sys_fixed

    def static_gain(self):

        if self.is_continuous():
            return self.eval_transfer_function(0)
        elif self.is_shift():
            return self.eval_transfer_function(1)
        elif self.is_delta():
            return self.eval_transfer_function(0)

        msg = 'System neither continuous, shift, or delta type.'
        raise ValueError(msg)

    def cont2shift(self, dt):

        if not self.is_continuous():
            msg = 'System must be continuous to call this function.'
            raise ValueError(msg)

        tup = signal.cont2discrete(self.cofs, dt, method='bilinear')
        return StateSpace(tup[0:4], dt=dt)

    def delta2shift(self):

        if not self.is_delta():
            msg = 'System must use the delta operator to call this function.'
            raise ValueError(msg)

        ad, bd, cd, dd = self.cofs
        az = (np.identity(self.n_order) + self.delta * ad)
        bz = self.delta * bd
        return StateSpace((az, bz, cd, dd), dt=self.dt, delta=self.delta)

    def is_asymtotically_stable(self):
        """
        Determines if the system is asymtotically stable.
        
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
            return np.all(np.abs(1 + self.delta * e) < 1)

        msg = 'System neither continuous, shift, or delta type.'
        raise ValueError(msg)

    def time_constant(self):
        """
        Returns
        -------
        tc : float
            The time constant of the slowest pole in the system.
        """

        if not self.is_asymtotically_stable():
            raise ValueError('The system needs to be asymtotically stable.')

        if self.is_shift() is False:
            raise ValueError('This function is for shift operator systems.')

        mat_a, _, _, _ = self.cofs
        zeig = linalg.eigvals(mat_a)
        zeig = zeig[np.nonzero(zeig)]
        seig = np.log(zeig) / self.dt
        r = np.amin(np.abs(np.real(seig)))
        tc = 1.0 / r
        return tc

    def discrete_siso_impulse_response(self, n_tc=7):

        if self.is_siso() is False:
            raise ValueError('This function is for SISO systems.')

        if self.is_delta() is False and self.is_shift() is False:
            raise ValueError('This function is for discrete time systems.')

        if self.is_delta() is True:
            sys = self.delta2shift()
        else:
            sys = self

        mat_a, mat_b, mat_c, mat_d = sys.cofs
        tc = sys.time_constant()
        n = round(n_tc * tc / sys.dt)
        t, y = signal.dimpulse((mat_a, mat_b, mat_c, mat_d, sys.dt), n=n)
        return t, np.squeeze(y)

    def discrete_siso_step_response(self, n_tc=7):

        if self.is_siso() is False:
            raise ValueError('This function is for SISO systems.')

        if self.is_delta() is False and self.is_shift() is False:
            raise ValueError('This function is for discrete time systems.')

        if self.is_delta() is True:
            sys = self.delta2shift()
        else:
            sys = self

        mat_a, mat_b, mat_c, mat_d = sys.cofs
        tc = sys.time_constant()
        n = round(n_tc * tc / sys.dt)
        t, y = signal.dstep((mat_a, mat_b, mat_c, mat_d, sys.dt), n=n)
        return t, np.squeeze(y)
