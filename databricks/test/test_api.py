#!/usr/bin/env python3
"""
Test the Care Copilot Supervisor endpoint over REST (the same call Foundry makes).

Fill in HOST, ENDPOINT, and either a bearer TOKEN or SP CLIENT_ID/SECRET.
Run: python3 test_api.py
"""
import requests, json

# ---- EDIT THESE ----
HOST     = "https://adb-xxxx.azuredatabricks.net"     # your workspace host
ENDPOINT = "mas-xxxxxxxx-endpoint"                     # your Supervisor endpoint name

# Auth: either paste a bearer token, or set CLIENT_ID/CLIENT_SECRET to mint one.
TOKEN         = ""                                     # optional: a ready bearer token
CLIENT_ID     = ""                                     # service principal applicationId
CLIENT_SECRET = ""                                     # service principal OAuth secret
# --------------------

def get_token():
    if TOKEN:
        return TOKEN
    r = requests.post(f"{HOST}/oidc/v1/token",
                      auth=(CLIENT_ID, CLIENT_SECRET),
                      data={"grant_type": "client_credentials", "scope": "all-apis"},
                      timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def ask(question, token):
    r = requests.post(f"{HOST}/serving-endpoints/{ENDPOINT}/invocations",
                      headers={"Authorization": f"Bearer {token}",
                               "Content-Type": "application/json"},
                      json={"input": [{"role": "user", "content": question}]},
                      timeout=120)
    r.raise_for_status()
    return r.json()

def final_text(resp):
    out = ""
    for o in resp.get("output", []):
        c = o.get("content")
        if isinstance(c, list):
            for part in c:
                t = part.get("text", "")
                if t and not t.startswith("<name>"):
                    out = t
    return out or json.dumps(resp)[:500]

if __name__ == "__main__":
    tok = get_token()
    print("token OK\n")
    for q in [
        "How many SPO2-CRIT alerts fired, broken down by region?",
        "What does a BATT-CRIT alert mean and what should I do about it?",
        "Member watch-007's oxygen readings look low and the watch keeps disconnecting. "
        "How bad is it and what should I tell them?",
    ]:
        print("Q:", q)
        print("A:", final_text(ask(q, tok))[:400], "\n" + "-"*60)
