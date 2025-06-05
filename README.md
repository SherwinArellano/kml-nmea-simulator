# Generalized Track Simulator

A real‑time track simulator that streams simulated movement of one or more objects based on KML sources (e.g., Google My Maps). Depending on provided options, it produces asynchronous output over UDP, MQTT, or both, **or** generates timestamped output files, with the following customizable parameters:

- **Track modes**:

  - **NMEA** (`mode=nmea` / `sea`): standard NMEA 0183 sentences (`$GPRMC`, `$GPGGA`, `$GPGLL`)
  - **TRK-truck** (`mode=trk-truck` / `land`): custom `$TRK` messages for wheeled vehicles
  - **TRK-container** (`mode=trk-container`): container tracking messages (one per minute by default)

- **Emit channels**: UDP (`--udp HOST:PORT`), MQTT (`--mqtt BROKER:PORT`), or both

- **Update interval**: configure per-track with `interval=<ms>` (default 1000 ms); for `trk-container`, defaults to 60000 ms if not set

- **Inline config tokens**: `velocity`, `interval`, `delay`, `loop`, `repeat`, `mode`, `source`

- **Source types**: define vehicle/container type (e.g., `truck`, `car`, `ship`, `boat`, `tug-boat`)

## Table of Contents

- [Generalized Track Simulator](#generalized-track-simulator)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Listen](#listen)
  - [Configuration (Inline in KML)](#configuration-inline-in-kml)
    - [Supported Tokens](#supported-tokens)
  - [Output Formats](#output-formats)
    - [1. NMEA (`mode=nmea`)](#1-nmea-modenmea)
    - [2. TRK-truck (`mode=trk-truck`)](#2-trk-truck-modetrk-truck)
    - [3. TRK-container (`mode=trk-container`)](#3-trk-container-modetrk-container)
  - [Adding New CLI / YAML and KML Options](#adding-new-cliyaml-and-kml-options)
    - [CLI / YAML Options](#cliyaml-options)
    - [KML Options](#kml-options)


## Installation

```bash
# Python 3.8+ recommended

# Clone the repo and change directory there
git clone git@github.com:SherwinArellano/kml-nmea-simulator.git
cd kml-nmea-simulator

# Create a virtual environment
python -m venv venv # depending on what you're using, `python` could be `py` or `python3`

# Activate virtual environment
source venv/bin/activate # LINUX
.\venv\Scripts\Activate.ps1 # WINDOWS

# Install packages
pip install -r requirements.txt

# Use sample kml files
python migrate.py
```

## Usage

```bash
python main.py
```

**IMPORTANT:** Check the help section on how to use the program by running:

```bash
python main.py -h
```

Do note that the program checks the `config.yaml` for running configurations.

## Listen

To listen in UDP, you can do so with `socat` (you may have to install):

```bash
socat -u UDP-RECV:10110 STDOUT
```

To listen in MQTT:

```bash
mosquitto_sub -h localhost -t <topic>/#
```

> Where `<topic>` is set in `config.yaml` or given through CLI's `--topic`.

## Configuration (Inline in KML)

All settings are specified _inline_ in each KML `<Placemark><name>` tag—no external config needed. The `<name>` text begins with the track ID (quoted or unquoted) followed by space‑separated tokens:

```xml
<Placemark>
  <name><![CDATA[TR742-1 velocity=30 interval=500 delay=2000 loop repeat mode=trk-truck source=truck id-port=001 dest-port=A01]]></name>
  <LineString>
    <coordinates>
      12.4923,41.8902,0 12.4964,41.9028,0 ...
    </coordinates>
  </LineString>
</Placemark>
```

### Supported Tokens

| Token                                       | Description                                                            | Default              | Notes                                                    |
| ------------------------------------------- | ---------------------------------------------------------------------- | -------------------- | -------------------------------------------------------- |
| `mode=<nmea \| trk-truck \| trk-container>` | Protocol: `nmea`→NMEA, `trk-truck`→TRK, `trk-container`→container mode | `nmea`               | Selects the message format                               |
| `velocity=<km/h>`                           | Travel speed in km/h                                                   | `5.0`                |                                                          |
| `interval=<ms>`                             | Update interval between messages in milliseconds                       | `1000`               |                                                          |
| `delay=<ms>`                                | Initial delay before streaming in milliseconds                         | `0`                  |                                                          |
| `loop`                                      | Ping-pong along track (back and forth)                                 | off                  |                                                          |
| `repeat`                                    | Restart upon completion                                                | off                  |                                                          |
| `source=<type>`                             | Object type (e.g., `truck`, `car`, `ship`, `boat`, `tug-boat`)         | _(required for TRK)_ |                                                          |
| `id-port=<code>`                            | Starting code port (format: 3 digits, e.g., `001`)                     | `001`                | Can be set manually; otherwise defaults to `001`         |
| `dest-port=<code>`                          | Destination port code (format: 1 letter + 2 digits, e.g., `A01`)       | `A01`                | Can be set manually; otherwise defaults to `A01`         |
| `prov=<code or name>`                       | Province code or name (e.g., `GE` or `Genova`)                         | _(auto-detect)_      | Auto-detected from track `<name>` or can be set manually |
| `comune=<code or name>`                     | Municipality (comune) code or name (e.g., `D969` or `Genova`)          | _(auto-detect)_      | Auto-detected from track `<name>` or can be set manually |

## Output Formats

### 1. NMEA (`mode=nmea`)

Emits standard NMEA 0183 sentences. By default, `$GPRMC`, `$GPGGA`, and `$GPGLL` are emitted each update:

```
$GPRMC,143212.00,A,4128.6081,N,01229.7840,E,12.34,0.0,,,*5A
```

- **UDP**: sent to `<host>:<port>`
- **MQTT**: topic `<topic>/nmea/<port-id>`

### 2. TRK-truck (`mode=trk-truck`)

Custom `$TRK` messages for wheeled vehicles:

```
$TRK,<ID>,<YYYYMMDDThhmmssZ>,<lat>,<lon>,<km/h>,<heading>*<checksum>
```

Published over UDP and/or MQTT topic `<topic>/trk-truck/<port-id>`.

### 3. TRK-container (`mode=trk-container`)

Per-minute container tracking messages (one update every minute by default). Same `$TRK` format, under `<topic>/trk-container/<port-id>`.

## Adding New CLI / YAML and KML Options

### CLI / YAML Options

**Configuration Priority:**

1. **CLI arguments** → **YAML file** → **Defaults**

2. **Edit `config.yaml`**

- Under the relevant top-level section (e.g. `udp`, `mqtt`, `rest`), add your new key with a default and an `enabled: true/false` flag if needed.

3. **Edit `config/cli.py`**

- In the `Args` (or equivalent) class, add a new `parser.add_argument` entry whose name matches the YAML key (e.g. `--rest-timeout` for `rest.timeout`).

4. **Edit `config/app.py`**

- Add the field to the appropriate dataclass (or create a new `XXXConfig` module and export it via `config/__init__.py`).
- In `AppConfig` (or the main builder), merge CLI → YAML → default by checking:

  - If CLI flag is provided, use it.
  - Else, if YAML block exists (and `enabled: true` or a value is set), use YAML.
  - Otherwise, fall back to the hard-coded default.

### KML Options

1. **Edit `core/models/track_info.py`**

- Add a new attribute to `TrackCfg` (or equivalent) with a sensible default (e.g. `alert_level: Optional[str] = None`).

2. **Edit `code/parser.py`**

- In the section that splits `<name>` into tokens, add logic so that when it sees your token (e.g. `alert-level=<value>` or a standalone flag), it assigns to the new `TrackCfg` field.

3. **(Optional) Adjust Downstream Behavior**

- If your new KML field should alter message formatting or simulator behavior, update the relevant formatter/emitter to check that field.

4. **Test with Sample KML**

- Create a `<Placemark>` containing the new token in `<name>`, run the simulator, and verify that the field is populated and, if applicable, that any behavior tied to it works as expected.
