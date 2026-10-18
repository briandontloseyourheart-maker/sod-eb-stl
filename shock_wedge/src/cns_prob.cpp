#include <AMReX_PROB_AMR_F.H>
#include <AMReX_ParmParse.H>
#include <AMReX_Print.H>
#include "cns_prob_parm.H"
#include "CNS.H"
#include <cmath>

extern "C" {
    void amrex_probinit (const int* /*init*/,
                         const int* /*name*/,
                         const int* /*namelen*/,
                         const amrex_real* /*problo*/,
                         const amrex_real* /*probhi*/)
    {
        auto& pp = *CNS::h_prob_parm;
        {
            amrex::ParmParse ppp("prob");
            ppp.query("mach", pp.mach);
            ppp.query("x_shock", pp.x_shock);
            ppp.query("rho_1", pp.rho_1);
            ppp.query("p_1", pp.p_1);
        }
        AMREX_ALWAYS_ASSERT(pp.mach > 1.0 && pp.rho_1 > 0.0 && pp.p_1 > 0.0);

        // Rankine-Hugoniot jump for a normal shock moving at W = M*c_1 into gas at rest.
        const amrex::Real g = CNS::h_parm->eos_gamma;
        const amrex::Real M2 = pp.mach*pp.mach;
        const amrex::Real c1 = std::sqrt(g*pp.p_1/pp.rho_1);
        const amrex::Real rho_ratio = (g+1.0)*M2/((g-1.0)*M2+2.0);
        pp.rho_2 = pp.rho_1*rho_ratio;
        pp.p_2   = pp.p_1*(1.0 + 2.0*g/(g+1.0)*(M2-1.0));
        pp.u_2   = pp.mach*c1*(1.0 - 1.0/rho_ratio);

        amrex::Print() << "[shock_wedge] M = " << pp.mach << ", shock speed W = " << pp.mach*c1
                       << "\n  pre-shock  rho,p,u = " << pp.rho_1 << ", " << pp.p_1 << ", 0"
                       << "\n  post-shock rho,p,u = " << pp.rho_2 << ", " << pp.p_2 << ", " << pp.u_2
                       << "\n";

        amrex::Gpu::copy(amrex::Gpu::hostToDevice, CNS::h_prob_parm, CNS::h_prob_parm+1,
                         CNS::d_prob_parm);
    }
}
