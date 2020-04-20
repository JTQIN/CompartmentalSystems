import numpy as np

from numpy.linalg import pinv
from scipy.linalg import expm#, inv
from scipy.optimize import root# least_squares
from sympy import  Matrix, symbols, zeros, Function
from tqdm import tqdm
#
#from CompartmentalSystems import picklegzip
from .model_run import ModelRun
from .pwc_model_run import PWCModelRun
from .smooth_reservoir_model import SmoothReservoirModel


################################################################################


class Error(Exception):
    """Generic error occurring in this module."""
    pass


################################################################################


#class PWCModelRunFD(PWCModelRun):
class PWCModelRunFD(ModelRun):
    def __init__(self, time_symbol, data_times, start_values, xs, Fs, rs, gross_Us):

        self.data_times = data_times
        cls = self.__class__
        disc_times = data_times
        print('reconstructing us')
        #us = cls.reconstruct_us(data_times, gross_Us)
        us = gross_Us/self.dts.reshape(-1,1)

        print('reconstructing Bs')
        Bs = cls.reconstruct_Bs(data_times, xs, Fs, rs, us)
        
        nr_pools = len(start_values)
        strlen   = len(str(nr_pools))
        pool_str = lambda i: ("{:0"+str(strlen)+"d}").format(i)
        par_set  = dict()
        func_set = dict()
    
        srm_generic = cls.create_srm_generic(
            time_symbol,
            Bs,
            us
        )
        time_symbol = srm_generic.time_symbol

        u_funcs = cls.u_pwc(data_times, us)
        B_funcs = cls.B_pwc(data_times, Bs)
    
        def func_maker_u(pool):
            def func(s):
                return u_funcs[pool](s)
            return func
    
        v = srm_generic.external_inputs
        for i in range(nr_pools):
#        if v[i].is_Function:
            func_set['u_'+pool_str(i)+'('+time_symbol.name+')'] = func_maker_u(i)
    
        def func_maker_B(p_to, p_from):
            def func(s):
                return B_funcs[(p_to, p_from)](s)
            return func
    
        M = srm_generic.compartmental_matrix
        for j in range(nr_pools):
            for i in range(nr_pools):
#                if M[i,j].is_Function:
#                if not M[i,j].is_constant():
                func_set['b_'+pool_str(i)+pool_str(j)+'('+time_symbol.name+')'] = \
                        func_maker_B(i,j)

        self.pwc_mr=PWCModelRun(
            srm_generic, 
            par_set, 
            start_values, 
            data_times,
            func_set=func_set,
            disc_times=disc_times 
        )
        self.us=us
        self.Bs=Bs
    
    @property
    def dts(self):
        """
        The lengths of the time 
        """
        return np.diff(self.data_times).astype(np.float64)

    def solve(self,alternative_start_values:np.ndarray=None): 
        return self.pwc_mr.solve(alternative_start_values)

    def B_func(self, vec_sol_func=None):
        return self.pwc_mr.B_func(vec_sol_func)
 
    def external_input_vector_func(self, cut_off = True):
        return self.pwc_mr.external_input_vector_func(cut_off)

    @property
    def times(self):
        return self.data_times

    def acc_external_input_vector(self):
        return self.us*self.dts.reshape(-1,1)


    def acc_internal_flux_matrix(self):
        return self.pwc_mr.acc_internal_flux_matrix()
    
    def acc_external_output_vector(self) :
        return self.pwc_mr.acc_external_output_vector()


#    
#    @classmethod
#    def load_from_file(cls, filename):
#        pwc_mr_fd_dict = picklegzip.load(filename)
#
#        return cls.load_from_dict(pwc_mr_fd_dict)
#
#
#    def save_to_file(self, filename):
#        soln = self.solve()
#        self.soln = soln
##        pwc_mr = self.to_smooth_model_run()
##        soln1 = pwc_mr.solve()
##        self.soln1 = soln1
##        soln2, soln2_func = pwc_mr.solve_2()
##        self.soln2 = soln2
#        pwc_mr_fd_dict = {
#            'start_values': self.start_values,
#            'time_symbol':  self.model.time_symbol,
#            'Bs':           self.Bs,
#            'us':           self.us,
#            'data_times':   self.data_times,
##            'times':        self.times
#            'soln':         soln,
##            'soln1':        soln1,
##            'soln2':        soln2,
#            'location':     getattr(self, 'location', None)
#        }
#
#        picklegzip.dump(pwc_mr_fd_dict, filename)
#
#
#    def to_smooth_model_run(self):
#        pwc_mr = PWCModelRun(
#            self.model, 
#            self.parameter_set, 
#            self.start_values, 
#            self.data_times,
#            self.func_set
#        )
#
#        return pwc_mr
#
#
    @classmethod
    def reconstruct_B_surrogate(cls, dt, x0, F, r, u, B0, x1):
        ## reconstruct a B that meets F and r possibly well,
        ## B0 is some initial guess for the optimization
        nr_pools = len(x0)
        VAL = 0
    
        ## integrate x by trapezoidal rule
        def x_trapz(tr_times, B):
            def x(tau):
                M = expm(tau*B)
