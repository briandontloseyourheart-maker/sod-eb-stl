# brake_shock_3d: Mach 1.3 shock along a body with deployed brake plates (STL, 3D)

Same M = 1.3 planar shock as `../shock_wedge` and `../shock_wedge_3d`, now running
along your `brake.stl`: a body of radius about 1.0-1.12 from the nose (x = 0) to the
tail (x = 6.5), with four brake plates at x = 4.77-4.98 that reach r = 2.28, one on
each of the +y, -y, +z, -z axes. The STL is used exactly as uploaded.


## Build, run, plot

```bash
# from the repository root, AMReX checked out next to it (same commit as the main README)
cmake -S brake_shock_3d -B build-brake -DAMREX_SOURCE_DIR=../amrex
cmake --build build-brake -j 8
mkdir -p results/brake && cd results/brake
cp ../../brake_shock_3d/inputs ../../brake_shock_3d/brake.stl .
OMP_NUM_THREADS=8 ../../build-brake/bin/brake_shock_3d inputs
python3 ../../shock_wedge_3d/tools/slice_images.py plt00XXX --slice z=0.01 --slice x=4.87
python3 ../../shock_wedge_3d/tools/slice_images.py . --all          # every frame
```

Quick check first: add `amr.max_level=1 stop_time=0.3` to the run line.

## STL check

| | |
|---|---|
| Triangles | 71,618 (binary STL) |
| Closed | yes: every edge is shared by exactly two triangles |
| Normals | outward (stored normals agree with the vertex order), signed volume 19.56 |
| Bounding box | x 0 to 6.498, y and z -2.279 to 2.279 |

Because it is already positioned, `eb2.stl_scale = 1` and `eb2.stl_center = 0 0 0`.

## Setup

| | value |
|---|---|
| Domain | x -2 to 10, y 0 to 5, z 0 to 5: one quarter, since the body is symmetric about y = 0 and z = 0 |
| Grid | 96 x 40 x 40 base (dx = 0.125), 2 levels of ratio 2, finest dx = 0.03125 (about 7 cells across a plate) |
| Initial state | Rankine-Hugoniot jump for `prob.mach = 1.3`, shock at x = -1 |
| Timing | shock reaches the nose at t = 0.77, the plates at t = 4.4, the tail at t = 5.8; run to t = 6 |
| x boundaries | inflow of the post-shock state (1) / outflow (2) |
| y, z boundaries | symmetry (3) on the planes through the axis / outflow (2) on the far sides |
| Refinement | cut cells, and density jump > 0.01 between neighbours |

The plates are thin compared with the coarse cells, so AMReX could not build the
coarse EB level by coarsening the fine one ("Failed to build required coarse EB
level 1"). The inputs set `eb2.build_coarse_level_by_coarsening = 0`, which builds
every level straight from the STL; `../shock_wedge/src/CNS_init_eb2.cpp` now reads
that option.

The C++ is shared, nothing is copied: the solver is `../src/solver` and the shock
setup is `../shock_wedge/src`. `CMakeLists.txt` here is the 3D build.

## Images

Use `../shock_wedge_3d/tools/slice_images.py` (any 3D plotfile works). Useful slices:
`z=0.01` (symmetry plane through the +y plate), `x=4.87` (cross-section through
the plates) and `x=2` (along the body). For a 3D view, open the plotfiles in
ParaView and use `../shock_wedge/tools/paraview_schlieren.py` on a Slice filter, or a
density Contour.
