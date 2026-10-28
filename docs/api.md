# 接口清单

由 `tools/gen_docs.py` 从 `xhh/api.py` 自动生成，与代码保持一致。

约定：

* 所有方法返回服务端 `result` 字段（已剥掉 `status` / `msg` 外壳）；
* 请求失败抛 `xhh.XhhError`，命中验证码风控抛它的子类 `xhh.CaptchaRequired`；
* 每个请求都会自动带上签名三件套 `hkey` / `_time` / `nonce` 和 9 个公共参数，下表只列业务参数。

---

## 首页 / 社区流

### `feeds(self, offset: 'int' = 0, pull: 'int' = 0, dw: 'int' = 604, **kw)`

`GET /bbs/app/feeds`

首页推荐流。

:param offset: 偏移量，步长等于单次返回条数（实测 10 条/页）。
:param pull:  1 = 下拉刷新（会重新取一批新内容），0 = 翻页。
:param dw:    设备宽度，影响图文卡片的图片尺寸选择。

### `banner(self)`

`GET /bbs/app/feeds/banner`

首页轮播图（``topic_banner``）。

### `topic_categories(self)`

`GET /bbs/app/topic/categories`

社区树：为你推荐 / 近期热门 / 我的偏好。

返回 ``{recommend_for_user_topics, latest_hot_topics, subscribed_topics,
categories, follow_topic_limit}``，前三者是 ``{name, key, children[]}``。

### `topic_menu(self, topic_id: 'int')`

`GET /bbs/app/topic/menu`

社区详情页顶部菜单（游戏 / 社区 / 头条 / 赛事 …）。

``menu[]`` 的 ``type`` 决定子页面：``game``/``link``/``news``/``webview``/
``hot_point``；``filters[]`` 是二级 tab。

### `topic_feeds(self, topic_id: 'int', offset: 'int' = 0, limit: 'int' = 20, sort_filter: 'str' = '', **kw)`

`GET /bbs/app/topic/feeds`

社区帖子列表。``sort_filter`` 见返回的 ``sort_filter`` 字段（默认 ``hot-rank``）。

### `topic_feeds_news(self, topic_id: 'int', offset: 'int' = 0, limit: 'int' = 20)`

`GET /bbs/app/topic/feeds/news`

社区头条（资讯）列表。

### `website_background(self, appid: 'int')`

`GET /heyboxpc/v2/client/website_background/v1`

PC 网页端背景图（按游戏定制）。

---

## 搜索

### `search_welcome(self)`

`GET /bbs/app/api/search/welcome_page/v2`

搜索页默认内容：``default_q``（热搜词）、``Lists``、``ads_banner``。

### `search_found(self, force_refresh: 'bool' = False)`

`GET /bbs/app/api/search/found`

搜索发现（推荐搜索词卡片）。

### `search_suggestion(self, q: 'str')`

`GET /bbs/app/api/search/suggestion/v2`

输入框联想词。

### `search(self, q: 'str', search_type: 'str' = 'general', offset: 'int' = 0, limit: 'int' = 30, game_type: 'str' = '', time_range: 'str' = '', filter_tag: 'str' = '', sort_filter: 'str' = '', dw: 'int' = 628, is_pull_down: 'int' = 0)`

`GET /bbs/app/api/general/search/v1`

综合搜索。

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

### `search_web(self, q: 'str', search_type: 'str' = 'general', offset: 'int' = 0, limit: 'int' = 30, **kw)`

`GET /bbs/app/api/general/search/v1/web`

Web 版搜索（``/v1/web``）。

与 :meth:`search` 同参同结构，但结果集更偏向网页端可展示的内容
（同样的 ``q`` 下 ``items`` 更少、不含客户端专属卡片）。

### `search_filter_tags(self, q: 'str')`

`GET （组合调用，见实现）`

取搜索结果顶部的筛选词条（"全部 / 地图 / 豪华版 …"）。

