import controlinverilog as civ

freq_in, top, dw = 100e6, 9, 16

decimator = civ.TimeDelay(freq_in, top, dw)
decimator.print_verilog('decimator.v')
