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