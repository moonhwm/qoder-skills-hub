import re, json, sys, subprocess

def extract(url):
    h = subprocess.run(["curl","-s","-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36","-H","Accept: text/html",url],capture_output=True,text=True).stdout
    m = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', h, re.S)
    if not m: return None
    d = json.loads(m.group(1))
    convs = d["props"]["pageProps"]["fullChatShareData"]["chat"]["convs"]
    turns = []
    for c in convs:
        for sp in c.get("speechesV2", []):
            role = sp.get("role") or sp.get("type") or "?"
            texts = []
            for ct in sp.get("content", []):
                if isinstance(ct, dict):
                    for cc in (ct.get("contents") or []):
                        if isinstance(cc, dict) and isinstance(cc.get("text"), str): texts.append(cc["text"])
                    if isinstance(ct.get("text"), str): texts.append(ct["text"])
                elif isinstance(ct, str): texts.append(ct)
            turns.append({"role": role, "text": "\n".join(texts)})
    return turns

if __name__ == "__main__":
    turns = extract(sys.argv[1])
    if turns is None: print("EXTRACT_FAIL"); sys.exit(1)
    print(f"轮次数: {len(turns)}")
    for i,t in enumerate(turns):
        print(f"--- turn{i} role={t['role']} {len(t['text'])}字: {t['text'][:80].replace(chr(10),' ')}")
