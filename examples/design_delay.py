import controlinverilog as civ

delay = civ.TimeDelay(
    name='example_delay',
    aw=8,
    dw=16
)
delay.print_summary()
delay.print_verilog('example_delay.v')