#                x = M @ x0 + inv(B) @ (-np.identity(nr_pools)+M) @ u
                x = M @ x0 + pinv(B) @ (-np.identity(nr_pools)+M) @ u
                return x
    
            xs, x1 = np.array(list(map(x, tr_times))), x(tr_times[-1])
            return np.trapz(xs, tr_times, axis=0), x1
    
        ## convert parameter vector to compartmental matrix
        def pars_to_matrix(pars):
            B = np.zeros((nr_pools**2))
            B[int_indices.tolist()] = pars[:len(int_indices)]
            B = B.reshape((nr_pools,nr_pools))
            d = B.sum(0)
            d[(ext_indices-nr_pools**2).tolist()] += pars[len(int_indices):]
            B[np.diag_indices(nr_pools)] = -d
    
            return B
    
        ## function to minimize difference vector of
        ## internal fluxes F and outfluxes r
        def g_tr(pars):
            B = pars_to_matrix(pars)
            tr_times = np.linspace(0, dt, 11)

            int_x, x1_tmp = x_trapz(tr_times, B)
            res0 = 0
            ## keep the next line if next x-value is also a constraint
            res0 = np.sum(np.abs(x1_tmp-x1))
            nonlocal VAL
            VAL = res0 

            res1_int = F.reshape((nr_pools**2,))[int_indices.tolist()]
            res2_int = pars[:len(int_indices)] * int_x[(int_indices % nr_pools).tolist()]
            res_int = np.abs(res1_int-res2_int)
    
            res1_ext = r[(ext_indices-nr_pools**2).tolist()] 
            res2_ext = pars[len(int_indices):] * int_x[(ext_indices-nr_pools**2).tolist()]
            res_ext = np.abs(res1_ext-res2_ext)

            res = np.append(res_int, res_ext)
            return res
    
        ## wrapper around g_tr that keeps parameter within boundaries
        def constrainedFunction(x, f, lower, upper, minIncr=0.001):
            x = np.asarray(x)
            lower = np.asarray(lower)
            upper = np.asarray(upper)
    
            xBorder = np.where(x<lower, lower, x)
            xBorder = np.where(x>upper, upper, xBorder)
            fBorder = f(xBorder)
            distFromBorder = (np.sum(np.where(x<lower, lower-x, 0.))
                          +np.sum(np.where(x>upper, x-upper, 0.)))
            return (fBorder + (fBorder
                           +np.where(fBorder>0, minIncr, -minIncr))*distFromBorder) 
    
        lbounds = [0]*(nr_pools**2 + nr_pools)
        for i in range(nr_pools):
            lbounds[i*nr_pools+i] = -10
    
        ubounds = [10]*(nr_pools**2 + nr_pools)
        for i in range(nr_pools):
            ubounds[i*nr_pools+i] = 0
    
        par_indices = []
        for i in range(nr_pools):
            for j in range(nr_pools):
                if (F[i,j] > 0):
                    par_indices.append(i*nr_pools+j)
        for i in range(nr_pools):
            if r[i] > 0:
                par_indices.append(nr_pools**2+i)
    
        par_indices = np.array(par_indices)
        int_indices = par_indices[par_indices<nr_pools**2]
        ext_indices = par_indices[par_indices>=nr_pools**2]
    
        lbounds = np.array(lbounds)[par_indices.tolist()]
        ubounds = np.array(ubounds)[par_indices.tolist()]
        A0 = np.append(B0.reshape((nr_pools**2,)), -B0.sum(0))
        pars0 = A0[par_indices.tolist()]

        y = root(
            constrainedFunction, 
            x0=pars0,
            args=(g_tr, lbounds, ubounds)
        )

#        y = least_squares(
#            g_tr,
#            x0      = pars0,
#            verbose = 2,
##            xtol    = 1e-03,
#            bounds  = (lbounds, ubounds)
#        )
    
        B = pars_to_matrix(y.x)
        ## correct for empty pools, avoid vanishing rows/cols
#        print(np.where(x0==0))
#        print(np.where(x1==0))
#        for j in range(nr_pools):
##            if (x0[j] == 0) and (x1[j] == 0):
#            if (x0[j] == 0) or (x1[j] == 0):
##                print(j)
#                B[j,j] = np.mean(np.diag(B))
    
