# ParaView Python Shell script: numerical Schlieren (right) and interferogram (left)
# from the AMReX plotfile series that is already loaded in ParaView.
#
# Use: select the plt reader in the Pipeline Browser, then
#      View -> Python Shell -> Run Script -> choose this file.
# Works with ParaView 5.10 or newer (older versions: see the try/except fallbacks).

from paraview.simple import *

K     = 15.0    # Schlieren sensitivity: bigger = darker, thicker lines
DRHO  = 0.02    # density change per interference fringe: smaller = more fringes
RHO0  = 1.0     # reference density (still gas)

src = GetActiveSource()
if src is None:
    raise RuntimeError('Select the plt reader in the Pipeline Browser first')

# Make sure density and vfrac are loaded from the plotfile.
try:
    src.CellArrayStatus = ['density', 'vfrac']
except Exception:
    pass
src.UpdatePipeline()
has_vfrac = 'vfrac' in src.CellData.keys()

# ---- Schlieren: S = exp(-K |grad rho| / max|grad rho|) ----
try:
    grad = Gradient(registrationName='GradRho', Input=src)
except Exception:  # ParaView < 5.10
    grad = GradientOfUnstructuredDataSet(registrationName='GradRho', Input=src)
grad.ScalarArray = ['CELLS', 'density']
grad.ResultArrayName = 'Gradient'
grad.UpdatePipeline()
gmax = grad.CellData['Gradient'].GetRange(-1)[1]   # largest |grad rho| at this time
if gmax <= 0:
    gmax = 1.0

schl = Calculator(registrationName='Schlieren', Input=grad)
schl.AttributeType = 'Cell Data'
schl.ResultArrayName = 'Schlieren'
schl.Function = 'exp(-%g*mag(Gradient)/%g)' % (K, gmax)

# ---- Interferogram: I = cos^2(pi (rho - RHO0) / DRHO) ----
fringe = Calculator(registrationName='Interferogram', Input=src)
fringe.AttributeType = 'Cell Data'
fringe.ResultArrayName = 'Fringe'
fringe.Function = 'cos(3.14159265*(density-%g)/%g)^2' % (RHO0, DRHO)


def drop_solid(inp, name):
    """Remove cells inside the wedge (vfrac = 0); the black background shows through."""
    if not has_vfrac:
        return inp
    thr = Threshold(registrationName=name, Input=inp)
    thr.Scalars = ['CELLS', 'vfrac']
    try:
        thr.LowerThreshold = 1e-6
        thr.UpperThreshold = 10.0
    except Exception:  # ParaView < 5.10
        thr.ThresholdRange = [1e-6, 10.0]
    return thr


schl_out = drop_solid(schl, 'SchlierenFluid')
fringe_out = drop_solid(fringe, 'InterferogramFluid')

# ---- two views side by side ----
layout = GetLayout()
left = GetActiveViewOrCreate('RenderView')
for s in list(GetSources().values()):
    Hide(s, left)
right = CreateView('RenderView')
try:
    layout.SplitHorizontal(0, 0.5)
    AssignViewToLayout(view=right, layout=layout, hint=2)
except Exception:
    AssignViewToLayout(view=right, layout=layout)


def show(data, view, array):
    disp = Show(data, view)
    ColorBy(disp, ('CELLS', array))
    lut = GetColorTransferFunction(array)
    lut.ApplyPreset('Blues', True)        # white -> dark blue
    lut.InvertTransferFunction()          # 0 (shock) dark, 1 (uniform flow) light
    lut.RescaleTransferFunction(0.0, 1.0)
    lut.AutomaticRescaleRangeMode = 'Never'
    disp.SetScalarBarVisibility(view, False)
    try:
        view.UseColorPaletteForBackground = 0
    except Exception:
        pass
    view.Background = [0.0, 0.0, 0.0]     # wedge cells were removed -> black
    view.OrientationAxesVisibility = 0
    view.InteractionMode = '2D'
    view.ResetCamera()
    return disp


show(fringe_out, left, 'Fringe')
show(schl_out, right, 'Schlieren')
AddCameraLink(left, right, 'SchlierenLink')   # zoom/pan both together
Render(left)
Render(right)

# ---- optional: save the picture of the current time, or every time step ----
# SaveScreenshot('wedge.png', layout, ImageResolution=[2400, 900])
# SaveAnimation('frames/wedge.png', layout, ImageResolution=[2400, 900])   # wedge.0000.png, ...
print('Schlieren normalised with max|grad rho| = %g at this time' % gmax)
