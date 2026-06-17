from __future__ import annotations

import json
from pathlib import Path

from harness.manifest import checksum_file
from harness.publish import publish_campaign


def write_render_output(root: Path) -> Path:
    output_dir = root / "outputs" / "feature-x-launch"
    output_dir.mkdir(parents=True)
    (output_dir / "web-banner.png").write_bytes(b"image-bytes")
    source_dir = root / "source"
    brand_path = source_dir / "brand" / "brand.lock.yaml"
    campaign_path = source_dir / "campaigns" / "feature-x-launch.campaign.yaml"
    reference_path = source_dir / "references" / "main_visual.png"
    brand_path.parent.mkdir(parents=True)
    campaign_path.parent.mkdir(parents=True)
    reference_path.parent.mkdir(parents=True)
    brand_path.write_text("brand:\n  id: codefox\n  name: CodeFox\nversion: 1.2.3\n")
    campaign_path.write_text("name: feature-x-launch\n")
    reference_path.write_bytes(b"reference-bytes")
    run_lock = {
        "brand_lock_path": str(brand_path),
        "campaign_path": str(campaign_path),
        "resolved_style": {
            "references": [str(reference_path)],
        },
    }
    (output_dir / "run.lock.json").write_text(
        json.dumps(run_lock, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "1.0",
        "campaign": "feature-x-launch",
        "brand": {
            "id": "codefox",
            "name": "CodeFox",
            "version": "1.2.3",
        },
        "brand_lock_version": "1.2.3",
        "generated_at": "2026-06-16T00:00:00+00:00",
        "provider": {
            "gateway": "generic",
            "model": "flux-2-pro",
        },
        "assets": [
            {
                "id": "web-banner",
                "file": "web-banner.png",
                "path": "web-banner.png",
                "url": None,
                "size": [1920, 600],
                "mime_type": "image/png",
                "checksum_sha256": checksum_file(output_dir / "web-banner.png"),
                "seed": 12345,
            }
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return root / "outputs"


def test_repo_publish_dry_run_reports_versioned_repo_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    outputs_dir = write_render_output(tmp_path)
    monkeypatch.setenv("HARNESS_REPO_PUBLISH_DIR", str(tmp_path / "published"))

    result = publish_campaign(
        "feature-x-launch",
        channel="repo",
        outputs_dir=outputs_dir,
        publish=False,
    )

    assert result.dry_run is True
    assert result.release_path == tmp_path / "published" / "codefox" / "1.2.3"
    assert result.artifacts[0]["url"].startswith("repo://")
    assert not result.release_path.exists()


def test_repo_publish_copies_assets_manifest_and_run_lock(
    tmp_path: Path,
    monkeypatch,
) -> None:
    outputs_dir = write_render_output(tmp_path)
    monkeypatch.setenv("HARNESS_REPO_PUBLISH_DIR", str(tmp_path / "published"))

    result = publish_campaign(
        "feature-x-launch",
        channel="repo",
        outputs_dir=outputs_dir,
        publish=True,
    )

    snapshot_dir = tmp_path / "published" / "codefox" / "1.2.3"
    artifact_dir = snapshot_dir / "artifacts" / "feature-x-launch"
    published_manifest = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))

    assert result.dry_run is False
    assert result.release_path == snapshot_dir
    assert (artifact_dir / "web-banner.png").read_bytes() == b"image-bytes"
    assert (artifact_dir / "run.lock.json").exists()
    assert (snapshot_dir / "brand" / "brand.lock.yaml").exists()
    assert (snapshot_dir / "campaigns" / "feature-x-launch.campaign.yaml").exists()
    assert (snapshot_dir / "references" / "main_visual.png").read_bytes() == b"reference-bytes"
    assert published_manifest["brand"]["id"] == "codefox"
    assert published_manifest["brand"]["version"] == "1.2.3"
    assert published_manifest["publish_channel"] == "repo"
    assert published_manifest["storage"]["channel"] == "repo"
    assert published_manifest["storage"]["snapshot_path"].endswith("/published/codefox/1.2.3")
    assert published_manifest["assets"][0]["path"] == "artifacts/feature-x-launch/web-banner.png"
    assert published_manifest["assets"][0]["url"].endswith("/web-banner.png")
