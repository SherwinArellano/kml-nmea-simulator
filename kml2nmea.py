#!/usr/bin/env python3
"""
kml2nmea.py - Concurrent My Maps → live NMEA or custom TRK streamer & file generator
=====================================================================
This script reads Google My Maps KML exports and spawns one asyncio task per track,
streaming live NMEA ($GPRMC, $GPGGA, $GPGLL) or custom $TRK messages over UDP and/or MQTT,
or generating timestamped output files. Configuration is embedded inline in each KML
LineString `<name>` element using tokens, for example:

    "Truck 1" velocity=30 interval=500 delay=2000 loop repeat mode=trk-auto source=truck

Key features
------------
* **Inline config**: define per-track parameters (`velocity`, `interval`, `delay`, `loop`, `repeat`, `mode`, `source`) directly in KML names.
* **Geodesic accuracy**: ellipsoidal distance and interpolation using `geographiclib`.
* **Concurrent streaming**: non-blocking `asyncio` tasks per track.
* **Modes**:
    - **NMEA (sea)**: emits selected NMEA sentences (`$GPRMC`, `$GPGGA`, `$GPGLL`), with optional batching.
    - **TRK (land)**: emits custom `$TRK` messages; `trk-auto` (per-update) and `trk-container` (per-minute).
* **Output**:
    - **Live streaming**: UDP (`--udp HOST:PORT`) and/or MQTT (`--mqtt BROKER:PORT`, `--topic TOPIC`).
    - **File generation**: single merged file (`--filegen single --outfile FILE`) or one file per track (`--filegen multi --outdir DIR`).

Usage
-----
```bash
python kml2nmea.py [KML_PATHS...] \
    [--udp [HOST:PORT]] \
    [--mqtt [BROKER:PORT]] \
    [--topic TOPIC] \
    [--nmea-types TYPES] [--nmea-batch-types] \
    [--filegen {single,multi}] [--outdir DIR] [--outfile FILE]
```

Quick start
------------
```bash
python kml2nmea.py --udp --mqtt --filegen single
socat -u UDP-RECV:10110 STDOUT         # view UDP stream
mosquitto_sub -h localhost -t kml2nmea # listen messages
```

Install deps:
```bash
pip install -r requirements.txt
```
"""
from __future__ import annotations

import os         # for finding *.kml files
import glob       # for checking if a path is a directory
import asyncio    # for concurrent track tasks
import socket     # for UDP streaming
import sys        # for command-line args and exit
import time       # for timestamp generation
import re         # for parsing inline config
import xml.etree.ElementTree as ET  # for KML parsing
import argparse   # for CLI with MQTT support
from dataclasses import dataclass
from typing import List, Literal, Tuple, Iterator


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
    interval_ms: int   = 1000  # update interval in milliseconds between messages
    delay_ms: int  = 0     # initial delay before streaming (ms)
    loop:    bool  = False # whether to return back to initial starting point
    repeat:  bool  = False # whether to restart after finishing
    mode:    str   = "nmea"  # 'nmea', 'trk-auto', or 'trk-container'
    source:  str   = ""     # new: vehicle type (truck, auto, ship, etc.)

@dataclass
class TrackInfo:
    name: str
    cfg: TrackCfg
    coords: list[tuple[float, float]]
    source: str

# regex splits quoted name and optional tokens
_RE = re.compile(r'^\s*(?:"([^"]+)"|(\S+))(.*)$')

def parse_name(text: str) -> Tuple[str, TrackCfg]:
    """Parse a KML <name> string into (name, TrackCfg), reading inline tokens."""
    m = _RE.match(text)
    if not m:
        raise ValueError(f"Invalid name/text: {text!r}")
    name = m.group(1) or m.group(2)
    cfg  = TrackCfg()
    seen_interval = False

    # iterate tokens like 'velocity=30', 'interval=500', 'mode=trk-container'
    for tok in m.group(3).split():
        if "=" in tok:
            k, v = tok.split("=",1)
            if k == "velocity":
                cfg.vel_kmh = float(v)
            elif k == "interval":
                cfg.interval_ms = int(v)
                seen_interval = True
            elif k == "delay":
                cfg.delay_ms = int(v)
            elif k == "mode":
                cfg.mode = v.lower()
            elif k == "source":
                cfg.source = v.lower()
        else:
            if tok == "loop":
                cfg.loop = True
            elif tok == "repeat":
                cfg.repeat = True

    # normalize mode names
    lm = cfg.mode.lower()
    if lm in ("sea", "nmea"):
        cfg.mode = "nmea"
    elif lm in ("land", "trk-auto"):
        cfg.mode = "trk-auto"
    elif lm in ("trk-container",):
        cfg.mode = "trk-container"
    else:
        # unknown: fall back to nmea
        cfg.mode = "nmea"

    # default interval for container if not overridden
    if cfg.mode == "trk-container" and not seen_interval:
        cfg.interval_ms = 60_000

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
UDP_CLIENT: socket.socket | None
UDP_TARGET: Tuple[str, int]
MQTT_CLIENT: mqtt.Client | None
MQTT_TOPIC: str

