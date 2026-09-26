#!/usr/bin/env python3
"""k3_security 自测（纯标准库）：全过 exit 0，任一败 exit 1。"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from k3_security import (totp_secret, totp, totp_verify, device_fingerprint,
                         hash_password, verify_password)

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond: fails.append(name)

# TOTP（RFC 6238 测试向量, sha1/8位/59秒步 — 本实现 6 位, 故用自洽性+窗口测）
sec = totp_secret()
check("totp_secret 32字符base32", len(sec) == 32)
code = totp(sec)
check("totp 6位数字", code.isdigit() and len(code) == 6)
check("totp_verify 自洽", totp_verify(sec, code))
check("totp_verify 拒错码", not totp_verify(sec, "000000" if code != "000000" else "111111"))
check("totp 窗口±1 接受", totp_verify(sec, totp(sec, int(time.time()) - 30)))

# 指纹：同人同机稳定、extra 扰动即变、64hex
f1, f2 = device_fingerprint(), device_fingerprint()
check("fingerprint 稳定", f1 == f2 and len(f1) == 64)
check("fingerprint 扰动敏感", device_fingerprint("x") != f1)

# 慢哈希：双方案往返 + 错口令拒绝 + 盐随机
h1 = hash_password("correct-horse", "pbkdf2", rounds=10_000)
h2 = hash_password("correct-horse", "scrypt")
check("pbkdf2 往返", verify_password("correct-horse", h1))
check("scrypt 往返", verify_password("correct-horse", h2))
check("错口令拒绝", not verify_password("wrong", h1) and not verify_password("wrong", h2))
check("盐随机", hash_password("a", "pbkdf2", rounds=10_000) != hash_password("a", "pbkdf2", rounds=10_000))

print(f"\n{'全过' if not fails else '失败: ' + str(fails)}")
sys.exit(0 if not fails else 1)
