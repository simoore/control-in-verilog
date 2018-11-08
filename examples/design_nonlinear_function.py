import controlinverilog as civ


func = lambda x: 7.716e-4 / (x + 0.1528) ** 2
nonlinear = civ.NonlinearFunction(name='example_nonlinear_function',
                                  func=func,
                                  input_word_length=11,
                                  input_frac_length=13)
nonlinear.print_summary()
nonlinear.print_verilog('example_nonlinear_function.v')
