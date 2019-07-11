import unittest
import numpy as np
from controlinverilog import mechatronics
from controlinverilog.state_space import StateSpace
import controlinverilog as civ
import matplotlib.pyplot as plt


class TestLtiSystem(unittest.TestCase):

    def test_sequence(self):
        sys1 = get_system1()

        norm_infc = mechatronics.norm_hinf_discrete(*sys1.cofs)
        norm_2c = mechatronics.norm_h2_discrete(*sys1.cofs[:3])
        self.assertTrue(abs(norm_infc - 12.9998) / 12.9998 < 0.01)
        self.assertTrue(abs(norm_2c - 1.3232) / 1.3232 < 0.01)

        # print('sysa Inf Norm: %g' % norm_infc)
        # print('sysa 2 Norm: %g' % norm_2c)

        sysa = get_system2()

        norm_infc = mechatronics.norm_hinf_continuous(*sysa.cofs)
        norm_2c = mechatronics.norm_h2_continuous(*sysa.cofs[:3])
        self.assertTrue(abs(norm_infc - 0.9999) < 0.0001)
        self.assertTrue(abs(norm_2c - 75.1826) / 75.1826 < 0.0001)

        # print('sysa Inf Norm: %g' % norm_infc)
        # print('sysa 2 Norm: %g' % norm_2c)

        sysd = sysa.cont2shift(1 / 122.88e6)

        norm_infc = mechatronics.norm_hinf_discrete(*sysd.cofs)
        norm_2c = mechatronics.norm_h2_discrete(*sysd.cofs[:3])
        self.assertTrue(abs(norm_infc - 0.9999) < 0.0001)
        self.assertTrue(abs(norm_2c - 0.00678229) / 0.00678229 < 0.0001)

        # print('sysd Inf Norm: %g' % norm_infc)
        # print('sysd 2 Norm: %g' % norm_2c)

    def test_gramians(self):
        sysa = get_system2()
        A, B, C, D = sysa.cofs
        Wc = mechatronics.controllability_gramian_continuous(A, B)
        Wo = mechatronics.observability_gramian_continuous(A, C)

        cWc = np.array(
            [[6.999969e-01, 1.114907e-05, 2.368522e-06, -1.562850e-06],
             [1.114907e-05, 2.353370e-01, -2.539451e-06, 6.104784e-07],
             [2.368522e-06, -2.539451e-06, 3.775594e-02, 2.332329e-07],
             [-1.562850e-06, 6.104784e-07, 2.332329e-07, 2.452912e-03]])
        cWo = np.array(
            [[6.999969e-01, -1.114907e-05, 2.368522e-06, 1.562850e-06],
             [-1.114907e-05, 2.353370e-01, 2.539451e-06, 6.104784e-07],
             [2.368522e-06, 2.539451e-06, 3.775594e-02, -2.332329e-07],
             [1.562850e-06, 6.104784e-07, -2.332329e-07, 2.452912e-03]])
        self.assertTrue(np.all(np.isclose(cWc, Wc, rtol=1e-5)))
        self.assertTrue(np.all(np.isclose(cWo, Wo, rtol=1e-5)))

        sysd = sysa.cont2shift(1 / 122.88e6)
        A, B, C, D = sysd.cofs
        Wc = mechatronics.controllability_gramian_discrete(A, B)
        Wo = mechatronics.observability_gramian_discrete(A, C)

        dWc = np.array(
            [[5.696589e-09, 9.073142e-14, 1.927509e-14, -1.271850e-14],
             [9.073142e-14, 1.915178e-09, -2.066611e-14, 4.968086e-15],
             [1.927509e-14, -2.066611e-14, 3.072586e-10, 1.898054e-15],
             [-1.271850e-14, 4.968086e-15, 1.898054e-15, 1.996185e-11]])
        dWo = np.array(
            [[8.601562e+07, -1.369998e+03, 2.910440e+02, 1.920430e+02],
             [-1.369998e+03, 2.891821e+07, 3.120477e+02, 7.501562e+01],
             [2.910440e+02, 3.120477e+02, 4.639449e+06, -2.865966e+01],
             [1.920430e+02, 7.501562e+01, -2.865966e+01, 3.014138e+05]])
        self.assertTrue(np.all(np.isclose(dWc, Wc, rtol=1e-5)))
        self.assertTrue(np.all(np.isclose(dWo, Wo, rtol=1e-5)))

    def test_cont2shift(self):
        sysa = get_system2()
        sysd = sysa.cont2shift(1 / 122.88e6)
        Ad = np.array([[1, 0.000113, 4.483e-05, -1.69e-05],
                       [-0.000113, 0.9999, -0.0002071, 6.131e-05],
                       [4.483e-05, 0.0002071, 0.9997, 0.0002602],
                       [1.69e-05, 6.131e-05, -0.0002602, 0.9993]])
        Bd = np.array([[-5.879e-07], [-7.271e-07], [4.579e-07], [1.632e-07]])
        Cd = np.array([[-72.24, 89.35, 56.26, -20.05]])
        Dd = np.array([[9.993e-12]])
        A, B, C, D = sysd.cofs
        self.assertTrue(np.all(np.isclose(Ad, A, rtol=1e-3)))
        self.assertTrue(np.all(np.isclose(Bd, B, rtol=1e-3)))
        self.assertTrue(np.all(np.isclose(Cd, C, rtol=1e-3)))
        self.assertTrue(np.all(np.isclose(Dd, D, rtol=1e-3)))


def get_system1():
    A = np.array([[0.9688, 0.2048], [-0.2048, 0.9678]])
    B = np.array([[-0.4007], [-0.325]])
    C = np.array([[-0.4007, 0.325]])
    D = np.array([[0.01396]])
    dt = 1 / 30e3
    sys = StateSpace((A, B, C, D), dt=dt)
    return sys


def get_system2():
    A = 1.0e+04 * np.array([
        [-0.3728, 1.3891, 0.5511, -0.2078],
        [-1.3891, -1.6962, -2.5451, 0.7540],
        [0.5511, 2.5451, -4.1947, 3.1990],
        [0.2078, 0.7540, -3.1990, -8.2078]])
    B = np.array([[-72.2415], [-89.3518], [56.2813], [20.0667]])
    C = np.array([[-72.2415, 89.3518, 56.2813, -20.0667]])
    D = np.array([[0.0]])
    return StateSpace((A, B, C, D))


if __name__ == '__main__':
    unittest.main()
    # test_norm_functions()
