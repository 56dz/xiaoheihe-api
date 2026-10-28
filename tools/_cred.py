# -*- coding: utf-8 -*-
"""开发期脚本共用的凭据加载：优先环境变量，其次仓库根目录的本地凭据文件。

仓库里不保存任何真实凭据，下列文件都在 .gitignore 中：
  * 环境变量 ``XHH_PKEY`` / ``XHH_HEYBOX_ID``
  * ``pkey.txt``  —— 只放一行 ``user_pkey`` 的值
  * ``cookie.json`` —— get_token.js 的产物，可能含 ``user_pkey`` 字段或整条 cookie
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_pkey() -> str:
    pkey = os.environ.get("XHH_PKEY")
    if pkey:
        return pkey.strip()

    path = os.path.join(ROOT, "pkey.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()

    path = os.path.join(ROOT, "cookie.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("user_pkey"):
            return data["user_pkey"]
        for part in data.get("cookie", "").split(";"):
            part = part.strip()
            if part.startswith("user_pkey="):
                return part.split("=", 1)[1]

    raise SystemExit(
        "缺少登录凭据：请设置环境变量 XHH_PKEY，或在仓库根目录放 pkey.txt / cookie.json"
    )


def load_heybox_id() -> str:
    uid = os.environ.get("XHH_HEYBOX_ID")
    if uid:
        return uid.strip()

    path = os.path.join(ROOT, "cookie.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("heybox_id"):
            return str(data["heybox_id"])
        for part in data.get("cookie", "").split(";"):
            part = part.strip()
            if part.startswith("heybox_id="):
                return part.split("=", 1)[1]

    raise SystemExit(
        "缺少 heybox_id：请设置环境变量 XHH_HEYBOX_ID，或在 cookie.json 里提供"
    )
