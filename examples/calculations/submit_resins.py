"""Example code for submitting Euphonic phonon modes calculations."""

from __future__ import annotations

from typing import Any
import pathlib
from pathlib import Path

from aiida.common import NotExistent
from aiida.engine import run_get_node
from aiida.orm import Float, Str, load_code
from aiida.plugins import CalculationFactory
from euphonic import Spectrum1DCollection
import click
import json


def resins_experiment(params: dict[str, Any]) -> None:
    """Prepare inputs and run a phonon modes calculation.

    Parameters
    ----------
    params : dict[str, Any]
        A dictionary containing the input parameters for the calculation.
    """
    resins_calc = CalculationFactory("abinslib.resins")

    inputs = {
        "metadata": {"options": {"resources": {"num_machines": 1}}},
        "code": params["code"],
        "input_source": Str(params["input_source"]),
        "out": Str(params["out"]),
        "instrument": Str(params["instrument"]),
    }

    print(f"inputs for calculation: {inputs}")

    result, node = run_get_node(resins_calc, **inputs)
    print(f"Node of calculation: {node}")
    print("use verdi calcjob gotocomputer <pk> for a shell in the work directory")
    print("Results dictionary:")
    print(result.keys())

    #only uncomment if you want lots of data printed to the screen
    #print(result["results_dict"].get_dict())

    remote_folder = result["remote_folder"]
    spectra_path = Path(remote_folder.get_remote_path()) / params["out"]
    spectra = Spectrum1DCollection.from_json_file(spectra_path)

    spectra.to_json_file(params["out"])
        
    print(f"remote folder {result['remote_folder']} {node.get_remote_workdir()} ")
    print(f"retrieved {result['retrieved']}  ")


@click.command("cli")
@click.argument("codelabel", type=str)
@click.argument("input_source", type=str)
@click.option(
    "--out",
    default="resins-spectrum.json",
    type=str,
    help="Name of the generated Euphonic phonon modes output file.",
)

@click.option(
    "--instrument",
    default="TOSCA",
    type=str,
    help="Instrument resolution.",
)

def cli(
    codelabel: str,
    input_source: str,
    out: str,
    instrument: str,
    
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
        "instrument": instrument,
    }

    print(f"Parameters for calculation: {params}")
    resins_experiment(params)


if __name__ == "__main__":
    cli()
    print("normal exit to the code")
