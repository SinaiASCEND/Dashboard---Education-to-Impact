#!/usr/bin/env python3
"""build.py: refresh the public Strategic Plan site and its SharePoint working files from the OneDrive master.

    python3 tools/build.py            # rewrite data/e2i-data.js and the two working files
    python3 tools/build.py --master DIR

Master folder (OneDrive): # Dashboards/22 Strategic Plan/2 MASTER - Claude only/
    e2i-data.json   the full record: gaps, milestones, members, actions, meetings, minutes, materials
    links.json      SharePoint "People in Mount Sinai" links listed on the Working files tab
    docs/gap-report.html   printed to files/<GAP_PDF>

The site is public (GitHub Pages), so only gaps and milestones reach it. Members, actions, meetings,
minutes and materials go to files/<WORKBOOK>, which people open from SharePoint with a Mount Sinai
sign-in. Both working files are rewritten in place, so their SharePoint links keep working.
"""
import argparse, io, json, os, pathlib, subprocess, sys, tempfile
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.expanduser("~/Library/CloudStorage/OneDrive-TheMountSinaiHospital/Curricular Affairs - Documents/"
                            "# Dashboards/22 Strategic Plan/2 MASTER - Claude only")
WORKBOOK = "Strategic Plan working details - G2.2 and G3.1.xlsx"
GAP_PDF = "Curriculum Gap Report - Phases 1 and 2 - October 2026.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

GAP_FIELDS = ("topic", "area", "type", "route", "priority", "evidence", "decision", "owner", "notes", "order", "_id")
MS_FIELDS = ("kpi", "due", "title", "done_when", "status", "owner", "seq", "_id")
SHEETS = {
    "Members": ("members", [("initiative", "Initiative"), ("kind", "Role in this work"), ("name", "Name"), ("role", "Title"),
                            ("seat", "What this person owns"), ("status", "Status"), ("email", "Email"), ("notes", "Notes")]),
    "Actions": ("actions", [("due", "Due"), ("title", "Action"), ("owner", "Owner"), ("initiative", "Initiative"),
                            ("status", "Status"), ("source", "Source"), ("notes", "Notes"), ("links", "Links")]),
    "Meetings": ("meetings", [("date", "Date"), ("time", "Time"), ("title", "Meeting"), ("kind", "Type"), ("status", "Status"),
                              ("where", "Where"), ("summary", "Summary"), ("decisions", "Decisions and outcomes"),
                              ("followups", "Follow-ups"), ("materials", "Materials"), ("links", "Links")]),
    "Minutes": ("minutes", [("date", "Meeting date"), ("title", "Meeting"), ("group", "Group"), ("status", "Status"),
                            ("summary", "Summary"), ("decisions", "Decisions"), ("actions", "Action items"),
                            ("where", "Where the file lives"), ("pdf", "File")]),
    "Materials": ("materials", [("date", "Date"), ("name", "Item"), ("kind", "Type"), ("where", "Where it lives"),
                                ("notes", "Notes")]),
}


def write_in_place(path, data):
    """Overwrite the existing file's bytes so OneDrive keeps the same item (and its sharing link)."""
    with open(path, "wb") as f:
        f.write(data)


def workbook(data, file_links):
    wb = Workbook(); wb.remove(wb.active)
    for title, (key, cols) in SHEETS.items():
        ws = wb.create_sheet(title)
        ws.append([c[1] for c in cols])
        rows = sorted(data[key], key=lambda r: (str(r.get("initiative", "")), r.get("order", 99)) if key == "members"
                      else str(r.get("date") or r.get("due") or ""), reverse=key in ("meetings", "minutes"))
        for r in rows:
            vals = []
            for k, _ in cols:
                v = r.get(k, "")
                if k == "pdf" and v:  # /files/x.pdf on the old site -> its SharePoint link
                    v = file_links.get(os.path.basename(v), os.path.basename(v))
                vals.append("" if v is None else v)
            ws.append(vals)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor="1B2A5A")
        for row in ws.iter_rows(min_row=2):
            for cell in row: cell.alignment = Alignment(wrap_text=True, vertical="top")
        for i, (k, _) in enumerate(cols):
            ws.column_dimensions[ws.cell(1, i + 1).column_letter].width = 48 if k in (
                "summary", "decisions", "notes", "seat", "followups", "materials", "evidence", "where", "actions", "title") else 18
        ws.freeze_panes = "A2"
    buf = io.BytesIO(); wb.save(buf); return buf.getvalue()


def gap_pdf(html):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "gap.pdf")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", pathlib.Path(html).as_uri()], check=True, capture_output=True)
        return open(out, "rb").read()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--master", default=MASTER); a = ap.parse_args()
    data = json.load(open(os.path.join(a.master, "e2i-data.json"), encoding="utf-8"))
    for k in ("gaps", "milestones") + tuple(v[0] for v in SHEETS.values()):
        if not isinstance(data.get(k), list): sys.exit(f"e2i-data.json: '{k}' missing")
    lp = os.path.join(a.master, "links.json")
    links = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else []
    file_links = {l["file"]: l["url"] for l in links if l.get("file") and l.get("url")}

    public = {"generated": data.get("generated", ""),
              "gaps": [{k: g[k] for k in GAP_FIELDS if k in g} for g in data["gaps"]],
              "milestones": [{k: m[k] for k in MS_FIELDS if k in m} for m in data["milestones"]],
              "emerging": [{k: e[k] for k in ("topic", "why", "strength", "status", "order", "_id") if k in e} for e in data.get("emerging", [])],
              "links": [{k: l[k] for k in ("name", "kind", "date", "url", "format", "note") if k in l} for l in links if l.get("url")]}
    blob = json.dumps(public, ensure_ascii=False)
    for bad in ("@mssm.edu", "@mountsinai.org", "/files/", "/docs/"):
        if bad in blob: sys.exit(f"public data still contains {bad!r}; it belongs in the working files, not the public site")
    with open(os.path.join(HERE, "data", "e2i-data.js"), "w", encoding="utf-8") as f:
        f.write("/* From Education to Impact public data. Generated by tools/build.py from the OneDrive master; do not edit by hand. */\n")
        f.write("window.E2I_DATA = " + blob + ";\n")

    files = os.path.join(a.master, "files")
    write_in_place(os.path.join(files, WORKBOOK), workbook(data, file_links))
    write_in_place(os.path.join(files, GAP_PDF), gap_pdf(os.path.join(a.master, "docs", "gap-report.html")))
    print("data/e2i-data.js:", {k: len(v) for k, v in public.items() if isinstance(v, list)},
          "| wrote", WORKBOOK, "and", GAP_PDF)


if __name__ == "__main__":
    main()
