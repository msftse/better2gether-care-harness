#!/usr/bin/env bash
# Grant a service principal least-privilege access to run the Care Copilot Supervisor.
# The Supervisor runs each tool AS THE CALLER, so the SP needs the endpoint AND
# everything the tools reach (KA endpoint, Genie space, catalog/schema/SELECT, warehouse).
#
# Fill in the IDs below, then run:  bash grant_sp.sh
set -euo pipefail

PROFILE="care"                              # your CLI profile
SP_APP_ID="<SP_applicationId>"              # service principal applicationId (client_id)
MAS_ENDPOINT_ID="<supervisor_endpoint_id>"  # Serving endpoint id of the Supervisor
KA_ENDPOINT_ID="<ka_endpoint_id>"           # Serving endpoint id of the Knowledge Assistant
GENIE_SPACE_ID="<genie_space_id>"
CATALOG="main"
SCHEMA="care_copilot"
WAREHOUSE_ID="<serverless_warehouse_id>"

echo "CAN_QUERY on Supervisor endpoint"
databricks serving-endpoints update-permissions "$MAS_ENDPOINT_ID" --profile "$PROFILE" \
  --json "{\"access_control_list\":[{\"service_principal_name\":\"$SP_APP_ID\",\"permission_level\":\"CAN_QUERY\"}]}"

echo "CAN_QUERY on Knowledge Assistant endpoint"
databricks serving-endpoints update-permissions "$KA_ENDPOINT_ID" --profile "$PROFILE" \
  --json "{\"access_control_list\":[{\"service_principal_name\":\"$SP_APP_ID\",\"permission_level\":\"CAN_QUERY\"}]}"

echo "CAN_RUN on Genie space"
databricks api patch "/api/2.0/permissions/genie/$GENIE_SPACE_ID" --profile "$PROFILE" \
  --json "{\"access_control_list\":[{\"service_principal_name\":\"$SP_APP_ID\",\"permission_level\":\"CAN_RUN\"}]}"

echo "USE_CATALOG"
databricks grants update catalog "$CATALOG" --profile "$PROFILE" \
  --json "{\"changes\":[{\"principal\":\"$SP_APP_ID\",\"add\":[\"USE_CATALOG\"]}]}"

echo "USE_SCHEMA + SELECT"
databricks grants update schema "$CATALOG.$SCHEMA" --profile "$PROFILE" \
  --json "{\"changes\":[{\"principal\":\"$SP_APP_ID\",\"add\":[\"USE_SCHEMA\",\"SELECT\"]}]}"

echo "CAN_USE on warehouse"
databricks warehouses update-permissions "$WAREHOUSE_ID" --profile "$PROFILE" \
  --json "{\"access_control_list\":[{\"service_principal_name\":\"$SP_APP_ID\",\"permission_level\":\"CAN_USE\"}]}"

echo "Done. Test with test_api.py using the SP client_id/secret."
