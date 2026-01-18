==================================================
INSTRUCTION FILE: PASSWORD RESET (LINUX USER)
==================================================

TARGET SYSTEM:
- Authentication server: auth01.internal.example.com
- Service account: svc-it-automation

PRELOADED COMMANDS:
- ssh svc-it-automation@auth01.internal.example.com
- whoami
- hostname
- getent passwd
- chage
- passwd
- journalctl

STEP 1: OPEN TERMINAL

STEP 2: CONNECT TO AUTH SERVER
- Run:
  ssh svc-it-automation@auth01.internal.example.com

STEP 3: VERIFY SESSION
- Run:
  whoami
  hostname

STEP 4: VERIFY USER EXISTS
- Run:
  getent passwd jsmith

- If no output:
  - Stop and escalate.

STEP 5: CHECK PASSWORD STATUS
- Run:
  chage -l jsmith

STEP 6: RESET PASSWORD
- Run:
  sudo passwd jsmith

- Follow prompt to set temporary password.

STEP 7: FORCE PASSWORD CHANGE ON NEXT LOGIN
- Run:
  sudo chage -d 0 jsmith

STEP 8: CHECK AUTH LOGS
- Run:
  journalctl -u sshd --since "15 minutes ago"

STEP 9: NOTIFY USER
- Inform user to log in and change password.

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record all commands executed
- Record password reset time
- Update ticket
- Close or escalate

==================================================