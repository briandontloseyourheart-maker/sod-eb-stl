#ifndef CNS_PROB_H_
#define CNS_PROB_H_

#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include "CNS_index_macros.H"
#include "CNS_parm.H"
#include "cns_prob_parm.H"

// Write the freestream state into components [comp0, comp0+ncomp) of one cell;
// orig_comp is the state index of comp0.
AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
void cns_set_freestream (int i, int j, int k, amrex::Array4<amrex::Real> const& s,
                         int comp0, int ncomp, int orig_comp,
                         Parm const& parm, ProbParm const& pp, bool moving = true)
{
    using amrex::Real;
    const Real ei = pp.p/(parm.eos_gamma-Real(1.0));
    const Real u = moving ? pp.u : Real(0.0);
    for (int n = 0; n < ncomp; ++n) {
        Real v = Real(0.0);
        switch (orig_comp+n) {
        case URHO:  v = pp.rho; break;
        case UMX:   v = pp.rho*u; break;
        case UEDEN: v = ei + Real(0.5)*pp.rho*u*u; break;
        case UEINT: v = ei; break;
        case UTEMP: v = ei/(pp.rho*parm.cv); break;
        default:    v = Real(0.0); // y (and z) momentum
        }
        s(i,j,k,comp0+n) = v;
    }
}

AMREX_GPU_DEVICE
inline
void
cns_initdata (int i, int j, int k, amrex::Array4<amrex::Real> const& state,
              amrex::GeometryData const& geomdata, Parm const& parm, ProbParm const& prob_parm)
{
    const amrex::Real x = geomdata.ProbLo()[0] + (i+amrex::Real(0.5))*geomdata.CellSize()[0];
    cns_set_freestream(i, j, k, state, 0, NUM_STATE, 0, parm, prob_parm, x < prob_parm.x_start);
}

#endif
