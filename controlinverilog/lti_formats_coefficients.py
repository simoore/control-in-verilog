import math
import itertools
import numpy as np
from . import mechatronics


class LtiFormatsCoefficients(object):

    def __init__(self, system, params):
        """
        This class selects the word and fractional lengths of the coefficients for an LTI system to be implemented with
        fixed point arithmetic.

        Parameters
        ----------
        system : controlinverilog.state_space.StateSpace
            This system contains the coefficients to be stored in a fixed point format.
        params : dictionary
            This dictionary contains the following relevent parameters:
            - cof_scaling_method: 'hinf' | 'h2' | 'impulse' | 'pole' | 'fixed'.
            - cof_word_length: The word length for the 'fixed' method.
            - cof_frac_length: The fractional length for the 'fixed' method.
            - cof_threshold: The bound on the error between the quantized and unquantized systems.
        """

        method = params['cof_scaling_method']
        metric = self._select_cof_scaling_method(method)

        if metric is None:
            self._cw = params['cof_word_length']
            self._cf = params['cof_frac_length']
        else:
            self._threshold = params['cof_threshold']
            self._cw, self._cf = self._set_coefficient_format(metric, system)

    @property
    def cof_word_length(self):
        return self._cw

    @property
    def cof_frac_length(self):
        return self._cf

    def _select_cof_scaling_method(self, method):

        funcs = {'hinf': self.metric_hinf,
                 'h2': self.metric_h2,
                 'pole': self.metric_pole,
                 'impulse': self.metric_impulse,
                 'fixed': None}

        if method not in funcs:
            vals = ' | '.join(funcs.keys())
            msg = 'Valid cof_scaling_method values: %s.' % vals
            raise ValueError(msg)

        metric = funcs[method]
        return metric

    def _set_coefficient_format(self, metric, sys):
        """
        This function selects the coefficient word and fractional lengths.
        """

        # Find the largest coefficient to determine the location of the most
        # significant bit.
        max_param = max(map(lambda x: np.amax(np.abs(x)), sys.cofs[:3]))
        int_w = math.ceil(math.log2(max_param))

        def eval_metric(cf):
            # scale = 2 ** cf
            # func = lambda mat: np.around(scale * mat) / scale
            # sys_q = sys.transform_params(func)
            sys_q = sys.quantized_system(cf)
            met = metric(sys, sys_q)
            return met

        # Find the location of the least significant bit.
        flt = filter(lambda cf: eval_metric(cf) < self._threshold, itertools.count(1 - int_w))

        cf_ = next(flt)
        cw = 1 + int_w + cf_

        return cw, cf_

    def print_summary(self):

        print('--- Coefficient Format Information ---')
        print('Coefficient format: s(%d,%d)' % (self.cof_word_length, self.cof_frac_length))
        print()

    ####################################################################################################################
    # Metrics that measure the difference between two system.
    ####################################################################################################################
    @staticmethod
    def metric_h2(sys, sys_q):

        sys_diff = sys - sys_q
        if np.any(sys_diff.poles() == 0.0):
            return np.inf
        a = mechatronics.norm_h2_discrete(*sys_diff.cofs)
        b = mechatronics.norm_h2_discrete(*sys.cofs)
        return a / b

    @staticmethod
    def metric_hinf(sys, sys_q):

        sys_diff = sys - sys_q
        if np.any(sys_diff.poles() == 0.0):
            return np.inf
        a = mechatronics.norm_hinf_discrete(*sys_diff.cofs)
        b = mechatronics.norm_hinf_discrete(*sys.cofs)
        return a / b

    @staticmethod
    def metric_pole(sys, sys_q):
        """
        Calculates the maximum difference between the poles of the system and its quantized version.
        """
        poles = sys.poles()
        poles_q = sys_q.poles()
        metric = 0
        for ii in range(sys.n_order):
            diff_vec = np.abs(poles[ii] - poles_q) / np.abs(poles[ii])
            idx = np.argmin(diff_vec)
            if metric < diff_vec[idx]:
                metric = diff_vec[idx]
            poles_q = np.delete(poles_q, idx)
        return metric

    @staticmethod
    def metric_impulse(sys, sys_q):
        """
        The size of the impulse is measured using the l2 norm. This metric only considers SISO systems.
        """
        if not sys.is_siso():
            message = 'cof_scaling_method `impulse` only for SISO systems.'
            raise ValueError(message)
        sys_diff = sys - sys_q
        _, y = sys.discrete_siso_impulse_response(n_tc=20.0)
        _, yd = sys_diff.discrete_siso_impulse_response(n_tc=20.0)
        y, yd = y[0], yd[0]
        return np.sqrt(np.sum(yd * yd) / np.sum(y * y))

    # @staticmethod
    # def impulse_response(sys, n_tc=7):
    #     """
    #
    #     :param n_tc:
    #     :return:
    #     """
    #     A, B, C, D = sys.params
    #     if sys.delta is not None:
    #         A, B = (np.identity(sys.n_order) + sys.delta * A), sys.delta * B
    #     ev, _ = linalg.eig(A)
    #     tc = time_constant(sys, sys.dt)
    #     n = round(n_tc * tc / sys.dt)
    #     t, y = signal.dstep((A, B, C, D, sys.dt), n=n)
    #     return t, np.squeeze(y)
