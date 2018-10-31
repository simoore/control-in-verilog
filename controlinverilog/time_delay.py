class TimeDelay(object):
    
    def __init__(self, dw, cycles, fclk, verbose):
        """
        :param dw:      The data width of the shift register.
        :param taps:    The number of cycles to delay.
        """
        
        self.cycles = cycles
        self.dw = dw
        self.time = self.cycles / fclk

        if verbose is True:
            print('The time delay is (s): ', self.time)
        

