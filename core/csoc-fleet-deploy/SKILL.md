# Skill: /csoc-fleet-deploy — ส่ง URL-Checker เวอร์ชันใหม่ไปติดตั้งทั้ง 4 CSOC machines

> **เป้าหมาย**: ติดตั้ง/อัปเดต URL-Checker บน `mdes001`, `mdes002`, `pc-csoc001`, `pc-csoc002` พร้อม detect DB ของผู้ใช้ โดยไม่หมุน key ก่อน 18:00 และไม่รัน production mode

## คำสั่ง

```
/csoc-fleet-deploy                   # สั่ง deploy ทั้งกองทัพ (dry-run → real)
/csoc-fleet-deploy --dry-run         # ทดสอบทุกขั้นตอน แต่ไม่ติดตั้งจริง
/csoc-fleet-deploy --gui-canary     # เปิด GUI canary บน Boss session
/csoc-fleet-deploy --machine mdes001 # deploy เครื่องเดียว
```

## สิ่งที่ทำ

1. **อ่าน fleet inventory** จาก `csoc_boi/fleet/machines.json`
2. **ส่งคำสั่ง** ให้แต่ละเครื่องรัน `scripts/deploy_fleet_machine.ps1` (ผ่าน Tailscale/SSH/Hermes bus/scheduled task ตาม method ของเครื่อง)
3. **รัน dry-run canary** (`python -m csoc_boi.canary_launch --dry-run`) บนแต่ละเครื่อง
4. **Detect DB** ของผู้ใช้จาก `.env` ที่มีอยู่ โดยไม่หมุน key
5. **รวมผล** เป็น JSON report ที่ `csoc_boi/fleet/deploy-report.json`
6. **ส่งข้อความ** "เพื่อน พวกนายไม่ต้องเหนื่อยแล้ว" ไปยัง CSOC team channel เมื่อสำเร็จ

## กฎเหล็ก

- **Test Mode ก่อนเสมอ**: ตั้ง `URLCHECKER_TEST_MODE=1`
- **ไม่รัน production mode** ของ URL-Checker
- **ไม่หมุน key ก่อน 18:00** (Boss rule)
- **ไม่ force-push / ไม่ลบ history**
- **Dry-run ผ่านก่อน** ค่อย real deploy

## ผลลัพธ์

```
[OK] fleet inventory loaded: 4 machines
[OK] mdes001: dry-run passed, DB detected
[OK] mdes002: dry-run passed, DB detected
[OK] pc-csoc001: dry-run passed, DB detected
[OK] pc-csoc002: dry-run passed, DB detected
[OK] report written to csoc_boi/fleet/deploy-report.json
[OK] message queued for CSOC team
```
