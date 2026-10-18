"""Schlieren and interferogram images of plane slices through 3D AMReX plotfiles.

Usage:
    python slice_images.py RUN_DIR/plt00013                      # z = 0.01 (mid-span) and y = 0.01
    python slice_images.py RUN_DIR/plt00013 --slice z=0.5 --slice z=1.5
    python slice_images.py RUN_DIR --all                         # every plt* in RUN_DIR

Each slice takes the cell layer that contains the plane on every AMR level and
puts it on the finest grid (coarse cells copied into their fine children); the
image formulas are those of ../../shock_wedge/tools/wedge_images.py:
  Schlieren      S = exp(-k |grad rho| / max|grad rho|)   (gradient within the plane)
  interferogram  I = cos^2(pi (rho - rho_ref) / drho)
Cells inside the wedge (vfrac = 0) are drawn black. A slice is not a
line-of-sight integral; for a shadowgraph-like view open the plotfile in ParaView.
Needs only NumPy and Matplotlib.
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'shock_wedge' / 'tools'))
from wedge_images import make_images  # noqa: E402

AXES = 'xyz'


def read_slice(path, axis, pos):
    """Return (fields on the plane, extent of the plane, labels, time)."""
    path = Path(path)
    lines = (path / 'Header').read_text().split('\n')
    nvar = int(lines[1])
    names = lines[2:2 + nvar]
    i = 2 + nvar
    if int(lines[i]) != 3:
        raise SystemExit('This tool handles 3D plotfiles only')
    i += 1
    time = float(lines[i]); i += 1
    finest = int(lines[i]); i += 1
    lo = [float(v) for v in lines[i].split()]; i += 1
    hi = [float(v) for v in lines[i].split()]; i += 1
    i += 1  # ref ratios
    doms = [tuple(map(int, d)) for d in re.findall(r'\(\((\d+),(\d+),(\d+)\) \((\d+),(\d+),(\d+)\)', lines[i])]
    if not lo[axis] <= pos <= hi[axis]:
        raise SystemExit(f'{AXES[axis]} = {pos} is outside the domain')
    plane = [d for d in range(3) if d != axis]          # the two in-plane directions
    nfine = [doms[finest][3 + d] + 1 for d in range(3)]
    out = np.zeros((nvar, nfine[plane[1]], nfine[plane[0]]))
    for lev in range(finest + 1):
        n = [doms[lev][3 + d] + 1 for d in range(3)]
        r = nfine[0] // n[0]
        dx = (hi[axis] - lo[axis]) / n[axis]
        k = min(int((pos - lo[axis]) / dx), n[axis] - 1)
        cell_h = (path / f'Level_{lev}' / 'Cell_H').read_text()
        boxes = re.findall(r'\(\((-?\d+),(-?\d+),(-?\d+)\) \((-?\d+),(-?\d+),(-?\d+)\) \(0,0,0\)\)', cell_h)
        fabs = re.findall(r'FabOnDisk: (\S+) (\d+)', cell_h)
        for b, (fname, offset) in zip(boxes, fabs):
            b = list(map(int, b))
            blo, bhi = b[:3], b[3:]
            if not blo[axis] <= k <= bhi[axis]:
                continue
            with open(path / f'Level_{lev}' / fname, 'rb') as f:
                f.seek(int(offset))
                header = f.readline().decode()
                ncomp = int(header.split()[-1])
                shape = [bhi[d] - blo[d] + 1 for d in range(3)]
                dtype = '<f8' if '8 7 6 5 4 3 2 1' in header else '>f8'
                data = np.fromfile(f, dtype=dtype, count=ncomp * shape[0] * shape[1] * shape[2])
            data = data.reshape(ncomp, shape[2], shape[1], shape[0])   # (comp, z, y, x)
            sl = data[:, k - blo[2], :, :] if axis == 2 else (
                 data[:, :, k - blo[1], :] if axis == 1 else data[:, :, :, k - blo[0]])
            # sl is (comp, plane[1], plane[0])
            sl = sl.repeat(r, axis=1).repeat(r, axis=2)
            a0, a1 = blo[plane[0]] * r, blo[plane[1]] * r
            out[:, a1:a1 + sl.shape[1], a0:a0 + sl.shape[2]] = sl[:nvar]
    extent = (lo[plane[0]], hi[plane[0]], lo[plane[1]], hi[plane[1]])
    return {nm: out[c] for c, nm in enumerate(names)}, extent, (AXES[plane[0]], AXES[plane[1]]), time


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('paths', nargs='+', type=Path)
    p.add_argument('--all', action='store_true', help='process every plt* directory in the given run directory')
    p.add_argument('--slice', action='append', default=None,
                   help='plane as axis=value, e.g. z=0.01; repeatable (default z=0.01 and y=0.01)')
    p.add_argument('--out', type=Path, default=None)
    p.add_argument('--k', type=float, default=15.0)
    p.add_argument('--drho', type=float, default=0.02)
    p.add_argument('--rho-ref', type=float, default=1.0)
    args = p.parse_args()
    slices = []
    for s in args.slice or ['z=0.01', 'y=0.01']:
        a, v = s.split('=')
        slices.append((AXES.index(a.strip()), float(v)))

    plts = []
    for path in args.paths:
        plts += sorted(path.glob('plt*')) if args.all else [path]
    plts = [q for q in plts if (q / 'Header').is_file()]
    if not plts:
        raise SystemExit('No plotfiles found')

    blues = LinearSegmentedColormap.from_list('schl', ['#08306b', '#2171b5', '#c6dbef', '#fdf8f8'])
    fringe = LinearSegmentedColormap.from_list('fringe', ['#08306b', '#4a7fb5', '#d4dbec'])
    for cm in (blues, fringe):
        cm.set_bad('black')

    for plt_dir in plts:
        for axis, pos in slices:
            fields, extent, labels, time = read_slice(plt_dir, axis, pos)
            schl, fr = make_images(fields, extent, args.k, args.drho, args.rho_ref)
            aspect = (extent[3] - extent[2]) / (extent[1] - extent[0])
            fig, axes = plt.subplots(1, 2, figsize=(16, 8 * aspect + 0.8), facecolor='black',
                                     layout='constrained')
            for ax, img, cmap, title in [(axes[0], fr, fringe, 'Interferogram'),
                                         (axes[1], schl, blues, 'Schlieren')]:
                ax.imshow(img, origin='lower', extent=extent, cmap=cmap, vmin=0, vmax=1,
                          interpolation='nearest')
                ax.set_xticks([]); ax.set_yticks([])
                ax.set_title(f'{title}, {AXES[axis]} = {pos:g} slice ({labels[0]}-{labels[1]} plane), '
                             f't = {time:.3f}', color='white')
            out_dir = args.out or plt_dir.parent / 'images'
            out_dir.mkdir(parents=True, exist_ok=True)
            name = out_dir / f'{plt_dir.name}_{AXES[axis]}{pos:g}.png'
            fig.savefig(name, dpi=120, facecolor='black')
            plt.close(fig)
            print(name)


if __name__ == '__main__':
    main()
