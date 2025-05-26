from abc import ABC, abstractmethod
from core.models import TrackInfo
from core.utils import CallContext
from dataclasses import dataclass


@dataclass
class MessageContext(CallContext):
    ti: TrackInfo
    point: tuple[float, float]
    epoch_s: float | None = None


class MessageBuilder(ABC):
    @abstractmethod
    def build(self, ctx: MessageContext) -> list[str]: ...
