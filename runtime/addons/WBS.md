# Windows Binux Share

WBS sources are in `lib/binux/wbs.py`. In a binux Linux VM or Windows WSL,
run `wbs init --ip YOUR_DEVICE_IP`, exchange public `identity.pem` certificates,
and verify each fingerprint on both devices before `wbs pair`.
Only explicitly shared paths and exact command allowlists can be accessed.
WBS uses TLS 1.3 and mutual certificate authentication. Private keys stay outside
the Android shared project home. `wbs revoke NAME` removes device trust.
For a VM listener on 127.0.0.1:58290, use
`binux runtime forward debian 58290 --allow-network` only when LAN access is wanted.
Screen sharing and native Windows executable emulation are not provided by WBS.
