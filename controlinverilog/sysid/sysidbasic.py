from re import X
import numpy as np
from scipy import signal as sig
from scipy import optimize as opt

def fitPercent(nominal, observed):
    error = nominal - observed
    rmse = np.sqrt(np.mean(error**2))
    nrmse = rmse / (np.amax(observed) - np.amin(observed))
    return 100*(1 - nrmse)

class TFIdentifier:
    def __init__(self):
        self.tf = None
        self.inputs = None

    def secondOrderLowpassTf(self, k, wn, zeta):
        return sig.TransferFunction(k*(wn**2), [1, 2*zeta*wn, wn**2])

    def secondOrderTf(self, k, wn, delta, alpha):
        return sig.TransferFunction([k*2*alpha*wn, k*(wn**2)], [1, 2*delta*wn, wn**2])

    def firstOrderMdl(self, t, k, pole, offset=0.0):
        self.tf = sig.TransferFunction(k, [pole, 1])
        _, yo, _ = sig.lsim2(self.tf, U=self.inputs, T=t)
        return yo + offset

    def secondOrderMdlLowpass(self, t, k, wn, zeta, offset=0.0):
        self.tf = self.secondOrderLowpassTf(k, wn, zeta)
        _, yo, _ = sig.lsim2(self.tf, U=self.inputs, T=t)
        return yo + offset

    def secondOrderMdl(self, t, k, wn, delta, alpha, offset=0.0):
        self.tf = self.secondOrderTf(k, wn, delta, alpha)
        _, yo, _ = sig.lsim2(self.tf, U=self.inputs, T=t)
        return yo + offset

    def identifyFirstOrder(self, t, u, y, method='lm', p0=[1.0, 1.0, 0.0]):
        self.inputs = u
        params, params_cov = opt.curve_fit(self.firstOrderMdl, t, y, method=method, maxfev=1000, p0=p0)
        return {'k': params[0], 'tau': params[1]}

    def identifySecondOrderLowpass(self, t, u, y, p0=[1.0, 1.0, 0.1, 10], method='lm'):
        self.inputs = u
        popt, pcov = opt.curve_fit(self.secondOrderMdlLowpass, t, y, method=method, maxfev=1000, p0=p0)
        return {'k': popt[0], 'wn': popt[1], 'zeta': popt[2], 'offset': popt[3]}

    def identifySecondOrder(self, t, u, y, method='lm', p0=[1.0, 1.0, 0.1, 0.1, 10, 0.1]):
        self.inputs = u
        popt, pcov = opt.curve_fit(self.secondOrderMdl, t, y, method=method, maxfev=1000, p0=p0)
        return {'k': popt[0], 'wn': popt[1], 'zetaDen': popt[2], 'zetaNum': popt[3], 'offset': popt[4]}
