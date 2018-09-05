import controlinverilog as civ

civ.test_func()
dds = civ.DDS('modulator_dds')
dds.calc_freqword()
dds.calc_phase()
dds.generate_sine_lut()
dds.generate_fine_lut()

