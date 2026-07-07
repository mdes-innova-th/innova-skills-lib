# innova-skills-lib — Troubleshooting

Common problems and how to resolve them.

---

## `register_skills.py` says "Skills root does not exist"

**Symptom**:

```text
ERROR: Skills root does not exist: C:\Users\MDES-DEV-NB\.claude\skills
```

**Cause**: The global Claude Code skills directory hasn't been created yet.  
**Fix**:

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.claude\skills" -Force
```

---

## Manifest total doesn't match adapter count

**Symptom**: `manifests/skills_manifest.json` says 295 skills, but `adapters/claude/` has fewer files.

**Cause**: Adapter generation was run before/after manifest changes, or some entries lack `claude` in `runtimes`.  
**Fix**:

```powershell
cd C:\Users\MDES-DEV-NB\DEV\innova-skills-lib
python tools\register_skills.py
python tools\generate_adapters.py --runtime claude
(Get-ChildItem adapters\claude\*.md).Count
```

Compare the count to the manifest's `total` field.

---

## `generate_adapters.py` reports source not found

**Symptom**:

```text
[ERROR] my-skill: source not found: C:/Users/MDES-DEV-NB/.claude/skills/my-skill/SKILL.md
```

**Cause**: The manifest references a skill path that doesn't exist in the live `~/.claude/skills/` directory.  
**Fix**:

1. Check whether the skill exists in the source tree (`core/`, `ECC/`, etc.).
2. If it exists in this repo but not in `~/.claude/skills/`, sync it first:

```powershell
python tools\register_skills.py --sync-to "$env:USERPROFILE\.claude\skills"
```

3. If the skill was deleted or moved, update the source directory or rerun `register_skills.py` after fixing the layout.

---

## `sync_to_project.ps1` fails to create a junction

**Symptom**:

```text
ERROR my-skill  (...
```

**Cause**: Windows Developer Mode is off and the process lacks admin rights, or the target path already exists and `-Force` wasn't used.  
**Fix options**:

- Enable Windows Developer Mode (Settings → System → For developers → Developer Mode).
- Run PowerShell as administrator.
- Or use copy mode:

```powershell
.\tools\sync_to_project.ps1 -ProjectPath "C:\Users\MDES-DEV-NB\my-project" -Mode copy -Force
```

---

## Skill changes aren't visible in Claude Code

**Symptom**: You edited a skill, but Claude Code still uses the old version.

**Cause**: The project is loading skills from a stale local copy or the global skills directory hasn't been updated.  
**Fix**:

1. Regenerate manifest and adapters:

```powershell
python tools\register_skills.py
python tools\generate_adapters.py --runtime claude
```

2. Sync to the target project:

```powershell
.\tools\sync_to_project.ps1 -ProjectPath "C:\Users\MDES-DEV-NB\my-project" -Force
```

3. Restart Claude Code or reload the project window so it picks up new `.claude/skills/` content.

---

## `register_skills.py` throws a Unicode error

**Symptom**: `UnicodeDecodeError` while reading a `SKILL.md`.

**Cause**: A skill file is saved in a non-UTF-8 encoding.  
**Fix**:

1. Identify the problematic file from the error output.
2. Re-save it as UTF-8:

```powershell
Get-Content "path\to\SKILL.md" -Encoding UTF8 | Set-Content "path\to\SKILL.md" -Encoding UTF8
```

3. The script already falls back to `latin-1`, but UTF-8 is strongly preferred for Thai and special characters.

---

## Category README is out of date

**Symptom**: A skill exists and is in the manifest, but the category `README.md` doesn't list it.

**Cause**: Category READMEs are maintained manually, not generated.  
**Fix**: Add a one-line entry to the appropriate category `README.md` after adding a new skill.

---

## Frontmatter changes don't appear in manifest

**Symptom**: You updated the `description` or `name` in `SKILL.md`, but the manifest still shows the old value.

**Cause**: The manifest wasn't regenerated.  
**Fix**:

```powershell
python tools\register_skills.py
```

---

## `generate_adapters.py` skips entries

**Symptom**:

```text
[SKIP] my-skill: runtime 'claude' not listed, skipping.
```

**Cause**: The manifest entry's `runtimes` array doesn't include `claude`.  
**Fix**: Update the source skill frontmatter or tooling so the entry includes `"claude"` in `runtimes`.
