import csv, json, os, sys, time

sys.path.insert(0, os.path.dirname(__file__))
from api_client import ApiClient

PUBLISHED_FILE = "published.json"
ERRORS_FILE = "errors.log"
INTERVAL_SECONDS = 1.5


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
    card_content = build_card_content(row["link"], row.get("extract_code", ""))
    price_fen = int(float(row["price"]) * 100)

    payload = {
        "item_biz_type": 7,
        "sp_biz_type": 1,
        "channel_cat_id": row["category_id"],
        "price": price_fen,
        "express_fee": 0,
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
