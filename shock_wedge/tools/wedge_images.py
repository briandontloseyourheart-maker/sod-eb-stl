"""Numerical Schlieren and interferogram images from 2D AMReX plotfiles.

Usage:
    python wedge_images.py RUN_DIR/plt00246 [more plotfiles ...] [--out DIR]
    python wedge_images.py RUN_DIR --all          # every plt* in RUN_DIR (for a movie)

Needs only NumPy and Matplotlib: the plotfile is read directly (no yt).
All AMR levels are put on the finest grid, coarse cells copied into their
fine children, then
  Schlieren      S = exp(-k |grad rho| / max|grad rho|)   (Quirk's numerical Schlieren)
  interferogram  I = cos^2(pi (rho - rho_ref) / drho)     (one fringe per drho)
Cells with vfrac = 0 (inside the wedge) are drawn black.
"""
import argparse
import re
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


def read_plotfile(path):
    """Return (variables, composite dict of arrays on the finest grid, extent, time)."""
    path = Path(path)
    lines = (path / 'Header').read_text().split('\n')
    nvar = int(lines[1])
    names = lines[2:2 + nvar]
    i = 2 + nvar
    dim = int(lines[i]); i += 1
    if dim != 2:
        raise SystemExit('This tool handles 2D plotfiles only')
    time = float(lines[i]); i += 1
    finest = int(lines[i]); i += 1
    lo = [float(v) for v in lines[i].split()]; i += 1
    hi = [float(v) for v in lines[i].split()]; i += 1
    i += 1  # ref ratios
    domains = re.findall(r'\(\((-?\d+),(-?\d+)\) \((-?\d+),(-?\d+)\)', lines[i])
    fine_lo = [int(domains[finest][0]), int(domains[finest][1])]
    fine_hi = [int(domains[finest][2]), int(domains[finest][3])]
    nx, ny = fine_hi[0] - fine_lo[0] + 1, fine_hi[1] - fine_lo[1] + 1
    out = np.zeros((nvar, ny, nx))
    for lev in range(finest + 1):
        ratio = 2 ** 0
        # ratio between this level and the finest, from domain sizes
        dlo = int(domains[lev][0]); dhi = int(domains[lev][2])
        ratio = nx // (dhi - dlo + 1)
        cell_h = (path / f'Level_{lev}' / 'Cell_H').read_text()
        boxes = re.findall(r'\(\((-?\d+),(-?\d+)\) \((-?\d+),(-?\d+)\) \(0,0\)\)', cell_h)
        fabs = re.findall(r'FabOnDisk: (\S+) (\d+)', cell_h)
        for (x0, y0, x1, y1), (fname, offset) in zip(boxes, fabs):
            x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
            with open(path / f'Level_{lev}' / fname, 'rb') as f:
                f.seek(int(offset))
                header = f.readline().decode()
                ncomp = int(header.split()[-1])
                bx, by = x1 - x0 + 1, y1 - y0 + 1
                dtype = '<f8' if '8 7 6 5 4 3 2 1' in header else '>f8'
                data = np.fromfile(f, dtype=dtype, count=ncomp * bx * by)
            data = data.reshape(ncomp, by, bx)
            if ratio > 1:
                data = data.repeat(ratio, axis=1).repeat(ratio, axis=2)
            out[:, y0 * ratio:(y1 + 1) * ratio, x0 * ratio:(x1 + 1) * ratio] = data[:nvar]
    fields = {n: out[k] for k, n in enumerate(names)}
    return fields, (lo[0], hi[0], lo[1], hi[1]), time


def wedge_polygon(inputs):
    """Triangle vertices from the wedge.* lines of an inputs file (None if absent)."""
    if not inputs or not Path(inputs).is_file():
        return None
    vals = {}
    for line in Path(inputs).read_text().splitlines():
        m = re.match(r'\s*wedge\.(\w+)\s*=\s*([-\d.eE+]+)', line)
        if m:
            vals[m.group(1)] = float(m.group(2))
    if not vals:  # e.g. an STL case: cells with vfrac = 0 are drawn black instead
        return None
    ax, ay = vals.get('apex_x', 3.0), vals.get('apex_y', 0.0)
    L, th = vals.get('length', 1.0), np.radians(vals.get('half_angle', 30.0))
    h = L * np.tan(th)
    return np.array([[ax, ay], [ax + L, ay - h], [ax + L, ay + h]])


