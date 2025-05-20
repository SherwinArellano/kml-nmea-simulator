#!/usr/bin/env python3
"""kml2nmea.py - Concurrent My Maps → live NMEA or TRK streamer
================================================================
This script reads a **Google My Maps KML export** where each LineString (or route)
encodes configuration tokens in its `<name>` element, e.g.: 

    "Truck 1" velocity=30 freq=500 loop delay=2000 repeat mode=land

It then spawns **one `asyncio` task per track**, walks the geometry at the
requested speed, and broadcasts either `$GPRMC` sentences (default) or custom
`$TRK` messages over UDP in real time, depending on `mode` or via MQTT.

A new `--emit` option lets you choose `udp`, `mqtt`, or `both` as output.
For MQTT, use `--mqtt BROKER:PORT` (default `localhost:1883`) and optional
`--topic TOPIC` (default `kml2nmea`).

Key features
------------
* **Inline config**: no external JSON/YAML; all in the KML name (incl. `mode`).
* **Per-track control**: `velocity`, `freq` (ms), `delay` (ms), `loop`, `repeat`, `mode`.
* **Geodesic accuracy**: uses `geographiclib` for ellipsoidal distance.
* **Non-blocking**: each track runs concurrently via `asyncio` tasks.

Modes
-----
* `mode=sea` (default): emits NMEA `$GPRMC` sentences.
* `mode=land`: emits `$TRK` messages:

    $TRK,<ID_Camion>,<Timestamp>,<Latitude>,<Longitude>,<Velocity>,<Direction>*<Checksum>

Quick start
-----------
```bash
python kml2nmea.py mymap.kml 127.0.0.1:10110 --emit both --mqtt broker.local:1883 --topic my/topic
socat -u UDP-RECV:10110 STDOUT           # view UDP stream
mosquitto_sub -h localhost -t my/topic # listen messages
```  
Install deps:
```bash
pip install -r requirements.txt paho-mqtt
```
"""
from __future__ import annotations

import asyncio  # for concurrent track tasks
import socket     # for UDP streaming
import sys        # for command-line args and exit
import time       # for timestamp generation
import re         # for parsing inline config
import xml.etree.ElementTree as ET  # for KML parsing
import argparse   # for CLI with MQTT support
from dataclasses import dataclass
from typing import List, Tuple, Iterator

from geographiclib.geodesic import Geodesic  # ellipsoidal geodesics
import paho.mqtt.client as mqtt  # for MQTT streaming

# WGS84 ellipsoid
_GEO = Geodesic.WGS84
# KML namespace for parsing
_NS  = {"k": "http://www.opengis.net/kml/2.2"}

# ───────────────────────── Geometry helpers ─────────────────────────

