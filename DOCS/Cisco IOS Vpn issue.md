==================================================
INSTRUCTION FILE: VPN SITE-TO-SITE DOWN (CISCO IOS)
==================================================

TARGET DEVICE:
- Edge Router: rtr-edge-01.internal.example.com

PRELOADED COMMANDS:
- ssh netadmin@rtr-edge-01.internal.example.com
- show crypto isakmp sa
- show crypto ipsec sa
- show running-config
- debug crypto isakmp

STEP 1: CONNECT TO ROUTER
- Run:
  ssh netadmin@rtr-edge-01.internal.example.com

STEP 2: CHECK ISAKMP STATUS
- Run:
  show crypto isakmp sa

STEP 3: CHECK IPSEC STATUS
- Run:
  show crypto ipsec sa

STEP 4: VERIFY PEER IP
- Confirm remote peer: 198.51.100.2

STEP 5: CLEAR AND REINITIATE VPN
- Run:
  clear crypto isakmp sa
  clear crypto ipsec sa

STEP 6: RECHECK STATUS
- Run:
  show crypto isakmp sa

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record SA states
- Record peer IP
- Close or escalate

==================================================