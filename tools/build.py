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

GAP_FIELDS = ("topic", "area", "type", "route", "priority", "tier_label", "usmle", "basis", "evidence", "decision", "owner", "notes", "order", "_id")
MS_FIELDS = ("kpi", "due", "title", "done_when", "status", "owner", "seq", "_id")
MIN_FIELDS = ("date", "title", "group", "status", "present", "absent", "next", "decision_list", "action_items", "official", "summary_page", "_id")
MEMBER_FIELDS = ("initiative", "kind", "name", "role", "seat", "photo", "order", "_id")
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
                if isinstance(v, (list, dict)): v = json.dumps(v, ensure_ascii=False)
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


STYLED = os.path.expanduser("~/Library/CloudStorage/OneDrive-TheMountSinaiHospital/Curricular Affairs - Documents/"
                            "# RPS/# Strategic Plan - From Education to Impact/Styled pages")
CHARTERS = {"g22-charter.html": "G2.2 Charter", "g31-charter.html": "G3.1 Charter"}
CHARTER_LINKS = [{"name": label, "kind": "Charter", "url": f"docs/{fn}", "format": "Web page", "date": "2026-11-03",
                  "note": "Latest version. One charter per group; earlier drafts and the Year 1 charter workbook are not listed"} for fn, label in CHARTERS.items()]


# The G3.1 kickoff guides in kickoff/ (live slide reveal). Names start "G3.1" so they list on the G3.1 Documents tab.
KICKOFF_LINKS = [
    {"name": "G3.1 Kickoff: participant guide (live, Nov 4, 2026)", "kind": "Meeting guide", "date": "2026-11-04",
     "url": "kickoff/", "format": "Web page", "note": "Members follow the slides here; no account needed"},
    {"name": "G3.1 Kickoff: meeting summary and action plan (Nov 4, 2026)", "kind": "Meeting summary", "date": "2026-11-04",
     "url": "kickoff/summary.html", "format": "Web page", "note": "Decisions, topics proposed, actions with owners and dates"},
    {"name": "G2.2 Kickoff: participant guide (live, Nov 12, 2026)", "kind": "Meeting guide",
     "date": "2026-11-05", "url": "kickoff-g22/", "format": "Web page",
     "note": "Members follow the slides here; no account needed"},
    # The G2.2 deck lives on the Curricular Affairs SharePoint (the G2.2 Year 1 folder is not ours to change).
    {"name": "G2.2 Kickoff slides (Nov 12, 2026)", "kind": "Slides", "date": "2026-11-05", "folder": "02 Meetings",
     "url": "https://mtsinai.sharepoint.com/sites/CurricularAffairs/_layouts/15/Doc.aspx?sourcedoc=%7BD2758299-9E78-4DA0-B178-456C1F08BA1C%7D&action=default",
     "format": "PowerPoint", "note": "Curricular Affairs SharePoint (Mount Sinai sign-in)"},
    {"name": "G3.1 Evidence source: SCOPE survey page (Both groups)", "kind": "Evidence source", "date": "2026-11-05",
     "url": "#scope", "format": "Dashboard page",
     "note": "Mount Sinai's AAMC Curriculum SCOPE answers against the national norm, with the AAMC reports"},
]


def publish_charters():
    """Copy the styled charter pages (user ruling 2026-10-25: charters readable on this public site) into docs/."""
    out = os.path.join(HERE, "docs"); os.makedirs(out, exist_ok=True)
    for fn in CHARTERS:
        html = open(os.path.join(STYLED, fn), encoding="utf-8").read()
        for bad in ("@mssm.edu", "@mountsinai.org"):
            if bad in html: sys.exit(f"{fn} contains {bad!r}; charters on the public site must not carry email addresses")
        if not html.lstrip().lower().startswith("<!doctype"):
            html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">\n'
                    + html + "\n</html>\n")
        open(os.path.join(out, fn), "w", encoding="utf-8").write(html)


# The working groups' SharePoint folders (Year 1 Initiatives Working Groups site, set up by Kevin Han).
# The Documents tab mirrors their folders: 01 Charter, 02 Meetings (+ Meeting Minutes), 03 Working Drafts.
SP_SITE = "https://mtsinai.sharepoint.com/sites/Year1InitiativesWorkingGroups2"
SP_DOC = SP_SITE + "/_layouts/15/Doc.aspx?sourcedoc=%7B{}%7D&action=default"
SP_FOLDERS = {
    "G3.1": "https://mtsinai.sharepoint.com/:f:/s/Year1InitiativesWorkingGroups2/IgBH-hSShNhETKV8HVP9uYoeASlQ-v2r4e7fM9GV5LjQyCE",
    "G2.2": SP_SITE + "/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FYear1InitiativesWorkingGroups2%2FShared%20Documents%2F03_Working_Groups%2FP2_G2.2_Curriculum-Gap-Closure",
}
FOLDER_ORDER = ["01 Charter", "02 Meetings", "02 Meetings › Meeting Minutes", "03 Working Drafts", "Evidence and reports"]
_SP = [  # (group, folder, name, kind, date, format, SharePoint UniqueId)
    ("G3.1", "01 Charter", "Charter approval vote (G3.1_Charter_Vote_2026-11)", "Charter vote", "2026-11-05", "Excel", "b110e6c0-e657-4fc1-9973-681e900ed199"),
    ("G3.1", "02 Meetings", "Running agenda", "Agenda", "2026-10-30", "Word", "88c28fff-8412-40a1-aea0-93234c9ea513"),
    ("G3.1", "02 Meetings", "Kickoff slides (Nov 4, 2026)", "Slides", "2026-11-04", "PowerPoint", "41aa74be-01a9-4427-b348-71297f9d7358"),
    ("G3.1", "02 Meetings", "Emerging topics list (until the combined G3.1 Emerging Topics Register is uploaded)", "Topic list", "2026-11-05", "Excel", "cb698f1a-0fd0-40be-adf9-7b0e322f7165"),
    ("G3.1", "02 Meetings › Meeting Minutes", "Meeting minutes, Nov 4, 2026 (official, Word)", "Minutes", "2026-11-04", "Word", "e2cfd687-796b-4a41-bcc4-add2fef89a84"),
    ("G2.2", "02 Meetings", "Running agenda", "Agenda", "2026-10-30", "Word", "810c00e0-9c24-4a59-bde6-6e274acaa15c"),
]
SP_LINKS = [{"name": f"{g} {n}", "group": g, "folder": f, "kind": k, "date": d, "format": fmt, "url": SP_DOC.format(u),
             "note": "Working group SharePoint (Mount Sinai sign-in)"} for g, f, n, k, d, fmt, u in _SP]


