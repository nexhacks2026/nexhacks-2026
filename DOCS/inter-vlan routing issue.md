==================================================
INSTRUCTION FILE: VLAN NOT ROUTING (INTER-VLAN ROUTING ISSUE)
==================================================

TARGET DEVICE:
- Layer 3 Switch: sw-core-01.internal.example.com

PRELOADED COMMANDS:
- ssh netadmin@sw-core-01.internal.example.com
- show ip interface brief
- show running-config interface
- show ip route

STEP 1: CONNECT TO SWITCH
- Run:
  ssh netadmin@sw-core-01.internal.example.com

STEP 2: CHECK VLAN INTERFACE
- Run:
  show ip interface brief | include Vlan20

STEP 3: VERIFY VLAN INTERFACE CONFIG
- Run:
  show running-config interface Vlan20

STEP 4: VERIFY IP ADDRESS
- Expected:
  ip address 10.20.0.1 255.255.255.0

STEP 5: ENABLE VLAN INTERFACE IF DOWN
- Run:
  configure terminal
  interface Vlan20
  no shutdown
  end
  write memory

STEP 6: CHECK ROUTING TABLE
- Run:
  show ip route | include 10.20.0.0

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record VLAN interface state
- Record routing entry
- Close or escalate

==================================================