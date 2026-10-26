"""One-off (2026-10-25, co-leads): G2.2 KPI wording revised to match the milestones. Keeps the Oct 14 workbook wording
in `wb` (shown under the new text) until the plan's Change Log approves the revision with the charter (Nov 13).
Edits the embedded PLAN data in index.html. Run from the repo root: python3 tools/kpi_revisions_g22.py"""
import json, re
REV = {
 "G2.2-K1": ("Governance Deadline",
   "100% of the curriculum gaps on the confirmed register receive a documented EEC decision (Address, Defer or Monitor) by December 31, 2026, after review by PCCS (Phase 1 gaps), CCS (Phase 2 and 3 gaps) or CIS (AOC and thread gaps) at their December meetings."),
 "G2.2-K2": ("Curriculum Map as CIS's Central Source",
   "By March 31, 2027, the Curricular Integration Subcommittee uses the curriculum map database as its central source for curriculum content and integration data: the fields it needs are complete (including the five societal problems in every phase) and the procedure is adopted at its March 18 meeting."),
 "G2.2-K3": ("Annual Curriculum Gap Report",
   "Establish an Annual Curriculum Gap Report, presented to the EEC at its March 5, 2027 meeting, that identifies curriculum gaps across student surveys, assessment outcomes, the AAMC SCOPE survey, the curriculum map database and the LCME Standard 7 coverage check, with its sections reviewed by PCCS, CCS and CIS."),
 "G2.2-K4": ("Gap Closure Tracking",
   "Use the Annual Curriculum Gap Report to track the gaps the EEC designates Address: 100% of Address gaps closed by their target dates, beginning Year 2, with a baseline at the May 2027 Annual Review."),
}
NOTE = "Wording revised Oct 25, 2026 by the co-leads to match the milestones; goes to the plan's Change Log with the charter (Nov 13)."
p = "index.html"; s = open(p, encoding="utf-8").read()
for kid, (name, text) in REV.items():
    m = re.search(r'\{"id": "' + re.escape(kid) + r'", [^{}]*\}', s)
    rec = json.loads(m.group(0))
    rec.setdefault("wb", rec["text"]); rec.setdefault("wbName", rec["name"])
    rec["name"], rec["text"], rec["issue"] = name, text, NOTE
    s = s[:m.start()] + json.dumps(rec, ensure_ascii=False) + s[m.end():]
open(p, "w", encoding="utf-8").write(s)
print("revised", len(REV))
