# Generate feature availability table

Use when the user asks which GenAI features are available per environment.

1. Config: `configs/feature-availability.yaml` (or `--note <id>`).
2. Run from the gitops repo root:
   ```
   mkdir -p tmp && python3 scripts/generate_tables.py --note <id> --repo . > tmp/out.txt 2>&1
   ```
3. Read `tmp/out.txt` and report it, including the undecided-cell count.
4. Blank cells are intentional — a feature with no explicit true/false flag is
   undecided, never "No". Do not invent flag paths.
