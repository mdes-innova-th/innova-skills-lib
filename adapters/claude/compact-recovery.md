<!-- skill-id: compact-recovery -->
<!-- source-path: compact-recovery -->
<!-- source-file: C:/Users/MDES-DEV-NB/.claude/skills/compact-recovery/SKILL.md -->
<!-- runtime: claude -->

# Compact Recovery

After Claude Code auto-compacts (context 100%), skill descriptions and session context are lost.
This skill recovers them.

## Recovery Steps

1. Read `.claude/skills/.arra-oracle-skills.json` — verify skill registry intact
2. Count skills with SKILL.md: ~110 expected
3. Read most recent `network/outbox/hermes/` for last known state
4. Read `CLAUDE.md` for identity and rules
5. Read `AGENTS.md` for Jit operating contract
6. Read `backlog.md` for pending tasks
7. Announce recovery: "Compact detected, recovered X skills, last state: [summary]"
