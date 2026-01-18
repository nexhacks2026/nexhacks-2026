## ==================================================
## DOC 2: HOT RELOAD NOT DETECTING CHANGES
## ==================================================

TARGET:
- Dev Server: localhost:3000 (React, Vue, etc.)
- Issue: File changes not triggering rebuild

PRELOADED COMMANDS:
- grep
- ps
- kill

STEP 1: VERIFY DEV SERVER STATUS
- Run:
  ```bash
  ps aux | grep webpack
  ```
  or
  ```bash
  ps aux | grep vite
  ```

STEP 2: CHECK FILE WATCHER CONFIG
- Look for:
  - watchOptions in webpack.config.js
  - polling enabled/disabled
  - .watchmanconfig present
- Run:
  ```bash
  cat webpack.config.js | grep -A 5 watch
  ```

STEP 3: RESTART DEV SERVER
- Kill existing process:
  ```bash
  pkill -f "webpack serve"
  ```
- Restart:
  ```bash
  npm run dev
  ```

STEP 4: VERIFY FILE SYSTEM EVENTS
- Touch a file to trigger watch:
  ```bash
  touch src/index.js
  ```
- Check console for rebuild logs

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Confirm HMR (Hot Module Replacement) connected in browser console
- Check browser DevTools > Sources for latest file content
- If persists, increase inotify limits (Linux)

---
