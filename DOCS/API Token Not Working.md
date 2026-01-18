
## ==================================================
## DOC 7: API TOKEN / AUTH DEBUGGING
## ==================================================

TARGET:
- Service: REST/GraphQL API
- Issue: 401/403 errors, token not being sent/validated

PRELOADED COMMANDS:
- curl
- grep
- jq

STEP 1: VERIFY TOKEN GENERATION
- Add logging to auth endpoint:
  ```bash
  console.log('Token generated:', token);
  ```
- Test token generation:
  ```bash
  curl -X POST http://localhost:3000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"pass"}'
  ```

STEP 2: CHECK TOKEN FORMAT
- Decode JWT:
  ```bash
  echo "YOUR_TOKEN" | jq -R 'split(".")[1] | @base64d | fromjson'
  ```
- Look for:
  - Expiration time (exp claim)
  - User ID (sub claim)
  - Correct audience (aud claim)

STEP 3: VERIFY TOKEN IN REQUEST
- Run:
  ```bash
  curl -H "Authorization: Bearer YOUR_TOKEN" \
    http://localhost:3000/api/protected
  ```

STEP 4: CHECK MIDDLEWARE ORDER
- Look for:
  - Auth middleware placed before protected routes
  - Token verification key matches signing key
- Run:
  ```bash
  grep -n "app.use.*auth\|authenticate" src/index.js
  ```

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Verify token expiration is reasonable (15m-1h)
- Check browser DevTools > Network > Authorization header
- Test with Postman/Insomnia with token
- Close or escalate to security team
