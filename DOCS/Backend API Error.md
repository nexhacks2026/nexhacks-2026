==================================================
INSTRUCTION FILE: BACKEND SERVICE ERROR (NODE.JS API)
==================================================

SERVICE:
- Name: api-service
- Server: be01.internal.example.com
- Port: 4000

PRELOADED COMMANDS:
- ssh svc-it-automation@be01.internal.example.com
- systemctl status
- journalctl
- node
- npm

STEP 1: CONNECT TO BACKEND SERVER
- Run:
  ssh svc-it-automation@be01.internal.example.com

STEP 2: CHECK SERVICE STATUS
- Run:
  systemctl status api-service

STEP 3: CHECK SERVICE LOGS
- Run:
  journalctl -u api-service --since "30 minutes ago"

STEP 4: CHECK NODE VERSION
- Run:
  node -v

STEP 5: RESTART SERVICE
- Run:
  sudo systemctl restart api-service

STEP 6: VERIFY SERVICE
- Run:
  systemctl status api-service

STEP 7: TEST API
- Run:
  curl http://localhost:4000/health

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record service state
- Record logs reviewed
- Record API response
- Close or escalate

==================================================