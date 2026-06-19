# Marketing Harness Workflows

Run commands from the product repository root. The product repo owns the
marketing paths declared in metadata; the installed skill owns workflow
instructions and the harness launcher. Do not assume a root-level `workspace/`,
`outputs/`, or `published/` tree.

Set the launcher and metadata paths once:

```bash
HARNESS_SCRIPT="$SKILL_ROOT/scripts/harness.py"
HARNESS_METADATA="packages/branding/marketing.harness.yaml"
```

The launcher prefers `HARNESS_PROJECT_DIR`, then `runtime.projectDir` from
metadata, then `harness` on PATH. Remote `uvx` fallback is disabled unless
`HARNESS_ALLOW_REMOTE_RUNTIME=1` or `policy.allowRemoteRuntimeFallback: true`.

## Setup

Consumer repo:

```bash
sh "$SKILL_ROOT/scripts/bootstrap_project.sh" --metadata "$HARNESS_METADATA" .
sh "$SKILL_ROOT/scripts/bootstrap_project.sh" --metadata "$HARNESS_METADATA" --write .
```

Harness development repo:

```bash
uv sync
```

Edit `.env` locally for the GPT Image skill/CLI:

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
HARNESS_REPO_PUBLISH_DIR=packages/branding/public/marketing
```

`.env` is ignored by git. Never paste key values into committed files.

## Validate Existing Campaign

```bash
python3 "$HARNESS_SCRIPT" --metadata "$HARNESS_METADATA" validate
```

## Dry-Run Render

```bash
python3 "$HARNESS_SCRIPT" --metadata "$HARNESS_METADATA" render \
  --dry-run
```

Expected output:

```text
<metadata artifacts.scratch>/<campaign>/
├── *.svg
├── manifest.json
└── run.lock.json
```

## Live Render With GPT Image Skill CLI

Confirm with the user before running because this calls the configured image API
through the GPT Image skill/CLI and can incur cost. `brand.lock.yaml` must set
`provider.gateway` to `gpt-image-skill` or its alias `skill-cli`. The provider
calls the local `gpt-image` CLI or the installed Codex skill launcher, then
resizes the output to each deliverable's exact size.

```bash
command -v gpt-image || true
test -f ~/.codex/skills/gpt-image/scripts/generate.py && echo "gpt-image skill installed"

python3 "$HARNESS_SCRIPT" --metadata "$HARNESS_METADATA" render
```

Expected output:

```text
<metadata artifacts.scratch>/<campaign>/
├── *.png
├── manifest.json
└── run.lock.json
```

This is only the local render buffer. Do not publish it yet unless the user
explicitly pre-approved auto-publish after render. Inspect the assets and ask
for human acceptance before any `--publish` command.

## Publish To Repo

Only enter this step after the user accepts the rendered assets, or when the
user explicitly asked to auto-publish after render. API-cost approval is not
asset approval.

Dry-run:

```bash
python3 "$HARNESS_SCRIPT" --metadata "$HARNESS_METADATA" publish
```

Write versioned artifacts:

```bash
python3 "$HARNESS_SCRIPT" --metadata "$HARNESS_METADATA" publish --publish
```

Expected output:

```text
<metadata artifacts.approved>/portfolios/<portfolio-id>/<portfolio-version>/
├── portfolio.meta.yaml
├── elements.yaml
└── accepted.yaml

<metadata artifacts.approved>/products/<portfolio-id>/<brand-id>/<brand-lock-version>/
├── portfolio/
├── metadata/
├── brand/brand.lock.yaml
├── campaigns/feature-x-launch.campaign.yaml
├── references/
└── artifacts/feature-x-launch/
    ├── *.png
    ├── manifest.json
    └── run.lock.json
```

The approved asset directory may be a public package directory, a separate
asset repository, or a git submodule inside the product repo. Portfolio
snapshots are stored there too. The harness does not run `git add`, `commit`,
or `push`; commit the asset repo/submodule after reviewing the snapshot.

## Produce Style Proposal

Use this when a design skill, Claude, or Codex is responsible for style production.

Design skill routing is intentionally fuzzy:

- If the user writes a hint after an explicit skill mention such as `$marketing-harness`, honor it first, for example "use local frontend-design" or "prefer claude-design".
- If the user does not name one, use an already-installed local design skill that fits brand/frontend/visual design.
- If none is available, stop. Do not install, clone, or download a fallback unless the user explicitly asks.
- The built-in local harness producer is only a deterministic scaffold; do not treat it as a replacement for creative style production from scratch unless the user explicitly accepts that tradeoff.

```bash
python3 "$HARNESS_SCRIPT" style propose \
  --metadata "$HARNESS_METADATA" \
  --out packages/branding/marketing/proposals/<brand-name>.lock.yaml \
  --version <next-version>
```

Then validate:

```bash
python3 "$HARNESS_SCRIPT" --metadata "$HARNESS_METADATA" validate \
  --brand packages/branding/marketing/proposals/<brand-name>.lock.yaml
```

Run regression before promotion:

```bash
python3 "$HARNESS_SCRIPT" regression \
  --metadata "$HARNESS_METADATA" \
  --brand packages/branding/marketing/proposals/<brand-name>.lock.yaml \
  --dry-run
```

Promote only after user review:

```bash
python3 "$HARNESS_SCRIPT" style promote \
  packages/branding/marketing/proposals/<brand-name>.lock.yaml \
  --metadata "$HARNESS_METADATA"
```

## External Design Producer

Use `--producer command` when an external design skill or script will generate the complete brand lock proposal:

```bash
python3 "$HARNESS_SCRIPT" style propose \
  --metadata "$HARNESS_METADATA" \
  --producer command \
  --producer-command "./scripts/design-skill-producer" \
  --out packages/branding/marketing/proposals/<brand-name>.lock.yaml \
  --version <next-version>
```

The command contract is documented in `references/design-producer-protocol.md`.

## Regression Review

Regression does not auto-score image quality.

```bash
python3 "$HARNESS_SCRIPT" --metadata "$HARNESS_METADATA" regression
```

Fill in the generated `scores.csv` manually. If quality drops, do not promote or publish the style change.
