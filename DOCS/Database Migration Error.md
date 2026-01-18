==================================================
INSTRUCTION FILE: BACKEND DATABASE MIGRATION FAILURE
==================================================

SERVICE:
- api-service
- Database: app_prod
- Server: db01.internal.example.com

PRELOADED COMMANDS:
- ssh svc-it-automation@be01.internal.example.com
- npm run migrate
- psql

STEP 1: CONNECT TO BACKEND SERVER
- Run:
  ssh svc-it-automation@be01.internal.example.com

STEP 2: RUN MIGRATION
- Run:
  npm run migrate

STEP 3: IF MIGRATION FAILS
- Capture output
- Do NOT re-run automatically

STEP 4: CONNECT TO DATABASE
- Run:
  ssh svc-it-automation@db01.internal.example.com

STEP 5: CHECK DATABASE STATUS
- Run:
  systemctl status postgresql

STEP 6: ESCALATE
- Attach migration logs

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record migration output
- Record database status
- Escalate

==================================================