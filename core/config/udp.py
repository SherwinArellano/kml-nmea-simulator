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


def build_udp_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> UDPConfig | None:
    udp_cfg = None

    if "udp_target" in cli:
        host, port = parse_host_port(cli.udp_target or DEFAULT_UDP_URL)
        udp_cfg = UDPConfig(True, host, port)
    elif len(yaml_cfg):
        host = yaml_cfg.get("host")
        if not host:
            raise KeyError("Missing required 'host' in udp section of YAML config")

        port = yaml_cfg.get("port")
        if not port:
            raise KeyError("Missing required 'port' in udp section of YAML config")

        udp_cfg = UDPConfig(yaml_cfg.get("enabled", False), host, port)

    return udp_cfg
