#!/usr/bin/env python3
"""
Generic SAP availability table generator (SAP Help Portal / SAP note content).

Reads only the gitops repository — no SAP note / MCP dependency.

Config patterns
  A) model catalog        : `table1:` present  -> model metadata / pricing table
  B) region availability  : `table2:` present  -> model x region matrices,
                            optionally split into region groups, and optionally
                            split into hosted vs cross-region tables
  C) feature flags        : `features:` present -> feature x environment matrix

Usage
  python3 scripts/generate_tables.py --note <sap-note-id> --repo .
  python3 scripts/generate_tables.py --config configs/<file>.yaml --repo .
  python3 scripts/generate_tables.py --all --repo .
Options
  --service-plan extended|sap-internal   (catalog/region configs)
  --no-open                              do not open generated HTML
"""
import argparse
import csv
import html
import io
import subprocess
import sys
from pathlib import Path

import yaml


# ---------- yaml loading ----------

class _PermissiveLoader(yaml.SafeLoader):
    """SafeLoader that tolerates unknown custom tags (e.g. !HumanInput)."""


def _unknown_tag(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


_PermissiveLoader.add_multi_constructor("!", _unknown_tag)
_PermissiveLoader.add_multi_constructor("tag:", _unknown_tag)


def _safe_load(text):
    return yaml.load(text, Loader=_PermissiveLoader)


# ---------- helpers ----------

def get_path(obj, dotted, default=""):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return default if cur is None else cur


def apply_transform(value, transform):
    if not transform:
        return value
    if transform.startswith("contains:"):
        needle = transform.split(":", 1)[1].lower()
        hay = ([str(v).lower() for v in value]
               if isinstance(value, (list, tuple)) else [str(value).lower()])
        return "yes" if any(needle in v for v in hay) else ""
    return value


def as_cell(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def contains_value(container, needle):
    if container is None:
        return False
    if isinstance(container, (list, tuple)):
        return any(str(v).lower() == str(needle).lower() for v in container)
    return str(needle).lower() in str(container).lower()


def truthy(v):
    """True / False, or None when the value cannot decide a flag."""
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("true", "yes", "enabled", "on", "1"):
        return True
    if s in ("false", "no", "disabled", "off", "0"):
        return False
    return None


def env_yaml_path(cfg, repo, folder):
    cluster_dir = repo / cfg["sources"]["cluster_dir"]
    tmpl = cfg["sources"].get("env_file_template")
    if tmpl:
        return cluster_dir / tmpl.format(env=folder)
    return cluster_dir / folder / cfg["sources"].get("env_yaml_name", "main.yaml")


def open_in_browser(paths):
    if sys.platform == "darwin":
        opener = ["open"]
    elif sys.platform.startswith("win"):
        opener = ["cmd", "/c", "start", ""]
    else:
        opener = ["xdg-open"]
    for p in paths:
        try:
            subprocess.run(opener + [str(p)], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


# ---------- writers ----------

EMITTED_HTML = []


def write_md(path, headers, rows):
    with open(path, "w", encoding="utf-8") as f:
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
        for r in rows:
            f.write("| " + " | ".join(c if c else " " for c in r) + " |\n")


def write_csv(path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


HTML_STYLE = """
<style>
  body { font-family: Arial, sans-serif; margin: 16px; }
  h2 { font-size: 17px; margin: 0 0 4px; }
  h3 { font-size: 14px; margin: 22px 0 4px; }
  p.note { font-size: 12px; color: #555; margin: 2px 0 10px; }
  table { border-collapse: collapse; font-size: 12px; margin-bottom: 18px; }
  th, td { border: 1px solid #999; padding: 3px 7px; white-space: nowrap; }
  thead th { background: #e8eef7; position: sticky; top: 0; }
  tbody td:nth-child(-n+3) { background: #fafafa; }
  .yes { background: #e6f4e6; text-align: center; }
  .no  { background: #f7e4e4; text-align: center; }
  .xr  { background: #fdf3d8; text-align: center; }
</style>
"""


def _cell_class(v):
    s = str(v).strip().lower()
    if s == "yes":
        return " class='yes'"
    if s == "no":
        return " class='no'"
    if s.startswith("yes"):          # Yes* = cross-region
        return " class='xr'"
    return ""


def render_table(headers, rows):
    b = io.StringIO()
    b.write("<table><thead><tr>")
    for h in headers:
        b.write(f"<th>{html.escape(h)}</th>")
    b.write("</tr></thead><tbody>")
    for r in rows:
        b.write("<tr>")
        for c in r:
            b.write(f"<td{_cell_class(c)}>{html.escape(str(c))}</td>")
        b.write("</tr>")
    b.write("</tbody></table>")
    return b.getvalue()


def write_html_sections(path, title, sections, note=""):
    """sections: list of (subtitle, headers, rows, subnote)."""
    b = io.StringIO()
    b.write(f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{html.escape(title)}</title>{HTML_STYLE}</head><body>")
    b.write(f"<h2>{html.escape(title)}</h2>")
    if note:
        b.write(f"<p class='note'>{html.escape(note)}</p>")
    for subtitle, headers, rows, subnote in sections:
        if subtitle:
            b.write(f"<h3>{html.escape(subtitle)}</h3>")
        if subnote:
            b.write(f"<p class='note'>{html.escape(subnote)}</p>")
        b.write(render_table(headers, rows))
    b.write("</body></html>")
    path.write_text(b.getvalue(), encoding="utf-8")
    EMITTED_HTML.append(path)


def emit(outdir, name, title, headers, rows, formats, note=""):
    emit_sections(outdir, name, title, [(None, headers, rows, "")], formats, note)


def emit_sections(outdir, name, title, sections, formats, note=""):
    if "md" in formats:
        with open(outdir / f"{name}.md", "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            if note:
                f.write(note + "\n\n")
            for subtitle, headers, rows, subnote in sections:
                if subtitle:
                    f.write(f"## {subtitle}\n\n")
                if subnote:
                    f.write(subnote + "\n\n")
                f.write("| " + " | ".join(headers) + " |\n")
                f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
                for r in rows:
                    f.write("| " + " | ".join(c if c else " " for c in r) + " |\n")
                f.write("\n")
    if "csv" in formats:
        if len(sections) == 1:
            write_csv(outdir / f"{name}.csv", sections[0][1], sections[0][2])
        else:
            for subtitle, headers, rows, _ in sections:
                slug = "".join(ch if ch.isalnum() else "-" for ch in (subtitle or "all")).strip("-").lower()
                write_csv(outdir / f"{name}-{slug}.csv", headers, rows)
    if "html" in formats:
        write_html_sections(outdir / f"{name}.html", title, sections, note)


# ---------- catalog / region note ----------

def load_metadata(cfg, repo):
    gpath = repo / cfg["sources"]["global_yaml"]
    if not gpath.exists():
        sys.exit(f"ERROR: {gpath} not found. Wrong --repo or config path?")
    gdata = _safe_load(gpath.read_text(encoding="utf-8"))
    metas = get_path(gdata, cfg["sources"]["metadata_key"], default=None)
    if metas is None:
        sys.exit(f"ERROR: key '{cfg['sources']['metadata_key']}' not found in {gpath}. "
                 f"Top-level keys: {list(gdata)[:20]}")
    if isinstance(metas, dict):
        metas = list(metas.values())
    return metas


def select_by_plan(cfg, metas, sp_mode):
    f = cfg.get("filters", {})
    sp_field = f.get("service_plan_field", "servicePlan")
    exclusive = f.get("exclusive_against", "extended")

    def ok(m):
        plans = get_path(m, sp_field, None)
        if sp_mode == exclusive:
            return contains_value(plans, sp_mode)
        return contains_value(plans, sp_mode) and not contains_value(plans, exclusive)

    return [m for m in metas if ok(m)]


def build_table1(cfg, selected, warnings):
    cols = cfg["table1"]["columns"]
    headers = [c["title"] for c in cols]
    rows = []
    for m in selected:
        row = []
        for c in cols:
            for cand in (c.get("fields") or [c["field"]]):
                v = get_path(m, cand, "")
                if v != "":
                    break
            row.append(as_cell(apply_transform(v, c.get("transform"))))
        rows.append(row)
    if selected:
        for i, c in enumerate(cols):
            if all(r[i] == "" for r in rows):
                warnings.append(
                    f"Table 1 column '{c['title']}' is empty for ALL models — check its "
                    f"field path(s). Sample model keys: {sorted(selected[0].keys())}")
    return headers, rows


def scan_regions(cfg, repo, warnings, missing):
    """region short -> {identity: hosted_bool} where hosted_bool False = cross-region."""
    cf = cfg["table2"]["connection_fields"]
    ckey = cfg["sources"]["connections_key"]
    xr_field = cfg["table2"].get("cross_region_field")
    out = {}
    for region in cfg["regions"]:
        short, folder = region["short"], region["folder"]
        if folder == "TODO":
            warnings.append(f"region {short}: folder mapping still TODO in config")
            out[short] = {}
            continue
        ypath = env_yaml_path(cfg, repo, folder)
        if not ypath.exists():
            missing.append(f"{short} -> {folder}")
            out[short] = {}
            continue
        ydata = _safe_load(ypath.read_text(encoding="utf-8")) or {}
        conns = get_path(ydata, ckey, default=[]) or []
        if isinstance(conns, dict):
            conns = list(conns.values())
        found = {}
        for conn in conns:
            ident = (as_cell(get_path(conn, cf["executable_id"])),
                     as_cell(get_path(conn, cf["model"])),
                     as_cell(get_path(conn, cf["version"])))
            hosted = True
            if xr_field:
                xr = truthy(get_path(conn, xr_field, None))
                if xr is True:          # flag marks cross-region access
                    hosted = False
            found[ident] = hosted
        out[short] = found
    return out


def region_sections(cfg, identities, region_models, mode):
    """mode: 'all' | 'hosted' | 'cross'. Returns list of (subtitle, headers, rows, note)."""
    groups = cfg.get("region_groups")
    if not groups:
        groups = [{"name": None, "regions": [r["short"] for r in cfg["regions"]]}]
    id_cols = ["Executable ID (Access Type)", "Model", "Version"]
    sections = []
    for g in groups:
        shorts = [s for s in g["regions"] if s in region_models]
        headers = id_cols + shorts
        rows = []
        for ident in identities:
            row = list(ident)
            any_mark = False
            for s in shorts:
                hosted = region_models[s].get(ident)
                cell = ""
                if hosted is True:
                    cell = "Yes" if mode in ("all", "hosted") else ""
                elif hosted is False:
                    if mode == "all":
                        cell = "Yes*"
                    elif mode == "cross":
                        cell = "Yes"
                if cell:
                    any_mark = True
                row.append(cell)
            if any_mark or mode == "all":
                rows.append(row)
        if rows:
            sections.append((g.get("name"), headers, rows, g.get("note", "")))
    return sections


def run_catalog_or_region(cfg, repo, outdir, formats, warnings, args):
    metas = load_metadata(cfg, repo)
    sp_mode = args.service_plan or cfg.get("filters", {}).get("service_plan_default", "extended")
    selected = select_by_plan(cfg, metas, sp_mode) if cfg.get("filters") else metas
    report = [f"Service plan mode: {sp_mode} — {len(selected)} of {len(metas)} models selected"]
    out_name = cfg["output"].get("name", "table")
    title = cfg["output"].get("title", "SAP AI Core availability")

    if "table1" in cfg:
        headers, rows = build_table1(cfg, selected, warnings)
        emit(outdir, out_name, title, headers, rows, formats,
             note=cfg["output"].get("note", ""))
        report.append(f"Metadata table: {len(rows)} rows x {len(headers)} columns")

    if "table2" in cfg:
        missing = []
        region_models = scan_regions(cfg, repo, warnings, missing)
        all_ids = {(as_cell(get_path(m, "provider")), as_cell(get_path(m, "name")),
                    as_cell(get_path(m, "version"))) for m in metas}
        identities = [(as_cell(get_path(m, "provider")), as_cell(get_path(m, "name")),
                       as_cell(get_path(m, "version"))) for m in selected]
        for s, found in region_models.items():
            for ident in found:
                if ident not in all_ids:
                    warnings.append(f"{s}: model {ident} in cluster yaml but not in metadata")

        split = cfg["table2"].get("split_hosted_cross_region", False)
        if split:
            secs_h = region_sections(cfg, identities, region_models, "hosted")
            secs_x = region_sections(cfg, identities, region_models, "cross")
            emit_sections(outdir, f"{out_name}-hosted",
                          f"{title} — hosted in the data centre", secs_h, formats,
                          note="Models physically hosted in the listed region's data centre.")
            emit_sections(outdir, f"{out_name}-cross-region",
                          f"{title} — accessed cross-region", secs_x, formats,
                          note="Models usable from the listed region but hosted elsewhere. "
                               "Relevant where data residency restrictions apply.")
            report.append(f"Region tables: hosted ({len(secs_h)} groups), "
                          f"cross-region ({len(secs_x)} groups)")
        else:
            secs = region_sections(cfg, identities, region_models, "all")
            emit_sections(outdir, f"{out_name}-regions", f"{title} — region availability",
                          secs, formats,
                          note="Yes = hosted in that region. Yes* = accessible from that "
                               "region but hosted elsewhere." if cfg["table2"].get("cross_region_field")
                               else "Yes = available in that region.")
            report.append(f"Region tables: {len(secs)} group(s), {len(identities)} models")
        if missing:
            report.append("Missing environment folders: " + ", ".join(missing))
    return report


# ---------- feature note ----------

def run_features(cfg, repo, outdir, formats, warnings):
    feats = cfg["features"]
    groups = cfg.get("region_groups") or [
        {"name": None, "regions": [r["short"] for r in cfg["regions"]]}]
    missing, undecided = [], []

    gdata = None
    gpath_cfg = cfg["sources"].get("global_yaml")
    if gpath_cfg and (repo / gpath_cfg).exists():
        gdata = _safe_load((repo / gpath_cfg).read_text(encoding="utf-8")) or {}

    env_data = {}
    for region in cfg["regions"]:
        short, folder = region["short"], region["folder"]
        if folder == "TODO":
            warnings.append(f"region {short}: folder mapping still TODO in config")
            env_data[short] = None
            continue
        p = env_yaml_path(cfg, repo, folder)
        if not p.exists():
            missing.append(f"{short} -> {folder}")
            env_data[short] = None
            continue
        env_data[short] = _safe_load(p.read_text(encoding="utf-8")) or {}

    def resolve(data, paths):
        for path in paths:
            v = get_path(data, path, None)
            if v is not None and v != "":
                tv = truthy(v)
                if tv is not None:
                    return tv
        return None

    sections = []
    for g in groups:
        shorts = [s for s in g["regions"] if s in env_data]
        headers = ["Feature"] + shorts
        rows = []
        for f in feats:
            row = [f["title"]]
            for s in shorts:
                d = env_data.get(s)
                if d is None:
                    row.append("")
                    continue
                val = resolve(d, f.get("paths", []))
                if val is None and gdata is not None:
                    val = resolve(gdata, f.get("global_paths", f.get("paths", [])))
                if val is None:
                    undecided.append(f"{f['title']} @ {s}")
                    row.append("")
                else:
                    row.append("Yes" if val else "No")
            rows.append(row)
        sections.append((g.get("name"), headers, rows, g.get("note", "")))

    emit_sections(outdir, cfg["output"].get("name", "feature-availability"),
                  cfg["output"].get("title", "Feature availability per environment"),
                  sections, formats,
                  note="Yes / No are set only by an explicit flag in the cluster "
                       "configuration. A blank cell means no explicit flag exists.")

    report = [f"Feature matrix: {len(feats)} features x "
              f"{sum(len(s[1]) - 1 for s in sections)} environment columns "
              f"across {len(sections)} group(s)"]
    if missing:
        report.append("Missing environment files: " + ", ".join(missing))
    if undecided:
        report.append(f"Undecided cells (no explicit flag, left blank): {len(undecided)}")
        report += [f"  ? {u}" for u in undecided[:30]]
        if len(undecided) > 30:
            report.append(f"  ... and {len(undecided) - 30} more")
    return report


# ---------- driver ----------

def run_config(config_path, args):
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    repo = Path(args.repo)
    outdir = repo / cfg["output"].get("dir", "output")
    outdir.mkdir(parents=True, exist_ok=True)
    formats = cfg["output"].get("formats", ["md", "csv", "html"])
    warnings = []

    if "features" in cfg:
        report = run_features(cfg, repo, outdir, formats, warnings)
    else:
        report = run_catalog_or_region(cfg, repo, outdir, formats, warnings, args)

    if warnings:
        report.append("Warnings:")
        report += [f"  - {w}" for w in warnings[:30]]
        if len(warnings) > 30:
            report.append(f"  ... and {len(warnings) - 30} more")
    text = "\n".join(report)
    (outdir / f"report-{cfg['note']['name']}.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


def resolve_by_note(note_id, configs_dir):
    candidates = {}
    for p in sorted(Path(configs_dir).glob("*.yaml")):
        try:
            c = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        nid = str(((c.get("note") or {}).get("sap_note_id") or "")).strip()
        if nid:
            candidates.setdefault(nid, []).append(p)
    hits = candidates.get(str(note_id), [])
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        sys.exit(f"ERROR: several configs claim note {note_id}: "
                 f"{', '.join(p.name for p in hits)}. Note ids must be unique.")
    known = ", ".join(f"{k} -> {v[0].name}" for k, v in sorted(candidates.items())) or "none"
    sys.exit(f"ERROR: no config with note.sap_note_id={note_id} in {configs_dir}/. "
             f"Known notes: {known}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="path to a config yaml")
    ap.add_argument("--note", help="SAP note id — resolves the matching config")
    ap.add_argument("--all", action="store_true", help="run every config in --configs-dir")
    ap.add_argument("--configs-dir", default="configs")
    ap.add_argument("--repo", default=".", help="gitops repo root")
    ap.add_argument("--service-plan", default=None,
                    help="extended (external) or sap-internal (internal only)")
    ap.add_argument("--no-open", action="store_true", help="don't open generated HTML")
    args = ap.parse_args()

    if args.all:
        paths = sorted(Path(args.configs_dir).glob("*.yaml"))
        if not paths:
            sys.exit(f"ERROR: no configs found in {args.configs_dir}/")
        for p in paths:
            print(f"=== {p.name} ===")
            try:
                run_config(p, args)
            except SystemExit as e:
                print(f"  SKIPPED: {e}")
            print()
    else:
        config_path = args.config
        if not config_path:
            if not args.note:
                ap.error("provide --config <file>, --note <sap-note-id>, or --all")
            config_path = resolve_by_note(args.note, args.configs_dir)
        run_config(config_path, args)

    for p in EMITTED_HTML:
        print(f"HTML: {p}")
    if not args.no_open:
        open_in_browser(EMITTED_HTML)


if __name__ == "__main__":
    main()
