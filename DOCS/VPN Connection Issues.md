==================================================
INSTRUCTION FILE: VPN CONNECTION FAILURE (USER SIDE)
==================================================

TARGET SYSTEM:
- VPN gateway: vpn01.internal.example.com
- VPN software: OpenVPN

PRELOADED COMMANDS (SERVER CHECK):
- ssh svc-it-automation@vpn01.internal.example.com
- systemctl status openvpn-server
- journalctl -u openvpn-server

STEP 1: CONFIRM USER DETAILS
- Username: jsmith
- Operating system: Windows / macOS / Linux

STEP 2: USER INSTRUCTIONS (NO SSH)
- Instruct user to:
  1. Disconnect VPN
  2. Reboot device
  3. Reconnect VPN

STEP 3: CONNECT TO VPN SERVER
- Run:
  ssh svc-it-automation@vpn01.internal.example.com

STEP 4: CHECK VPN SERVICE STATUS
- Run:
  systemctl status openvpn-server

STEP 5: CHECK VPN LOGS
- Run:
  journalctl -u openvpn-server --since "30 minutes ago"

STEP 6: CHECK USER CERTIFICATE
- Run:
  ls /etc/openvpn/clients/jsmith.crt

STEP 7: RESTART VPN SERVICE (ONCE)
- Run:
  sudo systemctl restart openvpn-server

STEP 8: ASK USER TO RETRY CONNECTION

--------------------------------------------------
FINALIZATION
--------------------------------------------------
- Record server status
- Record user retry outcome
- Attach logs if failure persists
- Close or escalate

==================================================
