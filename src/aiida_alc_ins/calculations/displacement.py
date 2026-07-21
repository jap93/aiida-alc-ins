"""AiiDA wrapper for Euphonic q-point phonon mode calculations."""

from __future__ import annotations

from aiida.common import datastructures
import aiida.common.folders
from aiida.engine import CalcJobProcessSpec
import aiida.engine.processes
from aiida.orm import Dict, Float, SinglefileData, Str

from aiida_alc_ins.calculations.base import BaseINS
import json

class Displacements(BaseINS):
    """CalcJob implementation for generating phonon modes from force constants.

    This wrapper mirrors the CLI workflow exposed by
    ``aiida_alc_ins.cli.modes`` and stores the generated mode data and mode
    gradients as retrievable AiiDA outputs.
    """

    DEFAULT_INPUT_FILE = "phonon_modes.json"
    MODE_DISPLACEMENTS_OUTPUT = "aiida-mode-displacements.json"
    ATOMIC_DISPLACEMENTS_OUTPUT = "aiida-atomic-displacements.json"

    @classmethod
    def define(cls, spec: CalcJobProcessSpec) -> None:
        """Define the process specification for the phonon modes calcjob."""
        super().define(spec)

        spec.input(
            "input_source",
            valid_type=Str,
            required=True,
            default=lambda: Str("phonon_modes.json"),
            help="The phonon modes file to use as the calculation input.",
        )
        spec.input(
            "out_mode_displacements",
            valid_type=Str,
            required=False,
            default=lambda: Str(cls.MODE_DISPLACEMENTS_OUTPUT),
            help="Name of the generated mode displacements output file.",
        )
        spec.input(
            "out_atomic_displacements",
            valid_type=Str,
            required=False,
            default=lambda: Str(cls.ATOMIC_DISPLACEMENTS_OUTPUT),
            help="Name of the generated atomic displacements output file.",
        )

        spec.input(
            "temperature",
            valid_type=Float,
            required=False,
            default=Float(50.0),
            help="Temperature for the phonon calculations.",
        )

        spec.inputs["metadata"]["options"]["parser_name"].default = "abinslib.displacement_parser"


        spec.output(
            "results_dict",
            valid_type=Dict,
            help="The parsed results dictionary produced by the calculation.",
        )
        spec.output("mode_displacements_output", valid_type=SinglefileData)
        spec.output("atomic_displacements_output", valid_type=SinglefileData)

        spec.default_output_node = "results_dict"

    def prepare_for_submission(
        self, folder: aiida.common.folders.Folder
    ) -> datastructures.CalcInfo:
        """Create the input files and command-line arguments for the calcjob."""
        calcinfo = super().prepare_for_submission(folder)
        codeinfo = calcinfo.codes_info[0]

        mode_output_filename = self.inputs.out_mode_displacements.value
        atomic_output_filename = self.inputs.out_atomic_displacements.value    

        cmdline_params = [self.inputs.input_source.value]

        if self.inputs.temperature.value != 50.0:
            cmdline_params.extend(["--temperature", str(self.inputs.temperature.value)])    

        cmdline_params.extend(["--out_mode_displacements", mode_output_filename])
        cmdline_params.extend(["--out_atomic_displacements", atomic_output_filename])
        codeinfo.cmdline_params = cmdline_params

        calcinfo.retrieve_list.extend([mode_output_filename, atomic_output_filename])

        input_filename = self.inputs.metadata.options.input_filename
        mode_data = {}
        
        with open(input_filename, 'r') as file:
            mode_data = json.load(file)
        
        with folder.open(input_filename, mode="w") as file:
            json.dump(mode_data, file)

        return calcinfo
