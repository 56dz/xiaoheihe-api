"""小黑盒 (xiaoheihe) Web API 签名算法。

来源
----
`https://static.max-c.com/static/heybox/webapp/@heybox-spa/website/app/index-*.js`

调用链
------
``Tr() -> qM() / WM() / Wwe() / Uwe() / qwe() -> S3()/Pc()/Sf()/Bh()/lg()``

hkey 结构
---------
``[5 字符主干] + [2 位十进制校验]``，共 7 字符。

算法
----
1. 路径规范化：去空段、首尾补 ``/``。
2. 三段素材：
   - ``o = qM(str(_time), KEY, -2)``  时间戳，取 KEY 前 30 位
   - ``a = WM(path)``                 路径，用 KEY 全表
   - ``s = WM(nonce)``                nonce，用 KEY 全表
3. ``Wwe([o, a, s])[:20]`` —— 按列交织后截前 20 字符。
4. 对 seed 取 md5。
5. 校验位：``Uwe(qwe([ord(c) for c in md5[-6:]])) % 100``，补零到 2 位。
6. 主干：``qM(md5[:5], KEY, -4)`` 取 5 字符。
"""

from __future__ import annotations

import hashlib
import secrets
import string
import time

__all__ = ["KEY", "hkey", "sign", "gen_nonce"]

#: 32 字符映射表（秘密常量，硬编码在 bundle 里）
KEY = "AB45STUVWZEFGJ6CH01D237IXYPQRKLMN89"

_HEX = string.hexdigits.upper()[:16]


# ---------------------------------------------------------------------------
# GF(2^8) 线性变换（本原多项式 x^8+x^4+x^3+x+1，即 AES 的 0x1B 约简）
# ---------------------------------------------------------------------------
def _s3(e: int) -> int:
    """xtime：乘以 x。"""
    return ((e << 1) ^ 0x1B) & 0xFF if e & 0x80 else (e << 1) & 0xFF


def _pc(e: int) -> int:
    return _s3(e) ^ e


def _sf(e: int) -> int:
    return _pc(_s3(e))


def _bh(e: int) -> int:
    return _sf(_pc(_s3(e)))


def _lg(e: int) -> int:
    return _bh(e) ^ _sf(e) ^ _pc(e)


def _qwe(codes: list[int]) -> list[int]:
    """4x4 MDS 矩阵混合。

    原实现会**原地**把前 4 个元素换成混合结果，然后返回整个（可能长于 4 的）
    数组；调用方 `Uwe` 对返回数组的所有元素求和。这里必须保留该副作用，
    否则校验位会算错（这也是最容易踩的坑）。
    """
    t = [0, 0, 0, 0]
    t[0] = _lg(codes[0]) ^ _bh(codes[1]) ^ _sf(codes[2]) ^ _pc(codes[3])
    t[1] = _pc(codes[0]) ^ _lg(codes[1]) ^ _bh(codes[2]) ^ _sf(codes[3])
    t[2] = _sf(codes[0]) ^ _pc(codes[1]) ^ _lg(codes[2]) ^ _bh(codes[3])
    t[3] = _bh(codes[0]) ^ _sf(codes[1]) ^ _pc(codes[2]) ^ _lg(codes[3])
    codes[:4] = t
    return codes


# ---------------------------------------------------------------------------
# 基础映射
# ---------------------------------------------------------------------------
def qm(e: str, t: str = KEY, n: int = 0) -> str:
    """从 ``t`` 的前 ``n`` 位切片按 ``e`` 的字符码取字符（``n=0`` 表示全表）。"""
    o = t[:n] if n != 0 else t
    return "".join(o[ord(ch) % len(o)] for ch in e)


def wm(e: str, t: str = KEY) -> str:
    """按 ``e`` 的字符码从 ``t`` 全表取字符。"""
    return "".join(t[ord(ch) % len(t)] for ch in e)


def wwe(parts) -> str:
    """按列交织多个等长/不等长字符串。"""
    return "".join(p[i] for i in range(max(len(p) for p in parts)) for p in parts if i < len(p))


def uwe(vals) -> int:
    return sum(vals)


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------
def normalize_path(url_path: str) -> str:
    """规范化路径：去掉空段，首尾补 ``/``。查询串必须提前剥离。"""
    path = url_path.split("?", 1)[0]
    return "/" + "/".join(seg for seg in path.split("/") if seg) + "/"


def hkey(url_path: str, _time: int, nonce: str) -> str:
    """计算 ``hkey``。

    :param url_path: 接口路径，如 ``/bbs/app/feeds``（不含域名与 query）
    :param _time:    秒级时间戳
    :param nonce:    32 位大写十六进制随机串
    """
    path = normalize_path(url_path)

    o = qm(str(_time), KEY, -2)
    a = wm(path)
    s = wm(nonce)

    seed = wwe([o, a, s])[:20]
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()

    codes = [ord(c) for c in digest[-6:]]
    check = str(uwe(_qwe(codes)) % 100).rjust(2, "0")

    body = qm(digest[:5], KEY, -4)
    return body + check


def gen_nonce(n: int = 32) -> str:
    """生成 ``n`` 位大写十六进制 nonce（默认 32 位，与原实现一致）。"""
    return "".join(secrets.choice(_HEX) for _ in range(n))


def sign(url_path: str, _time: int | None = None, nonce: str | None = None) -> dict:
    """返回可直接并入 query 的签名字段。"""
    if _time is None:
        _time = int(time.time())
    if nonce is None:
        nonce = gen_nonce()
    return {"hkey": hkey(url_path, _time, nonce), "_time": _time, "nonce": nonce}


# ---------------------------------------------------------------------------
# 自检
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 真实抓包样本：若全部通过，说明 KEY 与算法均正确
    SAMPLES = [
        ("/bbs/app/feeds", 1793159576, "E228D657D7AE3182EFDA4283E2C32F06", "VS2S006"),
        ("/bbs/app/feeds/banner", 1793159576, "B358F4066EC902AACCE68BBCA66EDDE2", "D7PV763"),
        ("/account/restore_login", 1793159576, "22BF3B0F660816C5929439F2E9D80299", "YT0TV70"),
        ("/bbs/app/topic/categories", 1793159576, "D78865C774303864E97ECB6119BC30C4", "VUP1022"),
        ("/bbs/app/api/search/found", 1793159576, "4399A965B2891DC60660993ADF5F3C44", "1371749"),
        ("/bbs/app/api/search/welcome_page/v2", 1793159576, "DAFC50032B4C5B13E91EB517AE9EE717", "U00UU96"),
    ]
    ok = 0
    for path, ts, nonce, expect in SAMPLES:
        got = hkey(path, ts, nonce)
        flag = "OK  " if got == expect else "FAIL"
        ok += got == expect
        print(f"{flag} {path:42s} got={got} expect={expect}")
    print(f"\n{ok}/{len(SAMPLES)} passed")
