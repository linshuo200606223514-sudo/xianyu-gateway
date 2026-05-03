import json, time, requests
from sign import gen_sign

class ApiClient:
    def __init__(self, app_key: int, app_secret: str, base_url: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url

    def _build_url(self, path: str, body_json: str, timestamp: int) -> str:
        sign = gen_sign(body_json, timestamp, self.app_key, self.app_secret)
        return f"{self.base_url}{path}?appid={self.app_key}&timestamp={timestamp}&sign={sign}"

    def post(self, path: str, data: dict) -> dict:
        body = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        timestamp = int(time.time())
        url = self._build_url(path, body, timestamp)
        resp = requests.post(url, data=body.encode("utf-8"),
                             headers={"Content-Type": "application/json"}, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API error {result.get('code')}: {result.get('msg')}")
        return result.get("data", {})

    @classmethod
    def from_config(cls, config_path: str = "config.json") -> "ApiClient":
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cls(
            app_key=cfg["app_key"],
            app_secret=cfg["app_secret"],
            base_url=cfg.get("base_url", "https://open.goofish.pro"),
        )
