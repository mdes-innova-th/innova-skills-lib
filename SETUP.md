# innova-skills-lib — Setup & Workflow

How to install, develop, and maintain the central skill library.

---

## Prerequisites

- Python 3.10+ (for `register_skills.py` and `generate_adapters.py`)
- PowerShell 5.1+ (for `sync_to_project.ps1`)
- Git
- A global Claude Code skills directory at `~/.claude/skills/` (or `C:\Users\%USERNAME%\.claude\skills\` on Windows)

---

## Initial Setup

1. **Clone the repo** (if you haven't already):

```powershell
# From C:\Users\MDES-DEV-NB\DEV\
git clone <your-fork-or-origin> innova-skills-lib
cd innova-skills-lib
```

2. **Verify the global skills directory exists**:

```powershell
Test-Path "$env:USERPROFILE\.claude\skills"
```

If it doesn't exist, create it:

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.claude\skills" -Force
```

3. **Test the manifest generator**:

```powershell
cd C:\Users\MDES-DEV-NB\DEV\innova-skills-lib
python tools\register_skills.py
```

You should see output like:

```text
Scanning: C:\Users\MDES-DEV-NB\.claude\skills
Found 295 SKILL.md files
Manifest written: C:\Users\MDES-DEV-NB\DEV\innova-skills-lib\manifests\skills_manifest.json
Index written:    C:\Users\MDES-DEV-NB\DEV\innova-skills-lib\skills_index.md
============================================================
Skills registered : 295
Categories        : 3 -- 9arm, core, ecc
Errors            : 0
============================================================
```

---

## Normal Development Workflow

### Add a New Skill

1. Choose the right category directory (`core/`, `ECC/`, `gov/`, `finance/`, `9arm/`).
2. Create a subdirectory: `core/my-skill/`.
3. Add `core/my-skill/SKILL.md` with YAML frontmatter.
4. Run `python tools/register_skills.py` to update the manifest and index.
5. Run `python tools/generate_adapters.py --runtime claude` to regenerate Claude adapters.
6. Update the category `README.md` with a one-line entry linking to the new skill.
7. Sync to a project or global skills when ready:

```powershell
python tools\register_skills.py --sync-to "C:\Users\MDES-DEV-NB\innova-bot"
```

### Modify an Existing Skill

1. Edit the source `SKILL.md`.
2. Run `python tools/register_skills.py`.
3. Run `python tools/generate_adapters.py --runtime claude`.
4. Test the updated skill in a Claude Code project.

### Deprecate a Skill

1. Move the skill directory into a `deprecated/` subdirectory inside its category.
2. Add a deprecation note at the top of `SKILL.md`.
3. Run `python tools/register_skills.py`.
4. Do **not** delete the skill — history is preserved.

---

## Tool Reference

### `register_skills.py`

```bash
python tools/register_skills.py
python tools/register_skills.py --sync-to "/path/to/project/.claude/skills/"
```

- Scans `~/.claude/skills/` (hard-coded path in the script).
- Builds `manifests/skills_manifest.json`.
- Builds `skills_index.md`.
- With `--sync-to`, copies/junctions skills into a target project directory.

### `generate_adapters.py`

```bash
python tools/generate_adapters.py --runtime claude
```

- Currently supports `claude` only.
- Reads from the live `~/.claude/skills/` tree.
- Writes to `adapters/claude/`.

### `sync_to_project.ps1`

```powershell
.\tools\sync_to_project.ps1 -ProjectPath "C:\Users\MDES-DEV-NB\innova-bot"
.\tools\sync_to_project.ps1 -ProjectPath "C:\Users\MDES-DEV-NB\my-project" -Mode copy
.\tools\sync_to_project.ps1 -ProjectPath "C:\Users\MDES-DEV-NB\innova-bot" -DryRun
```

- Default mode is `junction` (zero-copy NTFS directory junction).
- Use `copy` for CI, containers, or network paths.
- `-Force` recreates existing entries.
- `-DryRun` prints planned actions without changing anything.

---

## Testing Your Changes

1. **Manifest integrity**:

```bash
python -m json.tool manifests/skills_manifest.json > /dev/null
```

2. **Adapter count check**:

```powershell
(Get-ChildItem adapters\claude\*.md).Count
```

This should equal the `total` value in the manifest for the Claude runtime.

3. **Skill load check** (in a Claude Code project):

```bash
/skill my-skill-name
```

or check that the skill file appears under the project's `.claude/skills/`.

---

## Windows Notes

- The tooling assumes Windows paths and `~/.claude/skills/` resolves to `C:\Users\%USERNAME%\.claude\skills\`.
- `sync_to_project.ps1` uses `cmd /c rmdir` to remove junctions safely without deleting source files.
- Developer Mode or admin rights may be required to create junctions; use `-Mode copy` if junction creation fails.

---

## Related Repos

| Path | Purpose |
|---|---|
| `C:\Users\MDES-DEV-NB\.claude\skills\` | Global, live Claude Code skills |
| `C:\Users\MDES-DEV-NB\innova-bot\` | innova-bot body — consumes this library |
| `C:\Users\MDES-DEV-NB\Jit\` | Jit Oracle — master orchestrator |
