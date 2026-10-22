"""Drag coefficient from the solver's forces.dat, for one or more runs.

    python drag_plot.py run000/forces.dat:0 run030/forces.dat:30 run060/forces.dat:60 run090/forces.dat:90

Each argument is FILE:ANGLE. forces.dat holds "time Fx Fy Fz", the pressure force on the
computed quarter of the body (pressure relative to the freestream). The full-body drag
is 4 Fx, and
    C_D = 4 Fx / (0.5 rho u^2 A),   A = pi R^2,  R = 1.118 (largest body radius).
With rho = 1, u = 2 (Mach 2, sound speed 1): 0.5 rho u^2 = 2.

Writes drag.png (C_D against time for every run, and the settled C_D against angle)
and prints the settled value = mean over the last --avg fraction of the run.
Needs NumPy and Matplotlib.
"""
import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('runs', nargs='+', help='FILE:ANGLE')
    p.add_argument('--rho', type=float, default=1.0)
    p.add_argument('--u', type=float, default=2.0)
    p.add_argument('--radius', type=float, default=1.118)
    p.add_argument('--avg', type=float, default=0.25, help='fraction of the run (at the end) to average')
    p.add_argument('--out', type=Path, default=Path('drag.png'))
    args = p.parse_args()

    q_area = 0.5 * args.rho * args.u ** 2 * np.pi * args.radius ** 2
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8), layout='constrained')
    angles, cds = [], []
    for item in args.runs:
        fname, ang = item.rsplit(':', 1)
        d = np.loadtxt(fname, ndmin=2)
        t, cd = d[:, 0], 4.0 * d[:, 1] / q_area
        settled = cd[t >= t[-1] - args.avg * t[-1]].mean()
        angles.append(float(ang)); cds.append(settled)
        a1.plot(t, cd, label=f'{ang}°')
        print(f'angle {ang:>4}: C_D = {settled:.3f}  (mean over t = {t[-1]*(1-args.avg):.1f} to {t[-1]:.1f})')
    a1.set_xlabel('time'); a1.set_ylabel('C_D'); a1.set_title('Drag coefficient during the run')
    a1.legend(); a1.grid(alpha=.3)
    order = np.argsort(angles)
    a2.plot(np.array(angles)[order], np.array(cds)[order], 'o-')
    a2.set_xlabel('plate angle (deg)'); a2.set_ylabel('settled C_D'); a2.set_title('Drag against plate angle, Mach 2')
    a2.grid(alpha=.3)
    fig.savefig(args.out, dpi=120)
    print(args.out)


if __name__ == '__main__':
    main()
