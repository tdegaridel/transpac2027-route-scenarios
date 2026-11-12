import json, numpy as np
from matplotlib.path import Path
import os
G=os.environ.get('GEO_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))+'/'
def to360(lon): return np.where(np.asarray(lon)<0, np.asarray(lon)+360, lon)
def short(n):
    m={'Papua New Guinean':'Papua New Guinea','Micronesian':'Federated States of Micronesia','Solomon Islands':'Solomon Islands','Nauruan':'Nauru','Tuvaluan':'Tuvalu','Samoan':'Samoa','Fijian':'Fiji','Vanuatuan':'Vanuatu','Marshallese':'Marshall Islands','Tongan':'Tonga'}
    for k,v in m.items():
        if n.startswith(k): return v
    if 'Kiribati' in n: return 'Kiribati'+(' ('+n.split('(')[1] if '(' in n else '')
    if 'United States' in n: return 'USA ('+n.split('(')[1]
    if 'New Zealand' in n: return ('NZ ('+n.split('(')[1]) if '(' in n else 'New Zealand'
    if 'French' in n: return 'France ('+n.split('(')[1]
    if 'Australian' in n: return 'Australia'+(' (Norfolk)' if 'Norfolk' in n else '')
    return n
POLYS=[]
seen=set()
for f in ['eez_w.json','eez_e.json']:
    for ft in json.load(open(G+f))['features']:
        name=ft['properties'].get('geoname'); key=(name,ft['properties'].get('mrgid'))
        if key in seen: continue
        seen.add(key)
        g=ft['geometry']; polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for poly in polys:
            ring=np.array(poly[0]); lon=to360(ring[:,0])
            # handle polygons spanning antimeridian: if span>180 shift
            if lon.max()-lon.min()>180: lon=np.where(lon<180,lon+360,lon)
            step=max(1,len(lon)//4000)
            xy=np.c_[lon,ring[:,1]][::step]
            POLYS.append((short(name),name,Path(xy),[Path(np.c_[to360(np.array(h)[:,0]),np.array(h)[:,1]][::max(1,len(h)//2000)]) for h in poly[1:]],(xy[:,0].min(),xy[:,0].max(),xy[:,1].min(),xy[:,1].max())))
_C={}
def eez(lat,lon):
    x=float(to360(lon)); k=(round(lat,2),round(x,2))
    if k in _C: return _C[k]
    r='High seas'
    for s,n,p,holes,bb in POLYS:
        for xx in (x,x+360):
            if bb[0]<=xx<=bb[1] and bb[2]<=lat<=bb[3] and p.contains_point((xx,lat)) and not any(h.contains_point((xx,lat)) for h in holes):
                r=s;break
        if r!='High seas': break
    _C[k]=r; return r
def asc(f):
    with open(G+f) as fh:
        h={}
        for _ in range(6):
            k,v=fh.readline().split(); h[k.lower()]=float(v)
        z=np.loadtxt(fh)
    z[z==h['nodata_value']]=np.nan
    ny,nx=z.shape
    lon=h['xllcorner']+h['cellsize']*(np.arange(nx)+0.5); lat=h['yllcorner']+h['cellsize']*(np.arange(ny)[::-1]+0.5)
    return lon,lat,z
