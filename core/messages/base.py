from abc import ABC, abstractmethod
from typing import Self
from core.models import TrackInfo
from dataclasses import dataclass


@dataclass
class BuilderContext:
    ti: TrackInfo
    point: tuple[float, float]
    epoch_s: float | None = None

    # For NMEA types
    nmea_types: list[str] | None = None

    # For TRK types
    prev_point: tuple[float, float] | None = None


class MessageBuilder(ABC):
    ctx: BuilderContext | None = None

    @abstractmethod
    def set_context(self, ctx: BuilderContext) -> Self: ...

    @abstractmethod
    def build(self) -> list[str]: ...
