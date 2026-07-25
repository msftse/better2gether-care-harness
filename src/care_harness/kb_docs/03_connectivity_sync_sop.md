# Connectivity & Sync Troubleshooting SOP

Use these procedures when a member reports their Better2gether watch is not syncing, keeps
disconnecting, or shows data gaps. Each procedure has a **TS-** code for reference.

## TS-01: Watch won't pair with the app
1. Confirm Bluetooth is enabled on the phone.
2. In the app, go to Devices → Forget device, then re-add.
3. Restart the watch (hold side button 10s).
4. If pairing still fails on a **B2G Pulse** (first-gen), confirm the phone OS meets minimum version.

## TS-02: Intermittent disconnects during the day
1. Check that the watch is within 10m of the phone during sync windows.
2. Disable phone battery-optimization/"deep sleep" for the Better2gether app.
3. Confirm firmware is current (see OTA Update SOP). Disconnect loops were common on **v2.3.8**
   and are resolved in **v2.4.1**.

## TS-03: Data gaps / missing hours of readings
1. Data gaps usually follow a battery depletion event (see BATT-CRIT) or a disconnect loop (TS-02).
2. Confirm the watch charged above 15% overnight.
3. Force a manual sync: app → Devices → Sync now.

## TS-04: Rapid battery drain + repeated disconnects
This is the classic combined symptom. Root cause is most often a firmware regression on
older builds.
1. Check firmware version. If **v2.3.8**, push the OTA update to **v2.4.1** (see OTA Update SOP).
   v2.4.1 fixes the background-scan loop that caused both fast drain and disconnects.
2. If already on v2.4.1 and drain persists, initiate a battery-health RMA (see Warranty & RMA Policy).
3. Advise the member that SpO2 accuracy can be reduced while battery is critically low, so any
   SPO2-LOW/SPO2-CRIT alerts during a drain event should be re-confirmed after charging.

## TS-05: GPS not recording routes
1. Grant the app "precise location, always" permission.
2. Ensure outdoor line-of-sight for first GPS lock (up to 60s).
