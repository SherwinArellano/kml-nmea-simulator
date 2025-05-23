from typing import override
from core.messages import BuilderContext
from core.walker import walk_path
from .base import TrackPlayer
import time


class InstantPlayer(TrackPlayer):
    def generate_messages(self):
        """Yields (timestamp, raw_payload_bytes, track_name) in track-order."""
        ti = self.ti
        cfg = self.ti.cfg

        start = time.time() + cfg.delay_ms / 1000
        step_s = cfg.interval_ms / 1000
        step_m = cfg.vel_kmh / 3.6 * step_s

        prev_point = None
        for idx, point in enumerate(walk_path(ti.coords, step_m, cfg.loop)):
            epoch_s = start + idx * step_s
            ctx = BuilderContext(
                self.ti,
                point,
                epoch_s,
                nmea_types=self.cfg.nmea_types,
                prev_point=prev_point,
            )
            self.builder.set_context(ctx)

            msgs = self.builder.build()

            for m in msgs:
                yield epoch_s, m.encode(), ti.name

            prev_point = point

    @override
    async def play(self):
        # generate messages of all tracks sorted by timestamp
        msgs = list(self.generate_messages())
        msgs.sort(key=lambda x: x[0])

        for _ts, payload, _topic in msgs:
            for t in self.transports:
                t.send(self.ti, payload)
