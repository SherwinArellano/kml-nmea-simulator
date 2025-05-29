from core.models import TrackMode
from dataclasses import dataclass
from typing import Any
from .cli import Args
from .common import NmeaType
import os
import glob


@dataclass(frozen=True)
class DefaultTrackConfig:
    velocity: float
    interval: float
    delay: float
    loop_mode: bool
    repeat_mode: bool
    mode: TrackMode
    source: str  # like "truck", "ship", etc.


def build_default_track_cfg(yaml_cfg: dict[str, Any]) -> DefaultTrackConfig:
    return DefaultTrackConfig(
        yaml_cfg.get("default_velocity", 50.0),
        yaml_cfg.get("default_interval", 1000),
        yaml_cfg.get("default_delay", 0),
        yaml_cfg.get("default_loop_mode", False),
        yaml_cfg.get("default_repeat_mode", False),
        yaml_cfg.get("default_mode", "nmea"),
        yaml_cfg.get("default_source", "truck"),
    )


def build_kml_paths(cli: Args, yaml_cfg: dict[str, Any]) -> list[str]:
    kml_sources = cli.kml or yaml_cfg.get("kml_paths") or ["."]
    kml_paths: list[str] = []

    for path in kml_sources:
        if os.path.isdir(path):
            kml_paths.extend(glob.glob(os.path.join(path, "*.kml")))
        elif path.lower().endswith(".kml"):
            kml_paths.append(path)

    return kml_paths


def build_nmea_batch(cli: Args, yaml_cfg: dict[str, Any]) -> bool:
    return bool(
        cli.nmea_batch_types
        if "nmea_batch_types" in cli
        else yaml_cfg.get("nmea_batch", False)
    )


def build_nmea_types(cli: Args, yaml_cfg: dict[str, Any]) -> list[NmeaType]:
    return (
        [t.strip().upper() for t in cli.nmea_types.split(",")]
        if "nmea_types" in cli and cli.nmea_types
        else yaml_cfg.get("nmea_types", ["GPRMC", "GPGGA", "GPGLL"])
    )
