# -*- coding: utf-8 -*-
"""从打包后的 JS 里恢复出完整的 (HTTP方法, 路径) 清单。

打包代码的固定形态：
    const XX="/bbs/app/xxx"; function YY(e,t,o){return ZZ.$get/$post(XX,e,t,o)}
所以用正则先把 "/path" 赋值抓出来，再看它后面 200 字符内出现的 $get / $post。
"""
import re, glob, json, sys, io, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# const <id> = "<path>";
DECL = re.compile(r'(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"(/[A-Za-z0-9_\-/\.]{2,120})"')
# 引用处：$get(ID / $post(ID
CALL = re.compile(r'\$(\w+?)\(\s*([A-Za-z_$][\w$]*)\s*[,)]')

found = {}   # (method, path) -> {"ids": set, "files": set, "count": int}

for f in sorted(glob.glob("js3/**/*.js", recursive=True)):
    try:
        t = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    id2path = {}
    for m in DECL.finditer(t):
        id2path.setdefault(m.group(1), m.group(2))
    for m in CALL.finditer(t):
        fn, var = m.group(1), m.group(2)
        if var not in id2path:
            continue
        if fn not in ("get", "post", "put", "delete", "patch"):
            continue
        path = id2path[var]
        key = (fn.upper(), path)
        d = found.setdefault(key, {"ids": set(), "files": set(), "count": 0})
        d["ids"].add(var)
        d["files"].add(f)
        d["count"] += 1

# 另外补一批「直接内联字符串 + $get/$post」的写法
INLINE = re.compile(r'\$(\w+?)\(\s*"(/[A-Za-z0-9_\-/\.]{2,120})"')
for f in sorted(glob.glob("js3/**/*.js", recursive=True)):
    try:
        t = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for m in INLINE.finditer(t):
        fn, path = m.group(1), m.group(2)
        if fn not in ("get", "post", "put", "delete", "patch"):
            continue
        d = found.setdefault((fn.upper(), path), {"ids": set(), "files": set(), "count": 0})
        d["files"].add(f)
        d["count"] += 1

rows = sorted(((m, p, d) for (m, p), d in found.items()), key=lambda x: (x[1], x[0]))

print("distinct endpoint: %d\n" % len(rows))

# 按顶级前缀分组，方便看有哪些业务域
buckets = collections.defaultdict(list)
for m, p, d in rows:
    top = p.strip("/").split("/")[0]
    buckets[top].append((m, p, d))

for top in sorted(buckets):
    print("=" * 70)
    print("# %-20s (%d)" % (top, len(buckets[top])))
    for m, p, d in buckets[top]:
        print("  %-5s %s" % (m, p))

json.dump(
    [{"method": m, "path": p, "refs": d["count"], "files": sorted(d["files"])} for m, p, d in rows],
    open("endpoints.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1,
)
print("\nsaved endpoints.json")
