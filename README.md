# Control in Verilog

This library provides a set of class to automatically generate verilog code for
a set of common signal processing and control functions.

## Direct Digital Synthesizer (DDS)

A DDS outputs sine and cosine waves. The system uses a phase accummulator convert
a frequency word to phase. The phase is converted to a sine wave using a LUT. 
Circular interpolation is used to increase the purity of the sine wave.

The DDS module has two static functions to assist in determining values for the
frequency word and phase offset.

```
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
```

| parameter     | type   | description                                      |
| ------------- | ------ | ------------------------------------------------ |
| `name`        | string | The name of the module.                          |
| `f_exe`       | float  | The frequency of the system clock.               |
| `n_phase`     | int    | The word length of the phase accummulator.       |
| `n_amplitude` | int    | The word length of the course LUT.               |
| `n_sine`      | int    | The size of the course LUT.                      |
| `n_fine`      | int    | The size length of the fine LUT.                 |
| `n_fine_word` | int    | The word length of the fine LUT.                 |


The system clock is usually at a fixed frequency, this makes the frequency and 
phase resolution a function of `n_phase`. `n_ampltiude`, `n_fine_word`, 
`n_sine`, and `n_fine` set the size of the LUT used to generate the sine wave.
Increasing these variables increases the purity of the sine wave at the 
expense of memory consumption.

## Decimator

The decimator reduces the sampling frequency of an input signal.

```
import controlinverilog as civ

decimator = civ.Decimator(freq_in=100e6,
                          top=9,
                          dw=16)
decimator.print_summary()
decimator.print_verilog('example_decimator.v')
```

| parameter | type    | description                                      |
| --------- | ------- | ------------------------------------------------ |
| `name`    | string  | The name of the module.                          |
| `freq_in` | float   | The sampling frequency of the input signal.      |
| `top`     | int     | The decimation factor is (top + 1).              |
| `dw`      | int     | The word size of the datapath.                   |


## Integrator

An integral control with anti-windup.

```
import controlinverilog as civ

integrator = civ.Integrator(
    gain=3000,
    ts=1.0/1.0e6,
    dw=24,
    df=22,
    cw=16,
    cf=16,
    min_=-1.5,
    max_=1.5,
    name='example_integrator'
)
integrator.print_summary()
integrator.print_verilog('example_integrator.v')
```

| parameter | type    | description                                      |
| --------- | ------- | ------------------------------------------------ |
| gain      | float   | The analog integral gain.                        |
| ts        | float   | The sampling period.                             |
| dw        | int     | The signal word length.                          |
| df        | int     | The signal fractional length.                    |
| cw        | int     | The coefficient word length.                     |
| cf        | int     | The coefficient fractional length.               |
| min_      | float   | The minimum analog saturation value.             |
| max_      | float   | The maximum analog saturation value.             |
| name      | string  | The name of the verilog module.                  |
        
## LTI System

A module that implements an asymtotically stable linear time invariant 
state space system. The module takes a continuous time state space system
and produces the coffieicents, logic, word-lengths for a verilog 
discretization of the system. 

The continuous time system in the example below is a low pass filter.

```
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
```

| parameter          | type    | description                                      |
| ------------------ | ------- | ------------------------------------------------ |
| name               | string  | The module name.                                 |
| fs                 | float   | The sampling frequency.                          |
| sys                | tuple   | The continuous state space system (A,B,C,D).     |
| operator           | string  | 'delta', or 'shift'.                             |
| input_word_length  | int     | The input word length.                           |
| input_frac_length  | int     | The input fractional length.                     |
| cof_word_length    | int     | The coefficient word length when fixed.          |
| cof_frac_length    | int     | The coefficient fractional length when fixed.    |
| n_add              | int     | The maximum number of additions per cycle.       |
| cof_threshold      | float   | A metric to set the coefficient format.          |
| sig_threshold      | float   | A metric to set the state and output formats.    |
| sig_scaling_method | string  | 'hinf', 'h2', 'overshoot', or 'safe'.            |
| cof_scaling_method | string  | 'hinf', 'h2', 'pole', 'impulse, or 'fixed'.      | 
| verbose            | bool    | To print information to console.                 |

Coefficient format selection method: The range of the format is selected to
accommodate the largest discrete time coefficient and the resolution is selected
to minimize some measure of error between the unquantized and quantized system. The
measures of error are:

* The h-infinity norm - `hinf` 
* The h-2 norm - `h2` 
* Magnitude difference between poles - `pole`
* l-2 norm of the impulse response - `impulse`

Since the error should be small, `cof_threshold` is a small value. The `fixed` 
method allows the coefficient format to be specified directly.

Signal format selection method: The range of the format is selected to account for 
the gain of the system both to the outputs and the states. The measures of gain are:

* The h-infinity norm - `hinf` 
* The h-2 norm - `h2` 
* Maximum of the absolute value of the step response - `overshoot`
* An upper bound on the signal - `safe`

The resolution of the format is selected to ensure the dynamic range of the 
respresentation is above a threshold in dB. Therefore `sig_threshold` needs
to be a large number.

## Nonlinear Function

Implements a nonlinear function using a LUT and linear interpolation.
An entry in the LUT exists of all valid inputs.

```
import controlinverilog as civ

func = lambda x: 7.716e-4 / (x + 0.1528) ** 2
nonlinear = civ.NonlinearFunction(
    name='example_nonlinear_function',
    func=func,
    input_word_length=11,
    input_frac_length=13
)
nonlinear.print_summary()
nonlinear.print_verilog('example_nonlinear_function.v')
```

| parameter         | type     | description                                      |
| ----------------- | -------- | ------------------------------------------------ |
| name              | string   | The module name.                                 |
| func              | function | The function to implement                        |
| input_word_length | int      | The input word length.                           |
| input_frac_length | int      | The signal fractional length.                    |

## Saturation

Saturation reduces the word length of the signal by limiting the range and removing
a number of the most significant bits. The fractional length of the output is the
same as the input.

```
import controlinverilog as civ

saturation = civ.Saturation(name='example_saturation',
                            input_word_length=22,
                            input_frac_length=10,
                            output_word_length=16)
saturation.print_summary()
saturation.print_verilog('example_saturation.v')
```

| parameter            | type   | description                                         |
| -------------------- | ------ | --------------------------------------------------- |
| `name`               | string | The name of the verilog module.                     |
| `input_word_length`  | int    | The word length of the input signal.                |
| `input_frac_length`  | int    | The fractional length of the signal.                |
| `output_word_length` | int    | The reduced word length of the signal.              |

## Time Delay

The time delay implements a cicular buffer for realizing time delays. The delay in
module is variable, set by an input signal. Upon power up and change in the delay,
the output signal is undefined until the buffer is full. The size of the buffer,
and thus the maximum delay, is set by the `aw` parameter.

```
import controlinverilog as civ

delay = civ.TimeDelay(
    name='example_delay',
    aw=8,
    dw=16
)
delay.print_summary()
delay.print_verilog('example_delay.v')
```

| parameter | type   | description                                         |
| --------- | ------ | --------------------------------------------------- |
| `name`    | string | The name of the verilog module.                     |
| `aw`      | int    | The word length of the delay signal.                |
| `dw`      | int    | The word length of the data signal.                 |
