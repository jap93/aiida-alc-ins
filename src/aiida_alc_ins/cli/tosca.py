"""Command line interface for running ToSCA calculations from AiiDA."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
import json
from collections.abc import Sequence
from typing import Any

import click
import numpy as np

from euphonic import Quantity, QpointPhononModes
from abinslib.displacements import Displacements
from abinslib.almost_isotropic_incoherent import (
            calculate_almost_isotropic_incoherent_spectra,
            mantid_like_combination_spectra,
        )
from abinslib.displacements import Displacements
from abinslib.util import calculate_indirect_q2

@click.command(name="aiida-alc-ins-tosca")
@click.argument("modes_filename", type=click.Path(exists=True, dir_okay=False))

@click.option(
    "--temperature",
    type=float,
    default=50.0,
    show_default=True,
    help="Simulation temperature in kelvin.",
)
@click.option(
    "--out",
    "output_filename",
    default="tosca-spectra.json",
    show_default=True,
    help="Name of the output JSON file produced by the ToSCA wrapper.",
)
def cli(
    modes_filename: str,
    temperature: float,
    output_filename: str,
) -> None:
    """Run a ToSCA calculation."""
    config = collect_tosca_cli_options(
        {
            "modes_filename": modes_filename,
            "temperature": temperature,
            "output_filename": output_filename,
        }
    )
    run_tosca_calculation(config)


def build_parser() -> click.Command:
    """Return the Click command used by the ToSCA CLI."""
    return cli


def collect_tosca_cli_options(args: dict[str, Any] | Any) -> dict[str, Any]:
    """Convert parsed CLI values into a ToSCA-friendly option dictionary."""
    if hasattr(args, "params"):
        values = args.params
    elif hasattr(args, "to_dict"):
        values = args.to_dict()
    elif isinstance(args, dict):
        values = args
    else:
        values = vars(args)

    modes_filename = values.get("modes_filename") or values.get("filename")
    temperature = float(values.get("temperature", 50.0))
    output_filename = values.get("output_filename") or values.get("out", "tosca-spectra.json")

    return {
        "modes_filename": modes_filename,
        "temperature": temperature,
        "output_filename": output_filename,
    }


def run_tosca_calculation(args: dict[str, Any]) -> None:
    """Run a ToSCA calculation from CLI arguments."""
    

    modes_filename = args.get("modes_filename")
    if modes_filename is None:
        raise ValueError("The CLI config must include a modes filename.")

    modes = QpointPhononModes.from_json_file(modes_filename)

    temperature = Quantity(float(args.get("temperature", 50.0)), "kelvin")
    
    mode_displacements = Displacements.from_modes(modes, temperature=temperature)
    atomic_displacements = mode_displacements.to_atomic_displacements()

    tosca_backward_q2 = calculate_indirect_q2(
        modes.frequencies,
        angle=(135 * np.pi / 180),
        final_energy=Quantity(32.0, "cm^-1").to("hartree"),
    )

    bins = Quantity(np.linspace(0, 2000, 201), "cm^-1")
    bin_centres = (bins[1:] + bins[:-1]) * 0.5
    
    binned_q2 = calculate_indirect_q2(
        bin_centres,
        angle=(135 * np.pi / 180),
        final_energy=Quantity(32.0, "cm^-1").to("hartree"),
    )

    fundamentals = calculate_almost_isotropic_incoherent_spectra(
        modes=modes,
        mode_displacements=mode_displacements,
        atomic_displacements=atomic_displacements,
        nominal_q2=tosca_backward_q2,
        bins=bins,
        apply_cross_section=True,
    )

    second_order = mantid_like_combination_spectra(
        modes,
        mode_displacements,
        atomic_displacements,
        binned_q2,
        bins,
        apply_cross_section=True,
    )

    spectra = fundamentals + second_order

    spectra.to_json_file(args.get("output_filename", "tosca-spectra.json"))

def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI options and forward them to the ToSCA entry point."""
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