import json, os, sys, time

sys.path.insert(0, os.path.dirname(__file__))
from api_client import ApiClient

ORDERS_FILE = "orders.json"
POLL_INTERVAL = 30


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
        "order_status": 11,
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
    last_check = int(time.time()) - 60

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
