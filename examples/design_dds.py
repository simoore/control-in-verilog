import controlinverilog as civ

dds = civ.DDS(name='example_dds',
              f_exe=122.88e6,
              n_phase=24,
              n_amplitude=16,
              n_sine=8,
              n_fine=6,
              n_fine_word=8)
dds.print_summary()
dds.print_verilog('example_dds.v')

civ.DDS.calc_freqword(n_phase=24, f_exe=122.88e6, f_dds=50e3)
civ.DDS.calc_phase(n_phase=24, angle_deg=90)
