"""对全部端点做一次统一采集，输出结构摘要（供文档使用）。"""
import io
import json
import os
import sys
import time

sys.path.insert(0, ".")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import xhh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _cred

PK = _cred.load_pkey()
c = xhh.Client(cookie="user_pkey=" + PK, heybox_id=_cred.load_heybox_id(), timeout=30)

LINK = 195147076          # 普通图文帖
VIDEO = 195148022         # 视频帖
UID = int(_cred.load_heybox_id())

# (key, method, path, params, data)
CASES = [
    # ---- 首页 / 信息流 ----
    ("feeds", "GET", "/bbs/app/feeds", {"offset": 0, "pull": 0, "dw": 604}, None),
    ("banner", "GET", "/bbs/app/feeds/banner", {}, None),
    ("topic_categories", "GET", "/bbs/app/topic/categories", {}, None),
    ("topic_menu", "GET", "/bbs/app/topic/menu", {}, None),
    ("topic_feeds", "GET", "/bbs/app/topic/feeds", {"topic_id": 1021, "offset": 0, "limit": 20}, None),
    ("topic_feeds_news", "GET", "/bbs/app/topic/feeds/news", {"offset": 0, "limit": 20}, None),
    ("website_background", "GET", "/heyboxpc/v2/client/website_background/v1", {}, None),

    # ---- 搜索 ----
    ("search_welcome", "GET", "/bbs/app/api/search/welcome_page/v2", {}, None),
    ("search_found", "GET", "/bbs/app/api/search/found", {"force_refresh": "false"}, None),
    ("search_suggestion", "GET", "/bbs/app/api/search/suggestion/v2", {"q": "黑神话"}, None),
    ("search_general", "GET", "/bbs/app/api/general/search/v1",
     {"q": "黑神话", "offset": 0, "limit": 20, "search_type": "general", "is_pull_down": 0}, None),
    ("search_web", "GET", "/bbs/app/api/general/search/v1/web",
     {"q": "黑神话", "offset": 0, "limit": 20}, None),
    ("search_wiki", "GET", "/wiki/search", {"q": "黑神话", "offset": 0, "limit": 20}, None),
    ("search_mod", "GET", "/workshop/open/mod_search", {"q": "mod", "offset": 0, "limit": 20}, None),
    ("search_mall", "GET", "/mall/search/", {"q": "手柄", "offset": 0, "limit": 10}, None),

    # ---- 帖子 ----
    ("link_tree", "GET", "/bbs/app/link/tree",
     {"link_id": LINK, "is_first": 1, "page": 1, "index": 1, "limit": 20}, None),
    ("link_tree_video", "GET", "/bbs/app/link/tree",
     {"link_id": VIDEO, "is_first": 1, "page": 1, "index": 1, "limit": 20}, None),
    ("link_tree_backend", "GET", "/bbs/app/link/tree/backend",
     {"link_id": LINK, "is_first": 1, "page": 1, "index": 1, "limit": 20}, None),
    ("link_tree_v2", "GET", "/bbs/app/link/tree/v2",
     {"link_id": LINK, "is_first": 1, "page": 1, "index": 1, "limit": 20}, None),
    ("link_related", "GET", "/bbs/app/link/related/recommend_web", {"link_id": LINK}, None),
    ("link_author", "GET", "/bbs/app/link/author_info", {"link_id": LINK}, None),
    ("sub_comments", "GET", "/bbs/app/comment/sub/comments",
     {"link_id": LINK, "root_comment_id": 985455842, "offset": 0, "limit": 10}, None),
    ("link_drafts", "GET", "/bbs/app/link/drafts", {"offset": 0, "limit": 20}, None),

    # ---- 用户 ----
    ("user_profile", "GET", "/bbs/app/profile/user/profile", {"userid": UID}, None),
    ("user_links_v2", "GET", "/bbs/app/profile/user/link/list_v2",
     {"userid": UID, "offset": 0, "limit": 20}, None),
    ("user_events", "GET", "/bbs/app/profile/events",
     {"userid": UID, "list_type": "moment", "lastval": "", "dw": 636}, None),
    ("fav_folders", "GET", "/bbs/app/profile/fav/folders", {}, None),
    ("fav_links", "GET", "/bbs/app/profile/fav/folder/v2/links",
     {"folder_id": 0, "offset": 0, "limit": 20}, None),
    ("history_visit", "GET", "/bbs/app/profile/history/visit",
     {"offset": 0, "limit": 30, "type": "all", "dw": 636}, None),
    ("follower_list", "GET", "/bbs/app/profile/follower/list", {"userid": UID, "offset": 0, "limit": 20}, None),
    ("following_list", "GET", "/bbs/app/profile/following/list", {"userid": UID, "offset": 0, "limit": 20}, None),
    ("post_limits", "GET", "/bbs/app/profile/post/limits", {}, None),
    ("message", "GET", "/bbs/app/user/message", {"list_type": 0, "limit": 20, "offset": 0}, None),
    ("message_award", "GET", "/bbs/app/user/message", {"list_type": 1, "limit": 20, "offset": 0}, None),
    ("message_center", "GET", "/bbs/app/user/message", {"list_type": 2, "limit": 20, "offset": 0}, None),
    ("official_msg", "GET", "/bbs/notify/official_msg_v2/list", {"offset": 0, "limit": 20}, None),
    ("discount_msg", "GET", "/bbs/app/user/discount_message_v2", {}, None),
    ("user_permission", "GET", "/bbs/app/api/user/permission", {}, None),
    ("restore_login", "GET", "/account/restore_login", {}, None),

    # ---- 编辑器 ----
    ("emojis", "GET", "/bbs/app/api/emojis/list", {}, None),
    ("at_search", "GET", "/bbs/app/api/at/search", {"q": "56", "limit": 10}, None),
    ("topic_index", "GET", "/bbs/app/api/topic/index",
     {"is_post": 1, "post_tab": 1, "is_new_style": 1, "type": "list", "link_id": LINK,
      "need_award_bubble_info": 1}, None),
    ("topic_selection", "GET", "/bbs/app/api/post_editor/topic_selection/index",
     {"is_post": 1, "post_tab": 1, "is_new_style": 1, "type": "list", "link_id": LINK}, None),
    ("topic_selection_search", "GET", "/bbs/app/api/post_editor/topic_selection/search",
     {"q": "黑神话", "limit": 20}, None),
    ("forbid_reason", "GET", "/bbs/app/api/get/forbid_reason", {"link_id": LINK}, None),

    # ---- 游戏 ----
    ("game_infos", "GET", "/game/get_game_infos/", {"appids": 2358720}, None),
    ("game_detail", "GET", "/game/get_game_detail/", {"appid": 2358720}, None),
    ("console_game_detail", "GET", "/game/console/get_game_detail/", {"appid": 2358720}, None),
    ("owned_games", "GET", "/game/owned_game/game_list", {"limit": 20, "offset": 0, "game_type": "steam"}, None),
    ("hot_games", "GET", "/game/owned_game/hot_list", {"limit": 20, "offset": 0}, None),
    ("game_comments", "GET", "/bbs/app/link/game/comments", {"appid": 2358720, "offset": 0, "limit": 20}, None),
    ("game_match_leagues", "GET", "/game/match/leagues", {}, None),
    ("game_match_batch", "GET", "/game/match/batch_match_data", {}, None),
    ("game_wx_share", "GET", "/game/wx_share/info/v2", {"appid": 2358720}, None),
    ("self_made_games", "GET", "/game/self_made_game_list/data/infos", {"offset": 0, "limit": 20}, None),
    ("wiki_infos", "GET", "/wiki/get_wiki_infos", {"appid": 2358720}, None),
    ("steam_screenshots", "GET", "/game/steam/screenshot/list", {"appid": 2358720, "offset": 0, "limit": 20}, None),

    # ---- 赛事 ----
    ("oa_games", "GET", "/oa/match/game/list/data", {}, None),
    ("oa_leagues", "GET", "/oa/match/league/list/data", {"game_id": 1}, None),
    ("oa_matches", "GET", "/oa/match/match/list/data", {"league_id": 1}, None),

    # ---- 聊天室 / 创作者 ----
    ("chatroom_tab", "GET", "/chatroom/v2/common/tab", {}, None),
    ("chatroom_card", "GET", "/chatroom/v2/room/card_info", {"room_id": 1}, None),
    ("creator_articles", "GET", "/bbs/app/author/concept/article/list",
     {"article_type": "all", "artilce_state": "all", "sort_filter": "create_at", "offset": 0, "limit": 20}, None),
    ("marketing_tasks", "GET", "/bbs/content_marketing/post/task_list", {"offset": 0, "limit": 20}, None),
    ("feedback_mylist", "GET", "/bbs/web/feedback/mylist", {"offset": 0, "limit": 20}, None),

    # ---- 客户端下载 ----
    ("pc_download", "GET", "/heyboxpc/client/get_download_url", {}, None),
    ("pc_release", "GET", "/heyboxpc/v2/client/release/download/v1", {}, None),
]


