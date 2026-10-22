#ifndef WEDGE_IF_H_
#define WEDGE_IF_H_

#include <AMReX_Array.H>
#include <AMReX_EB2_IF_Base.H>
#include <cmath>

// Implicit function of a finite triangular wedge (a prism along z in 3D).
// AMReX EB2 convention: > 0 inside the body, < 0 in the fluid.
// The apex points upstream (-x); the flat base is at x = apex_x + length.
class WedgeIF
    : amrex::GPUable
{
public:
    WedgeIF (amrex::Real apex_x, amrex::Real apex_y, amrex::Real length, amrex::Real half_angle_deg)
    {
        const amrex::Real h = length*std::tan(half_angle_deg*amrex::Real(M_PI)/amrex::Real(180.0));
        // Counter-clockwise vertices: apex, lower base corner, upper base corner.
        m_x[0] = apex_x;        m_y[0] = apex_y;
        m_x[1] = apex_x+length; m_y[1] = apex_y-h;
        m_x[2] = apex_x+length; m_y[2] = apex_y+h;
    }

    [[nodiscard]] AMREX_GPU_HOST_DEVICE AMREX_FORCE_INLINE
    amrex::Real operator() (AMREX_D_DECL(amrex::Real x, amrex::Real y, amrex::Real /*z*/)) const noexcept
    {
        // Distance to each edge, positive on the inner side; the minimum is
        // positive only inside the triangle.
        amrex::Real f = amrex::Real(1.e30);
        for (int e = 0; e < 3; ++e) {
            const int n = (e+1)%3;
            const amrex::Real ex = m_x[n]-m_x[e], ey = m_y[n]-m_y[e];
            const amrex::Real d = (ex*(y-m_y[e]) - ey*(x-m_x[e]))/std::sqrt(ex*ex+ey*ey);
            f = amrex::min(f, d);
        }
        return f;
    }

    [[nodiscard]] inline amrex::Real operator() (const amrex::RealArray& p) const noexcept
    {
        return this->operator()(AMREX_D_DECL(p[0],p[1],p[2]));
    }

private:
    amrex::Real m_x[3]{}, m_y[3]{};
};

#endif
