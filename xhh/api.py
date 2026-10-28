"""接口方法集合。

每个 mixin 对应页面上的一个功能区块，最终与 :class:`xhh.client.Client` 组合成
唯一的 :class:`xhh.Client`。所有方法都返回服务端的 ``result`` 字段（已剔除
``status``/``msg`` 外层），并在失败时抛 :class:`xhh.client.XhhError`。
"""

from __future__ import annotations

import json

from .client import _cos_put

# ---------------------------------------------------------------------------
# 首页 / 社区流
# ---------------------------------------------------------------------------


class FeedsAPI:
    """首页推荐流、轮播、社区（板块）树与版块流。"""

    def feeds(self, offset: int = 0, pull: int = 0, dw: int = 604, **kw):
        """首页推荐流。

        :param offset: 偏移量，步长等于单次返回条数（实测 10 条/页）。
        :param pull:  1 = 下拉刷新（会重新取一批新内容），0 = 翻页。
        :param dw:    设备宽度，影响图文卡片的图片尺寸选择。
        """
        return self.result("/bbs/app/feeds", dict(offset=offset, pull=pull, dw=dw, **kw))

    def banner(self):
        """首页轮播图（``topic_banner``）。"""
        return self.result("/bbs/app/feeds/banner")

    def topic_categories(self):
        """社区树：为你推荐 / 近期热门 / 我的偏好。

        返回 ``{recommend_for_user_topics, latest_hot_topics, subscribed_topics,
        categories, follow_topic_limit}``，前三者是 ``{name, key, children[]}``。
        """
        return self.result("/bbs/app/topic/categories")

    def topic_menu(self, topic_id: int):
        """社区详情页顶部菜单（游戏 / 社区 / 头条 / 赛事 …）。

        ``menu[]`` 的 ``type`` 决定子页面：``game``/``link``/``news``/``webview``/
        ``hot_point``；``filters[]`` 是二级 tab。
        """
        return self.result("/bbs/app/topic/menu", {"topic_id": topic_id})

    def topic_feeds(self, topic_id: int, offset: int = 0, limit: int = 20,
                    sort_filter: str = "", **kw):
        """社区帖子列表。``sort_filter`` 见返回的 ``sort_filter`` 字段（默认 ``hot-rank``）。"""
        return self.result("/bbs/app/topic/feeds", {
            "topic_id": topic_id, "offset": offset, "limit": limit,
            "sort_filter": sort_filter or None, **kw,
        })

    def topic_feeds_news(self, topic_id: int, offset: int = 0, limit: int = 20):
        """社区头条（资讯）列表。"""
        return self.result("/bbs/app/topic/feeds/news", {
            "topic_id": topic_id, "offset": offset, "limit": limit,
        })

    def website_background(self, appid: int):
        """PC 网页端背景图（按游戏定制）。"""
        return self.result("/heyboxpc/v2/client/website_background/v1", {"appid": appid})


# ---------------------------------------------------------------------------
# 搜索
# ---------------------------------------------------------------------------


