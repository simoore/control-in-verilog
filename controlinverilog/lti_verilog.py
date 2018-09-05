from math import ceil
import veriloggen as vg
import string


class LtiVerilog:
    
    
    def __init__(self, lti, stages=1):
        """Contructs the verilog code implementing an LTI system. The generated 
        code is output to the console.
        
        Parameters
        ----------
        lti : LtiSystem
            The structure containing the parameters of the LTI system.
        stages : int
            The length of the pipelined in the adder for the matrix 
            multiplications.
        """
        
        self._stages = stages
        
        # add verilog components
        self.init_statements = []
        self._add_header(lti)
        self._add_input_buffer(lti)
        self._add_multiplier_buffer(lti)
        self._add_adder_buffer(lti)
        self._add_output_assignments(lti)
        self._add_delta_operator(lti)
        self.mod.Initial(self.init_statements)
        
        # generate verilog code
        self.verilog = self.mod.to_verilog()
        
        
    def _add_header(self, lti):

        # module header
        self.mod = vg.core.module.Module(lti.name)
    
        # parameters
        self.iw = self.mod.Parameter('IW', lti.iw)
        self.ow = self.mod.Parameter('OW', lti.ow)
        self.cw = self.mod.Parameter('CW', lti.cw)
        self.sw = self.mod.Parameter('SW', lti.sw)
        self.rw = self.mod.Parameter('RW', self.sw + self.cw - 1)
        self.cf = self.mod.Parameter('CF', lti.cf)
        self.del_par = self.mod.Parameter('DEL', lti.del_par)
        
        # input and output signals
        self.clk = self.mod.Input('clk')
        self.ce_in = self.mod.Input('ce_in')
        self.sig_in = self._add_inputs(lti.ninputs)
        self.ce_out = self.mod.OutputReg('ce_out')
        self.sig_out = self._add_outputs(lti.noutputs) 
            
        # add registers to module
        self.ce_mul = self.mod.Reg('ce_mul')
        self.ce_buf = self.mod.Reg('ce_buf')
        
        self.ureg = self._add_registers(lti.ninputs, 'u', self.sw)
        self.xreg = self._add_registers(lti.order, 'x', self.sw)
        self.x_long = self._add_registers(lti.order, 'x_long', self.rw)
        self.y_long = self._add_registers(lti.noutputs, 'y_long', self.rw)
        self.dx = self._add_registers(lti.order, 'dx', self.rw)
        
        # Add pipeline registers.
        self.ce_add = [None for _ in range(self._stages - 1)]
        self.dxs = [None for _ in range(self._stages - 1)]
        self.ylongs = [None for _ in range(self._stages - 1)]
        ind = list(string.ascii_uppercase)
        for i in range(self._stages - 1):
            name1 = ''.join(('ce_add_', ind[i]))
            self.ce_add[i] = self.mod.Reg(name1)
            name2 = ''.join(('dx', ind[i], '_'))
            self.dxs[i] = self._add_registers(lti.order, name2, self.rw)
            name3 = ''.join(('ylong', ind[i], '_'))
            self.ylongs[i] = self._add_registers(lti.noutputs, name3, self.rw)
        
    
        self.ax, self.acof = self._add_matrix(lti.A, 'A', 'ax', self.xreg)
        self.bu, self.bcof = self._add_matrix(lti.B, 'B', 'bu', self.ureg)
        self.cx, self.ccof = self._add_matrix(lti.C, 'C', 'cx', self.xreg)
        self.du, self.dcof = self._add_matrix(lti.D, 'D', 'du', self.ureg)

        
    def _add_inputs(self, num):

        name = 'sig_in'
        wid = self.iw
        u = [None for _ in range(num)]
        for i in range(num):
            n = ''.join([name, str(i + 1)])
            u[i] = self.mod.Input(n, wid)
        return u   
    
    
    def _add_outputs(self, num):

        name = 'sig_out'
        wid = self.ow
        u = [None for _ in range(num)]
        for i in range(num):
            n = ''.join([name, str(i + 1)])
            u[i] = self.mod.Output(n, wid)
        return u
    
    
    def _add_registers(self, num, name, wid):
        
        regs = [None for _ in range(num)]
        for i in range(num):
            n = ''.join([name, str(i + 1)])
            regs[i] = self.mod.Reg(n, width=wid, initval=0, signed=True)
            self.init_statements.append(regs[i].write(0))
        return regs
    
        
    def _add_matrix(self, mat, par_name, reg_name, inp):
    
        rows, cols = mat.shape
        a = [[None for _ in range(cols)] for _ in range(rows)]
        u = [[None for _ in range(cols)] for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                n1 = ''.join([par_name, str(r + 1), '_', str(c + 1)])
                n2 = ''.join([reg_name, str(r + 1), '_', str(c + 1)])
                val = int(mat[r,c])
                a[r][c] = self.mod.Parameter(n1, val, signed=True, width=self.cw)
                u[r][c] = self.mod.Reg(n2, width=self.rw, initval=0, signed=True)
                self.init_statements.append(u[r][c].write(0))
        return u, a   


    def _add_input_buffer(self, lti):
        """Adds the input buffer to the verilog module. The input buffer sign 
        extends the input to an internal data width and truncates the previous 
        state for use in the next iteration of the LTI system.
        
        Parameters
        ----------
        lti : LtiSystem
            The parameters of the LTI system.
        """
        inp_buf = vg.seq.seq.Seq(self.mod, 'input_buffer', self.clk)
        inp_buf.add(self.ce_buf.write(self.ce_in))
        ureg_statements = [None for _ in range(lti.ninputs)]
        xreg_statements = [None for _ in range(lti.order)]
        upper = self.sw + self.cf - 1
        for i in range(lti.ninputs):
            signed_sig_in = vg.core.vtypes.SystemTask('signed', self.sig_in[i])
            ureg_statements[i] = self.ureg[i].write(signed_sig_in)
        for i in range(lti.order):
            x_long_slice = vg.core.vtypes.Slice(self.x_long[i], upper, self.cf)
            xreg_statements[i] = self.xreg[i].write(x_long_slice)
        statements = ureg_statements + xreg_statements
        inp_buf.If(self.ce_in).add(statements)
        
        
    def _add_multiplier_buffer(self, lti):
        """Adds the multiplication buffer to the verilog module.
        
        Parameters
        ----------
        lti : LtiSystem
            The parameters of the LTI system.
        """
        mul_buf = vg.seq.seq.Seq(self.mod, 'multiplier_buffer', self.clk)
        mul_buf.add(self.ce_mul.write(self.ce_buf))
        bufs = [self.ax, self.bu, self.cx, self.du]
        cofs = [self.acof, self.bcof, self.ccof, self.dcof]
        inps = [self.xreg, self.ureg, self.xreg, self.ureg]
        for buf, cof, inp in zip(bufs, cofs, inps):
            for br, cr in zip(buf, cof):
                for b, c, i in zip(br, cr, inp):
                    mul_buf.add(b.write(c * i)) 
    
    
    def _add_adder_buffer(self, lti):
        """Adds the adder buffer to the verilog module.
        
        Parameters
        ----------
        lti : LtiSystem
            The parameters of the LTI system.
        """
        
        add_total = (lti.order + lti.ninputs + self._stages - 1) 
        add_per_stage = ceil(add_total / self._stages)
        state_stages = [x // (add_per_stage-1) for x in range(lti.order-1)]
        input_stages = [x // (add_per_stage-1) for x in 
                        range(lti.order-1, lti.order-1 + lti.ninputs)]
        ls = self._stages - 1
        
        
        # add register
        add_buf = vg.seq.seq.Seq(self.mod, 'addition_buffer', self.clk)
        
        for k in range(self._stages):
            
            input_ce = self.ce_mul if k == 0 else self.ce_add[k-1]
            output_ce = self.ce_out if k == ls else self.ce_add[k]
            add_buf.add(output_ce.write(input_ce))
            state_ind = [j + 1 for j, s in enumerate(state_stages) if s == k]
            input_ind = [j for j, s in enumerate(input_stages) if s == k]
            
            # For state equation.
            for i in range(lti.order):
                state_terms = [self.ax[i][j] for j in state_ind]
                input_terms = [self.bu[i][j] for j in input_ind] 
                init_term = self.ax[i][0] if k == 0 else self.dxs[k-1][i]
                addition = sum(state_terms + input_terms, init_term)
                reg = self.dx[i] if k == ls else self.dxs[k][i]
                add_buf.add(reg.write(addition))
        
            # For output equation.
            for i in range(lti.noutputs):
                state_terms = [self.cx[i][j] for j in state_ind]
                input_terms = [self.du[i][j] for j in input_ind] 
                init_term = self.cx[i][0] if k == 0 else self.ylongs[k-1][i]
                addition = sum(state_terms + input_terms, init_term)
                reg = self.y_long[i] if k == ls else self.ylongs[k][i]
                add_buf.add(reg.write(addition))

        
    def _add_output_assignments(self, lti):
        """Adds the assign statements truncating the LTI system output.
        
        Parameters
        ----------
        lti : LtiSystem
            The parameters of the LTI system.
        hdl : LtiVerilog
            The set of veriloggen objects composing the verilog module.
        """
        upper = self.ow + self.cf - 1
        for i in range(lti.noutputs):
            y_long_slice = vg.core.vtypes.Slice(self.y_long[i], upper, self.cf)
            self.mod.Assign(self.sig_out[i](y_long_slice))
    
            
    def _add_delta_operator(self, lti):
        """Adds a register implementing the delta operator to the verilog module.
        
        Parameters
        ----------
        lti : LtiSystem
            The parameters of the LTI system.
        """
        operator = vg.seq.seq.Seq(self.mod, 'delta_operator', self.clk)
        statements = [None for _ in range(lti.order)]
        for i in range(lti.order):
            dx_slice = vg.core.vtypes.Slice(self.dx[i], self.rw - 1, self.del_par)
            signed_d = vg.core.vtypes.SystemTask('signed', dx_slice)
            statements[i] = self.x_long[i].write(self.x_long[i] + signed_d)
        operator.If(self.ce_out).add(statements)   
        
        
    def print_verilog(self, filename=None):
        if filename is None:
            print(self.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.verilog)
            