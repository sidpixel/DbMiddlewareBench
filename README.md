# 中间件压测工具 - 完整使用指南

## 📋 目录结构

```
benchmark/
├── benchmark_tool.py      # 核心压测工具
├── app.py                 # Flask 后端服务
├── dashboard.html         # Web 仪表板
├── requirements.txt       # 依赖列表
├── config.yaml           # 配置文件（可选）
└── README.md             # 本文件
```

---

## 🚀 快速开始

### 1️⃣ 安装依赖

#### 基础依赖
```bash
pip install redis mysql-connector-python pymongo pika flask flask-cors
```

#### 或使用 requirements.txt
```bash
# 创建 requirements.txt
cat > requirements.txt << EOF
redis==5.0.0
mysql-connector-python==8.0.33
pymongo==4.5.0
pika==1.3.1
flask==2.3.0
flask-cors==4.0.0
EOF

pip install -r requirements.txt
```

### 2️⃣ 配置中间件

#### Redis
```bash
# 启动 Redis（Docker）
docker run -d -p 6379:6379 redis:latest

# 或本地启动
redis-server
```

#### MySQL
```bash
# 启动 MySQL（Docker）
docker run -d -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=test \
  mysql:8.0

# 或本地启动
mysql -u root -p
```

#### MongoDB
```bash
# 启动 MongoDB（Docker）
docker run -d -p 27017:27017 mongo:latest

# 或本地启动
mongod
```

#### RabbitMQ
```bash
# 启动 RabbitMQ（Docker）
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Web 管理界面: http://localhost:15672 (guest/guest)
```

### 3️⃣ 运行压测

#### 方式 A：命令行工具
```bash
python benchmark_tool.py
```

输出示例：
```
============================================================
开始压测 | 工作线程: 20 | 单客户端操作数: 100
============================================================

✓ Redis 连接成功
✓ MySQL 连接成功
✓ MongoDB 连接成功
✓ RabbitMQ 连接成功

... 压测进行中 ...

================================================================================
                        压测报告
================================================================================

【Redis】
  总操作数: 100
  成功: 100 | 失败: 0
  成功率: 100.00%
  延迟 (ms):
    - 最小: 1.23
    - 平均: 3.45
    - 中位: 3.20
    - P95:  5.67
    - P99:  7.89
    - 最大: 12.34
  吞吐量: 29.04 ops/sec
  耗时: 3.44s

【MySQL】
  ...

✓ 报告已导出: benchmark_results.json
```

#### 方式 B：Web 仪表板 + Flask 后端
```bash
# 终端 1: 启动 Flask 服务
python app.py

# 终端 2: 打开浏览器
# http://localhost:5000
```

---

## 🔧 配置文件

### 修改压测参数

编辑 `benchmark_tool.py` 的 `main()` 函数：

```python
def main():
    # 创建压测套件
    suite = BenchmarkSuite(num_workers=50)  # 增加工作线程
    
    # 配置各中间件
    configs = {
        "redis": {
            "host": "192.168.1.100",  # 修改 IP
            "port": 6379,
            "db": 0,
            "timeout": 5
        },
        "mysql": {
            "host": "192.168.1.101",
            "port": 3306,
            "user": "root",
            "password": "your_password",  # 修改密码
            "database": "test"
        },
        # ... 其他配置
    }
    
    # 运行压测 (500 次操作/客户端)
    try:
        suite.run_benchmark(operations_per_client=500, timeout=120)
        # ...
    except Exception as e:
        print(f"✗ 压测失败: {e}")
```

### 通过 Flask API 配置

```bash
# 获取默认配置
curl http://localhost:5000/api/config

# 启动自定义压测
curl -X POST http://localhost:5000/api/start \
  -H "Content-Type: application/json" \
  -d '{
    "num_workers": 50,
    "operations_per_client": 500,
    "timeout": 120,
    "services": ["redis", "mysql"],
    "redis_host": "192.168.1.100",
    "mysql_user": "root",
    "mysql_password": "password"
  }'
```

---

## 📊 API 文档

### 获取状态
```bash
GET /api/status
```
响应:
```json
{
  "status": "running",
  "progress": 45,
  "results": {},
  "start_time": "2024-01-15T10:30:00",
  "total_operations": 4000
}
```

### 启动压测
```bash
POST /api/start
Content-Type: application/json

{
  "num_workers": 20,
  "operations_per_client": 100,
  "timeout": 60,
  "services": ["redis", "mysql", "mongodb", "rabbitmq"]
}
```

### 获取结果
```bash
GET /api/results
```
响应:
```json
{
  "status": "completed",
  "results": {
    "Redis": {
      "total_operations": 100,
      "successful_operations": 100,
      "avg_latency_ms": 3.45,
      "p95_latency_ms": 5.67,
      "throughput_ops_per_sec": 29.04,
      "success_rate": 100.0
    },
    "MySQL": { ... },
    "MongoDB": { ... },
    "RabbitMQ": { ... }
  },
  "start_time": "2024-01-15T10:30:00",
  "end_time": "2024-01-15T10:30:45"
}
```

### 停止压测
```bash
POST /api/stop
```

### 健康检查
```bash
GET /api/health
```

---

## 📈 理解结果

### 关键指标说明

| 指标 | 说明 | 参考值 |
|------|------|--------|
| **成功率** | 成功操作数 / 总操作数 | ≥95% 为正常 |
| **平均延迟** | 所有操作的平均响应时间 | Redis <5ms, MySQL <10ms |
| **P95/P99** | 95%/99% 的操作在此时间内完成 | 反映长尾延迟 |
| **吞吐量** | 每秒完成的操作数 | 越高越好 |
| **耗时** | 整个压测的总耗时 | 用于性能对比 |

### 结果解读示例