返回 ``[{name, tag, report_id}]``，把 ``tag`` 透传回 :meth:`search` 的
``filter_tag`` 即可切换。

### `search_links(self, q: 'str', **kw)`

`GET （组合调用，见实现）`

只搜帖子（``search_type=link`` 的快捷方式）。

### `search_games(self, q: 'str', **kw)`

`GET （组合调用，见实现）`

只搜游戏。

### `wiki_search(self, q: 'str', offset: 'int' = 0, limit: 'int' = 20)`

`GET /wiki/search`

Wiki（攻略站）搜索，返回 ``wiki_infos``。

### `wiki_search_wiki(self, query: 'str')`

`GET /wiki/search_wiki/`

Wiki 联想（编辑器里插入 wiki 卡片用）。

参数名是 ``query``（不是 ``q``），返回 ``{wikis, search_result}``，
``search_result`` 30 条。

### `mod_search(self, q: 'str', offset: 'int' = 0, limit: 'int' = 20)`

`GET /workshop/open/mod_search`

工坊（MOD）搜索。

### `mod_detail(self, mod_id: 'int | str')`

`POST /workshop/app/mod_detail`

工坊 MOD 详情。

注意是 **POST**，且 ``mod_id`` 走 query 而不是 body，body 里要带 ``_temp=3``。

### `mall_search(self, q: 'str', offset: 'int' = 0, limit: 'int' = 10)`

`GET /mall/search/`

商城搜索。

---

## 帖子与评论

### `link_tree(self, link_id: 'int', page: 'int' = 1, index: 'int' = 1, limit: 'int' = 20, is_first: 'int' = 1, sort_filter: 'str' = '', **kw)`

`GET /bbs/app/link/tree`

帖子详情 + 楼层评论（主页面的唯一接口）。

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

### `link_tree_v2(self, link_id: 'int', page: 'int' = 1, index: 'int' = 1, limit: 'int' = 20)`

`GET /bbs/app/link/tree/v2`

帖子接口 v2：只返回 ``{link, comment}``，比 v1 更轻。

### `link_tree_backend(self, link_id: 'int', page: 'int' = 1, index: 'int' = 1, limit: 'int' = 20)`

`GET /bbs/app/link/tree/backend`

帖子接口 backend 版本（字段与 v1 相同，供 SSR/后台渲染用）。

### `link_by_url(self, share_url: 'str', page: 'int' = 1, limit: 'int' = 20)`

`GET /bbs/app/link/tree`

用分享链接里的短 ID 打开帖子（``?link_id=`` 参数是 hex 串时走这个）。

### `sub_comments(self, link_id: 'int', root_comment_id: 'int', offset: 'int' = 0, limit: 'int' = 10)`

`GET /bbs/app/comment/sub/comments`

楼中楼子评论。

:param root_comment_id: 顶层评论 ID（**不是** ``comment_id``/``root_id``）。

### `link_related(self, link_id: 'int')`

`GET /bbs/app/link/related/recommend_web`

帖子底部相关推荐：``{related_links, related_topics}``。

### `link_author(self, link_id: 'int')`

`GET /bbs/app/link/author_info`

帖子作者的简要资料。

### `forbid_reason(self, link_id: 'int' = 0)`

`GET /bbs/app/api/get/forbid_reason`

举报原因枚举（37 条）。

### `comment_create(self, link_id: 'int', text: 'str', reply_id: 'int | str' = '-1', root_id: 'int | str' = '-1', is_cy: 'int' = 0, imgs: 'list[str] | None' = None)`

`POST /bbs/app/comment/create`

发表评论 / 回复。

:param reply_id: 被回复的评论 ID，顶层评论传 ``"-1"``。
:param root_id:  楼中楼里的根评论 ID，非楼中楼传 ``"-1"``。
:param imgs:     图片 URL 列表（服务端要求用 ``;`` 连接）。

### `link_favour(self, link_id: 'int', favour: 'bool' = True, favour_type: 'int' = 1, userid: 'int | str' = '', folder_id: 'str' = '')`

