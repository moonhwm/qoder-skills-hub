#!/usr/bin/env python3
"""zip_crack.py — 自有加密 zip 定长数字密码爆破（仅限本人文件 + 用户书面授权场景）
v1.0 2026-08-28 Orchestrator (Kimi K3)｜泛化自美团/京东账单实战脚本

铁律1【授权】：仅用于用户本人文件且已明确授权；脚本每次运行打印授权确认行。
铁律2【两级校验】：快速预筛必有误报（AES 2字节校验值≈1/65536；ZipCrypto 头校验字节≈1/256），
  命中后必须 full_verify（完整解密+CRC/认证码）才算真密码——实战误报真实发生过。
铁律3【自包含】：AES 终验需 pyzipper（缺时保留候选并给安装命令，不静默）；
  ZipCrypto 优先 vendored C 加速器（scripts/jd_crack.c，有 gcc 自动编译），
  无编译器退化 stdlib 纯 Python 头校验预筛（慢但可用）。
铁律4【保密】：产出的密码文件 = credentials.env 同级保密，绝不打包进 .skill / git / 提示词。

用法:
  python3 zip_crack.py "美团账单*.zip"                 # 通配多包，6位数字
  python3 zip_crack.py bill.zip --digits 6 --workers 3 --out passwords.json
  python3 zip_crack.py bill.zip --resume passwords.json  # 复跑跳过已破解
"""
import argparse, glob, hashlib, json, os, struct, subprocess, sys, time
from multiprocessing import Process, Queue, Manager

CANDIDATES = ["123456", "000000", "666666", "888888", "111111", "654321",
              "112233", "121212", "102938", "996633"]

# ---------- 加密类型识别 ----------
def detect(path):
    """返回 ('aes', salt, verifier) 或 ('zipcrypto', check_byte, first_name) 或 ('plain',)"""
    with open(path, "rb") as f:
        head = f.read(65536)
    if head[:4] != b"PK\x03\x04":
        sys.exit(f"[错误] 非 zip 文件：{path}")
    flag = struct.unpack("<H", head[6:8])[0]
    if not flag & 0x1:
        return ("plain",)
    fn_len, ex_len = struct.unpack("<HH", head[26:30])
    off = 30 + fn_len
    extra = head[off:off + ex_len]
    i = 0
    while i + 4 <= len(extra):
        tag, sz = struct.unpack("<HH", extra[i:i+4])
        if tag == 0x9901:  # AES extra field
            strength = extra[i+6]
            salt_len = {1: 8, 2: 12, 3: 16}.get(strength, 16)
            doff = off + ex_len
            return ("aes", head[doff:doff+salt_len], head[doff+salt_len:doff+salt_len+2])
        i += 4 + sz
    # ZipCrypto：校验字节 = 首文件 CRC 高字节（bit3 置位时为 mtime 高字节）
    import zipfile
    with zipfile.ZipFile(path) as z:
        zi = z.infolist()[0]
        chk = (zi.date_time[5] >> 0) & 0xFF if flag & 0x8 else (zi.CRC >> 24) & 0xFF
        if flag & 0x8:
            chk = zi._raw_time >> 8 & 0xFF if hasattr(zi, "_raw_time") else chk
        return ("zipcrypto", chk, zi.filename, flag)

# ---------- AES ----------
def aes_check(salt, verifier, pw):
    dk = hashlib.pbkdf2_hmac("sha1", pw.encode(), salt, 1000, 66)
    return dk[64:66] == verifier

def aes_verify(path, pw):
    try:
        import pyzipper
    except ImportError:
        return None  # 无法终验：显式返回 None，调用方必须告警
    try:
        with pyzipper.AESZipFile(path) as z:
            z.read(z.namelist()[0], pwd=pw.encode())
        return True
    except Exception:
        return False

# ---------- ZipCrypto ----------
_CRCTAB = []
def _crc_tab():
    global _CRCTAB
    if _CRCTAB:
        return _CRCTAB
    for i in range(256):
        c = i
        for _ in range(8):
            c = (0xEDB88320 ^ (c >> 1)) if c & 1 else (c >> 1)
        _CRCTAB.append(c)
    return _CRCTAB

def zc_header_ok(path, pw, chk):
    """纯 Python：解密 12 字节加密头，末字节应等于校验字节（≈1/256 误报）"""
    tab = _crc_tab()
    with open(path, "rb") as f:
        head = f.read(65536)
    fn_len, ex_len = struct.unpack("<HH", head[26:30])
    enc = head[30+fn_len+ex_len: 30+fn_len+ex_len+12]
    k = [0x12345678, 0x23456789, 0x34567890]
    def upd(b):
        k[0] = tab[(k[0] ^ b) & 0xFF] ^ (k[0] >> 8)
        k[1] = ((k[1] + (k[0] & 0xFF)) * 134775813 + 1) & 0xFFFFFFFF
        k[2] = tab[(k[2] ^ (k[1] >> 24)) & 0xFF] ^ (k[2] >> 8)
    for b in pw.encode():
        upd(b)
    out = bytearray()
    for c in enc:
        t = (k[2] | 2) & 0xFFFFFFFF
        p = ((t * (t ^ 1)) >> 8) & 0xFF
        out.append(c ^ p)
        upd(p)
    return out[11] == chk

def zc_verify(path, pw):
    import zipfile
    try:
        with zipfile.ZipFile(path) as z:
            z.read(z.infolist()[0].filename, pwd=pw.encode())
        return True
    except Exception:
        return False

