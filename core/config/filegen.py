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


def build_filegen_cfg(cli: Args, yaml_cfg: dict[str, Any]) -> FilegenConfig | None:
    filegen_cfg = None

    if "filegen_mode" in cli:
        filegen_cfg = FilegenConfig(
            True, cli.filegen_stream, cli.filegen_mode, cli.outfile, cli.outdir
        )
    elif len(yaml_cfg):
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

        filegen_cfg = FilegenConfig(
            yaml_cfg.get("enabled", False),
            yaml_cfg.get("streaming", False),
            mode,
            outfile,
            outdir,
        )

    return filegen_cfg
