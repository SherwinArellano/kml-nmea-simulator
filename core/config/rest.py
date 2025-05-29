from .common import DEFAULT_REST_URL
from .cli import Args
from core.utils import parse_host_port
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class RESTConfig:
    enabled: bool
    url: str


def build_rest_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> RESTConfig | None:
    rest_cfg = None

    if "rest_target" in cli:
        url = (
            cli.rest_target
            if "rest_target" in cli and cli.rest_target
            else DEFAULT_REST_URL
        )

        rest_cfg = RESTConfig(True, url)
    elif len(yaml_cfg):
        url = yaml_cfg.get("url")
        if not url:
            raise KeyError("Missing required 'url' in rest section of YAML config")

        rest_cfg = RESTConfig(yaml_cfg.get("enabled", False), url)

    return rest_cfg