def make_images(fields, extent, k, drho, rho_ref, gmax=None):
    rho = fields['density']
    solid = fields['vfrac'] <= 0.0
    dx = (extent[1] - extent[0]) / rho.shape[1]
    gy, gx = np.gradient(rho, dx)
    grad = np.hypot(gx, gy)
    # gradients that touch a covered cell are meaningless
    near = solid.copy()
    for s in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        near |= np.roll(solid, s, axis=(0, 1))
    grad[near] = 0.0
    # gmax: fixed normalisation (same for every frame, so an animation does not flicker)
    norm = gmax if gmax else max(grad.max(), 1e-30)
    schlieren = np.exp(-k * grad / norm)
    fringes = np.cos(np.pi * (rho - rho_ref) / drho) ** 2
    schlieren[solid] = np.nan
    fringes[solid] = np.nan
    return schlieren, fringes


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('paths', nargs='+', type=Path, help='plotfile(s), or a run directory with --all')
    p.add_argument('--all', action='store_true', help='process every plt* directory in the given run directory')
    p.add_argument('--out', type=Path, default=None, help='output folder (default: next to the plotfiles)')
    p.add_argument('--inputs', type=Path, default=None, help='inputs file for the exact wedge outline')
    p.add_argument('--k', type=float, default=15.0, help='Schlieren sensitivity')
    p.add_argument('--drho', type=float, default=0.02, help='density change per interference fringe')
    p.add_argument('--rho-ref', type=float, default=1.0, help='density of the reference beam')
    p.add_argument('--gmax', type=float, default=None,
                   help='fixed |grad rho| for the Schlieren scale (default: each frame\'s own maximum)')
    p.add_argument('--xlim', type=float, nargs=2, default=None)
    p.add_argument('--ylim', type=float, nargs=2, default=None)
    args = p.parse_args()

    plts = []
    for path in args.paths:
        plts += sorted(path.glob('plt*')) if args.all else [path]
    plts = [q for q in plts if (q / 'Header').is_file()]
    if not plts:
        raise SystemExit('No plotfiles found')
    inputs = args.inputs or next((c for c in [plts[0].parent / 'inputs', plts[0].parent / 'inputs.used'] if c.is_file()), None)
    tri = wedge_polygon(inputs)

    blues = LinearSegmentedColormap.from_list('schl', ['#08306b', '#2171b5', '#c6dbef', '#fdf8f8'])
    fringe = LinearSegmentedColormap.from_list('fringe', ['#08306b', '#4a7fb5', '#d4dbec'])
    for cm in (blues, fringe):
        cm.set_bad('black')

    for plt_dir in plts:
        fields, extent, time = read_plotfile(plt_dir)
        schl, fr = make_images(fields, extent, args.k, args.drho, args.rho_ref, args.gmax)
        h_over_w = (extent[3] - extent[2]) / (extent[1] - extent[0])
        if h_over_w < 0.5:   # long, flat domain: put the two images one above the other
            fig, axes = plt.subplots(2, 1, figsize=(16, 2 * 16 * h_over_w + 1.0), facecolor='black',
                                     layout='constrained')
        else:
            fig, axes = plt.subplots(1, 2, figsize=(16, 6.6), facecolor='black', layout='constrained')
        for ax, img, cmap, title in [(axes[0], fr, fringe, 'Numerical interferogram'),
                                     (axes[1], schl, blues, 'Numerical Schlieren')]:
            ax.imshow(img, origin='lower', extent=extent, cmap=cmap, vmin=0, vmax=1,
                      interpolation='nearest')
            if tri is not None:
                ax.fill(tri[:, 0], tri[:, 1], color='black', zorder=3)
            if args.xlim: ax.set_xlim(*args.xlim)
            if args.ylim: ax.set_ylim(*args.ylim)
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_title(f'{title},  t = {time:.3f}', color='white')
        out_dir = args.out or plt_dir.parent / 'images'
        out_dir.mkdir(parents=True, exist_ok=True)
        name = out_dir / f'{plt_dir.name}.png'
        fig.savefig(name, dpi=130, facecolor='black')
        plt.close(fig)
        print(name)


if __name__ == '__main__':
    main()
