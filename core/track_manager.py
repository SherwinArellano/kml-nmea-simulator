from core.models import TrackInfo


class TrackManager:
    def __init__(self, tracks: list[TrackInfo]):
        self.tracks = {t.name: t for t in tracks}

    def get(self, track_name: str):
        return self.tracks[track_name]

    def values(self):
        return self.tracks.values()
