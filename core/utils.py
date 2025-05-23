def parse_host_port(hostname: str) -> tuple[str, int]:
    host, port = hostname.split(":")
    return (host, int(port))