`POST /bbs/app/link/favour`

点赞 / 收藏。

:param favour_type: 1 = 点赞，2 = 收藏。
:param folder_id:   收藏夹 ID（收藏时可指定）。

### `link_vote(self, link_id: 'int', opt_ids)`

`POST /bbs/app/link/vote`

在帖子的投票里投票。

:param opt_ids: 选项 ID 或 ID 列表（``vote_options[].id``）。
                多选投票用逗号连接，单选也走同一个字段。

### `link_award(self, link_id: 'int', award_type: 'int' = 1)`

`POST /bbs/app/profile/award/link`

给帖子投币（打赏）。

:param award_type: 1 = 投币，0 = 取消投币（前端就是按
                   ``is_award_link`` 取反传这个值）。

### `comment_support(self, comment_id: 'int', link_id: 'int' = 0)`

`POST /bbs/app/comment/support`

点赞某条评论。

### `link_report(self, link_id: 'int', reason_id: 'int', text: 'str' = '')`

`POST /bbs/app/link/report`

举报帖子。``reason_id`` 取自 :meth:`forbid_reason`。

### `comment_report(self, comment_id: 'int', reason_id: 'int', text: 'str' = '')`

`POST /bbs/app/comment/report`

举报评论。

### `link_delete(self, link_id: 'int')`

`POST /bbs/app/link/delete`

删除自己的帖子。

### `build_relation(self, userid: 'int', relation: 'str' = 'blacklist')`

`POST /bbs/app/profile/build/relation`

拉黑 / 移除拉黑（``relation`` 由服务端枚举，默认黑名单）。

---

## 用户 / 关注 / 收藏 / 登录

### `user_profile(self, userid: 'int | str')`

`GET /bbs/app/profile/user/profile`

用户主页资料（``account_detail``）。

### `user_links(self, userid: 'int | str', offset: 'int' = 0, limit: 'int' = 20)`

`GET /bbs/app/profile/user/link/list_v2`

用户发布的帖子列表（``link/list_v2``，注意下划线写法）。

### `user_events(self, userid: 'int | str', list_type: 'str' = 'moment', lastval: 'str' = '', dw: 'int' = 636)`

`GET /bbs/app/profile/events`

用户动态（``moments``）。

:param list_type: ``moment``（动态）或 ``dynamic``。

### `follower_list(self, userid: 'int | str', offset: 'int' = 0, limit: 'int' = 20)`

`GET /bbs/app/profile/follower/list`

粉丝列表。

### `following_list(self, userid: 'int | str', offset: 'int' = 0, limit: 'int' = 20)`

`GET /bbs/app/profile/following/list`

关注列表。

### `follow_user(self, userid: 'int | str', follow: 'bool' = True, follower_id: 'int | str | None' = None)`

`POST /bbs/app/profile/follow/user` / `/bbs/app/profile/follow/user/cancel`

关注 / 取关用户。

:param userid: 被关注者（服务端字段名 ``following_id``）。
:param follow: True 关注，False 取关。
:param follower_id: 自己的 uid；不传则用客户端上的 ``heybox_id``。

### `fav_folders(self)`

`GET /bbs/app/profile/fav/folders`

收藏夹列表与统计：``{folders, cy_fav_num, game_list_fav_num,
wiki_fav_num, user}``。

### `fav_links(self, offset: 'int' = 0, limit: 'int' = 30, dw: 'int' = 1072)`

`GET /bbs/app/profile/fav/folder/v2/links`

收藏的帖子列表。

注意：这个接口**不需要** ``folder_id``，靠 ``enable_new_style_collect=1``
走新版收藏；返回 ``{links[{link:{...}}], has_next}``。

### `fav_folder_add(self, name: 'str', folder_id: 'int' = 0)`

`POST /bbs/app/profile/fav/folder/add`

新建收藏夹（``folder_id=0``）或重命名。

