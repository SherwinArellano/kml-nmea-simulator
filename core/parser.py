from core.models import TrackCfg
import re, xml.etree.ElementTree as ET
from core.config import AppConfig

_NS = {"k": "http://www.opengis.net/kml/2.2"}
_RE = re.compile(r'^\s*(?:"([^"]+)"|(\S+))(.*)$')


def parse_cfg_in_name_tags(text: str) -> tuple[str, TrackCfg]:
    """Parse a KML <name> string into (name, TrackCfg), reading inline tokens."""
    m = _RE.match(text)
    if not m:
        raise ValueError(f"Invalid name/text: {text!r}")

    default_cfg = AppConfig.get().default_track_cfg
    cfg = TrackCfg(
        default_cfg.velocity,
        default_cfg.interval,
        default_cfg.delay,
        default_cfg.loop_mode,
        default_cfg.repeat_mode,
        default_cfg.mode,
        default_cfg.source,
    )

    name = m.group(1) or m.group(2)
    seen_interval = False

    # iterate tokens like 'velocity=30', 'interval=500', 'mode=trk-container'
    for tok in m.group(3).split():
        if "=" in tok:
            k, v = tok.split("=", 1)
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

    # default interval for container if not overridden
    if cfg.mode == "trk-container" and not seen_interval:
        cfg.interval_ms = 60_000

    return name, cfg


def parse_tracks(path: str) -> list[tuple[str, TrackCfg, list[tuple[float, float]]]]:
    """Load all routes from a KML file, returning list of (name,cfg,coords)."""
    tracks: list[tuple[str, TrackCfg, list[tuple[float, float]]]] = []

    # find each Placemark with a LineString
    for pm in ET.parse(path).iterfind(".//k:Placemark", _NS):
        name_el = pm.find("k:name", _NS)
        line_el = pm.find("k:LineString", _NS)
        if name_el is None or line_el is None:
            continue

        # parse coordinate tuples (lon,lat) -> (lat,lon)
        coord_el = line_el.find("k:coordinates", _NS)
        if coord_el is None:
            continue

        coords: list[tuple[float, float]] = []
        for c in (coord_el.text or "").split():
            parts = c.split(",")
            lon, lat = map(float, parts[:2])
            coords.append((lat, lon))

        name, cfg = parse_cfg_in_name_tags((name_el.text or "").strip())
        tracks.append((name, cfg, coords))

    return tracks