```
Redis 性能很好:
  - 平均延迟 3.45ms
  - P99 在 7.89ms
  - 成功率 100%
  - 吞吐量 29 ops/sec

MySQL 性能一般:
  - 平均延迟 12.3ms
  - P99 在 45.6ms  ← 长尾延迟明显
  - 成功率 98.5%
  - 吞吐量 8.1 ops/sec

MongoDB 性能较差:
  - 平均延迟 25.6ms
  - P99 在 120.5ms  ← 波动很大
  - 成功率 92%      ← 失败率较高
  - 吞吐量 3.9 ops/sec
```

---

## 🎯 常见使用场景

### 场景 1：基准测试（确定基线）
```bash
# 在空闲时段，用较小的负载做基准测试
python benchmark_tool.py
# 修改: operations_per_client=100, num_workers=10
```

### 场景 2：压力测试（发现极限）
```bash
# 逐步增加负载，找到系统崩溃点
# 第一轮: num_workers=50, operations_per_client=500
# 第二轮: num_workers=100, operations_per_client=1000
# 第三轮: num_workers=200, operations_per_client=2000
```

### 场景 3：长时间运行测试（稳定性）
```bash
# 运行较长时间，观察是否有内存泄漏或性能衰减
# num_workers=20, operations_per_client=10000, timeout=600
```

### 场景 4：对比测试（不同配置）
```bash
# 测试 1: 使用默认配置
python benchmark_tool.py
# 记录 benchmark_results.json

# 修改配置（如增加连接池大小）
# 测试 2: 使用新配置
python benchmark_tool.py
# 记录 benchmark_results_v2.json

# 对比两个 JSON 文件
```

---

## 🐛 故障排除

### 问题 1：无法连接 Redis
```
✗ Redis 连接失败: [Errno 111] Connection refused
```

**解决方案:**
```bash
# 检查 Redis 是否运行
redis-cli ping

# 如果未运行，启动 Redis
redis-server

# 检查配置中的 host/port 是否正确
```

### 问题 2：MySQL 连接超时
```
Error: [Errno 110] Connection timed out
```

**解决方案:**
```bash
# 检查 MySQL 是否运行
mysql -u root -p

# 检查防火墙
sudo ufw allow 3306

# 修改配置，增加超时时间
# app.py 中修改 timeout 参数
```

### 问题 3：压测过程中内存溢出
```
MemoryError: Unable to allocate XX.XX GB for an array
```

**解决方案:**
```bash
# 减少 num_workers
num_workers = 10  # 从 50 改为 10

# 减少 operations_per_client
operations_per_client = 100  # 从 1000 改为 100

# 增加系统 swap 空间
```

### 问题 4：Web 仪表板显示不正常
```
CORS 错误 或 API 调用失败
```

**解决方案:**
```bash
# 确保 Flask 后端在运行
python app.py

# 清空浏览器缓存
# Ctrl+Shift+Delete (Windows/Linux) 或 Cmd+Shift+Delete (Mac)

# 检查 localhost:5000 是否可访问
curl http://localhost:5000/api/health
```

---

## 📦 Docker 一键启动

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    networks:
      - benchmark

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: test
    ports:
      - "3306:3306"
    networks:
      - benchmark

  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    networks:
      - benchmark

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    networks:
      - benchmark

  benchmark:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - redis
      - mysql
      - mongodb
      - rabbitmq
    networks:
      - benchmark
    environment:
      REDIS_HOST: redis
      MYSQL_HOST: mysql
      MONGODB_HOST: mongodb
      RABBITMQ_HOST: rabbitmq

networks:
  benchmark:
    driver: bridge
```

运行:
```bash
docker-compose up -d
# 访问 http://localhost:5000
```

---

## 💡 性能优化建议

### 1. 增加工作线程
```python
suite = BenchmarkSuite(num_workers=100)  # 从 20 增加到 100
```

### 2. 使用连接池
```python
# Redis 示例
self.client = redis.Redis(
    host=...,
    connection_pool=redis.ConnectionPool(...)
)
```

### 3. 批量操作
```python
# 而不是逐个插入，使用批量操作
pipeline = self.client.pipeline()
for i in range(100):
    pipeline.set(f"key_{i}", f"value_{i}")
pipeline.execute()
```

### 4. 调整超时时间
```python
# 根据网络状况调整
socket_timeout=10  # 增加到 10 秒
```

---

## 📚 扩展功能

### 自定义测试操作

编辑 `benchmark_tool.py`:

```python
class CustomClient(BenchmarkClient):
    def test_operation(self) -> OperationResult:
        try:
            start = time.time()
            
            # 自定义测试逻辑
            # 例如: 复杂的多步骤操作
            
            latency = (time.time() - start) * 1000
            return OperationResult(
                status=StatusEnum.SUCCESS.value,
                latency_ms=latency,
                timestamp=time.time()
            )
        except Exception as e:
            return OperationResult(...)

# 在 main() 中注册
suite.register_client(CustomClient("Custom", {}))
```

### 导出为 Prometheus 格式

```python
def export_prometheus_format(results):
    for name, stats in results.items():
        print(f"benchmark_avg_latency_ms{{service=\"{name}\"}} {stats.avg_latency_ms}")
        print(f"benchmark_throughput{{service=\"{name}\"}} {stats.throughput_ops_per_sec}")
        print(f"benchmark_success_rate{{service=\"{name}\"}} {stats.success_rate}")
```

---

## 📞 支持和反馈

如有问题，请检查:
1. 所有中间件是否正确安装和运行
2. 网络连接是否正常
3. 防火墙是否阻止端口访问
4. 系统资源是否充足

---

## 📄 许可证

GPL-3.0-or-later

---

**祝你压测顺利！** 🚀
