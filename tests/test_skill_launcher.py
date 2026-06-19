from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "skills" / "marketing-harness" / "scripts" / "harness.py"


def load_launcher() -> ModuleType:
    spec = importlib.util.spec_from_file_location("marketing_harness_skill_launcher", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metadata(root: Path) -> dict[str, object]:
    return {
        "project": {
            "root": str(root),
            "marketingRoot": "packages/branding/marketing",
        },
        "brand": {
            "lock": "packages/branding/marketing/brand.lock.yaml",
            "campaigns": "packages/branding/marketing/campaigns",
            "references": "packages/branding/marketing/references",
        },
        "campaign": {
            "name": "launch",
            "path": "packages/branding/marketing/campaigns/launch.campaign.yaml",
        },
        "artifacts": {
            "scratch": "packages/branding/.harness/out",
            "approved": "packages/branding/public/marketing",
        },
        "policy": {
            "allowRemoteRuntimeFallback": False,
        },
    }


def test_metadata_supplies_validate_and_render_paths(tmp_path: Path) -> None:
    launcher = load_launcher()
    meta = metadata(tmp_path)

    validate_args = launcher.apply_metadata_args(["validate"], meta)
    render_args = launcher.apply_metadata_args(["render", "--dry-run"], meta)

    campaign = str(tmp_path / "packages/branding/marketing/campaigns/launch.campaign.yaml")
    brand = str(tmp_path / "packages/branding/marketing/brand.lock.yaml")
    outputs = str(tmp_path / "packages/branding/.harness/out")
    assert validate_args == ["validate", campaign, "--brand", brand]
    assert render_args == [
        "render",
        campaign,
        "--dry-run",
        "--brand",
        brand,
        "--outputs-dir",
        outputs,
    ]


def test_metadata_defaults_publish_to_repo_channel(tmp_path: Path) -> None:
    launcher = load_launcher()

    publish_args = launcher.apply_metadata_args(["publish"], metadata(tmp_path))

    assert publish_args == [
        "publish",
        "launch",
        "--outputs-dir",
        str(tmp_path / "packages/branding/.harness/out"),
        "--channel",
        "repo",
        "--repo-dir",
        str(tmp_path / "packages/branding/public/marketing"),
    ]


def test_metadata_project_paths_are_root_relative(tmp_path: Path) -> None:
    launcher = load_launcher()

    paths = launcher.project_paths(metadata(tmp_path), tmp_path)

    assert paths["marketing_root"] == tmp_path / "packages/branding/marketing"
    assert paths["campaigns_dir"] == tmp_path / "packages/branding/marketing/campaigns"
    assert paths["references_dir"] == tmp_path / "packages/branding/marketing/references"


def test_remote_runtime_fallback_is_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = load_launcher()
    fake_uvx = tmp_path / "uvx"
    fake_uvx.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_uvx.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.delenv("HARNESS_PROJECT_DIR", raising=False)
    monkeypatch.delenv("HARNESS_ALLOW_DEV_ANCESTOR", raising=False)
    monkeypatch.delenv("HARNESS_ALLOW_REMOTE_RUNTIME", raising=False)

    with pytest.raises(SystemExit, match="explicitly allow remote runtime fallback"):
        launcher.resolve_harness_command({})

    assert launcher.resolve_harness_command(
        {"policy": {"allowRemoteRuntimeFallback": True}}
    ) == [
        str(fake_uvx),
        "--from",
        "git+https://github.com/CodeFox-Repo/marketing-harness",
        "harness",
    ]


def test_bootstrap_is_dry_run_until_write(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    launcher = load_launcher()
    meta = metadata(tmp_path)
    marketing_root = tmp_path / "packages/branding/public/marketing"
    scratch = tmp_path / "packages/branding/.harness/out"

    assert launcher.bootstrap_project([str(tmp_path)], meta, "marketing.harness.yaml") == 0
    assert not marketing_root.exists()
    assert not scratch.exists()
    assert "mode=dry-run" in capsys.readouterr().out

    assert (
        launcher.bootstrap_project(["--write", str(tmp_path)], meta, "marketing.harness.yaml")
        == 0
    )
    assert marketing_root.is_dir()
    assert scratch.is_dir()
    assert "mode=write" in capsys.readouterr().out
