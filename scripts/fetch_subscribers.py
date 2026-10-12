"""YouTube Data APIから登録者数を取得し docs/data/subscribers.csv に追記する。
- channels.csv の channel_id が空の行は @handle から解決して書き戻す
- 同じ (date, key) が既にあれば追記しない(再実行しても重複しない)
- 登録者数を非公開にしているチャンネルは記録しない
env: YOUTUBE_API_KEY
"""
import csv, json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

DATA = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
CHANNELS, SUBS = os.path.join(DATA, "channels.csv"), os.path.join(DATA, "subscribers.csv")
API = "https://www.googleapis.com/youtube/v3/channels"
KEY = os.environ["YOUTUBE_API_KEY"]


def call(**params):
    q = urllib.parse.urlencode({**params, "key": KEY})
    with urllib.request.urlopen(f"{API}?{q}", timeout=30) as r:
        return json.load(r)


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


channels = read(CHANNELS)

changed = False
for c in channels:
    if not c["channel_id"]:
        items = call(part="id", forHandle=c["handle"]).get("items", [])
        if items:
            c["channel_id"], changed = items[0]["id"], True
        else:
            print("handle not found:", c["name"], c["handle"], file=sys.stderr)
if changed:
    with open(CHANNELS, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(channels[0].keys()))
        w.writeheader(); w.writerows(channels)

today = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
existing = {(r["date"], r["key"]) for r in read(SUBS)}
by_id = {c["channel_id"]: c["key"] for c in channels if c["channel_id"]}
ids = list(by_id)
new = []
for i in range(0, len(ids), 50):
    for it in call(part="statistics", id=",".join(ids[i:i + 50]), maxResults=50).get("items", []):
        st = it["statistics"]
        if st.get("hiddenSubscriberCount") or "subscriberCount" not in st:
            continue
        key = by_id[it["id"]]
        if (today, key) not in existing:
            new.append([today, key, int(st["subscriberCount"]), "api"])

with open(SUBS, "a", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(new)
print(f"{today}: appended {len(new)} rows / {len(ids)} channels")
