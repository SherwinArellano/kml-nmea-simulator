from typing import override
from core.config import AppConfig
from core.messages import MessageBuilder
from core.geodesy import checksum, deg2dm
import time


class NMEABuilder(MessageBuilder):
    @override
    def build(self, ctx):
        """
        Build a list of NMEA sentences based on the global NMEA_TYPES and NMEA_BATCH.
        """

        ti = ctx.ti
        cfg = ti.cfg
        point = ctx.point
        ts = time.strftime("%H%M%S", time.gmtime(ctx.epoch_s))

        app_cfg = AppConfig.get()
        nmea_types = app_cfg.nmea_types

        lat_dm, ns = deg2dm(point[0], is_lat=True)
        lon_dm, ew = deg2dm(point[1], is_lat=False)
        sog = cfg.vel_kmh * 0.539957

        msgs: list[str] = []
        for nmea in nmea_types:
            if nmea == "GPRMC":
                pay = (
                    f"GPRMC,{ts}.00,A,{lat_dm},{ns}," f"{lon_dm},{ew},{sog:.2f},0.0,,,"
                )
            elif nmea == "GPGGA":
                fix_q, num_sat, hdop, alt = 1, 8, 1.0, 0.0
                pay = (
                    f"GPGGA,{ts}.00,"
                    f"{lat_dm},{ns},{lon_dm},{ew},"
                    f"{fix_q},{num_sat},{hdop:.1f},{alt:.1f},M,0.0,M,,"
                )
            elif nmea == "GPGLL":
                pay = f"GPGLL,{lat_dm},{ns},{lon_dm},{ew}," f"{ts}.00,A"
            else:
                continue

            msgs.append(f"${pay}{checksum(pay)}\r\n")

        return msgs