### `history_visit(self, offset: 'int' = 0, limit: 'int' = 30, type: 'str' = 'all', dw: 'int' = 636)`

`GET /bbs/app/profile/history/visit`

浏览历史（``history_visit``）。

### `post_limits(self)`

`GET /bbs/app/profile/post/limits`

当前账号的发帖/评论限制（字数、图片数、每日条数等）。

### `user_permission(self)`

`GET /bbs/app/api/user/permission`

账号权限位（是否可发视频、是否开发者等）。

这个接口没有 ``status``/``result`` 外壳，直接返回权限对象。

### `restore_login(self)`

`GET /account/restore_login`

用 cookie 恢复登录态，返回当前账号信息（10 个字段）。

### `logout(self)`

`GET /account/logout`

退出登录。

### `qrcode_url(self)`

`GET /account/get_qrcode_url/`

获取登录二维码。

返回 ``qr_url``（二维码图片地址）与其指向的 ``qr_login`` 长链接；
客户端拿 ``qr_url`` 生成二维码，然后轮询 :meth:`qr_state`。

### `qr_state(self, qr: 'str')`

`GET /account/qr_state/`

轮询扫码状态（``qr`` 取自 :meth:`qrcode_url` 返回链接里的 ``qr`` 参数）。

### `wechat_state(self)`

`GET /account/wechat/state/`

微信登录态检查（返回 wiki 权限位与 account_detail）。

### `login_code(self, payload: 'dict')`

`POST /account/login_code/`

短信验证码登录。

### `login(self, payload: 'dict')`

`POST /account/login/`

账号密码登录（``payload`` 含 ``username``/``password``/``captcha`` 等）。

### `get_login_code(self, phone: 'str', **kw)`

`POST /account/get_login_code/`

发送登录短信验证码。

### `google_2fa_verify(self, code: 'str', **kw)`

`GET /account/google_2fa_verify/`

Google 两步验证。

---

## 消息中心

### `message(self, list_type: 'int' = 2, offset: 'int' = 0, limit: 'int' = 20)`

`GET /bbs/app/user/message`

消息列表。

:param list_type: 0 回复 / 1 赞与收藏 / 2 聚合中心。
                  传字符串会报 ``错误的消息列表``，必须用整数。

### `official_messages(self, offset: 'int' = 0, limit: 'int' = 20)`

`GET /bbs/notify/official_msg_v2/list`

官方消息列表。

### `discount_messages(self)`

`GET /bbs/app/user/discount_message_v2`

优惠 / 活动推送消息。

---

## 游戏 / 赛事

### `game_detail(self, appid: 'int', **kw)`

`GET /game/get_game_detail/`

游戏详情（PC）。

返回 59 个字段，重点：``menu_v2``（发布时间/开发商/DLC/媒体评分等条目，
带 ``heybox://`` 深链）、``comment_stats``（五星分布）、
``morelike``、``follow_state``、``button_style_list_v2``。

### `game_detail_mobile(self, appid: 'int')`

`GET /game/mobile/get_game_detail/`

手游详情（部分 appid 会报 ``非法游戏id``）。

### `game_detail_console(self, appid: 'int')`

`GET /game/console/get_game_detail/`

主机游戏详情。

### `game_introduction(self, steam_appid: 'int')`

`GET /game/game_introduction/`

游戏简介正文（HTML）。

参数名是 ``steam_appid`` + ``return_json=1``，传 ``appid`` 不行。

### `game_infos(self, appids)`

`GET /game/get_game_infos/`

批量取游戏基础信息。

### `owned_games(self, offset: 'int' = 0, limit: 'int' = 20, game_type: 'str' = 'steam')`

`GET /game/owned_game/game_list`

我的游戏库。``game_type`` 只接受 ``steam``（pc/mobile/console 均失败）。

### `hot_games(self, offset: 'int' = 0, limit: 'int' = 20)`

`GET /game/owned_game/hot_list`

热门游戏榜。

### `game_comments(self, appid: 'int', offset: 'int' = 0, limit: 'int' = 20, **kw)`

