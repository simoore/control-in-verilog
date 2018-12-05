import math
import itertools
import numpy as np
import scipy.linalg as linalg
from . import mechatronics
from .state_space import StateSpace


class LtiFormatsSignals(object):

    def __init__(self, system, params, lti_format_cofs):
        """
        This class selects the word and fractional lengths of the signals for an LTI system to be implemented with
        fixed point arithmetic.

        Parameters
        ----------
        system : controlinverilog.state_space.StateSpace
            This system contains the coefficients to be stored in a fixed point format.
        params : dictionary
            This dictionary contains the following relevent parameters:
            - verbose: If True print information regarding the signal formats.
            - sig_threshold: A benchmark used to select signal word lengths.
            - input_word_length: The word length of the input signals.
            - input_frac_length: The fractional length of the input signals.
            - sig_scaling_method: 'hinf' | 'h2' | 'overshoot' | 'safe'
        lti_format_cofs : controlinverilog.lti_formats_coefficients.LtiFormatsCoefficients
            The object containing the coefficient fixed point formats.
        """

        self._sig_threshold = params['sig_threshold']
        self._cf = lti_format_cofs.cof_frac_length
        self._cw = lti_format_cofs.cof_word_length
        self._iw = params['input_word_length']
        self._if = params['input_frac_length']

        method = params['sig_scaling_method']
        metric = self._select_signal_scaling_method(method)
        if metric is None:
            self._sf = params['state_frac_length']
            self._sw = params['state_word_length']
            self._of = params['output_frac_length']
            self._ow = params['output_word_length']
        else:
            self._sf, self._of, self._sw, self._ow = self._set_signal_format(metric, system)
        self._rw = self._cw + self._sw - 1
        self._rf = self._cf + self._sf

    @property
    def state_frac_length(self):
        return self._sf

    @property
    def state_word_length(self):
        return self._sw

    @property
    def output_frac_length(self):
        return self._of

    @property
    def output_word_length(self):
        return self._ow

    @property
    def register_frac_length(self):
        return self._rf

    @property
    def register_word_length(self):
        return self._rw

    def _select_signal_scaling_method(self, method):

        if method == 'fixed':
            return None
        
        funcs = {'hinf': self._discrete_siso_hinf_gain,
                 'h2': self._discrete_siso_h2_gain,
                 'overshoot': self._discrete_siso_overshoot_gain,
                 'safe': self._discrete_siso_safe_gain}

        if method not in funcs:
            vals = ' | '.join(funcs.keys())
            msg = 'Valid sig_scaling_method values: %s.' % vals
            raise ValueError(msg)

        func = funcs[method]
        return func

    def _set_signal_format(self, norm_func, sys):
        """
        Set the word length of the output, state and intermediate registers. The coefficient word length must be set
        before calling this function for accurate results.

        sys : controlinverilog.StateSpace
            A state space discrete time to be coded in verilog. The coefficients are in their full precision values in
            the final realization.
        """

        state_norms = self.state_norms(sys, norm_func)
        state_norm = np.amax(state_norms)
        output_norms = self.output_norms(sys, norm_func)
        output_norm = np.amax(output_norms)
        sys_norm = norm_func(sys)

        no = math.ceil(math.log(output_norm, 2))
        ns = math.ceil(math.log(state_norm, 2))

        def eval_dynamic_range(sf):
            return self._dynamic_range(sys, sf, self._cf, sys_norm)

        flt = filter(lambda sf: eval_dynamic_range(sf) > self._sig_threshold, itertools.count(0))
        sf_ = of = next(flt)

        ow = self._iw + no + of - self._if
        sw = self._iw + ns + sf_ - self._if

        return sf_, of, sw, ow

    @staticmethod
    def _discrete_siso_overshoot_gain(sys):
        """
        Returns
        -------
        The overshoot due to a unit step of the system.
        """
        _, y = sys.discrete_siso_step_response(sys)
        return np.amax(y)

    @staticmethod
    def _discrete_siso_safe_gain(sys):
        """
        The upper bound on the output of a SISO system is given by

        gain = sum(|f[k]|)

        where f[k] is the impulse response of the system. To evaluate the impulse response, the system is simulated for
        20x the time constant of the slowest pole of the system.
        """
        _, y = sys.discrete_siso_impulse_response(n_tc=20)
        gain = np.sum(np.abs(y))
        return gain

    @staticmethod
    def _discrete_siso_hinf_gain(sys):
        if sys.is_delta() is True:
            sysz = sys.delta2shift()
        else:
            sysz = sys
        return mechatronics.norm_hinf_discrete(*sysz.cofs)

    @staticmethod
    def _discrete_siso_h2_gain(sys):
        if sys.is_delta() is True:
            sysz = sys.delta2shift()
        else:
            sysz = sys
        return mechatronics.norm_h2_discrete(*sysz.cofs)

    def print_summary(self):

        print('--- Signal Format Information ---')
        # print('Input word length (IW): s(%d,%d)' % (self.iw, self.if_))
        print('Output word length (OW): s(%d,%d)' % (self.output_word_length, self.output_frac_length))
        print('State word length (SW): s(%d,%d)' % (self.state_word_length, self.state_frac_length))
        print('Register word length (RW): s(%d,%d)' % (self.register_word_length, self.register_frac_length))

        # print()
        # for i, n in enumerate(self.state_norms):
        #    print('The norm from input to state x%d is %g' % (i, n))
        #
        # for i, n in enumerate(self.output_norms):
        #    print('The norm from input to output y%d is %g' % (i, n))
        print()

    @staticmethod
    def _variances_shift(sys, var_e):

        mat_a, _, mat_c, _ = sys.cofs

        def variance_single_output(idx):
            c_idx = mat_c[[idx], :]
            a_bar = mat_a
            b_bar = np.hstack((mat_a, np.zeros((sys.n_order, 1))))
            c_bar = c_idx
            d_bar = np.hstack((c_idx, np.ones((1, 1))))
            sigma = np.identity(sys.n_order + 1) * var_e
            wo = mechatronics.observability_gramian_discrete(a_bar, c_bar)
            var_y = np.trace(sigma @ (d_bar.T @ d_bar + b_bar.T @ wo @ b_bar))
            return var_y

        vfunc = np.vectorize(variance_single_output)
        variances = vfunc(np.arange(sys.n_output))
        return variances

    @staticmethod
    def _variances_delta(sys, var_e, var_delta):

        mat_a, _, mat_c, _ = sys.cofs

        def variance_single_output(idx):
            c_idx = mat_c[[idx], :]
            a_bar = np.identity(sys.n_order) + sys.delta * mat_a
            b_bar = np.hstack((mat_a, np.zeros((sys.n_order, 1)), sys.delta * np.identity(sys.n_order)))
            c_bar = c_idx
            d_bar = np.hstack((c_idx, np.ones((1, 1)), np.zeros((1, sys.n_order))))
            sigma = linalg.block_diag(np.identity(sys.n_order + 1) * var_e, np.identity(sys.n_order) * var_delta)
            wo = mechatronics.observability_gramian_discrete(a_bar, c_bar)
            var_y = np.trace(sigma @ (d_bar.T @ d_bar + b_bar.T @ wo @ b_bar))
            return var_y

        vfunc = np.vectorize(variance_single_output)
        variances = vfunc(np.arange(sys.n_output))
        return variances

    def _dynamic_range(self, sys, sf, cf, sys_norm):

        var_e = 1.0 / 12.0 * (2 ** (-sf)) ** 2
        if sys.is_shift():
            variances = self._variances_shift(sys, var_e)
        elif sys.is_delta():
            df = int(math.log(1 / sys.delta, 2))
            exponent = -sf - cf + df
            var_d = 1.0 / 12.0 * (2 ** exponent) ** 2
            variances = self._variances_delta(sys, var_e, var_d)
        else:
            msg = 'This function applies to shift or delta operator systems only.'
            raise ValueError(msg)
        metric = 10 * np.log10(sys_norm ** 2 / np.amax(variances))
        return metric

    @staticmethod
    def state_norms(sys, func):
        """
        A SISO system for each state is created to evaluate the state norms. First, an equivalent single input is made
        where all inputs are equal. Then the output is equal to the selected state. This function returns the norms of
        this set of SISO systems.

        Parameters
        ----------
        sys : controlinverilog.state_space.StateSpace
            The system to evaluate the norms from a combined input to each state.
        func : function: controlinverilog.State->float
            The function to calculate the norm of the SISO systems.

        Returns
        -------
        state_norms : ndarray
            The norms of the system from the combined input to each state.
        """
        a0, b0, c0, d0 = sys.cofs

        def state_system(idx):
            b = b0 @ np.ones((sys.n_input, 1))
            c = np.zeros((1, sys.n_order))
            c[0, idx] = 1
            d = np.zeros((1, 1))
            sys_state = StateSpace((a0, b, c, d), dt=sys.dt, delta=sys.delta)
            return sys_state

        def idx2norm(idx):
            return func(state_system(idx))

        state_norms = np.array(list(map(idx2norm, range(sys.n_order))))
        return state_norms

    @staticmethod
    def output_norms(sys, func):

        a0, b0, c0, d0 = sys.cofs

        def output_system(idx):
            bn = b0 @ np.ones((sys.n_input, 1))
            cn = c0[[idx], :]
            dn = d0[[idx], :] @ np.ones((sys.n_input, 1))
            sys_out = StateSpace((a0, bn, cn, dn), dt=sys.dt, delta=sys.delta)
            return sys_out

        def idx2norm(idx):
            return func(output_system(idx))

        output_norms = np.array(list(map(idx2norm, range(sys.n_output))))
        return output_norms
