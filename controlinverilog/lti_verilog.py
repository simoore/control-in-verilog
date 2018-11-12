import math
import numpy as np
import jinja2


class LtiVerilog(object):

    def __init__(self, sys, params):

        self.cache = {}
        self.order = sys.n_order
        self.n_inputs = sys.n_input
        self.n_outputs = sys.n_output
        self.n_add = params['n_add']
        self.context = {'name': params['name'],
                        'iw': params['iw'],
                        'ow': params['ow'],
                        'sw': params['sw'],
                        'cw': params['cw'],
                        'cf': params['cf'],
                        'if_': params['if'],
                        'sf': params['sf'],
                        'del': params['del_par']}

        mat_a, mat_b, mat_c, mat_d = sys.cofs
        self.gen_header()
        self.gen_matrix(mat_a, 'A', 'ax', 'x')
        self.gen_matrix(mat_b, 'B', 'bu', 'u')
        self.gen_matrix(mat_c, 'C', 'cx', 'x')
        self.gen_matrix(mat_d, 'D', 'du', 'u')
        self.gen_adder_ce()
        self.gen_adder('state')
        self.gen_adder('output')

        loader = jinja2.PackageLoader('controlinverilog', 'templates')
        env = jinja2.Environment(loader=loader,
                                 trim_blocks=True,
                                 lstrip_blocks=True)
        template = env.get_template('lti_system.v')
        self.verilog = template.render(self.context)

    def gen_header(self):

        ind_in = np.arange(self.n_inputs)
        ind_out = np.arange(self.n_outputs)
        ind_order = np.arange(self.order)

        def name_signal(name, index):
            return '_'.join((name, str(index + 1)))

        vfunc = np.vectorize(name_signal)
        sig_in = vfunc('sig_in', ind_in)
        sig_out = vfunc('sig_out', ind_out)
        sig_u = vfunc('u', ind_in)
        sig_x_long = vfunc('x_long', ind_order)
        sig_x = vfunc('x', ind_order)
        sig_dx = vfunc('dx', ind_order)
        sig_y_long = vfunc('y_long', ind_out)

        self.context['sig_in'] = sig_in
        self.context['sig_out'] = sig_out
        self.context['sig_u'] = sig_u
        self.context['sig_x_long'] = sig_x_long
        self.context['sig_x'] = sig_x
        self.context['sig_dx'] = sig_dx
        self.context['sig_y_long'] = sig_y_long

        input_buffers = zip(sig_u, sig_in)
        state_buffers = zip(sig_x, sig_x_long)
        outputs = zip(sig_out, sig_y_long)
        deltas = zip(sig_x_long, sig_dx)

        self.context['input_buffers'] = input_buffers
        self.context['state_buffers'] = state_buffers
        self.context['outputs'] = outputs
        self.context['deltas'] = deltas

    def gen_matrix(self, mat, par_name, reg_name, inp_name):

        params = np.empty(mat.shape, dtype=object)
        registers = np.empty(mat.shape, dtype=object)
        products = np.empty(mat.shape, dtype=object)

        for r, c in np.ndindex(mat.shape):
            pname = '_'.join((par_name, str(r + 1), str(c + 1)))
            iname = '_'.join((inp_name, str(c + 1)))
            rname = '_'.join((reg_name, str(r + 1), str(c + 1)))

            params[r, c] = {'name': pname, 'value': int(mat[r, c])}
            registers[r, c] = rname
            products[r, c] = {'o': rname, 'a': pname, 'b': iname}

        params_key = '_'.join((par_name, 'params'))
        registers_key = '_'.join((par_name, 'sig_prod'))
        products_key = '_'.join((par_name, 'prods'))

        self.cache[registers_key] = registers
        self.context[params_key] = params.ravel()
        self.context[registers_key] = registers.ravel()
        self.context[products_key] = products.ravel()

    def gen_adder_ce(self):

        n_inp = self.order + self.n_inputs
        n_stages = int(math.ceil(math.log(n_inp, self.n_add)))

        ce = ['_'.join(('ce_add', str(ii))) for ii in range(1, n_stages)]
        ce.insert(0, 'ce_mul')
        ce.append('ce_out')

        self.context['adder_ce'] = list(zip(ce[1:], ce[:-1]))
        self.context['reg_ce_add'] = ['_'.join(('ce_add', str(ii))) for ii in range(1, n_stages)]

    def gen_adder(self, equation):

        if equation == 'state':
            input_terms = self.cache['B_sig_prod']
            state_terms = self.cache['A_sig_prod']
            output_terms = self.context['sig_dx']
            temp_name = 'sumS'
            adder_key = 'state_adders'
            reg_key = 'state_sig_add'
        else:
            input_terms = self.cache['D_sig_prod']
            state_terms = self.cache['C_sig_prod']
            output_terms = self.context['sig_y_long']
            temp_name = 'sumO'
            adder_key = 'output_adders'
            reg_key = 'output_sig_add'

        n_add = self.n_add
        n_inp = self.order + self.n_inputs
        n_stages = int(math.ceil(math.log(n_inp, n_add)))
        n_eqn = len(output_terms)

        def name_reg(x, y, z):
            return '_'.join((temp_name, str(x), str(y), str(z)))

        adders, sig_add = [], []
        for ii in range(n_eqn):
            terms = np.concatenate((state_terms[ii, :], input_terms[ii, :]))
            for jj in range(n_stages):
                size = min(n_add, len(terms))
                n_terms = (len(terms) - 1) // size + 1
                terms = np.array_split(terms, n_terms)
                terms = [' + '.join(n) for n in terms]
                if jj == n_stages - 1:
                    new_terms = [output_terms[ii]]
                else:
                    index = np.arange(n_terms)
                    new_terms = [name_reg(ii, jj, kk) for kk in index]
                    sig_add.extend(new_terms)
                adders.extend(list(zip(new_terms, terms)))
                terms = new_terms

        self.context[adder_key] = adders
        self.context[reg_key] = sig_add
