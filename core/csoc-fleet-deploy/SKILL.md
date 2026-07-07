# Skill: /csoc-fleet-deploy — 3-phase hybrid deploy ของ URL-Checker ไปยัง CSOC fleet

> **เป้าหมาย**: ส่ง URL-Checker เวอร์ชันใหม่ไปติดตั้งบน 4 CSOC machines (`mdes001`, `mdes002`, `pc-csoc001`, `pc-csoc002`) ด้วยขั้นตอน 3 phase: สร้าง+canary exe -> ติดตั้ง csoc_boi agent -> อัปเดต fleet

## คำสั่งหลัก

```
/csoc-fleet-deploy                  # รันทั้ง 3 phases ตามลำดับ
/csoc-fleet-deploy --dry-run        # ทดสอบทุก command แต่ไม่เปลี่ยนแปลงจริง
/csoc-fleet-deploy --phase 1        # ทำเฉพาะ phase 1: build + canary exe
/csoc-fleet-deploy --phase 2        # ทำเฉพาะ phase 2: deploy csoc_boi agent
/csoc-fleet-deploy --phase 3        # ทำเฉพาะ phase 3: fleet update
/csoc-fleet-deploy --machine mdes001 # deploy เครื่องเดียว (phase 2+3)
```

## Phase 1 — Build & Canary EXE (บน Boss machine)

**เป้าหมาย**: สร้าง `URLChecker_ver{xxx}.exe` แล้วพิสูจน์ว่า GUI canary เปิด Test Mode ได้

### คำสั่ง

```powershell
# 1.1 สร้าง exe (PyInstaller / nuitka ตาม project setup)
rtk python -m build_exe

# 1.2 รัน verify launch script บน Boss session
powershell -ExecutionPolicy Bypass -File scripts/verify_exe_launch.ps1

# 1.3 เปิด GUI canary แล้วกด Test Mode
python -m csoc_boi.canary_launch --gui --urls data/canary_urls.csv

# 1.4 ตรวจสอบ evidence ที่เก็บไว้
Get-Content csoc_boi/fleet/canary-evidence.json
```

### เกณฑ์ผ่าน phase 1

- `verify_exe_launch.ps1` return `[OK]`
- `canary_launch` รายงาน `ok: true`
- Test Mode เปิดใช้งานได้ (ไม่รัน production mode)
- DB ของผู้ใช้ detect ได้โดยไม่ต้องหมุน key

## Phase 2 — Deploy csoc_boi Agent (บนแต่ละ target machine)

**เป้าหมาย**: ติดตั้ง/อัปเดต `csoc_boi` remote-command agent บนแต่ละเครื่องให้สามารถรับคำสั่งและรายงานผลกลับ

### Inventory

อ่านจาก `csoc_boi/fleet/machines.json`:

```json
[
  {"name": "mdes001",    "host": "mdes001",       "method": "tailscale-ssh", "user": "csoc-admin"},
  {"name": "mdes002",    "host": "mdes002",       "method": "tailscale-ssh", "user": "csoc-admin"},
  {"name": "pc-csoc001", "host": "pc-csoc001",    "method": "hermes-bus",    "user": "local"},
  {"name": "pc-csoc002", "host": "pc-csoc002",    "method": "hermes-bus",    "user": "local"}
]
```

### คำสั่งสำหรับแต่ละเครื่อง

#### mdes001 (Tailscale SSH)

```powershell
# อัปเดต agent code ผ่าน SSH
ssh csoc-admin@mdes001 "powershell -ExecutionPolicy Bypass -Command \"cd C:\csoc_boi; git pull; rtk python -m pip install -r requirements.txt\""

# restart agent service
ssh csoc-admin@mdes001 "powershell -ExecutionPolicy Bypass -File C:\csoc_boi\scripts\restart_agent.ps1"

# health check
ssh csoc-admin@mdes001 "powershell -ExecutionPolicy Bypass -Command \"python -m csoc_boi.health\""
```

#### mdes002 (Tailscale SSH)

```powershell
ssh csoc-admin@mdes002 "powershell -ExecutionPolicy Bypass -Command \"cd C:\csoc_boi; git pull; rtk python -m pip install -r requirements.txt\""
ssh csoc-admin@mdes002 "powershell -ExecutionPolicy Bypass -File C:\csoc_boi\scripts\restart_agent.ps1"
ssh csoc-admin@mdes002 "powershell -ExecutionPolicy Bypass -Command \"python -m csoc_boi.health\""
```

#### pc-csoc001 (Hermes bus / scheduled task)

