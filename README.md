# TransPac 2027 — route scenarios, legs 1–2 (Nouméa – Apia – Papeete)

R/V *Pourquoi pas ?* · Leg 1 Nouméa → Apia (13 Jul – 9 Aug 2027, 26 days available) · Leg 2 Apia → Papeete (31 Aug – 24 Sep 2027, 23 days available)

Planning study, 12 November 2026. The base plan is **route v2 (16 September 2026)** in [`input/`](input/20260916_TransPac_route_v2.xlsx). Every station and every transit is checked against the exclusive economic zones (EEZs).

| | Scenario | Folder |
|---|---|---|
| **A** | Route v2 as planned, with the zones re-checked | [`scenario_A_route_v2`](scenario_A_route_v2) |
| **B** | Water-column stations every 2–3 days, partly decoupled from coring (not the preferred option) | [`scenario_B_hydro_cadence`](scenario_B_hydro_cadence) |
| **C** | No access to Papua New Guinea waters | [`scenario_C_no_PNG`](scenario_C_no_PNG) |
| C′ | Variant of C: transit also kept outside the PNG EEZ | [`scenario_C_no_PNG_detour`](scenario_C_no_PNG_detour) |

Each folder holds the following files:

- `map_overview.png`: the whole route.
- `map_ontong_java.png`: a zoom on the Ontong Java Plateau.
- `stations.csv`: position, GMRT depth, checked jurisdiction, estimated arrival and departure, and hours per operation.
- `timeline.csv`: every transit and operation in order.
- `eez_crossings.csv`: estimated entry and exit times for each zone.
- `route.geojson`: the track and stations, which open in QGIS or geojson.io.

## Summary

| | Leg 1 (limit 26 d) | Leg 2 (limit 23 d) | Stations with sampling in foreign EEZs | Foreign EEZs crossed without stations |
|---|---|---|---|---|
| **A** | 26.3 d (**−0.3 d**) | 22.4 d (+0.6 d) | PNG (2), FSM (2), Kiribati (4), Tuvalu (1 + reserve), USA (2), Cook Is. (2) | Solomon Is., Nauru, Samoa |
| **B** | 26.8 d (**−0.8 d**) | 22.5 d (+0.5 d) | as A, plus 1 water-column station in PNG | Solomon Is., Nauru, Samoa |
| **C** | 25.9 d (+0.1 d) | 22.4 d (+0.6 d) | FSM (2), Kiribati (4), Tuvalu (1 + reserve), USA (2), Cook Is. (2) | Solomon Is., **PNG (transit only, acquisition off)**, Nauru, Samoa |
| C′ | 26.7 d (−0.7 d) | 22.4 d (+0.6 d) | as C | **Vanuatu**, Solomon Is., Nauru, Samoa |

French waters (New Caledonia, Wallis and Futuna, French Polynesia) are crossed in every scenario and need the French procedures, not a foreign consent.

The time balance assumes a transit speed of 10 knots and the operation hours from route v2. Day counts run from departure (13 Jul 08:00 and 31 Aug 08:00) to arrival in port. They include no weather or technical contingency.

## A — Route v2, zones checked

The route is unchanged, except for waypoints that keep the transits off land. The straight line from Loy1 to OJP_1 crossed Santa Isabel (Solomon Islands), and the Nouméa lagoon exit needed waypoints too.

**The EEZ column of the route v2 sheet is wrong for 10 of the 22 stations:**

| Station | Route v2 sheet says | Checked (Marine Regions EEZ v12) |
|---|---|---|
| OJP_1 | High seas | **Papua New Guinea** |
| OJP_5 | Papua New Guinea | **High seas** |
| OJP_6, OJP_7, OJP_9, OJP_8 | Federated States of Micronesia | **High seas** |
| ESAM | High seas (to confirm) | **USA (American Samoa)**. The site is about 120 nm from the Rose Atoll Marine National Monument. |
| MH_1, MH_2 | Kiribati (Line Islands) | **High seas** |
| CHAL, VOST | French Polynesia | **Kiribati (Line Islands)** |

All other stations match the sheet. NT_3, the reserve station, does fall inside the Tuvalu EEZ, so the "to confirm" in the sheet is resolved.

**Transit-only EEZs:**

| Zone | Approx. dates (leg 1) | Approx. duration |
|---|---|---|
| Solomon Islands | 15–18 Jul | about 3 days |
| Nauru | 29–30 Jul | about 1 day |
| Wallis and Futuna (France) | 7 Aug | about 1 day |
| Samoa | arrival and departure at Apia | |

Underway acquisition in these zones (EK80, multibeam, seismic, seawater line) needs consent, or must be switched off.

