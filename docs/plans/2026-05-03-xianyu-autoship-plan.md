# 闲鱼自动发货系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过闲管家开放平台 API，批量将上万个百度网盘资源发布为闲鱼卡密商品，买家付款后平台自动发货链接，无需人工干预。

**Architecture:** 两个独立脚本：`publish.py` 读取 CSV 批量创建卡密商品；`monitor.py` 轮询订单接口记录发货日志。自动发货由闲管家平台在卡密商品层面处理，脚本无需主动推送消息。签名采用两步 MD5：`MD5(appKey + "," + MD5(body) + "," + timestamp + "," + appSecret)`。

**Tech Stack:** Python 3.10+, requests, csv, json, hashlib, 闲管家开放平台 API (https://open.goofish.pro)

---

## 文件结构

```
xianyu-autoship/
├── config.json          # AppKey/AppSecret/authorize_id（用户填写，不提交 git）
├── products.csv         # 商品数据（用户填写）
├── published.json       # 已发布记录（脚本自动维护）
├── orders.json          # 已处理订单记录（脚本自动维护）
├── errors.log           # 错误日志
├── src/
│   ├── sign.py          # 签名工具
│   ├── api_client.py    # HTTP 请求封装
│   ├── publish.py       # 批量发布商品
│   └── monitor.py       # 订单监听
└── tests/
    ├── test_sign.py
    └── test_api_client.py
```

---

## Task 1: 项目初始化 + 配置文件

**Files:**
- Create: `config.json`
- Create: `products.csv`
- Create: `published.json`
- Create: `orders.json`
- Create: `.gitignore`

- [ ] **Step 1: 创建 config.json 模板**

```json
{
  "app_key": 1566422639953477,
  "app_secret": "YOUR_APP_SECRET_HERE",
  "authorize_id": 0,
  "base_url": "https://open.goofish.pro"
}
```

保存到 `config.json`。`authorize_id` 填入从闲管家后台获取的店铺授权 ID（调用 `/api/open/user/authorize/list` 查询）。

- [ ] **Step 2: 创建 products.csv 模板**

```csv
title,description,price,category_id,link,extract_code
百度网盘资源-示例,高清资源合集，永久有效,9.9,e11455b218c06e7ae10cfa39bf43dc0f,https://pan.baidu.com/s/xxxxx,abcd
```

字段说明：
- `title`: 商品标题（最长60字）
- `description`: 商品描述
- `price`: 售价（元，脚本自动转换为分）
- `category_id`: 类目ID（从 `/api/open/product/category/list` 查询）
- `link`: 百度网盘分享链接
- `extract_code`: 提取码（无提取码填空）

- [ ] **Step 3: 创建空的状态文件**

```bash
echo "{}" > published.json
echo "{}" > orders.json
```

- [ ] **Step 4: 创建 .gitignore**

```
config.json
*.log
__pycache__/
*.pyc
```

- [ ] **Step 5: 提交**

```bash
git add config.json products.csv published.json orders.json .gitignore
git commit -m "chore: init project structure and config templates"
```

---

## Task 2: 签名工具

**Files:**
- Create: `src/sign.py`
- Create: `tests/test_sign.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_sign.py`：

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sign import gen_sign

def test_sign_deterministic():
    body = '{"title":"test"}'
    timestamp = 1700000000
    app_key = 203413189371893
    app_secret = "o9wl81dncmvby3ijpq7eur456zhgtaxs"
    result = gen_sign(body, timestamp, app_key, app_secret)
    # 相同输入必须产生相同签名
    assert result == gen_sign(body, timestamp, app_key, app_secret)
    assert len(result) == 32  # MD5 hex 长度

def test_sign_different_body():
    timestamp = 1700000000
    app_key = 203413189371893
    app_secret = "o9wl81dncmvby3ijpq7eur456zhgtaxs"
    s1 = gen_sign('{"a":1}', timestamp, app_key, app_secret)
    s2 = gen_sign('{"a":2}', timestamp, app_key, app_secret)
    assert s1 != s2
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd C:/Users/clown/xianyu-autoship
python -m pytest tests/test_sign.py -v
```

预期：`ImportError: No module named 'sign'`

- [ ] **Step 3: 实现 sign.py**

创建 `src/sign.py`：

```python
import hashlib

def gen_sign(body_json: str, timestamp: int, app_key: int, app_secret: str) -> str:
    body_md5 = hashlib.md5(body_json.encode("utf-8")).hexdigest()
    raw = f"{app_key},{body_md5},{timestamp},{app_secret}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_sign.py -v
```

预期：2 passed

- [ ] **Step 5: 提交**

```bash
git add src/sign.py tests/test_sign.py
git commit -m "feat: add request signing utility"
```

---

## Task 3: API 客户端

**Files:**
- Create: `src/api_client.py`
- Create: `tests/test_api_client.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_api_client.py`：

```python
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import patch, MagicMock
from api_client import ApiClient

def test_build_url_contains_required_params():
    client = ApiClient(app_key=12345, app_secret="secret", base_url="https://open.goofish.pro")
    url = client._build_url("/api/open/test", '{"x":1}', timestamp=1700000000)
    assert "appid=12345" in url
    assert "timestamp=1700000000" in url
    assert "sign=" in url

def test_post_returns_data_on_success():
    client = ApiClient(app_key=12345, app_secret="secret", base_url="https://open.goofish.pro")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"code": 0, "msg": "OK", "data": {"product_id": 999}}
    mock_resp.raise_for_status = MagicMock()
    with patch("api_client.requests.post", return_value=mock_resp) as mock_post:
        result = client.post("/api/open/test", {"x": 1})
    assert result == {"product_id": 999}

