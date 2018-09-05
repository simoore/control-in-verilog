from math import sqrt
from controlinverilog import NonlinearFunction 
    
x1, y1 = -2 ** -3, 1 - 2 ** -13
x2, y2 = 2 ** -3, 0.01
d0 = (sqrt(y1)*x1 - sqrt(y2)*x2) / (sqrt(y2) - sqrt(y1))
k0 = y1 * (x1  + d0) ** 2
iw = 11
if_ = 13
func = lambda x: k0 / (x + d0) ** 2

hdl_nonlinear = NonlinearFunction(func, iw, if_)
hdl_nonlinear.print_summary()
hdl_nonlinear.print_verilog('nonlinear_function.v')