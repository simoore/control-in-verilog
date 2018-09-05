class TimeDelay(object):
    
    def __init__(self, dw, cycles, fclk):
        """
        :param dw:      The data width of the shift register.
        :param taps:    The number of cycles to delay.
        """
        
        self.cycles = cycles
        self.dw = dw
        self.time = self.cycles / fclk
        
        print('The time delay is:', self.time)
        

