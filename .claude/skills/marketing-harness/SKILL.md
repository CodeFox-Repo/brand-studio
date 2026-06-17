---
name: marketing-harness
description: >-
  Operate the marketing image-generation harness repository: create or promote
  brand.lock design-token style proposals, validate campaign YAML, run
  regression, render OpenAI or gateway-backed marketing assets, publish
  repo/release/CDN artifacts, or package this harness as a reusable skill. Use
  when the user asks to create campaign assets, update brand style, use design
  skills for style production, run harness commands, manage manifests/artifacts,
  or install this skill for Claude Code/Codex.
---

# Marketing Harness

Operate the `marketing-harness` repository through its Python CLI. Preserve the core boundary:

```text
creative style production -> frozen brand.lock proposal -> validate/regression -> render -> publish
```

Never put visual style prompt text in campaign files. Campaigns describe only content and deliverables. Editable brand visual decisions live in `workspace/brand/*.lock.yaml`; proposed style changes live under `workspace/brand/proposals/`.

## Initial Check

Run this read-only check from the repository root before making changes:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-$HOME/.codex/skills/marketing-harness}"
python3 "$SKILL_DIR/scripts/check_harness.py" .
```

If that path is unavailable because the skill is being used directly from the repo, use `.claude/skills/marketing-harness/scripts/check_harness.py`.

If the check reports missing files, stop and explain the missing prerequisites. If `uv` is missing, tell the user to install it before running live commands.

## Common Workflows

Read [references/workflows.md](references/workflows.md) for exact command sequences.

Use these defaults unless the user says otherwise:

- Brand lock: `workspace/brand/brand.lock.yaml`
- Example campaign: `workspace/campaigns/example.campaign.yaml`
- Dry-run first for new flows
- Publish channel for local review: `repo`
- Do not commit automatically

## Style Production

When asked to have a design skill, Claude, Codex, or another creative system produce style, treat the user's words after the skill invocation as fuzzy routing hints. Examples: "use local frontend-design", "prefer claude-design", "from scratch", or "no design skill".

Use this selection order:

1. If the user names a local design skill, prefer that local skill.
2. Otherwise prefer any already-installed local design skill suited to brand/frontend/visual design.
3. If no suitable local design skill is available, stop and ask the user to install or specify one, or provide a reviewed brief and reference assets.

Do not download, install, or clone a remote design skill as an implicit fallback. Only do that if the user explicitly asks for installation.

Once a design producer is selected:

1. Create or update a brief, usually `workspace/brand/brief.md`.
2. Put reference assets in `workspace/references/`.
3. Run `harness style propose` to generate `workspace/brand/proposals/<name>.lock.yaml`.
4. Validate the proposal against a campaign.
5. Run regression, normally dry-run first.
6. Only after review, run `harness style promote`.

For the external design producer contract, read [references/design-producer-protocol.md](references/design-producer-protocol.md).

If the user asks to install or expose this skill in Codex, prefer a symlink from `$HOME/.codex/skills/marketing-harness` to this skill directory so the repo remains the single editable source.

## Rendering And Publishing

Before live render, confirm the user expects API usage and possible cost. `OPENAI_API_KEY` belongs in `.env`; never print, commit, or copy it into configuration files.

For live campaign generation:

```bash
uv run harness validate <campaign.yaml> --brand <brand.lock.yaml>
uv run harness render <campaign.yaml> --brand <brand.lock.yaml>
uv run harness publish <campaign-name> --channel repo --publish
```

When the user asks for a full generation, a new version, or assets ready for
project consumption, do not stop after `render`. `render` only writes the local
`outputs/` buffer; follow it with repo publish so the consumable snapshot lands
under `published/<brand-id>/<brand-version>/`.

For safe smoke tests:

```bash
uv run harness render <campaign.yaml> --brand <brand.lock.yaml> --dry-run
uv run harness publish <campaign-name> --channel repo
```

## Contracts

Use [references/contracts.md](references/contracts.md) when editing or reviewing `brand.lock.yaml`, campaign YAML, `manifest.json`, or `run.lock.json`.

Use bundled templates when creating new inputs:

- [assets/brand-brief-template.md](assets/brand-brief-template.md)
- [assets/campaign-template.yaml](assets/campaign-template.yaml)

## Verification

After code or workflow changes, run:

```bash
uv run ruff check .
uv run pytest
uv run harness validate workspace/campaigns/example.campaign.yaml
uv run harness render workspace/campaigns/example.campaign.yaml --dry-run
```

After live output, inspect:

- `outputs/<campaign>/manifest.json`
- `outputs/<campaign>/run.lock.json`
- `published/<brand-id>/<brand-version>/artifacts/<campaign>/manifest.json` when using repo publish

Check that no API key or image base64 payload is stored in tracked files.
