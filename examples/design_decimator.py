import controlinverilog as civ

decimator = civ.Decimator(name='example_decimator',
                          freq_in=100e6,
                          top=9,
                          dw=16)
decimator.print_summary()
decimator.print_verilog('example_decimator.v')
