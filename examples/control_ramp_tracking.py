import numpy as np
import scipy.integrate as integrate
import control
import matplotlib.pyplot as plt
import controlinverilog as civ

def ise(time, error):
    return integrate.trapz(error*error, time)

def ramp_tracking_optimization_tuning_example():
    s = control.TransferFunction.s
    ratio = 0.1
    wn = 2*np.pi*50
    Go = wn**2 / (s*s + 2*ratio*wn*s + wn**2)
    gradient = 6/10e-3
    sim_time=20e-3
    T = np.arange(0.0, sim_time, 1e-5)
    ramp = T*gradient

    def objective(x, metric=ise):
        kp, tz1, tz2, tz3, tp = x
        Co = kp * (tz1*s + 1)*(tz2*s + 1)*(tz3*s + 1) / (s*s*(tp*s + 1))
        So = control.minreal(1/(1+Co*Go), verbose=False)
        T = np.arange(0.0, sim_time, 1e-5)
        ramp = T*gradient
        _, yout = control.forced_response(So, T, U=ramp, squeeze=True)
        return (metric(T, yout)/sim_time,)

    def step_system(xopt, label, ax):
        kp, tz1, tz2, tz3, tp = xopt
        Co = kp * (tz1*s + 1)*(tz2*s + 1)*(tz3*s + 1) / (s*s*(tp*s + 1))
        To = control.minreal(Co*Go/(1+Co*Go), verbose=False)
        _, yout = control.forced_response(To, T, U=ramp, squeeze=True)
        ax.plot(T, yout, label=label)

    fig, ax = plt.subplots()
    ax.plot(T, ramp)
    # Run a first optimization with the itse cost function.
    params = civ.GAOptimizer.AlgorithmParameters(
        cost_function=lambda x: objective(x),
        lower_bounds=[1, 0.001, 0.001, 0.001, 0.001],
        upper_bounds=[50, 1, 1, 1, 1],
        generations=10
    )
    optimizer = civ.GAOptimizer(params)
    optimizer.execute()
    step_system(optimizer.hof[0], 'ise', ax)

    ax.legend()
    fig.tight_layout()
    plt.show()

if __name__ == '__main__':
    ramp_tracking_optimization_tuning_example()