def c_accel(path):
    """vendored C 加速器：有 gcc 现场编译；返回密码或 None；编译失败返回 'nogcc'"""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jd_crack.c")
    if not os.path.exists(src):
        return None
    exe = f"/tmp/_zip_crack_accel_{os.getuid()}"
    if not os.path.exists(exe):
        r = subprocess.run(["gcc", "-O3", src, "-o", exe, "-lz"], capture_output=True, text=True)
        if r.returncode != 0:
            return "nogcc"
    r = subprocess.run([exe, path], capture_output=True, text=True, timeout=1800)
    pw = r.stdout.strip()
    return pw if r.returncode == 0 and pw else None

# ---------- 主流程 ----------
def crack_one(path, digits, found_cache):
    name = os.path.basename(path)
    if name in found_cache:
        pw = found_cache[name]
        ok = aes_verify(path, pw) if detect(path)[0] == "aes" else zc_verify(path, pw)
        if ok:
            print(f"[复跑跳过] {name} 已验证密码在册")
            return pw
    t = detect(path)
    if t[0] == "plain":
        print(f"[明文] {name} 未加密，直接解压即可")
        return ""
    print(f"[{name}] 类型={t[0].upper()} 开始 {10**digits} 空间爆破…")
    for pw in CANDIDATES:
        if len(pw) != digits:
            continue
        if t[0] == "aes" and aes_check(t[1], t[2], pw) and aes_verify(path, pw):
            return pw
        if t[0] == "zipcrypto" and zc_header_ok(path, pw, t[1]) and zc_verify(path, pw):
            return pw
    if t[0] == "zipcrypto":
        r = c_accel(path)
        if r == "nogcc":
            print("  ⚠ 无 gcc/编译失败，退化纯 Python（慢）")
        elif r:
            return r if zc_verify(path, r) else None
        t0 = time.time()
        for i in range(10 ** digits):
            pw = f"{i:0{digits}d}"
            if zc_header_ok(path, pw, t[1]) and zc_verify(path, pw):
                return pw
            if i % 50000 == 49999:
                print(f"  …{i+1}/{10**digits} ({(i+1)/(time.time()-t0):.0f} pw/s)")
        return None
    # AES：纯 python pbkdf2 预筛 ≈ 数百 pw/s，多进程切区间
    return aes_brute(path, t[1], t[2], digits)

def _aes_worker(rg, q, salt, verifier, path, hit):
    for i in rg:
        if hit.value:
            return
        pw = f"{i:0{PW_DIGITS}d}"
        if aes_check(salt, verifier, pw):
            v = aes_verify(path, pw)
            if v is True:
                q.put(pw); hit.value = 1; return
            elif v is None:
                q.put(("UNVERIFIED", pw)); hit.value = 1; return

PW_DIGITS = 6
def aes_brute(path, salt, verifier, digits):
    global PW_DIGITS
    PW_DIGITS = digits
    n = os.cpu_count() or 2
    workers = max(1, min(3, n - 1))
    q = Queue()
    from multiprocessing import Value
    hit = Value("i", 0)
    step = (10 ** digits + workers - 1) // workers
    procs = [Process(target=_aes_worker,
                     args=(range(s, min(s + step, 10 ** digits)), q, salt, verifier, path, hit))
             for s in range(0, 10 ** digits, step)]
    t0 = time.time()
    for p in procs: p.start()
    print(f"  AES 纯python预筛 {workers} 进程并行（pbkdf2 约数百pw/s/核，全程可能以小时计）")
    while any(p.is_alive() for p in procs):
        try:
            r = q.get(timeout=30)
            for p in procs: p.terminate()
            if isinstance(r, tuple) and r[0] == "UNVERIFIED":
                print(f"  ⚠ 预筛命中 {r[1]} 但缺 pyzipper 无法终验：pip install pyzipper 后 --resume 复跑")
                return None
            return r
        except Exception:
            el = int(time.time() - t0)
            print(f"  …t+{el}s 进行中")
    return None

def main():
    print("[授权确认] 本工具仅限用户本人文件且已书面授权的场景使用。")
    p = argparse.ArgumentParser()
    p.add_argument("pattern", help="zip 路径或通配（如 \"账单*.zip\"）")
    p.add_argument("--digits", type=int, default=6)
    p.add_argument("--out", default=None, help="密码登记 json（默认同目录 _passwords.json，注意保密）")
    p.add_argument("--resume", default=None, help="已有密码 json，复跑跳过")
    a = p.parse_args()
    zips = sorted(glob.glob(a.pattern)) or ([a.pattern] if os.path.exists(a.pattern) else [])
    if not zips:
        sys.exit(f"[错误] 无匹配文件：{a.pattern}")
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(zips[0])), "_passwords.json")
    cache = {}
    for fp in (a.resume, out):
        if fp and os.path.exists(fp):
            cache.update(json.load(open(fp)))
    result = dict(cache)
    for zp in zips:
        name = os.path.basename(zp)
        if name in result and result[name]:
            continue
        pw = crack_one(zp, a.digits, cache)
        result[name] = pw
        json.dump(result, open(out, "w"), ensure_ascii=False, indent=1)
        print(f"[{'命中' if pw else '未破'}] {name} → {pw or '（穷举空间内无密码）'}")
    print(f"[落盘] {out}（= credentials.env 同级保密，勿外传勿入包）")

if __name__ == "__main__":
    main()