`GET /bbs/app/link/game/comments`

游戏的盒友评价（打分 + 短评）。

### `game_comment_up(self, comment_id: 'int')`

`POST /bbs/app/link/game/comment/up`

给游戏评价点赞。

### `follow_game(self, steam_appid: 'int', follow: 'bool' = True)`

`POST /account/follow_game/` / `/account/unfollow_game/`

关注 / 取关游戏（参数名是 ``steam_appid``）。

### `game_wx_share(self, appid: 'int')`

`GET /game/wx_share/info/v2`

游戏分享卡片信息。

### `steam_screenshots(self, appid: 'int', offset: 'int' = 0, limit: 'int' = 20)`

`GET /game/steam/screenshot/list`

Steam 截图墙。

### `self_made_games(self, offset: 'int' = 0, limit: 'int' = 20)`

`GET /game/self_made_game_list/data/infos`

个人自制 / 独立游戏列表。

### `self_made_game_favour(self, game_id: 'int', favour: 'bool' = True)`

`GET /game/self_made_game_list/favour`

收藏 / 取消收藏自制游戏。

### `wiki_infos(self, appid: 'int')`

`GET /wiki/get_wiki_infos`

游戏的 Wiki 入口信息。

### `match_games(self)`

`GET /oa/match/game/list/data`

赛事中心：游戏列表。

### `match_leagues(self, appid: 'int')`

`GET /oa/match/league/list/data`

赛事中心：某游戏的联赛列表（必须传 ``appid``）。

### `match_list(self, appid: 'int', offset: 'int' = 0, limit: 'int' = 20)`

`GET /oa/match/match/list/data`

赛事中心：赛程列表（必须传 ``appid``）。

### `watch_match(self, match_id: 'int | str')`

`POST /game/match/watch_match`

订阅 / 观看某场比赛。

### `unwatch_match(self, match_id: 'int | str')`

`POST /game/match/unwatch_match`

取消订阅比赛。

### `match_leagues_batch(self)`

`GET /game/match/leagues`

赛事模块的批量联赛数据。

### `batch_match_data(self, **kw)`

`GET /game/match/batch_match_data`

赛事模块的批量比赛数据。

---

## 发帖编辑器 / 上传 / 发布

### `emojis(self)`

`GET /bbs/app/api/emojis/list`

可用表情包列表（小黑盒表情 ``[cube_xxx]``）。

### `at_search(self, q: 'str', limit: 'int' = 10)`

`GET /bbs/app/api/at/search`

@ 提及用户搜索。

### `topic_index(self, is_post: 'int' = 1, post_tab: 'int' = 1, is_new_style: 'int' = 1, type: 'str' = 'list', link_id: 'int' = 0, **kw)`

`GET /bbs/app/api/topic/index`

发帖编辑器初始化：可选社区、置顶公告、声明选项。

没有 ``status``/``result`` 外壳，直接返回
``{topics_list_v2, notify, post_article_alert, extra_declaration_choice,
enable_post_declaration_v2, post_article_plan, post_pic_link_plan,
title_notify}``。

### `topic_selection(self, is_post: 'int' = 1, post_tab: 'int' = 1, is_new_style: 'int' = 1, type: 'str' = 'list', link_id: 'int' = 0)`

`GET /bbs/app/api/post_editor/topic_selection/index`

"选择社区"弹窗的数据源。

### `topic_selection_search(self, q: 'str', limit: 'int' = 20)`

`GET /bbs/app/api/post_editor/topic_selection/search`

"选择社区"弹窗里的搜索。

### `owned_game_list(self, offset: 'int' = 0, limit: 'int' = 20, game_type: 'str' = 'steam')`

`GET /game/owned_game/game_list`

发帖时可关联的"我的游戏"（``game_type`` 只能传 ``steam``）。

### `owned_game_hot(self, offset: 'int' = 0, limit: 'int' = 20, game_type: 'str' = 'steam')`

