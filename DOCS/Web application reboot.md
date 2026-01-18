==================================================
INSTRUCTION FILE: APPLICATION REBOOT / RESTART
==================================================

TARGET SYSTEM:
- Application server: app01.internal.example.com
- Service: web-api.service

PRELOADED COMMANDS:
- ssh svc-it-automation@app01.internal.example.com
- systemctl status
- systemctl restart
- journalctl

STEP 1: CONNECT TO APPLICATION SERVER
- Run:
  ssh svc-it-automation@app01.internal.example.com

STEP 2: VERIFY SESSION
- Run:
  whoami
  hostname

STEP 3: CHECK SERVICE STATUS
- Run:
  systemctl status web-api.service

STEP 4: RESTART SERVICE
- Run:
  sudo systemctl restart web-api.service

STEP 5: VERIFY SERVICE IS RUNNING
- Run:
  systemctl status web-api.service

STEP 6: CHECK RECENT LOGS
- Run:
  journalctl -u web-api.service --since "10 minutes ago"

STEP 7: CONFIRM USER IMPACT RESOLVED

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record restart time
- Record service state
- Close or escalate

==================================================