from core.models import TrackCfg, TrackInfo
from core.config import AppConfig
from core.walker import total_path_distance
from core.utils import get_cod_prov, get_cod_comune
from lxml import etree as ET
import re

_NS = {"k": "http://www.opengis.net/kml/2.2"}
_RE = re.compile(r'^\s*(?:"([^"]+)"|(\S+))(.*)$')

DEFAULT_DESTINATION_PORT = "A01"

parser = ET.XMLParser(remove_blank_text=True)


def parse_cfg_in_name_tags(text: str) -> tuple[str, TrackCfg]:
    """Parse a KML <name> string into (name, TrackCfg), reading inline tokens."""
    m = _RE.match(text)
    if not m:
        raise ValueError(f"Invalid name/text: {text!r}")

    default_cfg = AppConfig.get().default_track_cfg
    cfg = TrackCfg(
        vel_kmh=default_cfg.velocity,
        interval_ms=default_cfg.interval,
        delay_ms=default_cfg.delay,
        loop=default_cfg.loop_mode,
        repeat=default_cfg.repeat_mode,
        mode=default_cfg.mode,
        source=default_cfg.source,
        dest_port=DEFAULT_DESTINATION_PORT,
        prov="",
        comune="",
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
            elif k == "dest-port":
                cfg.dest_port = v.upper()
            elif k == "prov":
                cfg.prov = v
            elif k == "comune":
                cfg.comune = v
        else:
            if tok == "loop":
                cfg.loop = True
            elif tok == "repeat":
                cfg.repeat = True

    # normalize mode names
    lm = cfg.mode.lower()
    if lm in ("sea", "nmea"):
        cfg.mode = "nmea"
    elif lm in ("land", "trk-truck"):
        cfg.mode = "trk-truck"
    elif lm in ("trk-container",):
        cfg.mode = "trk-container"

    # default interval for container if not overridden
    if cfg.mode == "trk-container" and not seen_interval:
        cfg.interval_ms = 60_000

    return name, cfg


def parse_main_placemark(
    pm: ET._Element,
) -> tuple[str, str, TrackCfg, list[tuple[float, float]]] | None:
    """
    Parse main placemark of a folder element, returning a tuple of (raw_name,vehicle_name,cfg,coords).
    """
    name_el = pm.find("k:name", _NS)
    line_el = pm.find("k:LineString", _NS)
    if name_el is None or line_el is None:
        return

    # parse coordinate tuples (lon,lat) -> (lat,lon)
    coord_el = line_el.find("k:coordinates", _NS)
    if coord_el is None:
        return

    coords: list[tuple[float, float]] = []
    for c in (coord_el.text or "").split():
        parts = c.split(",")
        lon, lat = map(float, parts[:2])
        coords.append((lat, lon))

    raw_name = (name_el.text or "").strip()
    vehicle_name, cfg = parse_cfg_in_name_tags(raw_name)

    return (raw_name, vehicle_name, cfg, coords)


def parse_driving_placemarks(
    pms: list[ET._Element], tracks: list[TrackInfo], path: str
) -> None:
    results = parse_main_placemark(pms[0])
    if results is None:
        return

    raw_name, vehicle_name, cfg, coords = results

    # Parse starting and ending placemark
    start_el: ET._Element = pms[1].find("k:name", _NS)
    end_el: ET._Element = pms[-1].find("k:name", _NS)

    cfg.prov = get_cod_prov(start_el.text, cfg.prov) or ""
    cfg.comune = get_cod_comune(start_el.text, cfg.comune) or ""

    ti = TrackInfo(
        name=vehicle_name,
        cfg=cfg,
        coords=coords,
        path=path,
        total_dist=total_path_distance(coords, cfg.loop),
        raw_name=raw_name,
        start_placemark=start_el.text,
        end_placemark=end_el.text,
    )

    tracks.append(ti)


def parse_lines_placemarks(
    pms: list[ET._Element], tracks: list[TrackInfo], path: str
) -> None:
    for pm in pms:
        results = parse_main_placemark(pm)
        if results is None:
            continue

        raw_name, vehicle_name, cfg, coords = results
        ti = TrackInfo(
            name=vehicle_name,
            cfg=cfg,
            coords=coords,
            path=path,
            total_dist=total_path_distance(coords, cfg.loop),
            raw_name=raw_name,
            start_placemark=None,
            end_placemark=None,
        )

        tracks.append(ti)


def parse_tracks(path: str) -> list[TrackInfo]:
    tracks: list[TrackInfo] = []

    for folder in ET.parse(path, parser).iterfind(".//k:Folder", _NS):
        folder: ET._Element
        # 1. Find all <Placemark> in a <Folder>
        # 2. Check if <Folder> is a driving route or routes of lines
        #    by checking if the second Placemark has <Point>
        # 3. If driving route then parse Placemark and starting/ending Placemarks
        #    (There could be Placemarks in between so take the last Placemark for ending)
        # 4. If routes of lines, parse each Placemark
        pms: list[ET._Element] = folder.findall("k:Placemark", _NS)

        if len(pms) == 0:
            continue

        is_driving_route = len(pms) >= 2 and pms[1].find("k:Point", _NS) is not None
        if is_driving_route:
            parse_driving_placemarks(pms, tracks, path)
        else:
            parse_lines_placemarks(pms, tracks, path)

    return tracks
