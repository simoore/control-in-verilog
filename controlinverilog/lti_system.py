import math
import numpy as np
import scipy.signal as signal
from . import mechatronics
from .state_space import StateSpace
from .lti_verilog import LtiVerilog
from .lti_formats_coefficients import LtiFormatsCoefficients
from .lti_formats_signals import LtiFormatsSignals


class LtiSystem(object):

    def __init__(
        self,
        name,
        fs,
        sys,
        input_word_length=16,
        input_frac_length=14,
        cof_word_length=16,
        cof_frac_length=15,
        n_add=3,
        cof_threshold=0.001,
        sig_threshold=100,
        operator='delta',
        sig_scaling_method='hinf',
        cof_scaling_method='hinf',
        verbose=True
    ):
        """
        Contructs the verilog code implementing an LTI system.
        
        Parameters
        ----------
        name : string
            The name of module.
        fs : float
            The sampling frequency.
        sys : tuple of ndarray
            The state space representation of an analog system that is to be implemented in verilog.
        input_word_length : int
            Input word length.
        input_frac_length : int
            Input fractional length.
        cof_word_length : int
            The coefficient word length if using 'fixed' cof_scaling_method.
        cof_frac_length : int
            The coefficient fractional length if using 'fixed' cof_scaling method.
        n_add : int
            The number of additions that can be simulataneously performed in one cycle.
        cof_threshold : float
            A metric to set the coefficient fixed point formats. The small this number the larger the word length.
        sig_threshold : float
            A metric to set the signal formats. The larger this number the larger the word length.
        operator : 'delta' | 'shift'
            The operator employed in the state equations.
        sig_scaling_method : 'hinf' | 'h2' | 'overshoot' | 'safe'
            The method to calculate the word growth of the state and output signals.
        cof_scaling_method : 'h2' | 'hinf' | 'impulse' | 'pole' | 'fixed'
            The method to calculate the fixed point format of the coefficients.
        verbose : bool
            True to print a summary of the conversion process.
        """

        if isinstance(sys, signal.StateSpace) is True:
            sysa = StateSpace((sys.A, sys.B, sys.C, sys.D))
        else:
            sysa = StateSpace((sys[0], sys[1], sys[2], sys[3]))

        if sysa.is_asymtotically_stable() is False:
            raise ValueError('The system must be asymtotically stable.')

        self._verbose = verbose

        sysm, del_par = self.set_system(sysa, dt=1.0 / fs, operator=operator)

        cof_params = dict()
        cof_params['cof_scaling_method'] = cof_scaling_method
        cof_params['cof_word_length'] = cof_word_length
        cof_params['cof_frac_length'] = cof_frac_length
        cof_params['cof_threshold'] = cof_threshold
        cof_params['verbose'] = verbose
        cof_formats = LtiFormatsCoefficients(sysm, cof_params)

        sig_params = dict()
        sig_params['sig_threshold'] = sig_threshold
        sig_params['sig_scaling_method'] = sig_scaling_method
        sig_params['input_word_length'] = input_word_length
        sig_params['input_frac_length'] = input_frac_length
        sig_params['verbose'] = verbose
        sig_formats = LtiFormatsSignals(sysm, sig_params, cof_formats)

        assert sig_formats.state_frac_length - input_frac_length >= 0
        assert (sig_formats.state_word_length - input_word_length
                - sig_formats.state_word_length + input_word_length >= 0)

        verilog_params = dict()
        verilog_params['name'] = name
        verilog_params['n_add'] = n_add
        verilog_params['iw'] = input_word_length
        verilog_params['ow'] = sig_formats.output_word_length
        verilog_params['sw'] = sig_formats.state_word_length
        verilog_params['cw'] = cof_formats.cof_word_length
        verilog_params['cf'] = cof_formats.cof_frac_length
        verilog_params['if'] = input_frac_length
        verilog_params['sf'] = sig_formats.state_frac_length
        verilog_params['del_par'] = del_par

        sysf = sysm.fixed_point_system(cof_formats.cof_frac_length)
        self.lti_verilog = LtiVerilog(sysf, verilog_params)

        if verbose is True:
            cof_formats.print_summary()
            sig_formats.print_summary()

    def set_system(self, sysa, dt, operator):
        """
        Computes parameters for verilog code generation.
        """

        # step 1 - discretization using the bilinear transform
        sysd = sysa.cont2shift(dt)

        # step 2 - convert to balanced realization
        ab, bb, cb, db = mechatronics.balanced_realization_discrete(*sysd.cofs)
        sysb = StateSpace((ab, bb, cb, db), dt=sysd.dt)

        # step 3 - convert to delta operator
        if operator == 'delta':
            sysm = self.sys_to_delta(sysb)
        elif operator == 'shift':
            sysm = sysb
        else:
            msg = 'Valid operator values: delta | shift.'
            raise ValueError(msg)

        # step 4 - set attributes used in verilog code generation
        if sysm.delta is None:
            del_par = None
        else:
            del_par = int(math.log(1 / sysm.delta, 2))

        # step 5 - convert to fixed point (done in the constructor).
        return sysm, del_par

    @staticmethod
    def sys_to_delta(sys):
        """
        Converts the operator of a system from the shift operator to the delta operator. The delta parameter is
        automatically chosen to scale the coefficients to fit in the range (-1,1). In addition it is set to a power of
        two for ease of implementation. Note, the D matrix isn't scaled and may lie out of the range (-1,1).
        
        Parameters
        ----------
        sys : controlinverilog.state_space.StateSpace
            A shift operator system to be converted to a delta operator system.
            
        Returns
        -------
        sysdelta : controlinverilog.state_space.StateSpace
            The coefficients of the delta operator system (A, B, C, D) and the delta parameter.
        """

        # convert A matrix to delta form
        az, bz, cz, dz = sys.cofs
        a1 = az - np.identity(sys.n_order)

        # choose delta parameter
        range_ = 1  # 2 ** (self.cw - self.cf - 1)
        alpha = max([np.amax(np.abs(a1)), np.amax(bz * bz), np.amax(cz * cz)])
        delta = 2 ** (-math.floor(math.log2(range_ / alpha)))

        if delta > 1:
            msg = 'Invalid delta parameter, use the shift operator.'
            raise ValueError(msg)

        # transform system
        am = a1 / delta
        bm = bz / np.sqrt(delta)
        cm = cz / np.sqrt(delta)

        sysdelta = StateSpace((am, bm, cm, dz), dt=sys.dt, delta=delta)
        return sysdelta

    def print_verilog(self, filename=None):

        if filename is None:
            print(self.lti_verilog.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.lti_verilog.verilog)
