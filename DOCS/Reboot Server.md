==================================================
INSTRUCTION FILE: SYSTEM REBOOT (VIRTUAL SERVER)
==================================================

TARGET SYSTEM:
- Server: app01.internal.example.com

PRELOADED COMMANDS:
- ssh svc-it-automation@app01.internal.example.com
- uptime
- shutdown
- last reboot

STEP 1: CONFIRM REBOOT IS ALLOWED
- Ensure no production freeze is active.

STEP 2: CONNECT TO SERVER
- Run:
  ssh svc-it-automation@app01.internal.example.com

STEP 3: CHECK CURRENT UPTIME
- Run:
  uptime

STEP 4: NOTIFY AFFECTED USERS
- Send reboot notice.

STEP 5: REBOOT SYSTEM
- Run:
  sudo shutdown -r now

STEP 6: WAIT 2–5 MINUTES

STEP 7: RECONNECT
- Run:
  ssh svc-it-automation@app01.internal.example.com

STEP 8: VERIFY SYSTEM STATE
- Run:
  uptime
  last reboot

STEP 9: VERIFY SERVICES
- Run:
  systemctl status web-api.service

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record reboot time
- Record uptime
- Record service status
- Close or escalate

==================================================