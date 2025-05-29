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


def build_mqtt_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> MQTTConfig | None:
    mqtt_cfg = None

    if "mqtt_broker" in cli:
        host, port = parse_host_port(cli.mqtt_broker or DEFAULT_MQTT_URL)
        mqtt_cfg = MQTTConfig(True, host, port, cli.topic or DEFAULT_MQTT_TOPIC)
    elif len(yaml_cfg):
        host = yaml_cfg.get("host")
        if not host:
            raise KeyError("Missing required 'host' in mqtt section of YAML config")

        port = yaml_cfg.get("port")
        if not port:
            raise KeyError("Missing required 'port' in mqtt section of YAML config")

        topic = (
            cli.topic if "topic" in cli else yaml_cfg.get("topic", DEFAULT_MQTT_TOPIC)
        )

        mqtt_cfg = MQTTConfig(yaml_cfg.get("enabled", False), host, port, topic)

    return mqtt_cfg
