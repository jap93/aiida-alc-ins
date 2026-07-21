"""Example code for submitting Euphonic phonon modes calculations."""

from __future__ import annotations

from typing import Any

from aiida.common import NotExistent
from aiida.engine import run_get_node
from aiida.orm import Float, Str, load_code
from aiida.plugins import CalculationFactory
import click


def phonon_displacements(params: dict[str, Any]) -> None:
    """Prepare inputs and run a phonon displacements calculation.

    Parameters
    ----------
    params : dict[str, Any]
        A dictionary containing the input parameters for the calculation.
    """
    modes_calc = CalculationFactory("abinslib.displacements")

    inputs = {
        "metadata": {"options": {"resources": {"num_machines": 1}}},
        "code": params["code"],
        "input_source": Str(params["input_source"]),
        "out_mode_displacements": Str(params["out_mode_displacements"]),
        "out_atomic_displacements": Str(params["out_atomic_displacements"]),
        "temperature": Float(params["temperature"]),
    }

    print(f"inputs for calculation: {inputs}")

    result, node = run_get_node(modes_calc, **inputs)
    print(f"Node of calculation: {node}")
    print("use verdi calcjob gotocomputer <pk> for a shell in the work directory")
    print("Results dictionary:")
    print(result.keys())

    print(result["results_dict"].get_dict())
    #write phonon modes to a json file
    with open("phonon_modes.json", "w") as f:
        f.write(result["phonon_output"].get_content())
        
    print(f"remote folder {result['remote_folder']} {node.get_remote_workdir()} ")
    print(f"retrieved {result['retrieved']}  ")


@click.command("cli")
@click.argument("codelabel", type=str)
@click.argument("input_source", type=str)
@click.option(
    "--out_mode_displacements",
    default="aiida-mode-displacements.json",
    type=str,
    help="Name of the generated Euphonic phonon modes output file.",
)
@click.option(
    "--out_atomic_displacements",
    default="aiida-atomic-displacements.json",
    type=str,
    help="Name of the generated Euphonic atomic displacements output file.",
)
@click.option(
    "--temperature",
    default=50.0,
    type=float,
    help="Temperature for the phonon calculations.",
)

def cli(
    codelabel: str,
    input_source: str,
    out_mode_displacements: str,
    out_atomic_displacements: str,
    temperature: float,
) -> None:
    """Click interface for submitting calculation of atomic and mode displacements."""
    try:
        code = load_code(codelabel)
    except NotExistent as exc:
        print(f"The code '{codelabel}' does not exist.")
        raise SystemExit from exc

    params: dict[str, Any] = {
        "code": code,
        "input_source": input_source,
        "out_mode_displacements": out_mode_displacements,
        "out_atomic_displacements": out_atomic_displacements,
        "temperature": temperature,
    }

    print(f"Parameters for calculation: {params}")
    phonon_displacements(params)


if __name__ == "__main__":
    cli()
    print("normal exit to the code")