class SearchAPI:
    """搜索页、搜索联想与综合搜索。"""

    #: ``/bbs/app/api/general/search/v1`` 的 ``search_type`` 取值。
    SEARCH_TYPES = ("general", "link", "game", "hashtag", "user", "mall")

    def search_welcome(self):
        """搜索页默认内容：``default_q``（热搜词）、``Lists``、``ads_banner``。"""
        return self.result("/bbs/app/api/search/welcome_page/v2")

    def search_found(self, force_refresh: bool = False):
        """搜索发现（推荐搜索词卡片）。"""
        return self.result("/bbs/app/api/search/found",
                           {"force_refresh": "true" if force_refresh else "false"})

    def search_suggestion(self, q: str):
        """输入框联想词。"""
        return self.result("/bbs/app/api/search/suggestion/v2", {"q": q})

    def search(self, q: str, search_type: str = "general", offset: int = 0,
               limit: int = 30, game_type: str = "", time_range: str = "",
               filter_tag: str = "", sort_filter: str = "", dw: int = 628,
               is_pull_down: int = 0):
        """综合搜索。

        :param search_type: ``general`` 混合 / ``link`` 帖子 / ``game`` 游戏 /
                            ``hashtag`` 话题 / ``user`` 用户 / ``mall`` 商品。
        :param sort_filter: 排序，取自返回的 ``filter_list`` 里 ``sort_filter``
                            组的 key：``default`` / ``create_date`` / ``award_num`` /
                            ``comment_num``。
        :param time_range: ``link`` 下生效，取自 ``time_range`` 组：
                            ``""`` / ``7d`` / ``30d`` / ``180d`` / ``360d``。
        :param game_type: ``game`` 下生效：``pc``/``mobile``/``console`` 等。
        :param filter_tag: 话题筛选词的 ``tag``（``general`` 下 ``filter_tag``
                           元素里的 ``filter_tags[].tag``），如 ``"地图"``。

        返回的 ``items[]`` 里每项结构是 ``{type, info, report_id}``，实体都在
        ``info`` 里；``type`` 可能是 ``link/game/topic/hashtag/user/mall/space/
        filter_tag/new_game_list/mini_app_v2/tool/relevant_search``；其中
        ``space`` 只是排版留白，做数据清洗时应过滤。
        """
        return self.result("/bbs/app/api/general/search/v1", {
            "q": q,
            "search_type": search_type,
            "game_type": game_type or None,
            "time_range": time_range or None,
            "filter_tag": filter_tag or None,
            "sort_filter": sort_filter or None,
            "is_pull_down": is_pull_down,
            "offset": offset,
            "limit": limit,
            "dw": dw,
        })

    def search_web(self, q: str, search_type: str = "general", offset: int = 0,
                   limit: int = 30, **kw):
        """Web 版搜索（``/v1/web``）。

        与 :meth:`search` 同参同结构，但结果集更偏向网页端可展示的内容
        （同样的 ``q`` 下 ``items`` 更少、不含客户端专属卡片）。
        """
        params = {"q": q, "search_type": search_type, "offset": offset,
                  "limit": limit, "dw": kw.pop("dw", 628), **kw}
        return self.result("/bbs/app/api/general/search/v1/web",
                           {k: v for k, v in params.items() if v not in (None, "")})

    def search_filter_tags(self, q: str):
        """取搜索结果顶部的筛选词条（"全部 / 地图 / 豪华版 …"）。

        返回 ``[{name, tag, report_id}]``，把 ``tag`` 透传回 :meth:`search` 的
        ``filter_tag`` 即可切换。
        """
        r = self.search(q, search_type="general", limit=30)
        for it in r.get("items") or []:
            if it.get("type") == "filter_tag":
                return (it.get("info") or {}).get("filter_tags") or []
        return []

    def search_links(self, q: str, **kw):
        """只搜帖子（``search_type=link`` 的快捷方式）。"""
        return self.search(q, search_type="link", **kw)

    def search_games(self, q: str, **kw):
        """只搜游戏。"""
        return self.search(q, search_type="game", **kw)

    def wiki_search(self, q: str, offset: int = 0, limit: int = 20):
        """Wiki（攻略站）搜索，返回 ``wiki_infos``。"""
        return self.result("/wiki/search", {"q": q, "offset": offset, "limit": limit})

    def wiki_search_wiki(self, query: str):
        """Wiki 联想（编辑器里插入 wiki 卡片用）。

        参数名是 ``query``（不是 ``q``），返回 ``{wikis, search_result}``，
        ``search_result`` 30 条。
        """
        return self.result("/wiki/search_wiki/", {"query": query})

    def mod_search(self, q: str, offset: int = 0, limit: int = 20):
        """工坊（MOD）搜索。"""
        return self.result("/workshop/open/mod_search",
                           {"q": q, "offset": offset, "limit": limit})

    def mod_detail(self, mod_id: int | str):
        """工坊 MOD 详情。

        注意是 **POST**，且 ``mod_id`` 走 query 而不是 body，body 里要带 ``_temp=3``。
        """
        return self.result("/workshop/app/mod_detail", {"mod_id": str(mod_id)},
                           method="POST", data={"_temp": 3})

    def mall_search(self, q: str, offset: int = 0, limit: int = 10):
        """商城搜索。"""
        return self.result("/mall/search/", {"q": q, "offset": offset, "limit": limit})


# ---------------------------------------------------------------------------
# 帖子 / 评论
# ---------------------------------------------------------------------------


