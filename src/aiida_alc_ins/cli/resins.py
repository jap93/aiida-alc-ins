"""Command line interface for running ToSCA calculations from AiiDA."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
import json
from collections.abc import Sequence
from typing import Any

import click
import numpy as np

from euphonic import Quantity, QpointPhononModes, Spectrum1DCollection
from resins import Instrument
from abinslib.displacements import Displacements
from abinslib.almost_isotropic_incoherent import (
            calculate_almost_isotropic_incoherent_spectra,
            mantid_like_combination_spectra,
        )
from abinslib.displacements import Displacements
from abinslib.util import calculate_indirect_q2

@click.command(name="aiida-alc-ins-resins")
@click.argument("input_source", type=click.Path(exists=True, dir_okay=False))

@click.option(
    "--out",
    "output_filename",
    default="resins-spectra.json",
    show_default=True,
    help="Name of the output JSON file produced by the ToSCA wrapper.",
)
@click.option(
    "--instrument",
    type=str,
    default="TOSCA",
    show_default=True,
    help="Name of the instrument to use for resolution function.",
)
def cli(
    input_source: str,
    output_filename: str,
    instrument: str
) -> None:
    """Run a ToSCA calculation."""
    config = collect_resins_cli_options(
        {
            "input_source": input_source,
            "output_filename": output_filename,
            "instrument": instrument,
        }
    )
    run_resins_calculation(config)


def build_parser() -> click.Command:
    """Return the Click command used by the ToSCA CLI."""
    return cli


def collect_resins_cli_options(args: dict[str, Any] | Any) -> dict[str, Any]:
    """Convert parsed CLI values into a ToSCA-friendly option dictionary."""
    if hasattr(args, "params"):
        values = args.params
    elif hasattr(args, "to_dict"):
        values = args.to_dict()
    elif isinstance(args, dict):
        values = args
    else:
        values = vars(args)

    input_source = values.get("input_source") or values.get("filename")
    instrument = str(values.get("instrument", "TOSCA"))
    output_filename = values.get("output_filename") or values.get("out", "resins-spectra.json")

    return {
        "input_source": input_source,
        "instrument": instrument,
        "output_filename": output_filename,
    }


def run_resins_calculation(args: dict[str, Any]) -> None:
    """Run a RESINS calculation from CLI arguments."""
    

    input_source = args.get("input_source")
    if input_source is None:
        raise ValueError("The CLI config must include a modes filename.")

    #with open(input_source, "r") as f:
    #    spectra = json.load(f)
    spectra = Spectrum1DCollection.from_json_file(input_source)

    tosca = Instrument.from_default(args.get("instrument", "TOSCA"))
    res = tosca.get_resolution_function("AbINS_v1")

    x = spectra.get_bin_centres().to("meV").magnitude
    spectrum = spectra.sum()
    y = spectrum.y_data.magnitude

    y_broadened = res.broaden(
        # broaden() requires a Nx1 array of input points, so we broadcast a new
        # axis with None; in theory these could be 2D (|Q|,ω) or 4D (q,ω).
        points=x[:, None],
        data=y,
        # In this case the output mesh is the same as the input x-values
        mesh=x,
    )
    spectrum.y_data = Quantity(y_broadened, spectrum.y_data.units)

    spectrum.to_json_file(args.get("output_filename"))

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