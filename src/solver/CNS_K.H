#ifndef CNS_K_H_
#define CNS_K_H_

#include "CNS_index_macros.H"
#include <AMReX_FArrayBox.H>
#include <limits>
#include <cmath>

#include "cns_prob.H"
#include "CNS_parm.H"
#include "CNS_K.H"

AMREX_GPU_DEVICE AMREX_FORCE_INLINE
amrex::Real
cns_estdt (int i, int j, int k, amrex::Array4<Real const> const& state,
           amrex::GpuArray<amrex::Real,AMREX_SPACEDIM> const& dx,
           Parm const& parm) noexcept
{
    using amrex::Real;

    Real rho = state(i,j,k,URHO);
    Real mx  = state(i,j,k,UMX);
    Real my  = state(i,j,k,UMY);
#if (AMREX_SPACEDIM == 3)
    Real mz  = state(i,j,k,UMZ);
#endif
    Real ei  = state(i,j,k,UEINT);
    Real rhoinv = Real(1.0)/amrex::max(rho,parm.smallr);
    Real vx = mx*rhoinv;
    Real vy = my*rhoinv;
#if (AMREX_SPACEDIM == 3)
    Real vz = mz*rhoinv;
#endif
    Real p = amrex::max((parm.eos_gamma-Real(1.0))*ei, parm.smallp);
    Real cs = std::sqrt(parm.eos_gamma*p*rhoinv);
    Real dtx = dx[0]/(std::abs(vx)+cs);
    Real dty = dx[1]/(std::abs(vy)+cs);
#if (AMREX_SPACEDIM == 3)
    Real dtz = dx[2]/(std::abs(vz)+cs);
#endif

#if (AMREX_SPACEDIM == 2)
    return amrex::min(dtx,dty);
#else
    return amrex::min(dtx,amrex::min(dty,dtz));
#endif
}


AMREX_GPU_DEVICE AMREX_FORCE_INLINE
void
cns_compute_temperature (int i, int j, int k, amrex::Array4<amrex::Real> const& u,
                         Parm const& parm) noexcept
{
    using amrex::Real;

    if (parm.floor_rho > Real(0.0) && !(u(i,j,k,URHO) >= parm.floor_rho)) {
        // keep the velocity, raise the density
        Real fac = parm.floor_rho / u(i,j,k,URHO);
        if (!(fac > Real(0.0)) || fac > Real(1.e10)) { fac = Real(0.0); }
        u(i,j,k,UMX) *= fac;
        u(i,j,k,UMY) *= fac;
#if (AMREX_SPACEDIM == 3)
        u(i,j,k,UMZ) *= fac;
#endif
        u(i,j,k,URHO) = parm.floor_rho;
    }
    if (parm.floor_vmax > Real(0.0)) {
        // cap the speed; the kinetic energy removed stays in rho_E (becomes heat)
        Real m2 = AMREX_D_TERM(u(i,j,k,UMX)*u(i,j,k,UMX), +u(i,j,k,UMY)*u(i,j,k,UMY), +u(i,j,k,UMZ)*u(i,j,k,UMZ));
        Real mmax = parm.floor_vmax * u(i,j,k,URHO);
        if (m2 > mmax*mmax) {
            Real fac = mmax / std::sqrt(m2);
            AMREX_D_TERM(u(i,j,k,UMX) *= fac;, u(i,j,k,UMY) *= fac;, u(i,j,k,UMZ) *= fac;);
        }
    }
    Real rhoinv = Real(1.0)/u(i,j,k,URHO);
    Real mx = u(i,j,k,UMX);
    Real my = u(i,j,k,UMY);
#if (AMREX_SPACEDIM == 2)
    Real ke = Real(0.5) * rhoinv * (mx*mx+my*my);
#else
    Real mz = u(i,j,k,UMZ);
    Real ke = Real(0.5) * rhoinv * (mx*mx+my*my+mz*mz);
#endif
    u(i,j,k,UEINT) = u(i,j,k,UEDEN) - ke;
    if (parm.floor_p > Real(0.0)) {
        const Real eint_min = parm.floor_p/(parm.eos_gamma-Real(1.0));
        if (!(u(i,j,k,UEINT) >= eint_min)) {
            u(i,j,k,UEINT) = eint_min;
            u(i,j,k,UEDEN) = eint_min + ke;
        }
    }
    u(i,j,k,UTEMP) = rhoinv * u(i,j,k,UEINT) * (Real(1.0)/parm.cv);
}

#endif
