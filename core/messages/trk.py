from typing import override, Self
from core.messages import MessageBuilder, ContextNotSetError
from core.geodesy import _GEO, checksum
import time


class TRKBuilder(MessageBuilder):
    azi: float = 0.0

    @override
    def set_context(self, ctx):
        self.ctx = ctx
        self.set_timestamp(ctx.epoch_s)
        if ctx.prev_point:
            self.calc_heading(ctx.point, ctx.prev_point)
        return self

    def set_timestamp(self, epoch_s: float | None) -> Self:
        self.ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(epoch_s))
        return self

    def calc_heading(
        self, point: tuple[float, float], prev_point: tuple[float, float]
    ) -> Self:
        d = _GEO.Inverse(prev_point[0], prev_point[1], point[0], point[1])
        self.azi = d["azi1"] % 360
        return self

    @override
    def build(self):
        """
        Build the list of $TRK messages (always exactly one) for land mode.
        """
        if self.ctx is None:
            raise ContextNotSetError(self.__class__.__name__)

        ti = self.ctx.ti
        cfg = ti.cfg
        point = self.ctx.point
        payload = (
            f"TRK,{ti.name},{cfg.source},{self.ts},"
            f"{point[0]:.6f},{point[1]:.6f},"
            f"{cfg.vel_kmh:.1f},{int(self.azi)}"
        )

        return [f"${payload}{checksum(payload)}\r\n"]
