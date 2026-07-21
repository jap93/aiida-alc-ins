"""Parser for Euphonic phonon modes calculations."""

from __future__ import annotations

import json
from pathlib import Path

from aiida.common import exceptions
from aiida.engine import ExitCode
from aiida.orm import Dict, SinglefileData
from aiida.orm.nodes.process.process import ProcessNode
from aiida.plugins import CalculationFactory

from euphonic import Spectrum1DCollection

from aiida_alc_ins.parsers.base_parser import BaseParser

ToscaCalc = CalculationFactory("abinslib.tosca")
    

class ToscaParser(BaseParser):
    """Parse outputs from the AiiDA phonon modes calculation wrapper.

    Parameters
    ----------
    node : ProcessNode
        The AiiDA process node produced by a ``euphonic.tosca`` calcjob.
    """

    def __init__(self, node: ProcessNode):
        """Check that the passed node is produced by a ``ToscaCalc``."""
        super().__init__(node)

        if not issubclass(node.process_class, ToscaCalc):
            raise exceptions.ParsingError("Can only parse `ToscaCalc` calculations")

    def parse(self, **kwargs) -> int:
        """Parse the retrieved mode output files and publish the parsed results."""
        exit_code = super().parse(**kwargs)
        if exit_code != ExitCode(0):
            return exit_code

        spectra_output = self.node.inputs.out.value

        print(f"*************spectra_output: {spectra_output}*************")

        files_retrieved = self.retrieved.list_object_names()
        files_expected = {spectra_output}
        if not files_expected.issubset(files_retrieved):
            self.logger.error(
                f"Found files '{files_retrieved}', expected to find '{files_expected}'"
            )
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        remote_workdir = Path(self.node.get_remote_workdir())
        spectrum_path = remote_workdir / spectra_output
        
        content = Spectrum1DCollection.from_json_file(spectrum_path).to_dict()

        results_node = Dict(content)
        self.out("results_dict", results_node)

        return ExitCode(0)
