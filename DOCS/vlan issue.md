==================================================
INSTRUCTION FILE: CANNOT CONNECT TO NETWORK (USER VLAN ISSUE)
==================================================

TARGET DEVICE:
- Access Switch: sw-access-01.internal.example.com
- Management IP: 10.0.10.5
- Vendor: Cisco IOS

PRELOADED COMMANDS:
- ssh netadmin@sw-access-01.internal.example.com
- show ip interface brief
- show vlan brief
- show interface status
- show running-config interface

STEP 1: CONNECT TO SWITCH
- Run:
  ssh netadmin@sw-access-01.internal.example.com

STEP 2: VERIFY SWITCH STATUS
- Run:
  show ip interface brief

STEP 3: CHECK VLAN EXISTS
- Run:
  show vlan brief

- Confirm VLAN 20 (User_Network) exists.

STEP 4: CHECK USER PORT STATUS
- Identify port from ticket (example: GigabitEthernet1/0/12)
- Run:
  show interface status | include Gi1/0/12

STEP 5: CHECK PORT VLAN CONFIGURATION
- Run:
  show running-config interface GigabitEthernet1/0/12

STEP 6: VERIFY PORT IS UP AND IN CORRECT VLAN
- Look for:
  - switchport mode access
  - switchport access vlan 20

STEP 7: FIX VLAN ASSIGNMENT (IF INCORRECT)
- Run:
  configure terminal
  interface GigabitEthernet1/0/12
  switchport mode access
  switchport access vlan 20
  end
  write memory

STEP 8: VERIFY CONNECTIVITY
- Run:
  show interface status | include Gi1/0/12

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record port and VLAN
- Record configuration changes
- Close or escalate

==================================================