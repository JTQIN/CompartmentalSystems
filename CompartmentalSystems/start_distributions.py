from sympy import Matrix
import numpy as np 
from scipy.linalg import inv, LinAlgError
from scipy.special import factorial
from CompartmentalSystems.helpers_reservoir import jacobian, func_subs, numerical_function_from_expression,pe
from CompartmentalSystems.smooth_model_run import SmoothModelRun
from LAPM.linear_autonomous_pool_model import LinearAutonomousPoolModel

def start_age_moments_from_zero_initial_content(srm,max_order):
    return [ np.zeros(srm.nr_pools,1) for n in range(1, max_order+1)]

def start_age_moments_from_empty_spin_up(srm,parameter_set,func_set,a_max,max_order):
    # to do:
    # run a spin up and observe the age distribution at the end
    # then compute the moments numerically
    raise Exception("Not implemented yet")

def start_age_moments_from_steady_state(srm,t0,parameter_set,func_set,max_order):
    """
    The age distribution at the start :math`t_0` is NOT 
    defined by the constituents of objects of class SmoothModelRun. 
    In fact EVERY age distribution can be chosen. 
    The implemented algorithms will correcly project it 
    to any time :math`t`.
    The distributions eaisiest to imagine are the one with all pools empty or the one where all initial mass has age zero.
    However often one is interested in the CHANGE of an age distribution that has been ESTABLISHED over a long period of time.        
    There are several ways to generate such an established
    distribution.

    1 ) Finite age spin up from empty pools ( see function start_age_moments_from_empty_spin_up)
    Start the computation with all pools empty at time 
    :math `t_0` and run it till time :math `t = a_{max}` where :math `a_max` is the oldest age you care about about in your interpretation of the results. 
    The resulting distribution will be non zero only in the interval :math `[0,a_max]`. This has to be considere regarding the questions that can be asked. 
    It would for instance not make sense to mistake the fact that the percentage of material older than :math `a_max` will increase over time as a property of the system, where it is actually a property of the (spun up) start distribution.  
    
    2 ) find a steady state  of the autonumuous system
    If you take the term ESTABLISHED to the limit of infinity you can look for a related system that has persisted unchanged for all  times :math `t<t_0` and start with the age distribution created by this system.
      1.) Transform the general nonlinear non-autonomous system into a nonlinear autonomous system by freezing it at time :math `t=t_0`: 
    Compute :math `u_0(x)=u(t_0,x_0)` and :math `B_0(x)=B(t_0,x_0)` 
    Numerically look for an equilibrium :math `x*` of the nonlinear system :math `0=B_0(x*)+u_0(x*).
    :math `x*` is the compatible startvalue for the following simulation. 
    A special case occures for linear systems where B(x,t)=B(t)
    and u(x,t) = u(t)
    We can compute the :math `x*` in one step: `x*=B_0**-1 u_0`.
    

    Args:
        srm (SmoothReservoirModel) : The (symbolic) model
        par_set : The parameter set that transforms the symbolic model into a numeric one. 
        max_order (int): The highest order up to which moments are
        to be computed.

    Returns:
        numpy.ndarray: moments x pools, containing the moments of the
        pool ages in equilibrium.
    """
    
    # check for linearity, note that some state dependent input counts
    # as linear too (because it leads to a linear system) 
    # We can write u=M*stateVector+I0 
    # If M is state INdependent M is the jacobian of u with respect to the statevariables
    # (This is not true for general nonlinear u)
    if srm.is_linear:

        B_sym = srm.compartmental_matrix
        u_sym=srm.external_inputs

        if srm.is_state_dependent(u_sym):
            # in this case we can in principle transform to a linear Model with constant
            # imput and new B
            # compute the jacobian of u
            sv=Matrix(srm.state_vector)
            M=jacobian(u_sym,sv)
            u_sym=u_sym-M*sv
            B_sym=B_sym+M
        
        t=srm.time_symbol
         
        #tup = tuple(srm.state_vector) + (t,)
        # since we are in the linear case B can not depend on the state variables
        tup = (t,)
        u_func=numerical_function_from_expression(u_sym,tup,parameter_set,func_set)
        B_func=numerical_function_from_expression(B_sym,tup,parameter_set,func_set)
        B0=B_func(t0)
        u0=u_func(t0)
        try:
            x0=-inv(B0)@u0
        except LinAlgError as e:
            print("""
            B_0=B(t_0) is not invertable
            If a singular matrix B_0 occurs, then the system would have traps. 
            A steady state could then only occour
            if the components of u0=u(t0) would be zero for the pools connected
            to the trap. 
            In this (unlikely) event the startage distribution would
            be ambigous because the fixedpoint x* is not uniqe (The content of the trap is a free 
            parameter and so is its age.)
            """)
            raise e

        lapm=LinearAutonomousPoolModel(Matrix(u0),Matrix(B0))
        start_age_moments = []
        for n in range(1, max_order+1):
            start_age_moment_sym=lapm.a_nth_moment(n)
            start_age_moment=np.array(start_age_moment_sym).astype(np.float).reshape(srm.nr_pools)
            #start_age_moment = (-1)**n * factorial(n) \
                            #* inv(X0) @ np.linalg.matrix_power(inv(B0), n) @ x0
                            # fixed mm 8.8.2018: 
                            #* pinv(X0) @ matrix_power(pinv(B0), n) @ x0
                            # I think that pinv (pseudo inverse) is not justified here since 
                            # the computation seems to relyon the same assumptions as LAPMs steady state
                            # formulas.
                            # If a singular matrix B_0 occurs as B(x*,t0)
                            # consequence of the solution of the steady state x*            
                            # Then the system would have traps. A steady state could then only occour
                            # if the components of u0=u(x*,t0) would be zero for the pools connected
                            # to the trap. In this (unlikely) event the startage distribution would
                            # be ambigous because x* is not uniqe (The content of the trap is a free 
                            # parameter and so is its age.)
                            # In this case we should at least issue  a warning 
                            
            start_age_moments.append(start_age_moment)
        ret=np.array(start_age_moments)
        
        return ret
    else:
        raise Exception("""
        At the moment the algorithm assumes an equilibrium
        at t_0 with B_0=B(t_0) but starts at arbitrary startvalues.
        Actually it could start at the equilibrium point of the 
        nonlinear autonomous system. 
        Until this is actually implemented  the tests should fail 
        at least for all nonlinear models.
         
        """)
        # to do:
        # try to find an equilibrium
        # and implement 2a) or fail