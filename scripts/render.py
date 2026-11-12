"""Render maps, CSV tables and GeoJSON for the TransPac 2027 route scenarios (reads results.json)."""
import sys, os, json, csv, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from geo import POLYS, asc, to360

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
R = json.load(open(os.path.join(OUT, 'results.json')))
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data') + '/'
CODES = ['CS', 'C1', 'C2', 'MN', 'NP', 'NM', 'CA', 'MT']
TITLES = {
    'A': 'Scenario A — Route v2 as planned (EEZ zones checked)',
    'B': 'Scenario B — Water-column stations every 2–3 days, partly decoupled from coring',
    'C': 'Scenario C — No access to Papua New Guinea waters (direct transit, acquisition off in PNG EEZ)',
    'C_detour': 'Scenario C variant — No PNG access, transit kept outside the PNG EEZ',
}
FOLDER = {'A': 'scenario_A_route_v2', 'B': 'scenario_B_hydro_cadence', 'C': 'scenario_C_no_PNG', 'C_detour': 'scenario_C_no_PNG_detour'}
LEGC = {'1': '#c0392b', '2': '#1f5fa8'}

# ---------- basemap ----------
BW = asc('west.asc'); BE = asc('east.asc'); BO = asc('ojp.asc')
lonw, latw, zw = BW; lone, late, ze = BE
lon_all = np.concatenate([lonw[lonw < 180], lone + 360]); z_all = np.concatenate([zw[:, lonw < 180], ze], axis=1)
deep = LinearSegmentedColormap.from_list('deep', ['#0b2545', '#1d4e89', '#5d8fc4', '#a9c8e8', '#e3eef8'])

def short_label(n):
    import re
    if n.startswith('NZ ('):
        n = n[4:].rstrip(')')
    n = n.replace('Federated States of Micronesia', 'FSM').replace('Papua New Guinea', 'PNG').replace('Solomon Islands', 'Solomon Is.')
    n = re.sub(r'^(Kiribati|USA|France) \((.*)\)$', r'\1\n(\2)', n)
    if n.startswith('Overlapping'):
        n = 'Matthew & Hunter\n(FR/VU claim)'
    return n

def basemap(ax, extent, scen):
    x0, x1, y0, y1 = extent
    if extent[0] >= 155 and extent[1] <= 162.5:
        lon, lat, z = BO
    else:
        lon, lat, z = lon_all, latw, z_all
    zz = np.where(z > 0, np.nan, -z)
    ax.imshow(zz, extent=[lon[0], lon[-1], lat[-1], lat[0]], cmap=deep.reversed(), vmin=0, vmax=6500, origin='upper', aspect='auto', zorder=0)
    land = np.where(z > 0, 1.0, np.nan)
    ax.imshow(land, extent=[lon[0], lon[-1], lat[-1], lat[0]], cmap=LinearSegmentedColormap.from_list('l', ['#c9b98f', '#c9b98f']), origin='upper', aspect='auto', zorder=1)
    st = R[scen]['stations']
    sampled = {s['eez'] for s in st if s['kind'] in ('station', 'hydro') and s.get('ops')}
    labelled = set()
    for sname, full, path, holes, bb in POLYS:
        v = path.vertices
        if bb[1] < x0 - 5 or bb[0] > x1 + 5:
            continue
        kind = 'sampled' if sname in sampled else 'other'
        if sname.startswith('France'):
            kind = 'france'
        col = {'sampled': '#f39c12', 'france': '#8e44ad', 'other': '#d0d7de'}[kind]
        ax.plot(v[:, 0], v[:, 1], color=col, lw=0.9 if kind != 'other' else 0.6, zorder=2, alpha=0.95)
        if sname not in labelled and (bb[1] - bb[0]) > 2:
            cx, cy = (bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2
            if x0 < cx < x1 and y0 < cy < y1:
                ax.text(cx, cy, short_label(sname), fontsize=6.5, color='white', ha='center', va='center', alpha=0.85, zorder=3,
                        fontweight='bold')
                labelled.add(sname)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    xt = ax.get_xticks()
    ax.set_xticks(xt); ax.set_xticklabels([f"{int(t)}°E" if t <= 180 else f"{int(360 - t)}°W" for t in xt], fontsize=7)
    yt = ax.get_yticks(); ax.set_yticks(yt); ax.set_yticklabels([f"{abs(int(t))}°{'S' if t < 0 else ('N' if t > 0 else '')}" for t in yt], fontsize=7)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    ax.axhline(0, color='white', lw=0.4, ls=':', zorder=2)

def draw_route(ax, scen, labels=True, fs=6):
    tr = R[scen]['track']
    for leg in ('1', '2'):
        pts = np.array([(float(to360(lo)), la) for (t, la, lo, l) in tr if l == leg])
        if len(pts):
            ax.plot(pts[:, 0], pts[:, 1], color=LEGC[leg], lw=1.4, zorder=4)
    for s in R[scen]['stations']:
        x, y = float(to360(s['lon'])), s['lat']
        if s['kind'] == 'port':
            ax.plot(x, y, 's', ms=6, mfc='white', mec='black', zorder=6)
            if labels:
                ax.text(x + 0.4, y - 0.6, s['name'], fontsize=fs + 1, fontweight='bold', zorder=7, color='black',
                        bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.8))
            continue
        if s['kind'] == 'hydro':
            ax.plot(x, y, 'o', ms=5, mfc='#2ecc71', mec='black', mew=0.5, zorder=6)
        else:
            coring = 'CA' in s['ops'] or 'MT' in s['ops']
            ax.plot(x, y, '^' if coring else 'D', ms=6 if coring else 5, mfc='#ffd166' if coring else '#2ecc71', mec='black', mew=0.6, zorder=6)
        if labels:
            ax.text(x + 0.25, y + 0.25, s['site'], fontsize=fs, zorder=7, color='white',
                    bbox=dict(boxstyle='round,pad=0.1', fc='black', ec='none', alpha=0.55))

