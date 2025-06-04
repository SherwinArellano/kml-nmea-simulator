from dataclasses import dataclass
from typing import Literal

TrackMode = Literal["trk-nmea", "trk-truck", "trk-container"]


@dataclass
class TrackCfg:
    vel_kmh: float
    interval_ms: int
    delay_ms: int
    loop: bool
    repeat: bool
    mode: TrackMode | str
    source: str  # boat, ship, truck, etc.
    dest_port: str
    prov: str
    comune: str


@dataclass
class TrackInfo:
    name: str
    cfg: TrackCfg
    coords: list[tuple[float, float]]
    total_dist: float
    path: str
    raw_name: str
    start_placemark: str | None
    end_placemark: str | None