`GET /game/owned_game/hot_list`

发帖时可关联的热门游戏。

### `drafts(self, offset: 'int' = 0, limit: 'int' = 20)`

`GET /bbs/app/link/drafts`

我的草稿箱。

### `link_edit_info(self, link_id: 'int')`

`GET /bbs/app/link/edit/info`

编辑帖子前拉取原文（需要编辑权限）。

### `link_change_status(self, link_id: 'int', status: 'int' = 0)`

`GET /bbs/app/link/change/status`

草稿箱里切换稿件状态。

注意：Web 端调用会返回 ``请前往 app 使用该功能``，只在 App 内可用。

### `upload_info(self, files, scope: 'str' = 'bbs', need_cache: 'int' = 0)`

`POST /web/bbs/2026/10/28/xxx.png`

第一步：登记要上传的文件，拿到对象名与存储桶。

:param files: 单个文件描述 dict 或它们的列表。每个描述形如
              ``{"name": "a.png", "mimetype": "image/png",
                 "fsize": 18234, "width": 100, "height": 100,
                 "duration": 0}``。
:param scope: web 端固定用 ``"bbs"``（业务后台另有 ``business``）。
:return: ``{"keys": ["/web/bbs/2026/10/28/xxx.png"], "region":
          "ap-shanghai", "bucket": "imgheybox-1251007209",
          "host": "imgheybox.max-c.com"}``

### `upload_token(self, bucket: 'str', keys, mimetypes)`

`POST /bbs/app/api/qcloud/cos/upload/token/v2`

第二步：用桶名 + 对象名换 COS 临时凭证，直接 PUT 上去。

:param keys: :meth:`upload_info` 返回的 ``keys``。
:param mimetypes: 与 ``keys`` 一一对应的 MIME 列表。

拿到 ``credentials.tmpSecretId/tmpSecretKey/sessionToken`` 后，用
COS SDK 或任意 S3/COS 兼容客户端 PUT 到 ``bucket`` + ``key``。

### `upload_callback(self, keys)`

`POST /bbs/app/api/qcloud/cos/upload/callback/v2`

第三步：告诉服务端上传完成，换回最终可访问 URL。

:return: ``{"preview_urls": [...], "thumbs": [...], ...}``
         ``preview_urls[0]`` 就是可以直接塞进帖子/评论里的图片地址。

### `upload_heartbeat(self, keys)`

`POST /bbs/app/api/qcloud/cos/upload/heartbeat`

大文件分片上传时的心跳（每 3 分钟一次），小文件可跳过。

### `upload_image(self, data_or_path, filename: 'str' = 'image.png', mimetype: 'str' = 'image/png', timeout: 'float' = 120)`

`GET （组合调用，见实现）`

一步到位上传一张图片/一段视频，返回最终 URL。

完整走完 info → token → COS PUT → callback，纯 ``urllib`` 实现，
不依赖腾讯云 SDK。

:param data_or_path: ``bytes`` 或本地文件路径。
:return: ``{"url":..., "thumb":..., "key":..., "bucket":...}``

### `copy_image_by_url(self, url: 'str', **kw)`

`GET /bbs/app/api/qcloud/cos/copy/image/by/url`

把外链图片转存到小黑盒图床。

### `original_image(self, url: 'str', **kw)`

`GET /bbs/app/api/original/image`

取图片原图地址（去掉缩略参数后的版本）。

### `post_link(self, payload: 'dict')`

`POST /bbs/app/api/link/post`

发布图文帖。payload 结构见文档「发帖」一节。

### `post_video_link(self, payload: 'dict')`

`POST /bbs/app/api/video-link/post`

发布视频帖。

### `post_marketing_link(self, payload: 'dict')`

`POST /bbs/content_marketing/author/link/post`

带任务/激励的投稿（创作激励计划）。

### `marketing_tasks(self, offset: 'int' = 0, limit: 'int' = 20)`

`GET /bbs/content_marketing/post/task_list`

