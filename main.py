#!/usr/bin/env python3
from core.parser import parse_tracks
from core.models import TrackInfo
from core.services import ServiceManager, StreamingService
from core.track_manager import TrackManager
from core.config import parse_args, build_app_cfg
import sys
import asyncio


async def main():
    args = parse_args()
    cfg = build_app_cfg(args)

    if not cfg.kml_paths:
        sys.exit("No KML files found in specified paths.")

    # Synchronously load all TrackInfo
    tracks: list[TrackInfo] = []
    for path in cfg.kml_paths:
        for name, track_cfg, coords in parse_tracks(path):
            tracks.append(TrackInfo(name, track_cfg, coords, path))

    if not tracks:
        sys.exit("No tracks found in the provided KML files.")

    # Create managers
    tm = TrackManager(tracks)
    sm = ServiceManager(cfg, tm)

    # Register services
    sm.register(StreamingService)

    await sm.start_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user, shutting down.")
        sys.exit(0)
