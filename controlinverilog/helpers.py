def real2int(val, vf):
    """
    val     The real number to convert to its signed integer representation.
    vf      The fractional length.
    """
    return round(val * 2 ** vf)


def int2verilog(val, vw):
    """
    val     An signed integer to convert to a verilog literal.
    vw      The word length.
    """
    if val < 0:
        val = 2 ** vw + val
    return '%d\'d%s' % (vw, format(val, 'x')) 