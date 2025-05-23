from geographiclib.geodesic import Geodesic
from typing import Tuple

_GEO: Geodesic = Geodesic.WGS84  # type: ignore[attr-defined]


def geod_dist(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Compute ellipsoidal WGS-84 distance between two (lat, lon) points in meters."""
    return _GEO.Inverse(p1[0], p1[1], p2[0], p2[1])["s12"]


def geod_interp(
    p1: Tuple[float, float], p2: Tuple[float, float], meters: float
) -> Tuple[float, float]:
    """Return point located *meters* along the geodesic from p1 toward p2."""
    # calculate initial azimuth
    az12 = _GEO.Inverse(p1[0], p1[1], p2[0], p2[1])["azi1"]
    d = _GEO.Direct(p1[0], p1[1], az12, meters)
    return d["lat2"], d["lon2"]


def deg2dm(val: float, *, is_lat: bool) -> Tuple[str, str]:
    """Convert decimal degrees to NMEA degrees+minutes string and hemisphere."""
    hemi = ("N", "S") if is_lat else ("E", "W")
    sign = 0 if val >= 0 else 1
    val = abs(val)
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
