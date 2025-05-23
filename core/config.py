from core.utils import parse_host_port
from typing import Literal, cast
from dataclasses import dataclass
import argparse
import os
import glob

FilegenMode = Literal["single", "multi"]
NmeaType = Literal["GPRMC", "GPGGA", "GPGLL"]


class Args(argparse.Namespace):
    kml: list[str]
    udp_target: str
    mqtt_broker: str
    topic: str
    nmea_types: str
    nmea_batch_types: bool
    filegen_mode: str
    outdir: str
    outfile: str


@dataclass
class AppConfig:
    kml_paths: list[str]
    nmea_batch: bool
    nmea_types: list[NmeaType | str]
    udp_target: tuple[str, int] | None
    mqtt_broker: tuple[str, int] | None
    mqtt_topic: str
    filegen_mode: FilegenMode | None
    outfile: str
    outdir: str


def parse_args() -> Args:
    parser = argparse.ArgumentParser(
        description="Stream KML tracks via UDP/MQTT or generate them as files.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "kml",
        nargs="*",
        default=["."],
        help="Path(s) to KML file or directory containing KMLs;\n"
        "If no files or directories provided, uses the current directory.",
    )

    parser.add_argument(
        "--udp",
        dest="udp_target",
        nargs="?",
        const="localhost:10110",
        metavar="HOST:PORT",
        help="UDP target address;\n"
        "If address not provided, defaults to localhost:10110",
    )

    parser.add_argument(
        "--mqtt",
        dest="mqtt_broker",
        nargs="?",
        const="localhost:1883",
        metavar="BROKER:PORT",
        help="MQTT broker address;\n"
        "If address not provided, defaults to localhost:1883",
    )

    parser.add_argument(
        "--topic", default="kml2nmea", help="MQTT topic (default: kml2nmea)"
    )

    parser.add_argument(
        "--nmea-types",
        choices=["GPRMC", "GPGGA", "GPGLL"],
        default="GPRMC,GPGGA,GPGLL",
        help="Comma-separated NMEA sentences to emit in sea mode (e.g. GPRMC,GPGLL)",
    )

    parser.add_argument(
        "--nmea-batch-types",
        action="store_true",
        help="if set, emit all selected NMEA sentences in one UDP/MQTT packet per update",
    )

    parser.add_argument(
        "--filegen",
        dest="filegen_mode",
        choices=["single", "multi"],
        help="single = write one merged file (default);\n" "multi = one file per track",
    )

    parser.add_argument(
        "--outdir",
        default=".",
        metavar="DIR",
        help="Directory for single-track files\n" "(ignored in 'single' filegen mode)",
    )

    parser.add_argument(
        "--outfile",
        default="output.trks",
        metavar="FILE",
        help="Path to merged output file for global mode\n"
        "(ignored in 'multi' filegen mode)",
    )

    return parser.parse_args(namespace=Args())


def build_app_cfg(args: Args) -> AppConfig:
    nmea_types = [t.strip().upper() for t in args.nmea_types.split(",") if t.strip()]
    kml_paths: list[str] = []
    for path in args.kml:
        if os.path.isdir(path):
            kml_paths.extend(glob.glob(os.path.join(path, "*.kml")))
        elif path.lower().endswith(".kml"):
            kml_paths.append(path)

    return AppConfig(
        kml_paths=kml_paths,
        filegen_mode=cast(FilegenMode, args.filegen_mode),
        mqtt_broker=parse_host_port(args.mqtt_broker) if args.mqtt_broker else None,
        mqtt_topic=args.topic,
        nmea_batch=args.nmea_batch_types,
        nmea_types=nmea_types,
        outdir=args.outdir,
        outfile=args.outfile,
        udp_target=parse_host_port(args.udp_target) if args.udp_target else None,
    )
