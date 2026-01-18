---

## ==================================================
## DOC 1: LOCAL BUILD CACHE / STALE DEPENDENCIES
## ==================================================

TARGET:
- Project: Node.js / npm application
- Issue: Changes not reflecting in build output

PRELOADED COMMANDS:
- npm
- rm
- ls

STEP 1: VERIFY STALE CACHE
- Run:
  ```bash
  npm cache verify
  ```

STEP 2: CHECK NODE_MODULES
- Look for:
  - Outdated lock file timestamps
  - Missing dependencies
  Run:
  ```bash
  ls -la node_modules/.bin
  npm list --depth=0
  ```

STEP 3: CLEAR LOCAL CACHE
- Run:
  ```bash
  rm -rf node_modules
  rm package-lock.json
  npm install
  ```

STEP 4: REBUILD & RETEST
- Run:
  ```bash
  npm run build
  ```

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Verify build output in dist/ folder
- Check bundle sizes haven't changed unexpectedly
- Close or escalate to DevOps

---