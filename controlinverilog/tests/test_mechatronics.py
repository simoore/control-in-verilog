import numpy as np
from controlinverilog import mechatronics
import matplotlib.pyplot as plt

A = np.array([[0.9688, 0.2048], [-0.2048, 0.9678]])
B = np.array([[-0.4007], [-0.325]])
C = np.array([[-0.4007,   0.325]])
D = [[0.01396]]
sys = (A, B, C, D)
dt = 1/30e3
    
    
def test_norm_functions():
    
    norm_inf = mechatronics.norm_hinf_discrete_siso(sys)
    #norm_infa = mechatronics.norm_hinf_discrete(sys)
    norm_2 = mechatronics.norm_h2_discrete_siso(sys)
    norm_2a = mechatronics.norm_h2_discrete(sys)
    
    print(norm_inf, norm_2, norm_2a)
    
    
def test_step_info():
    t, y = mechatronics.step_response(sys, dt)
    print(t[1]-t[0])
    plt.plot(t, y)
    ans = mechatronics.overshoot(sys, dt)
    print(ans)
    
if __name__ == '__main__':
    test_step_info()
    