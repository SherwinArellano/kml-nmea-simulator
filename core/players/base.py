from abc import ABC, abstractmethod
from core.messages import MessageBuilder
from core.transports import Transport
from core.models import TrackInfo
from core.config import AppConfig


class TrackPlayer(ABC):
    def __init__(
        self,
        cfg: AppConfig,
        ti: TrackInfo,
        builder: MessageBuilder,
        transports: list[Transport],
    ):
        self.cfg = cfg
        self.ti = ti
        self.builder = builder
        self.transports = transports

    @abstractmethod
    async def play(self): ...