class LinkAPI:
    """帖子详情、楼层评论、子评论与互动。"""

    #: 楼中楼评论排序。
    COMMENT_SORTS = ("hot", "time_aes", "time_desc")

    def link_tree(self, link_id: int, page: int = 1, index: int = 1, limit: int = 20,
                  is_first: int = 1, sort_filter: str = "", **kw):
        """帖子详情 + 楼层评论（主页面的唯一接口）。

        :param link_id:    帖子 ID。
        :param page:       第几页评论，从 1 开始。
        :param is_first:   1 = 首次加载（同时返回帖子主体），0 = 翻页。
        :param sort_filter: ``hot`` 热门 / ``time_aes`` 正序 / ``time_desc`` 倒序。

        返回 ``{link, comments, cy_control, folded_comment_tips,
        has_more_floors, show_interact_list, sort_filter, total_floor_num,
        total_page}``。

        帖子的三种内容形态都在这一个 ``link`` 里：

        * 纯文字：``link.text`` 是 HTML 字符串；
        * 图文：``link.text`` 是 **JSON 字符串**，解析后为元素列表，
          第一个元素是 HTML 正文（内嵌 ``<img data-original=...>``），
          其余元素形如 ``{"type":"img","url":...,"width":...,"height":...}``；
        * 视频：``link.has_video=1``，配 ``video_url``（带时效签名）、
          ``video_thumb``、``video_duration``、``video_width``、``video_height``。
        """
        return self.result("/bbs/app/link/tree", {
            "link_id": link_id, "is_first": is_first, "page": page,
            "index": index, "limit": limit,
            "sort_filter": sort_filter or None, **kw,
        })

    def link_tree_v2(self, link_id: int, page: int = 1, index: int = 1, limit: int = 20):
        """帖子接口 v2：只返回 ``{link, comment}``，比 v1 更轻。"""
        return self.result("/bbs/app/link/tree/v2", {
            "link_id": link_id, "is_first": 1, "page": page,
            "index": index, "limit": limit,
        })

    def link_tree_backend(self, link_id: int, page: int = 1, index: int = 1, limit: int = 20):
        """帖子接口 backend 版本（字段与 v1 相同，供 SSR/后台渲染用）。"""
        return self.result("/bbs/app/link/tree/backend", {
            "link_id": link_id, "is_first": 1, "page": page,
            "index": index, "limit": limit,
        })

    def link_by_url(self, share_url: str, page: int = 1, limit: int = 20):
        """用分享链接里的短 ID 打开帖子（``?link_id=`` 参数是 hex 串时走这个）。"""
        return self.result("/bbs/app/link/tree", {
            "link_id": share_url, "is_first": 1, "page": page, "limit": limit,
        })

    def sub_comments(self, link_id: int, root_comment_id: int, offset: int = 0, limit: int = 10):
        """楼中楼子评论。

        :param root_comment_id: 顶层评论 ID（**不是** ``comment_id``/``root_id``）。
        """
        return self.result("/bbs/app/comment/sub/comments", {
            "link_id": link_id, "root_comment_id": root_comment_id,
            "offset": offset, "limit": limit,
        })

    def link_related(self, link_id: int):
        """帖子底部相关推荐：``{related_links, related_topics}``。"""
        return self.result("/bbs/app/link/related/recommend_web", {"link_id": link_id})

    def link_author(self, link_id: int):
        """帖子作者的简要资料。"""
        return self.result("/bbs/app/link/author_info", {"link_id": link_id})

    def forbid_reason(self, link_id: int = 0):
        """举报原因枚举（37 条）。"""
        return self.result("/bbs/app/api/get/forbid_reason",
                           {"link_id": link_id} if link_id else {})

    # ---- 写操作（需登录） ----
    def comment_create(self, link_id: int, text: str, reply_id: int | str = "-1",
                       root_id: int | str = "-1", is_cy: int = 0,
                       imgs: list[str] | None = None):
        """发表评论 / 回复。

        :param reply_id: 被回复的评论 ID，顶层评论传 ``"-1"``。
        :param root_id:  楼中楼里的根评论 ID，非楼中楼传 ``"-1"``。
        :param imgs:     图片 URL 列表（服务端要求用 ``;`` 连接）。
        """
        data = {
            "is_cy": is_cy,
            "link_id": str(link_id),
            "reply_id": str(reply_id),
            "root_id": str(root_id),
            "text": text,
        }
        if imgs:
            data["imgs"] = ";".join(imgs)
        return self.result("/bbs/app/comment/create", method="POST", data=data)

    def link_favour(self, link_id: int, favour: bool = True, favour_type: int = 1,
                    userid: int | str = "", folder_id: str = ""):
        """点赞 / 收藏。

        :param favour_type: 1 = 点赞，2 = 收藏。
        :param folder_id:   收藏夹 ID（收藏时可指定）。
        """
        data = {
            "favour_type": 2 if favour_type == 2 else 1,
            "link_id": str(link_id),
            "favour": int(bool(favour)),
        }
        if userid:
            data["userid"] = str(userid)
        if folder_id:
            data["folder_id"] = str(folder_id)
        return self.result("/bbs/app/link/favour", method="POST", data=data)

    def link_vote(self, link_id: int, opt_ids):
        """在帖子的投票里投票。

        :param opt_ids: 选项 ID 或 ID 列表（``vote_options[].id``）。
                        多选投票用逗号连接，单选也走同一个字段。
        """
        if isinstance(opt_ids, (list, tuple)):
            opt_ids = ",".join(str(o) for o in opt_ids)
        return self.result("/bbs/app/link/vote", method="POST",
                           data={"link_id": str(link_id), "opt_ids": str(opt_ids),
                                 "target": "auto"})

    def link_award(self, link_id: int, award_type: int = 1):
        """给帖子投币（打赏）。

        :param award_type: 1 = 投币，0 = 取消投币（前端就是按
                           ``is_award_link`` 取反传这个值）。
        """
        return self.result("/bbs/app/profile/award/link", method="POST",
                           data={"link_id": str(link_id), "award_type": award_type,
                                 "target": "heybox_app"})

    def comment_support(self, comment_id: int, link_id: int = 0):
        """点赞某条评论。"""
        data = {"comment_id": str(comment_id)}
        if link_id:
            data["link_id"] = str(link_id)
        return self.result("/bbs/app/comment/support", method="POST", data=data)

    def link_report(self, link_id: int, reason_id: int, text: str = ""):
        """举报帖子。``reason_id`` 取自 :meth:`forbid_reason`。"""
        return self.result("/bbs/app/link/report", method="POST", data={
            "link_id": str(link_id), "reason_id": reason_id,
            "text": text, "target": "heybox_app",
        })

    def comment_report(self, comment_id: int, reason_id: int, text: str = ""):
        """举报评论。"""
        return self.result("/bbs/app/comment/report", method="POST", data={
            "comment_id": str(comment_id), "reason_id": reason_id,
            "text": text, "target": "heybox_app",
        })

    def link_delete(self, link_id: int):
        """删除自己的帖子。"""
        return self.result("/bbs/app/link/delete", method="POST",
                           data={"link_id": str(link_id)})

    def build_relation(self, userid: int, relation: str = "blacklist"):
        """拉黑 / 移除拉黑（``relation`` 由服务端枚举，默认黑名单）。"""
        return self.result("/bbs/app/profile/build/relation", method="POST",
                           data={"userid": str(userid), "relation": relation,
                                 "target": "heybox_app"})


