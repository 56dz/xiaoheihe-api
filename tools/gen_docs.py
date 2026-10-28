"""从 xhh/api.py 生成 docs/api.md（方法名、路径、HTTP 方法、docstring）。

跑一次就够，改完 api.py 再跑一次即可。

    python tools/gen_docs.py
"""

import inspect
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import xhh  # noqa: E402

GROUPS = [
    ("FeedsAPI", "首页 / 社区流"),
    ("SearchAPI", "搜索"),
    ("LinkAPI", "帖子与评论"),
    ("UserAPI", "用户 / 关注 / 收藏 / 登录"),
    ("MessageAPI", "消息中心"),
    ("GameAPI", "游戏 / 赛事"),
    ("EditorAPI", "发帖编辑器 / 上传 / 发布"),
    ("MiscAPI", "创作者中心 / 反馈 / 客户端 / 聊天室"),
]

_PATH_RE = re.compile(r'"(/[A-Za-z0-9_/.\-]+)"')


def _doc(fn):
    d = inspect.getdoc(fn) or ""
    return d.strip()


def _sig(fn):
    try:
        return str(inspect.signature(fn))
    except (TypeError, ValueError):
        return "(...)"


def main():
    out = [
        "# 接口清单",
        "",
        "由 `tools/gen_docs.py` 从 `xhh/api.py` 自动生成，与代码保持一致。",
        "",
        "约定：",
        "",
        "* 所有方法返回服务端 `result` 字段（已剥掉 `status` / `msg` 外壳）；",
        "* 请求失败抛 `xhh.XhhError`，命中验证码风控抛它的子类 `xhh.CaptchaRequired`；",
        "* 每个请求都会自动带上签名三件套 `hkey` / `_time` / `nonce` 和 9 个公共参数，"
        "下表只列业务参数。",
        "",
        "---",
        "",
    ]

    for cls_name, title in GROUPS:
        cls = getattr(xhh, cls_name)
        out.append(f"## {title}")
        out.append("")
        for name, fn in vars(cls).items():
            if name.startswith("_") or not inspect.isfunction(fn):
                continue
            src = inspect.getsource(fn)
            paths = _PATH_RE.findall(src)
            methods = re.findall(r'method="(POST|GET)"', src)
            verb = methods[0] if methods else "GET"
            if len(paths) > 1 and "follow" in name:
                path = paths[0] + "` / `" + paths[1]
            elif paths:
                path = paths[0]
            else:
                path = "（组合调用，见实现）"
            out.append(f"### `{name}{_sig(fn)}`")
            out.append("")
            out.append(f"`{verb} {path}`")
            out.append("")
            doc = _doc(fn)
            if doc:
                out.append(doc)
                out.append("")
        out.append("---")
        out.append("")

    dest = os.path.join(ROOT, "docs", "api.md")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out).rstrip() + "\n")
    print(f"wrote {dest} ({len(out)} lines)")


if __name__ == "__main__":
    main()
