import controlinverilog as civ
import numpy as np

length = 8192
N = length - 1
x = np.arange(1250)
pad = (length - 2500) / 2
hann = 0.5 * (1 - np.cos(2*np.pi*(x + pad)/N))
lut = civ.LookUpTable(
    name='example_hann_function',
    values=hann,
    values_frac_length=12
)
lut.print_summary()
lut.print_verilog('example_hann_function.sv')
