# NMEA Simulator

## Running

To run the simulator:

```bash
python3 nmea_simulator.py <sim-config-file> <host> <port>
python3 nmea_simulator.py sim.yaml 127.0.0.1 6000
```

To listen, we can use `socat` on the specified UDP port:

```bash
socat -u UDP-RECV:<port> STDOUT
socat -u UDP-RECV:6000 STDOUT
```

## Simulation Config File

The simulation config file is written in `yaml` and has the following structure:

```yaml
<nmea filename (without .nmea)>:
  start: <int milliseconds>
  interval: <int milliseconds>
  repeat: <boolean>
  mirror: <boolean>
  filter:
    - gprmc
    - <other nmea type string>
```
