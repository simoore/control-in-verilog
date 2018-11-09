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
