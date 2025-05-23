from core.models import TrackInfo


class TrackManager:
    def __init__(self, tracks: list[TrackInfo]):
        self.tracks = {t.name: t for t in tracks}

    def values(self):
        return self.tracks.values()
