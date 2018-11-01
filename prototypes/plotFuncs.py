
import inspect
from sympy import Symbol,lambdify
from copy import copy
import numpy as np
# for 2d plots we use Matplotlib
import matplotlib.pyplot as plt
from testinfrastructure.helpers  import pe
from CompartmentalSystems.smooth_model_run import SmoothModelRun
from CompartmentalSystems.smooth_reservoir_model import SmoothReservoirModel
from CompartmentalSystems.helpers_reservoir import  numsol_symbolic_system ,numerical_function_from_expression
from testinfrastructure.helpers  import pe
from Classes import BastinModel,BastinModelRun
import drivers #contains the fossil fuel interpolating functions
from string import Template

def poolsizes(ax,times,soln):
    ax.plot(times, soln[:,0],label='Atmosphere')
    ax.plot(times, soln[:,1],label='Terrestrial Biosphere')
    ax.plot(times, soln[:,2],label='Surface ocean')
    #ax.plot(times, soln[:,0:3].sum(1), label='lim Total')
    ax.set_xlabel('Time (yr)')
    ax.set_ylabel('Mass (PgC)')
    #if soln.shape[1]>3:
    #    ax.plot(times, soln[:,3], color='black', label='z')

    ax.legend(loc=2)
    return(ax)

def my_func_name():
    cf=inspect.currentframe()
    callerName=cf.f_back.f_code.co_name
    return callerName

def panel_one(limited_srm,bm, par_dict_v1, control_start_values, times, func_dict):
    start_values=control_start_values[:-1]
    limited_smr = SmoothModelRun(limited_srm, par_dict_v1, start_values, times, func_dict)
    bmr=BastinModelRun( bm, par_dict_v1, control_start_values, times, func_dict)

    soln_uncontrolled = limited_smr.solve()

    soln_controlled = bmr.solve()
    fig=plt.figure(figsize=(10,10))
    #fig1.title('Total carbon'+title_suffs[version])
    ax1=fig.add_subplot(2,1,1)
    ax1.plot(times, soln_uncontrolled[:,0],color='blue' ,label='Atmosphere')
    ax1.plot(times, soln_uncontrolled[:,1],color='green',label='Terrestrial Biosphere')
    ax1.plot(times, soln_uncontrolled[:,2],color='red'  ,label='Surface ocean')
    ax1.set_ylabel('Mass (PgC)')
    ax1.legend(loc=2)
    ax1.set_title("Uncontrolled")

    ax2=fig.add_subplot(2,1,2)
    ax2.plot(times, soln_controlled[:,0],color='blue' ,label='Atmosphere')
    ax2.plot(times, soln_controlled[:,1],color='green',label='Terrestrial Biosphere')
    ax2.plot(times, soln_controlled[:,2],color='red'  ,label='Surface ocean')
    ax2.set_ylabel('Carbon stocks (PgC)')
    ax2.set_xlabel('Time (yr)')
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_title("Controlled")
    
    #limited_soln_uncontrolled 
    fig.savefig(my_func_name()+'.pdf')


def all_in_one(unlimited_srm,limited_srm,bm,par_dict_v1, control_start_values, times, func_dict,u_A):
    start_values=control_start_values[:-1]
    unlimited_smr = SmoothModelRun(unlimited_srm, par_dict_v1, start_values, times, func_dict)
    limited_smr = SmoothModelRun(limited_srm, par_dict_v1, start_values, times, func_dict)
    bmr=BastinModelRun( bm, par_dict_v1, control_start_values, times, func_dict)

    soln = unlimited_smr.solve()
    limited_soln_uncontrolled = limited_smr.solve()

    limited_soln_controlled = bmr.solve()
    fig=plt.figure(figsize=(18,30))
    #fig.title('Total carbon'+title_suffs[version])
    ax1=fig.add_subplot(5,1,1)
    ax2=fig.add_subplot(5,1,2)
    ax3=fig.add_subplot(5,1,3)
    ax4=fig.add_subplot(5,1,4)
    ax5=fig.add_subplot(5,1,5)
    
    ax1=poolsizes(ax1,times,soln)
    ax1.set_title("unlimited uncontrolled")

    ax2=poolsizes(ax2,times,limited_soln_uncontrolled)
    ax2.set_title("limited uncontrolled")

    ax3=poolsizes(ax3,times,limited_soln_controlled)
    ax3.set_title("limited controlled")
    
    
    # since we do not know the actual phi of the bastin model run 
    # we assume the most general case that after all paramteters
    # and functions have been substituted t,z remain as arguments
    # The actual expression might not even contain t but that is no
    # problem
    bm=bmr.bm
    tup=(bm.time_symbol,bm.z_sym)
    times=bmr.times
    phi_num=bmr.phi_num(tup)
    ax4.set_title("control")
    zval=limited_soln_controlled[:,3]
    u_vals=phi_num(times,zval)
    pe('times.shape',locals())
    pe('zval.shape',locals())
    ax4.plot(times, u_vals, label='u')
    ax4.legend(loc=3)
   
    
    ax5.plot(times, func_dict[u_A](times),label='u_A')
    ax5.legend(loc=2)
    ax5.set_xlabel('Time (yr)')
    ax5.set_ylabel('Mass (PgC)')
    fig.savefig(my_func_name()+'.pdf')
    