def test_post_raises_on_api_error():
    client = ApiClient(app_key=12345, app_secret="secret", base_url="https://open.goofish.pro")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"code": 100004, "msg": "param error", "data": None}
    mock_resp.raise_for_status = MagicMock()
    with patch("api_client.requests.post", return_value=mock_resp):
        try:
            client.post("/api/open/test", {"x": 1})
            assert False, "should have raised"
        except Exception as e:
            assert "100004" in str(e)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_api_client.py -v
```

预期：`ImportError: No module named 'api_client'`

- [ ] **Step 3: 实现 api_client.py**

创建 `src/api_client.py`：

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_api_client.py -v
```

预期：3 passed

- [ ] **Step 5: 提交**

```bash
git add src/api_client.py tests/test_api_client.py
git commit -m "feat: add API client with signing"
```

---

## Task 4: 批量发布脚本

**Files:**
- Create: `src/publish.py`

- [ ] **Step 1: 安装依赖**

```bash
pip install requests
```

- [ ] **Step 2: 实现 publish.py**

创建 `src/publish.py`：

```python
import csv, json, os, sys, time

sys.path.insert(0, os.path.dirname(__file__))
from api_client import ApiClient

PUBLISHED_FILE = "published.json"
ERRORS_FILE = "errors.log"
INTERVAL_SECONDS = 1.5  # 每条发布间隔，避免触发 QPS 限制


def load_published() -> dict:
    if os.path.exists(PUBLISHED_FILE):
        with open(PUBLISHED_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_published(data: dict):
    with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_error(msg: str):
    with open(ERRORS_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(f"[ERROR] {msg}")


def build_card_content(link: str, extract_code: str) -> str:
    if extract_code:
        return f"百度网盘链接：{link}\n提取码：{extract_code}"
    return f"百度网盘链接：{link}"


def publish_product(client: ApiClient, cfg: dict, row: dict) -> str:
    """发布单个卡密商品，返回 product_id 字符串，失败抛出异常"""
    card_content = build_card_content(row["link"], row.get("extract_code", ""))
    price_fen = int(float(row["price"]) * 100)

    payload = {
        "item_biz_type": 7,          # 卡密订单类型
        "sp_biz_type": 1,
        "channel_cat_id": row["category_id"],
        "price": price_fen,
        "express_fee": 0,            # 虚拟商品无运费
        "stock": 9999,
        "card_content": card_content,
        "publish_shop": [
            {
                "images": [],
                "user_name": cfg["user_name"],
                "province": cfg.get("province", 110000),
                "city": cfg.get("city", 110100),
                "district": cfg.get("district", 110101),
                "title": row["title"],
                "content": row["description"],
            }
        ],
    }
    data = client.post("/api/open/product/create", payload)
    product_id = str(data["product_id"])

    # 上架
    client.post("/api/open/product/publish", {
        "product_id": int(product_id),
        "user_name": [cfg["user_name"]],
    })
    return product_id


def main():
    with open("config.json", encoding="utf-8") as f:
        cfg = json.load(f)

    client = ApiClient.from_config()
    published = load_published()

    with open("products.csv", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    success = 0
    skip = 0

    for i, row in enumerate(rows, 1):
        key = row["title"].strip()
        if key in published:
            skip += 1
            print(f"[{i}/{total}] 跳过（已发布）: {key}")
            continue

        try:
            product_id = publish_product(client, cfg, row)
            published[key] = {
                "product_id": product_id,
                "link": row["link"],
                "extract_code": row.get("extract_code", ""),
            }
            save_published(published)
            success += 1
            print(f"[{i}/{total}] 发布成功: {key} → product_id={product_id}")
        except Exception as e:
            log_error(f"[{i}/{total}] 发布失败: {key} | {e}")

        time.sleep(INTERVAL_SECONDS)

    print(f"\n完成：成功 {success}，跳过 {skip}，失败 {total - success - skip}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 提交**

```bash
git add src/publish.py
git commit -m "feat: add batch product publisher"
```

---

## Task 5: 订单监听脚本

**Files:**
- Create: `src/monitor.py`

- [ ] **Step 1: 实现 monitor.py**

创建 `src/monitor.py`：

```python
import json, os, sys, time

