import controlinverilog as civ
    
iw = 11
if_ = 13
func = lambda x: 7.716e-4 / (x + 0.1528) ** 2

hdl_nonlinear = civ.NonlinearFunction(func, iw, if_)
hdl_nonlinear.print_summary()
hdl_nonlinear.print_verilog('nonlinear_function.v')