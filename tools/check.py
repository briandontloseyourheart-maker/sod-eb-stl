"""Checks actual composite-AMR diagnostics, without optional plotting dependencies."""
import argparse
import csv
import json
import math
from pathlib import Path


def check(output, stop_time):
    output=Path(output)
    with (output/'diagnostics.csv').open() as f:
        rows=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
    assert len(rows)>1, 'No time advancement'
    assert abs(rows[-1]['time']-stop_time)<1e-10, 'Did not reach requested stop_time'
    assert all(b['time']>a['time'] for a,b in zip(rows,rows[1:])), 'Unordered times'
    sphere=4*math.pi*.125**3/3
    assert abs(rows[0]['time'])<1e-14
    assert abs(rows[0]['rho_min']-.125)<1e-10 and abs(rows[0]['rho_max']-1)<1e-10
    assert abs(rows[0]['p_min']-.1)<1e-10 and abs(rows[0]['p_max']-1)<1e-10
    # Sphere is entirely in the right initial state. This checks masking and volume weights.
    assert abs(rows[0]['mass']-(.5625-.125*sphere))<.03*.125*sphere
    assert abs(rows[0]['total_energy']-(1.375-.25*sphere))<.03*.25*sphere
    max_volume_error=0.
    for row in rows:
        assert all(math.isfinite(v) for v in row.values()), 'Nonfinite diagnostics'
        assert row['rho_min']>0 and row['p_min']>0, 'Nonpositive state'
        assert row['cut_cells']>0 and row['finest_level']==1, 'Missing EB/AMR'
        max_volume_error=max(max_volume_error,abs((1-row['fluid_volume'])-sphere)/sphere)
    assert max_volume_error<.03, 'Sphere volume error exceeds 3%'
    mass_change=max(abs(r['mass']/rows[0]['mass']-1) for r in rows)
    energy_change=max(abs(r['total_energy']/rows[0]['total_energy']-1) for r in rows)
    assert mass_change<.005 and energy_change<.005, 'Composite conservation drift exceeds 0.5%'
    for filename in ['slice_initial.csv','slice_final.csv']:
        with (output/filename).open() as f: data=list(csv.DictReader(f))
        assert data, 'Missing slice data'
        for row in data:
            assert all(math.isfinite(float(v)) for v in row.values())
            vf=float(row['vfrac'])
            assert 0<=vf<=1
            if vf>0: assert float(row['density'])>0 and float(row['pressure'])>0
        expected=0 if filename=='slice_initial.csv' else stop_time
        assert all(abs(float(r['time'])-expected)<1e-10 for r in data)
    report={'passed':True,'steps':int(rows[-1]['step']),'final_time':rows[-1]['time'],
            'max_sphere_volume_relative_error':max_volume_error,
            'max_mass_relative_change':mass_change,'max_energy_relative_change':energy_change,
            'final_cut_cells':int(rows[-1]['cut_cells']),
            'min_density':min(r['rho_min'] for r in rows),'min_pressure':min(r['p_min'] for r in rows)}
    (output/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--stop-time',type=float,default=.2)
    args=parser.parse_args()
    print(json.dumps(check(args.output,args.stop_time),indent=2))
