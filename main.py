#!/usr/bin/env python3
from core.parser import parse_tracks
from core.models import TrackInfo
from core.services import ServiceManager, StreamingService, RESTService
from core.track_manager import TrackManager
from core.config import parse_args, build_app_cfg, load_yaml_config, AppConfig
from core.utils import increment_all_track_numbers
from core.walker import total_path_distance
import sys
import asyncio


async def main():
    args = parse_args()
    yaml_cfg = load_yaml_config(args.config)
    cfg = build_app_cfg(args, yaml_cfg)
    AppConfig.init(cfg)

    if not cfg.kml_paths:
        sys.exit("No KML files found in specified paths.")

    # Synchronously load all TrackInfo
    tracks: list[TrackInfo] = []
    for path in cfg.kml_paths:
        for name, track_cfg, coords in parse_tracks(path):
            print(f"Loaded track: {name} (from {path})")
            total_dist = total_path_distance(coords, track_cfg.loop)
            tracks.append(TrackInfo(name, track_cfg, coords, total_dist, path))
        increment_all_track_numbers(path, path)

    if not tracks:
        sys.exit("No tracks found in the provided KML files.")

    # Create managers
    tm = TrackManager(tracks)
    sm = ServiceManager(tm)

    # Register services
    sm.register(RESTService())

    if not sm.transports and not sm.instant_transports:
        sys.exit("No transports set or enabled.")

    await sm.start_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user, shutting down.")
        sys.exit(0)
