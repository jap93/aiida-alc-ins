"""Command line interface for running Euphonic DOS calculations from AiiDA."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import click
import json

import numpy as np

from euphonic import util
from euphonic import Quantity, QpointPhononModes
from abinslib.displacements import Displacements


@click.command(name="aiida-alc-ins-euphonic")
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--out_mode_displacements",
    default="aiida-mode-displacements.json",
    show_default=True,
    help="Name of the output file produced by the AiiDA wrapper.",
)

@click.option(
    "--out_atomic_displacements",
    default="aiida-atomic-displacements.json",
    show_default=True,
    help="Name of the output file produced by the AiiDA wrapper.",
)
@click.option(
    "--temperature",
    type=float,
    default=50.0,
    show_default=True,
    help="Temperature for the phonon calculations.",
)

def cli(
    filename: str,
    out_mode_displacements: str,
    out_atomic_displacements: str,
    temperature: float,
) -> None:
    """Run an calculation of mode and atomic displacements."""
    
    config = collect_aiida_cli_options(
        {
            "filename": filename,
            "out_mode_displacements": out_mode_displacements,
            "out_atomic_displacements": out_atomic_displacements,
            "temperature": temperature,
            
        }
    )
    run_displacement_calculation(config)


def build_parser() -> click.Command:
    """Return the Click command used by the CLI."""
    return cli


def collect_aiida_cli_options(
    args: dict[str, Any] | Any, parser: Any | None = None
) -> dict[str, Any]:
    """Convert parsed CLI values into an AiiDA-friendly option dictionary."""
    if hasattr(args, "params"):
        values = args.params
    elif hasattr(args, "to_dict"):
        values = args.to_dict()
    elif isinstance(args, dict):
        values = args
    else:
        values = vars(args)

    filename = values.get("filename")
    out_mode_displacements = values.get("out_mode_displacements", "aiida-modes.json")
    out_atomic_displacements = values.get("out_atomic_displacements", "aiida-atomic-displacements.json")
    temperature = values.get("temperature", 50.0)
    

    euphonic_args = [str(filename)]
    
    if temperature != 50.0:
        euphonic_args.extend(["--temperature", str(temperature)])

    return {
        "filename": filename,
        "mode_displacements_output": out_mode_displacements,
        "atomic_displacements_output": out_atomic_displacements,
        "temperature": temperature,
        "euphonic_args": euphonic_args,
    }
    
def run_displacement_calculation(args: dict[str, Any]) -> None:
    """calculate atomic and mode displacements from CLI arguments."""
    filename = args.get("filename")
    if filename is None:
        raise ValueError("The CLI config must include a filename.")

    temperature = Quantity(float(args.get("temperature", 50.0)), "kelvin")

    modes = QpointPhononModes.from_json_file(filename)

    mode_displacements = Displacements.from_modes(modes, temperature=temperature)
    atomic_displacements = mode_displacements.to_atomic_displacements()

    output_file = args.get("mode_displacements_output", "mode_displacement.json")
    with open(output_file, 'w') as f:
        json.dump(mode_displacements, f, indent=4)

    atomic_displacement_file = args.get("atomic_displacements_output", "atomic_displacements.json")
    with open(atomic_displacement_file, 'w') as f:
        json.dump(atomic_displacements, f, indent=4)
    
def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI options and forward them to the Euphonic entry point."""
    parser = build_parser()
    if argv is None:
        parser.main(standalone_mode=False)
        return 0

    from click.testing import CliRunner

    result = CliRunner().invoke(parser, list(argv))
    if result.exception is not None:
        raise result.exception
    return int(result.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
