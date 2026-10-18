"""Compare final composite cell layers on a common pixel grid, only in shared fluid."""
import argparse
import json
from pathlib import Path
import numpy as np

def load(folder):
    d=np.atleast_1d(np.genfromtxt(folder/'slice_final.csv',delimiter=',',names=True))
    return d

def raster(d,n):
    values=np.full((3,n,n),np.nan);count=np.zeros((n,n),int)
    for r in d:
        i=int(round((r['x']-r['dx']/2)*n));j=int(round((r['y']-r['dx']/2)*n))
        w=int(round(r['dx']*n));assert w>=1
        count[j:j+w,i:i+w]+=1
        values[:,j:j+w,i:i+w]=np.array([r['vfrac'],r['density'],r['pressure']])[:,None,None]
    assert np.all(count==1), 'Overlapping or missing composite slice cells'
    return values

p=argparse.ArgumentParser();p.add_argument('stl',type=Path);p.add_argument('analytic',type=Path);args=p.parse_args()
a,b=load(args.stl),load(args.analytic)
assert np.allclose(a['time'],.2) and np.allclose(b['time'],.2)
n=int(round(1/min(a['dx'].min(),b['dx'].min())))
va,vb=raster(a,n),raster(b,n)
mask=(va[0]>0)&(vb[0]>0)
report={'time':.2,'comparison':'cell-constant composite z layer on shared fluid pixels','grid':[n,n],
        'shared_fluid_pixels':int(mask.sum()),'solid_classification_different_pixels':int(np.sum((va[0]>0)!=(vb[0]>0)))}
for i,name in [(1,'density'),(2,'pressure')]:
    delta=abs(va[i][mask]-vb[i][mask]);report[name]={'mean_absolute_difference':float(delta.mean()),'max_absolute_difference':float(delta.max())}
(args.stl/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
