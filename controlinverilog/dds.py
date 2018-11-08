import numpy as np
import jinja2


class DDS(object):

    def __init__(self, name, f_exe, n_phase=24, n_amplitude=16, n_sine=8, n_fine=6, n_fine_word=8):

        # This ensures that the LUTs don't have excessive entries.
        assert (n_phase - n_sine - n_fine - 2) >= 0

        sine_lut = self._generate_sine_lut(n_sine, n_amplitude)
        fine_lut, n_fine_frac = self._generate_fine_lut(n_fine, n_sine, n_fine_word)

        context = {'name': name,
                   'pw': n_phase,
                   'sw': n_sine,
                   'aw': n_amplitude,
                   'fw': n_fine,
                   'faw': n_fine_word,
                   'faf': n_fine_frac,
                   'sine_lut': sine_lut,
                   'fine_lut': fine_lut}

        self.name = name
        self.f_exe = f_exe
        self.freq_res = f_exe / 2.0 ** n_phase
        self.phase_res = 360.0 / 2.0 ** n_phase
        self.output_word_len = n_amplitude
        self.output_frac_len = n_amplitude - 1

        loader = jinja2.PackageLoader('controlinverilog', 'templates')
        env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
        template = env.get_template('dds_v2.v')
        self.verilog = template.render(context)

    def print_summary(self):

        print('--- DDS Module: %s ---' % self.name)
        print('Execution frequency (Hz): %g' % self.f_exe)
        print('Frequency resolution (Hz/unit): %g' % self.freq_res)
        print('Phase Resolution (Degree/unit): %g' % self.phase_res)
        print('Output Format: s(%d,%d)' % (self.output_word_len, self.output_frac_len))

    def print_verilog(self, filename=None):

        if filename is None:
            print(self.verilog)
        else:
            with open(filename, 'w') as text_file:
                text_file.write(self.verilog)

    @staticmethod
    def calc_freqword(n_phase=24, f_exe=122.88e6, f_dds=50e3):

        freqword = np.round(f_dds / f_exe * 2 ** n_phase)
        print('FREQWORD = %d' % freqword)

    @staticmethod
    def calc_phase(n_phase=24, angle_deg=90):

        phaseword = np.round(angle_deg / 360 * 2 ** n_phase)
        print('PHASE = %d' % phaseword)

    @staticmethod
    def _generate_sine_lut(n_sine, n_amplitude):

        n_vals = 2 ** n_sine
        alpha = np.pi / 2 / n_vals
        n_frac = n_amplitude - 1

        angles = np.arange(n_vals) * alpha
        reals = (1 - 2 ** -n_frac) * np.sin(angles)
        fixed = np.round(reals * 2 ** n_frac).astype(int)

        return fixed

    @staticmethod
    def _generate_fine_lut(n_fine, n_sine, n_fine_word):

        n_vals = 2 ** n_fine
        beta = np.pi / 2 / 2 ** n_sine
        alpha = beta / n_vals
        scale = 2 ** (n_fine_word - 1) / np.sin(beta)
        n_frac = int(np.floor(np.log2(scale)))

        angles = np.arange(n_vals) * alpha
        reals = np.sin(angles)
        fixed = np.round(2 ** n_frac * reals).astype(int)

        return fixed, n_frac
