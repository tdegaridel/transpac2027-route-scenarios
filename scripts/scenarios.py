"""TransPac 2027 (legs 1-2, Noumea - Apia - Papeete): three route scenarios.

A  Route v2 (16 Sep 2026) as planned, with EEZ zones re-checked.
B  Water-column (hydrology/biology) stations every 2-3 days, partly decoupled from coring.
C  No access to Papua New Guinea waters.
"""
import sys, os, json, math, csv, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import openpyxl
from geo import eez, asc, POLYS, to360

OUT = sys.argv[1]
SCR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'input') + '/'
SPEED = 10.0  # knots
CODES = ['CS', 'C1', 'C2', 'MN', 'NP', 'NM', 'CA', 'MT']
WATER = ['C1', 'MN', 'NP', 'NM']          # water-column biology ops movable to hydro stations
HYDRO = {'C1': 2, 'C2': 3, 'MN': 2, 'NP': 1, 'NM': 1}   # standalone hydro station, 9 h (CP_130 template)
LEG = {'1': dict(start=dt.datetime(2027, 7, 13, 8), limit_days=26, name='Leg 1  Nouméa – Apia'),
       '2': dict(start=dt.datetime(2027, 8, 31, 8), limit_days=23, name='Leg 2  Apia – Papeete')}

# ---------- bathymetry for depth estimates ----------
BW = asc('west.asc'); BE = asc('east.asc'); BO = asc('ojp.asc')
def depth(lat, lon):
    lon = float(lon)
    for (gx, gy, gz) in ([BO] if 155 <= lon <= 162 and -5 <= lat <= 4.5 else []) + ([BW] if lon > 0 else [BE]):
        i = int(np.argmin(abs(gx - lon))); j = int(np.argmin(abs(gy - lat)))
        v = gz[j, i]
        if not np.isnan(v):
            return int(round(-v))
    return None

def depths(pts):
    """vectorized depth (m, positive down) for an array of (lat, lon); land/unknown -> -9999"""
    pts = np.asarray(pts); out = np.full(len(pts), -9999.0)
    for (gx, gy, gz) in (BW, BE):
        lon = pts[:, 1]
        m = (lon >= gx[0] - 0.05) & (lon <= gx[-1] + 0.05) & (pts[:, 0] >= gy[-1] - 0.05) & (pts[:, 0] <= gy[0] + 0.05)
        if m.any():
            i = np.clip(np.round((lon[m] - gx[0]) / (gx[1] - gx[0])).astype(int), 0, len(gx) - 1)
            j = np.clip(np.round((gy[0] - pts[m, 0]) / (gy[0] - gy[1])).astype(int), 0, len(gy) - 1)
            v = -gz[j, i]; v[np.isnan(v)] = -9999; out[m] = v
    return out

# ---------- stations from route v2 ----------
def load_v2():
    wb = openpyxl.load_workbook(SCR + '20260916_TransPac_route_v2.xlsx', data_only=True)
    legs = {}
    for leg, sh in (('1', '20260916_TransPac_leg1'), ('2', '20260916_leg2')):
        st = []
        for r in wb[sh].iter_rows(min_row=2, values_only=True):
            if not isinstance(r[0], (int, float)):
                continue
            ops = {c: float(r[10 + i]) for i, c in enumerate(CODES) if r[10 + i]}
            st.append(dict(site=r[2], name=str(r[3]), lat=float(r[6]), lon=float(r[5]), sheet_eez=r[7],
                           sheet_depth=r[8], prio=r[9], ops=ops, kind='port' if r[4] == 'Port call' else 'station'))
        legs[leg] = st
    return legs

# ---------- geodesy ----------
R = 3440.065
def dist(a, b):
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    return 2 * R * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))
def interp(a, b, f):
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    d = dist(a, b) / R
    if d == 0:
        return a
    A = math.sin((1 - f) * d) / math.sin(d); B = math.sin(f * d) / math.sin(d)
    x = A * math.cos(la1) * math.cos(lo1) + B * math.cos(la2) * math.cos(lo2)
    y = A * math.cos(la1) * math.sin(lo1) + B * math.cos(la2) * math.sin(lo2)
    z = A * math.sin(la1) + B * math.sin(la2)
    return (math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x)))

def fmt(t): return t.strftime('%d %b %H:%M')

# ---------- scheduler ----------
OVERRIDE = {'Faaroa': ('France (French Polynesia), internal waters', 50)}
PERMITTED = ('Papua New Guinea', 'Federated States of Micronesia', 'Kiribati', 'Tuvalu', 'USA', 'NZ (Cook', 'France')

def place(s):
    z, d = eez(s['lat'], s['lon']), depth(s['lat'], s['lon'])
    if s['site'] in OVERRIDE:
        z, d = OVERRIDE[s['site']]
    return z, d

