from __future__ import annotations

from click.testing import CliRunner


def test_modes_collects_expected_cli_config():
    from aiida_alc_ins.cli.modes import collect_aiida_cli_options

    config = collect_aiida_cli_options(
        {
            "filename": "phonopy_data.yaml",
            "out": "aiida.yml",
            "grid": (2, 3, 4),
            "grid_spacing": 0.2,
            "length_unit": "angstrom",
        }
    )

    assert config["filename"] == "phonopy_data.yaml"
    assert config["output_filename"] == "aiida.yml"
    assert config["grid"] == (2, 3, 4)
    assert config["grid_spacing"] == 0.2
    assert config["length_unit"] == "angstrom"
    assert config["euphonic_args"] == [
        "phonopy_data.yaml",
        "--grid",
        "2",
        "3",
        "4",
        "--grid-spacing",
        "0.2",
    ]


def test_modes_command_invokes_backend_with_parsed_options(tmp_path, monkeypatch):
    from aiida_alc_ins.cli import modes as modes_cli

    input_file = tmp_path / "phonopy_data.yaml"
    input_file.write_text("phonopy:\n")

    captured: dict[str, object] = {}

    def fake_run(args):
        captured.update(args)

    monkeypatch.setattr(modes_cli, "run_euphonic_phonon_calculation", fake_run)

    result = CliRunner().invoke(
        modes_cli.build_parser(),
        [
            str(input_file),
            "--out",
            "mode-output.json",
            "--grid",
            "2",
            "3",
            "4",
            "--grid-spacing",
            "0.25",
            "--length-unit",
            "bohr",
        ],
    )

    assert result.exit_code == 0
    assert captured["filename"] == str(input_file)
    assert captured["output_filename"] == "mode-output.json"
    assert captured["grid"] == (2, 3, 4)
    assert captured["grid_spacing"] == 0.25
    assert captured["length_unit"] == "bohr"


def test_displacement_collects_expected_cli_config():
    from aiida_alc_ins.cli.displacement_cli import collect_aiida_cli_options

    config = collect_aiida_cli_options(
        {
            "filename": "phonon_modes.json",
            "out_mode_displacements": "mode-displacements.json",
            "out_atomic_displacements": "atomic-displacements.json",
            "temperature": 60.0,
        }
    )

    assert config["filename"] == "phonon_modes.json"
    assert config["mode_displacements_output"] == "mode-displacements.json"
    assert config["atomic_displacements_output"] == "atomic-displacements.json"
    assert config["temperature"] == 60.0
    assert config["euphonic_args"] == ["phonon_modes.json", "--temperature", "60.0"]


def test_displacement_command_invokes_backend_with_parsed_options(tmp_path, monkeypatch):
    from aiida_alc_ins.cli import displacement_cli

    input_file = tmp_path / "phonon_modes.json"
    input_file.write_text("{}")

    captured: dict[str, object] = {}

    def fake_run(args):
        captured.update(args)

    monkeypatch.setattr(displacement_cli, "run_displacement_calculation", fake_run)

    result = CliRunner().invoke(
        displacement_cli.build_parser(),
        [
            str(input_file),
            "--out_mode_displacements",
            "mode-displacements.json",
            "--out_atomic_displacements",
            "atomic-displacements.json",
            "--temperature",
            "75.0",
        ],
    )

    assert result.exit_code == 0
    assert captured["filename"] == str(input_file)
    assert captured["mode_displacements_output"] == "mode-displacements.json"
    assert captured["atomic_displacements_output"] == "atomic-displacements.json"
    assert captured["temperature"] == 75.0


def test_resins_collects_expected_cli_config():
    from aiida_alc_ins.cli.resins import collect_resins_cli_options

    config = collect_resins_cli_options(
        {
            "input_source": "resins-spectrum.json",
            "output_filename": "broadened.json",
            "instrument": "TOSCA",
        }
    )

    assert config["input_source"] == "resins-spectrum.json"
    assert config["output_filename"] == "broadened.json"
    assert config["instrument"] == "TOSCA"


def test_resins_command_invokes_backend_with_parsed_options(tmp_path, monkeypatch):
    from aiida_alc_ins.cli import resins as resins_cli

    input_file = tmp_path / "resins-spectrum.json"
    input_file.write_text("{}")

    captured: dict[str, object] = {}

    def fake_run(args):
        captured.update(args)

    monkeypatch.setattr(resins_cli, "run_resins_calculation", fake_run)

    result = CliRunner().invoke(
        resins_cli.build_parser(),
        [
            str(input_file),
            "--out",
            "resins-output.json",
            "--instrument",
            "TOSCA",
        ],
    )

    assert result.exit_code == 0
    assert captured["input_source"] == str(input_file)
    assert captured["output_filename"] == "resins-output.json"
    assert captured["instrument"] == "TOSCA"


def test_tosca_collects_expected_cli_config():
    from aiida_alc_ins.cli.tosca import collect_tosca_cli_options

    config = collect_tosca_cli_options(
        {
            "modes_filename": "tosca-spectrum.json",
            "temperature": 80.0,
            "output_filename": "tosca-output.json",
        }
    )

    assert config["modes_filename"] == "tosca-spectrum.json"
    assert config["temperature"] == 80.0
    assert config["output_filename"] == "tosca-output.json"


def test_tosca_command_invokes_backend_with_parsed_options(tmp_path, monkeypatch):
    from aiida_alc_ins.cli import tosca as tosca_cli

    input_file = tmp_path / "tosca-spectrum.json"
    input_file.write_text("{}")

    captured: dict[str, object] = {}

    def fake_run(args):
        captured.update(args)

    monkeypatch.setattr(tosca_cli, "run_tosca_calculation", fake_run)

    result = CliRunner().invoke(
        tosca_cli.build_parser(),
        [
            str(input_file),
            "--temperature",
            "90.0",
            "--out",
            "tosca-output.json",
        ],
    )

    assert result.exit_code == 0
    assert captured["modes_filename"] == str(input_file)
    assert captured["temperature"] == 90.0
    assert captured["output_filename"] == "tosca-output.json"