# ---------------------------------------------------------------------------
# 用户
# ---------------------------------------------------------------------------


class UserAPI:
    """用户主页、动态、关注、收藏、历史、消息。"""

    def user_profile(self, userid: int | str):
        """用户主页资料（``account_detail``）。"""
        return self.result("/bbs/app/profile/user/profile", {"userid": userid})

    def user_links(self, userid: int | str, offset: int = 0, limit: int = 20):
        """用户发布的帖子列表（``link/list_v2``，注意下划线写法）。"""
        return self.result("/bbs/app/profile/user/link/list_v2", {
            "userid": userid, "offset": offset, "limit": limit,
        })

    def user_events(self, userid: int | str, list_type: str = "moment",
                    lastval: str = "", dw: int = 636):
        """用户动态（``moments``）。

        :param list_type: ``moment``（动态）或 ``dynamic``。
        """
        return self.result("/bbs/app/profile/events", {
            "userid": userid, "list_type": list_type, "lastval": lastval, "dw": dw,
        })

    def follower_list(self, userid: int | str, offset: int = 0, limit: int = 20):
        """粉丝列表。"""
        return self.result("/bbs/app/profile/follower/list",
                           {"userid": userid, "offset": offset, "limit": limit})

    def following_list(self, userid: int | str, offset: int = 0, limit: int = 20):
        """关注列表。"""
        return self.result("/bbs/app/profile/following/list",
                           {"userid": userid, "offset": offset, "limit": limit})

    def follow_user(self, userid: int | str, follow: bool = True,
                    follower_id: int | str | None = None):
        """关注 / 取关用户。

        :param userid: 被关注者（服务端字段名 ``following_id``）。
        :param follow: True 关注，False 取关。
        :param follower_id: 自己的 uid；不传则用客户端上的 ``heybox_id``。
        """
        path = ("/bbs/app/profile/follow/user" if follow
                else "/bbs/app/profile/follow/user/cancel")
        body = {"following_id": str(userid),
                "follower_id": str(follower_id or self.heybox_id or "")}
        return self.result(path, method="POST", data=body)

    # ---- 收藏 ----
    def fav_folders(self):
        """收藏夹列表与统计：``{folders, cy_fav_num, game_list_fav_num,
        wiki_fav_num, user}``。"""
        return self.result("/bbs/app/profile/fav/folders",
                           {"enable_new_style_collect": 1})

    def fav_links(self, offset: int = 0, limit: int = 30, dw: int = 1072):
        """收藏的帖子列表。

        注意：这个接口**不需要** ``folder_id``，靠 ``enable_new_style_collect=1``
        走新版收藏；返回 ``{links[{link:{...}}], has_next}``。
        """
        return self.result("/bbs/app/profile/fav/folder/v2/links", {
            "enable_new_style_collect": 1, "dw": dw,
            "offset": offset, "limit": limit,
        })

    def fav_folder_add(self, name: str, folder_id: int = 0):
        """新建收藏夹（``folder_id=0``）或重命名。"""
        return self.result("/bbs/app/profile/fav/folder/add", method="POST",
                           data={"name": name, "folder_id": folder_id})

    # ---- 浏览历史 ----
    def history_visit(self, offset: int = 0, limit: int = 30, type: str = "all", dw: int = 636):
        """浏览历史（``history_visit``）。"""
        return self.result("/bbs/app/profile/history/visit", {
            "offset": offset, "limit": limit, "type": type, "dw": dw,
        })

    def post_limits(self):
        """当前账号的发帖/评论限制（字数、图片数、每日条数等）。"""
        return self.result("/bbs/app/profile/post/limits")

    def user_permission(self):
        """账号权限位（是否可发视频、是否开发者等）。

        这个接口没有 ``status``/``result`` 外壳，直接返回权限对象。
        """
        return self.result("/bbs/app/api/user/permission")

    def restore_login(self):
        """用 cookie 恢复登录态，返回当前账号信息（10 个字段）。"""
        return self.result("/account/restore_login")

    def logout(self):
        """退出登录。"""
        return self.result("/account/logout")

    # ---- 扫码登录 ----
    def qrcode_url(self):
        """获取登录二维码。

        返回 ``qr_url``（二维码图片地址）与其指向的 ``qr_login`` 长链接；
        客户端拿 ``qr_url`` 生成二维码，然后轮询 :meth:`qr_state`。
        """
        return self.result("/account/get_qrcode_url/")

    def qr_state(self, qr: str):
        """轮询扫码状态（``qr`` 取自 :meth:`qrcode_url` 返回链接里的 ``qr`` 参数）。"""
        return self.result("/account/qr_state/", {"qr": qr})

    def wechat_state(self):
        """微信登录态检查（返回 wiki 权限位与 account_detail）。"""
        return self.result("/account/wechat/state/")

    def login_code(self, payload: dict):
        """短信验证码登录。"""
        return self.result("/account/login_code/", method="POST", data=payload)

    def login(self, payload: dict):
        """账号密码登录（``payload`` 含 ``username``/``password``/``captcha`` 等）。"""
        return self.result("/account/login/", method="POST", data=payload)

    def get_login_code(self, phone: str, **kw):
        """发送登录短信验证码。"""
        return self.result("/account/get_login_code/", method="POST",
                           data={"phone": phone, **kw})

    def google_2fa_verify(self, code: str, **kw):
        """Google 两步验证。"""
        return self.result("/account/google_2fa_verify/", {"code": code, **kw})


