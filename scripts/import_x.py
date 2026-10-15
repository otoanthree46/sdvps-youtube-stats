"""Xフォロワー数をExcel(シャドバPSシート 2行目〜最初の空行)から取り込む(手動更新用)。
行: A=チーム B=選手名 C=Xのユーザー名(URLでも可) / 1行目が日付の列=フォロワー数(日付でない列・差分列は無視)
- 選手は名前で channels.csv と照合(無ければ新規登録。YouTube未開設なら key="チーム:名前")。x_handle を書き戻す
- docs/data/x_followers.csv (date,key,followers,source) に、既存と重複しない分だけ追記
usage: python -I scripts/import_x.py <xlsx path> [sheet]
"""
import csv, os, re, sys, datetime as dt
import openpyxl

TEAM = {"MURASH GAMING":"MRG","レバンガ北海道":"LVH","REJECT":"RC","RIDDLE ORDER":"RID","VARREL":"VL",
        "DetonatioN FocusMe":"DFM","Crazy Raccoon":"CR","ZETA DIVISION":"ZETA"}
CH, XF = "docs/data/channels.csv", "docs/data/x_followers.csv"
src, sheet = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "シャドバPS")
rows = list(openpyxl.load_workbook(src, read_only=True, data_only=True)[sheet].iter_rows(values_only=True))

def to_date(v):
    if isinstance(v, dt.datetime): return v.date().isoformat()
    m = re.fullmatch(r"(\d{2})/(\d{1,2})/(\d{1,2})", str(v or "").strip())
    return f"20{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}" if m else None
dcols = [(i, d) for i, v in enumerate(rows[0]) if (d := to_date(v))]

chans = list(csv.DictReader(open(CH, encoding="utf-8-sig")))
fields = list(chans[0].keys())
if "x_handle" not in fields: fields.append("x_handle")
for c in chans: c.setdefault("x_handle", "")
have = {(r["date"], r["key"]) for r in csv.DictReader(open(XF, encoding="utf-8-sig"))} if os.path.exists(XF) else set()

out, new = [], []
for r in rows[1:]:
    team, name, handle = r[0], r[1], (r[2] or "").strip().rstrip("/").split("/")[-1].split("?")[0]  # URL形式でも可
    if not name: break
    team = TEAM.get(team, team)
    c = next((c for c in chans if c["name"] == name), None)
    if not c:
        c = {k: "" for k in fields}; c.update(key=f"{team}:{name}", team=team, name=name); chans.append(c); new.append(name)
    if handle: c["x_handle"] = handle
    for i, d in dcols:
        v = r[i] if i < len(r) else None
        if isinstance(v, (int, float)) and (d, c["key"]) not in have:
            out.append([d, c["key"], int(v), "excel"]); have.add((d, c["key"]))

with open(CH, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(chans)
old = list(csv.reader(open(XF, encoding="utf-8-sig")))[1:] if os.path.exists(XF) else []
allr = sorted(old + [[str(x) for x in o] for o in out], key=lambda x: (x[0], x[1]))
with open(XF, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["date", "key", "followers", "source"]); w.writerows(allr)
print("new players:", new, "| added points:", len(out), "| dates:", sorted({d for _, d in dcols}))
