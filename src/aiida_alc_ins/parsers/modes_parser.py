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

ModesCalc = CalculationFactory("euphonic.modes")


class ModesParser(BaseParser):
    """Parse outputs from the AiiDA phonon modes calculation wrapper.

    Parameters
    ----------
    node : ProcessNode
        The AiiDA process node produced by a ``euphonic.modes`` calcjob.
    """

    def __init__(self, node: ProcessNode):
        """Check that the passed node is produced by a ``ModesCalc``."""
        super().__init__(node)

        if not issubclass(node.process_class, ModesCalc):
            raise exceptions.ParsingError("Can only parse `ModesCalc` calculations")

    def parse(self, **kwargs) -> int:
        """Parse the retrieved mode output files and publish the parsed results."""
        exit_code = super().parse(**kwargs)
        if exit_code != ExitCode(0):
            return exit_code

        phonon_output = self.node.inputs.out.value
        mode_grads_output = "aiida-mode_grads.json"

        files_retrieved = self.retrieved.list_object_names()
        files_expected = {phonon_output, mode_grads_output}
        if not files_expected.issubset(files_retrieved):
            self.logger.error(
                f"Found files '{files_retrieved}', expected to find '{files_expected}'"
            )
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        with self.retrieved.open(phonon_output, "rb") as handle:
            self.out(
                "phonon_output", SinglefileData(file=handle, filename=phonon_output)
            )

        remote_workdir = Path(self.node.get_remote_workdir())
        phonon_path = remote_workdir / phonon_output
        with open(phonon_path, encoding="utf-8") as handle:
            content = handle.read()

        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            parsed_content = yaml.safe_load(content)

        results_node = Dict(parsed_content)
        self.out("results_dict", results_node)

        mode_grads_path = remote_workdir / mode_grads_output
        try:
            filedata = self.retrieved.base.repository.get_object_content(
                mode_grads_output, mode="rb"
            )
        except FileNotFoundError:
            self.logger.error("exception in getting mode gradient filepath")
            return self.exit_codes.ERROR_MISSING_OUTPUT

        mode_grads_path.write_bytes(filedata)
        self.out("mode_grads", SinglefileData(file=mode_grads_path))

        return ExitCode(0)
