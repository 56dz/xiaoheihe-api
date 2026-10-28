"""小黑盒 (xiaoheihe) Web API。

只用 HTTP，不需要浏览器、不需要抓包代理：签名在本地按官方算法实时计算，
风控与登录态各由一个 cookie 承担。

快速开始
--------
>>> import xhh
>>> c = xhh.Client.from_file("cookie.json")          # 只带风控 cookie
>>> data = c.feeds(offset=0, pull=0, dw=604)         # 首页推荐流
>>> len(data["links"])
10

需要登录态时：

>>> c = c.with_pkey("<user_pkey>", heybox_id="<heybox_id>")
>>> c.restore_login()["account_detail"]["username"]
'<你的昵称>'
"""

from .api import (
    EditorAPI,
    FeedsAPI,
    GameAPI,
    LinkAPI,
    MessageAPI,
    MiscAPI,
    SearchAPI,
    UserAPI,
)
from .client import (
    API_BASE,
    BASE_PARAMS,
    UA,
    CaptchaRequired,
    Client as _Client,
    XhhError,
)
from .content import flatten_comments, parse_link, plain_text_comment
from .sign import KEY, gen_nonce, hkey, sign

__version__ = "1.0.0"


class Client(
    FeedsAPI, SearchAPI, LinkAPI, UserAPI, MessageAPI,
    GameAPI, EditorAPI, MiscAPI, _Client,
):
    """聚合全部接口方法的客户端。"""


__all__ = [
    "Client", "XhhError", "CaptchaRequired",
    "hkey", "sign", "gen_nonce", "KEY",
    "API_BASE", "BASE_PARAMS", "UA",
    "parse_link", "flatten_comments", "plain_text_comment",
    "__version__",
]
