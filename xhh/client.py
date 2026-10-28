"""HTTP 客户端：统一处理签名、公共参数、cookie、重试与错误。"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from .sign import gen_nonce, sign

API_BASE = "https://api.xiaoheihe.cn"

#: 全站共用的固定参数（web 端）。
BASE_PARAMS = {
    "app": "heybox",
    "os_type": "web",
    "x_app": "heybox_website",
    "x_client_type": "web",
    "x_os_type": "Windows",
    "x_client_version": "",
    "client_type": "web",
    "web_version": "3.0",
    "version": "999.0.4",
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)

#: 服务端用 HTTP 200 + status 字段表达业务错误，这些状态视为失败。
ERROR_STATUS = {"failed", "login", "relogin", "expired", "frontend_failed"}


class XhhError(Exception):
    """请求失败（网络、HTTP 状态、业务 status）。"""

    def __init__(self, message, *, status=None, path=None, payload=None):
        super().__init__(message)
        self.status = status
        self.path = path
        self.payload = payload


class CaptchaRequired(XhhError):
    """触发了腾讯验证码风控：缺少或过期的 ``x_xhh_tokenid``。"""


def _cos_put(region, bucket, key, raw, mimetype, sign_time,
             secret_id, secret_key, session_token, timeout=120,
             host_suffix="myqcloud.com"):
    """向腾讯云 COS 直传一个对象（纯 urllib + 手工签名，无需 SDK）。

    COS 的签名分两层：先算 ``HttpString = "put\\n<uri>\\n<params>\\n<headers>\\n"``，
    再算 ``StringToSign = "sha1\\n<sign_time>\\n" + sha1(HttpString).hexdigest() + "\\n"``，
    最后 ``signature = HMAC-SHA1(HMAC-SHA1(secret_key, sign_time), StringToSign)``。
    少算中间那层 sha1 会一直拿到 403 SignatureDoesNotMatch。
    """
    import hashlib
    import hmac

    host = f"{bucket}.cos.{region}.{host_suffix}"
    uri = key if key.startswith("/") else "/" + key

    def _hmac(key_bytes, msg):
        return hmac.new(key_bytes, msg.encode("utf-8"), hashlib.sha1).hexdigest()

    sign_key = _hmac(secret_key.encode("utf-8"), sign_time)
    http_string = f"put\n{uri}\n\nhost={host}\n"
    string_to_sign = (
        "sha1\n" + sign_time + "\n"
        + hashlib.sha1(http_string.encode("utf-8")).hexdigest() + "\n"
    )
    signature = _hmac(sign_key.encode("utf-8"), string_to_sign)
    auth = (
        "q-sign-algorithm=sha1"
        f"&q-ak={secret_id}"
        f"&q-sign-time={sign_time}"
        f"&q-key-time={sign_time}"
        "&q-header-list=host"
        "&q-url-param-list="
        f"&q-signature={signature}"
    )

    req = urllib.request.Request(
        f"https://{host}{uri}",
        data=raw,
        method="PUT",
        headers={
            "Host": host,
            "Content-Type": mimetype,
            "Content-Length": str(len(raw)),
            "Authorization": auth,
            "x-cos-security-token": session_token,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


class Client:
    """小黑盒 API 客户端。

    :param cookie: 完整 cookie 串。至少需要 ``x_xhh_tokenid=...`` 才能过风控；
                   需要登录态时再加 ``user_pkey=...``。
    :param heybox_id: 当前账号 ID，会作为公共参数 ``heybox_id`` 发送。
    :param timeout: 单次请求超时（秒）。
    :param retries: 网络异常重试次数（不含首次）。
    :param ua: User-Agent，默认与本仓库抓包一致。
    """

    def __init__(
        self,
        cookie: str = "",
        heybox_id: str | int = "",
        timeout: float = 20,
        retries: int = 1,
        ua: str = UA,
        base: str = API_BASE,
    ):
        self.cookie = cookie
        self.heybox_id = str(heybox_id) if heybox_id else ""
        self.timeout = timeout
        self.retries = retries
        self.ua = ua
        self.base = base.rstrip("/")

    # ------------------------------------------------------------------
    # 构造 / 凭据
    # ------------------------------------------------------------------
    @classmethod
    def from_file(cls, path: str = "cookie.json", **kw):
        """从 ``get_token.js`` 产出的 cookie.json 载入。

        文件里若有 ``pkey`` 字段，会连同 ``heybox_id`` 一起带上，直接就是登录态；
        只有 ``cookie`` / ``token`` 时是匿名客户端，需要登录态的接口请再用
        :meth:`with_pkey` 追加。
        """
        p = path if os.path.isabs(path) else os.path.join(os.getcwd(), path)
        with open(p, encoding="utf-8") as f:
            d = json.load(f)

        cookie = d.get("cookie") or ""
        if not cookie and d.get("token"):
            cookie = "x_xhh_tokenid=" + urllib.parse.quote(d["token"], safe="")

        pkey = d.get("pkey") or ""
        if pkey and "user_pkey=" not in cookie:
            cookie = (cookie + "; " if cookie else "") + "user_pkey=" + pkey

        kw.setdefault("heybox_id", d.get("heybox_id") or "")
        kw.setdefault("ua", d.get("ua") or UA)
        return cls(cookie=cookie, **kw)

    def with_pkey(self, pkey: str, heybox_id: str | int = "") -> "Client":
        """返回带登录态的新客户端（不修改自身）。"""
        parts = [p for p in self.cookie.split("; ") if p and not p.startswith("user_pkey=")]
        parts.append("user_pkey=" + pkey)
        kw = dict(
            cookie="; ".join(parts),
            heybox_id=heybox_id or self.heybox_id,
            timeout=self.timeout,
            retries=self.retries,
            ua=self.ua,
            base=self.base,
        )
        return type(self)(**kw)

    @property
    def logged_in(self) -> bool:
        return "user_pkey=" in self.cookie

    # ------------------------------------------------------------------
    # 底层请求
    # ------------------------------------------------------------------
    def request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        data: dict | None = None,
        *,
        timeout: float | None = None,
        raw: bool = False,
        form: bool = True,
    ):
        """发一个已签名的请求。

        :param raw: 为 True 时返回 ``(payload, http_status)`` 二元组，
                    用于处理非标准 envelope 的接口。
        :param form: POST 请求体是否用 ``application/x-www-form-urlencoded``
                     编码。web 前端所有 POST 都走表单编码，默认 True；
                     少数接口（按服务端实现）只认 JSON 时传 False。
        """
        merged = dict(BASE_PARAMS)
        if self.heybox_id:
            merged["heybox_id"] = self.heybox_id
        for k, v in (params or {}).items():
            if v is None:
                continue
            merged[k] = v

        ts = int(time.time())
        merged.update(sign(path, ts, gen_nonce()))

        url = f"{self.base}{path}?{urllib.parse.urlencode(merged, encoding='utf-8')}"

        headers = {
            "User-Agent": self.ua,
            "Referer": "https://www.xiaoheihe.cn/",
            "Origin": "https://www.xiaoheihe.cn",
            "Accept": "application/json, text/plain, */*",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie

        body = None
        if (method or "GET").upper() == "POST":
            if form:
                body = urllib.parse.urlencode(data or {}, encoding="utf-8").encode("utf-8")
                headers["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8"
            else:
                body = json.dumps(data or {}, ensure_ascii=False).encode("utf-8")
                headers["Content-Type"] = "application/json;charset=UTF-8"

        last = None
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
            try:
                resp = urllib.request.urlopen(req, timeout=timeout or self.timeout)
                text = resp.read().decode("utf-8", "replace")
                code = resp.status
                break
            except urllib.error.HTTPError as e:
                # 4xx/5xx 也可能带 JSON 业务错误，先尝试解析
                text = e.read().decode("utf-8", "replace")
                code = e.code
                if e.code < 500:
                    break
                last = XhhError(f"HTTP {e.code}: {text[:200]}", path=path)
            except Exception as e:  # 超时 / 连接重置
                last = e
                if attempt < self.retries:
                    time.sleep(0.8 * (attempt + 1))
                    continue
                raise XhhError(f"请求失败: {e}", path=path) from e

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            if raw:
                return text, code
            raise XhhError(
                f"响应不是 JSON（HTTP {code}）: {text[:200]}", path=path
            ) from None

        if raw:
            return payload, code
        return payload

    def get(self, path: str, params: dict | None = None, **kw):
        """GET 快捷方式，参数可以传 dict 也可以传关键字。"""
        return self.request("GET", path, {**(params or {}), **kw})

    def post(self, path: str, params: dict | None = None, data: dict | None = None,
             *, form: bool = True):
        return self.request("POST", path, params, data, form=form)

    # ------------------------------------------------------------------
    # 便捷封装：取 result / 校验 status
    # ------------------------------------------------------------------
    def result(self, path: str, params: dict | None = None, *, method="GET",
               data: dict | None = None, timeout: float | None = None,
               form: bool = True):
        """取 ``payload["result"]``，并在 status 非 ok 时抛 :class:`XhhError`。

        ``status`` 缺失（接口直接返回业务 JSON）时原样返回 payload。
        """
        p = self.request(method, path, params, data, timeout=timeout, form=form)
        if not isinstance(p, dict):
            return p
        st = p.get("status")
        if st is None:
            return p
        if st == "show_captcha":
            raise CaptchaRequired(
                "触发验证码风控：cookie 中的 x_xhh_tokenid 缺失或已失效（用 get_token.js 重新获取）",
                status=st, path=path, payload=p,
            )
        if st != "ok":
            raise XhhError(
                p.get("msg") or f"status={st}", status=st, path=path, payload=p
            )
        return p.get("result")
