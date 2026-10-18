import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from check import check

exe,inputs,root,mesh=sys.argv[1:]
Path(root).mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='sphere-',dir=root) as work:
    shutil.copy2(mesh,Path(work)/'sphere.stl')
    env=os.environ.copy();env['OMP_NUM_THREADS']='2'
    with open(Path(work)/'run.log','w') as log:
        r=subprocess.run([exe,inputs,'amr.n_cell=32 32 32','stop_time=0.01',
                          'amr.plot_files_output=0'],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:
        print((Path(work)/'run.log').read_text());sys.exit(r.returncode)
    print(check(work,.01))
