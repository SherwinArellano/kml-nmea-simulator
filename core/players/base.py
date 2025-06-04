from abc import ABC, abstractmethod
from core.messages import MessageBuilder
from core.transports import Transport
from core.models import TrackInfo
from pyee.asyncio import AsyncIOEventEmitter


class TrackPlayer(ABC):
    def __init__(
        self,
        ti: TrackInfo,
        builder: MessageBuilder,
        transports: list[Transport],
    ):
        self.ti = ti
        self.builder = builder
        self.transports = transports
        self._emitter = AsyncIOEventEmitter()

    @abstractmethod
    async def play(self): ...

    def start(self):
        return self._emitter.on("start")

    def finish(self):
        return self._emitter.on("finish")
