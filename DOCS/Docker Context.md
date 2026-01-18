## ==================================================
## DOC 4: DOCKER BUILD CONTEXT / LAYER CACHING
## ==================================================

TARGET:
- Dockerfile: Multi-stage build
- Issue: Build times slow, layers not cached properly

PRELOADED COMMANDS:
- docker
- grep

STEP 1: INSPECT DOCKER BUILD LAYERS
- Run:
  ```bash
  docker build --progress=plain .
  ```
- Look for:
  - CACHED markers on layers
  - RUN commands invalidating cache

STEP 2: CHECK DOCKERFILE ORDER
- Look for:
  - Heavy dependencies (npm install) placed before frequently-changing code
  - Copy . . appearing too early
- Run:
  ```bash
  grep -n "COPY\|RUN\|FROM" Dockerfile
  ```

STEP 3: OPTIMIZE LAYER ORDER
- Move stable dependencies first:
  ```
  COPY package.json .
  RUN npm ci
  COPY . .
  ```

STEP 4: REBUILD WITH CACHE
- Run:
  ```bash
  docker build --no-cache -t myapp:latest .
  ```

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Compare build times before/after optimization
- Check image size with `docker images`
- Document optimizations in team wiki

---