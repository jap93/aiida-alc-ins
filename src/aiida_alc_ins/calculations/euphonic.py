"""Class to run Phonon calculations."""

from __future__ import annotations

from aiida.common import datastructures
import aiida.common.folders
from aiida.engine import CalcJobProcessSpec
import aiida.engine.processes
from aiida.orm import Bool, Dict, Float, Int, SinglefileData, Str

from aiida_alc_ins.calculations.base import BaseINS

import numpy as np

import seekpath

import euphonic as eu
import euphonic.util as util
import euphonic.plot as plt



class DOS(BaseINS):
    """
    Calcjob implementation to retrieve force constants and calculate phonon data and include inelastic scattering.

    Attributes
    ----------
    PHONON_OUTPUT : str
        Default phonon output file name.

    Methods
    -------
    define(spec: CalcJobProcessSpec) -> None:
        Define the process specification, its inputs, outputs and exit codes.
    validate_inputs(value: dict, port_namespace: PortNamespace) -> str | None:
        Check if the inputs are valid.
    prepare_for_submission(folder: Folder) -> CalcInfo:
        Create the input files for the `CalcJob`.
    """

    PHONON_OUTPUT = "aiida-phonopy.yml"
    DEFAULT_SUMMARY_FILE = "phonon-summary.yml"

    @classmethod
    def define(cls, spec: CalcJobProcessSpec) -> None:
        """
        Define the process specification, its inputs, outputs and exit codes.

        Parameters
        ----------
        spec : `aiida.engine.CalcJobProcessSpec`
            The calculation job process spec to define.
        """
        super().define(spec)

        # Define inputs
        spec.input(
            "input_source",
            valid_type=Str,
            required=True,
            default=lambda: Str("phonopy_data.yaml"),
            help="The input source for the calculation.",
        )
        spec.input(
            "save_to",
            valid_type=Str,
            required=False,
            default=lambda: Str("matplot_fig.png"),
            help="The file to save the plot to.",
        )
        spec.input(
            "out",
            valid_type=Str,
            required=False,
            default=lambda: Str(cls.PHONON_OUTPUT),
            help="Name of the euphonic output file",
        )

        spec.input(
            "pdos",
            valid_type=Bool,
            required=False,
            help="Calculate the partial density of states",
        )

        spec.input(
            "weighting",
            valid_type=Str,
            required=False,
            default=lambda: Str("dos"),
            help="Type of DOS to plot: DOS, coherent neutron-weighted DOS, incoherent neutron-weighted DOS or total (coherent + incoherent) neutron-weighted DOS",
        )
        spec.input(
            "grid",
            valid_type=Str,
            required=False,
            help="Define Monkhurst grid for DOS calculation, e.g. '10 10 10'",
        )
        spec.input(
            "grid_spacing",
            valid_type=Float,
            required=False,
            default=Float(0.1),
            help="Define q-point spacing for Monkhurst Pack grid'",
        )
        spec.input(
            "length_unit",
            valid_type=Str,
            required=False,
            default=Str("angstrom"),
            help="Length unit for the calculation",
        )
        

        #spec.inputs["metadata"]["options"]["parser_name"].default = "euphonic.dos"

        # Define outputs. The default is a dictionary with the content of the
        # phonon file
        spec.output(
            "results_dict",
            valid_type=Dict,
            help="The `results_dict` output node of the successful calculation.",
        )
        spec.output("phonon_output", valid_type=SinglefileData)
        spec.output("mode_grads", valid_type=SinglefileData)
        spec.output("dos", valid_type=SinglefileData)
        spec.output("pdos", valid_type=SinglefileData)
        spec.output("band_structure", valid_type=SinglefileData)

        spec.default_output_node = "results_dict"

    def prepare_for_submission(
        self, folder: aiida.common.folders.Folder
    ) -> datastructures.CalcInfo:
        """
        Create the input files for the `Calcjob`.

        Parameters
        ----------
        folder : aiida.common.folders.Folder
            Folder where the calculation is run.

        Returns
        -------
        aiida.common.datastructures.CalcInfo
            An instance of `aiida.common.datastructures.CalcInfo`.
        """
        # Call the parent class method to prepare common inputs
        calcinfo = super().prepare_for_submission(folder)
        codeinfo = calcinfo.codes_info[0]

        # filename when recovering the outputs.
        output_filename = (self.inputs.out).value

        codeinfo.cmdline_params = [
            #create the command line to run the program
            self.inputs.input_source.value,
            "--weighting",
            (self.inputs.weighting).value,
            "--save-to",
            (self.inputs.save_to).value, 
        ]

        print(f"final cmdline_params: {codeinfo.cmdline_params}")

        
        calcinfo.retrieve_list.extend(
            [
                output_filename,
                "aiida-dos.dat",
                "aiida-pdos.dat",
                "aiida-auto_bands.yml.xz",
                # "aiida-bands.hdf5",
            ]
        )

        return calcinfo
