def real2int(val, vf):
    """
    :param val:     The real number to convert to its signed integer 
                    representation.
    :param vf:      The fractional length.
    """
    return round(val * 2 ** vf)


def int2verilog(val, vw):
    """
    :param val: A signed integer to convert to a verilog literal.
    :param vw:  The word length of the constant value.
    """
    sign = '-' if val < 0 else ''
    s = ''.join((sign, str(vw), '\'sd', str(abs(val))))
    return s
