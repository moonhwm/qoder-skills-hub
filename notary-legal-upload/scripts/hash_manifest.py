#!/usr/bin/env python3
"""hash_manifest.py — 目录级 SHA-256 清单生成与校验（证据固化第一步）

用法：
  生成清单：python3 hash_manifest.py create <源文件目录> [-o 输出清单路径]
  校验清单：python3 hash_manifest.py verify <清单路径>

约定：
  - 清单格式与 sha256sum 输出一致："<hash>  <相对路径>"，按文件名排序去重。
  - 默认清单写到 <源文件目录>/SOURCE_MANIFEST.sha256，且清单本身不参与哈希。
  - verify 逐行核对：文件缺失、哈希不符、清单外新增文件，全部报告。
"""
import hashlib
import sys
from pathlib import Path

MANIFEST_NAME = "SOURCE_MANIFEST.sha256"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def create(directory: Path, output: Path | None = None) -> int:
    if not directory.is_dir():
        print(f"错误：{directory} 不是目录", file=sys.stderr)
        return 2
    output = output or directory / MANIFEST_NAME
    lines = {}
    for p in sorted(directory.iterdir()):
        if not p.is_file() or p.name == MANIFEST_NAME or p.name == output.name:
            continue
        lines[p.name] = sha256_file(p)
    with open(output, "w", encoding="utf-8") as f:
        for name in sorted(lines):
            f.write(f"{lines[name]}  {name}\n")
    print(f"已生成 {output}（{len(lines)} 个文件）")
    return 0


def verify(manifest: Path) -> int:
    if not manifest.is_file():
        print(f"错误：{manifest} 不存在", file=sys.stderr)
        return 2
    base = manifest.parent
    listed = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, name = line.partition("  ")
        listed[name] = digest
    ok, problems = 0, []
    for name, digest in listed.items():
        p = base / name
        if not p.is_file():
            problems.append(f"缺失: {name}")
        elif sha256_file(p) != digest:
            problems.append(f"哈希不符: {name}")
        else:
            ok += 1
    for p in sorted(base.iterdir()):
        if p.is_file() and p.name not in listed and p.name != manifest.name:
            problems.append(f"清单外新增: {p.name}")
    print(f"校验通过 {ok}/{len(listed)}")
    for prob in problems:
        print(f"  ⚠ {prob}")
    return 1 if problems else 0


def main(argv):
    if len(argv) < 3 or argv[1] not in ("create", "verify"):
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "create":
        out = Path(argv[4]) if len(argv) >= 5 and argv[3] == "-o" else None
        return create(Path(argv[2]), out)
    return verify(Path(argv[2]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
