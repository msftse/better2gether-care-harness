# Databricks notebook source
# MAGIC %md
# MAGIC # Upload Care KB docs to the Volume
# MAGIC Run this notebook AFTER `01_setup_data.sql` has created the volume
# MAGIC `better2gether.care_copilot.care_kb`. It writes the 8 knowledge-base markdown files
# MAGIC (shipped alongside this kit in the `kb_docs/` folder) into the volume so the
# MAGIC Knowledge Assistant can index them.
# MAGIC
# MAGIC **Two ways to get the docs into the volume:**
# MAGIC 1. **UI (easiest):** Catalog Explorer → `better2gether.care_copilot.care_kb` volume →
# MAGIC    Upload → drag in all 8 files from the `kb_docs/` folder. Then skip this notebook.
# MAGIC 2. **This notebook:** paste each file's contents into the DOCS dict below (or
# MAGIC    upload the kb_docs folder to your workspace and point WORKSPACE_DIR at it).

# COMMAND ----------

CATALOG = "better2gether"
SCHEMA  = "care_copilot"
VOLUME  = "care_kb"
VOL_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Option B — copy from a workspace folder
# MAGIC Upload the `kb_docs/` folder (8 .md files) to your workspace, then set the path:

# COMMAND ----------

import os, shutil

# EDIT: point this at wherever you put the kb_docs folder (workspace files or a repo)
WORKSPACE_DIR = "/Workspace/Users/<you>@<company>.com/care_copilot_kit/kb_docs"

try:
    files = [f for f in os.listdir(WORKSPACE_DIR) if f.endswith(".md")]
    for f in files:
        shutil.copyfile(os.path.join(WORKSPACE_DIR, f), os.path.join(VOL_PATH, f))
    print("Uploaded:", files)
except FileNotFoundError:
    print(f"WORKSPACE_DIR not found: {WORKSPACE_DIR}")
    print("Edit WORKSPACE_DIR above, or just upload the 8 files via Catalog Explorer UI.")

# COMMAND ----------

# Verify
print(os.listdir(VOL_PATH))
