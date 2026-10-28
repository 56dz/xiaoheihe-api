"""对 xhh 包做一次全量冒烟测试：每个方法都真调一次，输出状态与关键信息。"""

import io
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import xhh

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import _cred

PK = _cred.load_pkey()
UID = int(_cred.load_heybox_id())
IMG_LINK = 195173343
VIDEO_LINK = 195148022
TOPIC = 43

c = xhh.Client.from_file("cookie.json").with_pkey(PK, heybox_id=UID)

ok, fail, skip = 0, 0, 0
lines = []


def call(name, fn, *a, **kw):
    global ok, fail, skip
    try:
        r = fn(*a, **kw)
    except Exception as e:
        fail += 1
        msg = f"{type(e).__name__}: {e}"
        print(f"FAIL {name:34s} {msg[:110]}")
        lines.append((name, "FAIL", msg[:200]))
        return None
    if isinstance(r, dict):
        info = ",".join(list(r.keys())[:5])
        print(f"ok   {name:34s} keys={len(r)} [{info[:90]}]")
    elif isinstance(r, list):
        print(f"ok   {name:34s} list={len(r)}")
    else:
        print(f"ok   {name:34s} {type(r).__name__}")
    ok += 1
    lines.append((name, "ok", ""))
    return r


print("=" * 100)
print("首页 / 社区")
print("=" * 100)
feed = call("feeds", c.feeds)
call("banner", c.banner)
cats = call("topic_categories", c.topic_categories)
menu = call("topic_menu", c.topic_menu, TOPIC)
call("topic_feeds", c.topic_feeds, TOPIC, 0, 10)
call("topic_feeds_news", c.topic_feeds_news, TOPIC, 0, 10)
call("website_background", c.website_background, 2358720)

print()
print("=" * 100)
print("搜索")
print("=" * 100)
call("search_welcome", c.search_welcome)
call("search_found", c.search_found)
call("search_suggestion", c.search_suggestion, "黑神话")
call("search", c.search, "黑神话", limit=10)
call("search_links", c.search_links, "黑神话", limit=10)
call("search_games", c.search_games, "黑神话", limit=10)
call("wiki_search", c.wiki_search, "黑神话")
call("mod_search", c.mod_search, "画质")
call("mall_search", c.mall_search, "手柄")

print()
print("=" * 100)
print("帖子 / 评论")
print("=" * 100)
tree = call("link_tree", c.link_tree, IMG_LINK, limit=5)
call("link_tree(video)", c.link_tree, VIDEO_LINK, limit=5)
call("link_tree_v2", c.link_tree_v2, IMG_LINK, limit=5)
call("link_tree_backend", c.link_tree_backend, IMG_LINK, limit=5)
call("link_related", c.link_related, IMG_LINK)
call("link_author", c.link_author, IMG_LINK)
call("forbid_reason", c.forbid_reason, IMG_LINK)

# 从详情里挖一个带子评论的评论去做楼中楼
root_cid = None
if tree:
    for w in tree.get("comments") or []:
        for cm in w.get("comment") or []:
            if cm.get("child_num"):
                root_cid = cm["commentid"]
                break
        if root_cid:
            break
if root_cid:
    call("sub_comments", c.sub_comments, IMG_LINK, root_cid, 0, 10)
else:
    skip += 1
    print(f"skip sub_comments (无带子评论的楼层)")

print()
print("=" * 100)
print("用户")
print("=" * 100)
call("user_profile", c.user_profile, UID)
call("user_links", c.user_links, UID, 0, 10)
call("user_events", c.user_events, UID)
call("follower_list", c.follower_list, UID)
call("following_list", c.following_list, UID)
call("fav_folders", c.fav_folders)
call("fav_links", c.fav_links, 0, 10)
call("history_visit", c.history_visit, 0, 10)
call("post_limits", c.post_limits)
call("user_permission", c.user_permission)
call("restore_login", c.restore_login)

print()
print("=" * 100)
print("消息")
print("=" * 100)
call("message(回复)", c.message, c.LIST_REPLY, 0, 10)
call("message(赞)", c.message, c.LIST_AWARD, 0, 10)
call("message(中心)", c.message, c.LIST_CENTER, 0, 10)
call("official_messages", c.official_messages, 0, 10)
call("discount_messages", c.discount_messages)

print()
print("=" * 100)
print("游戏 / 赛事")
print("=" * 100)
call("game_detail", c.game_detail, 2358720)
call("game_detail_console", c.game_detail_console, 2358720)
call("game_introduction", c.game_introduction, 2358720)
call("game_infos", c.game_infos, [2358720, 730])
call("owned_games", c.owned_games, 0, 10)
call("hot_games", c.hot_games, 0, 10)
call("game_comments", c.game_comments, 2358720, 0, 10)
call("game_wx_share", c.game_wx_share, 2358720)
call("steam_screenshots", c.steam_screenshots, 2358720, 0, 10)
call("self_made_games", c.self_made_games, 0, 10)
call("wiki_infos", c.wiki_infos, 2358720)
call("match_games", c.match_games)
call("match_leagues", c.match_leagues, 2358720)
call("match_list", c.match_list, 2358720, 0, 10)
call("match_leagues_batch", c.match_leagues_batch)
call("batch_match_data", c.batch_match_data)

print()
print("=" * 100)
print("编辑器")
print("=" * 100)
call("emojis", c.emojis)
call("at_search", c.at_search, "56")
call("topic_index", c.topic_index, link_id=IMG_LINK)
call("topic_selection", c.topic_selection, link_id=IMG_LINK)
call("topic_selection_search", c.topic_selection_search, "黑神话")
call("owned_game_list", c.owned_game_list, 0, 10)
call("owned_game_hot", c.owned_game_hot, 0, 10)
call("drafts", c.drafts, 0, 10)

print()
print("=" * 100)
print("其他")
print("=" * 100)
call("creator_articles", c.creator_articles)
call("award_users", c.award_users, 1)
call("feedback_mylist", c.feedback_mylist, 0, 10)
call("feedback_report_options", c.feedback_report_options, 730)
call("download_url", c.download_url)
call("release_download(win)", c.release_download, "win")
call("chatroom_tab", c.chatroom_tab)

print()
print("=" * 100)
print(f"ok={ok}  fail={fail}  skip={skip}")
print("=" * 100)
