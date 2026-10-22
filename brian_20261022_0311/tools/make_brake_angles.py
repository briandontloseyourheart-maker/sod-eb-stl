"""Make brake STLs with the four plates opened to any angle, from the 90-degree STL.

    python make_brake_angles.py ../../brake_shock_3d/brake.stl --angles 0 30 60 90 --out ..

Writes brake_000.stl, brake_030.stl, ... (closed, non-overlapping solids).

Geometry of the input (lengths in STL units, body axis = x, nose at x = 0):
  * each plate is a curved panel (edges bent toward the tail), x = 4.77..4.98,
    from r = 1.10 out to r = 2.28, width +-0.53;
  * its hinge (the two small pins in the STL) is at x = 4.81, r = 1.045, axis tangential;
  * a thin fin-shaped strut (0.04 thick) runs from the back of each plate to the
    body at x = 5.85.

Angle = angle between plate and body surface: 90 = as in the STL (plate radial),
0 = folded flat on the body, tip toward the tail. The plate swings about its hinge,
so it opens forward into the oncoming flow.

Simplifications: the struts (actuator braces) are removed at every angle, because
their shape at other angles is not known; the hinge pins are replaced by a small
solid hinge block that keeps each plate attached to the body.
Needs: numpy, trimesh, manifold3d.
"""
import argparse
from pathlib import Path

import numpy as np
import trimesh

HINGE_X, HINGE_R = 4.81, 1.045
PLATE_BOX = dict(x=(4.70, 4.985), r=(1.10, 2.40), t=0.60)    # region holding one (curved) plate
STRUT_BOX = dict(x=(4.985, 5.95), r=(1.005, 1.40), t=0.06)   # region holding one strut (0.04 thick fin)


def box(x, r, t, axis):
    """Axis-aligned box for the plate on direction axis (0: +y, 1: -y, 2: +z, 3: -z)."""
    lo = np.array([x[0], r[0], -t]); hi = np.array([x[1], r[1], t])
    b = trimesh.creation.box(bounds=[lo, hi])
    return b.apply_transform(frame(axis))


def frame(axis):
    """Rotation about x taking the +y plate frame to plate number axis."""
    ang = [0.0, np.pi, np.pi / 2, -np.pi / 2][axis]
    return trimesh.transformations.rotation_matrix(ang, [1, 0, 0])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('stl', type=Path)
    p.add_argument('--angles', type=float, nargs='+', default=[0, 30, 60, 90])
    p.add_argument('--out', type=Path, default=Path('.'))
    args = p.parse_args()

    m = trimesh.load(args.stl, force='mesh')
    parts = m.split(only_watertight=False)
    body = max(parts, key=lambda q: len(q.faces))   # drop the 8 small hinge pins
    print(f'input: {len(m.faces)} faces, kept main shell with {len(body.faces)}, watertight={body.is_watertight}')

    cut = trimesh.boolean.union([box(**PLATE_BOX, axis=a) for a in range(4)] +
                                [box(**STRUT_BOX, axis=a) for a in range(4)], engine='manifold')
    bare = trimesh.boolean.difference([body, cut], engine='manifold')
    plate0 = trimesh.boolean.intersection([body, box(**PLATE_BOX, axis=0)], engine='manifold')
    # hinge block: tangential cylinder through the hinge, joins plate root and body
    hinge0 = trimesh.creation.cylinder(radius=0.075, height=0.20, sections=48)
    hinge0.apply_translation([HINGE_X, HINGE_R, 0.0])     # cylinder axis is z = tangential for +y plate
    print(f'plate faces {len(plate0.faces)}, bare body faces {len(bare.faces)}')

    args.out.mkdir(parents=True, exist_ok=True)
    for angle in args.angles:
        # rotate the +y plate about the hinge axis (z through hinge) toward +x by (90 - angle)
        rot = trimesh.transformations.rotation_matrix(-np.radians(90.0 - angle), [0, 0, 1],
                                                      point=[HINGE_X, HINGE_R, 0.0])
        pieces = [bare]
        for a in range(4):
            # folded plates would rest exactly on the body surface (a 0.001 sliver of gas
            # under them); sink them slightly so plate and body overlap: 0.012 at 0 deg, 0 at 90
            sink = trimesh.transformations.translation_matrix([0, -0.012 * np.cos(np.radians(angle)), 0])
            pl = plate0.copy().apply_transform(rot).apply_transform(sink).apply_transform(frame(a))
            hg = hinge0.copy().apply_transform(frame(a))
            pieces += [pl, hg]
        solid = trimesh.boolean.union(pieces, engine='manifold')
        name = args.out / f'brake_{int(round(angle)):03d}.stl'
        solid.export(name)
        print(f'{name}: {len(solid.faces)} faces, watertight={solid.is_watertight}, '
              f'bounds {np.round(solid.bounds, 3).tolist()}')


if __name__ == '__main__':
    main()
