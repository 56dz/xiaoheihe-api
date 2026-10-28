# -*- coding: utf-8 -*-
"""全量端点探测（登录态）：GET 全打，POST 只打只读/无害的。

输出 probe_full.json：{path: {status, msg, result_shape, sample, elapsed}}
"""
import json, os, sys, io, time, traceback
sys.path.insert(0, '.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import xhh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _cred

PK = _cred.load_pkey()
c = xhh.Client(cookie="user_pkey=" + PK, heybox_id=_cred.load_heybox_id(), timeout=25)

# 已有真实样本做参照的 ID
LINK = 195147076
USER = int(_cred.load_heybox_id())
GAME = 2358720

GETS = [
    # ---------- 首页 / 推荐 ----------
    ("/bbs/app/feeds", {"offset": 0, "pull": 0, "dw": 604}),
    ("/bbs/app/feeds/banner", {}),
    # ---------- 社区 ----------
    ("/bbs/app/topic/categories", {}),
    ("/bbs/app/topic/menu", {"topic_id": 1}),
    ("/bbs/app/topic/menu", {"appid": GAME}),
    ("/bbs/app/topic/feeds", {"topic_id": 1, "offset": 0, "limit": 10, "lastval": "", "dw": 604}),
    ("/bbs/app/topic/feeds", {"topic_id": 1, "offset": 0, "limit": 10, "lastval": "", "dw": 604, "sort_filter": "hot-rank"}),
    ("/bbs/app/topic/feeds/news", {"topic_id": 1, "offset": 0, "limit": 10}),
    # ---------- 搜索 ----------
    ("/bbs/app/api/search/welcome_page/v2", {}),
    ("/bbs/app/api/search/found", {"force_refresh": "false"}),
    ("/bbs/app/api/search/suggestion/v2", {"q": "黑神话"}),
    ("/bbs/app/api/general/search/v1", {"q": "黑神话", "search_type": "general", "is_pull_down": 0, "offset": 0, "limit": 30, "dw": 628}),
    ("/bbs/app/api/general/search/v1", {"q": "黑神话", "search_type": "link", "is_pull_down": 0, "offset": 0, "limit": 30, "dw": 628}),
    ("/bbs/app/api/general/search/v1", {"q": "黑神话", "search_type": "user", "is_pull_down": 0, "offset": 0, "limit": 30, "dw": 628}),
    ("/bbs/app/api/general/search/v1", {"q": "黑神话", "search_type": "game", "is_pull_down": 0, "offset": 0, "limit": 30, "dw": 628}),
    ("/bbs/app/api/general/search/v1", {"q": "黑神话", "search_type": "topic", "is_pull_down": 0, "offset": 0, "limit": 30, "dw": 628}),
    # ---------- 帖子详情 ----------
    ("/bbs/app/link/tree", {"link_id": LINK, "is_first": 1, "page": 1, "index": 1, "limit": 20, "owner_only": 0}),
    ("/bbs/app/link/tree/v2", {"link_id": LINK, "is_first": 1, "page": 1, "index": 1, "limit": 20}),
    ("/bbs/app/link/tree/backend", {"link_id": LINK, "page": 1, "limit": 20}),
    ("/bbs/app/link/related/recommend_web", {"link_id": LINK, "device_info": "Chrome", "h_src": "hGEZL0UdafTw7SbLi"}),
    ("/bbs/app/link/author_info", {"link_id": LINK}),
    # ---------- 评论 ----------
    ("/bbs/app/comment/sub/comments", {"link_id": LINK, "root_comment_id": 0, "offset": 0, "limit": 10}),
    ("/bbs/app/link/game/comments", {"appid": GAME, "offset": 0, "limit": 20, "sort_type": "", "api_version": 2}),
    # ---------- 杂项 ----------
    ("/bbs/app/api/emojis/list", {}),
    ("/bbs/app/api/user/permission", {}),
    ("/bbs/app/api/get/forbid_reason", {}),
    ("/bbs/app/api/original/image", {"img_url": "https://imgheybox1.max-c.com/bbs/2026/10/24/82e3c86975c8589b44973f0cec43d1a2.webp"}),
    ("/bbs/app/api/article/get_award_users", {"link_id": LINK}),
    # ---------- 用户 ----------
    ("/bbs/app/profile/user/profile", {"userid": USER}),
    ("/bbs/app/profile/events", {"userid": USER, "list_type": "moment", "lastval": "", "dw": 636}),
    ("/bbs/app/profile/build/relation", {"userid": USER}),
    ("/bbs/app/profile/award/link", {"userid": USER, "offset": 0, "limit": 20}),
    ("/bbs/app/profile/fav/folders", {}),
    ("/bbs/app/profile/fav/folder/v2/links", {"offset": 0, "limit": 20, "dw": 636, "enable_new_style_collect": 1}),
    ("/bbs/app/profile/history/visit", {"offset": 0, "limit": 30, "type": "all", "dw": 636}),
    ("/bbs/app/author/concept/article/list", {"article_type": "all", "artilce_state": "all", "sort_filter": "create_at", "offset": 0, "limit": 20}),
    # ---------- 账号 ----------
    ("/account/restore_login", {}),
    # ---------- 游戏 ----------
    ("/game/get_game_infos/", {"appids": GAME}),
    ("/game/mobile/get_game_detail/", {"appid": GAME, "platf": "steam"}),
    ("/game/get_game_detail/", {"appid": GAME}),
    ("/game/console/get_game_detail/", {"appid": GAME}),
    ("/game/item/show", {"appid": GAME}),
    ("/game/match/leagues", {"appid": GAME}),
    ("/game/match/batch_match_data", {"leagues": ""}),
    ("/game/self_made_game_list/data/infos", {"appid": GAME}),
    ("/game/wx_share/info/v2", {"appid": GAME}),
    # ---------- wiki ----------
    ("/wiki/get_wiki_infos", {"appid": GAME}),
    # ---------- 商城 ----------
    ("/mall/sku/show", {}),
    ("/mall/sku/detail/", {"sku_id": 1}),
    # ---------- PC 客户端 ----------
    ("/heyboxpc/v2/client/website_background/v1", {"appid": GAME}),
    ("/heyboxpc/client/get_download_url", {}),
    # ---------- 其他 ----------
    ("/bbs/app/render/debug/info", {}),
    ("/account/follow_game/", {"appid": GAME}),
]


def shape(v, depth=0, maxk=12):
    if isinstance(v, dict):
        if depth >= 2:
            return "{...%d keys}" % len(v)
        items = list(v.items())[:maxk]
        return "{" + ", ".join("%s:%s" % (k, shape(x, depth + 1, maxk)) for k, x in items) + "}"
    if isinstance(v, list):
        if not v:
            return "[]"
        if depth >= 2:
            return "[%d]" % len(v)
        return "[%d x %s]" % (len(v), shape(v[0], depth + 1, maxk))
    if isinstance(v, str):
        return repr(v.replace("\n", " ")[:36])
    return repr(v)


out = {}
for path, params in GETS:
    key = path + ("?" + json.dumps(params, ensure_ascii=False) if params else "")
    t0 = time.time()
    try:
        r = c.get(path, **params)
    except Exception as e:
        print("EXC  %-52s %s" % (path, str(e)[:70]))
        out[key] = {"exception": str(e)[:200]}
        continue
    dt = time.time() - t0
    st, msg, res = r.get("status"), r.get("msg"), r.get("result")
    out[key] = {"status": st, "msg": msg, "result": res,
                "shape": shape(res), "elapsed": round(dt, 2)}
    print("%-4s %-52s %5.2fs status=%-8s %s" % (
        "OK" if st == "ok" else "!!", path, dt, st, shape(res)[:110]))
    time.sleep(0.4)

json.dump(out, open("probe_full.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nsaved probe_full.json  (%d endpoints)" % len(out))
