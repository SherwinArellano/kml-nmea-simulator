from .common import DEFAULT_UDP_URL
from .cli import Args
from core.utils import parse_host_port
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UDPConfig:
    enabled: bool
    host: str
    port: int


def parse_udp_yaml(yaml_cfg: dict[str, Any]) -> UDPConfig:
    host = yaml_cfg.get("host")
    if not host:
        raise KeyError("Missing required 'host' in udp section of YAML config")

    port = yaml_cfg.get("port")
    if not port:
        raise KeyError("Missing required 'port' in udp section of YAML config")

    return UDPConfig(yaml_cfg.get("enabled", False), host, port)


def build_udp_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> UDPConfig | None:
    udp_cfg = parse_udp_yaml(yaml_cfg) if len(yaml_cfg) else None

    if "udp_target" in cli:
        if not cli.udp_target and udp_cfg:
            # enable yaml config if exists
            udp_cfg = UDPConfig(
                True,
                udp_cfg.host,
                udp_cfg.port,
            )
        else:
            # use cli provided host:port or defaults
            host, port = parse_host_port(cli.udp_target or DEFAULT_UDP_URL)
            udp_cfg = UDPConfig(True, host, port)

    return udp_cfg