def shape(v, depth=0, maxdepth=3):
    """把 JSON 压成 {key: type} 形状树。"""
    if isinstance(v, dict):
        if depth >= maxdepth:
            return "{...%d keys}" % len(v)
        return {k: shape(x, depth + 1, maxdepth) for k, x in list(v.items())}
    if isinstance(v, list):
        if not v:
            return "[]"
        if depth >= maxdepth:
            return "[%d]" % len(v)
        return [shape(v[0], depth + 1, maxdepth)]
    if isinstance(v, str):
        return f'str"{v[:40]}"'
    return v


report = {}
for key, method, path, params, data in CASES:
    t0 = time.time()
    try:
        r = c.request(method, path, params, data)
        err = None
    except Exception as e:
        r, err = None, str(e)[:200]
    dt = int((time.time() - t0) * 1000)
    if err:
        print(f"{'EXC':10s} {dt:>5}ms {key:22s} {path}  {err[:80]}")
        report[key] = {"path": path, "method": method, "params": params, "error": err}
        continue
    st = r.get("status") if isinstance(r, dict) else None
    res = r.get("result") if isinstance(r, dict) else None
    n = len(res) if isinstance(res, (dict, list)) else 0
    print(f"{str(st):10s} {dt:>5}ms {key:22s} {path}  n={n}")
    report[key] = {
        "path": path, "method": method, "params": params,
        "status": st, "result_keys": sorted(res.keys())[:40] if isinstance(res, dict) else None,
        "shape": shape(res) if st == "ok" else None,
        "raw_head": json.dumps(r, ensure_ascii=False)[:1200],
    }
    time.sleep(0.15)

json.dump(report, open("api_shapes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nsaved api_shapes.json")
