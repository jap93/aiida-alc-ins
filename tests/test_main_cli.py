from aiida_alc_ins.calculations.phonon_modes import Modes
from aiida_alc_ins.main.main import build_parser, collect_aiida_cli_options


def test_build_parser_returns_click_command():
    parser = build_parser()

    assert parser.name == "aiida-alc-ins-euphonic"


def test_collect_aiida_cli_options_includes_euphonic_flags():
    config = collect_aiida_cli_options(
        {
            "filename": "phonopy_data.yaml",
            "out": "aiida.yml",
            "weighting": "coherent",
            "save_to": "plot.png",
            "grid": (2, 3, 4),
            "grid_spacing": 0.2,
            "length_unit": "angstrom",
            "pdos": True,
            "adaptive": False,
        }
    )

    assert config["filename"] == "phonopy_data.yaml"
    assert config["output_filename"] == "aiida.yml"
    assert config["euphonic_args"] == [
        "phonopy_data.yaml",
        "--weighting",
        "coherent",
        "--grid",
        "2",
        "3",
        "4",
        "--grid-spacing",
        "0.2",
        "--save-to",
        "plot.png",
        "--pdos",
    ]


def test_modes_wrapper_exposes_expected_defaults():
    assert Modes.PHONON_OUTPUT == "aiida-modes.yml"
    assert Modes.DEFAULT_SUMMARY_FILE == "phonon-summary.yml"
