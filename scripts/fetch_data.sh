#!/usr/bin/env bash
# Download the public geodata used by the scripts into ../data (not versioned: ~60 MB).
set -euo pipefail
D="$(cd "$(dirname "$0")/.." && pwd)/data"; mkdir -p "$D"; cd "$D"
WFS="https://geo.vliz.be/geoserver/MarineRegions/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=MarineRegions:eez&outputFormat=application/json"
curl -sS -o eez_w.json "$WFS&bbox=150,-26,180,12"
curl -sS -o eez_e.json "$WFS&bbox=-180,-26,-140,12"
GMRT="https://www.gmrt.org/services/GridServer?format=esriascii"
curl -sS -o west.asc "$GMRT&minlongitude=150&maxlongitude=180&minlatitude=-26&maxlatitude=12&resolution=low"
curl -sS -o east.asc "$GMRT&minlongitude=-180&maxlongitude=-140&minlatitude=-26&maxlatitude=12&resolution=low"
curl -sS -o ojp.asc "$GMRT&minlongitude=155&maxlongitude=162&minlatitude=-5&maxlatitude=4.5&resolution=med"
echo "data ready in $D"
