import hashlib

def gen_sign(body_json: str, timestamp: int, app_key: int, app_secret: str) -> str:
    body_md5 = hashlib.md5(body_json.encode("utf-8")).hexdigest()
    raw = f"{app_key},{body_md5},{timestamp},{app_secret}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()
