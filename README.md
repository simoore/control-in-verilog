# Control in Verilog

This library provides a set of class to automatically generate verilog code for
a set of common signal processing and control functions.

## Decimator

```
import controlinverilog as civ

freq_in, top, dw = 100e6, 9, 16

decimator = civ.Decimator(freq_in, top, dw)
decimator.print_summary()
decimator.print_verilog('decimator.v')
```

## Nonlinear Function

```
import controlinverilog as civ
    
iw = 11
if_ = 13
func = lambda x: 7.716e-4 / (x + 0.1528) ** 2

hdl_nonlinear = civ.NonlinearFunction(func, iw, if_)
hdl_nonlinear.print_summary()
hdl_nonlinear.print_verilog('nonlinear_function.v')
```