from .common import DEFAULT_MQTT_URL, DEFAULT_MQTT_TOPIC
from .cli import Args
from core.utils import parse_host_port
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MQTTConfig:
    enabled: bool
    host: str
    port: int
    topic: str


def parse_mqtt_yaml(yaml_cfg: dict[str, Any], topic: str) -> MQTTConfig:
    host = yaml_cfg.get("host")
    if not host:
        raise KeyError("Missing required 'host' in mqtt section of YAML config")

    port = yaml_cfg.get("port")
    if not port:
        raise KeyError("Missing required 'port' in mqtt section of YAML config")

    return MQTTConfig(yaml_cfg.get("enabled", False), host, port, topic)


def build_mqtt_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> MQTTConfig | None:
    topic = cli.topic if "topic" in cli else yaml_cfg.get("topic", DEFAULT_MQTT_TOPIC)
    mqtt_cfg = parse_mqtt_yaml(yaml_cfg, topic) if len(yaml_cfg) else None

    if "mqtt_broker" in cli:
        if not cli.mqtt_broker and mqtt_cfg:
            # enable yaml config if exists
            mqtt_cfg = MQTTConfig(True, mqtt_cfg.host, mqtt_cfg.port, topic)
        else:
            # use cli provided host:port or defaults
            host, port = parse_host_port(cli.mqtt_broker or DEFAULT_MQTT_URL)
            mqtt_cfg = MQTTConfig(
                True, host, port, cli.topic if "topic" in cli else DEFAULT_MQTT_TOPIC
            )

    return mqtt_cfg
