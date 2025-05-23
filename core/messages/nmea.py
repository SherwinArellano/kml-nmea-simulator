from typing import override, Self
from core.messages import MessageBuilder, ContextNotSetError
from core.geodesy import checksum, deg2dm
from core.config import NmeaType
import time


class NMEABuilder(MessageBuilder):
    nmea_types: list[str] = []

    @override
    def set_context(self, ctx):
        self.ctx = ctx
        self.set_timestamp(ctx.epoch_s)
        if ctx.nmea_types:
            self.set_nmea_types(ctx.nmea_types)
        return self

    def set_timestamp(self, epoch_s: float | None) -> Self:
        self.ts = time.strftime("%H%M%S", time.gmtime(epoch_s))
        return self

    def set_nmea_types(self, nmea_types: list[str]) -> Self:
        self.nmea_types = nmea_types
        return self

    @override
    def build(self):
        """
        Build a list of NMEA sentences based on the global NMEA_TYPES and NMEA_BATCH.
        """
        if self.ctx is None:
            raise ContextNotSetError(self.__class__.__name__)

        ti = self.ctx.ti
        cfg = ti.cfg
        point = self.ctx.point

        lat_dm, ns = deg2dm(point[0], is_lat=True)
        lon_dm, ew = deg2dm(point[1], is_lat=False)
        sog = cfg.vel_kmh * 0.539957

        msgs: list[str] = []
        for nmea in self.nmea_types:
            if nmea == "GPRMC":
                pay = (
                    f"GPRMC,{self.ts}.00,A,{lat_dm},{ns},"
                    f"{lon_dm},{ew},{sog:.2f},0.0,,,"
                )
            elif nmea == "GPGGA":
                fix_q, num_sat, hdop, alt = 1, 8, 1.0, 0.0
                pay = (
                    f"GPGGA,{self.ts}.00,"
                    f"{lat_dm},{ns},{lon_dm},{ew},"
                    f"{fix_q},{num_sat},{hdop:.1f},{alt:.1f},M,0.0,M,,"
                )
            elif nmea == "GPGLL":
                pay = f"GPGLL,{lat_dm},{ns},{lon_dm},{ew}," f"{self.ts}.00,A"
            else:
                continue

            msgs.append(f"${pay}{checksum(pay)}\r\n")

        return msgs
