from typing import override
from core.messages import MessageBuilder
from core.geodesy import _GEO, checksum
from core.utils import CallParams
import time


class TRKParams(CallParams):
    def __init__(self, prev_point: tuple[float, float] | None):
        self.prev_point = prev_point


class TRKBuilder(MessageBuilder):
    EXPECTS = [TRKParams]

    def _calc_heading(
        self, point: tuple[float, float], prev_point: tuple[float, float]
    ) -> float:
        d = _GEO.Inverse(prev_point[0], prev_point[1], point[0], point[1])
        return d["azi1"] % 360

    @override
    def build(self, ctx):
        """
        Build the list of $TRK messages (always exactly one) for land mode.
        """
        ctx.validate(self.EXPECTS)

        ti = ctx.ti
        cfg = ti.cfg
        point = ctx.point
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(ctx.epoch_s))

        # Calculate heading (bearing)
        azi = 0.0
        prev_point = ctx.get(TRKParams).prev_point
        if prev_point:
            azi = self._calc_heading(ctx.point, prev_point)

        payload = (
            f"TRK,{ti.name},{cfg.source},{ts},"
            f"{point[0]:.6f},{point[1]:.6f},"
            f"{cfg.vel_kmh:.1f},{int(azi)}"
        )

        return [f"${payload}{checksum(payload)}\r\n"]
