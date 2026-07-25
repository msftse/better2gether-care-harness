#!/usr/bin/env bash
# Build + deploy the Care Agent Teams bridge, and produce the Teams app package.
# Prereqs: terraform apply already done in ./iac (this script reads its outputs),
#          dotnet SDK, az CLI logged in.
set -euo pipefail
cd "$(dirname "$0")"

SUB=$(cd iac && terraform output -raw resource_group_name >/dev/null 2>&1 && grep -E '^subscription_id' terraform.tfvars | cut -d'"' -f2)
RG=$(cd iac && terraform output -raw resource_group_name)
APP=$(cd iac && terraform output -raw function_app_name)
BOT_APP_ID=$(cd iac && terraform output -raw bot_app_id)

echo "== 1. Publish the Functions app =="
rm -rf app/out publish.zip
dotnet publish app/CareAgentTeamsBridge.csproj -c Release -o app/out
(cd app/out && zip -qr ../../publish.zip .)

echo "== 2. Zip-deploy to $APP =="
az functionapp deployment source config-zip \
  --subscription "$SUB" -g "$RG" -n "$APP" --src publish.zip

echo "== 3. Build the Teams app package =="
sed "s/__BOT_APP_ID__/$BOT_APP_ID/g" teams-app/manifest.template.json > teams-app/manifest.json
(cd teams-app && rm -f ../care-copilot-teams.zip && zip -q ../care-copilot-teams.zip manifest.json color.png outline.png)

echo
echo "Done."
echo "  Bot app id:        $BOT_APP_ID"
echo "  Teams app package: teams/care-copilot-teams.zip"
echo "Upload the package in Teams: Apps -> Manage your apps -> Upload an app -> Upload a custom app."
