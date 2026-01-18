## ==================================================
## DOC 3: ENVIRONMENT VARIABLE NOT LOADING
## ==================================================

TARGET:
- Application: Node.js backend / frontend build
- Issue: process.env.VAR_NAME is undefined or wrong value

PRELOADED COMMANDS:
- grep
- env
- echo

STEP 1: VERIFY ENV FILE EXISTS
- Run:
  ```bash
  ls -la .env .env.local .env.development
  ```

STEP 2: CHECK ENV VARIABLE SYNTAX
- Look for:
  - KEY=value format (no spaces around =)
  - No quotes unless needed
  - No comments on same line
- Run:
  ```bash
  cat .env | grep YOUR_VAR
  ```

STEP 3: VALIDATE LOADING IN CODE
- Add console log:
  ```bash
  echo "console.log('API_URL:', process.env.API_URL)" >> src/index.js
  ```
- Restart dev server and check output

STEP 4: CLEAR ENV CACHE
- If using dotenv:
  ```bash
  rm -rf node_modules/.cache
  npm run dev
  ```

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Verify .env is in .gitignore
- Never commit secrets
- Confirm env vars in build logs
- Close or escalate to DevOps for production

---