# ---------------------------------------------------------------------------
# 消息
# ---------------------------------------------------------------------------


class MessageAPI:
    """消息中心：回复、赞、聚合入口。"""

    #: ``list_type`` 取值（必须是整数）。
    LIST_REPLY = 0        # 回复我的
    LIST_AWARD = 1        # 赞与收藏
    LIST_CENTER = 2       # 消息中心聚合（含各子入口）

    def message(self, list_type: int = LIST_CENTER, offset: int = 0, limit: int = 20):
        """消息列表。

        :param list_type: 0 回复 / 1 赞与收藏 / 2 聚合中心。
                          传字符串会报 ``错误的消息列表``，必须用整数。
        """
        return self.result("/bbs/app/user/message", {
            "list_type": int(list_type), "limit": limit, "offset": offset,
        })

    def official_messages(self, offset: int = 0, limit: int = 20):
        """官方消息列表。"""
        return self.result("/bbs/notify/official_msg_v2/list",
                           {"offset": offset, "limit": limit})

    def discount_messages(self):
        """优惠 / 活动推送消息。"""
        return self.result("/bbs/app/user/discount_message_v2")


# ---------------------------------------------------------------------------
# 游戏
# ---------------------------------------------------------------------------


class GameAPI:
    """游戏详情、库、评分、赛事、Wiki、工坊。"""

    def game_detail(self, appid: int, **kw):
        """游戏详情（PC）。

        返回 59 个字段，重点：``menu_v2``（发布时间/开发商/DLC/媒体评分等条目，
        带 ``heybox://`` 深链）、``comment_stats``（五星分布）、
        ``morelike``、``follow_state``、``button_style_list_v2``。
        """
        return self.result("/game/get_game_detail/", {"appid": appid, **kw})

    def game_detail_mobile(self, appid: int):
        """手游详情（部分 appid 会报 ``非法游戏id``）。"""
        return self.result("/game/mobile/get_game_detail/", {"appid": appid})

    def game_detail_console(self, appid: int):
        """主机游戏详情。"""
        return self.result("/game/console/get_game_detail/", {"appid": appid})

    def game_introduction(self, steam_appid: int):
        """游戏简介正文（HTML）。

        参数名是 ``steam_appid`` + ``return_json=1``，传 ``appid`` 不行。
        """
        return self.result("/game/game_introduction/",
                           {"steam_appid": steam_appid, "return_json": 1})

    def game_infos(self, appids):
        """批量取游戏基础信息。"""
        if isinstance(appids, (list, tuple)):
            appids = ",".join(str(a) for a in appids)
        return self.result("/game/get_game_infos/", {"appids": appids})

    def owned_games(self, offset: int = 0, limit: int = 20, game_type: str = "steam"):
        """我的游戏库。``game_type`` 只接受 ``steam``（pc/mobile/console 均失败）。"""
        return self.result("/game/owned_game/game_list", {
            "offset": offset, "limit": limit, "game_type": game_type,
        })

    def hot_games(self, offset: int = 0, limit: int = 20):
        """热门游戏榜。"""
        return self.result("/game/owned_game/hot_list", {"offset": offset, "limit": limit})

    def game_comments(self, appid: int, offset: int = 0, limit: int = 20, **kw):
        """游戏的盒友评价（打分 + 短评）。"""
        return self.result("/bbs/app/link/game/comments", {
            "appid": appid, "offset": offset, "limit": limit, **kw,
        })

    def game_comment_up(self, comment_id: int):
        """给游戏评价点赞。"""
        return self.result("/bbs/app/link/game/comment/up", method="POST",
                           data={"comment_id": str(comment_id)})

    def follow_game(self, steam_appid: int, follow: bool = True):
        """关注 / 取关游戏（参数名是 ``steam_appid``）。"""
        path = "/account/follow_game/" if follow else "/account/unfollow_game/"
        return self.result(path, method="POST", data={"steam_appid": str(steam_appid)})

    def game_wx_share(self, appid: int):
        """游戏分享卡片信息。"""
        return self.result("/game/wx_share/info/v2", {"appid": appid})

    def steam_screenshots(self, appid: int, offset: int = 0, limit: int = 20):
        """Steam 截图墙。"""
        return self.result("/game/steam/screenshot/list",
                           {"appid": appid, "offset": offset, "limit": limit})

    def self_made_games(self, offset: int = 0, limit: int = 20):
        """个人自制 / 独立游戏列表。"""
        return self.result("/game/self_made_game_list/data/infos",
                           {"offset": offset, "limit": limit})

    def self_made_game_favour(self, game_id: int, favour: bool = True):
        """收藏 / 取消收藏自制游戏。"""
        return self.result("/game/self_made_game_list/favour",
                           {"game_id": game_id, "favour": int(bool(favour))})

    def wiki_infos(self, appid: int):
        """游戏的 Wiki 入口信息。"""
        return self.result("/wiki/get_wiki_infos", {"appid": appid})

    # ---- 赛事中心 ----
    def match_games(self):
        """赛事中心：游戏列表。"""
        return self.result("/oa/match/game/list/data")

    def match_leagues(self, appid: int):
        """赛事中心：某游戏的联赛列表（必须传 ``appid``）。"""
        return self.result("/oa/match/league/list/data", {"appid": appid})

    def match_list(self, appid: int, offset: int = 0, limit: int = 20):
        """赛事中心：赛程列表（必须传 ``appid``）。"""
        return self.result("/oa/match/match/list/data",
                           {"appid": appid, "offset": offset, "limit": limit})

    def watch_match(self, match_id: int | str):
        """订阅 / 观看某场比赛。"""
        return self.result("/game/match/watch_match", method="POST",
                           data={"match_id": str(match_id)})

    def unwatch_match(self, match_id: int | str):
        """取消订阅比赛。"""
        return self.result("/game/match/unwatch_match", method="POST",
                           data={"match_id": str(match_id)})

    def match_leagues_batch(self):
        """赛事模块的批量联赛数据。"""
        return self.result("/game/match/leagues")

    def batch_match_data(self, **kw):
        """赛事模块的批量比赛数据。"""
        return self.result("/game/match/batch_match_data", kw)


