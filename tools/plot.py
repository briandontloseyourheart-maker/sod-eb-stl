"""Composite cell slices; no interpolation across AMR levels or solid cells."""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle, Circle

p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args()
data=[np.atleast_1d(np.genfromtxt(args.output/f'slice_{label}.csv',delimiter=',',names=True)) for label in ['initial','final']]
fig,axes=plt.subplots(2,2,figsize=(11,10),constrained_layout=True)
for i,(field,title) in enumerate([('density','Density'),('pressure','Pressure')]):
    vals=np.concatenate([d[field][d['vfrac']>0] for d in data]);vmin=vals.min();vmax=vals.max()
    for j,d in enumerate(data):
        ax=axes[i,j];fluid=d[d['vfrac']>0];solid=d[d['vfrac']==0]
        patches=[Rectangle((r['x']-r['dx']/2,r['y']-r['dx']/2),r['dx'],r['dx']) for r in fluid]
        pc=PatchCollection(patches,cmap='viridis',edgecolors='none');pc.set_array(fluid[field]);pc.set_clim(vmin,vmax);ax.add_collection(pc)
        for r in solid:ax.add_patch(Rectangle((r['x']-r['dx']/2,r['y']-r['dx']/2),r['dx'],r['dx'],color='lightgray',linewidth=0))
        ax.add_patch(Circle((.7,.5),.125,fill=False,color='black',lw=.7,ls='--'))
        ax.set(xlim=(0,1),ylim=(0,1),aspect='equal',xlabel='x',ylabel='y',title=f'{title}, t={d["time"][0]:.4f}')
        fig.colorbar(pc,ax=ax,shrink=.8)
fig.suptitle('Sod + STL sphere (Euler): cell layer at/above z=0.5; dashed circle = sphere midplane')
fig.savefig(args.output/'fields.png',dpi=150);plt.close(fig)
d=np.atleast_1d(np.genfromtxt(args.output/'diagnostics.csv',delimiter=',',names=True))
fig,axes=plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
for ax,keys in zip(axes.flat,[['rho_min','rho_max'],['p_min','p_max'],['cut_cells','composite_cells'],['mass','total_energy']]):
    for key in keys:
        y=d[key]/d[key][0]-1 if key in ['mass','total_energy'] else d[key]
        ax.plot(d['time'],y,label=key)
    ax.set_xlabel('Time');ax.legend();ax.grid(alpha=.2)
axes[1,1].set_ylabel('Relative change from initial value')
fig.savefig(args.output/'diagnostics.png',dpi=150);plt.close(fig)
print(args.output/'fields.png')
