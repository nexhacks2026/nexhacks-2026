==================================================
INSTRUCTION FILE: API ENDPOINT NOT RESPONDING
==================================================

SERVICE:
- api-service
- Endpoint: /v1/users
- Server: be01.internal.example.com

PRELOADED COMMANDS:
- ssh svc-it-automation@be01.internal.example.com
- curl
- journalctl

STEP 1: CONNECT TO SERVER
- Run:
  ssh svc-it-automation@be01.internal.example.com

STEP 2: TEST ENDPOINT LOCALLY
- Run:
  curl http://localhost:4000/v1/users

STEP 3: CHECK LOGS
- Run:
  journalctl -u api-service --since "15 minutes ago"

STEP 4: RESTART SERVICE
- Run:
  sudo systemctl restart api-service

STEP 5: RETEST ENDPOINT
- Run:
  curl http://localhost:4000/v1/users

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record response codes
- Record logs reviewed
- Close or escalate

==================================================