"""Example code for submitting Euphonic phonon modes calculations."""

from __future__ import annotations
import pathlib
from pathlib import Path

from typing import Any

from aiida.common import NotExistent
from aiida.engine import run_get_node
from aiida.orm import Float, Str, load_code
from aiida.plugins import CalculationFactory
from euphonic import Spectrum1DCollection
import click
import json


def tosca_experiment(params: dict[str, Any]) -> None:
    """Prepare inputs and run a phonon modes calculation.

    Parameters
    ----------
    params : dict[str, Any]
        A dictionary containing the input parameters for the calculation.
    """
    tosca_calc = CalculationFactory("abinslib.tosca")

    inputs = {
        "metadata": {"options": {"resources": {"num_machines": 1}}},
        "code": params["code"],
        "modes_filename": Str(params["modes_filename"]),
        "out": Str(params["out"]),
        "temperature": Float(params["temperature"]),
    }

    print(f"inputs for calculation: {inputs}")

    result, node = run_get_node(tosca_calc, **inputs)
    print(f"Node of calculation: {node}")
    print("use verdi calcjob gotocomputer <pk> for a shell in the work directory")
    print("Results dictionary:")
    print(result.keys())

    #only uncomment below if you want lots of information printed to the screen
    #print(result["results_dict"].get_dict())

    print(f"remote folder {result['remote_folder']} {node.get_remote_workdir()} ")
    print(f"retrieved {result['retrieved']}  ")

    remote_folder = result["remote_folder"]
    spectra_path = Path(remote_folder.get_remote_path()) / params["out"]
    spectra = Spectrum1DCollection.from_json_file(spectra_path)

    spectra.to_json_file(params["out"])
    

@click.command("cli")
@click.argument("codelabel", type=str)
@click.argument("modes_filename", type=str)
@click.option(
    "--out",
    default="tosca-spectrum.json",
    type=str,
    help="Name of the generated Euphonic phonon modes output file.",
)

@click.option(
    "--temperature",
    default=0.1,
    type=float,
    help="Simulation temperature in kelvin.",
)

def cli(
    codelabel: str,
    modes_filename: str,
    out: str,
    temperature: float,
    
) -> None:
    """Click interface for submitting a phonon modes calculation."""
    try:
        code = load_code(codelabel)
    except NotExistent as exc:
        print(f"The code '{codelabel}' does not exist.")
        raise SystemExit from exc

    params: dict[str, Any] = {
        "code": code,
        "modes_filename": modes_filename,
        "out": out,
        "temperature": temperature,
    }

    print(f"Parameters for calculation: {params}")
    tosca_experiment(params)


if __name__ == "__main__":
    cli()
    print("normal exit to the code")
