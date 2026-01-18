==================================================
INSTRUCTION FILE: CI/CD PIPELINE FAILURE
==================================================

PIPELINE:
- Tool: GitHub Actions
- Repo: git.internal.example.com/backend/api-service

PRELOADED COMMANDS:
- git clone
- git pull
- npm test
- npm run build

STEP 1: OPEN PIPELINE RUN
- Review failed job logs.

STEP 2: CLONE REPOSITORY
- Run:
  git clone git@git.internal.example.com:backend/api-service.git

STEP 3: REPRODUCE FAILURE LOCALLY
- Run:
  npm install
  npm test
  npm run build

STEP 4: IDENTIFY FAILURE POINT
- Test
- Lint
- Build

STEP 5: ESCALATE OR FIX
- If fix is code change → Developer required
- If env/config → Apply fix

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record pipeline ID
- Record failing step
- Escalate if needed

==================================================