"""Base class for features common to most calculations."""

from __future__ import annotations

import shutil

from aiida.common import InputValidationError, datastructures
import aiida.common.folders
from aiida.engine import CalcJob, CalcJobProcessSpec
import aiida.engine.processes
from aiida.orm import Dict, SinglefileData, Str, StructureData
from ase.io import read, write

def validate_inputs(
    inputs: dict, port_namespace: aiida.engine.processes.ports.PortNamespace
):
    """
    Check if the inputs are valid.

    Parameters
    ----------
    inputs : dict
        The inputs dictionary.

    port_namespace : `aiida.engine.processes.ports.PortNamespace`
        An instance of aiida's `PortNamespace`.

    Raises
    ------
    ValueError
        Error message if validation fails, None otherwise.
    
    if "struct" in port_namespace:
        if "struct" not in inputs and "config" not in inputs:
            raise InputValidationError(
                "Either 'struct' or 'config' must be specified in the inputs"
            )
        if (
            "struct" not in inputs
            and "config" in inputs
            and "struct" not in inputs["config"]
        ):
            raise InputValidationError(
                "Structure must be specified through 'struct' or 'config'"
            )
    if (
        "arch" not in inputs
        and "model" not in inputs
        and ("config" not in inputs or "arch" not in inputs["config"])
    ):
        raise InputValidationError(
            "'arch' must be specified in inputs, config file or ModelData"
        )
    """
    pass

class BaseINS(CalcJob):  # numpydoc ignore=PR01
    """
    Calcjob implementation to run single point calculations using mlips.

    Attributes
    ----------
    DEFAULT_OUTPUT_FILE : str
        Default stdout file name.
    DEFAULT_INPUT_FILE : str
        Default input file name.
    DEFAULT_LOG_FILE : str
        Default log file name.
    DEFAULT_SUMMARY_FILE : str
        Default summary file name.

    Methods
    -------
    define(spec: CalcJobProcessSpec) -> None:
        Define the process specification, its inputs, outputs and exit codes.
    validate_inputs(value: dict, port_namespace: PortNamespace) -> str | None:
        Check if the inputs are valid.
    prepare_for_submission(folder: Folder) -> CalcInfo:
        Create the input files for the `CalcJob`.
    """

    DEFAULT_OUTPUT_FILE = "aiida-stdout.txt"
    DEFAULT_INPUT_FILE = "phonopy_data.yaml"
    DEFAULT_LOG_FILE = "aiida.log"
    DEFAULT_SUMMARY_FILE = "aiida-summary.yml"

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
        spec.inputs.validator = validate_inputs
        # Define inputs
        
        
        spec.input(
            "log_filename",
            valid_type=Str,
            required=False,
            default=lambda: Str(cls.DEFAULT_LOG_FILE),
            help="Name of the log output file",
        )
        spec.input(
            "summary",
            valid_type=Str,
            required=False,
            default=lambda: Str(cls.DEFAULT_SUMMARY_FILE),
            help="Name of the summary output file",
        )
        spec.input(
            "metadata.options.output_filename",
            valid_type=str,
            default=cls.DEFAULT_OUTPUT_FILE,
        )
        spec.input(
            "metadata.options.input_filename",
            valid_type=str,
            default=cls.DEFAULT_INPUT_FILE,
        )
        spec.input(
            "metadata.options.scheduler_stdout",
            valid_type=str,
            default="_scheduler-stdout.txt",
            help="Filename to which the content of stdout of the scheduler is written.",
        )

        spec.input(
            "calc_kwargs",
            valid_type=Dict,
            required=False,
            help="Keyword arguments to pass to selected calculator.",
        )


        spec.output("std_output", valid_type=SinglefileData)
        spec.output("log_output", valid_type=SinglefileData)
        # Exit codes
        spec.exit_code(
            305,
            "ERROR_MISSING_OUTPUT_FILES",
            message="Some output files missing or cannot be read",
        )

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
        
        # Transform the structure data in xyz file called input_filename
        input_filename = self.inputs.metadata.options.input_filename
        phonopy_data = {}
        import yaml
        with open(input_filename, 'r') as file:
            phonopy_data = yaml.safe_load(file)
        
        with folder.open(input_filename, mode="w") as file:
            yaml.dump(phonopy_data, file)

        log_filename = self.inputs.log_filename.value
        summary = self.inputs.summary.value

        
        codeinfo = datastructures.CodeInfo()

        # Initialize cmdline_params with a placeholder "calculation" command
        #cmd_line = {}
        #    "struct": input_filename,
        #    "log": log_filename,
        #    "summary": summary,
        #}
        #codeinfo.cmdline_params = ["calculation", cmd_line]  #self.dict_to_cmdline_param(cmd_line)]

        # Node where the code is saved
        codeinfo.code_uuid = self.inputs.code.uuid
        # Save name of output as you need it for running the code
        codeinfo.stdout_name = self.metadata.options.output_filename
        

        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        # Save the info about the node where the calc is stored
        calcinfo.uuid = str(self.uuid)
        # Retrieve output files
        calcinfo.retrieve_list = [
            self.metadata.options.output_filename,
            self.uuid,
            log_filename,
            summary,
        ]
        
        return calcinfo

    def dict_to_cmdline_param(self, params: dict[str, Any]) -> list[str]:
        """
        Convert a dictionary of kwargs to a set of commandline flags.

        Bools are converted as though ``store_true`` flag keys.
    
        Parameters
        ----------
        params : dict[str, Any]
            Dictionary of arguments to convert.

        Returns
        -------
        list[str]
            Commandline arguments as flags.
        """
        cmdline_params = []

        for key, val in params.items():
            key = key.replace("_", "-")
            match val:
                case bool() if val:
                    cmdline_params.append(f"--{key}")
                case bool():
                    cmdline_params.append(f"--no-{key}")
                case _:
                    cmdline_params.extend((f"--{key}", str(val)))
        """
        for key, val in params.items():
            key = key.replace("_", "-")
            print(f"key: {key}, val: {val}")
            if key == "input-source":
                # Special case for input_source, which is a positional argument
                cmdline_params.append(str(val))
                print("source input is: ", str(val))
            else:
                match val:
                    case bool() if val:
                        cmdline_params.append(f"--{key}")
                    case bool():
                         cmdline_params.append(f"--no-{key}")
                    case _:
                        cmdline_params.extend((f"--{key}", str(val)))

        print(f"cmdline_params: {cmdline_params}")
        """
        print(f"cmdline_params: {cmdline_params}")

        return cmdline_params


