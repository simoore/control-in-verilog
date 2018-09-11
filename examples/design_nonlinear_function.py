import controlinverilog as civ
    
func = lambda x: 7.716e-4 / (x + 0.1528) ** 2
nonlinear = civ.NonlinearFunction(func=func, 
                                  iw=11, 
                                  if_=13)
nonlinear.print_summary()
nonlinear.print_verilog('nonlinear_function.v')