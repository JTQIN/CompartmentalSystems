# vim:set ff=unix expandtab ts=4 sw=4:
from concurrencytest import ConcurrentTestSuite, fork_for_tests
import sys
import unittest

import numpy as np
from sympy import Symbol, Matrix, symbols, diag, zeros, simplify, Function

from CompartmentalSystems.smooth_model_run import SmoothModelRun
from CompartmentalSystems.smooth_reservoir_model import SmoothReservoirModel
from testinfrastructure.InDirTest import InDirTest


######### TestClass #############
class TestSmoothReservoirModel(InDirTest):

    #fixme:
    def test_init(self):
        # test that state_vector is a sympy matrix
        # test simple cases
        pass

    def test_internal_flux_type(self):
        # test simple cases
        C_0, C_1  = symbols('C_0 C_1')
        state_vector = [C_0, C_1]
        time_symbol = Symbol('t')
        input_fluxes = {}
        output_fluxes = {}

        internal_fluxes = {(0,1): 5*C_0, (1,0): 4*C_1**2}
        rm = SmoothReservoirModel(state_vector, time_symbol, input_fluxes, output_fluxes, internal_fluxes)

        self.assertEqual(rm._internal_flux_type(0,1), 'linear')
        self.assertEqual(rm._internal_flux_type(1,0), 'nonlinear')

        # (1,0): 4 is considered to be nonlinear : in B the corresponding entry is 4/C_1
        internal_fluxes = {(0,1): C_0+5, (1,0): C_1/C_0}

        rm = SmoothReservoirModel(state_vector, time_symbol, input_fluxes, output_fluxes, internal_fluxes)

        self.assertEqual(rm._internal_flux_type(0,1), 'no substrate dependence')
        self.assertEqual(rm._internal_flux_type(1,0), 'nonlinear')

    def test_output_flux_type(self):
        # test simple cases
        C_0, C_1  = symbols('C_0 C_1')
        state_vector = [C_0, C_1]
        time_symbol = Symbol('t')
        input_fluxes = {}
        internal_fluxes = {}
        
        output_fluxes = {0: 5*C_0, 1: C_1**2}
        rm = SmoothReservoirModel(state_vector, time_symbol, input_fluxes, output_fluxes, internal_fluxes)

        self.assertEqual(rm._output_flux_type(0), 'linear')
        self.assertEqual(rm._output_flux_type(1), 'nonlinear')

        # (1,0): 4 is considered to be nonlinear : in B the corresponding entry is 4/C_1
        output_fluxes = {0: C_0+5, 1: C_1/C_0}

        rm = SmoothReservoirModel(state_vector, time_symbol, input_fluxes, output_fluxes, internal_fluxes)

        self.assertEqual(rm._output_flux_type(0), 'no substrate dependence')
        self.assertEqual(rm._output_flux_type(1), 'nonlinear')

    def test_port_controlled_Hamiltonian_representation(self):
        # for the test the two pool microbial model is used
        S,B,t,ux=symbols('S B,t,ux')
        V,ADD,k_B,k_SD,r,A_f,K_m,k_S=symbols('V,ADD,k_B,k_SD,r,A_f,K_m,k_S')
        state_vector = [S, B]
        time_symbol = Symbol('t')
        df      = k_S*A_f*S/(S+K_m)*B
        output_fluxes= {0:(1-r)*df}
        internal_fluxes= {(0,1):r*df,(1,0):k_B*B  }
        input_fluxes = {0: ADD}

        rm = SmoothReservoirModel(state_vector, time_symbol, input_fluxes, output_fluxes, internal_fluxes)
        J,Q,C,u = rm.port_controlled_Hamiltonian_representation()
        self.assertEqual(J, Matrix([[0,-r*df+k_B*B],[r*df-k_B*B, 0]]))
        self.assertEqual(zeros(2),simplify(Q-Matrix([[(1-r)*df,0],[0, 0]])))
        self.assertEqual(u, Matrix([ADD, 0]))

    def test_xi_T_N_u_representation(self):
        u_0, u_1, C_0, C_1, gamma  = symbols('u_0 u_1 C_0 C_1 gamma')
        state_vector = [C_0, C_1]
        time_symbol = Symbol('t')
        input_fluxes = {0: u_0, 1: u_1}
        output_fluxes = {1: 3*gamma*C_0*C_1}
        internal_fluxes = {(0,1): gamma*3*5*C_0*C_1, (1,0): gamma*3*4*C_0}

        rm = SmoothReservoirModel(state_vector, time_symbol, input_fluxes, output_fluxes, internal_fluxes)
        xi, T, N, C, u = rm.xi_T_N_u_representation()

        self.assertEqual(u, Matrix([u_0, u_1]))
        self.assertEqual(xi, 3*gamma)
        self.assertEqual(T, Matrix([[-1, 4/(C_1 + 4)], [1, -1]]))
        self.assertEqual(N, Matrix([[5*C_1, 0], [0, C_0*(C_1 + 4)/C_1]]))

    def test_NTu_matrices_to_fluxes_and_back(self):
        # f = xi*T*N*C + u
        t, C_1, C_2, C_3, gamma, k_1, k_2, k_3, t_12, t_13, t_21, t_23, t_31, t_32, u_1, u_2, u_3, xi \
            = symbols('t C_1 C_2 C_3 gamma k_1 k_2 k_3 t_12 t_13 t_21 t_23 t_31 t_32 u_1 u_2 u_3 xi')
        C = Matrix(3,1, [C_1, C_2, C_3])
        u = Matrix(3,1, [u_1, u_2, u_3])
        xi = gamma
        T = Matrix([[  -1, t_12, t_13],
                    [t_21,   -1, t_23],
                    [t_31, t_32,   -1]])
        N = diag(k_1, k_2, k_3)
        B = gamma*T*N

        rm=SmoothReservoirModel.from_B_u(C,t,B,u)

        self.assertEqual(rm.input_fluxes, {0: u_1, 1: u_2, 2: u_3})
        self.assertEqual(rm.output_fluxes, {0: gamma*k_1*(1-t_21-t_31)*C_1,
                                   1: gamma*k_2*(1-t_12-t_32)*C_2,
                                   2: gamma*k_3*(1-t_13-t_23)*C_3})
        self.assertEqual(rm.internal_fluxes, {
            (0,1): gamma*t_21*k_1*C_1, (0,2): gamma*t_31*k_1*C_1,
            (1,0): gamma*t_12*k_2*C_2, (1,2): gamma*t_32*k_2*C_2,
            (2,0): gamma*t_13*k_3*C_3, (2,1): gamma*t_23*k_3*C_3})

        # test backward conversion to matrices
        xi2, T2, N2, C2, u2 = rm.xi_T_N_u_representation()
        self.assertEqual(xi,xi2)
        self.assertEqual(u,u2)
        self.assertEqual(T,T2)
        self.assertEqual(N,N2)

    def test_Bu_matrices_to_fluxes_and_back(self):
        # f = u + xi*B*C
        t,C_1, C_2, C_3, k_1, k_2, k_3, a_12, a_13, a_21, a_23, a_31, a_32, u_1, u_2, u_3, gamma, xi \
        = symbols('t,C_1 C_2 C_3 k_1 k_2 k_3 a_12 a_13 a_21 a_23 a_31 a_32 u_1 u_2 u_3 gamma xi')
        C = Matrix(3,1, [C_1, C_2, C_3])
        u = Matrix(3,1, [u_1, u_2, u_3])
        B = gamma*Matrix([
                [-k_1, a_12, a_13],
                [a_21, -k_2, a_23],
                [a_31, a_32, -k_3]
            ])
        rm = SmoothReservoirModel.from_B_u(C,t,B,u)
        self.assertEqual(rm.input_fluxes, {0: u_1, 1: u_2, 2: u_3})
        self.assertEqual(rm.output_fluxes, {0: gamma*(k_1-a_21-a_31)*C_1,
                                   1: gamma*(k_2-a_12-a_32)*C_2,
                                   2: gamma*(k_3-a_13-a_23)*C_3})

        self.assertEqual(rm.internal_fluxes, {
            (0,1): gamma*a_21*C_1, (0,2): gamma*a_31*C_1,
            (1,0): gamma*a_12*C_2, (1,2): gamma*a_32*C_2,
            (2,0): gamma*a_13*C_3, (2,1): gamma*a_23*C_3})
            
        ## test backward conversion to compartmental matrix 
        B2 = rm.compartmental_matrix
        u2 = rm.external_inputs
        self.assertEqual(u,u2)
        self.assertEqual(B,B2)

    def test_matrix_to_flux_and_back_nonlinear(self):
        # f = u + xi*T*N*C
        t,C_1, C_2, C_3, gamma, k_1, k_2, k_3, t_12, t_13, t_21, t_23, t_31, t_32, u_1, u_2, u_3, xi \
            = symbols('t,C_1 C_2 C_3 gamma k_1 k_2 k_3 t_12 t_13 t_21 t_23 t_31 t_32 u_1 u_2 u_3 xi')
        C = Matrix(3,1, [C_1, C_2, C_3])
        u = Matrix(3,1, [u_1, u_2, u_3])
        xi = gamma*2
        T = Matrix([[  -1, t_12*C_2, t_13],
                    [t_21,   -1, t_23],
                    [t_31*k_1, t_32,   -1]])
        N = diag(k_1*C_2, k_2/C_3, k_3)
        rm = SmoothReservoirModel.from_B_u(C,t,xi*T*N,u)
         
        self.assertEqual(rm.input_fluxes, {0: u_1, 1: u_2, 2: u_3})
        self.assertEqual(rm.output_fluxes, {0: 2*gamma*k_1*(1-t_21-t_31*k_1)*C_1*C_2,
                                   1: -2*gamma*k_2*(-1+t_12*C_2+t_32)*C_2/C_3,
                                   2: 2*gamma*k_3*(1-t_13-t_23)*C_3})
        self.assertEqual(rm.internal_fluxes, {
            (0,1): 2*gamma*t_21*k_1*C_1*C_2, (0,2): 2*gamma*t_31*k_1**2*C_1*C_2,
            (1,0): 2*gamma*t_12*k_2*C_2**2/C_3, (1,2): 2*gamma*t_32*k_2*C_2/C_3,
            (2,0): 2*gamma*t_13*k_3*C_3, (2,1): 2*gamma*t_23*k_3*C_3})

        # test backward conversion to matrices
        
        xi2, T2, N2, C2, u2 = rm.xi_T_N_u_representation()
        self.assertEqual(xi,xi2)
        self.assertEqual(u,u2)
        self.assertEqual(T,T2)
        self.assertEqual(N,N2)

    def test_figure(self):
        C_0, C_1  = symbols('C_0 C_1')
        state_vector = [C_0, C_1]
        time_symbol = Symbol('t')
        input_fluxes = {}
        output_fluxes = {}
        internal_fluxes = {(0,1): 5*C_0*C_1, (1,0): 4*C_0}

        rm = SmoothReservoirModel(state_vector, time_symbol, input_fluxes, output_fluxes, internal_fluxes)
        fig = rm.figure()
        fig.savefig("reservoir_model_plot.pdf")

    def test_age_moment_system(self):
        x, y, t = symbols("x y t")
        state_vector = Matrix([x,y])
        B = Matrix([[-1, 0],
                    [ 0,-2]])
        u = Matrix(2, 1, [9,1])
        srm = SmoothReservoirModel.from_B_u(state_vector, t, B, u)

        max_order = 1
        extended_state, extended_rhs = srm.age_moment_system(max_order)
        x_moment_1, y_moment_1 = symbols('x_moment_1 y_moment_1')

        self.assertEqual(extended_state, Matrix([[x], [y], [x_moment_1], [y_moment_1]]))
        self.assertEqual(extended_rhs, Matrix([[-x + 9], 
                                               [-2*y + 1], 
                                               [1 - 9*x_moment_1/x], 
                                               [1 - y_moment_1/y]]))

        max_order = 2
        extended_state, extended_rhs = srm.age_moment_system(max_order)
        x_moment_1, y_moment_1, x_moment_2, y_moment_2 = symbols('x_moment_1 y_moment_1 x_moment_2 y_moment_2')

        self.assertEqual(extended_state, Matrix([[x], [y], [x_moment_1], [y_moment_1], [x_moment_2], [y_moment_2]]))
        self.assertEqual(extended_rhs, Matrix([[-x + 9], [-2*y + 1], 
                                               [1 - 9*x_moment_1/x], [1 - y_moment_1/y], 
                                               [2*x_moment_1 - 9*x_moment_2/x], [2*y_moment_1 - y_moment_2/y]]))
    

    def test_to_14C_only(self):
        lamda_1, lamda_2, C_1, C_2 = symbols('lamda_1 lamda_2 C_1 C_2')
        B = Matrix([[-lamda_1,        0],
                    [       0, -lamda_2]])
        u = Matrix(2, 1, [1, 2])
        state_vector = Matrix(2, 1, [C_1, C_2])
        time_symbol = Symbol('t')

        srm = SmoothReservoirModel.from_B_u(state_vector,
                                            time_symbol,
                                            B,
                                            u)
    
        srm_14C = srm.to_14C_only('lamda_14C', 'Fa_14C')
        C_1_14C, C_2_14C = symbols('C_1_14C, C_2_14C')
        ref_state_vector = Matrix(2, 1, [C_1_14C, C_2_14C])
        self.assertEqual(srm_14C.state_vector, ref_state_vector)

        decay_symbol = symbols('lamda_14C')
        ref_B = Matrix([[-lamda_1-decay_symbol,                     0],
                        [                    0, -lamda_2-decay_symbol]])
        self.assertEqual(srm_14C.compartmental_matrix, ref_B)

        Fa_expr = Function('Fa_14C')(time_symbol)
        ref_u = Matrix(2, 1, [Fa_expr, 2*Fa_expr])
        self.assertEqual(srm_14C.external_inputs, ref_u)


    def test_to_14C_explicit(self):
        lamda_1, lamda_2, C_1, C_2 = symbols('lamda_1 lamda_2 C_1 C_2')
        B = Matrix([[-lamda_1,        0],
                    [       0, -lamda_2]])
        u = Matrix(2, 1, [1, 2])
        state_vector = Matrix(2, 1, [C_1, C_2])
        time_symbol = Symbol('t')

        srm = SmoothReservoirModel.from_B_u(state_vector,
                                            time_symbol,
                                            B,
                                            u)
    
        srm_total = srm.to_14C_explicit('lamda_14C', 'Fa_14C')
        C_1_14C, C_2_14C = symbols('C_1_14C, C_2_14C')
        ref_state_vector = Matrix(4, 1, [C_1, C_2, C_1_14C, C_2_14C])
        self.assertEqual(srm_total.state_vector, ref_state_vector)

        decay_symbol = symbols('lamda_14C')
        ref_B = Matrix([[-lamda_1,0,0,0],
                        [0,-lamda_2,0,0],
                        [0,0,-lamda_1-decay_symbol,                     0],
                        [0,0,                    0, -lamda_2-decay_symbol]])
        self.assertEqual(srm_total.compartmental_matrix, ref_B)

        Fa_expr = Function('Fa_14C')(time_symbol)
        ref_u = Matrix(4, 1, [1, 2, Fa_expr, 2*Fa_expr])
        self.assertEqual(srm_total.external_inputs, ref_u)


####################################################################################################


if __name__ == '__main__':
    suite=unittest.defaultTestLoader.discover(".",pattern=__file__)

#    # Run same tests across 16 processes
#    concurrent_suite = ConcurrentTestSuite(suite, fork_for_tests(1))
#    runner = unittest.TextTestRunner()
#    res=runner.run(concurrent_suite)
#    # to let the buildbot fail we set the exit value !=0 if either a failure or error occurs
#    if (len(res.errors)+len(res.failures))>0:
#        sys.exit(1)

    unittest.main()

