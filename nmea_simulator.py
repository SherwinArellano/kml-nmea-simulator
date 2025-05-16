#!/usr/bin/env python3
import argparse
import asyncio
import socket
import yaml
import os

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

async def play_stream(name, cfg, host, port, sock):
    # wait until start offset
    await asyncio.sleep(cfg.get('start', 0) / 1000)

    # read and filter lines
    filename = f"{name}.nmea"
    if not os.path.isfile(filename):
        print(f"[Warning] File not found: {filename}")
        return

    with open(filename, 'r', encoding='utf-8') as f:
        raw = [line.rstrip('') for line in f if line.strip()]

    # apply filter keywords (case-insensitive substring match)
    filters = [kw.lower() for kw in cfg.get('filter', [])]
    if filters:
        lines = [ln for ln in raw if any(kw in ln.lower() for kw in filters)]
    else:
        lines = raw

    # apply mirror option
    if cfg.get('mirror', False):
        lines = lines + list(reversed(lines))

    if not lines:
        print(f"[Info] No lines to send for stream '{name}'")
        return

    interval_s = cfg.get('interval', 1000) / 1000  # ms → s
    repeat = cfg.get('repeat', False)

    # send loop
    while True:
        for line in lines:
            sock.sendto(line.encode('utf-8'), (host, port))
            await asyncio.sleep(interval_s)
        if not repeat:
            break

async def main():
    parser = argparse.ArgumentParser(
        description="Simulate multiple .nmea streams over UDP using a YAML config"
    )
    parser.add_argument("config", help="YAML simulator config file")
    parser.add_argument("host", help="UDP destination host")
    parser.add_argument("port", type=int, help="UDP destination port")
    args = parser.parse_args()

    cfg = load_config(args.config)

    # prepare a non-blocking UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # launch one task per stream
    tasks = []
    for name, stream_cfg in cfg.items():
        tasks.append(
            asyncio.create_task(
                play_stream(name, stream_cfg, args.host, args.port, sock)
            )
        )

    if tasks:
        await asyncio.gather(*tasks)
    else:
        print("No streams defined in config.")

if __name__ == "__main__":
    asyncio.run(main())
