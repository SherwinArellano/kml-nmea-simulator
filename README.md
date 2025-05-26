# Generalized Track Simulator

A real‑time track simulator that streams simulated movement of one or more objects based on KML sources (e.g., Google My Maps). Depending on provided options, it produces asynchronous output over UDP, MQTT, or both, **or** generates timestamped output files, with the following customizable parameters:

- **Track modes**:

  - **NMEA** (`mode=nmea` / `sea`): standard NMEA 0183 sentences (`$GPRMC`, `$GPGGA`, `$GPGLL`)
  - **TRK-auto** (`mode=trk-auto` / `land`): custom `$TRK` messages for wheeled vehicles
  - **TRK-container** (`mode=trk-container`): container tracking messages (one per minute by default)

- **Emit channels**: UDP (`--udp HOST:PORT`), MQTT (`--mqtt BROKER:PORT`), or both

- **Update interval**: configure per-track with `interval=<ms>` (default 1000 ms); for `trk-container`, defaults to 60000 ms if not set

- **Inline config tokens**: `velocity`, `interval`, `delay`, `loop`, `repeat`, `mode`, `source`

- **Source types**: define vehicle/container type (e.g., `truck`, `car`, `ship`, `boat`, `tug-boat`)

---

## Installation

```bash
# Python 3.8+ recommended
git clone git@github.com:SherwinArellano/kml-nmea-simulator.git
cd kml-nmea-simulator
pip install -r requirements.txt
```

## Usage

```bash
python kml2nmea.py [KML_PATHS...] \
  [--udp HOST:PORT] [--mqtt BROKER:PORT] [--topic TOPIC] \
  [--nmea-types TYPES] [--nmea-batch-types] \
  [--filegen {single,multi}] [--outdir DIR] [--outfile FILE]
```

- **KML_PATHS**: one or more files or directories containing `.kml`
- `--udp HOST:PORT`   → enable UDP streaming (e.g. `localhost:10110`)
- `--mqtt BROKER:PORT` → enable MQTT streaming (e.g. `broker.local:1883`)
- `--topic TOPIC`   → MQTT topic prefix (default: `kml2nmea`)
- `--nmea-types TYPES` → comma-separated NMEA sentences for sea mode (default: `GPRMC,GPGGA,GPGLL`)
- `--nmea-batch-types` → batch all selected NMEA sentences into one packet per update
- `--filegen single|multi` → generate output files instead of live streaming

  - `single`: one merged file (`--outfile`)
  - `multi` : one file per track (`--outdir`)

> Use the help option to learn more about the program's capabilities: `python kml2nmea.py -h`

**Examples**

- **UDP only** (default when `--udp` is set):

  ```bash
  python kml2nmea.py mymap.kml --udp 127.0.0.1:10110
  socat -u UDP-RECV:10110 STDOUT
  ```

- **MQTT only**:

  ```bash
  python kml2nmea.py mymap.kml --mqtt localhost:1883 --topic my/tracks
  mosquitto_sub -h localhost -t my/tracks/#
  ```

- **Both UDP and MQTT**:

  ```bash
  python kml2nmea.py mymap.kml --udp 127.0.0.1:10110 \
      --mqtt broker.local:1883 --topic my/tracks
  socat -u UDP-RECV:10110 STDOUT &
  mosquitto_sub -h broker.local -t my/tracks/#
  ```

- **Generate files**:

  ```bash
  # Single merged file:
  python kml2nmea.py mymap.kml --filegen single --outfile output.nmea

  # One file per track:
  python kml2nmea.py mymap.kml --filegen multi --outdir tracks/
  ```

---

## Configuration (Inline in KML)

All settings are specified _inline_ in each KML `<Placemark><name>` tag—no external config needed. The `<name>` text begins with the track ID (quoted or unquoted) followed by space‑separated tokens:

```xml
<Placemark>
  <name><![CDATA[
    "Truck 1" velocity=30 interval=500 delay=2000 loop repeat mode=trk-auto source=truck
  ]]></name>
  <LineString>
    <coordinates>
      12.4923,41.8902,0 12.4964,41.9028,0 ...
    </coordinates>
  </LineString>
</Placemark>
```

