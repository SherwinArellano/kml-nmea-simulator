# kml2nmea Simulator

A live NMEA (or custom `$TRK`) streamer driven by Google My Maps KML exports.

Instead of static playback, **kml2nmea** walks each route in your KML at real-world speed and broadcasts:

- **NMEA `$GPRMC`** sentences (default, `mode=sea`) for marine or GPS-style feeds
- **Custom `$TRK`** records (`mode=land`) for land-vehicle tracking

All configuration is specified _inline_ in each `<Placemark><name>` tag—no separate YAML/JSON required.

---

## Features

- **Inline config** via the KML `<name>` field
- Adjustable **speed** (`velocity`), **frequency** (`freq`), **initial delay** (`delay`) in milliseconds
- **Loop** and **repeat** controls for ping-pong or continuous playback
- **Mode** switch to select output format (`sea` vs. `land`)
- **Geodesic accuracy** using the WGS-84 ellipsoid (via `geographiclib`)
- **Concurrency**: each track runs in its own `asyncio` task

---

## Installation

```bash
# Python 3.8+ recommended
git clone https://github.com/youruser/kml2nmea.git
cd kml2nmea
pip install geographiclib
```

---

## Usage

```bash
python3 kml2nmea.py <map.kml> <HOST:PORT>
```

**Example:**

```bash
python3 kml2nmea.py mymap.kml 127.0.0.1:10110
socat -u UDP-RECV:10110 STDOUT
```

---

## Configuring Each Route

Within your KML file, each `<Placemark>` with a `<LineString>` should define a `<name>` containing the human-readable ID (quoted or unquoted) followed by zero or more space-separated tokens.

```xml
<Placemark>
  <name><![CDATA["Truck 1" velocity=45 freq=500 loop delay=2000 repeat mode=land]]></name>
  <LineString>
    <coordinates>
      12.4923,41.8902,0 12.4964,41.9028,0 ...
    </coordinates>
  </LineString>
</Placemark>
```

### Supported Tokens

| Token                  | Description                                       | Default |
| ---------------------- | ------------------------------------------------- | ------- |
| `velocity=<km/h>`      | Travel speed in km/h                              | 5.0     |
| `freq=<ms>`            | Update interval in milliseconds                   | 1000    |
| `delay=<ms>`           | Initial delay before streaming starts (ms)        | 0       |
| `loop`                 | Ping-pong playback (back and forth)               | off     |
| `repeat`               | Continuous restart upon completion                | off     |
| `mode=<sea&#124;land>` | Output format: `sea`→NMEA `$GPRMC`, `land`→`$TRK` | `sea`   |

---

## Output Formats

### NMEA `$GPRMC` (mode=sea)

```
$GPRMC,<hhmmss>.00,A,<lat>,<N/S>,<lon>,<E/W>,<sog>,0.0,,,
*<CHECKSUM>PlacemarkName

Example:
$GPRMC,143212.00,A,4128.6081,N,01229.7840,E,12.34,0.0,,,*5ARiverRoute
```

- **Latitude/Longitude** in degrees+minutes (DDMM.MMMM)
- **SOG** in knots (km/h → kn)
- **Timestamp** in UTC `hhmmss`

### Custom `$TRK` (mode=land)

```
$TRK,<PlacemarkName>,<YYYYMMDDThhmmssZ>,<lat>,<lon>,<km/h>,<heading>*<CHECKSUM>

Example:
$TRK,Truck 1,20250516T144643Z,41.902800,12.496400,45.0,270*3F
```

- **Coordinates** in decimal degrees
- **Speed** in km/h
- **Heading** as integer degrees (0–359)
- **Timestamp** in ISO-style UTC
