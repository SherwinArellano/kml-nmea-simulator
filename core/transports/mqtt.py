from .base import Transport
from typing import override
import paho.mqtt.client as mqtt


class MQTTTransport(Transport):
    def __init__(self, broker: tuple[str, int], topic: str):
        self.client = mqtt.Client()
        self.client.connect(*broker)
        self.topic = topic

    @override
    def send(self, ti, payload):
        self.client.publish(f"{self.topic}/{ti.name}", payload)

    @override
    def close(self):
        self.client.disconnect()