### Supported Tokens

| Token                                      | Description                                                           | Default              | Notes                      |
| ------------------------------------------ | --------------------------------------------------------------------- | -------------------- | -------------------------- |
| `mode=<nmea \| trk-auto \| trk-container>` | Protocol: `nmea`→NMEA, `trk-auto`→TRK, `trk-container`→container mode | `nmea`               | Selects the message format |
| `velocity=<km/h>`                          | Travel speed in km/h                                                  | `5.0`                |                            |
| `interval=<ms>`                            | Update interval between messages in milliseconds                      | `1000`               |                            |
| `delay=<ms>`                               | Initial delay before streaming in milliseconds                        | `0`                  |                            |
| `loop`                                     | Ping-pong along track (back and forth)                                | off                  |                            |
| `repeat`                                   | Restart upon completion                                               | off                  |                            |
| `source=<type>`                            | Object type (e.g., `truck`, `car`, `ship`, `boat`, `tug-boat`)        | _(required for TRK)_ |                            |
|                                            |

---

## Output Formats

### 1. NMEA (`mode=nmea`)

Emits standard NMEA 0183 sentences. By default, `$GPRMC`, `$GPGGA`, and `$GPGLL` are emitted each update:

```
$GPRMC,143212.00,A,4128.6081,N,01229.7840,E,12.34,0.0,,,*5A
```

- **UDP**: sent to `<host>:<port>`
- **MQTT**: topic `<topic>/nmea/<track_id>`

### 2. TRK-auto (`mode=trk-auto`)

Custom `$TRK` messages for wheeled vehicles:

```
$TRK,<ID>,<YYYYMMDDThhmmssZ>,<lat>,<lon>,<km/h>,<heading>*<checksum>
```

Published over UDP and/or MQTT topic `<topic>/trk-auto/<ID>`.

### 3. TRK-container (`mode=trk-container`)

Per-minute container tracking messages (one update every minute by default). Same `$TRK` format, under `<topic>/trk-container/<ID>`.

---

## Workflow & Integration

1. **Register trip** in your system (e.g., via REST API).
2. **Run simulator**, pointing to KML source: it loads tracks, parses inline configs, and⬇
3. **Stream** live updates or **generate files** based on selected options.

---

## Dependencies

- `geographiclib` – ellipsoidal geodesic calculations
- `paho-mqtt` – MQTT client
- `asyncio` – built-in Python async framework
- `pyee` – event emitter (to be used in the future)

---

## Improvements

### [ ] Event Emitter

Use the event emitter (pyee) to prevent _"prop-drilling"_ `AppConfig` and to decouple classes from other classes. For example, `TrackPlayer` is getting passed `AppConfig` just because it needs the `AppConfig.nmea_types` global configuration.

There are of course other solutions which mitigate this:

1. To create a root parent class which all classes will inherit and has the global configuration. **Problem:** Ties everything to a grand parent class which creates a very coupled system.
2. Use a Singleton. **Problem:** Methods become _unpure_ in the sense that they depend on the outside code.

By using an event emitter, the problems above are solved quite nicely:

```py
@evented # notice this helper from pyee
class TrackPlayer(ABC):
    def __init__(): ...

    @abstractmethod
    async def play(self): ...

    # we can also use decorators for these on_events
    # e.g. @trackPlayer.on_presend()
    def on_presend(self, handler): ...

    def on_finished(self, handler): ...
```

### [ ] Remove AppConfig

As it stands, app config is a god object which I want to avoid after thinking about it. In the sense that it creates this sense of obligation that I have to depend on it too much and pass it anywhere it's needed. Also, there's the overhead of adding a new argument for the cli also means maintaining `AppConfig`. And so I decided in the future to remove it.

As for what will happen to classes that do depend on it, look at the `core.utils.call_context` module for inspiration, also check event emitter, and always think: Single Responsibility Principle, i.e., _does this class really need to be coupled with this other class?_ Think in components, think in composition.
