#ifndef CNS_PROB_PARM_H_
#define CNS_PROB_PARM_H_

#include <AMReX_REAL.H>
#include <AMReX_GpuMemory.H>

using namespace amrex::literals;

// Planar shock of Mach number `mach` moving in +x into still gas (state 1).
// State 2 (behind the shock) is filled in amrex_probinit from the
// Rankine-Hugoniot relations, so only state 1 and the Mach number are inputs.
struct ProbParm
{
    amrex::Real mach    = 1.3;
    amrex::Real x_shock = 2.5;     // initial shock position
    amrex::Real rho_1   = 1.0;     // pre-shock (still) gas
    amrex::Real p_1     = 1.0/1.4; // p = 1/gamma  ->  sound speed c_1 = 1
    amrex::Real rho_2   = 0.0;     // post-shock gas, computed
    amrex::Real p_2     = 0.0;
    amrex::Real u_2     = 0.0;
};

#endif
