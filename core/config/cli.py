from .common import *
import argparse


class Args(argparse.Namespace):
    kml: list[str] | None
    udp_target: str | None
    mqtt_broker: str | None
    rest_target: str | None
    rest_post: str
    rest_put: str
    stream: bool | None
    topic: str
    nmea_types: str | None
    nmea_batch_types: bool | None
    verbose: bool | None
    filegen_mode: FilegenMode | None
    filegen_stream: bool
    outdir: str
    outfile: str


def parse_args() -> Args:
    parser = argparse.ArgumentParser(
        description="KML Simulator for IRIDESS' backend. Streams UDP or MQTT (or both) messages of type NMEA and custom TRK. Files can also be generated for a full history of messages.",
        formatter_class=argparse.RawTextHelpFormatter,
        argument_default=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="YAML config file path, defaults to config.yaml in the current directory",
    )

    parser.add_argument(
        "kml",
        nargs="+",
        help="Path(s) to KML file or directory containing KMLs;\n"
        "If no files or directories provided, uses the current directory.",
    )

    parser.add_argument(
        "--udp",
        dest="udp_target",
        metavar="HOST:PORT",
        nargs="?",
        help="UDP target address;\n"
        f"If address not provided, uses YAML-provided address otherwise defaults to {DEFAULT_UDP_URL}",
    )

    parser.add_argument(
        "--mqtt",
        dest="mqtt_broker",
        metavar="BROKER:PORT",
        nargs="?",
        help="MQTT broker address;\n"
        f"If address not provided, uses YAML-provided address otherwise defaults to {DEFAULT_MQTT_URL}",
    )

    parser.add_argument("--topic", help="MQTT topic (default: kml2nmea)")

    parser.add_argument(
        "--nmea-types",
        choices=["GPRMC", "GPGGA", "GPGLL"],
        help="Comma-separated NMEA sentences to emit in sea mode (e.g. GPRMC,GPGLL)",
    )

    parser.add_argument(
        "--nmea-batch-types",
        action="store_true",
        help="if set, emit all selected NMEA sentences in one UDP/MQTT packet per update",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="if set, print transport messages on console",
    )

    parser.add_argument(
        "--filegen",
        dest="filegen_mode",
        nargs="?",
        choices=["single", "multi"],
        help="If no mode provided, uses YAML-provided configuration;\n"
        "single = write one merged file (default);\n"
        "multi = one file per track",
    )

    parser.add_argument(
        "--filegen-stream",
        dest="filegen_stream",
        action="store_true",
        default=False,
        help="if set, streams messages rather than generating them at once (instant)",
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
        help="Path to merged output file for single filegen mode\n"
        "(ignored in 'multi' filegen mode; default: output.trks)",
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="if set, will activate streaming service",
    )

    parser.add_argument(
        "--rest",
        dest="rest_target",
        metavar="HOST:PORT",
        nargs="?",
        help="Backend service address to communicate with;\n"
        f"If address not provided, uses YAML-provided address otherwise defaults to {DEFAULT_REST_URL}\n",
    )

    parser.add_argument(
        "--post",
        dest="rest_post",
        default="/api/operations",
        help="Backend endpoint to send operation creation requests;\n"
        "If not provided, defaults to /api/operations",
    )

    parser.add_argument(
        "--put",
        dest="rest_put",
        default="/api/operations",
        help="Backend endpoint to send operation status requests;\n"
        "If not provided, defaults to /api/operations",
    )

    return parser.parse_args(namespace=Args())