# default NMEA sentence types for sea/NMEA mode
NMEA_TYPES: List[str] = ["GPRMC", "GPGGA", "GPGLL"]
NMEA_BATCH: bool = False

# ───────────────────────── Message builders ─────────────────────────

def get_timestamp(mode: str) -> str:
    """Return the appropriate UTC timestamp string for land or sea."""
    if mode.startswith('trk'):
        return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return time.strftime("%H%M%S", time.gmtime())


def fmt_timestamp(epoch_s: int, mode: str) -> str:
    """Return the appropriate UTC timestamp string for land or sea offset by specified seconds."""
    tm = time.gmtime(epoch_s)
    if mode.startswith("trk"):
        return time.strftime("%Y%m%dT%H%M%SZ", tm)
    return time.strftime("%H%M%S", tm)


def build_trk_messages(
    name: str, source: str, ts: str, lat: float, lon: float, vel: float, azi: float
) -> List[str]:
    """
    Build the list of $TRK messages (always exactly one) for land mode.
    """
    payload = (
        f"TRK,{name},{source},{ts},"
        f"{lat:.6f},{lon:.6f},"
        f"{vel:.1f},{int(azi)}"
    )
    return [f"${payload}{checksum(payload)}\r\n"]


def build_nmea_messages(
    ts: str, lat: float, lon: float, vel_kmh: float
) -> List[str]:
    """
    Build a list of NMEA sentences based on the global NMEA_TYPES and NMEA_BATCH.
    """
    lat_dm, ns = deg2dm(lat, is_lat=True)
    lon_dm, ew = deg2dm(lon, is_lat=False)
    sog = vel_kmh * 0.539957

    msgs: List[str] = []
    for nmea in NMEA_TYPES:
        if nmea == "GPRMC":
            pay = (
                f"GPRMC,{ts}.00,A,{lat_dm},{ns},"
                f"{lon_dm},{ew},{sog:.2f},0.0,,,"
            )
        elif nmea == "GPGGA":
            fix_q, num_sat, hdop, alt = 1, 8, 1.0, 0.0
            pay = (
                f"GPGGA,{ts}.00,"
                f"{lat_dm},{ns},{lon_dm},{ew},"
                f"{fix_q},{num_sat},{hdop:.1f},{alt:.1f},M,0.0,M,,"
            )
        elif nmea == "GPGLL":
            pay = (
                f"GPGLL,{lat_dm},{ns},{lon_dm},{ew},"
                f"{ts}.00,A"
            )
        else:
            continue

        msgs.append(f"${pay}{checksum(pay)}\r\n")

    return msgs


def send_messages(
    name: str,
    messages: List[str],
    mode: str,
):
    """
    Send one or more messages via UDP and/or MQTT, respecting NMEA_BATCH
    (only applied in sea mode).
    """
    payloads: List[bytes] = []

    if not mode.startswith("trk") and NMEA_BATCH:
        # Combine into one payload
        payloads.append("".join(messages).encode())
    else:
        # Add each message individually
        payloads.extend(msg.encode() for msg in messages)

    for data in payloads:
        if UDP_CLIENT: UDP_CLIENT.sendto(data, UDP_TARGET)
        if MQTT_CLIENT: MQTT_CLIENT.publish(f"{MQTT_TOPIC}/{mode}/{name}", data)


