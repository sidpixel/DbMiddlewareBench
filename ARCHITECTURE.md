# 中间件压测工具 - 系统架构

## 🏗️ 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     客户端层                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  命令行模式          Web 仪表板模式         API 客户端          │
│  ┌──────────┐       ┌──────────────┐    ┌───────────────┐      │
│  │  CLI     │       │  Dashboard   │    │   curl/SDK    │      │
│  │  Tool    │       │  (HTML+JS)   │    │  (REST API)   │      │
│  └────┬─────┘       └──────┬───────┘    └───────┬───────┘      │
│       │                    │                     │               │
└───────┼────────────────────┼─────────────────────┼───────────────┘
        │                    │                     │
        │ 直接调用           │ HTTP/REST           │ HTTP/REST
        │                    │                     │
┌───────▼────────────────────▼─────────────────────▼───────────────┐
│                     应用层 (Python)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                      Flask Web 框架                             │
│          (app.py - API 端点 + Web 服务)                        │
│                      ↓                                          │
│  ┌──────────────────────────────────────────────────┐           │
│  │        BenchmarkSuite (压测套件管理)             │           │
│  │   ┌─────────────────────────────────────────┐  │           │
│  │   │      并发执行器 (ThreadPoolExecutor)    │  │           │
│  │   │   max_workers = 20-200 个线程          │  │           │
│  │   └─────────────────────────────────────────┘  │           │
│  └──────────────────────────────────────────────────┘           │
│                      ↓                                          │
│  ┌──────────────────────────────────────────────────┐           │
│  │        客户端抽象 (BenchmarkClient)             │           │
│  │   ┌──────┬─────────┬─────────┬──────────┐     │           │
│  │   │Redis │  MySQL  │ MongoDB │ RabbitMQ│     │           │
│  │   └──────┴─────────┴─────────┴──────────┘     │           │
│  │                                              │           │
│  │   每个客户端负责:                             │           │
│  │   - 连接管理                                 │           │
│  │   - 单次操作执行                             │           │
│  │   - 结果收集                                 │           │
│  │   - 统计计算                                 │           │
│  └──────────────────────────────────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
        │         │          │          │
        │         │          │          │
┌───────▼─┴────┬──▼──────┬───▼────┬────▼──────────┐
│              │         │        │               │
▼              ▼         ▼        ▼               ▼
Redis        MySQL    MongoDB  RabbitMQ      系统资源
(6379)       (3306)    (27017)  (5672)       (监控)
```

---

## 🔄 工作流程

### 1. 启动阶段
```
用户启动
    ↓
加载配置
    ↓
创建 BenchmarkSuite 实例
    ↓
为每个中间件创建客户端
    ↓
连接到所有中间件
    ↓
准备就绪 ✓
```

### 2. 压测阶段
```
启动压测
    ↓
创建线程池 (ThreadPoolExecutor)
    ↓
┌─────────────────────────────┐
│ 并发执行测试操作            │
│ ├─ 20-200 个线程同时运行   │
│ ├─ 每个线程执行N次测试     │
│ ├─ 每次测试记录延迟和状态  │
│ └─ 汇总到客户端的结果队列  │
└─────────────────────────────┘
    ↓
所有操作完成
    ↓
收集结果
```

### 3. 计算阶段
```
收集所有操作结果
    ↓
┌─────────────────────────────┐
│ 计算统计数据                │
│ ├─ 最小/最大/平均延迟      │
│ ├─ P50/P95/P99 延迟        │
│ ├─ 成功率 & 吞吐量         │
│ └─ 失败原因分析            │
└─────────────────────────────┘
    ↓
导出结果 (JSON/报告)
    ↓
展示给用户 (CLI/Web/API)
```

---

## 📦 核心组件详解

### BenchmarkClient (基础客户端)

```python
class BenchmarkClient:
    ├─ connect()           # 建立连接
    ├─ disconnect()        # 断开连接
    ├─ test_operation()    # 执行单次测试
    ├─ add_result()        # 线程安全地添加结果
    ├─ calculate_stats()   # 计算统计数据
    └─ clear_results()     # 清空结果
