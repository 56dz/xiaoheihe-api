"""示例：首页推荐流 + 帖子详情 + 评论（含图文视频解析）。

用法::

    python examples/01_home_feed.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xhh


def main():
    # cookie.json 由 get_token.js 生成；若含 pkey 字段则自带登录态
    client = xhh.Client.from_file("cookie.json")
    print("登录态:", client.logged_in)

    print("== 首页推荐流 ==")
    data = client.feeds(offset=0, pull=0, dw=604)
    print(f"共 {len(data['links'])} 条，notify: {data.get('notify_msg') or '无'}")
    for item in data["links"][:5]:
        kind = "视频" if item.get("has_video") else (
            "图文" if (item.get("imgs") or []) else "文字")
        print(f"[{item['linkid']}] {kind} | {item['title'][:40]} "
              f"| 评论 {item.get('comment_num')} | 投币 {item.get('link_award_num')}")

    # 翻页：offset 步长 = 单页条数
    print("\n== 第 2 页 ==")
    page2 = client.feeds(offset=10, pull=0, dw=604)
    ids1 = {i["linkid"] for i in data["links"]}
    ids2 = {i["linkid"] for i in page2["links"]}
    print(f"第 2 页 {len(page2['links'])} 条，与第 1 页重叠 {len(ids1 & ids2)} 条")

    # 拿一个图文帖和视频帖做详情解析
    print("\n== 帖子详情 ==")
    target = next((i for i in data["links"] if i.get("has_video")), data["links"][0])
    tree = client.link_tree(target["linkid"], limit=5)
    post = xhh.parse_link(tree["link"])
    print(f"标题: {post['title']}")
    print(f"类型: {post['kind']}")
    print(f"正文: {post['text'][:120]}…")
    if post["video"]:
        print(f"视频: {post['video']['url'][:80]}… ({post['video']['duration']}s)")
    for i, img in enumerate(post["images"][:3], 1):
        print(f"图片{i}: {img['url']}")

    print(f"\n评论 {tree.get('total_floor_num')} 楼 / {tree.get('total_page')} 页")
    for c in xhh.flatten_comments(tree)[:5]:
        print(f"  {c['username']}[{c['floor_num']}楼] {xhh.plain_text_comment(c['text'])[:60]}")


if __name__ == "__main__":
    main()
