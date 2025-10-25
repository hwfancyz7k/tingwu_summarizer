#!/usr/bin/env python3
import os, sys, time
from pathlib import Path
import requests


COOKIE = os.getenv("TINGWU_COOKIE")
if not COOKIE:
    raise ValueError("环境变量 TINGWU_COOKIE 未设置，请在 ~/.zshrc 中配置")

OUT = Path("tingwu_exports")
API = "https://tingwu.aliyun.com/api"


def session():
    c = dict((k.strip(), v.strip()) for s in COOKIE.split(";") if "=" in s for k, v in [s.split("=", 1)])
    s = requests.Session()
    s.headers.update({
        "content-type": "application/json",
        "cookie": COOKIE,
        "x-csrf-token": requests.utils.unquote(c.get("login_aliyunid_csrf", "")),
        "x-help-csrf-token": requests.utils.unquote(c.get("help_csrf", "")),
    })
    return s


def fetch_list(s, dir_id):
    items, p = [], 1
    while True:
        r = s.post(f"{API}/trans/request?getTransList&c=web", json={"action": "getTransList", "version": "1.0", "userId": "", "filter": {"status": [0], "dirId": dir_id}, "orderType": 0, "orderDesc": True, "preview": 1, "pageNo": p, "pageSize": 100}).json()
        items.extend(r["data"])
        if len(items) >= r.get("total", 0): break
        p += 1
    return items


def export(s, item):
    tag = item.get("tag", {}) or {}
    for _ in range(5):
        time.sleep(1)
        r = s.post(f"{API}/export/request?c=web", json={"action": "exportTrans", "transIds": [item["transId"]], "userId": int(item["userId"]), "exportDetails": [{"docType": 1, "fileType": 2, "withSpeaker": str(tag.get("enableIdentify", "0")) == "1", "withTimeStamp": True, "withTranslate": str(tag.get("translateSwitch", "0")) == "1"}]}).json()
        if r.get("code") == "0" and (tid := r.get("data", {}).get("exportTaskId") or r.get("data", {}).get("taskId")): return tid
        if r.get("code") != "EPO.RequestTooFast": raise RuntimeError(r)


def poll(s, tid):
    for _ in range(60):
        r = s.post(f"{API}/export/request?c=web", json={"action": "getExportStatus", "version": "1.0", "exportTaskId": tid}).json()
        st = r.get("data", {}).get("exportStatus")
        if st == 1: return r["data"].get("exportUrls", [])
        if st == -1: raise RuntimeError(r)
        time.sleep(1.5)


def clean(n):
    return "".join("_" if c in "\\/:*?\"<>|" else c for c in n).strip() or "tingwu"


def download(url, path):
    for i in range(5):
        try:
            with requests.get(url, timeout=120, stream=True) as r:
                r.raise_for_status()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(r.content)
                return
        except:
            if i < 4: time.sleep(2)
            else: raise


def main():
    if len(sys.argv) < 2:
        print("用法: python tingwu_batch_export.py <DIR_ID>")
        sys.exit(1)

    dir_id = int(sys.argv[1])
    s = session()
    items = fetch_list(s, dir_id)
    print(f"Found {len(items)}")

    OUT.mkdir(exist_ok=True)

    for item in items:
        if not (tid := item.get("transId")): continue
        name = item.get("tag", {}).get("showName") or item.get("taskId") or tid
        path = OUT / f"{clean(name)}.srt"

        if path.exists():
            print(f"Skip {path.name}")
            continue

        print(f"Export {path.name}")
        urls = poll(s, export(s, item))
        if url := next((e.get("url") for e in urls if e.get("docType") == 1 and e.get("success")), None):
            download(url, path)
            print(f"Done {path.name}")
            time.sleep(1)


if __name__ == "__main__":
    main()
