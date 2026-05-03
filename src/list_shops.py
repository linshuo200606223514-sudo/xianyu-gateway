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
