from typing import ClassVar, Optional, Any
from dataclasses import dataclass
from .common import NmeaType
from .cli import Args
from .udp import UDPConfig, build_udp_cfg
from .mqtt import MQTTConfig, build_mqtt_cfg
from .filegen import FilegenConfig, build_filegen_cfg
from .rest import RESTConfig, build_rest_cfg
from .track import (
    DefaultTrackConfig,
    build_default_track_cfg,
    build_kml_paths,
    build_nmea_batch,
    build_nmea_types,
)
import os
import yaml


@dataclass(frozen=True)
class AppConfig:
    kml_paths: list[str]
    nmea_batch: bool
    nmea_types: list[NmeaType]
    default_track_cfg: DefaultTrackConfig
    udp: UDPConfig | None
    mqtt: MQTTConfig | None
    filegen: FilegenConfig | None
    rest: RESTConfig | None

    # Singleton backing field
    _instance: ClassVar[Optional["AppConfig"]] = None

    @classmethod
    def init(cls, cfg: "AppConfig") -> None:
        if cls._instance is not None:
            raise RuntimeError("AppConfig has already been initialized.")
        cls._instance = cfg

    @classmethod
    def get(cls) -> "AppConfig":
        if cls._instance is None:
            raise RuntimeError("AppConfig is not initialized.")
        return cls._instance


def load_yaml_config(path: str) -> dict[str, Any]:
    if os.path.isfile(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)
    return {}


def build_app_cfg(cli: Args, yaml_cfg: dict[str, Any]):
    # Load YAML subsections safely
    yaml_udp_cfg: dict[str, Any] = yaml_cfg.get("udp", {})
    yaml_mqtt_cfg: dict[str, Any] = yaml_cfg.get("mqtt", {})
    yaml_filegen_cfg: dict[str, Any] = yaml_cfg.get("filegen", {})
    yaml_rest_cfg: dict[str, Any] = yaml_cfg.get("rest", {})

    return AppConfig(
        kml_paths=build_kml_paths(cli, yaml_cfg),
        nmea_batch=build_nmea_batch(cli, yaml_cfg),
        nmea_types=build_nmea_types(cli, yaml_cfg),
        default_track_cfg=build_default_track_cfg(yaml_cfg),
        udp=build_udp_cfg(cli, yaml_udp_cfg),
        mqtt=build_mqtt_cfg(cli, yaml_mqtt_cfg),
        filegen=build_filegen_cfg(cli, yaml_filegen_cfg),
        rest=build_rest_cfg(cli, yaml_rest_cfg),
    )
