==================================================
INSTRUCTION FILE: NO INTERNET ACCESS (DEFAULT GATEWAY ISSUE)
==================================================

TARGET DEVICE:
- Core Router: rtr-core-01.internal.example.com
- Vendor: Cisco IOS

PRELOADED COMMANDS:
- ssh netadmin@rtr-core-01.internal.example.com
- show ip route
- show running-config
- ping
- traceroute

STEP 1: CONNECT TO ROUTER
- Run:
  ssh netadmin@rtr-core-01.internal.example.com

STEP 2: CHECK DEFAULT ROUTE
- Run:
  show ip route | include 0.0.0.0

STEP 3: VERIFY DEFAULT GATEWAY
- Expected:
  S* 0.0.0.0/0 via 203.0.113.1

STEP 4: TEST CONNECTIVITY
- Run:
  ping 8.8.8.8
  traceroute 8.8.8.8

STEP 5: ADD DEFAULT ROUTE IF MISSING
- Run:
  configure terminal
  ip route 0.0.0.0 0.0.0.0 203.0.113.1
  end
  write memory

STEP 6: RETEST CONNECTIVITY
- Run:
  ping 8.8.8.8

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record routing table
- Record connectivity test results
- Close or escalate

==================================================