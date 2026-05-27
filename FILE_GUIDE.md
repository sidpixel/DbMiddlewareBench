# 📁 项目文件指南

## 项目结构

```
benchmark/
├── 🚀 快速开始
│   ├── QUICK_START.md              # ⭐ 5分钟快速开始指南
│   ├── requirements.txt             # Python 依赖列表
│   └── docker-compose.yml           # Docker 一键启动中间件
│
├── 💻 核心程序
│   ├── benchmark_tool.py            # ⭐ 压测工具核心代码 (命令行模式)
│   ├── app.py                       # ⭐ Flask 后端服务 (Web 仪表板)
│   └── dashboard.html               # ⭐ Web 仪表板 (前端界面)
│
└── 📖 文档
    ├── README.md                    # ⭐ 完整使用手册
    ├── ARCHITECTURE.md              # 系统架构设计
    ├── FILE_GUIDE.md                # 本文件
    └── benchmark_results.json       # 压测结果 (自动生成)
```

---

## 各文件详细说明

### 🟦 QUICK_START.md
**用途**: 快速开始指南
**内容**:
- 3 步快速开始
- 选择性运行方式 (CLI vs Web)
- 常见问题解答
- 结果理解指南

**何时阅读**: 第一次使用时立即阅读

---

### 🟦 README.md
**用途**: 完整使用手册
**内容**:
- 详细安装步骤
- 中间件配置方法
- API 文档
- 性能优化建议
- Docker 部署
- 故障排除指南

**何时阅读**: 需要详细配置或遇到问题时

---

### 🟦 ARCHITECTURE.md
**用途**: 系统架构和设计文档
**内容**:
- 总体架构图
- 工作流程说明
- 核心组件详解
- 并发执行模型
- 性能优化策略
- 数据结构设计

**何时阅读**: 想了解实现原理或扩展功能时

---

### 🔴 benchmark_tool.py
**用途**: 核心压测工具
**大小**: ~600 行代码
**功能**:
- 支持 Redis/MySQL/MongoDB/RabbitMQ 四种中间件
- 并发压测引擎
- 统计计算
- JSON 报告导出
- 命令行交互

**使用方式**:
```bash
# 直接运行
python benchmark_tool.py

# 可输出:
# - 控制台报告
# - benchmark_results.json 文件
```

**关键类**:
- `BenchmarkClient` - 基础客户端类
- `RedisClient` - Redis 实现
- `MySQLClient` - MySQL 实现
- `MongoDBClient` - MongoDB 实现
- `RabbitMQClient` - RabbitMQ 实现
- `BenchmarkSuite` - 压测套件管理

---

### 🔴 app.py
**用途**: Flask 后端服务
**大小**: ~250 行代码
**功能**:
- RESTful API 端点
- Web 仪表板服务
- 异步压测执行
- 实时状态更新
- CORS 跨域支持

**使用方式**:
```bash
python app.py
# 访问 http://localhost:5000
```

**API 端点**:
- `GET /api/status` - 获取压测状态
- `GET /api/results` - 获取结果
- `GET /api/config` - 获取配置
- `POST /api/start` - 启动压测
- `POST /api/stop` - 停止压测
- `GET /api/health` - 健康检查

---

### 🔵 dashboard.html
**用途**: Web 仪表板前端
**大小**: ~800 行 (HTML + CSS + JavaScript)
**功能**:
- 实时压测可视化
- 交互式控制面板
- 动画图表展示
- 详细结果表格
- 进度监控

**使用方式**:
```bash
# Flask 服务启动后自动提供
http://localhost:5000
```

**特色**:
- 深色主题设计
- 完全响应式布局
- 流畅的动画效果
- 实时数据更新
- 导出功能

---

### 🟩 requirements.txt
**用途**: Python 依赖声明
**内容**:
```
redis==5.0.0
mysql-connector-python==8.0.33
pymongo==4.5.0
pika==1.3.1
flask==2.3.0
flask-cors==4.0.0
```

**使用方式**:
```bash
pip install -r requirements.txt
```

---

### 🟩 docker-compose.yml
**用途**: Docker 容器编排配置
**包含**:
- Redis (端口 6379)
- MySQL (端口 3306)
- MongoDB (端口 27017)
- RabbitMQ (端口 5672, 管理界面 15672)

**使用方式**:
```bash
# 启动所有中间件
docker-compose up -d

# 查看状态
docker-compose ps

# 停止服务
docker-compose down

# 清理数据
docker-compose down -v
```

