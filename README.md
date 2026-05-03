# 闲鱼自动发货系统

通过闲管家开放平台 API，批量发布百度网盘资源为卡密商品，买家付款后平台自动发货。

## 前置条件

1. 闲管家应用审核通过（当前状态：待上线）
2. 在闲管家后台完成闲鱼账号授权

## 首次使用

### 1. 填写 config.json

```json
{
  "app_key": "你的AppKey",
  "app_secret": "你的AppSecret",
  "authorize_id": 0,
  "user_name": "你的闲鱼会员名",
  "province": 110000,
  "city": 110100,
  "district": 110101,
  "base_url": "https://open.goofish.pro"
}
```

### 2. 查询授权店铺，获取 authorize_id

```bash
python src/list_shops.py
```

将输出的 authorize_id 填入 config.json。

### 3. 准备 products.csv

参考 products.csv 模板，每行一个商品：

| 字段 | 说明 |
|------|------|
| title | 商品标题（最长60字） |
| description | 商品描述 |
| price | 售价（元） |
| category_id | 类目ID（从闲管家后台查询） |
| link | 百度网盘分享链接 |
| extract_code | 提取码（无则留空） |

### 4. 批量发布商品

```bash
python src/publish.py
```

支持断点续传，中断后重新运行会跳过已发布的商品。

### 5. 监听订单（可选）

```bash
python src/monitor.py
```

每30秒轮询一次，记录新订单到 orders.json。卡密商品由平台自动发货，无需脚本干预。

## 注意事项

- 应用待上线时 API 只能访问沙箱环境
- 发布间隔 1.5 秒，如遇频率限制可增大 INTERVAL_SECONDS
- 发布失败记录在 errors.log，可手动处理后重新运行
