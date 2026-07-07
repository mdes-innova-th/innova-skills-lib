# innova-skills-lib — Central Skills Library

**The canonical shared skill library for the มนุษย์ Agent system (Jit Oracle)**

คลังทักษะกลางที่ใช้ร่วมกันสำหรับระบบ มนุษย์ Agent — ทักษะที่เก็บไว้ที่นี่คือความรู้ที่ innova-bot กระจายไปยัง AI runtimes ต่าง ๆ ทั้ง Claude, GitHub Copilot, GPT, MDES Ollama และอื่น ๆ

---

## 📚 Documentation

| Document | Purpose |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System context, layers, manifest schema, data flow |
| [SETUP.md](SETUP.md) | Install, develop, test, and maintain skills |
| [KNOWN_ISSUES.md](KNOWN_ISSUES.md) | Verified bugs, doc/behavior gaps, and workarounds |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common failures and how to fix them |
| [RISKS.md](RISKS.md) | Operational and architectural risk assessment |
| [STUDY_LOG.md](STUDY_LOG.md) | How this repo was studied and documented |

---

## Architecture Overview

```
                 ┌─────────────────────────────┐
                 │       Jit Oracle (จิต)       │
                 │  Personality / Soul Layer    │
                 │  Master Orchestrator         │
                 └──────────┬──────────────────┘
                            │ directs
                 ┌──────────▼──────────────────┐
                 │       innova-bot             │
                 │  Body / Orchestrator Layer   │
                 │  Runs continuously 24/7      │
                 │  Distributes skills to       │
                 │  AI runtimes on demand       │
                 └──────────┬──────────────────┘
                            │ loads from
                 ┌──────────▼──────────────────┐
                 │    innova-skills-lib         │
                 │  Shared Brain / Skill Store  │
                 │                             │
                 │  core/    ECC/    gov/       │
                 │  finance/ 9arm/   private/   │
                 │  adapters/ manifests/ tools/ │
                 └──────────┬──────────────────┘
                            │ adapts to
          ┌─────────────────┼──────────────────┐
          │                 │                  │
    ┌─────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐
    │   Claude   │  │  GitHub      │  │  MDES        │
    │   Code     │  │  Copilot     │  │  Ollama      │
    │            │  │  / GPT       │  │  (gemma4)    │
    └────────────┘  └──────────────┘  └──────────────┘
```

**Jit Oracle** is the personality and soul layer — the master orchestrator that decides which skills are needed and when.

**innova-bot** is the body and operational layer — it runs continuously, ingests this library, and distributes skills to whichever AI runtime is handling a given task.

**innova-skills-lib** is the shared brain — a runtime-neutral, versioned store of canonical skills. Skills here are the single source of truth; adapters transform them for each runtime.

---

## Directory Structure

```
innova-skills-lib/
│
├── core/                    # Engineering + productivity core skills
│   └── README.md            # Skill index for core category
│
├── ECC/                     # ECC coding standards skills
│   └── README.md
│
├── gov/                     # Government / GovTech domain skills
│   └── README.md
│
├── finance/                 # Finance domain skills
│   └── README.md
│
├── 9arm/                    # Personal dev-loop skills (innova's own 9arm set)
│   ├── skills/
│   │   ├── engineering/     # debug-mantra, post-mortem, scrutinize
│   │   ├── productivity/    # management-talk
│   │   └── misc/
│   ├── scripts/
│   │   ├── link-skills.sh
│   │   └── list-skills.sh
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── CLAUDE.md
│   └── README.md
│
├── adapters/                # Runtime-specific adapters (generated)
│   ├── claude/              # Claude Code SKILL.md format
│   ├── copilot/             # GitHub Copilot instructions format
│   ├── codex/               # OpenAI Codex format
│   └── hermes/              # Hermes / local model format
│
├── manifests/               # Skill registry and manifest files
│   └── skills_manifest.txt  # Master manifest (JSON array)
│
├── private/                 # Private / unreleased skills (not distributed)
│
├── tools/                   # Python tooling for managing the library
│   ├── register_skills.py   # Scans skill dirs, updates manifest
│   └── generate_adapters.py # Generates runtime-specific adapter files
│
└── skills_index.md          # Top-level index (auto-generated)
```

