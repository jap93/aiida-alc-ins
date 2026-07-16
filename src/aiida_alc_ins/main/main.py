"""Compatibility entrypoint for the plugin CLI helpers."""

from __future__ import annotations

from aiida_alc_ins.cli.modes import build_parser, collect_aiida_cli_options

__all__ = ["build_parser", "collect_aiida_cli_options"]
