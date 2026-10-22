#ifndef CNS_PROB_PARM_H_
#define CNS_PROB_PARM_H_

#include <AMReX_REAL.H>
#include <AMReX_GpuMemory.H>

using namespace amrex::literals;

// Uniform freestream at Mach number `mach` in +x, fed in at x-lo. At t = 0 the
// gas is at rest (same rho, p) for x >= x_start: starting the whole domain at
// Mach 3 makes the gas behind the cylinder pull away from its wall into
// near-vacuum and the run blows up in the first step.
struct ProbParm
{
    amrex::Real mach  = 3.0;
    amrex::Real rho   = 1.0;
    amrex::Real p     = 1.0/1.4;  // p = 1/gamma -> c = 1, so u = M
    amrex::Real u     = 0.0;      // computed: mach * c
    amrex::Real x_start = 1.0;    // freestream for x < x_start at t = 0, rest beyond
};

#endif