#        print(B0)
#        print(x0)
#        print(x1)
#        print(B)
#        print(np.where(np.diag(B)==0))

#        print(VAL, VAL/x1.sum(), flush=True)
#        input()
        
        tr_times = np.linspace(0, dt, 11)
        int_x, x1_tmp = x_trapz(tr_times, B)
        return B, x1_tmp


    @classmethod
    def reconstruct_Bs(cls, times, xs, Fs, rs, us):
        nr_pools = len(xs[0])
    
        def guess_B0(dt, x_approx, F, r):
            nr_pools = len(x_approx)
            B = np.identity(nr_pools)
        
            # construct off-diagonals
            for j in range(nr_pools):
                if x_approx[j] != 0:
                    B[:,j] = F[:,j] / x_approx[j] / dt
                else:
                    B[:,j] = 0
        
            # construct diagonals
            for j in range(nr_pools):
                if x_approx[j] != 0:
                    B[j,j] = - (sum(B[:,j]) - B[j,j] + r[j] / x_approx[j] / dt)
                else:
                    B[j,j] = -1
        
            return B
    
        x = xs[0]
        Bs = np.zeros((len(times)-1, nr_pools, nr_pools))
        for k in tqdm(range(len(times)-1)):
            dt = times[k+1] - times[k]
            B0 = guess_B0(dt, (xs[k]+xs[k+1])/2, Fs[k], rs[k])
            B, x = cls.reconstruct_B_surrogate(dt, x, Fs[k], rs[k], us[k], B0, xs[k+1])
            Bs[k,:,:] = B
    
        return Bs

    @classmethod
    def B_pwc(cls, times, Bs):
        def func_maker(i,j):
            def func(t):
                index = np.where(times<=t)[0][-1]
                index = min(index, Bs.shape[0]-1)
                return Bs[index,i,j]
            return func    

        nr_pools = Bs[0].shape[0]
        B_funcs = dict()
        for j in range(nr_pools):
            for i in range(nr_pools):
                B_funcs[(i,j)] = func_maker(i,j)

        return B_funcs

    #@classmethod
    #def reconstruct_u(cls, dt, data_U):
    #    return data_U / dt

    #@classmethod
    #def reconstruct_us(cls, times, gross_Us):
    #    us = np.zeros_like(gross_Us)
    #    for k in range(len(times)-1):
    #        #dt = times[k+1] - times[k]

    #        #dt = dt.item().days ##### to be removed or made safe
    #        us[k,:] = cls.reconstruct_u(self.dts[k], gross_Us[k])

    #    return us

    @classmethod
    def u_pwc(cls, times, us):
        def func_maker(i):
            def func(t):
                index = np.where(times<=t)[0][-1]
                index = min(index, us.shape[0]-1)
                return us[index,i]
            return func    
    
        nr_pools = us[0].shape[0]
        u_funcs = []
        for i in range(nr_pools):
            u_funcs.append(func_maker(i))
    
        return u_funcs

    @classmethod
    def create_B_generic(cls, Bs, time_symbol):
        nr_pools = Bs.shape[1]
        strlen   = len(str(nr_pools))
        pool_str = lambda i: ("{:0"+str(strlen)+"d}").format(i)
        
        def is_constant_Bs(i,j):
            c = Bs[0,i,j]
            diff = Bs[:,i,j]-c
    
            if len(diff[diff == 0]) == len(Bs):
                res = True
            else:
                res = False
    
            return res
    
        B_generic = zeros(nr_pools, nr_pools)
        for j in range(nr_pools):
            for i in range(nr_pools):
                if not is_constant_Bs(i,j):
                    B_generic[i,j] = Function('b_'+pool_str(i)+pool_str(j))(time_symbol)
                else:
                    B_generic[i,j] = Bs[0,i,j]
        
        return B_generic


    @classmethod
    def create_u_generic(cls, us, time_symbol):
        nr_pools = us.shape[1]
        strlen   = len(str(nr_pools))
        pool_str = lambda i: ("{:0"+str(strlen)+"d}").format(i)

        def is_constant_us(i):
            c = us[0,i]
            diff = us[:,i]-c
    
            if len(diff[diff == 0]) == len(us):
                res = True
            else:
                res = False
    
            return res
    
        u_generic = zeros(nr_pools, 1)
        for i in range(nr_pools):
            if not is_constant_us(i):
                u_generic[i] = Function('u_'+pool_str(i))(time_symbol)
            else:
                u_generic[i] = us[0,i]
    
        return u_generic


    @classmethod
    def create_srm_generic(cls, time_symbol, Bs, us):
        nr_pools = Bs.shape[1]
        strlen = len(str(nr_pools))
        pool_str = lambda i: ("{:0"+str(strlen)+"d}").format(i)
    
        state_vector_generic = Matrix(
            nr_pools,
            1, 
            [symbols('x_'+pool_str(i)) for i in range(nr_pools)]
        )
    
        B_generic = cls.create_B_generic(Bs, time_symbol)
        u_generic = cls.create_u_generic(us, time_symbol)

        srm_generic = SmoothReservoirModel.from_B_u(
            state_vector_generic,
            time_symbol,
            B_generic,
            u_generic)
   
        return srm_generic

