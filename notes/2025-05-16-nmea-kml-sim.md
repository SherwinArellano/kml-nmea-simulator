# NMEA KML Simulator

_May 16, 2025_

## Introduction

NMEA is a standard used for communication betwen marine electronic devices. One of which is the NMEA 0183 protocol which is mainly used for communicating navigation data. The objective of this project is to create a simple but powerful simulator of NMEA tracks.

For generating NMEA tracks, we can use the website [nmeagen.org](https://nmeagen.org/).

I have already created a little script which reads different NMEA files in Python and outputs them through a UDP socket. And each file can be configured through a `.yaml` file:

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

Which is then run through the Python script simulator:

```bash
python3 nmea_simulator.py <sim-config-file> <host> <port>
python3 nmea_simulator.py sim.yaml 127.0.0.1 6000
```

And to listen, we can use `socat` on the specified UDP port:

```bash
socat -u UDP-RECV:<port> STDOUT
socat -u UDP-RECV:6000 STDOUT
```

**This, however, even though the potential is there has quite a few problems:**

- [nmeagen.org](https://nmeagen.org/) only supports creating one track at a time.
- [nmeagen.org](https://nmeagen.org/) is also laggy when it comes to creating a very long track with lots of points.

> What is a "point"? A point, in terms of the [nmeagen.org](https://nmeagen.org/) website, is a point in time and space on the map. It's basically the location at a specific time.

- Third, even though the simulator can output these NMEA files, the problem is handling time. It would be very difficult to create multiple NMEA files and then keeping track of when the NMEA tracks start in time.

Thanks to our colleague, Leandro, who introduced us [Google My Maps](https://www.google.com/mymaps), we can use it to create multiple tracks and tracks in land can also be actual tracks! Actual tracks in the sense that they're navigating on real roads.

## Objective

To create multiple tracks in [Google My Maps](https://www.google.com/mymaps), save them in a `.kml` file which is then passed through a simulator which converts them to NMEA outputs.

## Idea Log 1

There are two types of tracks: a line track and a navigation track.

A line track is created by a line while a navigation track is a created through routes of navigation.

Since ships don't really have "routes" and Google My Maps obviously didn't account for it, we will use line tracks for them. Land vehicles, however, can use both line tracks and navigation tracks.

To simulate ships, we can create lines in Google My Maps and inside the generated `.kml` we find:

```xml
<Folder>
  <name>Ship</name>
  <Placemark>
    <name>Line 1</name>
    <styleUrl>#line-000000-1200-nodesc</styleUrl>
    <LineString>
      <tessellate>1</tessellate>
      <coordinates>
        8.9140163,44.4122675,0
        8.9230857,44.3992097,0
        8.9625804,44.3562165,0
        9.0706994,44.3127456,0
        ...
      </coordinates>
    </LineString>
  </Placemark>
</Folder>
```

As you can see, we can use the `<coordinates>` to build a NMEA track.

But how can we generate these tracks?

The initial problem would be how can we configure a track? Like its velocity, its loop (reaching its destination will traverse it back to its original), etc.

I thought that we can use something akin to terminal's parameter options, for example, in Google My Maps, we can specify that the name of the layer or line is:

```bash
"Truck 1" velocity=5 delay=5000 loop=true
```

Where:

- `"Truck 1"` is the name of the track.
- `velocity=5` specifies the velocity of the track.
- `delay=5000` specified when the track should start.
- `loop=true` if we want the track to navigate back to its initial position.

A navigation track can only have one path and therefore this configuration is set to its whole layer in Google My Maps, while with line tracks, we can set this configuration in its line itself.
