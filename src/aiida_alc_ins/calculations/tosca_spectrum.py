"""AiiDA wrapper for Euphonic q-point phonon mode calculations."""

from __future__ import annotations
import json
import pathlib
from pathlib import Path

from aiida.common import datastructures
import aiida.common.folders
from aiida.engine import CalcJobProcessSpec
import aiida.engine.processes
from aiida.orm import Dict, Float, SinglefileData, Str

from aiida_alc_ins.calculations.base import BaseINS


class Tosca(BaseINS):
    """CalcJob implementation for generating phonon modes from force constants.

    This wrapper mirrors the CLI workflow exposed by
    ``aiida_alc_ins.cli.modes`` and stores the generated mode data and mode
    gradients as retrievable AiiDA outputs.
    """

    DEFAULT_INPUT_FILE = "phonon_modes.json"
    TOSCA_OUTPUT = "tosca-spectra.json"
    DEFAULT_SUMMARY_FILE = "phonon-summary.yml"


    @classmethod
    def define(cls, spec: CalcJobProcessSpec) -> None:
        """Define the process specification for the phonon modes calcjob."""
        super().define(spec)

        spec.input(
            "modes_filename",
            valid_type=Str,
            required=True,
            default=lambda: Str("phonon_modes.json"),
            help="The phonopy summary file to use as the calculation input.",
        )
        spec.input(
            "out",
            valid_type=Str,
            required=False,
            default=lambda: Str(cls.TOSCA_OUTPUT),
            help="Name of the generated ToSCA spectra output file.",
        )        
        spec.input(
            "temperature",
            valid_type=Float,
            required=False,
            default=lambda: Float(50.0),
            help="Simulation temperature in kelvin.",
        )
        spec.inputs["metadata"]["options"]["parser_name"].default = "abinslib.tosca_parser"


        spec.output(
            "results_dict",
            valid_type=Dict,
            help="The parsed results dictionary produced by the calculation.",
        )
        spec.output("tosca_output", valid_type=SinglefileData)

        spec.default_output_node = "results_dict"

    def prepare_for_submission(
        self, folder: aiida.common.folders.Folder
    ) -> datastructures.CalcInfo:
        """Create the input files and command-line arguments for the calcjob."""
        calcinfo = super().prepare_for_submission(folder)
        codeinfo = calcinfo.codes_info[0]

        output_filename = self.inputs.out.value

        cmdline_params = [self.inputs.modes_filename.value]

        if self.inputs.temperature.value != 50.0:
            cmdline_params.extend(["--temperature", str(self.inputs.temperature.value)])

        cmdline_params.extend(["--out", output_filename])
        codeinfo.cmdline_params = cmdline_params

        calcinfo.retrieve_list.extend([output_filename])

        input_filename = self.inputs.metadata.options.input_filename
        mode_data = {}
        
        with open(input_filename, 'r') as file:
            mode_data = json.load(file)
        
        with folder.open(input_filename, mode="w", encoding="utf-8") as file:
            json.dump(mode_data, file, indent=4)

        return calcinfo
