# Firmware & OTA Update SOP

## Supported firmware
- **v2.4.1** — current recommended build for all models (B2G Pulse, B2G Pulse Pro, B2G Vital).
- **v2.3.8** — legacy build. Known issues: background-scan loop causing rapid battery drain and
  Bluetooth disconnects (see Connectivity SOP TS-04). All members on v2.3.8 should be upgraded.

## Release notes — v2.4.1
- Fixed background-scan loop that caused fast battery drain and repeated disconnects.
- Improved SpO2 sampling stability during sleep.
- Reduced skin-temperature sensor noise.

## How to push an OTA (over-the-air) update
1. Confirm the watch battery is above 40% and on charger.
2. In the app: Settings → Device → Software update → Update to v2.4.1.
3. Keep watch and phone within range; update takes ~8 minutes and the watch reboots once.
4. Verify the reported firmware after reboot.

## Fleet guidance
When a cluster of devices on **v2.3.8** shows elevated BATT-CRIT / disconnect symptoms, run a
coordinated OTA campaign for those members rather than one-off fixes. Cross-reference the
`device_registry.firmware_version` field to identify who is still on v2.3.8.
