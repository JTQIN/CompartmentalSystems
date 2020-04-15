import unittest

import numpy as np
from scipy.linalg import inv

from sympy import Function, Matrix, sin, symbols

from CompartmentalSystems.smooth_reservoir_model import SmoothReservoirModel
from CompartmentalSystems.pwc_model_run import PWCModelRun

from CompartmentalSystems.pwc_model_run_fd import PWCModelRunFD as PWCMRFD

class TestModelRun(unittest.TestCase):

    @unittest.skip('The tested function is not reasonable.')
    def test_find_equilibrium_model(self):
        ## create ReservoirModel
        C_1, C_2 = symbols('C_1 C_2')
        state_vector = Matrix(2, 1, [C_1, C_2]) 
        t = symbols('t')
        lamda_1 = Function('lamda_1')(t)
        lamda_2 = Function('lamda_2')(t)
        B = Matrix([[-lamda_1,      0.5*lamda_2],
                    [       0,         -lamda_2]])
        u = Matrix(2, 1, [0.3,0.5*0.5*sin(1/100*t)])
    
        srm = SmoothReservoirModel.from_B_u(state_vector, t, B, u)
    
        ## create ModelRun
        def rate_1(t):
            return 0.1+1/20*np.sin(1/10*t)
    
        def rate_2(t):
            return 0.05
    
        par_set = {}
        func_set = {lamda_1: rate_1, lamda_2: rate_2}
        start_values = np.array([40, 0])
        times = np.linspace(0, 10, 101)
        
        pwc_mr = PWCModelRun(srm, par_set, start_values, times, func_set)

        ## create fake discrete data
        nr_data_points = 3
        data_times = np.round(np.linspace(times[0], times[-1], nr_data_points),5)
        delta_t = (times[-1]-times[0]) / (nr_data_points-1)
        xs, Fs, rs, data_us = pwc_mr._fake_discretized_output(data_times)
    
        pwc_mr_fd = PWCMRFD.reconstruct_from_data(
            t,
            data_times, 
            start_values, 
            xs, 
            Fs,
            rs, 
            data_us)

        xss = pwc_mr.solve()[-1,...]
        B0 = pwc_mr_fd.Bs[-1]
        u0 = pwc_mr_fd.us[-1]

        B, u = pwc_mr_fd.find_equilibrium_model(xss, B0, u0)
        print(xss)
        print(-inv(B) @ u)
        self.assertTrue(np.allclose(-inv(B) @ u, xss))


################################################################################


if __name__ == '__main__':
    unittest.main()