def geod_dist(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Compute ellipsoidal WGS-84 distance between two (lat, lon) points in meters."""
    return _GEO.Inverse(p1[0], p1[1], p2[0], p2[1])["s12"]


def geod_interp(p1: Tuple[float, float], p2: Tuple[float, float], meters: float) -> Tuple[float, float]:
    """Return point located *meters* along the geodesic from p1 toward p2."""
    # calculate initial azimuth
    az12 = _GEO.Inverse(p1[0], p1[1], p2[0], p2[1])["azi1"]
    d    = _GEO.Direct(p1[0], p1[1], az12, meters)
    return d["lat2"], d["lon2"]


def deg2dm(val: float, *, is_lat: bool) -> Tuple[str, str]:
    """Convert decimal degrees to NMEA degrees+minutes string and hemisphere."""
    hemi = ("N", "S") if is_lat else ("E", "W")
    sign = 0 if val >= 0 else 1
    val  = abs(val)
    # split into degrees and fractional minutes
    deg, min_ = divmod(val * 60, 60)
    width = 2 if is_lat else 3
    return f"{int(deg):0{width}d}{min_:07.4f}", hemi[sign]


def checksum(payload: str) -> str:
    """Compute XOR-based checksum for NMEA-style payload (without leading '$')."""
    acc = 0
    for ch in payload:
        acc ^= ord(ch)
    return f"*{acc:02X}"

# ───────────────────────── Config parsing ───────────────────────────

@dataclass
class TrackCfg:
    """Configuration parameters for a single track."""
    vel_kmh: float = 5.0   # speed in km/h
    freq_ms: int   = 1000  # update frequency in milliseconds
    delay_ms: int  = 0     # initial delay before streaming (ms)
    loop:    bool  = False # whether to return back to initial starting point
    repeat:  bool  = False # whether to restart after finishing
    mode:    str   = "sea"  # 'sea' for NMEA, 'land' for TRK

# regex splits quoted name and optional tokens
_RE = re.compile(r'^\s*(?:"([^"]+)"|(\S+))(.*)$')

def parse_name(text: str) -> Tuple[str, TrackCfg]:
    """Parse a KML <name> string into (name, TrackCfg), reading inline tokens."""
    m = _RE.match(text)
    if not m:
        raise ValueError(f"Invalid name/text: {text!r}")
    name = m.group(1) or m.group(2)
    cfg  = TrackCfg()
    # iterate tokens like 'velocity=30', 'loop', 'mode=land'
    for tok in m.group(3).split():
        if "=" in tok:
            k, v = tok.split("=",1)
            if k == "velocity": cfg.vel_kmh = float(v)
            elif k == "freq":    cfg.freq_ms = int(v)
            elif k == "delay":   cfg.delay_ms = int(v)
            elif k == "mode":    cfg.mode   = v.lower()
        else:
            if tok == "loop":    cfg.loop   = True
            elif tok == "repeat": cfg.repeat = True
    return name, cfg

# ───────────────────────── KML loader ──────────────────────────────

def load_tracks(path: str):
    """Load all routes from a KML file, returning list of (name,cfg,coords)."""
    tracks = []
    # find each Placemark with a LineString
    for pm in ET.parse(path).iterfind('.//k:Placemark', _NS):
        name_el = pm.find('k:name', _NS)
        line_el = pm.find('k:LineString', _NS)
        if name_el is None or line_el is None:
            continue
        # parse coordinate tuples (lon,lat) -> (lat,lon)
        coords = [
            (float(lat), float(lon))
            for lon, lat, *_ in (
                c.split(',') for c in line_el.find('k:coordinates', _NS).text.split()
            )
        ]
        tracks.append((*parse_name(name_el.text.strip()), coords))
    return tracks

# ───────────────────── New global‑spacing iterator ──────────────────

def walk_path(points: List[Tuple[float,float]], step_m: float, loop: bool) -> Iterator[Tuple[float,float]]:
    """Yield points every `step_m` metres along the polyline; include endpoints."""
    if loop:
        # reverse for ping-pong behavior
        points = points + points[-2::-1]

    carry = 0.0               # leftover from previous segment
    cur   = points[0]
    yield cur                 # always yield first point

    for nxt in points[1:]:
        seg_len = geod_dist(cur, nxt)
        if seg_len == 0:
            continue
        # initial offset on this segment
        dist_from_cur = step_m - carry
        while dist_from_cur < seg_len:
            fix = geod_interp(cur, nxt, dist_from_cur)
            yield fix
            dist_from_cur += step_m
        # compute new carry into next segment
        carry = seg_len - (dist_from_cur - step_m)
        cur = nxt

    yield points[-1]  # ensure final endpoint is emitted

# ────────────────────── Async track coroutine ──────────────────────

# global emission settings
EMIT_MODE: str
MQTT_CLIENT: mqtt.Client | None
MQTT_TOPIC: str

async def run_track(name: str, cfg: TrackCfg, pts: list, sock: socket.socket, target):
    """Stream one track: walk its path, build messages, and send via UDP or MQTT."""
    if len(pts) < 2:
        return
    # derive step distance per update
    v_mps  = cfg.vel_kmh / 3.6
    step_m = v_mps * cfg.freq_ms / 1000
    if step_m <= 0:
        return
    # wait initial delay if specified
    await asyncio.sleep(cfg.delay_ms / 1000)

    while True:
        last_lat = last_lon = None
        for lat, lon in walk_path(pts, step_m, cfg.loop):
            # generate timestamps: full UTC for land, hhmmss for sea
            if cfg.mode == 'land':
                ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            else:
                ts = time.strftime("%H%M%S", time.gmtime())

            # compute heading from previous point
            if last_lat is not None:
                azi = _GEO.Inverse(last_lat, last_lon, lat, lon)["azi1"] % 360
            else:
                azi = 0.0
            last_lat, last_lon = lat, lon

            if cfg.mode == 'land':
                # construct TRK payload: name as truck ID, decimal coords, km/h speed, int heading
                payload = (
                    f"TRK,{name},{ts},"
                    f"{lat:.6f},{lon:.6f},"
                    f"{cfg.vel_kmh:.1f},{int(azi)}"
                )
                msg = f"${payload}{checksum(payload)}\r\n"
            else:
                # NMEA GPRMC construction: convert to deg-min format, knots speed
                lat_dm, ns = deg2dm(lat, is_lat=True)
                lon_dm, ew = deg2dm(lon, is_lat=False)
                sog = cfg.vel_kmh * 0.539957
                pay = (
                    f"GPRMC,{ts}.00,A,{lat_dm},{ns},"
                    f"{lon_dm},{ew},{sog:.2f},0.0,,,")
                msg = f"${pay}{checksum(pay)}\r\n"

            # send via selected protocol(s)
            if EMIT_MODE in ("udp", "both"):
                sock.sendto(msg.encode(), target)
            if EMIT_MODE in ("mqtt", "both") and MQTT_CLIENT is not None:
                MQTT_CLIENT.publish(MQTT_TOPIC, msg)

            # wait until next update
            await asyncio.sleep(cfg.freq_ms / 1000)

        if not cfg.repeat:
            break

# ───────────────────────────── Main ────────────────────────────────

async def main():
    """Parse CLI, load tracks, set up UDP, MQTT, and launch streaming tasks."""
    parser = argparse.ArgumentParser(description="Stream KML tracks via UDP, MQTT, or both.")
    parser.add_argument("kml", help="Path to KML file")
    parser.add_argument("udp_target", help="UDP target as host:port")
    parser.add_argument("--emit", choices=["udp","mqtt","both"], default="udp",
                        help="Emission mode: udp, mqtt, or both")
    parser.add_argument("--mqtt", dest="mqtt_broker", metavar="BROKER:PORT",
                        default="localhost:1883", help="MQTT broker address")
    parser.add_argument("--topic", default="kml2nmea", help="MQTT topic")
    args = parser.parse_args()

    # UDP setup
    host, port = args.udp_target.split(':')
    port = int(port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target = (host, port)

    # MQTT setup
    global EMIT_MODE, MQTT_CLIENT, MQTT_TOPIC
    EMIT_MODE = args.emit
    MQTT_TOPIC = args.topic
    if EMIT_MODE in ("mqtt", "both"):
        broker_host, broker_port = args.mqtt_broker.split(':')
        MQTT_CLIENT = mqtt.Client(protocol=mqtt.MQTTv311)
        MQTT_CLIENT.connect(broker_host, int(broker_port))
    else:
        MQTT_CLIENT = None

    tracks = load_tracks(args.kml)
    if not tracks:
        sys.exit("No tracks found.")

    # launch one asyncio task per track
    tasks = [asyncio.create_task(run_track(n, c, p, sock, target)) for n, c, p in tracks]
    for n, c, _ in tracks:
        print(f"▶ {n}: {c}")
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
