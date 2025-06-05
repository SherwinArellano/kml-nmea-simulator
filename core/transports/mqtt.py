from .base import Transport
from typing import override
import paho.mqtt.client as mqtt
from core.config import AppConfig


class MQTTTransport(Transport):
    def __init__(self, broker: tuple[str, int], topic: str):
        self.client = mqtt.Client()
        self.client.connect(*broker)
        self.topic = topic

    @override
    def send(self, ctx):
        topic = f"{self.topic}/{ctx.ti.cfg.mode}/{ctx.ti.cfg.dest_port}"
        self.client.publish(topic, ctx.payload)
        if AppConfig.get().verbose:
            print(f"[MQTT:{topic}] {ctx.payload.decode()}")

    @override
    def close(self):
        self.client.disconnect()
