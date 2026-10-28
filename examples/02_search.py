"""示例：搜索（综合 / 帖子 / 游戏 / 用户 / 话题），并演示翻页与结果清洗。

用法::

    python examples/02_search.py 黑神话
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xhh

#: 搜索结果里这些 type 不是实体内容：space 是排版留白，filter_tag 是筛选器。
SKIP_TYPES = {"space", "filter_tag"}


def collect(client, q, search_type="general", pages=2, limit=20):
    """按 offset 翻页去重。"""
    seen, out, offset = set(), [], 0
    for _ in range(pages):
        r = client.search(q, search_type=search_type, offset=offset, limit=limit)
        items = [i for i in r.get("items") or [] if i.get("type") not in SKIP_TYPES]
        if not items:
            break
        for it in items:
            info = it.get("info") or {}
            key = (it.get("type"),
                   info.get("linkid") or info.get("steam_appid") or info.get("userid")
                   or info.get("name"))
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        offset += limit
    return out


def describe(it):
    """所有结果实体都放在 ``info`` 里，靠 ``type`` 区分。

    各 type 的 info 结构并不统一：``topic`` 的社区对象内嵌在 ``info['topic']``，
    ``mini_app_v2`` 是 ``info['app_list']``，``relevant_search`` 是 ``info['items']``，
    ``tool`` 直接是扁平字段 —— 想一套代码通吃就得逐个分支。
    """
    info = it.get("info") or {}
    t = it.get("type")
    if t == "link":
        return (f"帖子 [{info.get('linkid')}] {info.get('title', '')[:40]} "
                f"| 评论 {info.get('comment_num')}")
    if t == "game":
        return f"游戏 [{info.get('steam_appid')}] {info.get('name', '')} {info.get('genres')}"
    if t == "user":
        return f"用户 [{info.get('userid')}] {info.get('username')} {info.get('rec_tag') or ''}"
    if t == "topic":
        tp = info.get("topic") or {}
        return f"社区 [{tp.get('topic_id')}] {tp.get('name')}（{len(info.get('items') or [])} 帖）"
    if t == "hashtag":
        return f"话题 #{info.get('name')} {info.get('sub_title') or ''}"
    if t == "mall":
        return f"商品 {info.get('title')}"
    if t == "new_game_list":
        return f"新游列表 {len(info.get('game_list') or [])} 个"
    if t == "mini_app_v2":
        apps = info.get("app_list") or []
        return f"小工具 {[a.get('name') for a in apps][:4]}"
    if t == "tool":
        return f"栏目 {info.get('title')} {info.get('desc') or ''}"
    if t == "relevant_search":
        return "相关搜索 " + " / ".join(i.get("text") or "" for i in (info.get("items") or [])[:5])
    return f"{t}"


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "黑神话"
    c = xhh.Client.from_file("cookie.json")

    print(f"== 搜索页 ==  热搜: {c.search_welcome().get('default_q')}")
    sug = c.search_suggestion(q).get("suggestions") or []
    print(f"联想词: {[s.get('name') or s.get('text') for s in sug[:6]]}")

    for st in ("general", "link", "game", "user", "hashtag"):
        print(f"\n== search_type={st} ==")
        items = collect(c, q, st, pages=1, limit=20)
        for it in items[:8]:
            print("  " + describe(it))
        print(f"  共 {len(items)} 条")

    # 筛选能力：filter_list 是筛选组，每组下面有 filters，key 透传回 sort_filter/time_range
    print("\n== 帖子搜索的筛选项 ==")
    r = c.search(q, search_type="link", limit=5)
    for group in r.get("filter_list") or []:
        key = group.get("key")
        opts = [(f.get("key"), f.get("desc")) for f in group.get("filters") or []]
        print(f"  {group.get('desc')}({key}): {opts}")

    print("\n== 按「最多点赞」重排 ==")
    items = c.search(q, search_type="link", sort_filter="award_num", limit=5)["items"]
    for it in items:
        if it.get("type") == "link":
            print("  " + describe(it))

    # 话题筛选词（general 结果顶部的横排标签）
    print("\n== 话题筛选词 ==")
    tags = c.search_filter_tags(q)
    print("  " + " / ".join(t.get("name") or "" for t in tags[:8]))


if __name__ == "__main__":
    main()
