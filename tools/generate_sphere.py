"""Deterministic, watertight, outward-oriented binary STL (standard library only)."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import struct

ROOT=Path(__file__).resolve().parents[1]
C=(.7,.5,.5); R=.125; NLON=128; NLAT=64

def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def float32(p): return struct.unpack('<3f',struct.pack('<3f',*p))

def main():
    vertices=[float32((C[0],C[1],C[2]+R))]
    for j in range(1,NLAT):
        theta=math.pi*j/NLAT
        for i in range(NLON):
            phi=2*math.pi*i/NLON
            vertices.append(float32((C[0]+R*math.sin(theta)*math.cos(phi),
                                     C[1]+R*math.sin(theta)*math.sin(phi),C[2]+R*math.cos(theta))))
    vertices.append(float32((C[0],C[1],C[2]-R)))
    def idx(j,i): return 1+(j-1)*NLON+i%NLON
    faces=[]
    for i in range(NLON): faces.append((0,idx(1,i),idx(1,i+1)))
    for j in range(1,NLAT-1):
        for i in range(NLON):
            a,b,c,d=idx(j,i),idx(j,i+1),idx(j+1,i),idx(j+1,i+1)
            faces.extend([(a,c,b),(b,c,d)])
    for i in range(NLON): faces.append((len(vertices)-1,idx(NLAT-1,i+1),idx(NLAT-1,i)))
    oriented=[];volume=0.;edges=Counter();directions=Counter();payload=[]
    assert len(set(vertices))==len(vertices)
    for face in faces:
        a,b,c=(vertices[i] for i in face);normal=cross(sub(b,a),sub(c,a))
        center=tuple((x+y+z)/3 for x,y,z in zip(a,b,c))
        if dot(normal,sub(center,C))<0:
            face=(face[0],face[2],face[1]);a,b,c=(vertices[i] for i in face)
            normal=cross(sub(b,a),sub(c,a))
        norm=math.sqrt(dot(normal,normal));assert norm>0
        normal=tuple(x/norm for x in normal)
        volume+=dot(sub(a,C),cross(sub(b,C),sub(c,C)))/6
        for i,j in zip(face,face[1:]+face[:1]):
            edges[tuple(sorted((i,j)))]+=1;directions[(i,j)]+=1
        payload.append(struct.pack('<12fH',*normal,*a,*b,*c,0));oriented.append(face)
    assert all(v==2 for v in edges.values()), 'Not a closed two-manifold'
    assert all(directions[(j,i)]==1 for i,j in directions), 'Inconsistent winding'
    assert len(vertices)-len(edges)+len(faces)==2
    exact=4*math.pi*R**3/3
    assert abs(volume/exact-1)<.002
    output=ROOT/'geometry/sphere.stl'
    output.write_bytes(b'Sod sphere; dimensionless; outward normals'.ljust(80,b' ')+struct.pack('<I',len(faces))+b''.join(payload))
    report={'format':'binary STL','center':C,'radius':R,'longitude_segments':NLON,'latitude_segments':NLAT,
            'vertices':len(vertices),'triangles':len(faces),'closed_two_manifold':True,
            'consistent_outward_winding':True,'volume':volume,'analytic_volume':exact,
            'relative_volume_error':abs(volume/exact-1),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    (ROOT/'geometry/audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