```

### 具体实现 (Redis/MySQL/MongoDB/RabbitMQ)

#### RedisClient
```python
test_operation():
    SET key → GET key → DELETE key → 计算延迟
    
特点:
- 最快 (内存操作)
- 低延迟 (3-5ms)
- 高吞吐量 (30+ ops/sec)
```

#### MySQLClient
```python
test_operation():
    INSERT → SELECT → DELETE → 计算延迟
    
特点:
- 中等速度
- 涉及磁盘 I/O
- 中等延迟 (10-20ms)
```

#### MongoDBClient
```python
test_operation():
    insert_one() → find_one() → delete_one() → 计算延迟
    
特点:
- 文档存储
- 灵活查询
- 相对较慢 (15-30ms)
```

#### RabbitMQClient
```python
test_operation():
    basic_publish() → basic_get() → 计算延迟
    
特点:
- 消息队列
- 异步通信
- 中等延迟 (8-15ms)
```

### BenchmarkSuite (套件管理)

```python
class BenchmarkSuite:
    ├─ register_client()     # 注册客户端
    ├─ run_benchmark()       # 执行压测
    │  ├─ 连接所有客户端
    │  ├─ 创建线程池
    │  ├─ 分配任务
    │  ├─ 收集结果
    │  └─ 计算统计
    ├─ print_report()        # 打印报告
    └─ export_json()         # 导出 JSON
```

---

## 🔌 API 接口设计

### REST API 端点

```
GET    /api/status          # 获取当前压测状态
GET    /api/results         # 获取压测结果
GET    /api/config          # 获取默认配置
GET    /api/health          # 健康检查

POST   /api/start           # 启动压测
POST   /api/stop            # 停止压测
```

### 数据流向

```
客户端 → HTTP Request → Flask 应用 → 处理 → BenchmarkSuite → 执行
        ← HTTP Response ← 序列化 ← 统计数据 ← 结果收集
```

---

## 📊 数据结构

### OperationResult (单次操作结果)
```
┌──────────────────────┐
│ OperationResult      │
├──────────────────────┤
│ status: str          │ → "success" / "failure"
│ latency_ms: float    │ → 延迟时间 (毫秒)
│ timestamp: float     │ → Unix 时间戳
│ error: str (可选)    │ → 错误信息
└──────────────────────┘
```

### BenchmarkStats (统计结果)
```
┌───────────────────────────────┐
│ BenchmarkStats                │
├───────────────────────────────┤
│ total_operations: int         │ → 总操作数
│ successful_operations: int    │ → 成功数
│ failed_operations: int        │ → 失败数
│ min_latency_ms: float         │ → 最小延迟
│ max_latency_ms: float         │ → 最大延迟
│ avg_latency_ms: float         │ → 平均延迟
│ p50_latency_ms: float         │ → P50 延迟
│ p95_latency_ms: float         │ → P95 延迟
│ p99_latency_ms: float         │ → P99 延迟
│ throughput_ops_per_sec: float │ → 吞吐量
│ duration_seconds: float       │ → 耗时
└───────────────────────────────┘
```

---

## ⚙️ 并发执行模型

### ThreadPoolExecutor 策略

```
┌─────────────────────────────────────────────────┐
│        主线程 (Flask/CLI)                        │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │      ThreadPoolExecutor (num_workers=20)  │ │
│  │                                           │ │
│  │  线程池管理:                              │ │
│  │  ├─ 创建 N 个工作线程                    │ │
│  │  ├─ 任务队列分配                        │ │
│  │  ├─ 动态调度                            │ │
│  │  └─ 异常处理                            │ │
│  │                                           │ │
│  │  ┌──┬──┬──┬──┬──┐                        │ │
│  │  │w1│w2│w3│w4│w5│ ... (20 个线程)      │ │
│  │  └──┴──┴──┴──┴──┘                        │ │
│  │   ↓  ↓  ↓  ↓  ↓                         │ │
│  │  [Redis Client 实例] ×N (线程本地)      │ │
│  │                                           │ │
│  └───────────────────────────────────────────┘ │
│  ↓ Future objects                             │
│  [Result Queue] (线程安全的队列)              │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 时序图

