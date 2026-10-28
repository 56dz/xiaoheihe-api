"""帖子内容的解析工具。

小黑盒的帖子正文有三种形态，全部挤在 ``link`` 对象的同一批字段里，
前端靠自己判断：这里把它们归一成 ``{kind, html, images, video}``，
省得每个调用方重写一遍判断逻辑。
"""

from __future__ import annotations

import json
import re

_IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
_ATTR = re.compile(r'(data-original|data-description|data-width|data-height)\s*=\s*"([^"]*)"', re.I)
_TAG = re.compile(r"<[^>]+>")


def _clean_html(html: str) -> str:
    """把正文 HTML 压成纯文本（保留换行）。"""
    if not html:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    s = re.sub(r"</p>", "\n", s, flags=re.I)
    s = _TAG.sub("", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#39;", "'")
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def _imgs_in_html(html: str) -> list[dict]:
    """抽出正文 HTML 里内嵌的 ``<img data-original=...>``。"""
    out = []
    for tag in _IMG_TAG.findall(html or ""):
        attrs = {k.lower(): v for k, v in _ATTR.findall(tag)}
        url = attrs.get("data-original") or attrs.get("data-url")
        if not url:
            continue
        out.append({
            "url": url,
            "width": _int(attrs.get("data-width")),
            "height": _int(attrs.get("data-height")),
            "desc": attrs.get("data-description") or "",
        })
    return out


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def parse_link(link: dict) -> dict:
    """把帖子 ``link`` 解析成统一结构。

    返回::

        {
          "link_id": 195173343,
          "title": "…",
          "kind": "text" | "image" | "video",
          "html": "<p>…</p>",          # 正文 HTML（视频帖为描述）
          "text": "纯文本正文",
          "images": [{"url","width","height","desc"}],
          "video": {"url","thumb","duration","width","height"} | None,
          "topics": [...],
          "user": {...},
          ...
        }

    * 纯文字帖：``text`` 字段本身是 HTML 字符串；
    * 图文帖：``text`` 是 **JSON 字符串**，解析后是元素列表 —— 首个
      ``type=text|html`` 元素是正文，其余 ``type=img`` 是配图；
    * 视频帖：``has_video=1``，视频地址在 ``video_url``（带时效签名，
      过期需重新拉一次详情）。
    """
    text = link.get("text") or ""
    html = ""
    images: list[dict] = []

    parsed = None
    if text.lstrip().startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None

    if isinstance(parsed, list):
        for el in parsed:
            if not isinstance(el, dict):
                continue
            t = el.get("type")
            if t in ("text", "html") and not html:
                html = el.get("text") or ""
                images.extend(_imgs_in_html(html))
            elif t == "img":
                url = el.get("url") or el.get("src")
                if url:
                    images.append({
                        "url": url,
                        "width": _int(el.get("width")),
                        "height": _int(el.get("height")),
                        "desc": el.get("description") or el.get("desc") or "",
                    })
            elif t == "video" and el.get("url"):
                pass  # 极少见，视频走 link.video_url
    else:
        html = text
        images.extend(_imgs_in_html(html))

    # 视频帖
    video = None
    if link.get("has_video") and link.get("video_url"):
        video = {
            "url": link.get("video_url"),
            "thumb": link.get("video_thumb"),
            "duration": link.get("video_duration"),
            "width": link.get("video_width"),
            "height": link.get("video_height"),
        }

    # 兜底：没有正文但有大图字段时
    if not images:
        for im in link.get("imgs") or []:
            if isinstance(im, str):
                images.append({"url": im, "width": None, "height": None, "desc": ""})
            elif isinstance(im, dict) and im.get("url"):
                images.append({
                    "url": im["url"],
                    "width": _int(im.get("width")),
                    "height": _int(im.get("height")),
                    "desc": im.get("description") or "",
                })

    if video:
        kind = "video"
    elif images:
        kind = "image"
    else:
        kind = "text"

    return {
        "link_id": link.get("linkid"),
        "title": link.get("title") or "",
        "kind": kind,
        "html": html,
        "text": _clean_html(html),
        "images": images,
        "video": video,
        "topics": link.get("topics") or [],
        "hashtags": link.get("hashtags") or link.get("act_hashtags") or [],
        "user": link.get("user") or {},
        "create_at": link.get("create_at"),
        "comment_num": link.get("comment_num"),
        "link_award_num": link.get("link_award_num"),
        "share_url": link.get("share_url"),
    }


def flatten_comments(tree: dict, limit: int = 0) -> list[dict]:
    """把 ``link_tree`` 的评论楼层压平成一维列表（含子评论标记）。

    顶层结构是 ``comments: [{comment: [...]}, ...]``，这里统一成
    ``[{commentid, userid, username, text, floor_num, child_num, up, ...}]``。
    """
    out = []
    for floor in tree.get("comments") or []:
        for cm in floor.get("comment") or []:
            u = cm.get("user") or {}
            out.append({
                "commentid": cm.get("commentid"),
                "userid": cm.get("userid"),
                "username": u.get("username"),
                "avatar": u.get("avatar") or u.get("avartar"),
                "text": cm.get("text"),
                "create_at": cm.get("create_at"),
                "floor_num": cm.get("floor_num"),
                "child_num": cm.get("child_num"),
                "up": cm.get("up"),
                "ip_location": cm.get("ip_location"),
                "is_link_owner": cm.get("is_link_owner"),
            })
            if limit and len(out) >= limit:
                return out
    return out


def plain_text_comment(text: str) -> str:
    """评论正文也是 HTML，压成纯文本。"""
    return _clean_html(text)
