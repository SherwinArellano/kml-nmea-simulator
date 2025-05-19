#!/usr/bin/env python3
"""kml2nmea.py - Concurrent My Maps → live NMEA streamer
================================================================
This script reads a **Google My Maps KML export** where each LineString (or route)
encodes configuration tokens in its `<name>` element, e.g.:

    "Truck 1" velocity=30 freq=500 loop delay=2000 repeat

It then spawns **one `asyncio` task per track**, walks the geometry at the
requested speed, and broadcasts `$GPRMC` sentences over UDP in real time.

Key features
------------
* **Inline config**: no external JSON/YAML; everything is in the KML name.
* **Per-track control**: `velocity`, `freq` (ms), `delay` (ms), `loop`, `repeat`.
* **Geodesic accuracy**: uses `geographiclib` for ellipsoidal distance.
* **Non-blocking**: each track runs concurrently via `asyncio` tasks.

Quick start
-----------
```bash
python kml2nmea.py mymap.kml 127.0.0.1:10110
socat -u UDP-RECV:10110 STDOUT   # view the NMEA stream
```
Install deps:
```bash
autopep8 geographical
pip install geographiclib  # or sudo apt install python3-geographiclib
```
"""
from __future__ import annotations

import asyncio
import socket
import sys
import time
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Tuple, Iterator

from geographiclib.geodesic import Geodesic

_GEO = Geodesic.WGS84
_NS  = {"k": "http://www.opengis.net/kml/2.2"}

# ───────────────────────── Geometry helpers ─────────────────────────

def geod_dist(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Ellipsoidal WGS-84 distance in metres."""
    return _GEO.Inverse(p1[0], p1[1], p2[0], p2[1])["s12"]


def geod_interp(p1: Tuple[float, float], p2: Tuple[float, float], meters: float) -> Tuple[float, float]:
    """Return point *meters* along the geodesic from p1 toward p2."""
    az12 = _GEO.Inverse(p1[0], p1[1], p2[0], p2[1])["azi1"]
    d    = _GEO.Direct(p1[0], p1[1], az12, meters)
    return d["lat2"], d["lon2"]


def deg2dm(val: float, *, is_lat: bool) -> Tuple[str, str]:
    hemi = ("N", "S") if is_lat else ("E", "W")
    sign = 0 if val >= 0 else 1
    val  = abs(val)
    deg, min_ = divmod(val * 60, 60)
    width = 2 if is_lat else 3
    return f"{int(deg):0{width}d}{min_:07.4f}", hemi[sign]


def checksum(payload: str) -> str:
    acc = 0
    for ch in payload:
        acc ^= ord(ch)
    return f"*{acc:02X}"

# ───────────────────────── Config parsing ───────────────────────────

@dataclass
class TrackCfg:
    vel_kmh: float = 5.0
    freq_ms: int   = 1000
    delay_ms:int   = 0
    loop:    bool  = False
    repeat:  bool  = False

_RE = re.compile(r'^\s*(?:"([^"]+)"|(\S+))(.*)$')

def parse_name(text: str) -> Tuple[str, TrackCfg]:
    m = _RE.match(text)
    if not m:
        raise ValueError(text)
    name = m.group(1) or m.group(2)
    cfg  = TrackCfg()
    for tok in m.group(3).split():
        if "=" in tok:
            k, v = tok.split("=",1)
            if k=="velocity": cfg.vel_kmh=float(v)
            elif k=="freq":   cfg.freq_ms=int(v)
            elif k=="delay":  cfg.delay_ms=int(v)
        else:
            if tok=="loop":   cfg.loop=True
            elif tok=="repeat": cfg.repeat=True
    return name, cfg

# ───────────────────────── KML loader ──────────────────────────────

def load_tracks(path:str):
    tracks=[]
    for pm in ET.parse(path).iterfind('.//k:Placemark', _NS):
        name_el=pm.find('k:name',_NS); line_el=pm.find('k:LineString',_NS)
        if name_el is None or line_el is None: continue
        coords=[(float(lat),float(lon)) for lon,lat,*_ in (c.split(',') for c in line_el.find('k:coordinates',_NS).text.split())]
        tracks.append((*parse_name(name_el.text.strip()),coords))
    return tracks

# ───────────────────── New global‑spacing iterator ──────────────────

def walk_path(points: List[Tuple[float,float]], step_m: float, loop: bool) -> Iterator[Tuple[float,float]]:
    """Yield fixes every *step_m* metres along the entire polyline.

    Remainder distance (carry) rolls over segment boundaries so spacing is
    constant across the whole route.  Endpoint is always yielded.
    """
    if loop:
        points = points + points[-2::-1]

    carry = 0.0              # leftover distance from previous segment
    cur   = points[0]
    yield cur                # always start at the first point

    for nxt in points[1:]:
        seg_len = geod_dist(cur, nxt)
        if seg_len == 0:
            continue
        dist_from_cur = step_m - carry  # first emission offset on this seg
        while dist_from_cur < seg_len:
            fix = geod_interp(cur, nxt, dist_from_cur)
            yield fix
            dist_from_cur += step_m
        carry = seg_len - (dist_from_cur - step_m)  # leftover into next seg
        cur = nxt

    yield points[-1]  # ensure final endpoint emitted

# ────────────────────── Async track coroutine ──────────────────────

async def run_track(name:str,cfg:TrackCfg,pts:list,sock:socket.socket,target):
    if len(pts)<2: return
    v_mps = cfg.vel_kmh/3.6
    step_m= v_mps*cfg.freq_ms/1000
    if step_m<=0: return
    await asyncio.sleep(cfg.delay_ms/1000)

    while True:
        for lat,lon in walk_path(pts,step_m,cfg.loop):
            ts=time.strftime("%H%M%S",time.gmtime())
            lat_dm,ns=deg2dm(lat,is_lat=True)
            lon_dm,ew=deg2dm(lon,is_lat=False)
            sog=cfg.vel_kmh*0.539957
            pay=f"GPRMC,{ts}.00,A,{lat_dm},{ns},{lon_dm},{ew},{sog:.2f},0.0,,,"
            msg=f"${pay}{checksum(pay)}{name}\r\n"
            sock.sendto(msg.encode(),target)
            await asyncio.sleep(cfg.freq_ms/1000)
        if not cfg.repeat: break

# ───────────────────────────── Main ────────────────────────────────

async def main():
    if len(sys.argv)!=3:
        sys.exit("usage: python kml2nmea.py map.kml HOST:PORT")
    kml, hp=sys.argv[1:]
    host,port=hp.split(':'); port=int(port)
    tracks=load_tracks(kml)
    if not tracks: sys.exit("No tracks found.")
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); target=(host,port)
    tasks=[asyncio.create_task(run_track(n,c,p,sock,target)) for n,c,p in tracks]
    for n,c,_ in tracks: print(f"▶ {n}: {c}")
    await asyncio.gather(*tasks)

if __name__=='__main__':
    asyncio.run(main())
