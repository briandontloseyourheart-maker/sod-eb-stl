"""Write a closed binary STL of the triangular wedge, extruded along z.

In a 2D AMReX build (eb2.geom_type = stl) the STL is cut by the plane z = 0,
so the prism spans z in [-depth/2, depth/2]. Defaults match the wedge.* values
in ../inputs: apex (3, 0), length 1, half-angle 30 deg (equilateral).

    python3 generate_wedge_stl.py [--out wedge.stl] [--apex 3 0] [--length 1] [--half-angle 30]
"""
import argparse
import math
import struct
from pathlib import Path


def prism_triangles(ax, ay, length, half_angle, depth):
    h = length * math.tan(math.radians(half_angle))
    base = [(ax, ay), (ax + length, ay - h), (ax + length, ay + h)]  # counter-clockwise
    z0, z1 = -depth / 2, depth / 2
    lo = [(x, y, z0) for x, y in base]
    hi = [(x, y, z1) for x, y in base]
    tris = [(lo[0], lo[2], lo[1]),      # bottom cap, normal -z
            (hi[0], hi[1], hi[2])]      # top cap, normal +z
    for a in range(3):
        b = (a + 1) % 3
        tris += [(lo[a], lo[b], hi[b]), (lo[a], hi[b], hi[a])]  # side faces, normals outward
    return tris


def normal(t):
    u = [t[1][i] - t[0][i] for i in range(3)]
    v = [t[2][i] - t[0][i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    s = math.sqrt(sum(c * c for c in n))
    return [c / s for c in n]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'wedge.stl')
    p.add_argument('--apex', type=float, nargs=2, default=[3.0, 0.0])
    p.add_argument('--length', type=float, default=1.0)
    p.add_argument('--half-angle', type=float, default=30.0)
    p.add_argument('--depth', type=float, default=1.0, help='extrusion in z, centred on z = 0')
    a = p.parse_args()
    tris = prism_triangles(a.apex[0], a.apex[1], a.length, a.half_angle, a.depth)
    with open(a.out, 'wb') as f:
        f.write(b'wedge prism for AMReX EB'.ljust(80, b' '))
        f.write(struct.pack('<I', len(tris)))
        for t in tris:
            f.write(struct.pack('<3f', *normal(t)))
            for v in t:
                f.write(struct.pack('<3f', *v))
            f.write(struct.pack('<H', 0))
    print(f'{a.out}: {len(tris)} triangles')


if __name__ == '__main__':
    main()
