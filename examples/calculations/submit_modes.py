"""Example code for submitting Euphonic phonon modes calculations."""

from __future__ import annotations

from typing import Any

from aiida.common import NotExistent
from aiida.engine import run_get_node
from aiida.orm import Float, Str, load_code
from aiida.plugins import CalculationFactory
import click


def phonon_modes(params: dict[str, Any]) -> None:
    """Prepare inputs and run a phonon modes calculation.

    Parameters
    ----------
    params : dict[str, Any]
        A dictionary containing the input parameters for the calculation.
    """
    modes_calc = CalculationFactory("euphonic.modes")

    inputs = {
        "metadata": {"options": {"resources": {"num_machines": 1}}},
        "code": params["code"],
        "input_source": Str(params["input_source"]),
        "out": Str(params["out"]),
        "grid_spacing": Float(params["grid_spacing"]),
        "length_unit": Str(params["length_unit"]),
    }

    if params.get("save_to"):
        inputs["save_to"] = Str(params["save_to"])

    if params.get("grid"):
        inputs["grid"] = Str(params["grid"])

    print(f"inputs for calculation: {inputs}")

    result, node = run_get_node(modes_calc, **inputs)
    print(f"Node of calculation: {node}")
    print("use verdi calcjob gotocomputer <pk> for a shell in the work directory")
    print("Results dictionary:")
    print(result.keys())


@click.command("cli")
@click.argument("codelabel", type=str)
@click.argument("input_source", type=str)
@click.option(
    "--out",
    default="aiida-modes.yml",
    type=str,
    help="Name of the generated Euphonic phonon modes output file.",
)
@click.option(
    "--save-to",
    default="matplot_fig.png",
    type=str,
    help="Destination for any generated plot image.",
)
@click.option(
    "--grid",
    default="",
    type=str,
    help="Monkhorst-Pack grid for modes calculation, e.g. '5 5 5'.",
)
@click.option(
    "--grid-spacing",
    default=0.1,
    type=float,
    help="Q-point spacing for Monkhorst-Pack sampling.",
)
@click.option(
    "--length-unit",
    default="angstrom",
    type=str,
    help="Length unit used by the calculation.",
)
def cli(
    codelabel: str,
    input_source: str,
    out: str,
    save_to: str,
    grid: str,
    grid_spacing: float,
    length_unit: str,
) -> None:
    """Click interface for submitting a phonon modes calculation."""
    try:
        code = load_code(codelabel)
    except NotExistent as exc:
        print(f"The code '{codelabel}' does not exist.")
        raise SystemExit from exc

    params: dict[str, Any] = {
        "code": code,
        "input_source": input_source,
        "out": out,
        "save_to": save_to,
        "grid": grid,
        "grid_spacing": grid_spacing,
        "length_unit": length_unit,
    }

    print(f"Parameters for calculation: {params}")
    phonon_modes(params)


if __name__ == "__main__":
    cli()
    print("normal exit to the code")
