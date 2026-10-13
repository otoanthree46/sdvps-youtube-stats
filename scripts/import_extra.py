"""追加データ.xlsx(Sheet1)を取り込む。既存チャンネルは日付別の値を追記、未登録チャンネルはチーム「参考」で新規登録。
照合: URLのchannel_id → @handle → 名前(既存のみ)の順。既存と同じ(date,key)は追記しない。
usage: python -I scripts/import_extra.py <xlsx path>
"""
import csv, re, sys, datetime as dt
from urllib.parse import unquote
import openpyxl

CH, SUBS = "docs/data/channels.csv", "docs/data/subscribers.csv"
ws = openpyxl.load_workbook(sys.argv[1], read_only=True, data_only=True)["Sheet1"]
rows = list(ws.iter_rows(values_only=True))
date_cols = [i for i, v in enumerate(rows[0]) if isinstance(v, dt.datetime)]

with open(CH, newline="", encoding="utf-8-sig") as f:
    chans = list(csv.DictReader(f))
fields = list(chans[0].keys())
have = {(r["date"], r["key"]) for r in csv.DictReader(open(SUBS, encoding="utf-8-sig"))}

new_subs, added = [], []
for r in rows[1:]:
    name, url = r[1], unquote(r[3] or "")
    if not name:
        continue
    m = re.search(r"/channel/(UC[\w-]+)", url); h = re.search(r"/(@[^/?]+)", url)
    cid, handle = (m.group(1) if m else ""), (h.group(1) if h else "")
    hit = next((c for c in chans if (cid and c["channel_id"] == cid) or (handle and c["handle"].lower() == handle.lower())), None) \
        or next((c for c in chans if c["name"] == name), None)
    if not hit:
        base = f"https://www.youtube.com/channel/{cid}" if cid else f"https://www.youtube.com/{handle}"
        hit = {"key": cid or handle, "team": "参考", "name": name, "channel_id": cid, "handle": handle, "url": base}
        chans.append(hit); added.append(name)
    for i in date_cols:
        v = r[i]
        d = rows[0][i].date().isoformat()
        if isinstance(v, (int, float)) and (d, hit["key"]) not in have:
            new_subs.append([d, hit["key"], int(v), "excel"]); have.add((d, hit["key"]))

with open(CH, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(chans)
allrows = list(csv.reader(open(SUBS, encoding="utf-8-sig")))
head, body = allrows[0], allrows[1:] + [[str(x) for x in n] for n in new_subs]
body.sort(key=lambda x: (x[0], x[1]))
with open(SUBS, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(head); w.writerows(body)
print("new channels:", added); print("added points:", len(new_subs))
