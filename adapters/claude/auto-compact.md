<!-- skill-id: auto-compact -->
<!-- source-path: auto-compact -->
<!-- source-file: C:/Users/MDES-DEV-NB/.claude/skills/auto-compact/SKILL.md -->
<!-- runtime: claude -->

# Auto-Compact

ป้องกัน context 100% → skill หาย โดย compact แบบมีวินัย

## Trigger
- context เต็ม > 80% → auto-trigger
- ก่อน compact: save state → compact → recover skills
- user เรียก /auto-compact เองได้

## Pre-Compact (Save State)
1. `/rrr` — สรุป retrospective ลงไฟล์ ψ/memory/retrospectives/
2. เขียน current-goal ลง `network/loop/current-goal.txt`
3. เขียน Hermes status ลง `network/outbox/hermes/`
4. เขียน state file ลง `.claude/compact-state.json`

## Compact
5. Execute `/compact` — Claude Code bakes in TodoWrite + CLAUDE.md + memory files
6. Post-compact: อ่าน `.claude/compact-state.json` เพื่อรู้ว่าทำอะไรค้างอยู่

## Recovery
7. อ่าน `network/loop/current-goal.txt` — เป้าหมายล่าสุด
8. อ่าน latest Hermes outbox — สถานะล่าสุด
9. อ่าน CLAUDE.md + AGENTS.md — ตัวตนและกฎ
10. ตรวจสอบ services :47778 :7010 :4322
11. ประกาศ: "Recovered from compact — [สรุป], [N] pending tasks"
