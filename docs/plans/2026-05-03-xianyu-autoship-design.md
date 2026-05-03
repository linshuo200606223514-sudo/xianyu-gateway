# 闲鱼自动发货系统设计文档

**日期**: 2026-05-03  
**状态**: 已确认

## 背景

用户持有闲管家开放平台 AppKey（虚拟货源类型，自研系统模式），需要：
1. 批量将上万个商品发布到闲鱼（每个商品对应一个百度网盘链接）
2. 买家付款后自动通过 IM 发送对应的网盘链接，无需人工干预

## 方案选择

采用**闲管家官方 API 方案**（方案A），理由：
- 用户已有 AppKey/AppSecret
- 合规路径，不易封号
- 官方支持虚拟商品自动发货场景

## 系统架构

```
products.csv（商品数据）
       ↓
  publish.py（批量发布）
       ↓
  闲鱼平台上架
       ↓
  monitor.py（轮询订单，每30秒）
       ↓
  新订单付款 → 查找对应网盘链接 → IM 发送给买家
```

## 组件设计

### 1. publish.py — 批量发布脚本

- 读取 `products.csv`，逐行调用闲管家发布商品 API
- 每发布成功一条，写入 `published.json`（商品标题 → 闲鱼商品ID + 网盘链接）
- 支持断点续传：跳过已在 `published.json` 中的商品
- 发布频率限制：每条间隔 1-2 秒，避免触发 QPS 限制

### 2. monitor.py — 订单监听 + 自动发货脚本

- 每 30 秒调用订单查询 API，获取最新付款订单
- 对每个新订单：
  1. 从 `published.json` 查找该商品对应的网盘链接
  2. 调用 IM 发送接口，将链接发给买家
  3. 将订单 ID 写入 `orders.json`，标记已处理
- 跳过 `orders.json` 中已处理的订单，防止重复发货

### 3. 数据文件

| 文件 | 格式 | 维护方 |
|------|------|--------|
| `products.csv` | 标题,描述,价格,分类,网盘链接,提取码 | 用户手动维护 |
| `published.json` | `{商品标题: {item_id, link, code}}` | 脚本自动写入 |
| `orders.json` | `{订单ID: {item_id, buyer, sent_at}}` | 脚本自动写入 |
| `config.json` | AppKey, AppSecret, access_token 等 | 用户初始化时填写 |

### 4. auth.py — OAuth 授权工具

- 一次性运行，引导用户完成闲鱼账号 OAuth 授权
- 获取并保存 access_token 到 `config.json`
- 提示 token 过期时间，到期前提醒重新授权

## 错误处理

- API 调用失败：打印错误，跳过当前条目，继续处理下一条
- 网盘链接找不到：记录到 `errors.log`，不发送，人工处理
- token 过期：monitor.py 检测到 401 时停止并提示重新运行 auth.py

## 目录结构

```
xianyu-autoship/
├── auth.py          # OAuth 授权（一次性）
├── publish.py       # 批量发布商品
├── monitor.py       # 订单监听 + 自动发货
├── config.json      # 配置（AppKey/Secret/token）
├── products.csv     # 商品数据（用户填写）
├── published.json   # 已发布记录（自动生成）
├── orders.json      # 已处理订单（自动生成）
├── errors.log       # 错误日志（自动生成）
└── docs/
    └── plans/
        └── 2026-05-03-xianyu-autoship-design.md
```

## 前置条件

- 闲管家应用审核通过（当前状态：待上线）
- 完成 OAuth 授权获取 access_token
- `products.csv` 准备好商品数据
