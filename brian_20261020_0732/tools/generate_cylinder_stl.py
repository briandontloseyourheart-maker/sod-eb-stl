"""Write a closed binary STL of a circular cylinder with its axis along z.

In a 2D AMReX build (eb2.geom_type = stl) the STL is cut by the plane z = 0,
so the cylinder spans z in [-depth/2, depth/2] and its cross-section is the circle.

    python3 generate_cylinder_stl.py [--out cylinder.stl] [--center 2 0] [--radius 0.5] [--segments 512]
"""
import argparse
import math
import struct
from pathlib import Path


def triangles(cx, cy, r, nseg, depth):
    z0, z1 = -depth / 2, depth / 2
    ring = [(cx + r * math.cos(2 * math.pi * k / nseg), cy + r * math.sin(2 * math.pi * k / nseg))
            for k in range(nseg)]
    tris = []
    for k in range(nseg):
        (xa, ya), (xb, yb) = ring[k], ring[(k + 1) % nseg]
        a0, b0, a1, b1 = (xa, ya, z0), (xb, yb, z0), (xa, ya, z1), (xb, yb, z1)
        tris += [(a0, b0, b1), (a0, b1, a1)]                       # side, normal outward
        tris += [((cx, cy, z1), a1, b1), ((cx, cy, z0), b0, a0)]   # caps, normals +z / -z
    return tris


def normal(t):
    u = [t[1][i] - t[0][i] for i in range(3)]
    v = [t[2][i] - t[0][i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    s = math.sqrt(sum(c * c for c in n))
    return [c / s for c in n]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'cylinder.stl')
    p.add_argument('--center', type=float, nargs=2, default=[2.0, 0.0])
    p.add_argument('--radius', type=float, default=0.5)
    p.add_argument('--segments', type=int, default=512, help='facets around the circle')
    p.add_argument('--depth', type=float, default=1.0, help='extrusion in z, centred on z = 0')
    a = p.parse_args()
    tris = triangles(a.center[0], a.center[1], a.radius, a.segments, a.depth)
    with open(a.out, 'wb') as f:
        f.write(b'cylinder for AMReX EB'.ljust(80, b' '))
        f.write(struct.pack('<I', len(tris)))
        for t in tris:
            f.write(struct.pack('<3f', *normal(t)))
            for v in t:
                f.write(struct.pack('<3f', *v))
            f.write(struct.pack('<H', 0))
    print(f'{a.out}: {len(tris)} triangles')


if __name__ == '__main__':
    main()
