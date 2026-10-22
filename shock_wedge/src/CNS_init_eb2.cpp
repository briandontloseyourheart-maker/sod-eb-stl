#include <AMReX_EB2.H>
#include <AMReX_EB2_GeometryShop.H>
#include <AMReX_ParmParse.H>
#include "WedgeIF.H"

// eb2.geom_type = wedge   -> finite triangular wedge from the "wedge.*" inputs
// any other eb2.geom_type -> AMReX built-ins (sphere, parser, stl, ...)
//
// eb2.build_coarse_level_by_coarsening = 0 builds every AMR level's EB directly
// from the geometry instead of coarsening the finest one. Needed for thin parts
// (e.g. brake plates) that cannot be coarsened cleanly ("Failed to build
// required coarse EB level").
void initialize_EB2 (const amrex::Geometry& geom, int required, int maximum)
{
    using namespace amrex;
    std::string geom_type;
    bool by_coarsening = true;
    ParmParse ppeb("eb2");
    ppeb.query("geom_type", geom_type);
    ppeb.query("build_coarse_level_by_coarsening", by_coarsening);
    if (geom_type == "wedge") {
        ParmParse pp("wedge");
        Real apex_x = 3.0, apex_y = 0.0, length = 1.0, half_angle = 30.0;
        pp.query("apex_x", apex_x);
        pp.query("apex_y", apex_y);
        pp.query("length", length);
        pp.query("half_angle", half_angle);
        EB2::GeometryShop<WedgeIF> gshop(WedgeIF(apex_x, apex_y, length, half_angle));
        EB2::Build(gshop, geom, required, maximum, 4, by_coarsening);
    } else {
        EB2::Build(geom, required, maximum, 4, by_coarsening);
    }
}
