from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import date, timedelta

from common import RAW, ensure_dirs, load_env, save_json


def request_json(url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("errcode", 0) != 0:
        raise RuntimeError(f"微信接口错误 {result.get('errcode')}: {result.get('errmsg')}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="获取微信公众号图文与用户统计原始数据")
    parser.add_argument("--date", default=(date.today() - timedelta(days=1)).isoformat(), help="群发日期 YYYY-MM-DD")
    args = parser.parse_args()
    ensure_dirs()
    env = {**load_env(), **os.environ}
    app_id, secret = env.get("WECHAT_APP_ID"), env.get("WECHAT_APP_SECRET")
    if not app_id or not secret:
        raise SystemExit("缺少 WECHAT_APP_ID/WECHAT_APP_SECRET。请复制 .env.example 为 .env 后填写。")
    query = urllib.parse.urlencode({"grant_type": "client_credential", "appid": app_id, "secret": secret})
    token = request_json(f"https://api.weixin.qq.com/cgi-bin/token?{query}")["access_token"]
    payload = {"begin_date": args.date, "end_date": args.date}
    endpoints = ["getarticletotal", "getarticlesummary", "getusersummary", "getusercumulate"]
    output = {name: request_json(f"https://api.weixin.qq.com/datacube/{name}?access_token={token}", payload) for name in endpoints}
    save_json(RAW / f"wechat-{args.date}.json", output)
    print(f"已获取 {args.date} 数据：data/raw/wechat-{args.date}.json")


if __name__ == "__main__":
    main()
