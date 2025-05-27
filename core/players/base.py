from abc import ABC, abstractmethod
from core.messages import MessageBuilder
from core.transports import Transport
from core.models import TrackInfo


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

    @abstractmethod
    async def play(self): ...
