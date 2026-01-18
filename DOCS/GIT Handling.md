
## ==================================================
## DOC 5: GIT MERGE CONFLICTS / REBASE ISSUES
## ==================================================

TARGET:
- Repository: Local git branch
- Issue: Conflicts or diverged history preventing merge

PRELOADED COMMANDS:
- git
- grep

STEP 1: CHECK CURRENT BRANCH STATE
- Run:
  ```bash
  git status
  git log --oneline -5
  ```

STEP 2: IDENTIFY CONFLICTS
- Run:
  ```bash
  git diff --name-only --diff-filter=U
  ```
- Look for:
  - <<<<<<< HEAD markers in files
  - Conflicting line changes

STEP 3: RESOLVE CONFLICTS
- Edit files manually OR use:
  ```bash
  git mergetool
  ```
- For each file:
  ```bash
  git add <resolved-file>
  ```

STEP 4: COMPLETE MERGE/REBASE
- If merging:
  ```bash
  git commit -m "Merge branch 'feature' into main"
  ```
- If rebasing:
  ```bash
  git rebase --continue
  ```

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Verify with `git log --graph --oneline`
- Run tests before pushing
- Push to remote: `git push origin branch-name`

---