sys.path.insert(0, os.path.dirname(__file__))
from api_client import ApiClient

ORDERS_FILE = "orders.json"
POLL_INTERVAL = 30  # 秒


def load_orders() -> dict:
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_orders(data: dict):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_paid_orders(client: ApiClient, cfg: dict, last_check_time: int) -> list:
    data = client.post("/api/open/order/list", {
        "authorize_id": cfg["authorize_id"],
        "order_status": 11,          # 11 = 已付款待发货
        "page": 1,
        "page_size": 50,
        "start_time": last_check_time,
    })
    return data.get("list", [])


def main():
    with open("config.json", encoding="utf-8") as f:
        cfg = json.load(f)

    client = ApiClient.from_config()
    orders = load_orders()
    last_check = int(time.time()) - 60  # 启动时往前查1分钟

    print(f"开始监听订单，每 {POLL_INTERVAL} 秒轮询一次...")

    while True:
        try:
            paid_orders = fetch_paid_orders(client, cfg, last_check)
            now = int(time.time())

            for order in paid_orders:
                order_no = str(order["order_no"])
                if order_no in orders:
                    continue

                orders[order_no] = {
                    "product_id": order.get("product_id"),
                    "buyer": order.get("user_name"),
                    "detected_at": now,
                    "order_type": order.get("order_type"),
                }
                save_orders(orders)

                # 卡密商品（order_type=7）由平台自动发货，此处仅记录日志
                print(f"[新订单] {order_no} | 买家: {order.get('user_name')} "
                      f"| 商品: {order.get('product_id')} "
                      f"| 类型: {order.get('order_type')} → 平台自动发货")

            last_check = now
        except KeyboardInterrupt:
            print("\n停止监听")
            break
        except Exception as e:
            print(f"[ERROR] 轮询失败: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
git add src/monitor.py
git commit -m "feat: add order monitor"
```

---

## Task 6: 查询授权店铺工具（一次性）

**Files:**
- Create: `src/list_shops.py`

- [ ] **Step 1: 实现 list_shops.py**

创建 `src/list_shops.py`，用于查询 authorize_id 并填入 config.json：

```python
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from api_client import ApiClient

def main():
    client = ApiClient.from_config()
    data = client.post("/api/open/user/authorize/list", {})
    shops = data.get("list", [])
    if not shops:
        print("未找到授权店铺，请先在闲管家后台完成店铺授权")
        return
    print("授权店铺列表：")
    for s in shops:
        print(f"  authorize_id={s['authorize_id']}  nick={s['user_nick']}  "
              f"valid={s['is_valid']}  expires={s['authorize_expires']}")
    print("\n将 authorize_id 填入 config.json 的 authorize_id 字段")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
git add src/list_shops.py
git commit -m "feat: add shop listing utility"
```

---

## Task 7: 使用说明

- [ ] **Step 1: 首次使用流程**

```bash
# 1. 填写 config.json（app_key, app_secret, user_name, province/city/district）
# 2. 查询授权店铺，获取 authorize_id
python src/list_shops.py

# 3. 将 authorize_id 填入 config.json

# 4. 准备 products.csv（参考模板格式）

# 5. 批量发布商品（支持断点续传，中断后重新运行会跳过已发布的）
python src/publish.py

# 6. 启动订单监听（可选，用于记录日志）
python src/monitor.py
```

- [ ] **Step 2: config.json 完整字段说明**

```json
{
  "app_key": 1566422639953477,
  "app_secret": "lOHmwpIo4d3yIISe59O7mY5l8wNSma69",
  "authorize_id": 0,
  "user_name": "你的闲鱼会员名",
  "province": 110000,
  "city": 110100,
  "district": 110101,
  "base_url": "https://open.goofish.pro"
}
```

- [ ] **Step 3: 提交**

```bash
git add .
git commit -m "docs: add usage instructions in plan"
```

---

## 注意事项

1. **应用待上线**：当前 AppKey 状态为"待上线"，需要先在闲管家后台提交审核通过后，API 才能正常调用生产环境。
2. **卡密商品参数**：`item_biz_type=7` 和 `card_content` 字段需根据实际 API 文档确认，如果参数不对，先调用 `/api/open/product/category/list` 查询正确的类目和商品类型。
3. **自动发货机制**：卡密商品由闲管家平台在买家付款后自动发送 `card_content` 内容，脚本无需主动推送消息。
4. **QPS 限制**：发布间隔设为 1.5 秒，如遇频率限制错误可适当增大 `INTERVAL_SECONDS`。
