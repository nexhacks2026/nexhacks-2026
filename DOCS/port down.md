==================================================
INSTRUCTION FILE: SWITCH PORT DOWN
==================================================

TARGET DEVICE:
- Access Switch: sw-access-02.internal.example.com

PRELOADED COMMANDS:
- ssh netadmin@sw-access-02.internal.example.com
- show interface
- show interface status
- show logging

STEP 1: CONNECT TO SWITCH
- Run:
  ssh netadmin@sw-access-02.internal.example.com

STEP 2: CHECK PORT STATUS
- Run:
  show interface GigabitEthernet1/0/8

STEP 3: CHECK ADMINISTRATIVE STATE
- Look for:
  - administratively down

STEP 4: ENABLE PORT IF SHUT DOWN
- Run:
  configure terminal
  interface GigabitEthernet1/0/8
  no shutdown
  end
  write memory

STEP 5: CHECK FOR ERRORS
- Run:
  show interface GigabitEthernet1/0/8 | include error

STEP 6: CHECK SYSTEM LOGS
- Run:
  show logging | include Gi1/0/8

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record port state
- Record errors
- Close or escalate

==================================================