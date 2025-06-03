from .common import FilegenMode
from .cli import Args
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FilegenConfig:
    enabled: bool
    streaming: bool
    mode: FilegenMode
    outfile: str | None
    outdir: str | None


def parse_filegen_yaml(yaml_cfg: dict[str, Any]) -> FilegenConfig:
    mode: FilegenMode | None = yaml_cfg.get("mode")
    if not mode:
        raise KeyError("Missing required 'mode' in filegen section of YAML config")
    if mode not in ("single", "multi"):
        raise KeyError(
            f"Mode '{mode}' in filegen section of YAML config is invalid or not supported (supported: 'single' or 'multi')"
        )

    outfile = yaml_cfg.get("outfile")
    if mode == "single" and not outfile:
        raise KeyError(
            "Missing required 'outfile' in 'single' mode of filegen section of YAML config"
        )

    outdir = yaml_cfg.get("outdir")
    if mode == "multi" and not outdir:
        raise KeyError(
            "Missing required 'outdir' in 'multi' mode of filegen section of YAML config"
        )

    return FilegenConfig(
        yaml_cfg.get("enabled", False),
        yaml_cfg.get("streaming", False),
        mode,
        outfile,
        outdir,
    )


def build_filegen_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> FilegenConfig | None:
    filegen_cfg = parse_filegen_yaml(yaml_cfg) if len(yaml_cfg) else None

    if "filegen_mode" in cli:
        if not cli.filegen_mode and filegen_cfg:
            # enable yaml config if exists
            filegen_cfg = FilegenConfig(
                True,
                filegen_cfg.streaming,
                filegen_cfg.mode,
                filegen_cfg.outfile,
                filegen_cfg.outdir,
            )
        elif cli.filegen_mode:
            # use provided argument or defaults (which is set in config/cli.py)
            filegen_cfg = FilegenConfig(
                True, cli.filegen_stream, cli.filegen_mode, cli.outfile, cli.outdir
            )
        else:
            raise ValueError(
                "Provided '--filegen' option but missing YAML config or not specified a filegen mode."
            )

    return filegen_cfg
