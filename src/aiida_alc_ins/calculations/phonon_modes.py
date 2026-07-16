"""AiiDA wrapper for Euphonic q-point phonon mode calculations."""

from __future__ import annotations

from aiida.common import datastructures
import aiida.common.folders
from aiida.engine import CalcJobProcessSpec
import aiida.engine.processes
from aiida.orm import Dict, Float, SinglefileData, Str

from aiida_alc_ins.calculations.base import BaseINS


class Modes(BaseINS):
    """CalcJob implementation for generating phonon modes from force constants.

    This wrapper mirrors the CLI workflow exposed by
    ``aiida_alc_ins.cli.modes`` and stores the generated mode data and mode
    gradients as retrievable AiiDA outputs.
    """

    PHONON_OUTPUT = "aiida-modes.yml"
    DEFAULT_SUMMARY_FILE = "phonon-summary.yml"
    DEFAULT_MODE_GRADS_FILE = "aiida-mode_grads.json"

    @classmethod
    def define(cls, spec: CalcJobProcessSpec) -> None:
        """Define the process specification for the phonon modes calcjob."""
        super().define(spec)

        spec.input(
            "input_source",
            valid_type=Str,
            required=True,
            default=lambda: Str("phonopy_data.yaml"),
            help="The phonopy summary file to use as the calculation input.",
        )
        spec.input(
            "out",
            valid_type=Str,
            required=False,
            default=lambda: Str(cls.PHONON_OUTPUT),
            help="Name of the generated phonon modes output file.",
        )
        spec.input(
            "save_to",
            valid_type=Str,
            required=False,
            default=lambda: Str("matplot_fig.png"),
            help="Destination for any generated plot image.",
        )
        spec.input(
            "grid",
            valid_type=Str,
            required=False,
            help="Monkhorst-Pack grid as a string of three integers, e.g. '5 5 5'.",
        )
        spec.input(
            "grid_spacing",
            valid_type=Float,
            required=False,
            default=Float(0.1),
            help="Q-point spacing used for Monkhorst-Pack sampling.",
        )
        spec.input(
            "length_unit",
            valid_type=Str,
            required=False,
            default=lambda: Str("angstrom"),
            help="Length unit used by the underlying calculation.",
        )

        spec.output(
            "results_dict",
            valid_type=Dict,
            help="The parsed results dictionary produced by the calculation.",
        )
        spec.output("phonon_output", valid_type=SinglefileData)
        spec.output("mode_grads", valid_type=SinglefileData)

        spec.default_output_node = "results_dict"

    def prepare_for_submission(
        self, folder: aiida.common.folders.Folder
    ) -> datastructures.CalcInfo:
        """Create the input files and command-line arguments for the calcjob."""
        calcinfo = super().prepare_for_submission(folder)
        codeinfo = calcinfo.codes_info[0]

        output_filename = self.inputs.out.value
        mode_grads_output = self.DEFAULT_MODE_GRADS_FILE

        cmdline_params = [self.inputs.input_source.value]

        if self.inputs.grid:
            cmdline_params.extend(["--grid", *self.inputs.grid.value.split()])

        if self.inputs.grid_spacing.value != 0.1:
            cmdline_params.extend(["--grid-spacing", str(self.inputs.grid_spacing.value)])

        if self.inputs.length_unit.value != "angstrom":
            cmdline_params.extend(["--length-unit", self.inputs.length_unit.value])

        if self.inputs.save_to.value != "matplot_fig.png":
            cmdline_params.extend(["--save-to", self.inputs.save_to.value])

        cmdline_params.extend(["--out", output_filename])
        codeinfo.cmdline_params = cmdline_params

        calcinfo.retrieve_list.extend([output_filename, mode_grads_output])

        return calcinfo