async def run_track(
    name: str,
    cfg: TrackCfg,
    pts: list,
):
    """Stream one track: walk its path, build messages, and send via UDP or MQTT."""
    if len(pts) < 2:
        return

    # derive step distance per update
    v_mps  = cfg.vel_kmh / 3.6
    step_m = v_mps * cfg.interval_ms / 1000
    if step_m <= 0:
        return

    # wait initial delay if specified
    await asyncio.sleep(cfg.delay_ms / 1000)

    last_lat = last_lon = None

    while True:
        for lat, lon in walk_path(pts, step_m, cfg.loop):
            # timestamp and heading
            ts  = get_timestamp(cfg.mode)
            if last_lat is not None:
                azi = _GEO.Inverse(last_lat, last_lon, lat, lon)["azi1"] % 360
            else:
                azi = 0.0
            last_lat, last_lon = lat, lon

            # build messages
            if cfg.mode.startswith('trk'):
                source = cfg.source or "unknown"
                msgs = build_trk_messages(name, source, ts, lat, lon, cfg.vel_kmh, azi)
            else:
                msgs = build_nmea_messages(ts, lat, lon, cfg.vel_kmh)

            # send them
            send_messages(name, msgs, cfg.mode)

            # wait until next update
            await asyncio.sleep(cfg.interval_ms / 1000)

        if not cfg.repeat:
            break

# ────────────────────────── File Generation ─────────────────────────────

async def generate_files(tracks: List[TrackInfo], args: Args):
    """Generate files synchronously."""
    if not args.filegen_mode:
        return

    print("Generating files...")

    now = int(time.time())

    # --- SINGLE MODE ---
    if args.filegen_mode == "single":
        # ensure parent dir exists
        od = os.path.dirname(args.outfile) or "."
        os.makedirs(od, exist_ok=True)

        # collect all (ts_sec, msg) across tracks
        all_msgs: list[tuple[int,str]] = []
        for name, cfg, pts, src in tracks:
            start = now + cfg.delay_ms / 1000
            step_s = cfg.interval_ms / 1000
            step_m = cfg.vel_kmh / 3.6 * cfg.interval_ms / 1000

            for idx, (lat, lon) in enumerate(walk_path(pts, step_m, cfg.loop)):
                ts_sec = start + idx*step_s
                ts = fmt_timestamp(ts_sec, cfg.mode)
                if cfg.mode.startswith("trk"):
                    msgs = build_trk_messages(name, cfg.source or "unknown", ts, lat, lon, cfg.vel_kmh, 0.0)
                else:
                    msgs = build_nmea_messages(ts, lat, lon, cfg.vel_kmh)
                for m in msgs:
                    all_msgs.append((ts_sec, m))

        # sort and write once
        all_msgs.sort(key=lambda x: x[0])
        with open(args.outfile, "w", buffering=1) as fh:
            for _, line in all_msgs:
                fh.write(line)

    # --- MULTI MODE ---
    # ensure outdir exists
    else:
        os.makedirs(args.outdir, exist_ok=True)

        for name, cfg, pts, src_path in tracks:
            kmlbase = os.path.splitext(os.path.basename(src_path))[0]
            # make "snake-case" track name
            safe = re.sub(r'[^A-Za-z0-9]+', "-", name).strip("-").lower()
            ext = ".trk" if cfg.mode.startswith("trk") else ".nmea"
            path = os.path.join(args.outdir, f"{kmlbase}.{safe}{ext}")

            start = now + cfg.delay_ms / 1000
            step_s = cfg.interval_ms / 1000
            step_m = cfg.vel_kmh / 3.6 * cfg.interval_ms / 1000

            with open(path, "w", buffering=1) as fh:
                for idx, (lat, lon) in enumerate(walk_path(pts, step_m, cfg.loop)):
                    ts = fmt_timestamp(start + idx*step_s, cfg.mode)
                    if cfg.mode.startswith("trk"):
                        msgs = build_trk_messages(name, cfg.source or "unknown", ts, lat, lon, cfg.vel_kmh, 0.0)
                    else:
                        msgs = build_nmea_messages(ts, lat, lon, cfg.vel_kmh)
                    for m in msgs:
                        fh.write(m)

    print("Files generated successfully.")

# ───────────────────────────── Main ────────────────────────────────

class Args(argparse.Namespace):
    kml: list[str]
    udp_target: str
    mqtt_broker: str
    topic: str
    nmea_types: str
    nmea_batch_types: bool
    filegen_mode: Literal["single", "multi"]
    outdir: str
    outfile: str

