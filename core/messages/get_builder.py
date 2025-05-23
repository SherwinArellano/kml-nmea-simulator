from core.models import TrackMode
from .base import MessageBuilder
from .nmea import NMEABuilder
from .trk import TRKBuilder


def get_builder(mode: TrackMode | str) -> MessageBuilder:
    if mode == "nmea":
        return NMEABuilder()

    return TRKBuilder()
