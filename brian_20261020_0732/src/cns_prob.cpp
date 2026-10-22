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
            ppp.query("rho", pp.rho);
            ppp.query("p", pp.p);
            ppp.query("x_start", pp.x_start);
        }
        AMREX_ALWAYS_ASSERT(pp.mach > 0.0 && pp.rho > 0.0 && pp.p > 0.0);
        const amrex::Real c = std::sqrt(CNS::h_parm->eos_gamma*pp.p/pp.rho);
        pp.u = pp.mach*c;
        amrex::Print() << "[cylinder] freestream M = " << pp.mach << ", rho = " << pp.rho
                       << ", p = " << pp.p << ", c = " << c << ", u = " << pp.u << "\n";
        amrex::Gpu::copy(amrex::Gpu::hostToDevice, CNS::h_prob_parm, CNS::h_prob_parm+1,
                         CNS::d_prob_parm);
    }
}
