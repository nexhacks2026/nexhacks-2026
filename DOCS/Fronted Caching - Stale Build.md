==================================================
INSTRUCTION FILE: FRONTEND CACHING / STALE BUILD
==================================================

TARGET:
- CDN: cdn.example.com
- Frontend URL: https://customer-portal.example.com

PRELOADED COMMANDS:
- curl  
- grep

STEP 1: VERIFY STALE CONTENT
- Run:
  curl -I https://customer-portal.example.com

STEP 2: CHECK CACHE HEADERS
- Look for:
  - cache-control
  - etag

STEP 3: CLEAR CDN CACHE
- Use CDN dashboard or API.

STEP 4: RETEST
- Run:
  curl -I https://customer-portal.example.com

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record headers before/after
- Close or escalate

==================================================