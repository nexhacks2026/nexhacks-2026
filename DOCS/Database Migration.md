## ==================================================
## DOC 6: DATABASE MIGRATION / SCHEMA MISMATCH
## ==================================================

TARGET:
- Migration Tool: Knex, TypeORM, Alembic, etc.
- Issue: Migration failed, schema out of sync

PRELOADED COMMANDS:
- npm / python / sql
- grep

STEP 1: CHECK MIGRATION STATUS
- For Knex:
  ```bash
  npm run knex migrate:status
  ```
- For TypeORM:
  ```bash
  npm run typeorm migration:show
  ```

STEP 2: IDENTIFY FAILED MIGRATION
- Look for:
  - "pending" status
  - Error logs in database
- Run:
  ```bash
  npm run knex migrate:status | grep pending
  ```

STEP 3: ROLLBACK & FIX
- Run:
  ```bash
  npm run knex migrate:rollback
  ```
- Edit migration file (check syntax, SQL correctness)
- Redeploy:
  ```bash
  npm run knex migrate:latest
  ```

STEP 4: VERIFY SCHEMA
- Run:
  ```bash
  npm run knex migrate:status
  ```

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Cross-check schema with ORM models
- Backup production before running migrations
- Document any manual schema fixes
- Close or escalate

---

