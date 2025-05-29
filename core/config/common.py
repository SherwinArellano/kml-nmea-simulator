from typing import Literal

FilegenMode = Literal["single", "multi"]
NmeaType = Literal["GPRMC", "GPGGA", "GPGLL"] | str

DEFAULT_UDP_URL = "localhost:10110"
DEFAULT_MQTT_URL = "localhost:1883"
DEFAULT_MQTT_TOPIC = "kml2nmea"
DEFAULT_REST_URL = "0.0.0.0:8000"
