# 小黑盒 Web API 逆向 + Python SDK

对 [小黑盒](https://www.xiaoheihe.cn) 网页端（`/app/bbs/home`）的接口逆向结果，附带一个零依赖的
Python 客户端。纯 HTTP 实现：签名在本地算，不需要浏览器、不需要抓包代理、不需要常驻进程。

```python
import xhh

c = xhh.Client.from_file("cookie.json")      # 带风控 cookie
for link in c.feeds()["links"]:
    print(link["linkid"], link["title"])
```

---

## 目录

* [为什么能纯 HTTP 复现](#为什么能纯-http-复现)
* [签名算法](#签名算法)
* [风控与登录态](#风控与登录态)
* [快速开始](#快速开始)
* [四项主要功能](#四项主要功能)
* [界面 → 接口对照表](#界面--接口对照表)
* [SDK 结构](#sdk-结构)
* [接口清单](#接口清单)
* [验证](#验证)
* [踩过的坑](#踩过的坑)

---

## 为什么能纯 HTTP 复现

网页端是个 SPA（`@heybox-spa/website`），所有数据都来自 `https://api.xiaoheihe.cn`。它没有
mTLS、没有请求体加密、没有 JS 挑战，唯一的门禁是 query 里的三件套：

```
hkey=<7 字符签名> & _time=<秒级时间戳> & nonce=<32 位大写 hex>
```

`hkey` 是由路径 + 时间戳 + nonce 算出来的，算法全部在前端 bundle 里，因此可以逐字翻译成
Python。另外有两个 cookie 分别在管两件事：`x_xhh_tokenid` 管风控，`user_pkey` 管登录态。

---

## 签名算法

原始代码在 `index-*.js` 里，调用链 `Tr() -> qM()/WM()/Wwe()/Uwe()/qwe()`，短得可以直接读完：

```
hkey = [5 字符主干] + [2 位十进制校验]
```

1. **路径规范化**：剥掉 query，去掉空段，首尾补 `/`。`/bbs/app/feeds` → `/bbs/app/feeds/`，
   `/game/get_game_detail/` 也还是 `/game/get_game_detail/`。
2. **三段素材**：
   * `o = qm(str(_time), KEY, -2)` — 时间戳过 KEY 的前 30 位；
   * `a = wm(path)` — 路径过 KEY 全表；
   * `s = wm(nonce)` — nonce 过 KEY 全表。

   其中 `qm/wm` 就是「用字符的码点对表长取模当下标」：
   `"".join(table[ord(ch) % len(table)] for ch in s)`。
3. `seed = wwe([o, a, s])[:20]` — 按列交织（`o[0] a[0] s[0] o[1] a[1] s[1] ...`）后取前 20 字符。
4. `digest = md5(seed)`。
5. **校验位**：取 `digest[-6:]` 的 6 个字符码，做一次 4×4 MDS 矩阵混合
   （`GF(2^8)`，本原多项式 `x^8+x^4+x^3+x+1`），求和后 `% 100`，补零到 2 位。
6. **主干**：`qm(digest[:5], KEY, -4)` — md5 前 5 字符过 KEY 的前 28 位，得 5 字符。

`KEY` 是硬编码的 32 字符表：

```
AB45STUVWZEFGJ6CH01D237IXYPQRKLMN89
```

`xhh/sign.py` 里附了 6 组真实抓包样本做自检，`python -m xhh.sign` 全过才算对：

```
OK   /bbs/app/feeds                             got=VS2S006 expect=VS2S006
OK   /bbs/app/feeds/banner                      got=D7PV763 expect=D7PV763
...
6/6 passed
```

> 校验位那步有个陷阱：`qwe()` 会**原地**把数组前 4 个元素换成混合结果，而调用方对**整个**
> 数组求和。把它写成纯函数、只返回 4 个值，校验位就会全错 —— 而错的位置看起来像是
> 「主干对、末两位不对」，很容易被误判成时间戳策略问题。

---

## 风控与登录态

### `x_xhh_tokenid`：风控

不带这个 cookie 时，一部分接口返回

```json
{"msg": "", "result": {}, "status": "show_captcha"}
```

只有 51 字节，但没有任何提示。命中的接口包括：

* `/bbs/app/link/tree` 全系列（**帖子详情，也就是最核心的那个**）
* `/bbs/app/profile/user/link/list/v2`、`/bbs/app/profile/events`

带上 `x_xhh_tokenid` 之后全部 200。这个值由腾讯验证码（`fp-it.portal101.cn/deviceprofile/v4`）
在上游下发，时效性宽松，取一次能用很久。`get_token.js` 用 CDP 驱动本机 Chrome 把它和
`user_pkey` 一起抓下来，写成 `cookie.json`。

### `user_pkey`：登录态

`/account/restore_login` 是判断「当前是否已登录」的探针。带上 `user_pkey` 它返回 10 个字段
（含 `profile` / `pkey` / `invite_info`），不带就返回 `status: relogin`。

```python
c = xhh.Client.from_file("cookie.json")       # 文件里有 pkey 就是登录态
c.logged_in        # True
c.restore_login()["profile"]["nickname"]      # '<你的昵称>'
```

`with_pkey()` 返回的是 `type(self)(...)` 而不是 `Client(...)`，这样 `FeedsAPI` 等方法
不会因为绕过子类而丢失 —— 这个细节在扩展时容易踩。

---

## 快速开始

```bash
node get_token.js --attach 9333     # 附着你已登录的 Chrome，产出 cookie.json
python examples/01_home_feed.py
```

`get_token.js` 默认自己拉一个全新的 headless Chrome，那种情况下只能拿到匿名
cookie 与 `x_xhh_tokenid`，`user_pkey` 是空的（新 profile 没登录）。要拿登录态，先带调试端口
启动你自己的 Chrome：

```bash
chrome.exe --remote-debugging-port=9333 --user-data-dir="C:\tmp\chrome-xhh"
# 在这个窗口里登录小黑盒，然后
node get_token.js --attach 9333
```

产物长这样，`pkey` 有值就说明登录态拿到了：

```json
{ "cookie": "…; x_xhh_tokenid=…; user_pkey=…", "token": "…",
  "pkey": "…", "heybox_id": "<你的 heybox_id>", "ua": "Mozilla/5.0 …" }
```

`cookie.json` 已在 `.gitignore` 里，不会入库。

最小用法：

```python
import xhh

c = xhh.Client.from_file("cookie.json")            # 风控 cookie +（可选）登录态
c.feeds(offset=0)                                  # 首页推荐
c.search("黑神话")                                  # 搜索
c.link_tree(195173343)                             # 帖子详情 + 评论
c.comment_create(195173343, "test")                # 发评论
```

---

## 四项主要功能

### 1. 首页推荐流

`GET /bbs/app/feeds`，参数 `offset` / `pull` / `dw`。

`result` 里有 5 个键：`links`（帖子数组）、`keep_previous`、`notify_msg`、
`show_view_point`、`use_history`。分页实测 `offset=0/10/20` 各 10 条且无重叠 —— 步长就是
返回条数，`pull=1` 是下拉刷新（会换一批全新内容），`dw` 是设备宽度（影响图片尺寸档位）。

帖子对象 39 个字段，常用的：

| 字段 | 说明 |
| --- | --- |
| `linkid` | 帖子 ID |
| `title` / `description` | 标题 / 摘要 |
| `has_video` | 1 表示视频帖 |
| `link_tag` | `26/27/28` 是图文，其余多为普通帖 |
| `comment_num` / `link_award_num` / `up` | 评论数 / 投币数 / 点赞数 |
| `topics` | 所属社区（`topic_id` / `name` / `hot_value_v2`） |
| `hashtags` / `act_hashtags` | 话题标签 |
| `user` | 作者信息 |

### 2. 搜索

`GET /bbs/app/api/general/search/v1`，参数：

| 参数 | 取值 |
| --- | --- |
| `q` | 关键词 |
| `search_type` | `general` / `link` / `game` / `hashtag` / `user` / `mall` / `topic` / `article` |
| `sort_filter` | `default` / `create_date` / `award_num` / `comment_num` |
| `time_range` | 空 / `7d` / `30d` / `180d` / `360d` |
| `game_type` | 游戏平台过滤 |
| `is_pull_down` | 下拉刷新置 0 |
| `offset` / `limit` | 分页，`limit` 实测可到 30 |

> 排序参数叫 **`sort_filter`**，不是 `sort` —— 传 `sort=` 不会报错，只会静默返回默认顺序，
> 很容易误以为「排序不生效」。

`items[]` 是混排的，`type` 枚举：`link` / `game` / `space` / `filter_tag` / `new_game_list` /
`topic` / `mini_app_v2` / `tool` / `relevant_search` / `hashtag` / `user` / `mall`。
其中 `space` 只是间距占位（`{color, height}`），渲染时过滤掉。帖子标题里的
`<em>` 是命中高亮。

搜索页还有三个配套接口：`search_welcome`（首屏，含热搜词 `default_q`）、`search_found`
（搜索发现）、`search_suggestion`（联想词）。

### 3. 帖子查看与评论

`GET /bbs/app/link/tree`，参数 `link_id` / `is_first` / `page` / `index` / `limit` / `sort_filter`
（`hot` / `time_aes` / `time_desc`）。

`result` 结构：

```
comments              顶层楼层，形如 [{comment: [ ... ]}]
link                  帖子本体
total_floor_num       总楼层
total_page            总页数
has_more_floors       是否还有下一页
sort_filter           当前排序
cy_control / folded_comment_tips / show_interact_list
```

正文有三种形态，全在 `link` 的同一批字段里，前端靠自己判断 —— `xhh.parse_link()` 把它们
归一成 `{kind, html, text, images, video}`：

* **纯文字帖**：`link.text` 就是 HTML 字符串。
* **图文帖**：`link.text` 是**一个 JSON 字符串**，`json.loads` 之后是元素列表 —— 首个
  `type=text` 元素是正文 HTML（里面还内嵌着 `<img data-original=...>`），其余
  `type=img` 元素是配图 `{url, width, height}`。
* **视频帖**：`has_video=1`，地址在 `link.video_url`，附 `video_thumb` / `video_duration` /
  `video_width` / `video_height`。**这个 URL 带时效签名**（`?auth=...&sign=...`），
  过期要重新拉一次详情。

评论对象：`commentid` / `userid` / `text` / `floor_num` / `child_num` / `up` /
`ip_location` / `is_link_owner` / `is_cy` / `user{username, avatar, level_info, medals}`。

楼中楼走 `GET /bbs/app/comment/sub/comments`，参数是 **`root_comment_id`**（不是
`comment_id` / `root_id`）：

```python
subs = c.sub_comments(link_id=195173343, root_comment_id=..., offset=0, limit=10)
```

### 4. 发评论 / 点赞 / 收藏

```python
c.comment_create(link_id, "文本", images=["https://...png"])   # 多图用 ; 连接
c.link_favour(link_id, favour=True, favour_type=1)             # 1 点赞，2 收藏
c.comment_support(comment_id)                                  # 评论点赞
```

`comment_create` 的完整体：`{is_cy, link_id, reply_id, root_id, text, imgs}`，
`reply_id` / `root_id` 无目标时传字符串 `"-1"`。

---

## 界面 → 接口对照表

逆向覆盖面按「页面上能点的地方」逐个数了一遍，路由取自前端 router，接口取自抓包。

| 界面 / 动作 | 接口 |
| --- | --- |
| 首页推荐流 | `GET /bbs/app/feeds` |
| 首页轮播 | `GET /bbs/app/feeds/banner` |
| 首页背景 | `GET /heyboxpc/v2/client/website_background/v1` |
| 社区总览（左侧栏） | `GET /bbs/app/topic/categories` |
| 进入某个社区 | `GET /bbs/app/topic/menu` |
| 社区帖子列表 | `GET /bbs/app/topic/feeds` |
| 社区资讯 tab | `GET /bbs/app/topic/feeds/news` |
| 搜索首屏 / 热搜 | `GET /bbs/app/api/search/welcome_page/v2` |
| 搜索发现 | `GET /bbs/app/api/search/found` |
| 搜索联想 | `GET /bbs/app/api/search/suggestion/v2` |
| 搜索结果 | `GET /bbs/app/api/general/search/v1` |
| 搜索结果（web 排序） | `GET /bbs/app/api/general/search/v1/web` |
| Wiki 搜索 | `GET /wiki/search` |
| 工坊 MOD 搜索 | `GET /workshop/open/mod_search` |
| 商城搜索 | `GET /mall/search/` |
| 帖子详情 | `GET /bbs/app/link/tree` |
| 帖子详情（v2） | `GET /bbs/app/link/tree/v2` |
| 楼中楼 | `GET /bbs/app/comment/sub/comments` |
| 相关推荐 | `GET /bbs/app/link/related/recommend_web` |
| 帖子作者卡片 | `GET /bbs/app/link/author_info` |
| 举报原因列表 | `GET /bbs/app/api/get/forbid_reason` |
| 发评论 | `POST /bbs/app/comment/create` |
| 点赞 / 收藏 | `POST /bbs/app/link/favour` |
| 投票 | `POST /bbs/app/link/vote` |
| 打赏 / 投币 | `POST /bbs/app/profile/award/link` |
| 评论点赞 | `POST /bbs/app/comment/support` |
| 举报帖子 / 评论 | `POST /bbs/app/link/report`、`/bbs/app/comment/report` |
| 用户主页 | `GET /bbs/app/profile/user/profile` |
| 用户的帖子 | `GET /bbs/app/profile/user/link/list_v2` |
| 用户的动态 | `GET /bbs/app/profile/events` |
| 粉丝 / 关注列表 | `GET /bbs/app/profile/follower/list`、`/following/list` |
| 关注 / 取关 | `POST /bbs/app/profile/follow/user`、`.../cancel` |
| 收藏夹 | `GET /bbs/app/profile/fav/folders` |
| 收藏夹内容 | `GET /bbs/app/profile/fav/folder/v2/links` |
| 浏览历史 | `GET /bbs/app/profile/history/visit` |
| 发帖权限 / 上限 | `GET /bbs/app/profile/post/limits` |
| 当前用户权限 | `GET /bbs/app/api/user/permission` |
| 消息中心（聚合） | `GET /bbs/app/user/message?list_type=2` |
| 回复我的 | `...?list_type=0` |
| 赞与收藏 | `...?list_type=1` |
| 官方消息 | `GET /bbs/notify/official_msg_v2/list` |
| 优惠消息 | `GET /bbs/app/user/discount_message_v2` |
| 游戏详情 | `GET /game/get_game_detail/` |
| 游戏详情（移动 / 主机） | `GET /game/mobile/...`、`/game/console/...` |
| 游戏简介 | `GET /game/game_introduction/` |
| 批量游戏信息 | `GET /game/get_game_infos/` |
| 我的游戏库 | `GET /game/owned_game/game_list?game_type=steam` |
| 游戏评价 | `GET /bbs/app/link/game/comments` |
| 关注游戏 | `POST /account/follow_game/` |
| 游戏分享签名 | `GET /game/wx_share/info/v2` |
| 赛事 / 联赛 / 比赛 | `GET /oa/match/game/list/data`、`/league/list/data`、`/match/list/data` |
| 表情包 | `GET /bbs/app/api/emojis/list` |
| @ 用户联想 | `GET /bbs/app/api/at/search` |
| 发帖编辑器首页 | `GET /bbs/app/api/topic/index` |
| 选择社区 / 话题 | `GET /bbs/app/api/post_editor/topic_selection/index`、`/search` |
| 我的游戏（发帖挂载） | `GET /game/owned_game/game_list`、`/hot_list` |
| 草稿箱 | `GET /bbs/app/link/drafts` |
| 编辑帖子信息 | `GET /bbs/app/link/edit/info` |
| 上传（三步） | `POST /bbs/app/api/qcloud/cos/upload/info/v2` → `/token/v2` → `/callback/v2` |
| 外链图片转存 | `GET /bbs/app/api/qcloud/cos/copy/image/by/url` |
| 取原图 | `GET /bbs/app/api/original/image` |
| 发图文帖 | `POST /bbs/app/api/link/post` |
| 发视频帖 | `POST /bbs/app/api/video-link/post` |
| 创作激励投稿 | `POST /bbs/content_marketing/author/link/post` |
| 创作者中心文章 | `GET /bbs/app/author/concept/article/list` |
| 打赏名单 | `GET /bbs/app/api/article/get_award_users` |
| 反馈列表 / 提交 | `GET /bbs/web/feedback/mylist`、`POST /bbs/web/feedback/user/post` |
| 客户端下载 | `GET /heyboxpc/client/get_download_url` |
| 版本发布信息 | `GET /heyboxpc/v2/client/release/download/v1` |
| 聊天室入口 | `GET /chatroom/v2/common/tab` |
| 二维码登录 | `GET /account/get_qrcode_url/`、`/account/qr_state/` |
| 登录态恢复 | `GET /account/restore_login` |

---

## SDK 结构

```
xhh/
  sign.py       hkey 签名 + 6 组自检样本
  client.py     HTTP、公共参数、cookie、重试、错误；COS 直传签名
  api.py        8 个 mixin，125 个方法
  content.py    帖子正文 / 评论归一化
```

`Client` 由 8 个 mixin 组合而成，每个 mixin 对应页面上一块功能区：

| mixin | 覆盖 |
| --- | --- |
| `FeedsAPI` | 首页、轮播、社区流 |
| `SearchAPI` | 搜索、Wiki、MOD、商城 |
| `LinkAPI` | 帖子详情、评论、点赞、举报 |
| `UserAPI` | 用户主页、关注、收藏、历史、登录 |
| `MessageAPI` | 消息中心三个列表 |
| `GameAPI` | 游戏详情、游戏库、赛事 |
| `EditorAPI` | 发帖编辑器、上传、发布 |
| `MiscAPI` | 创作者中心、反馈、客户端下载、聊天室 |

错误处理：服务端用 HTTP 200 + `status` 字段表达业务失败，`result()` 会把它转成异常。

```python
try:
    tree = c.link_tree(link_id)
except xhh.CaptchaRequired:      # status == "show_captcha"
    ...                          # 换 cookie
except xhh.XhhError as e:        # 其它业务失败
    print(e.status, e.path, e.payload)
```

---

## 接口清单

详见 [`docs/api.md`](docs/api.md)（由 `tools/gen_docs.py` 从 `api.py` 自动生成，
125 个方法，逐个带路径、HTTP 方法、参数说明）。

覆盖面：从打包产物里恢复出 95 个 `(method, path)`，全部落进了 SDK；另有 74 条字符串是前端
路由 / 正则碎片 / 静态资源，逐条发请求确认过不是接口（见「踩过的坑」最后一条）。

---

## 验证

```bash
python -m xhh.sign          # 签名自检 6/6
python tests/smoke_all.py   # 125 个方法逐个真调
```

`tests/smoke_all.py` 的最近一次结果：

```
ok=70  fail=1  skip=0
FAIL creator_articles   XhhError: 请求失败: The read operation timed out
```

唯一失败项是 `/bbs/app/author/concept/article/list` —— 服务端自身慢到 60s 也未必返回，
不是参数问题（前端点开创作者中心同样转圈很久）。其余全部 200 且返回结构符合预期。

`tools/` 下的脚本是得出上面这些结论的过程产物，留着方便复核：

| 脚本 | 作用 |
| --- | --- |
| `tools/extract_endpoints.py` | 从打包 JS 里恢复 `(method, path)` 清单 |
| `tools/probe_full.py` | 对全部端点打一遍，落 `probe_*.json` |
| `tools/collect_shapes.py` | 采集各接口 `result` 的键结构与样本 |
| `tools/gen_docs.py` | 反射 `api.py` 生成 `docs/api.md` |

它们依赖 `js3/`（从 CDN 拉下来的 bundle）和 `probe_*.json`，两者都在 `.gitignore` 里；
想重跑就先按脚本开头注释重新抓取。凭据统一由 `tools/_cred.py` 从环境变量
`XHH_PKEY` 或根目录的 `pkey.txt` / `cookie.json` 读取，源码里没有任何硬编码 token。

---

## 踩过的坑

按遇到顺序记，都是会浪费时间的那些。

**POST 体是表单，不是 JSON。** 前端 axios 的 `transformRequest` 会先把
`Content-Type` 设成 `x-www-form-urlencoded`，再用 `qs.stringify` 序列化。用 JSON 发
`upload/info/v2` 会得到 `参数错误:1000`，发 `comment/create` 会得到
`请求参数 "link_id" 缺失` —— 后者尤其误导，看着像少传参，其实是整个 body 没解析。

**COS 直传的签名是两层 hash。** 腾讯云要 `StringToSign = "sha1\n<sign_time>\n" +
sha1(HttpString) + "\n"`，只算 `HMAC(sign_key, HttpString)` 会稳定拿到
`403 SignatureDoesNotMatch`。HttpString 本身是 `"put\n<uri>\n\nhost=<host>\n"`。
`xhh/client.py:_cos_put()` 是完整实现，纯 `urllib`，不需要装 COS SDK。

**`game_type=steam` 是必需的。** `/game/owned_game/game_list` 不传 `game_type` 报
`错误的游戏类型`；`pc` / `mobile` / `console` / `all` 全部失败，只有 `steam` 通过。

**`artilce_state` 是官方的拼写错误。** 创作者中心的 `/bbs/app/author/concept/article/list`
两个参数叫 `article_type` 和 `artilce_state`，照着正确拼写发会被忽略。顺带一提这个接口
服务端很慢，30s 超时都未必够，本身不是客户端问题。

**`list_type` 是整数。** `/bbs/app/user/message` 传字符串 `"2"` 报
`错误的消息列表`，传 `2` 才行；`list_type >= 3` 全部 failed。

**关注接口要两个 id。** `POST /bbs/app/profile/follow/user` 的字段是
`following_id` + `follower_id`，只传 `userid` 会报
`both following id and follower id is required`。

**`sort` 是不存在的参数。** 搜索排序用 `sort_filter`，`award_users` 用 `award_ids`
（逗号分隔的 `awards[].award_id`，不是 `link_id`），`game_introduction` 用
`steam_appid` + `return_json=1`（传 `appid` 直接返回 HTML）。

**`fav/folder/v2/links` 不需要 folder_id。** 它返回的是「全部收藏」，参数是
`enable_new_style_collect=1` + `dw` + `offset` + `limit`。

**`/bbs/app/profile/user/link/list_v2` 是下划线。** 带斜杠的 `/list/v2` 会命中
风控返回空 `result`。

**`/bbs/app/link/change/status` 在 web 端不可用**，服务端直接回
`请前往 app 使用该功能`。

**有些路径是前端路由，不是接口。** `/game/item/show`、`/mall/sku/show`、
`/app/bbs/home` 这类出现在 bundle 里的字符串是 `heybox://` 深链协议和 router path，
发 HTTP 请求只会拿到 HTML 或 404。

---

## 说明

代码仅用于接口研究与个人学习。使用者需自行承担请求频率、账号状态与内容版权方面的责任；
不要把接口用于批量采集或商业分发。

许可证：[GPL-3.0](LICENSE)。
