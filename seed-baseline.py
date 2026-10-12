#!/usr/bin/env python3
"""Seed "last week" state from Wayback Machine copies, so the first run has something to compare against.

Only needed to reproduce the demo screenshot. In normal use the agent's first run saves the baseline itself.
Usage: python3 seed-baseline.py 20261005   (target date, YYYYMMDD)
"""
import json, os, subprocess, sys, urllib.request

here = os.path.dirname(os.path.abspath(__file__))
state_dir = os.path.expanduser("~/.hermes/competitor-intel/state")
target = sys.argv[1]
watch = json.load(open(f"{here}/watchlist.json"))
schemas = json.load(open(f"{here}/schemas.json"))
os.makedirs(state_dir, exist_ok=True)

for page in watch["pages"]:
    bare = page["url"].split("://", 1)[1]
    cdx = f"https://web.archive.org/cdx/search/cdx?url={bare}&to={target}&output=json&filter=statuscode:200&fl=timestamp&limit=-1"
    try:
        rows = json.load(urllib.request.urlopen(cdx, timeout=60))
        ts = rows[-1][0]
    except Exception as e:
        print(f"{page['id']}: no archived copy ({e})")
        continue
    args = {"url": f"https://web.archive.org/web/{ts}/{page['url']}", "formats": ["json"], "extraction_schema": schemas[page["type"]]}
    out = subprocess.run(["composio", "execute", "OLOSTEP_SCRAPE_PAGE", "-d", json.dumps(args)], capture_output=True, text=True).stdout
    try:
        data = json.loads(json.loads(out)["data"]["result"]["json_content"])
    except Exception:
        print(f"{page['id']}: scrape failed: {out[:200]}")
        continue
    state = {"id": page["id"], "url": page["url"], "captured_at": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}", "source": f"wayback:{ts}", "data": data}
    json.dump(state, open(f"{state_dir}/{page['id']}.json", "w"), indent=2)
    print(f"{page['id']}: saved copy from {state['captured_at']}")
