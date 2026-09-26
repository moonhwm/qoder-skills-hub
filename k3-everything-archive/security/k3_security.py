#!/usr/bin/env python3
"""K3 安全三件套（纯标准库，零依赖）：
1. MFA/TOTP（RFC 6238）：密钥生成、当前/指定步验证码、±1 窗口校验；
2. 设备指纹：多源本地特征（平台/机器/用户/环境变量集）慢哈希指纹，不含任何敏感串明文；
3. 慢哈希口令：PBKDF2-HMAC-SHA256（默认 600k 轮）与 scrypt（hashlib 原生）双方案 + 恒定时间比较。
参考成熟度：TOTP=RFC 6238 成熟标准；PBKDF2=RFC 8018；scrypt=RFC 7914；指纹=多源特征拼接的工程惯例（非标准，标注 conf=estimated）。
"""
import hmac, hashlib, base64, os, struct, time, secrets, platform, getpass, json

# ---------- 1. MFA / TOTP (RFC 6238) ----------
def totp_secret(nbytes: int = 20) -> str:
    """生成 base32 密钥（可读分组，供写入认证器）。"""
    return base64.b32encode(secrets.token_bytes(nbytes)).decode()

def _hotp(secret_b32: str, counter: int, digits: int = 6, digest=hashlib.sha1) -> str:
    key = base64.b32decode(secret_b32)
    msg = struct.pack(">Q", counter)
    hs = hmac.new(key, msg, digest).digest()
    off = hs[-1] & 0x0F
    code = (struct.unpack(">I", hs[off:off+4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)

def totp(secret_b32: str, t: int = None, step: int = 30, digits: int = 6) -> str:
    """当前（或指定时刻）TOTP 码。"""
    if t is None: t = int(time.time())
    return _hotp(secret_b32, t // step, digits)

def totp_verify(secret_b32: str, code: str, t: int = None, step: int = 30, window: int = 1) -> bool:
    """±window 窗口校验，恒定时间比较。"""
    if t is None: t = int(time.time())
    for w in range(-window, window + 1):
        if hmac.compare_digest(totp(secret_b32, t + w * step, step), str(code).strip()):
            return True
    return False

# ---------- 2. 设备指纹 ----------
def device_fingerprint(extra: str = "", rounds: int = 100_000) -> str:
    """多源本地特征 → PBKDF2 慢哈希指纹（hex）。
    特征源: platform/node/machine/processor/user/PATH 长度等——只取结构性特征, 不取敏感值明文。
    注意: 同一台机器同一用户结果稳定; 跨机不可比; 指纹非密钥, 不可用于授权唯一依据(conf=estimated)。"""
    feats = {
        "system": platform.system(), "release": platform.release(),
        "machine": platform.machine(), "processor": platform.processor(),
        "node": platform.node(), "user": getpass.getuser(),
        "py": platform.python_version(), "pathlen": len(os.environ.get("PATH", "")),
    }
    raw = json.dumps(feats, sort_keys=True) + "|" + extra
    salt = hashlib.sha256(("k3-fp:" + raw[:64]).encode()).digest()[:16]
    return hashlib.pbkdf2_hmac("sha256", raw.encode(), salt, rounds).hex()

# ---------- 3. 慢哈希口令 ----------
def hash_password(password: str, scheme: str = "pbkdf2", rounds: int = 600_000) -> str:
    """返回 'scheme$rounds$salt_hex$hash_hex' 自描述串。scheme ∈ {pbkdf2, scrypt}。"""
    salt = secrets.token_bytes(16)
    if scheme == "pbkdf2":
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
        return f"pbkdf2${rounds}${salt.hex()}${h.hex()}"
    if scheme == "scrypt":
        h = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return f"scrypt$16384,8,1${salt.hex()}${h.hex()}"
    raise ValueError("scheme 须为 pbkdf2|scrypt")

def verify_password(password: str, stored: str) -> bool:
    """自描述串校验，恒定时间比较。"""
    try:
        scheme, param, salt_hex, h_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        if scheme == "pbkdf2":
            h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(param))
        elif scheme == "scrypt":
            n, r, p = (int(x) for x in param.split(","))
            h = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p)
        else:
            return False
        return hmac.compare_digest(h.hex(), h_hex)
    except Exception:
        return False
