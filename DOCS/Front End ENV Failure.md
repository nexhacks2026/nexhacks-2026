==================================================
INSTRUCTION FILE: FRONTEND ENVIRONMENT VARIABLE ISSUE
==================================================

PROJECT:
- customer-portal

PRELOADED COMMANDS:
- ssh svc-it-automation@fe01.internal.example.com
- printenv
- cat
- grep

STEP 1: CONNECT TO SERVER
- Run:
  ssh svc-it-automation@fe01.internal.example.com

STEP 2: NAVIGATE TO PROJECT
- Run:
  cd /srv/frontend/customer-portal

STEP 3: CHECK ENV FILE
- Run:
  cat .env

STEP 4: VERIFY REQUIRED VARIABLES
- Required:
  - REACT_APP_API_URL
  - REACT_APP_AUTH_URL

STEP 5: CHECK RUNTIME ENV
- Run:
  printenv | grep REACT_APP_

STEP 6: RESTART APP IF CHANGED
- Run:
  npm run start

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record env values checked
- Record restart time
- Close or escalate

==================================================