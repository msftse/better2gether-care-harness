#!/usr/bin/env python3
"""
Create the Better2gether Care Genie space via the Databricks REST API.

Prereqs:
  - Databricks CLI installed and authenticated to YOUR workspace:
      databricks auth login --host https://<your-workspace-host> --profile care
  - The data foundation already created (run sql/01_setup_data.sql first).

Usage:
  python3 create_genie_space.py --profile care \\
      --warehouse-id <YOUR_SERVERLESS_WAREHOUSE_ID> \\
      --catalog main --schema care_copilot

The script builds the serialized_space payload and POSTs it. It prints the new
space_id — save it; you'll paste it into the Multi-Agent Supervisor.
"""
import argparse, json, subprocess, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="care")
    ap.add_argument("--warehouse-id", required=True, help="Serverless SQL warehouse id")
    ap.add_argument("--catalog", default="better2gether")
    ap.add_argument("--schema", default="care_copilot")
    args = ap.parse_args()

    cat, sch = args.catalog, args.schema
    serialized = {
        "version": 2,
        "data_sources": {
            "tables": [
                {"identifier": f"{cat}.{sch}.device_registry"},
                {"identifier": f"{cat}.{sch}.vitals_alerts"},
            ]
        },
        "instructions": {
            "text_instructions": [{
                # id must be a lowercase 32-hex UUID without hyphens
                "id": "a3f1c9d2b4e64f0a8c7d5e2f1b3a4c5d",
                "content": [
                    "This is a consumer wellness wearables dataset. vitals_alerts holds alert "
                    "events with alert_code in (SPO2-CRIT, SPO2-LOW, HR-HIGH, TEMP-HIGH, "
                    "BATT-LOW, BATT-CRIT) and a severity. device_registry is the device "
                    "dimension; join it to vitals_alerts on device_id to break alerts down by "
                    "region, plan_tier, model, or firmware_version. Devices on firmware v2.3.8 "
                    "are the legacy build with known battery/connectivity issues. Provide "
                    "wellness data only, never a medical diagnosis. Always state grain and filters."
                ],
            }]
        },
        # NOTE: serialized_space v2 rejects a top-level 'sample_questions' field
        # (Unknown field). Add curated/sample questions in the Genie UI after create.
    }

    payload = {
        "title": "Better2gether Care — Vitals & Fleet",
        "description": "Member vitals alerts and device fleet data for the Care Copilot.",
        "warehouse_id": args.warehouse_id,
        "serialized_space": json.dumps(serialized),
    }

    with open("/tmp/_genie_create.json", "w") as f:
        json.dump(payload, f)

    out = subprocess.run(
        ["databricks", "api", "post", "/api/2.0/genie/spaces",
         "--profile", args.profile, "--json", "@/tmp/_genie_create.json"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        print("ERROR:", out.stderr or out.stdout); sys.exit(1)
    resp = json.loads(out.stdout)
    space_id = resp.get("space_id") or resp.get("id")
    print("Genie space created.")
    print("space_id =", space_id)
    print("Open it in the UI (Genie) to verify, then paste this space_id into the Supervisor.")

if __name__ == "__main__":
    main()
