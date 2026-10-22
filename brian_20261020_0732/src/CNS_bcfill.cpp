#include <AMReX_FArrayBox.H>
#include <AMReX_Geometry.H>
#include <AMReX_PhysBCFunct.H>
#include "CNS.H"
#include "cns_prob.H"

using namespace amrex;

// cns.lo_bc = 1 (inflow -> BCType::ext_dir) on x-lo feeds the supersonic freestream.
struct CnsFillExtDir
{
    Parm parm;
    ProbParm prob;

    AMREX_GPU_DEVICE
    void operator() (const IntVect& iv, Array4<Real> const& dest,
                     const int dcomp, const int numcomp,
                     GeometryData const& geom, const Real /*time*/,
                     const BCRec* bcr, const int bcomp,
                     const int orig_comp) const
    {
        if (iv[0] >= geom.Domain().smallEnd(0)) { return; }
        for (int n = 0; n < numcomp; ++n) {
            if (bcr[bcomp+n].lo(0) == BCType::ext_dir) {
                cns_set_freestream(iv[0], iv[1], AMREX_D_PICK(0,0,iv[2]), dest,
                                   dcomp+n, 1, orig_comp+n, parm, prob);
            }
        }
    }
};

void cns_bcfill (Box const& bx, FArrayBox& data,
                 int dcomp, int numcomp,
                 Geometry const& geom, Real time,
                 const Vector<BCRec>& bcr, int bcomp,
                 int scomp)
{
    GpuBndryFuncFab<CnsFillExtDir> gpu_bndry_func(CnsFillExtDir{*CNS::h_parm, *CNS::h_prob_parm});
    gpu_bndry_func(bx,data,dcomp,numcomp,geom,time,bcr,bcomp,scomp);
}
