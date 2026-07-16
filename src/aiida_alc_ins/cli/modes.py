"""Command line interface for running Euphonic DOS calculations from AiiDA."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import click
import json

import numpy as np

from euphonic import ForceConstants, util



@click.command(name="aiida-alc-ins-euphonic")
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--out",
    default="aiida-modes.yml",
    show_default=True,
    help="Name of the output file produced by the AiiDA wrapper.",
)
@click.option(
    "--save-to",
    default="matplot_fig.png",
    show_default=True,
    help="Destination for any generated plot image.",
)
@click.option(
    "--weighting",
    type=str,
    default=None,
    help="Type of weighted phonon output to calculate.",
)
@click.option(
    "--grid",
    nargs=3,
    type=int,
    default=None,
    help="Monkhorst-Pack grid as three integers.",
)
@click.option(
    "--grid-spacing",
    type=float,
    default=0.1,
    show_default=True,
    help="Grid spacing for the Monkhorst-Pack mesh.",
)
@click.option(
    "--length-unit",
    type=str,
    default="angstrom",
    show_default=True,
    help="Length unit for the calculation.",
)
@click.option(
    "--pdos/--no-pdos",
    default=False,
    help="Calculate the partial density of states.",
)
@click.option(
    "--adaptive/--no-adaptive",
    default=False,
    help="Enable adaptive sampling for the calculation.",
)
def cli(
    filename: str,
    out: str,
    save_to: str,
    weighting: str | None,
    grid: tuple[int, int, int] | None,
    grid_spacing: float,
    length_unit: str,
    pdos: bool,
    adaptive: bool,
) -> None:
    """Run an Euphonic calculation."""
    config = collect_aiida_cli_options(
        {
            "filename": filename,
            "out": out,
            "save_to": save_to,
            "weighting": weighting,
            "grid": grid,
            "grid_spacing": grid_spacing,
            "length_unit": length_unit,
            "pdos": pdos,
            "adaptive": adaptive,
        }
    )
    run_euphonic_phonon_calculation(config)


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
    out = values.get("out", "aiida-modes.json")
    weighting = values.get("weighting")
    save_to = values.get("save_to", "matplot_fig.png")
    grid = values.get("grid")
    grid_spacing = values.get("grid_spacing", 0.1)
    length_unit = values.get("length_unit", "angstrom")
    pdos = bool(values.get("pdos", False))
    adaptive = bool(values.get("adaptive", False))

    euphonic_args = [str(filename)]

    if weighting is not None:
        euphonic_args.extend(["--weighting", str(weighting)])
    if grid is not None:
        euphonic_args.extend(["--grid", *[str(item) for item in grid]])
    if grid_spacing != 0.1:
        euphonic_args.extend(["--grid-spacing", str(grid_spacing)])
    if length_unit != "angstrom":
        euphonic_args.extend(["--length-unit", length_unit])
    if save_to != "matplot_fig.png":
        euphonic_args.extend(["--save-to", save_to])
    if pdos:
        euphonic_args.append("--pdos")
    if adaptive:
        euphonic_args.append("--adaptive")

    return {
        "filename": filename,
        "output_filename": out,
        "save_to": save_to,
        "weighting": weighting,
        "grid": grid,
        "grid_spacing": grid_spacing,
        "length_unit": length_unit,
        "pdos": pdos,
        "adaptive": adaptive,
        "euphonic_args": euphonic_args,
    }
    
def run_euphonic_phonon_calculation(args: dict[str, Any]) -> None:
    """Run an Euphonic phonon calculation from CLI arguments."""
    filename = args.get("filename")
    if filename is None:
        raise ValueError("The CLI config must include a filename.")

    fc = ForceConstants.from_phonopy(summary_name=filename)
    modes, mode_grads = fc.calculate_qpoint_phonon_modes(
        util.mp_grid([5, 5, 5]), return_mode_gradients=True
    )

    output_file = args.get("output_filename", "aiida-phonons.json")
    modes.to_json_file(output_file)

    mode_grad_file = args.get("mode_grads_output", "aiida-mode_grads.json")
    with open(mode_grad_file, "w", encoding="utf-8") as handle:
        json.dump({"quantity": str(mode_grads)}, handle, indent=4)

    
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
