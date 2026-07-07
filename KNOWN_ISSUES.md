# innova-skills-lib — Known Issues

Verified issues and documentation/behavior gaps discovered during the 2026-06-18 study pass.

---

## K-01: README references `.txt` manifest; actual file is `.json`

**Severity**: LOW  
**Location**: `README.md` line ~89 and `CLAUDE.md` line ~24  
**Detail**: Multiple docs state the manifest lives at `manifests/skills_manifest.txt`, but the tooling writes and reads `manifests/skills_manifest.json`.  
**Impact**: New contributors may look for the wrong file.  
**Workaround**: Use `manifests/skills_manifest.json`.  
**Fix needed**: Update README and CLAUDE.md to reference the correct filename.

---

## K-02: Only Claude runtime is actually produced

**Severity**: MEDIUM  
**Location**: `tools/register_skills.py`, `tools/generate_adapters.py`, `README.md` quick start  
**Detail**: README advertises `--runtime copilot`, `--runtime codex`, `--runtime hermes`, but:
- `register_skills.py` hard-codes `RUNTIMES = ['claude']` and `adapter_status = {'claude': 'ok'}`.
- `generate_adapters.py` only implements the Claude adapter writer; `ADAPTERS_OUT` is hard-coded to `adapters/claude`.
- No `adapters/copilot/`, `adapters/codex/`, or `adapters/hermes/` directories exist.

**Impact**: Multi-runtime distribution is documented but not implemented.  
**Workaround**: Use Claude-only workflows today.  
**Fix needed**: Extend `generate_adapters.py` with per-runtime writers or remove unimplemented runtimes from docs.

---

## K-03: 9arm plugin.json path mismatch

**Severity**: LOW  
**Location**: `CLAUDE.md` "Notes for Claude Code"  
**Detail**: CLAUDE.md says `9arm/.claude-plugin/plugin.json` must be updated when changing 9arm skills, but the file does not exist at that path.  
**Impact**: Contributors may search for a non-existent file.  
**Workaround**: Verify current 9arm packaging convention before adding plugin metadata.  
**Fix needed**: Either create `9arm/.claude-plugin/plugin.json` or update CLAUDE.md.

---

## K-04: Manifest total differs from index total

**Severity**: LOW  
**Location**: `manifests/skills_manifest.json`, `skills_index.md`  
**Detail**: Manifest reports 295 skills; index reports 291. Likely a stale `skills_index.md` from an earlier run or a difference in how duplicates/categories are counted.  
**Impact**: Mild confusion; numbers in docs may diverge.  
**Workaround**: Run `python tools/register_skills.py` to regenerate both from the same source.  
**Fix needed**: Re-run generator and commit both outputs together.

---

## K-05: No tests for the tooling

**Severity**: MEDIUM  
**Location**: `tools/`  
**Detail**: There are no unit or integration tests for `register_skills.py`, `generate_adapters.py`, or `sync_to_project.ps1`.  
**Impact**: Regressions in manifest generation or adapter formatting are caught only by manual inspection.  
**Workaround**: Manually verify manifest JSON and adapter counts after each change.  
**Fix needed**: Add pytest tests in a `tests/` directory (standard library only, matching the tooling's dependency policy).

---

## K-06: `private/` skills have no documented deprecation path

**Severity**: LOW  
**Location**: `private/`, `.gitignore`  
**Detail**: `private/` is ignored and excluded from the manifest (by design), but there is no visible workflow for promoting a private skill to public or archiving a retired private skill.  
**Impact**: Private skills are invisible to the registry; their lifecycle is ad-hoc.  
**Workaround**: Manually move skill directories between `private/` and category dirs, then rerun tooling.  
**Fix needed**: Document promotion/archival rules for private skills.

---

## K-07: Frontmatter parser is regex-based

**Severity**: LOW  
**Detail**: `register_skills.py` parses YAML frontmatter with a custom regex instead of a YAML library. It handles simple `key: value` pairs and strips matching quotes, but does not support nested structures, lists, or multi-line strings.  
**Impact**: Advanced frontmatter (e.g., `triggers: [a, b]`) would be mis-parsed. Current skills appear to use simple strings only.  
**Workaround**: Keep frontmatter flat and simple.  
**Fix needed**: Migrate to PyYAML if richer frontmatter is needed; add validation tests first.

---

## K-08: Windows-specific path assumptions

**Severity**: INFO  
**Location**: `tools/register_skills.py`, `tools/generate_adapters.py`  
**Detail**: Scripts embed Windows absolute paths (`C:\Users\MDES-DEV-NB\.claude\skills`) and normalize backslashes manually. This makes the repo non-portable to macOS/Linux without edits.  
**Impact**: Cross-platform CI or contributors on other OSes cannot run the tooling unchanged.  
**Workaround**: Parameterize skills root via environment variable or CLI argument.  
**Fix needed**: Replace hard-coded paths with `Path.home() / '.claude' / 'skills'` and a configurable override.
