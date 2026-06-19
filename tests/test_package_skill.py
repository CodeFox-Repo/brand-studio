from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "package_skill.py"


def load_package_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("marketing_harness_package_skill", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def zip_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        return archive.namelist()


def test_package_skill_excludes_heavy_examples_by_default(
    tmp_path: Path, monkeypatch
) -> None:
    module = load_package_script()
    output = tmp_path / "skill.zip"
    monkeypatch.setattr(sys, "argv", ["package_skill.py", str(output)])

    assert module.main() == 0

    names = zip_names(output)
    assert "SKILL.md" in names
    assert not any(name.startswith("examples/") for name in names)
    assert not any(name.startswith("src/") for name in names)
    assert not any(name.startswith("tests/") for name in names)


def test_package_skill_can_include_examples_when_requested(
    tmp_path: Path, monkeypatch
) -> None:
    module = load_package_script()
    output = tmp_path / "skill-with-examples.zip"
    monkeypatch.setattr(
        sys,
        "argv",
        ["package_skill.py", str(output), "--include-examples"],
    )

    assert module.main() == 0

    names = zip_names(output)
    assert any(name.startswith("examples/") for name in names)
    assert not any(name.startswith("src/") for name in names)
    assert not any(name.startswith("tests/") for name in names)


def test_package_skill_rejects_src_inside_skill_payload(
    tmp_path: Path, monkeypatch
) -> None:
    module = load_package_script()
    output = tmp_path / "skill.zip"
    invalid_dir = ROOT / "skills" / "marketing-harness" / "src"
    invalid_dir.mkdir()
    try:
        monkeypatch.setattr(sys, "argv", ["package_skill.py", str(output)])

        with pytest.raises(SystemExit, match="Invalid skill payload top-level entries: src"):
            module.main()
    finally:
        invalid_dir.rmdir()
