"""Excel(シャドバPSシート 40行目以降) -> docs/data/channels.csv, docs/data/subscribers.csv
読むのは「シャドバPS」シートのみ。1行目がdatetimeの列=登録者数、それ以外(差分列・Twitter期の文字列見出し)は無視。
usage: python -I scripts/import_excel.py <xlsx path>
"""
import csv, sys, datetime as dt
from urllib.parse import unquote
import openpyxl

SHEET, FIRST_ROW = "シャドバPS", 40
src = sys.argv[1]
ws = openpyxl.load_workbook(src, read_only=True, data_only=True)[SHEET]
rows = list(ws.iter_rows(values_only=True))
date_cols = [i for i, v in enumerate(rows[0]) if isinstance(v, dt.datetime)]

channels, subs = [], []
for n, r in enumerate(rows[FIRST_ROW - 1:], start=FIRST_ROW):
    team, name, url = r[0], r[1], r[2]
    url = (url or "").strip()
    if not name or not url.startswith("http"):
        continue  # URL無し("-")はチャンネルが無いので対象外
    cid = handle = ""
    if "/channel/" in url:
        cid = url.split("/channel/")[1].split("/")[0]
    elif "/@" in url:
        handle = "@" + unquote(url.split("/@")[1].split("/")[0])
    key = cid or handle or f"{team}:{name}"
    channels.append([key, team, name, cid, handle, url if url != "-" else ""])
    for i in date_cols:
        v = r[i]
        if isinstance(v, (int, float)):
            subs.append([rows[0][i].date().isoformat(), key, int(v), "excel"])

with open("docs/data/channels.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["key", "team", "name", "channel_id", "handle", "url"]); w.writerows(channels)
with open("docs/data/subscribers.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["date", "key", "subscribers", "source"]); w.writerows(sorted(subs))
print(len(channels), "channels,", len(subs), "points; dates:", [rows[0][i].date().isoformat() for i in date_cols])


