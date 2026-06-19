# Marketing Harness Skill

[English](README.md)

Marketing Harness 是一个可安装的 agent skill，用来生产“品牌风格锁定”的宣发图片。安装一次后，在任意业务 repo 里唤起它；agent 会校验品牌 token、准备 campaign、通过 GPT Image skill/CLI 出图，并把人工验收过的资产发布到当前业务 repo 的资产区。

这个 repo 交付两部分：

- `skills/marketing-harness/`: 真正可安装的 skill payload。
- `src/`: skill launcher 调用的 harness CLI runtime。

大多数使用者应该把它当作 skill，而不是普通 Python repo。Python runtime 的存在，是为了让 skill 有稳定可复现的执行层，而不是让每个业务 repo 复制一份生成代码。

## 这个 Skill 做什么

Marketing Harness 强制把“风格”和“内容”分开：

```text
brand memory -> brand.lock.yaml -> campaign.yaml -> render -> human review -> publish
```

skill 会帮助 agent 完成这些事：

- 读取小型 YAML/JSON metadata，明确业务 repo 的路径和策略。
- 构建或更新品牌 metadata 和 design-token 风格锁。
- 校验 `brand.lock.yaml` 和 campaign YAML。
- 先跑不花 API 钱的 dry-run。
- 通过本地 GPT Image skill/CLI 做真实出图。
- 在 publish 前要求人工验收产物。
- 把不可变快照发布到 `published/` 或指定 asset repo 路径。

下游应用只消费 `manifest.json` 和已发布图片文件，不自己跑生成。

## 安装

Claude Code：

```bash
npx skills add CodeFox-Repo/marketing-harness \
  --skill marketing-harness \
  --agent claude-code
```

Codex 本地开发时，可以把 Codex 指到 skill 子目录：

```bash
mkdir -p ~/.codex/skills
ln -s "$PWD/skills/marketing-harness" ~/.codex/skills/marketing-harness
```

安装后重启 agent。

## 使用

进入一个业务 repo，然后在任务里点名这个 skill：

```text
$marketing-harness 为这个 repo 初始化一个新产品品牌
$marketing-harness 校验 CodeFox example campaign
$marketing-harness 为 Claude 做一张 flag poster campaign，先 dry-run
$marketing-harness 用当前 brand lock 真实出图，然后等我验收
$marketing-harness 把已接受的 campaign 发布到 repo channel
```

安装后的 skill 内置一个 launcher：

```bash
python3 "$SKILL_ROOT/scripts/harness.py" ...
```

launcher 会让所有相对路径仍然落在当前业务 repo，并按这个顺序找 runtime：

1. `HARNESS_PROJECT_DIR` 指向的本地 checkout。
2. metadata 里的 `runtime.projectDir`。
3. PATH 上已有的 `harness` 命令。
4. 只有显式设置 `HARNESS_ALLOW_REMOTE_RUNTIME=1` 或
   `policy.allowRemoteRuntimeFallback: true` 时，才允许远端 `uvx` fallback。

所以 skill 包可以保持轻量，同时在新业务 repo 里仍然能跑。

## 业务 Repo 目录

业务 repo 拥有输入和产物。路径应该来自 metadata，而不是写死根目录结构。常见形态可以是：

```text
packages/branding/
  marketing/
    brand.lock.yaml
    campaigns/
    references/
    proposals/
  public/marketing/
    <approved assets and manifests>
  .harness/out/
```

- `project.marketingRoot`: 可编辑输入，包括品牌 metadata、风格锁、campaign YAML、proposal、references 和 accepted work 记录。
- `artifacts.scratch`: 本地 render buffer。
- `artifacts.approved`: 人工验收后的资产目录、资产仓路径或 submodule 目标。

raw scratch outputs 默认没有长期价值；只有人工验收后的最终资产才应该 promote 到 approved 路径。

## Brand Lock Contract

`brand.lock.yaml` 是某个产品品牌视觉风格的 single source of truth。token 结构遵循 W3C Design Tokens Format Module 的 `$value` + `$type` 约定。

参考：https://www.designtokens.org/tr/drafts/format/

锁定层分两层：

- `global`: 原始视觉决策，例如颜色、字体、风格片段、负向词和参考资产。
- `alias`: 语义风格配方，引用 `global`，例如 `alias.style.launch-hero`。

campaign 只能选择已经锁定的 style alias，并填写这次的内容：headline、subject、deliverable size。campaign 不能内联 prompt、palette、negative prompt、reference image、model 或 provider params。

## 人工验收

同意花 API 钱出图，不等于同意发布产物。

skill 应先 dry-run；真实调用 API 前确认成本；live render 后展示生成文件给用户检查。只有用户或 reviewer 明确接受图片、文字质量、尺寸和 brief 匹配度后，才执行带 `--publish` 的发布命令，除非用户提前明确允许自动发布。

回归测试也走人工评分。harness 可以生成对照图和 `scores.csv`，但不会假装自动判断图片质量。

## Skill 内容

```text
skills/marketing-harness/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
│   ├── harness.py
│   ├── bootstrap_project.sh
│   └── check_harness.sh
├── references/
│   ├── contracts.md
│   ├── workflows.md
│   └── design-producer-protocol.md
├── assets/
```

`SKILL.md` 是 agent 加载后的操作手册；这份 README 是给人看的总览。详细 schema 和命令流程在 `references/` 里，agent 会按任务需要加载，避免每次把所有细节塞进上下文。

开发 checkout 可以带 `examples/`，但默认打包出来的 skill artifact 不包含 examples。

## Runtime 要求

dry-run 和校验：

- Python 3.11+
- 推荐安装 `uv`

真实出图：

- 本地 GPT Image skill/CLI，或用 `HARNESS_SKILL_CLI_COMMAND` 指向等价命令
- `.env` 或环境变量里提供图片 API 凭证，通常是：

```bash
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
```

密钥只从环境读取，不应写进 YAML、manifest、run lock、日志或 published 快照。

## 维护者说明

repo 根目录用于维护 skill 和 CLI runtime：

```bash
uv sync
uv run ruff check .
uv run pytest
uv run harness validate skills/marketing-harness/examples/codefox/workspace/products/codefox/codefox/campaigns/example.campaign.yaml \
  --brand skills/marketing-harness/examples/codefox/workspace/products/codefox/codefox/brand.lock.yaml
```

只打包 skill payload：

```bash
python3 scripts/package_skill.py
```

zip 只包含 `skills/marketing-harness/` 内容。它不会打包根目录的 `src/`、`tests/`、`examples/`、`outputs/` 或 `published/`；真实 runtime 由本地 checkout 或已安装 CLI 提供。远端 runtime fallback 只能显式开启。只有维护/debug 包才使用 `--include-examples`。

打包脚本会强制 skill payload 形态：顶层允许 `scripts/`、`references/`、`assets/` 和 `agents/`；如果 skill payload 顶层出现 `src/` 或 `tests/`，打包会失败。
