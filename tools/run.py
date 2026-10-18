"""Create an isolated run directory; record inputs, arguments and solver exit status."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from check import check

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--exe',type=Path,default=ROOT/'build/bin/sod_eb_stl')
    p.add_argument('--output',type=Path,default=ROOT/'results/sphere_stl')
    p.add_argument('--threads',type=int,default=4)
    p.add_argument('--ncell',type=int,default=64)
    p.add_argument('--stop-time',type=float,default=.2)
    args=p.parse_args()
    if args.threads<1 or args.ncell<16 or args.ncell%8 or not 0<args.stop_time<=.2:
        p.error('threads>=1, ncell>=16 divisible by 8, and 0<stop-time<=0.2 required')
    exe=args.exe.resolve(); out=args.output.resolve()
    if not exe.is_file(): p.error('Build first: cmake --build build -j 8')
    if out.exists() and any(out.iterdir()): p.error('Output is not empty; choose a new --output directory')
    out.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'cases/sphere_stl/inputs',out/'inputs.used')
    shutil.copy2(ROOT/'geometry/sphere.stl',out/'sphere.stl')
    cmd=[str(exe),'inputs.used',f'amr.n_cell={args.ncell} {args.ncell} {args.ncell}',f'stop_time={args.stop_time}']
    env=os.environ.copy(); env['OMP_NUM_THREADS']=str(args.threads)
    record={'command':cmd,'cwd':str(out),'OMP_NUM_THREADS':args.threads,'returncode':None,
            'stl_sha256':hashlib.sha256((out/'sphere.stl').read_bytes()).hexdigest(),
            'geometry_type':'stl'}
    record_path=out/'run.json';record_path.write_text(json.dumps(record,indent=2)+'\n')
    print(f'Running in {out}',flush=True)
    with (out/'run.log').open('w') as log:
        result=subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
    record['returncode']=result.returncode;record_path.write_text(json.dumps(record,indent=2)+'\n')
    if result.returncode: raise SystemExit(f'Solver failed ({result.returncode}); inspect {out}/run.log')
    print(json.dumps(check(out,args.stop_time),indent=2))


if __name__=='__main__': main()