创作激励任务列表。

---

## 创作者中心 / 反馈 / 客户端 / 聊天室

### `creator_articles(self, article_type: 'str' = 'all', state: 'str' = 'all', sort: 'str' = 'create_at', offset: 'int' = 0, limit: 'int' = 20, timeout: 'float' = 60)`

`GET /bbs/app/author/concept/article/list`

创作者中心 - 我的稿件列表。

注意：官方把 ``state`` 拼成了 ``artilce_state``（不是 article），
必须照抄才能命中。该接口响应很慢，默认给 60s 超时。

### `creator_article_data(self, **kw)`

`GET /bbs/app/author/concept/article/data`

创作者中心 - 稿件数据（阅读/互动曲线）。

### `award_users(self, award_ids)`

`GET /bbs/app/api/article/get_award_users`

打赏/投币用户列表。

:param award_ids: 打赏 ID 或 ID 列表（服务端接收 ``award_ids=1,2,3``）。
                  打赏 ID 来自帖子的 ``awards[].award_id``。

### `feedback_mylist(self, offset: 'int' = 0, limit: 'int' = 20)`

`GET /bbs/web/feedback/mylist`

我的反馈工单。

### `feedback_edit_info(self, feedback_id: 'int')`

`GET /bbs/web/feedback/edit/info`

单条反馈详情。

### `feedback_close(self, feedback_id: 'int')`

`GET /bbs/app/feedback/close`

撤销 / 关闭反馈工单。

### `feedback_report_options(self, appid: 'int' = 0)`

`GET /bbs/web/feedback/pubg/report_options`

举报/反馈的选项树。

### `feedback_post(self, payload: 'dict')`

`POST /bbs/web/feedback/user/post`

提交反馈。

### `download_url(self)`

`GET /heyboxpc/client/get_download_url`

PC 客户端通用下载地址。

### `release_download(self, platform: 'str' = 'win')`

`GET /heyboxpc/v2/client/release/download/v1`

分平台/分渠道的客户端发布包信息。

:param platform: ``win`` 或 ``mac``（小写，服务端只认这两个）。

### `channel_download_page(self, **kw)`

`GET /heyboxpc/v2/client/channel_download_page/v1`

渠道下载引导页。

### `acquisition_issue(self, payload: 'dict')`

`POST /heyboxpc/v2/client/acquisition/issue/v1`

渠道拉新上报。

### `pc_download_click(self, payload: 'dict')`

`POST /web/website/home/pc_download/click`

"下载 PC 版"点击埋点。

### `chatroom_tab(self)`

`GET /chatroom/v2/common/tab`

语音房入口（返回独立域名 ``url`` 与邀请/下载链接）。

### `chatroom_card(self, **params)`

`GET /chatroom/v2/room/card_info`

语音房卡片信息（参数由客户端透传，web 端未暴露明文参数名）。

### `joined_rooms(self, **kw)`

`GET /chatroom/mobile/search/joined_rooms`

我加入的语音房。

### `chatroom_report(self, payload: 'dict')`

`POST /chatroom/mobile/report`

举报语音房 / 语音房用户。

### `chatroom_msg_user(self, userid: 'int | str', **kw)`

`GET /chatroom/v2/msg/user`

语音房会话里拉某用户的消息。

### `web_report(self, payload: 'dict')`

`POST /heyboxpc/v2/report/web`

网页端举报上报（下载页等）。

### `box_data_callback(self, payload: 'dict | None' = None)`

`POST /rc/box_data/callback`

风控 SDK（数美）数据回传，前端自动调用，一般无需手动触发。

### `stranger_messages(self, offset: 'int' = 0, limit: 'int' = 20)`

`GET /chat/stranger_messages/`

陌生人私信列表。

路径末尾带斜杠且**不带** userid —— 拼成 ``/chat/stranger_messages/123``
会被服务端当静态资源返回 404。返回 ``{list: [{count, user_a, user_b, …}]}``。

---
