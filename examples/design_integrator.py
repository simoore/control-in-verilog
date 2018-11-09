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