# ---------------------------------------------------------------------------
# 发帖编辑器
# ---------------------------------------------------------------------------


class EditorAPI:
    """发帖编辑器：社区选择、表情、@人、图片上传、发布。"""

    def emojis(self):
        """可用表情包列表（小黑盒表情 ``[cube_xxx]``）。"""
        return self.result("/bbs/app/api/emojis/list")

    def at_search(self, q: str, limit: int = 10):
        """@ 提及用户搜索。"""
        return self.result("/bbs/app/api/at/search", {"q": q, "limit": limit})

    def topic_index(self, is_post: int = 1, post_tab: int = 1, is_new_style: int = 1,
                    type: str = "list", link_id: int = 0, **kw):
        """发帖编辑器初始化：可选社区、置顶公告、声明选项。

        没有 ``status``/``result`` 外壳，直接返回
        ``{topics_list_v2, notify, post_article_alert, extra_declaration_choice,
        enable_post_declaration_v2, post_article_plan, post_pic_link_plan,
        title_notify}``。
        """
        return self.result("/bbs/app/api/topic/index", {
            "is_post": is_post, "post_tab": post_tab, "is_new_style": is_new_style,
            "type": type, "link_id": link_id or None,
            "need_award_bubble_info": 1, **kw,
        })

    def topic_selection(self, is_post: int = 1, post_tab: int = 1, is_new_style: int = 1,
                        type: str = "list", link_id: int = 0):
        """"选择社区"弹窗的数据源。"""
        return self.result("/bbs/app/api/post_editor/topic_selection/index", {
            "is_post": is_post, "post_tab": post_tab, "is_new_style": is_new_style,
            "type": type, "link_id": link_id or None,
        })

    def topic_selection_search(self, q: str, limit: int = 20):
        """"选择社区"弹窗里的搜索。"""
        return self.result("/bbs/app/api/post_editor/topic_selection/search",
                           {"q": q, "limit": limit})

    def owned_game_list(self, offset: int = 0, limit: int = 20, game_type: str = "steam"):
        """发帖时可关联的"我的游戏"（``game_type`` 只能传 ``steam``）。"""
        return self.result("/game/owned_game/game_list",
                           {"game_type": game_type, "offset": offset, "limit": limit})

    def owned_game_hot(self, offset: int = 0, limit: int = 20, game_type: str = "steam"):
        """发帖时可关联的热门游戏。"""
        return self.result("/game/owned_game/hot_list",
                           {"game_type": game_type, "offset": offset, "limit": limit})

    def drafts(self, offset: int = 0, limit: int = 20):
        """我的草稿箱。"""
        return self.result("/bbs/app/link/drafts", {"offset": offset, "limit": limit})

    def link_edit_info(self, link_id: int):
        """编辑帖子前拉取原文（需要编辑权限）。"""
        return self.result("/bbs/app/link/edit/info", {"link_id": link_id})

    def link_change_status(self, link_id: int, status: int = 0):
        """草稿箱里切换稿件状态。

        注意：Web 端调用会返回 ``请前往 app 使用该功能``，只在 App 内可用。
        """
        return self.result("/bbs/app/link/change/status",
                           {"link_id": link_id, "status": status})

    # ---- 上传（腾讯云 COS，三步走完拿到可访问 URL） ----
    def upload_info(self, files, scope: str = "bbs", need_cache: int = 0):
        """第一步：登记要上传的文件，拿到对象名与存储桶。

        :param files: 单个文件描述 dict 或它们的列表。每个描述形如
                      ``{"name": "a.png", "mimetype": "image/png",
                         "fsize": 18234, "width": 100, "height": 100,
                         "duration": 0}``。
        :param scope: web 端固定用 ``"bbs"``（业务后台另有 ``business``）。
        :return: ``{"keys": ["/web/bbs/2026/10/28/xxx.png"], "region":
                  "ap-shanghai", "bucket": "imgheybox-1251007209",
                  "host": "imgheybox.max-c.com"}``
        """
        if isinstance(files, dict):
            files = [files]
        infos = []
        for f in files:
            f = dict(f)
            infos.append({
                "name": f.pop("name", ""),
                "mimetype": f.pop("mimetype", ""),
                "fsize": f.pop("fsize", f.pop("size", 0)),
                "width": f.pop("width", 0),
                "height": f.pop("height", 0),
                "duration": f.pop("duration", 0),
                **f,
            })
        return self.result(
            "/bbs/app/api/qcloud/cos/upload/info/v2",
            method="POST",
            data={"file_infos": json.dumps(infos, ensure_ascii=False),
                  "scope": scope, "need_cache": need_cache},
        )

    def upload_token(self, bucket: str, keys, mimetypes):
        """第二步：用桶名 + 对象名换 COS 临时凭证，直接 PUT 上去。

        :param keys: :meth:`upload_info` 返回的 ``keys``。
        :param mimetypes: 与 ``keys`` 一一对应的 MIME 列表。

        拿到 ``credentials.tmpSecretId/tmpSecretKey/sessionToken`` 后，用
        COS SDK 或任意 S3/COS 兼容客户端 PUT 到 ``bucket`` + ``key``。
        """
        if isinstance(keys, str):
            keys = [keys]
        if isinstance(mimetypes, str):
            mimetypes = [mimetypes]
        return self.result(
            "/bbs/app/api/qcloud/cos/upload/token/v2",
            method="POST",
            data={"bucket": bucket,
                  "keys": json.dumps(keys, ensure_ascii=False),
                  "mimetypes": json.dumps(mimetypes, ensure_ascii=False)},
        )

    def upload_callback(self, keys):
        """第三步：告诉服务端上传完成，换回最终可访问 URL。

        :return: ``{"preview_urls": [...], "thumbs": [...], ...}``
                 ``preview_urls[0]`` 就是可以直接塞进帖子/评论里的图片地址。
        """
        if isinstance(keys, str):
            keys = [keys]
        return self.result(
            "/bbs/app/api/qcloud/cos/upload/callback/v2",
            method="POST",
            data={"is_finished": True, "keys": json.dumps(keys, ensure_ascii=False)},
        )

    def upload_heartbeat(self, keys):
        """大文件分片上传时的心跳（每 3 分钟一次），小文件可跳过。"""
        if isinstance(keys, str):
            keys = [keys]
        return self.result(
            "/bbs/app/api/qcloud/cos/upload/heartbeat",
            method="POST",
            data={"keys": json.dumps(keys, ensure_ascii=False)},
        )

    def upload_image(self, data_or_path, filename: str = "image.png",
                     mimetype: str = "image/png", timeout: float = 120):
        """一步到位上传一张图片/一段视频，返回最终 URL。

        完整走完 info → token → COS PUT → callback，纯 ``urllib`` 实现，
        不依赖腾讯云 SDK。

        :param data_or_path: ``bytes`` 或本地文件路径。
        :return: ``{"url":..., "thumb":..., "key":..., "bucket":...}``
        """
        raw = data_or_path
        if isinstance(data_or_path, (str, bytes)) and not isinstance(data_or_path, bytes):
            with open(data_or_path, "rb") as fh:
                raw = fh.read()
            import os as _os
            filename = _os.path.basename(data_or_path) or filename
            if mimetype == "image/png":
                ext = filename.rsplit(".", 1)[-1].lower()
                mimetype = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                            "png": "image/png", "gif": "image/gif",
                            "webp": "image/webp", "mp4": "video/mp4"}.get(ext, mimetype)

        # 1) info
        info = self.upload_info({"name": filename, "mimetype": mimetype,
                                 "fsize": len(raw)}, scope="bbs")
        key, bucket, region = info["keys"][0], info["bucket"], info.get("region")

        # 2) token
        tok = self.upload_token(bucket, [key], [mimetype])
        cred = tok["credentials"]

        # 3) PUT 到 COS
        sign_time = f"{tok['startTime']};{tok['expiredTime']}"
        _cos_put(region, bucket, key, raw, mimetype, sign_time,
                 cred["tmpSecretId"], cred["tmpSecretKey"], cred["sessionToken"],
                 timeout=timeout)

        # 4) callback
        cb = self.upload_callback([key])
        return {
            "url": (cb.get("preview_urls") or [None])[0],
            "thumb": (cb.get("thumbs") or [None])[0],
            "key": key, "bucket": bucket, "raw": cb,
        }

    def copy_image_by_url(self, url: str, **kw):
        """把外链图片转存到小黑盒图床。"""
        return self.result("/bbs/app/api/qcloud/cos/copy/image/by/url",
                           {"url": url, **kw})

    def original_image(self, url: str, **kw):
        """取图片原图地址（去掉缩略参数后的版本）。"""
        return self.result("/bbs/app/api/original/image", {"url": url, **kw})

    # ---- 发布 ----
    def post_link(self, payload: dict):
        """发布图文帖。payload 结构见文档「发帖」一节。"""
        return self.result("/bbs/app/api/link/post", method="POST", data=payload)

    def post_video_link(self, payload: dict):
        """发布视频帖。"""
        return self.result("/bbs/app/api/video-link/post", method="POST", data=payload)

    def post_marketing_link(self, payload: dict):
        """带任务/激励的投稿（创作激励计划）。"""
        return self.result("/bbs/content_marketing/author/link/post",
                           method="POST", data=payload)

    def marketing_tasks(self, offset: int = 0, limit: int = 20):
        """创作激励任务列表。"""
        return self.result("/bbs/content_marketing/post/task_list",
                           {"offset": offset, "limit": limit})


