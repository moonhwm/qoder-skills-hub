#!/usr/bin/env python3
"""verify_parts.py -- verify and reassemble the chunked sample-bank-1000.jsonl
Published 2026-10-01 by K3 Orchestrator (byte-exact push; ASCII-only to survive
model output-layer escapes).

Why chunks: the original file (353374 bytes, 1000 lines) exceeded the upload
lane's message limit, so it was published as 7 contiguous line-chunks:
  p0.jsonl  50454 bytes  hash 1b1baf37da691847ab6b544727452c0af62965aa  lines   1-143
  p1.jsonl  50315 bytes  hash 59aebd9984081e66fb93aae709b213ac240d1022  lines 144-286
  p2.jsonl  50681 bytes  hash 47088c3dd39e3d93ea1bd7f1b37a0530f04ff793  lines 287-429
  p3.jsonl  51007 bytes  hash 86169a4a7797a3ed8cb801b91a3b76ab4ab82efa  lines 430-572
  p4.jsonl  50355 bytes  hash ba5d0ba7a9806faa555bc01ad229e8dc86f4fd7f  lines 573-715
  p5.jsonl  50273 bytes  hash 0bc774e481345eeba86542935874881c39e0c965  lines 716-858
  p6.jsonl  50289 bytes  hash abd80fd5acd9a5c8a828d84a77df46cd556d2992  lines 859-1000

Reassembled file must be:
  353374 bytes, 1000 lines, git-hash-object 2be7f5e28fd831f86b29fe1271b0ac17f9486f45

Usage:
  python3 verify_parts.py PARTS_DIR [--write OUT.jsonl]
    PARTS_DIR: directory containing p0.jsonl .. p6.jsonl
    --write  : also write the reassembled file (default: verify only)
Exit code 0 = all checks pass; 2 = mismatch (details on stderr).
"""
import hashlib, os, sys

EXPECTED = [
    ("p0.jsonl", 50454, "1b1baf37da691847ab6b544727452c0af62965aa", 143),
    ("p1.jsonl", 50315, "59aebd9984081e66fb93aae709b213ac240d1022", 143),
    ("p2.jsonl", 50681, "47088c3dd39e3d93ea1bd7f1b37a0530f04ff793", 143),
    ("p3.jsonl", 51007, "86169a4a7797a3ed8cb801b91a3b76ab4ab82efa", 143),
    ("p4.jsonl", 50355, "ba5d0ba7a9806faa555bc01ad229e8dc86f4fd7f", 143),
    ("p5.jsonl", 50273, "0bc774e481345eeba86542935874881c39e0c965", 143),
    ("p6.jsonl", 50289, "abd80fd5acd9a5c8a828d84a77df46cd556d2992", 142),
]
FINAL_SIZE = 353374
FINAL_LINES = 1000
FINAL_BLOB = "2be7f5e28fd831f86b29fe1271b0ac17f9486f45"


def file_hash(b):
    header = str(len(b)).encode() + b"\0"
    return hashlib.sha1(b"blob " + header + b).hexdigest()


def fail(msg):
    print("[FAIL] " + msg, file=sys.stderr)
    sys.exit(2)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    d = args[0]
    write = "--write" in sys.argv
    out = None
    if write:
        i = sys.argv.index("--write")
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            out = sys.argv[i + 1]
        else:
            out = "sample-bank-1000.jsonl"

    parts = []
    for name, size, sha, nlines in EXPECTED:
        p = os.path.join(d, name)
        if not os.path.isfile(p):
            fail("missing " + p)
        b = open(p, "rb").read()
        got = file_hash(b)
        nl = b.count(b"\n")
        if len(b) != size:
            fail("%s size %d != %d" % (name, len(b), size))
        if got != sha:
            fail("%s hash %s != %s" % (name, got, sha))
        if nl != nlines:
            fail("%s lines %d != %d" % (name, nl, nlines))
        if not b.endswith(b"\n"):
            fail("%s lacks trailing newline" % name)
        parts.append(b)
        print("[ok] %s %dB %dL %s" % (name, len(b), nl, sha[:12]))

    whole = b"".join(parts)
    if len(whole) != FINAL_SIZE:
        fail("reassembled size %d != %d" % (len(whole), FINAL_SIZE))
    if whole.count(b"\n") != FINAL_LINES:
        fail("reassembled lines %d != %d" % (whole.count(b"\n"), FINAL_LINES))
    if file_hash(whole) != FINAL_BLOB:
        fail("reassembled hash %s != %s" % (file_hash(whole), FINAL_BLOB))
    print("[ok] reassembled %dB %dL hash %s" % (len(whole), FINAL_LINES, FINAL_BLOB))

    if write:
        with open(out, "wb") as f:
            f.write(whole)
        print("[ok] wrote " + out)
    print("ALL CHECKS PASS")


if __name__ == "__main__":
    main()
