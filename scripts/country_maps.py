"""Charts for the MSR consent applications (one set per coastal State), from a scenario in results.json.

Usage: python3 scripts/country_maps.py <repo_dir> <scenario_key> <out_dir>
For each foreign State: an overview chart of the whole route with that State's EEZ highlighted, and one
chart per EEZ area (e.g. Kiribati Gilbert / Line) zoomed on the stations and transits, with estimated dates.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import render as RD
from geo import POLYS, to360

REPO, SCEN, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
R = RD.R[SCEN]

COUNTRY_OF = {
    'Papua New Guinea': 'Papua New Guinea', 'Federated States of Micronesia': 'Federated States of Micronesia',
    'Kiribati (Gilbert Islands)': 'Kiribati', 'Kiribati (Line Group)': 'Kiribati', 'Kiribati (Phoenix Group)': 'Kiribati',
    'Tuvalu': 'Tuvalu', 'Solomon Islands': 'Solomon Islands', 'Nauru': 'Nauru', 'Samoa': 'Samoa',
    'USA (American Samoa)': 'United States of America', 'USA (Palmyra Atoll)': 'United States of America',
    'NZ (Cook Islands)': 'Cook Islands',
}
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
def dshort(s): return f"{int(s[8:10])} {MONTHS[int(s[5:7]) - 1]}"

def areas_of(country):
    return [k for k, v in COUNTRY_OF.items() if v == country]

def bbox_of(area):
    xs, ys = [], []
    for sname, full, path, holes, bb in POLYS:
        if sname == area:
            xs += [bb[0], bb[1]]; ys += [bb[2], bb[3]]
    return (min(xs), max(xs), min(ys), max(ys)) if xs else None

def highlight(ax, areas, color='#ff3b30'):
    for sname, full, path, holes, bb in POLYS:
        if sname in areas:
            v = path.vertices
            ax.fill(v[:, 0], v[:, 1], color=color, alpha=0.12, zorder=2)
            ax.plot(v[:, 0], v[:, 1], color=color, lw=2.0, zorder=3)

def station_labels(ax, areas, extent):
    x0, x1, y0, y1 = extent
    for s in R['stations']:
        if s['kind'] == 'port':
            continue
        x, y = float(to360(s['lon'])), s['lat']
        if x0 <= x <= x1 and y0 <= y <= y1 and s.get('eez') in areas:
            ops = ', '.join(k for k in s['ops'])
            ax.annotate(f"{s['site']}  {dshort(s['arr'])}\n{abs(s['lat']):.3f}°{'S' if s['lat'] < 0 else 'N'} {abs(s['lon']):.3f}°{'W' if s['lon'] < 0 else 'E'}\n{ops or 'reserve'}",
                        (x, y), xytext=(10, -12), textcoords='offset points', fontsize=6.5, color='black', zorder=8,
                        bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#999999', alpha=0.92))

def legend(ax, country):
    h = [Line2D([], [], color=RD.LEGC['1'], lw=2, label='Leg 1  Nouméa – Apia'),
         Line2D([], [], color=RD.LEGC['2'], lw=2, label='Leg 2  Apia – Papeete'),
         Line2D([], [], marker='^', ls='', mfc='#ffd166', mec='k', label='Coring station'),
         Line2D([], [], marker='o', ls='', mfc='#2ecc71', mec='k', label='Water-column station'),
         Line2D([], [], color='#ff3b30', lw=2, label=f'EEZ of {country} (this application)'),
         Line2D([], [], color='#f39c12', lw=1.5, label='Other EEZ with stations'),
         Line2D([], [], color='#d0d7de', lw=1.5, label='Other EEZ')]
    ax.legend(handles=h, loc='lower left', fontsize=6.5, framealpha=0.92)

def footer(ax):
    ax.text(0.0, -0.1, 'TransPac 2027 — R/V Pourquoi pas ? — scenario B (water-column stations every 2–3 days). '
            'EEZ: Marine Regions EEZ v12 · Bathymetry: GMRT · Dates estimated at 10 kn. Not for navigation.\n'
            'Operations: CS site survey (multibeam, sub-bottom, EK80) · C1/C2 CTD-rosette · MN MultiNet · NP phytoplankton net · NM Bongo net · CA Calypso core · MT multicorer',
            transform=ax.transAxes, fontsize=6, color='#555555')

def segments_text(country):
    out = []
    for g in R['segs']:
        if COUNTRY_OF.get(g['eez']) == country:
            out.append(f"Leg {g['leg']}: {g['eez']}  {dshort(g['start'])} – {dshort(g['end'])}")
    return '\n'.join(out)

def overview(country, path):
    areas = areas_of(country)
    fig, ax = plt.subplots(figsize=(14, 7.6), dpi=170)
    RD.basemap(ax, (150.5, 212, -24.5, 10.5), SCEN)
    highlight(ax, areas)
    RD.draw_route(ax, SCEN, fs=5.5)
    legend(ax, country)
    ax.text(0.99, 0.99, 'EEZ entry/exit (estimated)\n' + segments_text(country), transform=ax.transAxes, ha='right', va='top',
            fontsize=7, bbox=dict(boxstyle='round', fc='white', alpha=0.92), zorder=9)
    ax.set_title(f'TransPac 2027 — Route and stations — {country}', fontsize=11, fontweight='bold')
    footer(ax)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)

def zoom(country, area, path):
    from geo import eez as _eez
    pts = [(float(to360(lo)), la) for (t, la, lo, l) in R['track'] if _eez(la, lo) == area]
    pts += [(float(to360(s['lon'])), s['lat']) for s in R['stations'] if s.get('eez') == area]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = 2.0
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    if x1 - x0 < 7: c = (x0 + x1) / 2; x0, x1 = c - 3.5, c + 3.5
    if y1 - y0 < 6: c = (y0 + y1) / 2; y0, y1 = c - 3, c + 3
    w, h = x1 - x0, y1 - y0
    if w < h * 1.15:
        c = (x0 + x1) / 2; x0, x1 = c - h * 0.6, c + h * 0.6
    elif h < w / 1.6:
        c = (y0 + y1) / 2; y0, y1 = c - w / 3.2, c + w / 3.2
    fig, ax = plt.subplots(figsize=(10, 8.5), dpi=170)
    RD.basemap(ax, (x0, x1, max(y0, -24.5), min(y1, 10.5)), SCEN)
    highlight(ax, [area])
    RD.draw_route(ax, SCEN, labels=False)
    station_labels(ax, [area], (x0, x1, y0, y1))
    legend(ax, country)
    # scale bar (nautical miles) in the lower-right corner
    yb = y0 + (y1 - y0) * 0.05; nmbar = 100 if (x1 - x0) < 14 else 200
    dlon = nmbar / 60 / max(0.2, np.cos(np.radians(yb)))
    xb = x1 - (x1 - x0) * 0.05 - dlon
    ax.plot([xb, xb + dlon], [yb, yb], color='white', lw=3, zorder=9, solid_capstyle='butt')
    ax.plot([xb, xb + dlon], [yb, yb], color='black', lw=1.2, zorder=10, solid_capstyle='butt')
    ax.text(xb + dlon / 2, yb + (y1 - y0) * 0.012, f'{nmbar} nm', ha='center', va='bottom', fontsize=7.5, zorder=10,
            bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
    segs = [g for g in R['segs'] if g['eez'] == area]
    txt = '\n'.join(f"Leg {g['leg']}: entry {dshort(g['start'])}, exit {dshort(g['end'])}" for g in segs) or 'no transit'
    nst = sum(1 for s in R['stations'] if s.get('eez') == area and s['kind'] != 'port' and s['ops'])
    ax.text(0.99, 0.99, f"{area}\n{nst} station(s) · {txt}", transform=ax.transAxes, ha='right', va='top', fontsize=7.5,
            bbox=dict(boxstyle='round', fc='white', alpha=0.92), zorder=9)
    ax.set_title(f'TransPac 2027 — {area}: stations and transit', fontsize=11, fontweight='bold')
    footer(ax)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)

if __name__ == '__main__':
    made = {}
    for country in sorted(set(COUNTRY_OF.values())):
        areas = [a for a in areas_of(country) if any(g['eez'] == a for g in R['segs']) or any(s.get('eez') == a for s in R['stations'])]
        if not areas:
            continue
        slug = country.replace(' ', '_')
        files = [os.path.join(OUT, f'{slug}_1_overview.png')]
        overview(country, files[0])
        for i, a in enumerate(areas, 2):
            f = os.path.join(OUT, f"{slug}_{i}_{a.replace(' ', '_').replace('(', '').replace(')', '')}.png")
            zoom(country, a, f); files.append(f)
        made[country] = files
        print(country, [os.path.basename(f) for f in files])
    json.dump(made, open(os.path.join(OUT, 'charts.json'), 'w'), indent=1)
