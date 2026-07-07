# innova-skills-lib — Risk Assessment

Operational and architectural risks for the central skill library.

---

## R-01: Single-writer tooling with no tests

**Risk**: `register_skills.py` and `generate_adapters.py` are the only path from source skills to the manifest and adapters. They have no automated tests.  
**Impact**: A bug in path normalization, frontmatter parsing, or JSON writing could corrupt the manifest or produce broken adapters for all 295 skills.  
**Likelihood**: MEDIUM  
**Mitigation**:
- Add pytest coverage for frontmatter parsing, manifest JSON validation, and adapter output.
- Diff the manifest/adapters in CI before accepting changes.
- Run `python -m json.tool` on the manifest as a smoke test.

---

## R-02: Hard-coded Windows paths

**Risk**: `register_skills.py` hard-codes `C:\Users\MDES-DEV-NB\.claude\skills`.  
**Impact**: The library cannot be regenerated on another machine or CI runner without editing source.  
**Likelihood**: HIGH (any fresh clone on a different host)  
**Mitigation**:
- Replace the hard-coded path with `Path.home() / '.claude' / 'skills'`.
- Add a `--skills-root` CLI argument for overrides.
- Keep a local `.env` or config file out of the repo for machine-specific paths.

---

## R-03: Adapter drift between source and generated output

**Risk**: `adapters/claude/*.md` are generated output but committed to git. If someone edits an adapter by hand, the next generator run will silently overwrite it.  
**Impact**: Lost manual fixes; confusion about which file is authoritative.  
**Likelihood**: MEDIUM  
**Mitigation**:
- Add a CI check that fails if `adapters/` differs from a fresh `generate_adapters.py` run.
- Document the "generated output — do not edit" rule prominently (already in CLAUDE.md).
- Consider a pre-commit hook that blocks hand-edits to `adapters/`.

---

## R-04: Manifest/index out of sync

**Risk**: `skills_manifest.json` and `skills_index.md` are generated separately but both committed. They can drift (currently 295 vs 291).  
**Impact**: Consumers see inconsistent numbers; trust in the registry degrades.  
**Likelihood**: MEDIUM  
**Mitigation**:
- Always run both generators from the same invocation.
- CI check: compare manifest `total` against index total and adapter file count.

---

## R-05: Private skills are invisible to tooling

**Risk**: `private/` is excluded from the manifest by convention and `.gitignore`. Skills placed there are not tracked, versioned, or distributed.  
**Impact**: Important skills can be "lost" in private directories; there's no audit trail.  
**Likelihood**: LOW  
**Mitigation**:
- Document promotion/archival workflow for private skills.
- Keep a separate private manifest or inventory file if private skills need tracking without public distribution.

---

## R-06: Dependency on live `~/.claude/skills/`

**Risk**: `generate_adapters.py` reads source `SKILL.md` from the live global skills directory, not from the repo's own source tree.  
**Impact**: If the global directory is stale or has local overrides, the generated adapters don't match the repo state.  
**Likelihood**: MEDIUM  
**Mitigation**:
- Change the default source root to the repo's own category directories, with an optional override for live global skills.
- Or keep the repo's source tree as the canonical input and treat `~/.claude/skills/` as the deployment target.

---

## R-07: Multi-runtime support is documented but unimplemented

**Risk**: README and CLAUDE.md claim support for Claude, Copilot, Codex, and Hermes adapters, but only Claude is implemented.  
**Impact**: Users expect cross-runtime skills and encounter silent failures or missing directories.  
**Likelihood**: MEDIUM  
**Mitigation**:
- Either implement the missing runtime writers or update docs to say "Claude only (Copilot/Codex/Hermes planned)".
- Add a roadmap or issue tracker for runtime expansion.

---

## R-08: No rollback/backup for manifest regeneration

**Risk**: Running `register_skills.py` overwrites the manifest in place. A bad run can destroy the previous registry state.  
**Impact**: Hard to recover from generator bugs or accidental data loss.  
**Likelihood**: LOW  
**Mitigation**:
- Keep the manifest in git and rely on `git diff`/`git checkout` for recovery.
- Consider writing a backup copy before regeneration in a local `manifests/.backups/` directory (gitignored).

---

## R-09: Manual category README maintenance

**Risk**: Category `README.md` files list skills manually. They can fall out of sync with the manifest/index.  
**Impact**: Contributors look at READMEs and find missing skills or broken links.  
**Likelihood**: MEDIUM  
**Mitigation**:
- Generate category READMEs from the manifest, or
- Add CI check that verifies every manifest entry has a matching line in its category README.

---

## R-10: Regex frontmatter parser limits expressiveness

**Risk**: The custom frontmatter parser cannot handle lists, nested objects, or multi-line strings.  
**Impact**: Skill metadata stays flat; richer schema (e.g., per-runtime flags, dependencies) can't be added without parser changes.  
**Likelihood**: MEDIUM (as the library grows)  
**Mitigation**:
- Migrate to PyYAML with a test suite that validates every existing skill still parses correctly.
- Keep the parser simple until the schema actually needs complexity.
