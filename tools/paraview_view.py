"""Run with ParaView: View > Python Shell > Run Script.

Default result location is ../results/sphere_stl relative to this script.
Works with a Windows UNC script path or a Linux path, when the data is local to ParaView.
"""
from pathlib import Path
from paraview.simple import (AMReXBoxLibGridReader, Slice, Show, ColorBy,
    GetActiveViewOrCreate, GetColorTransferFunction, GetAnimationScene, Render)

folder=Path(__file__).resolve().parents[1]/'results/sphere_stl'
files=sorted(str(p) for p in folder.glob('plt[0-9][0-9][0-9][0-9][0-9]') if (p/'Header').is_file())
if not files: raise RuntimeError(f'No plotfiles in {folder}')
flow=AMReXBoxLibGridReader(registrationName='Sod STL time series',FileNames=files)
flow.CellArrayStatus=['density','pressure','x_velocity','vfrac']
flow.UpdatePipelineInformation()
section=Slice(registrationName='Sphere center slice',Input=flow)
section.SliceType='Plane'
section.SliceType.Origin=[.5,.5,.5]
section.SliceType.Normal=[0,0,1]
view=GetActiveViewOrCreate('RenderView')
display=Show(section,view)
ColorBy(display,('CELLS','pressure'))
GetColorTransferFunction('pressure').RescaleTransferFunction(.1,1.)
display.SetScalarBarVisibility(view,True)
view.CameraPosition=[.5,.5,3]
view.CameraFocalPoint=[.5,.5,.5]
view.CameraViewUp=[0,1,0]
view.CameraParallelProjection=1
view.CameraParallelScale=.58
scene=GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()
scene.PlayMode='Snap To TimeSteps'
scene.GoToLast()
Render()
print('Times:',list(flow.TimestepValues))