def margin_ok(pos, z, nm=10):
    """True if every point 10 nm around pos is in the same zone z (keeps stations off EEZ boundaries)."""
    for a in range(0, 360, 30):
        dl = nm / 60 * math.cos(math.radians(a)); dL = nm / 60 * math.sin(math.radians(a)) / max(0.2, math.cos(math.radians(pos[0])))
        if eez(pos[0] + dl, pos[1] + dL) != z:
            return False
    return True

def schedule(leg, plan, hydro=None):
    """hydro: None, or dict(period=h, window=h) for scenario B (water-column ops on a fixed cadence)."""
    t = LEG[leg]['start']
    events, track, stations = [], [], []
    last_wc = t
    nhy = 0
    for k, s in enumerate(plan):
        if k > 0:
            p = plan[k - 1]
            a, b = (p['lat'], p['lon']), (s['lat'], s['lon'])
            d = dist(a, b); h = d / SPEED
            f0, frm = 0.0, p['site']
            while hydro:
                T = last_wc + dt.timedelta(hours=hydro['period'])
                arr = t + dt.timedelta(hours=h * (1 - f0))
                if arr < T:
                    break                      # cadence not yet due when we reach the next point
                if s['kind'] == 'station' and arr <= T + dt.timedelta(hours=hydro['window']):
                    break                      # next coring station arrives within the window and carries the water column
                if s['kind'] == 'port' and arr <= T + dt.timedelta(hours=24):
                    break                      # end of leg: no extra stop just before port
                # choose the stop time within T +/- window: high seas first, then already-permitted EEZ
                best = None
                for off in [0] + [x * sg for x in range(1, hydro.get('search', hydro['window']) + 1) for sg in (1, -1)]:
                    tt = T + dt.timedelta(hours=off)
                    dh = (tt - t).total_seconds() / 3600
                    if dh <= 0.5 or dh >= h * (1 - f0) - 0.5:
                        continue
                    f = f0 + dh / h
                    pos = interp(a, b, f); z = eez(*pos)
                    if (depth(*pos) or 0) < 500:
                        continue
                    if not margin_ok(pos, z):
                        continue
                    rank = 0 if z == 'High seas' else (1 if z.startswith(PERMITTED) else 2)
                    if best is None or rank < best[0]:
                        best = (rank, dh, f, pos, z)
                    if rank == 0:
                        break
                if best is None:
                    break
                _, dh, f, pos, z = best
                n = max(1, int(d * (f - f0) // 10))
                for j in range(1, n + 1):
                    q = interp(a, b, f0 + (f - f0) * j / n)
                    track.append((t + dt.timedelta(hours=dh * j / n), q[0], q[1], leg))
                nhy += 1; hn = f'HY{leg}_{nhy}'
                events.append(dict(leg=leg, type='Transit', frm=frm, to=hn, start=t, end=t + dt.timedelta(hours=dh), hours=dh, nm=d * (f - f0)))
                t += dt.timedelta(hours=dh)
                hy = dict(site=hn, name='Water-column station (hydrology/biology)', lat=round(pos[0], 3), lon=round(pos[1], 3),
                          ops=dict(HYDRO), kind='hydro', eez=z, depth=depth(*pos), arr=t,
                          dep=t + dt.timedelta(hours=sum(HYDRO.values())), flag='' if best[0] < 2 else 'new EEZ')
                stations.append(hy)
                events.append(dict(leg=leg, type='Operations', frm=hn, to=hn, site=hn, start=t, end=hy['dep'], hours=sum(HYDRO.values()), ops=hy['ops'], eez=z))
                track.append((t, pos[0], pos[1], leg)); t = hy['dep']; track.append((t, pos[0], pos[1], leg))
                last_wc = t; f0, frm = f, hn
            rem = h * (1 - f0)
            n = max(1, int(d * (1 - f0) // 10))
            for j in range(1, n + 1):
                q = interp(a, b, f0 + (1 - f0) * j / n)
                track.append((t + dt.timedelta(hours=rem * j / n), q[0], q[1], leg))
            events.append(dict(leg=leg, type='Transit', frm=frm, to=s['site'], start=t, end=t + dt.timedelta(hours=rem), hours=rem, nm=d * (1 - f0)))
            t += dt.timedelta(hours=rem)
        if s['kind'] == 'waypoint':
            continue
        s = dict(s); ops = dict(s['ops'])
        if hydro and s['kind'] == 'station':
            had = [c for c in WATER if c in ops]
            for c in WATER:
                ops.pop(c, None)
            if t >= last_wc + dt.timedelta(hours=hydro['period'] - 24):
                for c in WATER:
                    ops[c] = max(s['ops'].get(c, 0), HYDRO[c])
                s['coupled'] = True
                last_wc = t + dt.timedelta(hours=sum(ops.values()))
            elif had:
                s['moved'] = had
        hrs = sum(ops.values()); s['ops'] = ops
        z, dd = place(s)
        s.update(arr=t, dep=t + dt.timedelta(hours=hrs), eez=z, depth=dd)
        stations.append(s)
        track.append((t, s['lat'], s['lon'], leg))
        if hrs:
            events.append(dict(leg=leg, type='Operations', frm=s['site'], to=s['site'], site=s['site'], start=t, end=s['dep'], hours=hrs, ops=ops, eez=z))
        t = s['dep']
        track.append((t, s['lat'], s['lon'], leg))
    return events, track, stations, t

def eez_segments(track):
    segs = []
    for (tt, la, lo, leg) in track:
        z = eez(la, lo)
        if z.startswith('Kiribati (Line'):
            z = 'Kiribati (Line Group)'
        if segs and segs[-1]['eez'] == z and segs[-1]['leg'] == leg:
            segs[-1]['end'] = tt
        else:
            segs.append(dict(eez=z, start=tt, end=tt, leg=leg))
    # drop 1-point flickers on boundaries (< 1 h) by merging
    out = []
    for g in segs:
        if out and (g['end'] - g['start']).total_seconds() < 3600 and len(out) and g is not segs[-1]:
            continue
        if out and out[-1]['eez'] == g['eez'] and out[-1]['leg'] == g['leg']:
            out[-1]['end'] = g['end']
        else:
            out.append(dict(g))
    return out

# ---------- scenario builders ----------
V2 = load_v2()

def scen_A():
    return {leg: [dict(s) for s in st] for leg, st in V2.items()}

def scen_C():
    legs = scen_A()
    l1 = [s for s in legs['1'] if s['site'] not in ('OJP_1', 'OJP_2')]
    hs = dict(site='OJP_HS', name='Ontong Java, high-seas shallow site (replaces OJP_1 + OJP_2)', lat=-1.000, lon=157.891,
              sheet_eez='High seas (new)', sheet_depth='~1985 (GMRT)', prio=1, kind='station',
              ops={'CS': 6, 'C1': 2, 'C2': 3, 'MN': 2, 'NP': 1, 'NM': 1, 'CA': 12, 'MT': 3})
    i = [s['site'] for s in l1].index('OJP_3')
    l1.insert(i, hs)
    legs['1'] = l1
    return legs

_CP = {}
def crosses(a, b, country):
    if country not in _CP:
        _CP[country] = [p for (sn, n, p, h, bb) in POLYS if sn.startswith(country)]
    d = dist(a, b); n = max(2, int(d // 8))
    pts = np.array([interp(a, b, j / n) for j in range(0, n + 1)])
    xy = np.c_[to360(pts[:, 1]), pts[:, 0]]
    return any(p.contains_points(xy).any() for p in _CP[country])

def hits_land(a, b, ends=8.0):
    """True if the straight transit a->b passes over land/reef (depth < 30 m), ignoring `ends` nm at each end (ports, coastal sites)."""
    d = dist(a, b); n = max(2, int(d // 3))
    fr = [j / n for j in range(n + 1) if ends <= d * j / n <= d - ends]
    if not fr:
        return False
    pts = np.array([interp(a, b, f) for f in fr])
    pts[:, 1] = np.where(pts[:, 1] > 180, pts[:, 1] - 360, pts[:, 1])
    return bool((depths(pts) < 30).any())

def avoid_land(legs):
    for leg, st in legs.items():
        out = [st[0]]
        for s in st[1:]:
            for _ in range(3):
                a, b = (out[-1]['lat'], out[-1]['lon']), (s['lat'], s['lon'])
                if not hits_land(a, b):
                    break
                cands = []
                for la in np.arange(min(a[0], b[0]) - 4, max(a[0], b[0]) + 4, 0.2):
                    for lo in np.arange(min(a[1], b[1]) - 4, max(a[1], b[1]) + 4, 0.2):
                        w = (float(la), float(lo))
                        cands.append((dist(a, w) + dist(w, b) - dist(a, b), w))
                cands.sort()
                best = None
                for extra, w in cands:
                    if not hits_land(a, w) and not hits_land(w, b):
                        best = (extra, w); break
                if best is None:   # two-step detour: accept a waypoint that at least clears the first half
                    for extra, w in cands:
                        if not hits_land(a, w):
                            best = (extra, w); break
                if best is None:
                    break
                out.append(dict(site=f'WP{leg}_{len(out)}', name=f'waypoint (avoid land, +{best[0]:.0f} nm)',
                                lat=round(best[1][0], 2), lon=round(best[1][1], 2), ops={}, kind='waypoint'))
            out.append(s)
        legs[leg] = out
    return legs

def avoid(legs, country):
    """For each transit that crosses a country's EEZ, insert the single waypoint that removes the crossing
    with the smallest extra distance (grid search, 0.25 deg)."""
    for leg, st in legs.items():
        out = [st[0]]
        for s in st[1:]:
            a, b = (out[-1]['lat'], out[-1]['lon']), (s['lat'], s['lon'])
            if crosses(a, b, country):
                cands = []
                for la in np.arange(min(a[0], b[0]) - 6, max(a[0], b[0]) + 6, 0.25):
                    for lo in np.arange(min(a[1], b[1]) - 6, max(a[1], b[1]) + 6, 0.25):
                        w = (float(la), float(lo))
                        cands.append((dist(a, w) + dist(w, b) - dist(a, b), w))
                cands.sort()
                best = None
                for extra, w in cands:
                    if not crosses(a, w, country) and not crosses(w, b, country):
                        best = (extra, w); break
                if best:
                    out.append(dict(site=f'WP{leg}_{len(out)}', name=f'waypoint (avoid {country} EEZ, +{best[0]:.0f} nm)',
                                    lat=round(best[1][0], 2), lon=round(best[1][1], 2), ops={}, kind='waypoint'))
            out.append(s)
        legs[leg] = out
    return legs

SCEN = {
    'A': dict(title='Scenario A — Route v2 as planned (EEZ zones checked)', legs=avoid_land(scen_A()), hydro=None),
    'B': dict(title='Scenario B — Water-column stations every 2–3 days, partly decoupled from coring', legs=avoid_land(scen_A()), hydro=dict(period=60, window=12, search=18)),
    'C': dict(title='Scenario C — No access to Papua New Guinea waters', legs=avoid_land(scen_C()), hydro=None),
    'C_detour': dict(title='Scenario C (variant) — No PNG access, transit kept outside the PNG EEZ', legs=avoid_land(avoid(scen_C(), 'Papua')), hydro=None),
}

RES = {}
for key, sc in SCEN.items():
    allev, alltr, allst, legsum = [], [], [], {}
    for leg in ('1', '2'):
        ev, tr, st, tend = schedule(leg, sc['legs'][leg], sc['hydro'])
        dur = (tend - LEG[leg]['start']).total_seconds() / 86400
        ops_h = sum(e['hours'] for e in ev if e['type'] == 'Operations')
        tr_h = sum(e['hours'] for e in ev if e['type'] == 'Transit')
        legsum[leg] = dict(days=dur, limit=LEG[leg]['limit_days'], margin=LEG[leg]['limit_days'] - dur, ops_h=ops_h, transit_h=tr_h,
                           nm=sum(e.get('nm', 0) for e in ev), end=tend)
        allev += ev; alltr += tr; allst += st
    RES[key] = dict(events=allev, track=alltr, stations=allst, legs=legsum, segs=eez_segments(alltr))

# ---------- console summary ----------
for key, r in RES.items():
    print('=' * 10, SCEN[key]['title'])
    for leg, s in r['legs'].items():
        print(f"  leg {leg}: {s['days']:.2f} d (limit {s['limit']}) margin {s['margin']:+.2f} d | ops {s['ops_h']:.0f} h, transit {s['transit_h']:.0f} h, {s['nm']:.0f} nm, end {fmt(s['end'])}")
    for s in r['stations']:
        if s['kind'] in ('station', 'hydro'):
            extra = (' water column moved to HY' if s.get('moved') else '') + (' +water column' if s.get('coupled') else '') + (' [' + s['flag'] + ']' if s.get('flag') else '')
            print(f"    {s['site']:10s} {s['lat']:8.3f} {s['lon']:9.3f} {str(s['depth']):>5s} m  {s['eez']:32s} {fmt(s['arr'])}  {sum(s['ops'].values()):4.0f} h{extra}")
    print('  EEZ crossings:')
    for g in r['segs']:
        print(f"    leg {g['leg']} {g['eez']:32s} {fmt(g['start'])} -> {fmt(g['end'])}")

json.dump({k: dict(legs={l: {kk: (str(vv) if isinstance(vv, dt.datetime) else vv) for kk, vv in s.items()} for l, s in r['legs'].items()},
                   stations=[{kk: (str(vv) if isinstance(vv, dt.datetime) else vv) for kk, vv in s.items()} for s in r['stations']],
                   events=[{kk: (str(vv) if isinstance(vv, dt.datetime) else vv) for kk, vv in e.items()} for e in r['events']],
                   track=[(str(a), b, c, d) for a, b, c, d in r['track']],
                   segs=[{kk: str(vv) for kk, vv in g.items()} for g in r['segs']]) for k, r in RES.items()},
          open(os.path.join(OUT, 'results.json'), 'w'), indent=1)
