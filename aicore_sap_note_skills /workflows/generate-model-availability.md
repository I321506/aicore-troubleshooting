# Generate model availability tables

Use when the user asks for model / region availability (Help Portal content).

1. Pick the config: `configs/model-availability-external.yaml` (customer-facing)
   or `configs/model-availability-internal.yaml` (SAP internal only). If the
   user gives a note/doc id, use `--note <id>` instead and let the script
   resolve it.
2. Run from the gitops repo root:
   ```
   mkdir -p tmp && python3 scripts/generate_tables.py --note <id> --repo . > tmp/out.txt 2>&1
   ```
3. Read `tmp/out.txt` and report it. Point the user at the generated HTML.
4. Never edit a config to make a run succeed. Report missing folders or
   wrong flag paths and ask.
