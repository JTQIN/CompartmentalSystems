from testinfrastructure.InDirTest import InDirTest
#from testinfrastructure.helpers import pe
import numpy as np

from CompartmentalSystems.BlockIvp import BlockIvp

class TestBlockIvp(InDirTest):
    def test_solution(self):
        x1_shape=(5,5)
        x2_shape=(2,)
        
        bivp=BlockIvp(
             time_str='t'
            ,start_blocks=[('x1',np.ones(x1_shape)),('x2',np.ones(x2_shape))]
            ,functions=[
                 ((lambda x1   : - x1     ),    [     'x1'     ])
                ,((lambda t,x2 : - 2*t*x2 ),    ['t' ,     'x2'])
             ])   
        # the reference solution 
        t_max=2
        ref={'x1':np.exp(-t_max)*np.ones(x1_shape),
             'x2':np.exp(-t_max**2)*np.ones(x2_shape)
        }
        res = bivp.block_solve(t_span=(0,t_max))
        self.assertTrue(np.allclose(res['x1'][-1],ref['x1'],rtol=1e-2))
        self.assertTrue(np.allclose(res['x2'][-1],ref['x2'],rtol=1e-2))

        # here we describe time by a variable with constant derivative
        # amd use it in the derivative of the second variable
        # to simulate a coupled system without feedback (skew product)
        x1_shape=(1,)
        x2_shape=(2,)
        bivp=BlockIvp(
             time_str='t'
            ,start_blocks=[('x1',np.zeros(x1_shape)),('x2',np.ones(x2_shape))]
            ,functions=[
                 ((lambda x1   :   np.ones(x1.shape)       ),    ['x1'])
                ,((lambda x1,x2 : - 2*x1*x2 ),    ['x1' ,     'x2'])
             ])   
        # the reference solution 
        t_max=2
        ref={'x1':t_max*np.ones(x1_shape),
             'x2':np.exp(-t_max**2)*np.ones(x2_shape)
        }
        res = bivp.block_solve(t_span=(0,t_max))
        self.assertTrue(np.allclose(res['x1'][-1],ref['x1'],rtol=1e-2))
        self.assertTrue(np.allclose(res['x2'][-1],ref['x2'],rtol=1e-2))