# ---------------------------------------------------------------------------
# 其他（创作者中心、反馈、客户端下载、聊天室）
# ---------------------------------------------------------------------------


class MiscAPI:
    """创作者中心、反馈、客户端下载、聊天室入口。"""

    def creator_articles(self, article_type: str = "all", state: str = "all",
                         sort: str = "create_at", offset: int = 0, limit: int = 20,
                         timeout: float = 60):
        """创作者中心 - 我的稿件列表。

        注意：官方把 ``state`` 拼成了 ``artilce_state``（不是 article），
        必须照抄才能命中。该接口响应很慢，默认给 60s 超时。
        """
        return self.result("/bbs/app/author/concept/article/list", {
            "article_type": article_type, "artilce_state": state,
            "sort_filter": sort, "offset": offset, "limit": limit,
        }, timeout=timeout)

    def creator_article_data(self, **kw):
        """创作者中心 - 稿件数据（阅读/互动曲线）。"""
        return self.result("/bbs/app/author/concept/article/data", kw)

    def award_users(self, award_ids):
        """打赏/投币用户列表。

        :param award_ids: 打赏 ID 或 ID 列表（服务端接收 ``award_ids=1,2,3``）。
                          打赏 ID 来自帖子的 ``awards[].award_id``。
        """
        if isinstance(award_ids, (list, tuple)):
            award_ids = ",".join(str(a) for a in award_ids)
        return self.result("/bbs/app/api/article/get_award_users", {"award_ids": award_ids})

    # ---- 反馈 ----
    def feedback_mylist(self, offset: int = 0, limit: int = 20):
        """我的反馈工单。"""
        return self.result("/bbs/web/feedback/mylist", {"offset": offset, "limit": limit})

    def feedback_edit_info(self, feedback_id: int):
        """单条反馈详情。"""
        return self.result("/bbs/web/feedback/edit/info", {"feedback_id": feedback_id})

    def feedback_close(self, feedback_id: int):
        """撤销 / 关闭反馈工单。"""
        return self.result("/bbs/app/feedback/close", {"feedback_id": feedback_id})

    def feedback_report_options(self, appid: int = 0):
        """举报/反馈的选项树。"""
        return self.result("/bbs/web/feedback/pubg/report_options",
                           {"appid": appid} if appid else {})

    def feedback_post(self, payload: dict):
        """提交反馈。"""
        return self.result("/bbs/web/feedback/user/post", method="POST", data=payload)

    # ---- 客户端 ----
    def download_url(self):
        """PC 客户端通用下载地址。"""
        return self.result("/heyboxpc/client/get_download_url")

    def release_download(self, platform: str = "win"):
        """分平台/分渠道的客户端发布包信息。

        :param platform: ``win`` 或 ``mac``（小写，服务端只认这两个）。
        """
        return self.result("/heyboxpc/v2/client/release/download/v1",
                           {"platform": platform})

    def channel_download_page(self, **kw):
        """渠道下载引导页。"""
        return self.result("/heyboxpc/v2/client/channel_download_page/v1", kw)

    def acquisition_issue(self, payload: dict):
        """渠道拉新上报。"""
        return self.result("/heyboxpc/v2/client/acquisition/issue/v1",
                           method="POST", data=payload)

    def pc_download_click(self, payload: dict):
        """"下载 PC 版"点击埋点。"""
        return self.result("/web/website/home/pc_download/click", method="POST", data=payload)

    # ---- 聊天室（语音房） ----
    def chatroom_tab(self):
        """语音房入口（返回独立域名 ``url`` 与邀请/下载链接）。"""
        return self.result("/chatroom/v2/common/tab")

    def chatroom_card(self, **params):
        """语音房卡片信息（参数由客户端透传，web 端未暴露明文参数名）。"""
        return self.result("/chatroom/v2/room/card_info", {"need_encrypt": 0, **params})

    def joined_rooms(self, **kw):
        """我加入的语音房。"""
        return self.result("/chatroom/mobile/search/joined_rooms", kw)

    def chatroom_report(self, payload: dict):
        """举报语音房 / 语音房用户。"""
        return self.result("/chatroom/mobile/report", method="POST", data=payload)

    def chatroom_msg_user(self, userid: int | str, **kw):
        """语音房会话里拉某用户的消息。"""
        return self.result("/chatroom/v2/msg/user", {"userid": userid, **kw})

    def web_report(self, payload: dict):
        """网页端举报上报（下载页等）。"""
        return self.result("/heyboxpc/v2/report/web", method="POST",
                           data={"target": "heybox_app", **payload})

    def box_data_callback(self, payload: dict | None = None):
        """风控 SDK（数美）数据回传，前端自动调用，一般无需手动触发。"""
        return self.result("/rc/box_data/callback", method="POST", data=payload or {})

    def stranger_messages(self, offset: int = 0, limit: int = 20):
        """陌生人私信列表。

        路径末尾带斜杠且**不带** userid —— 拼成 ``/chat/stranger_messages/123``
        会被服务端当静态资源返回 404。返回 ``{list: [{count, user_a, user_b, …}]}``。
        """
        return self.result("/chat/stranger_messages/",
                           {"offset": offset, "limit": limit})
