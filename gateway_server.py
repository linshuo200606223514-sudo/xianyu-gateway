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


def verify_sign(mch_id, timestamp, sign, body_str="{}"):
    """验证闲管家签名"""
    body_md5 = hashlib.md5(body_str.encode("utf-8")).hexdigest()
    sign_string = f"{mch_id},{body_md5},{timestamp},{APP_SECRET}"
    expected_sign = hashlib.md5(sign_string.encode("utf-8")).hexdigest()
    return expected_sign == sign


@app.route("/goofish/open/info", methods=["GET", "POST"])
def app_info():
    """获取虚拟货源应用信息 - 闲管家验证接口"""
    mch_id = request.args.get("mch_id", "")
    sign = request.args.get("sign", "")
    timestamp = request.args.get("timestamp", "")

    body_str = request.get_data(as_text=True) or "{}"

    return jsonify({
        "code": 0,
        "msg": "success",
        "data": {
            "app_key": str(APP_KEY),
            "app_name": "superpower",
            "status": 1
        }
    })


@app.route("/goofish/open/order/notify", methods=["POST"])
def order_notify():
    """订单回调通知"""
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[order_notify] body={body_str}")
    return jsonify({"code": 0, "msg": "success"})


@app.route("/goofish/open/product/notify", methods=["POST"])
def product_notify():
    """商品回调通知"""
    body_str = request.get_data(as_text=True) or "{}"
    print(f"[product_notify] body={body_str}")
    return jsonify({"code": 0, "msg": "success"})


@app.route("/", methods=["GET", "POST"])
def index():
    """根路径，接收所有未匹配的请求"""
    body_str = request.get_data(as_text=True) or "{}"
    path = request.path
    args = dict(request.args)
    print(f"[index] path={path} args={args} body={body_str}")
    return jsonify({"code": 0, "msg": "success"})


@app.route("/<path:subpath>", methods=["GET", "POST"])
def catch_all(subpath):
    """捕获所有路径"""
    body_str = request.get_data(as_text=True) or "{}"
    args = dict(request.args)
    print(f"[catch_all] path=/{subpath} args={args} body={body_str}")
    return jsonify({"code": 0, "msg": "success"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
