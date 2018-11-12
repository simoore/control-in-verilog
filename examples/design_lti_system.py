import numpy as np
import controlinverilog as civ

A = 1.0e+04 * np.array([
    [-0.3728,    1.3891,    0.5511,   -0.2078],
    [-1.3891,   -1.6962,   -2.5451,    0.7540],
    [ 0.5511,    2.5451,   -4.1947,    3.1990],
    [ 0.2078,    0.7540,   -3.1990,   -8.2078]
])
B = np.array([[-72.2415], [-89.3518], [56.2813], [20.0667]])
C = np.array([[-72.2415,   89.3518,   56.2813,  -20.0667]])
D = [[0.0]]

lti = civ.LtiSystem(
    name='example_lti_system',
    fs=122.88e6,
    sys=(A, B, C, D),
    operator='delta',
    input_word_length=16,
    input_frac_length=14,
    cof_word_length=16,
    cof_frac_length=15,
    n_add=3,
    cof_threshold=0.001,
    sig_threshold=100,
    sig_scaling_method='hinf',
    cof_scaling_method='hinf',
    verbose=True
)
lti.print_verilog('example_lti_system.v')