---

## Quick Start

### 1. Register skills (update the manifest)

After adding or modifying skills, regenerate the manifest:

```bash
python tools/register_skills.py
```

This scans all skill directories, reads YAML frontmatter from each `SKILL.md`, and writes the updated `manifests/skills_manifest.json`.

### 2. Generate adapters for a runtime

To produce runtime-specific files from the canonical skills:

```bash
python tools/generate_adapters.py --runtime claude
python tools/generate_adapters.py --runtime copilot
python tools/generate_adapters.py --runtime codex
python tools/generate_adapters.py --runtime hermes
```

Output lands in `adapters/<runtime>/`.

### 3. Sync to a project

To install core skills into a project's Claude Code environment:

```bash
# From within the target project
python /path/to/innova-skills-lib/tools/register_skills.py --sync-to ~/.claude/skills/
```

Or use the 9arm convenience script to symlink:

```bash
cd 9arm
./scripts/link-skills.sh
```

---

## Manifest Schema

The master manifest lives at `manifests/skills_manifest.txt` (JSON format). Each entry follows this schema:

```json
{
  "id": "gov-qr-v1",
  "name": "GovAsset QR",
  "path": "gov/qr",
  "version": "2026.05.23",
  "runtimes": ["claude", "copilot", "codex", "hermes"],
  "triggers": ["qr", "scan", "asset"],
  "adapter_status": {
    "copilot": "ok",
    "claude": "ok",
    "codex": "pending"
  },
  "author": "team/jit-9warat",
  "last_updated": "2026-05-23T12:00:00Z"
}
```

| Field | Description |
|---|---|
| `id` | Unique skill identifier — `<category>-<name>-<version>` |
| `name` | Human-readable display name |
| `path` | Path relative to repo root |
| `version` | Date-based version `YYYY.MM.DD` |
| `runtimes` | Runtimes this skill supports |
| `triggers` | Keywords/commands that activate the skill |
| `adapter_status` | Per-runtime adapter generation status |
| `author` | Owning team or agent |
| `last_updated` | ISO 8601 timestamp |

---

## Skill Format

Each skill lives in its own directory containing:

```
my-skill/
├── SKILL.md       # Required — YAML frontmatter + skill body
└── <any assets>   # Optional supporting files, scripts, references
```

`SKILL.md` must begin with YAML frontmatter:

```yaml
---
name: my-skill
description: One-sentence description used in manifests and plugin registries.
---
```

---

## Contributing

### Adding a new skill

1. Choose the right category directory (`core/`, `gov/`, `finance/`, etc.)
2. Create a subdirectory: `<category>/<skill-name>/`
3. Create `SKILL.md` with YAML frontmatter and full skill body
4. Run `python tools/register_skills.py` to update the manifest
5. Run `python tools/generate_adapters.py` for the target runtimes
6. Add an entry to the category `README.md`

### Rules

- Never delete a skill — move to `deprecated/` and add a deprecation note instead
- Always run `register_skills.py` after any skill add or change
- `private/` skills must not appear in the manifest or any adapter output
- Each skill entry must link to its `SKILL.md` in the category README

---

## Related Repos

| Repo | Purpose |
|---|---|
| `C:\Users\MDES-DEV-NB\.claude\skills\` | Global Claude Code skills (installed, active) |
| `C:\Users\MDES-DEV-NB\innova-bot\` | innova-bot body — reads this lib at runtime |
| `C:\Users\MDES-DEV-NB\Jit\` | Jit Oracle — master orchestrator and soul |
| `Soul-Brews-Studio/arra-oracle-v3` | Oracle knowledge base (FTS5 + vector search) |
