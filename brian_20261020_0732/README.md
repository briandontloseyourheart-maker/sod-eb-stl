# brian_20261020_0732: supersonic flow around a cylinder (Mach 3, STL, 2D)

Mach 3 flow past a circular cylinder in a channel of height 4 D with slip walls.
The bow shock reflects off the channel walls, the reflected shocks cross the wake,
and the wake behind the cylinder sheds vortices. The cylinder is an STL.

## Build, run, plot

```bash
# from the repository root, AMReX checked out next to it (same commit as the main README)
cmake -S brian_20261020_0732 -B build-cyl -DAMREX_SOURCE_DIR=../amrex
cmake --build build-cyl -j 8
mkdir -p results/cyl && cd results/cyl
cp ../../brian_20261020_0732/inputs ../../brian_20261020_0732/cylinder.stl .
OMP_NUM_THREADS=8 ../../build-cyl/bin/cylinder_mach3 inputs
python3 ../../shock_wedge/tools/wedge_images.py plt0XXXX --k 25 --drho 0.1   # Schlieren + interferogram
python3 ../../shock_wedge/tools/wedge_images.py . --all --k 25 --drho 0.1     # every frame, for a movie
```

A checkpoint is written every 5 time units; continue a run with `amr.restart=chkXXXXX`.
In ParaView, `../shock_wedge/tools/paraview_schlieren.py` gives the same Schlieren.

## Setup

| | value |
|---|---|
| Domain | x 0 to 16, y -2 to 2 (D = 1) |
| Cylinder | `cylinder.stl`, diameter 1, centre (1.9937, 0.0031), 512 facets, extruded in z |
| Freestream | rho = 1, p = 1/gamma (c = 1), u = 3 (M = 3), gamma = 1.4 |
| Grid | 256 x 64 base (dx = D/16), 3 levels of ratio 2, finest dx = D/128 |
| x boundaries | supersonic inflow of the freestream (1) / outflow (2) |
| y boundaries | slip walls (3) |
| Refinement | cut cells, and density jump > 0.05 between neighbours |
| Run | to t = 20 (3.75 flow-through times) |

Units: lengths in D, time in D/c. The freestream crosses the domain in 5.3 time units.

### Three things needed to make it run

1. **Start-up.** Filling the whole domain with Mach 3 flow at t = 0 makes the gas
   behind the cylinder pull away from its rear wall into near-vacuum, and the run
   blows up in the first step (negative density in the rear cut cells, time step
   collapses to 0). Instead the gas starts at rest for x > `prob.x_start` = 1 and
   the Mach 3 stream enters behind a start-up shock, which sweeps past the cylinder
   and leaves the domain.
2. **Cylinder position.** With the centre at exactly (2, 0) the cylinder touches
   grid lines at its front, back, top and bottom, which makes degenerate cut
   cells. The small offset avoids that and also breaks the up-down symmetry, so the
   wake starts shedding vortices on its own.
3. **Limiter and redistribution weights.** Even then, with the solver's default
   MC slope limiter and equal flux-redistribution weights, the start-up shock
   hitting the small cut cells on the cylinder face drove the pressure negative
   there (same with an exact analytic circle, so it is not the STL). The inputs use
   `cns.plm_theta = 1` (minmod) and `cns.eb_weights_type = 3` (volume-fraction
   weights); `../src/solver/CNS.cpp` now reads `cns.plm_theta` and `cns.plm_iorder`
   from the inputs (defaults unchanged, so the other cases are not affected).

## Files

- `src/`: freestream initial state and supersonic inflow boundary. `main.cpp`, the
  EB setup and the solver are shared with `../shock_wedge/src` and `../src/solver`.
- `tools/generate_cylinder_stl.py`: writes `cylinder.stl` (`--center`, `--radius`,
  `--segments`). Any closed STL works in its place.

The reference picture is likely viscous (Navier-Stokes); this case is inviscid
Euler, so the shear layers roll up through numerical dissipation and their fine
structure depends on the grid.
