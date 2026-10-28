"""示例：抓一个帖子 —— 正文、图片、视频、楼层评论、楼中楼，并把媒体落盘。

用法::

    python examples/03_post.py 195173343          # 图文帖
    python examples/03_post.py 195148022          # 视频帖
    python examples/03_post.py 195173343 --download
"""

import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xhh


def download(url, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    ext = os.path.splitext(url.split("?")[0])[1] or ".bin"
    path = os.path.join(out_dir, f"{name}{ext}")
    req = urllib.request.Request(url, headers={"User-Agent": xhh.UA})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        f.write(r.read())
    return path


def show_post(client, link_id, do_download=False):
    tree = client.link_tree(link_id, page=1, limit=20)
    post = xhh.parse_link(tree["link"])

    print("=" * 70)
    print(f"[{post['link_id']}] {post['title']}")
    print("=" * 70)
    print(f"作者: {(post['user'] or {}).get('username')}  类型: {post['kind']}")
    print(f"社区: {[t.get('name') for t in post['topics']]}")
    print(f"话题: {[h.get('name') if isinstance(h, dict) else h for h in post['hashtags']]}")
    print(f"评论数: {post['comment_num']}  投币: {post['link_award_num']}")
    print()
    print("--- 正文 ---")
    print(post["text"])

    if post["video"]:
        v = post["video"]
        print("\n--- 视频 ---")
        print(f"{v['width']}x{v['height']}  {v['duration']}s")
        print(v["url"])
        print(f"封面: {v['thumb']}")
        if do_download:
            print("已保存:", download(v["url"], "out", f"{link_id}_video"))
            if v["thumb"]:
                download(v["thumb"], "out", f"{link_id}_cover")

    if post["images"]:
        print(f"\n--- 图片 {len(post['images'])} 张 ---")
        for i, img in enumerate(post["images"], 1):
            print(f"{i:2d}. {img['url']}")
            if do_download:
                download(img["url"], "out", f"{link_id}_{i:02d}")

    # ---- 楼层评论 ----
    total_pages = tree.get("total_page") or 1
    print(f"\n--- 评论（{tree.get('total_floor_num')} 楼 / {total_pages} 页）---")
    comments = xhh.flatten_comments(tree)
    for c in comments:
        txt = xhh.plain_text_comment(c["text"])
        print(f"[{c['floor_num']}楼] {c['username']} ({c['ip_location'] or '-'}) "
              f"赞{c['up']} 回复{c['child_num']}")
        print(f"    {txt[:100]}")
        # 楼中楼
        if c["child_num"]:
            sub = client.sub_comments(link_id, c["commentid"], offset=0, limit=5)
            for s in (sub.get("comments") or [])[:5]:
                su = s.get("user") or {}
                print(f"    └ {su.get('username')}: "
                      f"{xhh.plain_text_comment(s.get('text'))[:60]}")

    # 相关推荐：related_links 是 {title, link_infos[]}，字段名是 link_id 不是 linkid
    rel = client.link_related(link_id)
    infos = (rel.get("related_links") or {}).get("link_infos") or []
    print(f"\n--- 相关帖子 {len(infos)} 条 ---")
    for r in infos[:5]:
        print(f"  [{r.get('link_id')}] {r.get('title', '')[:40]}")
    topics = (rel.get("related_topics") or {}).get("topic_infos") or []
    if topics:
        print(f"--- 相关社区 ---\n  {[t.get('name') for t in topics[:6]]}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    link_id = int(sys.argv[1])
    do_download = "--download" in sys.argv

    c = xhh.Client.from_file("cookie.json")
    show_post(c, link_id, do_download)


if __name__ == "__main__":
    main()
