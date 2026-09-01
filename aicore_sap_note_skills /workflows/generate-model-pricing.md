# Generate model pricing table

Use when the user asks for model pricing / retirement metadata (SAP note content).

1. Config: `configs/model-pricing.yaml` (or `--note <id>`).
2. Run from the gitops repo root:
   ```
   mkdir -p tmp && python3 scripts/generate_tables.py --note <id> --repo . > tmp/out.txt 2>&1
   ```
3. Read `tmp/out.txt` and report it. If a column is reported empty for ALL
   models, the report prints the real field names — propose a config fix and
   ask before editing.
