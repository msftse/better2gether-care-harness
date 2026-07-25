# Better2gether Alert Code Glossary

This glossary defines every alert code emitted by the Better2gether platform and surfaced
in the `vitals_alerts` data feed. Care-team agents should use this as the authoritative
reference when a member's device raises an alert. Alerts are wellness signals, not medical
diagnoses.

| Alert Code | Metric | Trigger Condition | Severity | Recommended Action |
|------------|--------|-------------------|----------|--------------------|
| SPO2-CRIT | Blood oxygen (SpO2) | Reading below 94.3% | High | Ask member how they feel; if symptomatic (shortness of breath, dizziness) advise contacting a clinician. Review trend over the day. See Vitals Interpretation Guide §2. |
| SPO2-LOW | Blood oxygen (SpO2) | Reading 94.3%–94.9% | Medium | Monitor. Often positional or motion artifact. Confirm the watch is worn snugly. See Vitals Interpretation Guide §2. |
| HR-HIGH | Heart rate | Above 150 bpm while resting or sleeping | Medium | Check for caffeine, stress, or recent activity. Persistent elevated resting HR warrants clinician follow-up. See Vitals Interpretation Guide §1. |
| TEMP-HIGH | Skin temperature | At or above 37.3°C | Low | Skin temp is influenced by environment and activity. Corroborate with other signals before acting. See Vitals Interpretation Guide §3. |
| BATT-LOW | Battery | Below 15% | Low | Prompt member to charge. If battery drains unusually fast, see Connectivity & Sync SOP TS-04. |
| BATT-CRIT | Battery | Below 8% | Medium | Data gaps likely imminent. Member should charge now. Rapid drain may indicate firmware regression — see TS-04 and OTA Update SOP. |

## Reading multiple alerts together
A single reading can raise more than one alert. When BATT-CRIT and SPO2-CRIT co-occur, treat
the SpO2 value with caution — low battery can degrade sensor accuracy (see TS-04). Always
weigh the whole picture rather than one code in isolation.

## Escalation
Codes with severity **High** that persist across three or more readings in a rolling hour
should be escalated per the Wellness Program Handbook escalation ladder.
