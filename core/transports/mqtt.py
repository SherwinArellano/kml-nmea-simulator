from .base import Transport
from typing import override, cast
import paho.mqtt.client as mqtt
from core.config import AppConfig
from urllib.parse import urlparse


class MQTTTransport(Transport):
    def _init_ws_client(self, url):
        parsed = urlparse(url)
        host = cast(str, parsed.hostname)
        port = parsed.port or (443 if parsed.scheme == "wss" else 80)
        path = parsed.path or "/"

        self.client = mqtt.Client(transport="websockets")
        if parsed.scheme == "wss":
            self.client.tls_set()

        self.client.ws_set_options(path=path)
        self.client.connect(host, port)

    def __init__(self, broker: tuple[str, int], topic: str):
        self.topic = topic
        if broker[0].startswith(("ws", "wss")):
            self._init_ws_client(broker[0])
        else:
            self.client = mqtt.Client()
            self.client.connect(*broker)

    @override
    def send(self, ctx):
        topic = f"{self.topic}/{ctx.ti.cfg.mode}/{ctx.ti.cfg.id_port}"
        self.client.publish(topic, ctx.payload)
        if AppConfig.get().verbose:
            print(f"[MQTT:{topic}] {ctx.payload.decode()}")

    @override
    def close(self):
        self.client.disconnect()