```
主线程              线程1              线程2              线程3
  |                  |                  |                  |
  |-- submit task1 →|                  |                  |
  |                  |-- execute ----→  (记录结果)        |
  |-- submit task2 →|                  |                  |
  |                  |                  |-- execute ----→  (记录结果)
  |-- submit task3 →|                  |                  |
  |                  |-- execute ----→  (记录结果)        |
  |                  |                  |                  |
  |-- wait for all →|[等待完成]         |[等待完成]         |[等待完成]
  |                  |                  |                  |
  |← [收集所有结果] ←|                  |                  |
  |
  |-- calculate stats
  |
  |-- return results
```

---

## 🎯 性能优化策略

### 1. 连接复用
```python
# ✓ 好: 复用连接
client = redis.Redis(...)
for i in range(1000):
    client.ping()

# ✗ 差: 重复创建连接
for i in range(1000):
    client = redis.Redis(...)
    client.ping()
```

### 2. 线程数调优
```python
# CPU 密集型: num_workers = CPU核心数
# I/O 密集型: num_workers = CPU核心数 × 2-4

CPU 核心    推荐线程数
   4           8-16
   8          16-32
  16          32-64
```

### 3. 批量操作
```python
# ✓ 好: 管道模式
pipeline = client.pipeline()
for i in range(100):
    pipeline.set(f"key_{i}", f"value_{i}")
pipeline.execute()

# ✗ 差: 逐个操作
for i in range(100):
    client.set(f"key_{i}", f"value_{i}")
```

---

## 📈 监控和日志

### 日志级别

```
DEBUG   → 详细的执行信息
INFO    → 关键事件 (连接, 开始, 完成)
WARNING → 异常情况 (重试, 超时)
ERROR   → 错误事件 (连接失败)
```

### 指标收集

```python
# 每个操作记录:
{
    "operation_id": "xxx",
    "client_name": "Redis",
    "thread_id": 12345,
    "start_time": 1234567890.123,
    "end_time": 1234567890.145,
    "latency_ms": 22,
    "status": "success"
}
```

---

## 🔐 安全考虑

### 1. 连接凭证
- 使用环境变量管理密码
- 不在代码中硬编码凭证
- 支持 SSL/TLS 加密

### 2. 资源限制
- 连接超时设置
- 最大重试次数
- 内存限制 (监控)

### 3. 错误处理
- try-catch 异常捕获
- 异常日志记录
- 优雅降级

---

## 🚀 扩展性设计

### 增加新的中间件

只需继承 `BenchmarkClient`:

```python
class ElasticsearchClient(BenchmarkClient):
    def connect(self):
        # 实现连接逻辑
        pass
    
    def test_operation(self):
        # 实现测试操作
        # 返回 OperationResult
        pass

# 注册到 BenchmarkSuite
suite.register_client(ElasticsearchClient(...))
```

### 添加自定义指标

```python
class CustomStats(BenchmarkStats):
    # 添加新字段
    cpu_usage: float
    memory_usage: float
    network_latency: float
```

---

## 📊 性能基准

在标准硬件上的典型性能:

```
硬件配置: 4 CPU, 8GB 内存

工具配置   吞吐量(ops/sec)
          Redis  MySQL  MongoDB  RabbitMQ
基础压测   25-30  8-12   5-8      10-15
中等压力   20-25  6-10   4-6      8-12
高强压力   15-20  4-8    2-4      5-8
```

---

**架构设计完成！** 🎯
