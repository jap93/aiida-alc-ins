"""Parser for Euphonic phonon modes calculations."""

from __future__ import annotations

import json
from pathlib import Path

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict, SinglefileData
from aiida.orm.nodes.process.process import ProcessNode
from aiida.plugins import CalculationFactory
import yaml

from aiida_alc_ins.parsers.base_parser import BaseParser

DisplacementCalc = CalculationFactory("abinslib.displacements")


class DisplacementParser(BaseParser):
    """Parse outputs from the AiiDA displacement calculation wrapper.

    Parameters
    ----------
    node : ProcessNode
        The AiiDA process node produced by a displacement calcjob.
    """

    def __init__(self, node: ProcessNode):
        """Check that the passed node is produced by a ``DisplacementCalc``."""
        super().__init__(node)

        if not issubclass(node.process_class, DisplacementCalc):
            raise exceptions.ParsingError("Can only parse `DisplacementCalc` calculations")

    def parse(self, **kwargs) -> int:
        """Parse the retrieved displacement output files and publish the parsed results."""
        exit_code = super().parse(**kwargs)
        if exit_code != ExitCode(0):
            return exit_code

        mode_output_filename = self.node.inputs.out_mode_displacements.value
        atomic_output_filename = self.node.inputs.out_atomic_displacements.value

        files_retrieved = self.retrieved.list_object_names()
        files_expected = {mode_output_filename, atomic_output_filename}
        if not files_expected.issubset(files_retrieved):
            self.logger.error(
                f"Found files '{files_retrieved}', expected to find '{files_expected}'"
            )
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        with self.retrieved.open(mode_output_filename, "rb") as handle:
            self.out(
                "mode_displacements", SinglefileData(file=handle, filename=mode_output_filename)
            )

        remote_workdir = Path(self.node.get_remote_workdir())
        mode_path = remote_workdir / mode_output_filename   
        with open(mode_path, encoding="utf-8") as handle:
            content = handle.read()

        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            parsed_content = yaml.safe_load(content)

        results_node = Dict(parsed_content)

        atomic_path = remote_workdir / atomic_output_filename
        with open(atomic_path, encoding="utf-8") as handle:
            content = handle.read()
        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            parsed_content = yaml.safe_load(content)
            
        results_node.update(parsed_content)

        self.out("results_dict", results_node)

        mode_displacements_path = remote_workdir / mode_displacements_output
        try:
            filedata = self.retrieved.base.repository.get_object_content(
                mode_displacements_output, mode="rb"
            )
        except FileNotFoundError:
            return self.exit_codes.ERROR_MISSING_OUTPUT

        mode_displacements_path.write_bytes(filedata)
        self.out("mode_displacements", SinglefileData(file=mode_displacements_path))

        atomic_displacements_path = remote_workdir / atomic_displacements_output
        try:
            filedata = self.retrieved.base.repository.get_object_content(
                atomic_displacements_output, mode="rb"
            )
        except FileNotFoundError:
            return self.exit_codes.ERROR_MISSING_OUTPUT 

        return ExitCode(0)
