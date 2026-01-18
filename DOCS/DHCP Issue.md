==================================================
INSTRUCTION FILE: DHCP NOT ASSIGNING IP ADDRESSES
==================================================

TARGET DEVICE:
- Router: rtr-core-01.internal.example.com

PRELOADED COMMANDS:
- ssh netadmin@rtr-core-01.internal.example.com
- show ip dhcp pool
- show ip dhcp binding
- show running-config

STEP 1: CONNECT TO ROUTER
- Run:
  ssh netadmin@rtr-core-01.internal.example.com

STEP 2: CHECK DHCP POOLS
- Run:
  show ip dhcp pool

STEP 3: CHECK ACTIVE LEASES
- Run:
  show ip dhcp binding

STEP 4: VERIFY DHCP CONFIG
- Run:
  show running-config | section dhcp

STEP 5: CHECK EXCLUDED ADDRESSES
- Ensure pool not exhausted.

STEP 6: CLEAR STALE LEASE (IF NECESSARY)
- Run:
  clear ip dhcp binding *

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record DHCP pool status
- Record number of leases
- Close or escalate

==================================================