from .common import DEFAULT_REST_URL
from .cli import Args
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RESTConfig:
    enabled: bool
    url: str
    post: str
    put: str


def parse_rest_yaml(yaml_cfg: dict[str, Any]) -> RESTConfig:
    url = yaml_cfg.get("url")
    if not url:
        raise KeyError("Missing required 'url' in rest section of YAML config")

    post = yaml_cfg.get("post")
    if not post:
        raise KeyError("Missing required 'post' in rest section of YAML config")

    put = yaml_cfg.get("put")
    if not put:
        raise KeyError("Missing required 'put' in rest section of YAML config")

    return RESTConfig(
        enabled=yaml_cfg.get("enabled", False), url=url, post=post, put=put
    )


def build_rest_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> RESTConfig | None:
    rest_cfg = parse_rest_yaml(yaml_cfg) if len(yaml_cfg) else None

    if "rest_target" in cli:
        if not cli.rest_target and rest_cfg:
            # enable yaml config if exists
            rest_cfg = RESTConfig(
                enabled=True, url=rest_cfg.url, post=rest_cfg.post, put=rest_cfg.put
            )
        else:
            # use cli provided host:port or defaults
            url = cli.rest_target if cli.rest_target else DEFAULT_REST_URL
            rest_cfg = RESTConfig(
                enabled=True, url=url, post=cli.rest_post, put=cli.rest_put
            )

    return rest_cfg