**Time:** leg 1 is 0.3 days (7 h) over. Dropping one priority-2 station recovers this, for example OJP_8 (8 h).

## B — Water-column cadence every 2–3 days

This scenario follows these rules:

- **Coring stations** keep the site survey, bottom CTD (C2), Calypso and multicorer.
- **Water-column biology** (CTD 1 with eDNA, MultiNet, phytoplankton net, Bongo net) runs on a fixed cadence of 60 h, with a ±12 h window.
- **When a coring station falls in the window**, the water column is done there (coupled). This happens at 10 coring stations: OJP_2, OJP_4, OJP_6, NT_1, NT_2, MH_3, MH_1, LI_2, LI_1 and VOST.
- **Otherwise**, a separate 9-h water-column station (C1 2 h + C2 3 h + MultiNet 2 h + nets 2 h) is added on the transit. Its position is chosen in this order: high seas, then an EEZ already requested, then elsewhere. It must also be deeper than 500 m.

| Added station | Position | Depth | Zone | Est. date |
|---|---|---|---|---|
| HY1_1 | 15.23°S 162.53°E | 4440 m | France (New Caledonia) | 15 Jul |
| HY1_2 | 5.46°S 157.46°E | 2149 m | Papua New Guinea | 18 Jul |
| HY1_3 | 0.20°S 163.46°E | 4457 m | High seas | 29 Jul |
| HY1_4 | 12.15°S 176.16°W | 2247 m | France (Wallis and Futuna) | 7 Aug |
| HY2_1 | 0.84°S 164.00°W | 5344 m | High seas | 9 Sep |
| HY2_2 | 6.26°S 151.79°W | 5065 m | High seas | 18 Sep |
| HY2_3 | 14.67°S 151.27°W | 4612 m | France (French Polynesia) | 21 Sep |

**Cost:** 11 coring stations lose their paired water-column sampling: Loy1, OJP_1, OJP_3, OJP_5, OJP_7, OJP_9, OJP_8, ESAM, MH_4, MH_2 and CHAL. This weakens the living-versus-sediment comparison (research question 3), which is why B is not the preferred option.

**Time:** leg 1 is 0.8 days (18.5 h) over. To make it fit, drop two or three priority-2 Ontong Java stations, for example OJP_3 (8 h), OJP_7 (8 h) and OJP_8 (6 h). Leg 2 fits, with 0.5 days to spare.

## C — No access to Papua New Guinea waters

- **OJP_1 and OJP_2 (PNG) are removed.** They are replaced by **OJP_HS** at 1.000°S, 157.891°E, **≈1985 m (GMRT)**, on the high seas.
  - This is the shallowest high-seas point on the plateau that stays at least 20 nm from every EEZ boundary. The seafloor is flat: less than 30 m of relief within about 6 km.
  - It takes the full OJP_1 programme: site survey, CTD 1 and 2, MultiNet, nets, Calypso and multicorer, 30 h in total.
  - A shallower alternative exists at 1.17°S, 157.60°E (≈1835 m), but it is only about 11 nm from the PNG EEZ boundary.
  - Either way, the shallow end of the Ontong Java depth transect starts at about 1850–1985 m instead of about 1600 m.
- **Transit through the PNG EEZ** (about 1 day) stays on the direct route. Under UNCLOS, navigation through the EEZ remains free, but all scientific acquisition (EK80, multibeam, seismic, seawater line) must be switched off there.
- **Variant C′** keeps the ship outside the PNG EEZ. It costs about 180 nm (0.8 days), puts leg 1 0.7 days over, and adds a transit through **Vanuatu**.
- **Time:** C is the only scenario where leg 1 fits, with 0.1 days to spare.

## Method and limits

- **EEZ limits:** Marine Regions EEZ v12 (VLIZ), queried by WFS. Points inside internal or archipelagic waters fall outside the EEZ polygons. Fa'aroa Bay (Raiatea) is therefore labelled by hand as French internal waters.
- **Bathymetry:** GMRT (low resolution for the overview maps, medium resolution on the Ontong Java Plateau). Depths are estimates. Small reefs are not resolved by the land check.
- **Route:** great-circle legs at 10 knots, with waypoints added only where a leg would cross land or, in C′, the PNG EEZ.
- **Dates:** estimates only. The French Oceanographic Fleet (DFO) will produce the official plan. This is a planning document and is not for navigation.

## Reproduce

```bash
scripts/fetch_data.sh                       # downloads EEZ polygons and GMRT grids into data/ (~60 MB, not versioned)
python3 scripts/scenarios.py .              # computes the scenarios -> results.json
python3 scripts/render.py .                 # writes maps, CSV and GeoJSON into the scenario folders
```

Requirements: Python 3 with numpy, matplotlib and openpyxl.
