"""
闲管家虚拟货源接口网关服务
响应闲管家的验证请求和回调请求
"""
import hashlib
import json
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
app.url_map.strict_slashes = False

APP_KEY = 1566744781702981
APP_SECRET = "Hwth2LiZ4eQBU7PHvd5B50CeWrkwdLFQ"

# 商品列表（卡密类型，每个商品对应一个网盘链接+提取码）
PRODUCTS = [
    {
        "goods_no": "goods_001",
        "goods_name": "2023 Q4 CPC数据-亚马逊&沃尔玛全球电商行业基准数据-22页",
        "goods_type": 2,  # 2=卡密
        "price": 100,     # 单位：分
        "stock": 9999,
        "link": "https://pan.baidu.com/s/163HWrLluwcjoXvRn7NbM-g",
        "code": "rlwe",
    },
    {
        "goods_no": "goods_002",
        "goods_name": "2023-2024抖音电商知识产权保护观察报告-巨量算数-25页",
        "goods_type": 2,
        "price": 100,
        "stock": 9999,
        "link": "https://pan.baidu.com/s/1o3Y3JLVmzqg8Pz3Lrx6YDw",
        "code": "0faf",
    },
    {
        "goods_no": "goods_003",
        "goods_name": "2023-2024快手电商营销全景洞察报告-飞瓜数据-52页",
        "goods_type": 2,
        "price": 100,
        "stock": 9999,
        "link": "https://pan.baidu.com/s/1jFZWbuf_beWy70qpwH198A",
        "code": "to0d",
    },
    {
        "goods_no": "goods_004",
        "goods_name": "2023TikTok全球社群电商趋势报告-TikTok for Business-18页",
        "goods_type": 2,
        "price": 100,
        "stock": 9999,
        "link": "https://pan.baidu.com/s/1-u166a4P87002iiJxMUQxA",
        "code": "k38c",
    },
    {
        "goods_no": "goods_005",
        "goods_name": "2023抖音电商视频带货爆单指南-蝉妈妈-202312-32页",
        "goods_type": 2,
        "price": 100,
        "stock": 9999,
        "link": "https://pan.baidu.com/s/1Nc2PVmEMhJWXmpNMrAZOXQ",
        "code": "v76z",
    },
]

# 用 goods_no 做索引方便查找
PRODUCTS_MAP = {p["goods_no"]: p for p in PRODUCTS}


def verify_sign(mch_id, timestamp, sign, body_str="{}"):
    """验证闲管家签名"""
    body_md5 = hashlib.md5(body_str.encode("utf-8")).hexdigest()
    sign_string = f"{mch_id},{body_md5},{timestamp},{APP_SECRET}"
    expected_sign = hashlib.md5(sign_string.encode("utf-8")).hexdigest()
    return expected_sign == sign


@app.route("/goofish/open/info", methods=["GET", "POST"])
def app_info():
    """查询平台信息 - 闲管家验证接口（无请求参数）"""
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[app_info] method={request.method} args={dict(request.args)} body={body_str}")
    return jsonify({"code": 0, "msg": "OK", "data": {"app_id": APP_KEY}})


@app.route("/goofish/user/info", methods=["GET", "POST"])
def user_info():
    """查询商户信息"""
    mch_id = request.args.get("mch_id", "")
    sign = request.args.get("sign", "")
    timestamp = request.args.get("timestamp", "")
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[user_info] mch_id={mch_id} timestamp={timestamp} sign={sign}")
    return jsonify({"code": 0, "msg": "OK", "data": {"balance": 9999999}})


@app.route("/goofish/open/goods/list", methods=["POST"])
def goods_list():
    """查询商品列表"""
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[goods_list] body={body_str}")
    try:
        body = json.loads(body_str)
    except Exception:
        body = {}

    page_no = int(body.get("page_no", 1))
    page_size = int(body.get("page_size", 20))
    start = (page_no - 1) * page_size
    end = start + page_size
    page_items = PRODUCTS[start:end]

    items = []
    for p in page_items:
        items.append({
            "goods_no": p["goods_no"],
            "goods_name": p["goods_name"],
            "goods_type": p["goods_type"],
            "price": p["price"],
            "stock": p["stock"],
            "status": 1,  # 1=上架
        })

    return jsonify({
        "code": 0,
        "msg": "OK",
        "data": {
            "total": len(PRODUCTS),
            "page_no": page_no,
            "page_size": page_size,
            "list": items,
        }
    })


@app.route("/goofish/open/goods/detail", methods=["POST"])
def goods_detail():
    """查询商品详情"""
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[goods_detail] body={body_str}")
    try:
        body = json.loads(body_str)
    except Exception:
        body = {}

    goods_no = body.get("goods_no", "")
    p = PRODUCTS_MAP.get(goods_no)
    if not p:
        return jsonify({"code": 1100, "msg": "商品不存在"})

    return jsonify({
        "code": 0,
        "msg": "OK",
        "data": {
            "goods_no": p["goods_no"],
            "goods_name": p["goods_name"],
            "goods_type": p["goods_type"],
            "price": p["price"],
            "stock": p["stock"],
            "status": 1,
        }
    })


@app.route("/goofish/open/order/card", methods=["POST"])
def order_card():
    """创建卡密订单 - 买家下单时调用，返回网盘链接+提取码"""
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[order_card] body={body_str}")
    try:
        body = json.loads(body_str)
    except Exception:
        body = {}

    goods_no = body.get("goods_no", "")
    order_no = body.get("order_no", "")  # 闲管家订单号
    num = int(body.get("num", 1))

    p = PRODUCTS_MAP.get(goods_no)
    if not p:
        return jsonify({"code": 1100, "msg": "商品不存在"})

    # 每个订单返回同一个网盘链接（网盘资料固定链接）
    cards = []
    for _ in range(num):
        cards.append({
            "card_no": p["link"],
            "card_pwd": p["code"],
        })

    print(f"[order_card] order_no={order_no} goods_no={goods_no} cards={cards}")
    return jsonify({
        "code": 0,
        "msg": "OK",
        "data": {
            "order_no": order_no,
            "cards": cards,
        }
    })


@app.route("/goofish/open/order/notify", methods=["POST"])
def order_notify():
    """订单回调通知"""
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[order_notify] body={body_str}")
    return jsonify({"code": 0, "msg": "OK"})


@app.route("/goofish/open/product/notify", methods=["POST"])
def product_notify():
    """商品回调通知"""
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[product_notify] body={body_str}")
    return jsonify({"code": 0, "msg": "OK"})


@app.route("/", methods=["GET", "POST"])
def index():
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[index] path=/ args={dict(request.args)} body={body_str}")
    return jsonify({"code": 0, "msg": "OK"})


@app.route("/<path:subpath>", methods=["GET", "POST"])
def catch_all(subpath):
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[catch_all] path=/{subpath} args={dict(request.args)} body={body_str}")
    return jsonify({"code": 0, "msg": "OK"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
