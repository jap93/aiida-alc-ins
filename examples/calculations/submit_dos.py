"""Example code for submitting phonon calculation."""

from __future__ import annotations

import json
from pathlib import Path

from aiida.common import NotExistent
from aiida.engine import run_get_node
from aiida.orm import Bool, Float, Str, load_code
from aiida.plugins import CalculationFactory
import click
import h5py
import yaml



def density_of_states(params: dict[str, any]) -> None:
    """
    Prepare inputs and run a DOS calculation.

    Parameters
    ----------
    params : dict
        A dictionary containing the input parameters for the calculations.

    Returns
    -------
        None
    """

    # Select calculation to use
    dos_calc = CalculationFactory("euphonic.dos")

    # Define inputs
    inputs = {
        "metadata": {"options": {"resources": {"num_machines": 1}}},
        "code": params["code"],
        "input_source": Str(params["input_source"]),
        "out": Str(params["out"]),
        "pdos": Bool(params["pdos"]),
        "weighting": Str(params["weighting"]),
        "grid_spacing": Float(params["grid_spacing"]),
        "length_unit": Str(params["length_unit"]),
    }

    if params.get("grid"):
        inputs["grid"] = Str(params["grid"])

    print(f"inputs for calculation: {inputs} ")
    

    #############################################################
    #  Run calculation
    #############################################################
    result, node = run_get_node(dos_calc, **inputs)
    print(f"Node of calculation: {node} ")
    print(f"use verdi calcjob gotocomputer {node.pk} for a shell in the work directory")

    # start processing the results
    print("Results dictionary: ")
    print(result.keys())

    


# Arguments and options to give to the cli when running the script
@click.command("cli")
@click.argument("codelabel", type=str)
@click.argument("input_source", type=str)

@click.option(
    "--out",
    default="aiida-phonopy.yml",
    type=str,
    help="Name of the euphonic output file.",
)

@click.option("--pdos", is_flag=True, help="Calculate the partial density of states.")
@click.option(
    "--weighting",
    default="dos",
    type=str,
    help="Type of DOS to plot: DOS, coherent neutron-weighted DOS, incoherent neutron-weighted DOS or total (coherent + incoherent) neutron-weighted DOS.",
)
@click.option(
    "--grid",
    default="",
    type=str,
    help="Define Monkhurst grid for DOS calculation, e.g. '10 10 10'.",
)
@click.option(
    "--grid-spacing",
    default=0.1,
    type=float,
    help="Define q-point spacing for Monkhurst Pack grid.",
)
@click.option(
    "--length-unit",
    default="angstrom",
    type=str,
    help="Length unit for the calculation.",
)
def cli(
    codelabel,
    input_source,
    out,
    pdos,
    weighting,
    grid,
    grid_spacing,
    length_unit,
) -> None:
    """Click interface."""

    try:
        code = load_code(codelabel)
    except NotExistent as exc:
        print(f"The code '{codelabel}' does not exist.")
        raise SystemExit from exc

    params = {
        "code": code,
        "input_source": input_source,
        "out": out,
        "pdos": pdos,
        "weighting": weighting,
        "grid_spacing": grid_spacing,
        "length_unit": length_unit,
    }

    if len(grid) > 0:
        params["grid"] = grid

    print(f"Parameters for calculation: {params} ")
    # Submit DOS calculation
    density_of_states(params)


if __name__ == "__main__":
    cli()

    print("normal exit to the code")