```bash
# ส่งคำสั่งผ่าน Hermes file bus
node ~/.claude/skills/organ-pulse/scripts/pulse.js sayanprasathan "task:deploy-csoc_boi pc-csoc001 $(git rev-parse HEAD)"

# หรือ ถ้าใช้ scheduled task โดยตรง
ssh csoc-admin@pc-csoc001 "schtasks /run /tn csoc_boi_update"

# ตรวจสอบ inbox
node ~/.claude/skills/organ-pulse/scripts/pulse.js --inbox sayanprasathan
```

#### pc-csoc002 (Hermes bus / scheduled task)

```bash
node ~/.claude/skills/organ-pulse/scripts/pulse.js sayanprasathan "task:deploy-csoc_boi pc-csoc002 $(git rev-parse HEAD)"
ssh csoc-admin@pc-csoc002 "schtasks /run /tn csoc_boi_update"
node ~/.claude/skills/organ-pulse/scripts/pulse.js --inbox sayanprasathan
```

### เกณฑ์ผ่าน phase 2

- Agent ทุกเครื่องรายงาน `status: ready`
- Version/SHA ตรงกับ commit ที่ deploy
- Bus inbox รับ-ส่งได้

## Phase 3 — Fleet EXE Update

**เป้าหมาย**: ส่ง `URLChecker_ver{xxx}.exe` ใหม่ไปแทนที่ของเก่าบน fleet แล้ว canary อีกรอบ

### คำสั่งสำหรับแต่ละเครื่อง

#### mdes001

```powershell
# copy exe ไปเครื่องเป้าหมาย
scp dist/URLChecker_ver140.exe csoc-admin@mdes001:C:/ProgramData/URLChecker/URLChecker.exe

# รัน dry-run canary ผ่าน agent
ssh csoc-admin@mdes001 "powershell -ExecutionPolicy Bypass -Command \"cd C:\csoc_boi; python -m csoc_boi.canary_launch --dry-run\""
```

#### mdes002

```powershell
scp dist/URLChecker_ver140.exe csoc-admin@mdes002:C:/ProgramData/URLChecker/URLChecker.exe
ssh csoc-admin@mdes002 "powershell -ExecutionPolicy Bypass -Command \"cd C:\csoc_boi; python -m csoc_boi.canary_launch --dry-run\""
```

#### pc-csoc001

```bash
# สั่ง agent ดึง exe จาก shared store แล้ว canary
node ~/.claude/skills/organ-pulse/scripts/pulse.js sayanprasathan "task:update-urlchecker pc-csoc001 URLChecker_ver140.exe --dry-run"
```

#### pc-csoc002

```bash
node ~/.claude/skills/organ-pulse/scripts/pulse.js sayanprasathan "task:update-urlchecker pc-csoc002 URLChecker_ver140.exe --dry-run"
```

### เปลี่ยนเป็น real deploy

เมื่อ dry-run ผ่านทุกเครื่อง:

```powershell
# สำหรับ SSH machines
ssh csoc-admin@mdes001  "powershell -ExecutionPolicy Bypass -Command \"cd C:\csoc_boi; python -m csoc_boi.canary_launch\""
ssh csoc-admin@mdes002  "powershell -ExecutionPolicy Bypass -Command \"cd C:\csoc_boi; python -m csoc_boi.canary_launch\""
```

```bash
# สำหรับ Hermes machines
node ~/.claude/skills/organ-pulse/scripts/pulse.js sayanprasathan "task:update-urlchecker pc-csoc001 URLChecker_ver140.exe"
node ~/.claude/skills/organ-pulse/scripts/pulse.js sayanprasathan "task:update-urlchecker pc-csoc002 URLChecker_ver140.exe"
```

### เกณฑ์ผ่าน phase 3

- ทุกเครื่องรายงาน `canary: ok`
- GUI เปิด Test Mode ได้
- ไม่มี process production mode เก่าค้าง
- Report ถูกเขียนที่ `csoc_boi/fleet/deploy-report.json`

## กฎเหล็ก

- **Test Mode ก่อนเสมอ**: ตั้ง `URLCHECKER_TEST_MODE=1` บน fleet
- **ไม่รัน production mode** ของ URL-Checker
- **ไม่หมุน key ก่อน 18:00** (Boss rule)
- **Phase 1 ผ่านก่อน** ค่อย phase 2; **phase 2 ผ่านก่อน** ค่อย phase 3
- **Dry-run ผ่านทุกเครื่องก่อน** ค่อย real deploy
- **ไม่ force-push / ไม่ลบ history**

## ผลลัพธ์ที่คาดหวัง

```
[OK] phase 1: exe built + Boss canary passed
[OK] phase 2: agents deployed on 4 machines
[OK] mdes001:    canary ok, DB detected, Test Mode active
[OK] mdes002:    canary ok, DB detected, Test Mode active
[OK] pc-csoc001: canary ok, DB detected, Test Mode active
[OK] pc-csoc002: canary ok, DB detected, Test Mode active
[OK] report written to csoc_boi/fleet/deploy-report.json
```
