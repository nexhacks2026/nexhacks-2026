==================================================
INSTRUCTION FILE: FRONTEND BUILD FAILURE (REACT)
==================================================

PROJECT:
- Name: customer-portal
- Repo: git.internal.example.com/frontend/customer-portal
- Server: fe01.internal.example.com
- Node version: 18.x

PRELOADED COMMANDS:
- ssh svc-it-automation@fe01.internal.example.com
- node -v
- npm -v
- npm install
- npm run build
- npm run start
- cat
- tail

STEP 1: CONNECT TO FRONTEND SERVER
- Run:
  ssh svc-it-automation@fe01.internal.example.com

STEP 2: VERIFY ENVIRONMENT
- Run:
  node -v
  npm -v

STEP 3: NAVIGATE TO PROJECT
- Run:
  cd /srv/frontend/customer-portal

STEP 4: INSTALL DEPENDENCIES
- Run:
  npm install

STEP 5: RUN BUILD
- Run:
  npm run build

STEP 6: REVIEW BUILD ERRORS
- If build fails:
  - Run:
    tail -n 100 npm-debug.log
  - Or:
    npm run build -- --verbose

STEP 7: START DEV SERVER (OPTIONAL)
- Run:
  npm run start

STEP 8: VERIFY APPLICATION
- Open:
  https://customer-portal.dev.example.com

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record Node and npm versions
- Record build output
- Attach error logs if failure persists
- Close or escalate

==================================================