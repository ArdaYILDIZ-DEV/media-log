import os
import re
from datetime import datetime
from collections import defaultdict

MEDIA_DIRS = ["animes", "films", "shows"]

def parse_frontmatter(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"---(.*?)---", content, re.S)
    if not match:
        return None

    block = match.group(1)

    data = {}

    for line in block.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()

    return data


entries = []

for folder in MEDIA_DIRS:
    if not os.path.exists(folder):
        continue

    for file in os.listdir(folder):
        if not file.endswith(".md"):
            continue

        path = os.path.join(folder, file)
        data = parse_frontmatter(path)

        if not data:
            continue

        title = data.get("title", "Unknown")
        date = data.get("date", "")
        mtype = data.get("type", "")
        status = data.get("status", "")

        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except:
            continue

        entries.append({
            "title": title,
            "date": date_obj,
            "type": mtype,
            "status": status
        })


entries.sort(key=lambda x: x["date"], reverse=True)

timeline = defaultdict(list)

for e in entries:
    month = e["date"].strftime("%Y-%m")
    timeline[month].append(e)

for month in timeline:
    print(month)
    for e in timeline[month]:
        print(f" └─ {e['title']} ({e['type']}) — {e['status']}")
    print()

