# Control in Verilog

This library provides a set of class to automatically generate verilog code for
a set of common signal processing and control functions.

## Decimator

The decimator reduces the sampling frequency of an input signal.

```
import controlinverilog as civ

decimator = civ.Decimator(freq_in=100e6, 
                          top=9, 
                          dw=16)
                          
decimator.print_summary()
decimator.print_verilog('decimator.v')
```

| parameter | type    | description                                      |
| --------- | ------- | ------------------------------------------------ |
| `freq_in` | float   | The sampling frequency of the input signal.      |
| `top`     | int     | The decimation factor is (top + 1).              |
| `dw`      | int     | The word size of the datapath.                   |

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