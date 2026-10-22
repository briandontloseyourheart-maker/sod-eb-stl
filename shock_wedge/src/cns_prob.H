#ifndef CNS_PROB_H_
#define CNS_PROB_H_

#include <AMReX_Geometry.H>
#include <AMReX_FArrayBox.H>
#include "CNS_index_macros.H"
#include "CNS_parm.H"
#include "cns_prob_parm.H"

// Fill one cell with either the post-shock (x < x_shock) or still (x >= x_shock) state.
AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
void cns_set_shock_state (int i, int j, int k, amrex::Array4<amrex::Real> const& s,
                          int comp0, int ncomp, int orig_comp, bool behind,
                          Parm const& parm, ProbParm const& pp)
{
    using amrex::Real;
    const Real rho = behind ? pp.rho_2 : pp.rho_1;
    const Real p   = behind ? pp.p_2   : pp.p_1;
    const Real u   = behind ? pp.u_2   : Real(0.0);
    const Real ei  = p/(parm.eos_gamma-Real(1.0));
    for (int n = 0; n < ncomp; ++n) {
        Real v = Real(0.0);
        switch (orig_comp+n) {
        case URHO:  v = rho; break;
        case UMX:   v = rho*u; break;
        case UEDEN: v = ei + Real(0.5)*rho*u*u; break;
        case UEINT: v = ei; break;
        case UTEMP: v = ei/(rho*parm.cv); break;
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
    cns_set_shock_state(i, j, k, state, 0, NUM_STATE, 0, x < prob_parm.x_shock, parm, prob_parm);
}

#endif