def legend(ax, extra=()):
    h = [Line2D([], [], color=LEGC['1'], lw=2, label='Leg 1  Nouméa – Apia (13 Jul – 9 Aug 2027)'),
         Line2D([], [], color=LEGC['2'], lw=2, label='Leg 2  Apia – Papeete (31 Aug – 24 Sep 2027)'),
         Line2D([], [], marker='^', ls='', mfc='#ffd166', mec='k', label='Coring station (+ water column if planned)'),
         Line2D([], [], marker='D', ls='', mfc='#2ecc71', mec='k', label='Water-column station (route v2)'),
         Line2D([], [], marker='o', ls='', mfc='#2ecc71', mec='k', label='Added water-column station (scenario B)'),
         Line2D([], [], marker='s', ls='', mfc='white', mec='k', label='Port'),
         Line2D([], [], color='#f39c12', lw=1.5, label='EEZ with stations (consent needed)'),
         Line2D([], [], color='#8e44ad', lw=1.5, label='French EEZ'),
         Line2D([], [], color='#d0d7de', lw=1.5, label='Other EEZ (transit only or none)')] + list(extra)
    ax.legend(handles=h, loc='lower left', fontsize=6.5, framealpha=0.9)

def summary_box(ax, scen):
    L = R[scen]['legs']
    txt = '\n'.join(f"Leg {l}: {float(v['days']):.1f} d / {v['limit']} d  (margin {float(v['margin']):+.1f} d)" for l, v in L.items())
    ax.text(0.99, 0.99, txt, transform=ax.transAxes, ha='right', va='top', fontsize=7.5,
            bbox=dict(boxstyle='round', fc='white', alpha=0.9), zorder=9)

def overview(scen, path):
    fig, ax = plt.subplots(figsize=(15, 8.2), dpi=150)
    basemap(ax, (150.5, 212, -24.5, 10.5), scen)
    draw_route(ax, scen)
    legend(ax); summary_box(ax, scen)
    ax.set_title(TITLES[scen], fontsize=11, fontweight='bold')
    ax.text(0.01, -0.07, 'EEZ: Marine Regions (VLIZ) EEZ v12 · Bathymetry: GMRT · Transit at 10 kn, great-circle with land-avoidance waypoints · Planning document, not for navigation',
            transform=ax.transAxes, fontsize=6.5, color='#555555')
    fig.tight_layout(); fig.savefig(path); plt.close(fig)

