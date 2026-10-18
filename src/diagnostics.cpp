#include "diagnostics.H"
#include "CNS.H"
#include <AMReX_EBFArrayBox.H>
#include <AMReX_MultiFabUtil.H>
#include <AMReX_BoxIterator.H>
#include <AMReX_ParmParse.H>
#include <fstream>
#include <iomanip>
#include <limits>
#include <cmath>

void observe(amrex::Amr& amr, bool initial, bool slice)
{
    using namespace amrex;
    AMREX_ALWAYS_ASSERT(ParallelDescriptor::NProcs() == 1);
    Gpu::streamSynchronize();
    Real z=.5;
    ParmParse("study").query("slice_z",z);
    std::ofstream image;
    if(slice) {
        image.open(initial ? "slice_initial.csv" : "slice_final.csv");
        AMREX_ALWAYS_ASSERT(image.good());
        image << std::setprecision(17) << "time,level,x,y,z,dx,vfrac,density,pressure,u,v,w\n";
    }
    Real fluid=0,mass=0,energy=0,rmin=std::numeric_limits<Real>::max(),rmax=0,pmin=rmin,pmax=0;
    Long cuts=0, cells=0;
    for(int l=0;l<=amr.finestLevel();++l) {
        auto& lev=amr.getLevel(l);
        auto const& s=lev.get_new_data(CNS::conservedStateType());
        auto const& factory=dynamic_cast<EBFArrayBoxFactory const&>(s.Factory());
        auto const& vf=factory.getVolFrac();
        auto dx=lev.Geom().CellSizeArray();
        auto lo=lev.Geom().ProbLoArray();
        Real dv=dx[0]*dx[1]*dx[2];
        int kz=static_cast<int>(std::floor((z-lo[2])/dx[2]));
        iMultiFab mask;
        if(l<amr.finestLevel()) mask=makeFineMask(s,amr.boxArray(l+1),amr.refRatio(l),1,0);
        for(MFIter mfi(s);mfi.isValid();++mfi) {
            auto a=s.const_array(mfi); auto f=vf.const_array(mfi);
            Array4<int const> m;
            if(l<amr.finestLevel()) m=mask.const_array(mfi);
            for(BoxIterator it(mfi.validbox());it.ok();++it) {
                auto iv=it();
                if(l<amr.finestLevel() && m(iv)==0) continue;
                Real fraction=f(iv),rho=0,p=0,u=0,v=0,w=0;
                fluid+=fraction*dv; ++cells;
                if(fraction>0) {
                    for(int n=0;n<NUM_STATE;++n) AMREX_ALWAYS_ASSERT(std::isfinite(a(iv,n)));
                    rho=a(iv,URHO);
                    AMREX_ALWAYS_ASSERT(rho>0);
                    u=a(iv,UMX)/rho; v=a(iv,UMY)/rho; w=a(iv,UMZ)/rho;
                    p=(CNS::h_parm->eos_gamma-1)*a(iv,UEINT);
                    AMREX_ALWAYS_ASSERT(p>0 && std::isfinite(p));
                    rmin=std::min(rmin,rho); rmax=std::max(rmax,rho);
                    pmin=std::min(pmin,p); pmax=std::max(pmax,p);
                    mass+=rho*fraction*dv; energy+=a(iv,UEDEN)*fraction*dv;
                    if(fraction<1) ++cuts;
                }
                if(slice && iv[2]==kz) image << amr.cumTime() << ',' << l << ','
                    << lo[0]+(iv[0]+.5)*dx[0] << ',' << lo[1]+(iv[1]+.5)*dx[1] << ','
                    << lo[2]+(iv[2]+.5)*dx[2] << ',' << dx[0] << ',' << fraction << ','
                    << rho << ',' << p << ',' << u << ',' << v << ',' << w << '\n';
            }
        }
    }
    // Final slice is requested after the last step: do not duplicate that CSV row.
    if(!initial && slice) return;
    std::ofstream out("diagnostics.csv",initial ? std::ios::out : std::ios::app);
    AMREX_ALWAYS_ASSERT(out.good());
    if(initial) out << "step,time,finest_level,composite_cells,cut_cells,fluid_volume,mass,total_energy,rho_min,rho_max,p_min,p_max\n";
    out << std::setprecision(17) << amr.levelSteps(0) << ',' << amr.cumTime() << ','
        << amr.finestLevel() << ',' << cells << ',' << cuts << ',' << fluid << ',' << mass << ','
        << energy << ',' << rmin << ',' << rmax << ',' << pmin << ',' << pmax << '\n';
}