def build_args() -> Args:
    parser = argparse.ArgumentParser(
        description="Stream KML tracks via UDP/MQTT or generate them as files.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "kml",
        nargs="*",
        default=["."],
        help="Path(s) to KML file or directory containing KMLs;\n"
             "If no files or directories provided, uses the current directory."
    )

    parser.add_argument(
        "--udp",
        dest="udp_target",
        nargs="?",
        const="localhost:10110",
        metavar="HOST:PORT",
        help="UDP target address;\n"
             "If address not provided, defaults to localhost:10110"
    )

    parser.add_argument(
        "--mqtt",
        dest="mqtt_broker",
        nargs="?",
        const="localhost:1883",
        metavar="BROKER:PORT",
        help="MQTT broker address;\n"
             "If address not provided, defaults to localhost:1883"
    )

    parser.add_argument(
        "--topic",
        default="kml2nmea",
        help="MQTT topic (default: kml2nmea)"
    )

    parser.add_argument(
        "--nmea-types",
        choices=["GPRMC","GPGGA","GPGLL"],
        default="GPRMC,GPGGA,GPGLL",
        help="Comma-separated NMEA sentences to emit in sea mode (e.g. GPRMC,GPGLL)",
    )

    parser.add_argument(
        "--nmea-batch-types",
        action="store_true",
        help="if set, emit all selected NMEA sentences in one UDP/MQTT packet per update",
    )

    parser.add_argument(
        "--filegen",
        dest="filegen_mode",
        choices=["single","multi"],
        help="single = write one merged file (default);\n"
             "multi = one file per track"
    )

    parser.add_argument(
        "--outdir",
        default=".",
        metavar="DIR",
        help="Directory for single-track files\n"
             "(ignored in 'single' filegen mode)"
    )

    parser.add_argument(
        "--outfile",
        default="output.trks",
        metavar="FILE",
        help="Path to merged output file for global mode\n"
             "(ignored in 'multi' filegen mode)"
    )

    return parser.parse_args(namespace=Args())


async def main():
    """Parse CLI, load tracks, set up UDP, MQTT, and launch streaming tasks."""
    args = build_args()

    if not args.udp_target and not args.mqtt_broker and not args.filegen_mode:
        sys.exit("No running mode set. Please provide either --udp, --mqtt, or --filegen option. Use -h for more info.")

    # parse NMEA types
    global NMEA_TYPES, NMEA_BATCH
    NMEA_TYPES = [t.strip().upper() for t in args.nmea_types.split(",") if t.strip()]
    NMEA_BATCH = args.nmea_batch_types

    # UDP setup
    global UDP_CLIENT, UDP_TARGET
    if args.udp_target:
        host, port = args.udp_target.split(':')
        port = int(port)
        UDP_CLIENT = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        UDP_TARGET = (host, port)
        print(f"UDP client is set on {args.udp_target}")
    else:
        UDP_CLIENT = None

    # MQTT setup
    global MQTT_CLIENT, MQTT_TOPIC
    if args.mqtt_broker:
        MQTT_TOPIC = args.topic

        broker_host, broker_port = args.mqtt_broker.split(':')
        MQTT_CLIENT = mqtt.Client(protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        MQTT_CLIENT.connect(broker_host, int(broker_port))
        print(f"MQTT client is set on {args.mqtt_broker} with topic: {MQTT_TOPIC}")
    else:
        MQTT_CLIENT = None

    # — expand all inputs (files or dirs) into a flat list of .kml files
    kml_paths: list[str] = []
    for path in args.kml:
        if os.path.isdir(path):
            kml_paths.extend(glob.glob(os.path.join(path, '*.kml')))
        elif path.lower().endswith('.kml'):
            kml_paths.append(path)

    if not kml_paths:
        sys.exit("No KML files found in specified paths.")

    # — load tracks from every KML file found, keeping source path
    tracks: List[TrackInfo] = []
    for src in kml_paths:
        for name, cfg, coords in load_tracks(src):
            tracks.append((name, cfg, coords, src))

    if not tracks:
        sys.exit("No tracks found in the provided KML files.")

    # launch one asyncio task per track and generate files if specified
    tasks = [asyncio.create_task(generate_files(tracks, args))]
    tasks.extend(asyncio.create_task(run_track(name, cfg, coords)) for name, cfg, coords, _ in tracks)
    for name, cfg, _, src in tracks:
        print(f"▶ {name} (from {src}): {cfg}")

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user, shutting down.")
        sys.exit(0)
