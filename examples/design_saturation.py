import controlinverilog as civ

saturation = civ.Saturation(name='example_saturation',
                            input_word_length=22,
                            input_frac_length=10,
                            output_word_length=16,
                            verbose=True)
saturation.print_verilog('example_saturation.v')