def ojp(scen, path):
    fig, ax = plt.subplots(figsize=(8.5, 9), dpi=150)
    basemap(ax, (155.2, 162.2, -5.2, 4.4), scen)
    lon, lat, z = BO
    cs = ax.contour(lon, lat, -z, levels=[2000, 2500, 3000, 3500, 4000], colors='white', linewidths=0.4, alpha=0.6, zorder=2)
    ax.clabel(cs, fmt='%d m', fontsize=5.5)
    draw_route(ax, scen, fs=7)
    ax.set_title(TITLES[scen].split(' — ')[0] + ' — Ontong Java Plateau', fontsize=10, fontweight='bold')
    summary_box(ax, scen)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)

def T(s): return s[:16].replace('T', ' ') if s else ''

def main():
    for scen, folder in FOLDER.items():
        d = os.path.join(OUT, folder); os.makedirs(d, exist_ok=True)
        r = R[scen]
        with open(os.path.join(d, 'stations.csv'), 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['order', 'leg', 'site', 'name', 'type', 'lat', 'lon', 'depth_m_GMRT', 'jurisdiction_checked', 'jurisdiction_in_route_v2',
                        'arrival_UTC_est', 'departure_UTC_est', 'ops_hours'] + [f'{c}_h' for c in CODES] + ['note'])
            legof = {}
            for e in r['events']:
                if e.get('site'):
                    legof[e['site']] = e['leg']
            for i, s in enumerate(r['stations'], 1):
                note = 'water column moved to a separate station' if s.get('moved') else ('water column done at this station (cadence)' if s.get('coupled') else '')
                if s.get('flag'): note = (note + '; ' if note else '') + s['flag']
                w.writerow([i, legof.get(s['site'], ''), s['site'], s.get('name', ''), s['kind'], round(s['lat'], 4), round(s['lon'], 4), s.get('depth', ''),
                            s.get('eez', ''), s.get('sheet_eez', '') or '', T(s.get('arr')), T(s.get('dep')), sum(s['ops'].values())] +
                           [s['ops'].get(c, '') for c in CODES] + [note])
        with open(os.path.join(d, 'timeline.csv'), 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['leg', 'type', 'from', 'to', 'start_UTC_est', 'end_UTC_est', 'hours', 'distance_nm', 'operations', 'jurisdiction'])
            for e in r['events']:
                ops = e.get('ops') or {}
                w.writerow([e['leg'], e['type'], e['frm'], e['to'], T(e['start']), T(e['end']), round(float(e['hours']), 2),
                            round(float(e['nm']), 1) if e.get('nm') else '', ', '.join(f'{k} {v:g} h' for k, v in ops.items()), e.get('eez', '')])
        with open(os.path.join(d, 'eez_crossings.csv'), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['leg', 'zone', 'entry_UTC_est', 'exit_UTC_est'])
            for g in r['segs']:
                w.writerow([g['leg'], g['eez'], T(g['start']), T(g['end'])])
        feats = []
        for leg in ('1', '2'):
            coords = [[round(lo, 4), round(la, 4)] for (t, la, lo, l) in r['track'] if l == leg]
            feats.append(dict(type='Feature', properties=dict(leg=leg), geometry=dict(type='LineString', coordinates=coords)))
        for s in r['stations']:
            feats.append(dict(type='Feature', properties=dict(site=s['site'], type=s['kind'], jurisdiction=s.get('eez'), arrival=T(s.get('arr')),
                                                             ops_hours=sum(s['ops'].values())), geometry=dict(type='Point', coordinates=[s['lon'], s['lat']])))
        json.dump(dict(type='FeatureCollection', features=feats), open(os.path.join(d, 'route.geojson'), 'w'))
        overview(scen, os.path.join(d, 'map_overview.png'))
        ojp(scen, os.path.join(d, 'map_ontong_java.png'))
        print('rendered', folder)


if __name__ == '__main__':
    main()