def dropped(l):
    """Only the latest version of each document is listed (user, 2026-11-05): the Word draft charters are reached
    from the one Charter listing per group, and the Oct 23 working-details snapshot is out of date."""
    n = l.get("name", "")
    return (l.get("kind") == "Plan document" and "charter" in n.lower()) or n.startswith("Working details:")


def folder_of(l):
    """Place each dashboard link in the SharePoint folder it belongs with."""
    n, k = l.get("name", ""), l.get("kind", "")
    if l.get("folder"): return l["folder"]
    if k in ("Charter", "Plan document") or "charter" in n.lower(): return "01 Charter"
    if k == "Meeting summary": return "02 Meetings › Meeting Minutes"
    if k == "Meeting guide": return "02 Meetings"
    return "Evidence and reports"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--master", default=MASTER); a = ap.parse_args()
    data = json.load(open(os.path.join(a.master, "e2i-data.json"), encoding="utf-8"))
    for k in ("gaps", "milestones") + tuple(v[0] for v in SHEETS.values()):
        if not isinstance(data.get(k), list): sys.exit(f"e2i-data.json: '{k}' missing")
    lp = os.path.join(a.master, "links.json")
    links = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else []
    file_links = {l["file"]: l["url"] for l in links if l.get("file") and l.get("url")}

    links = links + CHARTER_LINKS + KICKOFF_LINKS + SP_LINKS
    links = [l for l in links if not dropped(l)]
    for l in links:
        l["folder"] = folder_of(l)
        if l.get("name", "").endswith(" draft charter"):  # the editable Word copy lives on the Curricular Affairs SharePoint
            l["name"] = l["name"].replace(" draft charter", " Draft charter (Word, Curricular Affairs SharePoint)")
    # the charters on this site open in the side panel; SharePoint keeps the editable copies
    public = {"generated": data.get("generated", ""),
              "gaps": [{k: g[k] for k in GAP_FIELDS if k in g} for g in data["gaps"]],
              "milestones": [{k: m[k] for k in MS_FIELDS if k in m} for m in data["milestones"]],
              "emerging": [{k: e[k] for k in ("topic", "why", "strength", "status", "pilot", "order", "_id") if k in e} for e in data.get("emerging", [])],
              "links": [{k: l[k] for k in ("name", "kind", "date", "url", "format", "note", "folder") if k in l} for l in links if l.get("url")],
              "spFolders": SP_FOLDERS, "folderOrder": FOLDER_ORDER,
              # Working-group minutes: attendance, decisions and action items (the discussion stays in the Word minutes)
              "minutes": [{k: m[k] for k in MIN_FIELDS if k in m} for m in data["minutes"] if str(m.get("group", "")).startswith(("G2.2", "G3.1"))],
              # Members tab: name, title, seat and photo only (no email, status or notes; those stay in the workbook)
              "members": [{k: m[k] for k in MEMBER_FIELDS if k in m} for m in data["members"] if m.get("status") != "Declined"],
              # timelines, rules, criteria and resources from the co-leads' working doc (no names or emails)
              "workdoc": data.get("workdoc", {})}
    blob = json.dumps(public, ensure_ascii=False)
    for bad in ("@mssm.edu", "@mountsinai.org", "/files/", "/docs/"):
        if bad in blob: sys.exit(f"public data still contains {bad!r}; it belongs in the working files, not the public site")
    with open(os.path.join(HERE, "data", "e2i-data.js"), "w", encoding="utf-8") as f:
        f.write("/* From Education to Impact public data. Generated by tools/build.py from the OneDrive master; do not edit by hand. */\n")
        f.write("window.E2I_DATA = " + blob + ";\n")

    publish_charters()

    files = os.path.join(a.master, "files")
    write_in_place(os.path.join(files, WORKBOOK), workbook(data, file_links))
    write_in_place(os.path.join(files, GAP_PDF), gap_pdf(os.path.join(a.master, "docs", "gap-report.html")))
    print("data/e2i-data.js:", {k: len(v) for k, v in public.items() if isinstance(v, list)},
          "| wrote", WORKBOOK, "and", GAP_PDF)


if __name__ == "__main__":
    main()