**优势**:
- 一键启动所有依赖
- 自动化网络配置
- 内置健康检查
- 数据卷持久化

---

## 🎯 使用流程

### 新手流程 (推荐)

```
1. 阅读 QUICK_START.md
   ↓
2. 安装依赖
   pip install -r requirements.txt
   ↓
3. 启动中间件
   docker-compose up -d
   ↓
4. 运行压测
   方式 A: python benchmark_tool.py    (命令行)
   方式 B: python app.py               (Web)
   ↓
5. 查看结果
   控制台输出 或 http://localhost:5000
```

### 高级用户流程

```
1. 理解架构 (ARCHITECTURE.md)
   ↓
2. 自定义配置 (修改 benchmark_tool.py)
   ↓
3. 增加新中间件 (继承 BenchmarkClient)
   ↓
4. 运行自定义压测
   ↓
5. 分析结果 (benchmark_results.json)
```

---

## 📊 输出文件说明

### benchmark_results.json

压测完成后自动生成，包含完整结果:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "config": {
    "num_workers": 20,
    "clients": ["Redis", "MySQL", "MongoDB", "RabbitMQ"]
  },
  "results": {
    "Redis": {
      "total_operations": 100,
      "successful_operations": 100,
      "failed_operations": 0,
      "min_latency_ms": 1.23,
      "max_latency_ms": 12.34,
      "avg_latency_ms": 3.45,
      "p50_latency_ms": 3.20,
      "p95_latency_ms": 5.67,
      "p99_latency_ms": 7.89,
      "throughput_ops_per_sec": 29.04,
      "duration_seconds": 3.44
    },
    "MySQL": { ... },
    "MongoDB": { ... },
    "RabbitMQ": { ... }
  }
}
```

**用途**:
- 长期保存结果
- 对比多次压测
- 生成图表报告
- 集成到其他系统

---

## 🔧 定制指南

### 修改压测参数

编辑 `benchmark_tool.py` 的 `main()` 函数:

```python
# 工作线程数
suite = BenchmarkSuite(num_workers=50)

# 单客户端操作数
suite.run_benchmark(operations_per_client=500)

# 超时时间
suite.run_benchmark(..., timeout=120)
```

### 修改连接配置

```python
configs = {
    "redis": {
        "host": "192.168.1.100",  # 改为你的 IP
        "port": 6379,
        "timeout": 10              # 增加超时
    },
    # ... 其他配置
}
```

### 添加新中间件

```python
class ElasticsearchClient(BenchmarkClient):
    def connect(self):
        # 实现连接
        pass
    
    def test_operation(self):
        # 实现测试
        return OperationResult(...)

# 注册
suite.register_client(ElasticsearchClient(config))
```

---

## 📈 文件间的依赖关系

```
QUICK_START.md
    ↓
    ├─→ requirements.txt ─────┐
    ├─→ docker-compose.yml    │
    └─→ README.md ←───────────┘
            ↓
    ┌───────┴────────┐
    │                │
    v                v
benchmark_tool.py  app.py + dashboard.html
    │                │
    └────────┬────────┘
             ↓
    benchmark_results.json
    (每次运行自动生成)
    
ARCHITECTURE.md (参考文档)
```

---

## 🚀 推荐阅读顺序

### 第一次使用 (30 分钟)
1. QUICK_START.md (5 分钟)
2. docker-compose.yml 配置 (5 分钟)
3. 运行第一次压测 (10 分钟)
4. 查看结果 (5 分钟)
5. 简单定制 (5 分钟)

### 深入学习 (1 小时)
1. README.md - 完整手册
2. benchmark_tool.py - 代码阅读
3. ARCHITECTURE.md - 架构理解
4. 自定义扩展

### 生产部署 (2 小时)
1. README.md - Docker 部分
2. app.py - API 文档
3. dashboard.html - 前端定制
4. 性能优化指南

---

## 💡 常见问题速查

| 问题 | 查看文件 |
|------|---------|
| 如何快速开始? | QUICK_START.md |
| 如何配置中间件? | README.md |
| 如何理解结果? | QUICK_START.md |
| API 如何使用? | README.md |
| 系统如何工作? | ARCHITECTURE.md |
| 如何扩展功能? | ARCHITECTURE.md |
| 遇到错误怎么办? | README.md (故障排除) |
| Docker 怎么用? | docker-compose.yml + README.md |

---

**🎉 祝你使用愉快！**
