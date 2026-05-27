# ⚡ 5 分钟快速开始指南

## 步骤 1：安装依赖（1 分钟）

```bash
# 克隆或下载项目
cd benchmark

# 安装 Python 依赖
pip install -r requirements.txt
```

## 步骤 2：启动中间件（2 分钟）

### 使用 Docker Compose（推荐）
```bash
# 一键启动所有中间件
docker-compose up -d

# 验证
docker-compose ps
```

### 或手动启动
```bash
# 终端 1: Redis
redis-server

# 终端 2: MySQL
mysql.server start

# 终端 3: MongoDB
mongod

# 终端 4: RabbitMQ
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

## 步骤 3：运行压测（2 分钟）

### 选项 A：命令行模式
```bash
python benchmark_tool.py
```

**输出:**
```
✓ Redis 连接成功
✓ MySQL 连接成功
✓ MongoDB 连接成功
✓ RabbitMQ 连接成功

================================================================================
                        压测报告
================================================================================

【Redis】
  总操作数: 100
  成功率: 100.00%
  平均延迟: 3.45 ms
  P95 延迟: 5.67 ms
  P99 延迟: 7.89 ms
  吞吐量: 29.04 ops/sec

【MySQL】
  总操作数: 100
  成功率: 100.00%
  平均延迟: 12.34 ms
  P95 延迟: 18.90 ms
  P99 延迟: 25.67 ms
  吞吐量: 8.12 ops/sec

【MongoDB】
  总操作数: 100
  成功率: 99.00%
  平均延迟: 15.67 ms
  P95 延迟: 32.45 ms
  P99 延迟: 56.78 ms
  吞吐量: 6.45 ops/sec

【RabbitMQ】
  总操作数: 100
  成功率: 100.00%
  平均延迟: 8.90 ms
  P95 延迟: 14.23 ms
  P99 延迟: 19.45 ms
  吞吐量: 11.24 ops/sec

✓ 报告已导出: benchmark_results.json
```

### 选项 B：Web 仪表板模式
```bash
# 启动 Flask 服务
python app.py

# 打开浏览器
# http://localhost:5000
```

---

## 📊 理解结果

| 中间件 | 平均延迟 | 吞吐量 | 特点 |
|--------|---------|-------|------|
| **Redis** | ~3ms | 29 ops/sec | 最快，内存数据库 |
| **MySQL** | ~12ms | 8 ops/sec | 较慢，磁盘 I/O |
| **MongoDB** | ~15ms | 6 ops/sec | 最慢，文档存储 |
| **RabbitMQ** | ~8ms | 11 ops/sec | 消息队列，中等速度 |

---

## 🎨 自定义压测

### 增加并发数
```python
# 修改 benchmark_tool.py
suite = BenchmarkSuite(num_workers=100)  # 从 20 改为 100
```

### 增加操作数
```python
suite.run_benchmark(operations_per_client=1000)  # 从 100 改为 1000
```

### 修改连接信息
```python
configs = {
    "redis": {
        "host": "192.168.1.100",  # 改为你的 IP
        "port": 6379
    },
    ...
}
```

---

## 🐛 常见问题

**Q: 连接被拒绝？**
A: 检查中间件是否启动：`redis-cli ping`

**Q: Web 仪表板无法访问？**
A: 确保 Flask 后端运行：`python app.py`

**Q: 内存不足？**
A: 减少 `num_workers` 或 `operations_per_client`

---

## 📈 下一步

1. 修改配置进行定制压测
2. 对比不同配置的性能差异
3. 监控系统资源使用情况
4. 生成压测报告分享给团队

---

**祝你压测顺利！** 🚀