#    def solve(self):
#        if not hasattr(self, 'soln'):
#            soln = self.pwc_mrs[0].solve()
#            for k in range(1, len(self.data_times)-1):
#                soln = soln[:-1]
#                k_soln = self.pwc_mrs[k].solve()
#                soln = np.concatenate((soln, k_soln), axis=0)
#
#            
#
#            soln = custom_solve_ivp
#            self.soln = soln
#
#        return self.soln
#
#
#    ## which model would be reasonable??
#    ## here we try to find B and u to match xss
#    ## potentiallypotentially  very ill-conditioned
#
##    def find_equilibrium_model(self, xss, B0, u0):
##        B = self.model.compartmental_matrix
##        u = self.model.external_inputs
##
##        nr_pools = self.model.nr_pools
##
##        ## convert parameter vector to compartmental matrix
##        def pars_to_B_and_u(pars):
##            B_tmp = np.zeros((nr_pools**2))
##            B_tmp[int_indices.tolist()] = pars[:len(int_indices)]
##            B_tmp = B_tmp.reshape((nr_pools,nr_pools))
##            for i in range(nr_pools):
##                for j in range(nr_pools):
##                    if not B[i,j].is_Function:
##                       B_tmp[i,j] = B[i,j]
##
##            u_tmp = np.zeros((nr_pools))
##            u_tmp[(ext_indices-nr_pools**2).tolist()] = pars[len(int_indices):]
##    
##            for i in range(nr_pools):
##                if not u[i].is_Function:
##                    u_tmp[i] = u[i]
##
##            return B_tmp, u_tmp
##
##        ## function to minimize difference vector of Bx und -u
##        def g_eq(pars):
##            B, u = pars_to_B_and_u(pars)
###            print(B.sum(), u.sum())
##
##            res1 = np.abs(B @ xss + u)
###            res1 = np.abs(xss + pinv(B) @ u)
##            res2 = np.maximum(B.sum(0),0) # B compartmental?
##
##            print(res1.sum(), res2.sum()*1e12, (res1 + res2*1e12).sum())
##            return res1 + res2 * 1e12
##
##        lbounds = [0]*(nr_pools**2 + nr_pools)
##        for i in range(nr_pools):
##            lbounds[i*nr_pools+i] = -10
##    
##        ubounds = [10]*(nr_pools**2 + nr_pools)
##        for i in range(nr_pools):
##            ubounds[i*nr_pools+i] = 0
##    
##        par_indices = []
##        for i in range(nr_pools):
##            for j in range(nr_pools):
##                if B[i,j].is_Function:
##                    par_indices.append(i*nr_pools+j)
##        for i in range(nr_pools):
##            if u[i].is_Function:
##                par_indices.append(nr_pools**2+i)
##    
##        par_indices = np.array(par_indices)
##        int_indices = par_indices[par_indices<nr_pools**2]
##        ext_indices = par_indices[par_indices>=nr_pools**2]
##   
##        lbounds = np.array(lbounds)[par_indices.tolist()]
##        ubounds = np.array(ubounds)[par_indices.tolist()]
##
##        A0 = np.append(B0.reshape((nr_pools**2,)), u0)
##        pars0 = A0[par_indices.tolist()]
##   
##        y = least_squares(
##            g_eq, 
##            x0       = pars0,
##            verbose  = 2,
###            xtol     = 1e-03,
##            bounds   = (lbounds, ubounds)
##        )
##   
###        print(y) 
##        B, u = pars_to_B_and_u(y.x)   
##        return B, u
#
#
    ########## 14C methods #########


    def to_14C_only(self, start_values_14C, Fa_func, decay_rate=0.0001209681):
        pwc_mr_fd_14C = self.pwc_mr.to_14C_only(
            start_values_14C,
            Fa_func,
#            disc_times = self.data_times,
            decay_rate = decay_rate
        )

        return pwc_mr_fd_14C








