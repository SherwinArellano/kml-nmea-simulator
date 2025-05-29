from .common import DEFAULT_REST_URL
from .cli import Args
from core.utils import parse_host_port
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class RESTConfig:
    enabled: bool
    host: str
    port: int
    backend_url: str


def build_rest_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> RESTConfig | None:
    rest_cfg = None

    if "rest_target" in cli:
        host, port = parse_host_port(cli.rest_target or DEFAULT_REST_URL)
        if "backend_url" not in cli:
            raise ValueError("Missing required argument: '--backend-url <url>'")
        rest_cfg = RESTConfig(True, host, port, cast(str, cli.backend_url))
    elif len(yaml_cfg):
        host = yaml_cfg.get("host")
        if not host:
            raise KeyError("Missing required 'host' in rest section of YAML config")

        port = yaml_cfg.get("port")
        if not port:
            raise KeyError("Missing required 'port' in rest section of YAML config")

        backend_url = yaml_cfg.get("backend_url")
        if not backend_url:
            raise KeyError(
                "Missing required 'backend_url' in rest section of YAML config"
            )

        rest_cfg = RESTConfig(yaml_cfg.get("enabled", False), host, port, backend_url)

    return rest_cfg
