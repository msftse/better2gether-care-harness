#!/usr/bin/env bash
# Create the Agent Bricks agents via REST API — no UI needed.
# (Omri's kit says Agent Bricks is UI-only; that's outdated. The tile APIs are live:
#   POST /api/2.1/knowledge-assistants               — create KA
#   POST /api/2.1/knowledge-assistants/{id}/knowledge-sources
#   POST /api/2.0/multi-agent-supervisors            — create Supervisor
# Names must be alphanumeric + _ / - only.)
#
# Usage: bash create_agents_api.sh <profile> <genie_space_id>
set -euo pipefail

PROFILE="${1:?profile}"; GENIE_SPACE_ID="${2:?genie space id}"
VOL="/Volumes/better2gether/care_copilot/care_kb"

echo "== 1. Knowledge Assistant =="
KA=$(databricks api post /api/2.1/knowledge-assistants --profile "$PROFILE" --json '{
  "display_name": "Care_KB_Assistant",
  "description": "Better2gether wearable care knowledge base: alert-code glossary, vitals interpretation, connectivity & firmware/OTA SOPs, device setup, warranty/RMA, privacy, and the wellness handbook.",
  "instructions": "You are Better2gether'\''s Care Knowledge Assistant. Answer care-team questions using only the provided documentation.\n- Always cite the source doc (and the TS-code or alert code) you used.\n- Provide wellness guidance only — never a medical diagnosis.\n- For device faults, give the matching TS- procedure and check firmware first: v2.3.8 issues are usually fixed by updating to v2.4.1 before an RMA.\n- Be concise and actionable."
}')
KA_ID=$(echo "$KA" | python3 -c "import json,sys; print(json.load(sys.stdin,strict=False)['id'])")
KA_EP=$(echo "$KA" | python3 -c "import json,sys; print(json.load(sys.stdin,strict=False)['endpoint_name'])")
echo "KA tile_id=$KA_ID endpoint=$KA_EP"

echo "== 2. Attach knowledge source ($VOL) =="
databricks api post "/api/2.1/knowledge-assistants/$KA_ID/knowledge-sources" --profile "$PROFILE" --json "{
  \"display_name\": \"care_kb_docs\",
  \"description\": \"Knowledge source from $VOL\",
  \"source_type\": \"files\",
  \"files\": {\"path\": \"$VOL\"}
}" > /dev/null && echo "source attached (indexing starts automatically)"

echo "== 3. Wait for KA state=ACTIVE =="
while :; do
  ST=$(databricks api get "/api/2.1/knowledge-assistants/$KA_ID" --profile "$PROFILE" | python3 -c "import json,sys; print(json.load(sys.stdin,strict=False).get('state',''))")
  echo "  state=$ST"; [ "$ST" = "ACTIVE" ] && break; sleep 20
done

echo "== 4. Multi-Agent Supervisor =="
MAS=$(databricks api post /api/2.0/multi-agent-supervisors --profile "$PROFILE" --json "{
  \"name\": \"Care_Copilot\",
  \"description\": \"Better2gether Care Copilot — combines member and fleet data (Genie) and our care documentation (Knowledge Assistant) into one cited answer. Wellness support, never medical diagnosis.\",
  \"instructions\": \"You are Better2gether's Care Copilot for care-team agents. You have these tools:\n- Genie: our member and fleet data — vitals, device registry, and vitals_alerts.\n- Knowledge Assistant: our care documentation — alert meanings, fixes, and policies.\n\nRules:\n- Pick the right tool(s); many questions need more than one. Combine the numbers with the meaning.\n- Always cite the source of every part of your answer.\n- Provide wellness guidance only — never a medical diagnosis.\",
  \"agents\": [
    {\"name\": \"vitals_fleet_data\", \"description\": \"Our member vitals, alerts, and fleet data: device registry and vitals_alerts tables. Use for counts, breakdowns, per-device stats, firmware campaigns.\", \"agent_type\": \"genie\", \"genie_space\": {\"id\": \"$GENIE_SPACE_ID\"}},
    {\"name\": \"care_kb\", \"description\": \"How-to guidance, alert-code meanings, troubleshooting fixes (TS- procedures), firmware/OTA, warranty/RMA and privacy policies from the care documentation.\", \"agent_type\": \"serving_endpoint\", \"serving_endpoint\": {\"name\": \"$KA_EP\"}}
  ]
}")
echo "$MAS" | python3 -c "import json,sys; d=json.load(sys.stdin,strict=False); print('MAS:', json.dumps(d)[:400])"
