from dataclasses import dataclass
from typing import Literal

TrackMode = Literal["nmea", "trk-auto", "trk-container"]


@dataclass
class TrackCfg:
    vel_kmh: float = 5.0
    interval_ms: int = 1000
    delay_ms: int = 0
    loop: bool = False
    repeat: bool = False
    mode: TrackMode | str = "nmea"
    source: str = ""  # boat, ship, truck, etc.


@dataclass
class TrackInfo:
    name: str
    cfg: TrackCfg
    coords: list[tuple[float, float]]
    path: str
