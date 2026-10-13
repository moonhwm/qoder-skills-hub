#!/usr/bin/env python3
"""gh_sync_verify.py — GitHub 镜像同步的逐字节核验工具（纯标准库）。

子命令：
  blob-sha   计算本地文件的 git-blob sha 与字节数
  manifest   扫描本地树生成 {relpath: {sha, size}} 清单
  verify-file  单件核验：远端 contents API 拉回，断言 sha+size 双等
  verify-tree  全树终验：git/trees/<ref>?recursive=1 比对 manifest
  shard      大文件分片 + 指针文件（含总 sha/size 与片清单）
  reassemble 分片拼接还原并复算 sha/size（端到端验证）

私有仓/限流时用环境变量 GH_TOKEN 注入（只读 header，不回显）。
退出码：0=全过；1=有不符；2=用法/环境错误。
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.request

API = "https://api.github.com"
UA = {"User-Agent": "gh-sync-verify", "Accept": "application/vnd.github+json"}


def blob_sha(data: bytes) -> str:
    """git blob 对象 sha：sha1(b"blob <len>\\0" + data)。"""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _headers():
    h = dict(UA)
    tok = os.environ.get("GH_TOKEN", "").strip()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def gh_json(path: str, timeout: int = 60):
    req = urllib.request.Request(f"{API}{path}", headers=_headers())
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def cmd_blob_sha(a):
    rc = 0
    for f in a.files:
        try:
            d = open(f, "rb").read()
        except OSError as e:
            print(f"UNREADABLE {f}: {e}")
            rc = 1
            continue
        print(f"{blob_sha(d)}  {len(d)}B  {f}")
    return rc


def cmd_manifest(a):
    root = os.path.abspath(a.root)
    man = {}
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in (".git", "__pycache__")]
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            d = open(p, "rb").read()
            man[rel] = {"sha": blob_sha(d), "size": len(d)}
    out = a.out or "manifest.json"
    json.dump(man, open(out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print(f"manifest: {len(man)} files -> {out}")
    return 0


def cmd_verify_file(a):
    local = open(a.local, "rb").read()
    want_sha, want_size = blob_sha(local), len(local)
    j = gh_json(f"/repos/{a.owner}/{a.repo}/contents/{a.path}?ref={a.branch}")
    remote = base64.b64decode(j["content"])
    got_sha, got_size = blob_sha(remote), len(remote)
    ok = (got_sha == want_sha and got_size == want_size and j.get("sha") == got_sha)
    print(json.dumps({
        "path": a.path, "status": "PASS" if ok else "MISMATCH",
        "local": {"sha": want_sha, "size": want_size},
        "remote": {"sha": got_sha, "size": got_size, "api_sha": j.get("sha")},
    }, ensure_ascii=False))
    return 0 if ok else 1


def cmd_verify_tree(a):
    man = json.load(open(a.manifest))
    if isinstance(man, list):  # 兼容纯路径清单
        man = {p: None for p in man}
    tree = gh_json(f"/repos/{a.owner}/{a.repo}/git/trees/{a.ref}?recursive=1")
    tmap = {e["path"]: e.get("sha") for e in tree.get("tree", []) if e.get("type") == "blob"}
    missing, mismatch = [], []
    for rel, meta in man.items():
        want = meta["sha"] if isinstance(meta, dict) else None
        got = tmap.get(rel)
        if got is None:
            missing.append(rel)
        elif want and got != want:
            mismatch.append({"path": rel, "want": want, "got": got})
    total = len(man)
    passed = total - len(missing) - len(mismatch)
    print(json.dumps({
        "status": "PASS" if not missing and not mismatch else "FAIL",
        "passed": passed, "total": total,
        "missing": missing[:20], "mismatch": mismatch[:20],
        "truncated_remote_tree": bool(tree.get("truncated")),
    }, ensure_ascii=False, indent=1))
    if tree.get("truncated"):
        print("WARN: 远端树被 API 截断（truncated=true），终验不完整——分批或改 git 车道复核", file=sys.stderr)
    return 0 if not missing and not mismatch else 1


def cmd_shard(a):
    data = open(a.file, "rb").read()
    total_sha, total_size = blob_sha(data), len(data)
    os.makedirs(a.outdir, exist_ok=True)
    parts = []
    for i in range(0, total_size, a.size):
        chunk = data[i:i + a.size]
        name = f"p{len(parts)}.part"
        open(os.path.join(a.outdir, name), "wb").write(chunk)
        parts.append({"name": name, "sha": blob_sha(chunk), "size": len(chunk)})
    pointer = {
        "source": os.path.basename(a.file), "total_sha": total_sha,
        "total_size": total_size, "part_size": a.size, "parts": parts,
    }
    pf = os.path.join(a.outdir, os.path.basename(a.file) + ".PARTS.json")
    json.dump(pointer, open(pf, "w"), ensure_ascii=False, indent=1)
    print(f"shard: {total_size}B -> {len(parts)} parts, pointer={pf}, total_sha={total_sha}")
    return 0


def cmd_reassemble(a):
    pointer = json.load(open(a.pointer))
    buf = b""
    for p in pointer["parts"]:
        chunk = open(os.path.join(os.path.dirname(a.pointer), p["name"]), "rb").read()
        if blob_sha(chunk) != p["sha"]:
            print(f"FAIL: part {p['name']} sha mismatch")
            return 1
        buf += chunk
    ok = len(buf) == pointer["total_size"] and blob_sha(buf) == pointer["total_sha"]
    print(json.dumps({"status": "PASS" if ok else "FAIL",
                      "size": len(buf), "sha": blob_sha(buf)}, ensure_ascii=False))
    if ok and a.out:
        open(a.out, "wb").write(buf)
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("blob-sha", help="本地文件 git-blob sha")
    p.add_argument("files", nargs="+")
    p.set_defaults(fn=cmd_blob_sha)

    p = sub.add_parser("manifest", help="扫描本地树生成清单")
    p.add_argument("root")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_manifest)

    p = sub.add_parser("verify-file", help="单件远端核验")
    p.add_argument("owner"); p.add_argument("repo"); p.add_argument("path"); p.add_argument("local")
    p.add_argument("--branch", default="main")
    p.set_defaults(fn=cmd_verify_file)

    p = sub.add_parser("verify-tree", help="全树终验")
    p.add_argument("owner"); p.add_argument("repo")
    p.add_argument("--manifest", required=True)
    p.add_argument("--ref", default="HEAD")
    p.set_defaults(fn=cmd_verify_tree)

    p = sub.add_parser("shard", help="大文件分片")
    p.add_argument("file")
    p.add_argument("--size", type=int, default=50 * 1024 * 1024, help="单片字节数（默认 50MB）")
    p.add_argument("--outdir", required=True)
    p.set_defaults(fn=cmd_shard)

    p = sub.add_parser("reassemble", help="分片还原验证")
    p.add_argument("pointer", help="指针文件 *.PARTS.json")
    p.add_argument("--out", help="可选：还原落盘路径")
    p.set_defaults(fn=cmd_reassemble)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