#def as_sa_fluxes(mr):
#    fig=plt.figure()
#    fl_at=mr.internal_flux_funcs()[(0,1)]
#    fl_ta=mr.internal_flux_funcs()[(1,0)]
#    fl_as=mr.internal_flux_funcs()[(0,2)]
#    fl_sa=mr.internal_flux_funcs()[(2,0)]
#    ax1=fig.add_subplot(4,1,1)
#    ax2=fig.add_subplot(4,1,2)
#    ax3=fig.add_subplot(4,1,3)
#    ax4=fig.add_subplot(4,1,4)
#    ax1.plot(times,fl_as(times))
#    ax1.plot(times,fl_sa(times))
#    ax2.plot(times,fl_as(times)-fl_sa(times))
#
#    ax3.plot(times,fl_at(times))
#    ax3.plot(times,fl_ta(times))
#    ax4.plot(times,fl_as(times)-fl_sa(times))
#    return fig
def plot_epsilon_family(
        limited_srm,
        par_dict,
        control_start_values, 
        times,
        func_dict,
        epsilons
    ):    
    fig=plt.figure()
    ax1=fig.add_subplot(1,1,1)
    ax1.set_title("control u for different values of epsilon")
    for eps_val in epsilons:
        z=Symbol('z')
        eps=Symbol('eps')
        u_z_exp=z/(eps+z)
        par_dict[eps]=eps_val
        bm=BastinModel(limited_srm,u_z_exp,z)
        bmr=BastinModelRun(
            bm, 
            par_dict,
            control_start_values, 
            times,
            func_dict
        )
        phi_num=bmr.phi_num((z,))
        soln=bmr.solve() 
        z=soln[:,3]
        pe('bm.u_expr',locals())
        u=phi_num(z)
        ax1.plot(times,u)
        ax1.legend(loc=3)
     
    fig.savefig(my_func_name()+'.pdf')

def model_run(
        state_vector, 
        time_symbol, 
        net_input_fluxes, 
        lim_inf_300, 
        net_output_fluxes, 
        internal_fluxes,
        z_sym,
        epsilon_sym,
        u_t_z_exp,
        u_A,
        f_TA,
        func_dict,
        par_dict_v1,
        start_values, 
        z0,
        times
        ):
    # create the Models

    limited_srm = SmoothReservoirModel(state_vector, time_symbol, net_input_fluxes, net_output_fluxes, lim_inf_300)
    bm=BastinModel(limited_srm,u_t_z_exp,z_sym)
    
    # the systems start a little higher than the equilibrium
    # of the system with unconstrained fluxes
    
    
    # possibly nonlinear effects as a parameter dictionary
    u_t_z_exp_par=u_t_z_exp.subs(par_dict_v1)
    
        
    #f.savefig("limited_fluxes_ast.pdf")
    control_start_values = np.array(list(start_values)+[z0])
    control_start_values_z20 = np.array(list(start_values)+[20])
    control_start_values_z20000 = np.array(list(start_values)+[20000])
    legend_dict={
        'z0':z0,
        'epsilon':par_dict_v1[epsilon_sym]
    }
    parameter_str="\n".join([key+"="+str(val) for key,val in legend_dict.items()])
    file_name_str="__".join([key+"_"+str(val) for key,val in legend_dict.items()])
    start_values=control_start_values[:-1]
    bmr=BastinModelRun( bm, par_dict_v1, control_start_values, times, func_dict)
    
    #soln = unlimited_smr.solve()
    #limited_soln_uncontrolled = limited_smr.solve()
    
    limited_soln_controlled = bmr.solve()
    
    fig=plt.figure(figsize=(12,16))
    #fig.title('Total carbon'+title_suffs[version])
    ax_1_1=fig.add_subplot(4,1,1)
    ax_2_1=fig.add_subplot(4,1,2)
    ax_3_1=fig.add_subplot(4,1,3)
    ax_4_1=fig.add_subplot(4,1,4)
    
    ax_1_1=poolsizes(ax_1_1,times,limited_soln_controlled)
    ax_1_1.set_title("limited controlled_"+parameter_str)
    #ax_1_1.set_ylim(ax_1_1.get_ylim())
    
    ax_2_1.set_title("accounting pool z and sum")
    z_vals=limited_soln_controlled[:,3]
    sum_vals=limited_soln_controlled[:,0:3].sum(1)
    ax_2_1.plot(times, z_vals, label='u')
    ax_2_1.plot(times, sum_vals, label='sum ')
    ax_2_1.legend(loc=3)
    #ax_4_1.set_ylim(ax_1_1.get_ylim())
    
    
    # since we do not know the actual phi of the bastin model run 
    # we assume the most general case that after all paramteters
    # and functions have been substituted t,z remain as arguments
    # The actual expression might not even contain t but that is no
    # problem
    tup=(bm.time_symbol,bm.z_sym)
    times=bmr.times
    phi_num=bmr.phi_num(tup)
    ax_3_1.set_title("control u for limited")
    zval=limited_soln_controlled[:,3]
    u_vals=phi_num(times,zval)
    pe('times.shape',locals())
    pe('zval.shape',locals())
    ax_3_1.plot(times, u_vals, label='u')
    ax_3_1.legend(loc=3)
    ax_3_1.set_ylim([0,1])
    
    
    ax_4_1.plot(times, func_dict[u_A](times),label='u_A')
    ax_4_1.legend(loc=2)
    ax_4_1.set_xlabel('Time (yr)')
    ax_4_1.set_ylabel('Mass (PgC)')
    plt.subplots_adjust(hspace=0.4)
    file_name=my_func_name()+'_'+file_name_str+'.pdf'
    fig.savefig(file_name)

