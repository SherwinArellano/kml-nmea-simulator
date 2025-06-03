from .cli import Args
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class StreamConfig:
    enabled: bool


def parse_stream_yaml(yaml_cfg: dict[str, Any]) -> StreamConfig:
    return StreamConfig(yaml_cfg.get("enabled", False))


def build_stream_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> StreamConfig | None:
    stream_cfg = parse_stream_yaml(yaml_cfg) if len(yaml_cfg) else None

    if "stream" in cli:
        if stream_cfg:
            # enable yaml config if exists
            stream_cfg = StreamConfig(True)
        else:
            # use cli provided
            stream_cfg = StreamConfig(cli.stream or False)

    return stream_cfg
