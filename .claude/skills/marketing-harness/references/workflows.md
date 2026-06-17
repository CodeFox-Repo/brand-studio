# Marketing Harness Workflows

Run commands from the repository root.

## Setup

```bash
uv sync
cp .env.example .env
```

Edit `.env` locally:

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
HARNESS_REPO_PUBLISH_DIR=published
```

`.env` is ignored by git. Never paste key values into committed files.

## Validate Existing Campaign

```bash
uv run harness validate workspace/campaigns/example.campaign.yaml \
  --brand workspace/brand/brand.lock.yaml
```

## Dry-Run Render

```bash
uv run harness render workspace/campaigns/example.campaign.yaml \
  --brand workspace/brand/brand.lock.yaml \
  --dry-run
```

Expected output:

```text
outputs/feature-x-launch/
├── *.svg
├── manifest.json
└── run.lock.json
```

## Live Render With OpenAI

Confirm with the user before running because this calls OpenAI and can incur cost.

```bash
uv run harness render workspace/campaigns/example.campaign.yaml \
  --brand workspace/brand/brand.lock.yaml
```

Expected output:

```text
outputs/feature-x-launch/
├── *.png
├── manifest.json
└── run.lock.json
```

## Publish To Repo

Dry-run:

```bash
uv run harness publish feature-x-launch --channel repo
```

Write versioned artifacts:

```bash
uv run harness publish feature-x-launch --channel repo --publish
```

Expected output:

```text
published/<brand-id>/<brand-lock-version>/
├── brand/brand.lock.yaml
├── campaigns/feature-x-launch.campaign.yaml
├── references/
└── artifacts/feature-x-launch/
    ├── *.png
    ├── manifest.json
    └── run.lock.json
```

## Produce Style Proposal

Use this when a design skill, Claude, or Codex is responsible for style production.

Design skill routing is intentionally fuzzy:

- If the user writes a hint after `/marketing-harness`, honor it first, for example "use local frontend-design" or "prefer claude-design".
- If the user does not name one, use an already-installed local design skill that fits brand/frontend/visual design.
- If none is available, stop. Do not install, clone, or download a fallback unless the user explicitly asks.
- The built-in local harness producer is only a deterministic scaffold; do not treat it as a replacement for creative style production from scratch unless the user explicitly accepts that tradeoff.

```bash
uv run harness style propose \
  --base workspace/brand/brand.lock.yaml \
  --brief workspace/brand/brief.md \
  --source workspace/references/ \
  --out workspace/brand/proposals/<brand-name>.lock.yaml \
  --version <next-version>
```

Then validate:

```bash
uv run harness validate workspace/campaigns/example.campaign.yaml \
  --brand workspace/brand/proposals/<brand-name>.lock.yaml
```

Run regression before promotion:

```bash
uv run harness regression \
  --brand workspace/brand/proposals/<brand-name>.lock.yaml \
  --dry-run
```

Promote only after user review:

```bash
uv run harness style promote \
  workspace/brand/proposals/<brand-name>.lock.yaml \
  --to workspace/brand/<brand-name>.lock.yaml
```

## External Design Producer

Use `--producer command` when an external design skill or script will generate the complete brand lock proposal:

```bash
uv run harness style propose \
  --producer command \
  --producer-command "./scripts/design-skill-producer" \
  --base workspace/brand/brand.lock.yaml \
  --brief workspace/brand/brief.md \
  --source workspace/references/ \
  --out workspace/brand/proposals/<brand-name>.lock.yaml \
  --version <next-version>
```

The command contract is documented in `references/design-producer-protocol.md`.

## Regression Review

Regression does not auto-score image quality.

```bash
uv run harness regression --brand workspace/brand/brand.lock.yaml
```

Fill in the generated `scores.csv` manually. If quality drops, do not promote or publish the style change.
