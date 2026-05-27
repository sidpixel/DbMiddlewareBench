#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多中间件压测工具 - 支持 Redis/MySQL/MongoDB/RabbitMQ
支持并发测试、实时监控、详细报告生成
"""

import time
import threading
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
from enum import Enum
import traceback

# 第三方库
try:
    import redis
except ImportError:
    redis = None

try:
    import mysql.connector
except ImportError:
    mysql = None

try:
    import pymongo
except ImportError:
    pymongo = None

try:
    import pika
except ImportError:
    pika = None


class StatusEnum(Enum):
    """操作状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass
class OperationResult:
    """单次操作结果"""
    status: str
    latency_ms: float
    timestamp: float
    error: Optional[str] = None


@dataclass
class BenchmarkStats:
    """基准测试统计数据"""
    total_operations: int
    successful_operations: int
    failed_operations: int
    min_latency_ms: float
    max_latency_ms: float
    avg_latency_ms: float
    p50_latency_ms: float  # 中位数
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_ops_per_sec: float
    duration_seconds: float
    timestamp: str


class BenchmarkClient:
    """基准测试客户端基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.results: List[OperationResult] = []
        self.lock = threading.Lock()
    
    def connect(self) -> bool:
        """连接到服务"""
        raise NotImplementedError
    
    def disconnect(self) -> bool:
        """断开连接"""
        raise NotImplementedError
    
    def test_operation(self) -> OperationResult:
        """执行单次测试操作"""
        raise NotImplementedError
    
    def add_result(self, result: OperationResult):
        """线程安全地添加结果"""
        with self.lock:
            self.results.append(result)
    
    def calculate_stats(self, duration: float) -> BenchmarkStats:
        """计算统计数据"""
        if not self.results:
            return None
        
        latencies = [r.latency_ms for r in self.results if r.status == StatusEnum.SUCCESS.value]
        successful = len([r for r in self.results if r.status == StatusEnum.SUCCESS.value])
        failed = len([r for r in self.results if r.status == StatusEnum.FAILURE.value])
        
        if not latencies:
            return None
        
        return BenchmarkStats(
            total_operations=len(self.results),
            successful_operations=successful,
            failed_operations=failed,
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            avg_latency_ms=statistics.mean(latencies),
            p50_latency_ms=statistics.median(latencies),
            p95_latency_ms=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0],
            p99_latency_ms=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 1 else latencies[0],
            throughput_ops_per_sec=successful / duration if duration > 0 else 0,
            duration_seconds=duration,
            timestamp=datetime.now().isoformat()
        )
    
    def clear_results(self):
        """清空结果"""
        with self.lock:
            self.results.clear()


class RedisClient(BenchmarkClient):
    """Redis 压测客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Redis", config)
        self.client = None
    
    def connect(self) -> bool:
        try:
            self.client = redis.Redis(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 6379),
                db=self.config.get("db", 0),
                decode_responses=True,
                socket_timeout=self.config.get("timeout", 5)
            )
            self.client.ping()
            print(f"✓ {self.name} 连接成功")
            return True
        except Exception as e:
            print(f"✗ {self.name} 连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        if self.client:
            self.client.close()
            return True
        return False
    
    def test_operation(self) -> OperationResult:
        try:
            start = time.time()
            key = f"benchmark_{int(time.time() * 1000)}"
            self.client.set(key, "test_value", ex=60)
            value = self.client.get(key)
            self.client.delete(key)
            latency = (time.time() - start) * 1000
            
            return OperationResult(
                status=StatusEnum.SUCCESS.value,
                latency_ms=latency,
                timestamp=time.time()
            )
        except Exception as e:
            return OperationResult(
                status=StatusEnum.FAILURE.value,
                latency_ms=0,
                timestamp=time.time(),
                error=str(e)
            )


class MySQLClient(BenchmarkClient):
    """MySQL 压测客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("MySQL", config)
        self.client = None
        self.table_created = False
    
    def connect(self) -> bool:
        try:
            self.client = mysql.connector.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                user=self.config.get("user", "root"),
                password=self.config.get("password", ""),
                database=self.config.get("database", "test")
            )
            # 创建测试表
            cursor = self.client.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_test (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_key VARCHAR(255),
                    test_value VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.client.commit()
            cursor.close()
            self.table_created = True
            print(f"✓ {self.name} 连接成功")
            return True
        except Exception as e:
            print(f"✗ {self.name} 连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        if self.client:
            self.client.close()
            return True
        return False
    
    def test_operation(self) -> OperationResult:
        try:
            start = time.time()
            cursor = self.client.cursor()
            key = f"key_{int(time.time() * 1000)}"
            
            # 插入
            cursor.execute(
                "INSERT INTO benchmark_test (test_key, test_value) VALUES (%s, %s)",
                (key, "test_value")
            )
            # 查询
            cursor.execute("SELECT * FROM benchmark_test WHERE test_key = %s LIMIT 1", (key,))
            cursor.fetchone()
            # 删除
            cursor.execute("DELETE FROM benchmark_test WHERE test_key = %s", (key,))
            self.client.commit()
            cursor.close()
            
            latency = (time.time() - start) * 1000
            return OperationResult(
                status=StatusEnum.SUCCESS.value,
                latency_ms=latency,
                timestamp=time.time()
            )
        except Exception as e:
            return OperationResult(
                status=StatusEnum.FAILURE.value,
                latency_ms=0,
                timestamp=time.time(),
                error=str(e)
            )


class MongoDBClient(BenchmarkClient):
    """MongoDB 压测客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("MongoDB", config)
        self.client = None
        self.db = None
        self.collection = None
    
    def connect(self) -> bool:
        try:
            uri = f"mongodb://{self.config.get('username', '')}:{self.config.get('password', '')}:{self.config.get('host', '')}:{self.config.get('port', 27017)}"
            self.client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            
            self.db = self.client[self.config.get("database", "benchmark_db")]
            self.collection = self.db["benchmark_collection"]
            # 创建索引
            self.collection.create_index("test_key")
            print(f"✓ {self.name} 连接成功")
            return True
        except Exception as e:
            print(f"✗ {self.name} 连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        if self.client:
            self.client.close()
            return True
        return False
    
    def test_operation(self) -> OperationResult:
        try:
            start = time.time()
            key = f"key_{int(time.time() * 1000)}"
            
            # 插入
            result = self.collection.insert_one({"test_key": key, "test_value": "test_value"})
            # 查询
            self.collection.find_one({"test_key": key})
            # 删除
            self.collection.delete_one({"_id": result.inserted_id})
            
            latency = (time.time() - start) * 1000
            return OperationResult(
                status=StatusEnum.SUCCESS.value,
                latency_ms=latency,
                timestamp=time.time()
            )
        except Exception as e:
            return OperationResult(
                status=StatusEnum.FAILURE.value,
                latency_ms=0,
                timestamp=time.time(),
                error=str(e)
            )


class RabbitMQClient(BenchmarkClient):
    """RabbitMQ 压测客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("RabbitMQ", config)
        self.client = None
        self.channel = None
    
    def connect(self) -> bool:
        try:
            credentials = pika.PlainCredentials(
                self.config.get("user", "guest"),
                self.config.get("password", "guest")
            )
            parameters = pika.ConnectionParameters(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5672),
                credentials=credentials,
                connection_attempts=3,
                retry_delay=2
            )
            self.client = pika.BlockingConnection(parameters)
            self.channel = self.client.channel()
            
            # 声明队列
            self.channel.queue_declare(
                queue=self.config.get("queue", "benchmark_queue"),
                durable=True
            )
            print(f"✓ {self.name} 连接成功")
            return True
        except Exception as e:
            print(f"✗ {self.name} 连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        if self.client and not self.client.is_closed:
            self.client.close()
            return True
        return False
    
    def test_operation(self) -> OperationResult:
        try:
            start = time.time()
            queue_name = self.config.get("queue", "benchmark_queue")
            
            # 发送消息
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body='test_message',
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            # 接收消息
            method, properties, body = self.channel.basic_get(queue_name)
            if method:
                self.channel.basic_ack(method.delivery_tag)
            
            latency = (time.time() - start) * 1000
            return OperationResult(
                status=StatusEnum.SUCCESS.value,
                latency_ms=latency,
                timestamp=time.time()
            )
        except Exception as e:
            return OperationResult(
                status=StatusEnum.FAILURE.value,
                latency_ms=0,
                timestamp=time.time(),
                error=str(e)
            )


class BenchmarkSuite:
    """压测套件 - 管理多个中间件的并发测试"""
    
    def __init__(self, num_workers: int = 10):
        self.clients: Dict[str, BenchmarkClient] = {}
        self.num_workers = num_workers
        self.results: Dict[str, BenchmarkStats] = {}
    
    def register_client(self, client: BenchmarkClient):
        """注册客户端"""
        self.clients[client.name] = client
    
    def run_benchmark(self, operations_per_client: int = 1000, timeout: int = 300):
        """运行压测"""
        print(f"\n{'='*60}")
        print(f"开始压测 | 工作线程: {self.num_workers} | 单客户端操作数: {operations_per_client}")
        print(f"{'='*60}\n")
        
        # 连接所有客户端
        for name, client in self.clients.items():
            if not client.connect():
                print(f"跳过 {name}")
                continue
        
        # 并发执行压测
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {}
            
            for name, client in self.clients.items():
                if client.client is None:
                    continue
                
                for i in range(operations_per_client):
                    future = executor.submit(client.test_operation)
                    futures[future] = (name, client)
            
            # 收集结果
            completed = 0
            for future in as_completed(futures, timeout=timeout):
                name, client = futures[future]
                try:
                    result = future.result()
                    client.add_result(result)
                    completed += 1
                except Exception as e:
                    print(f"操作失败: {e}")
        
        duration = time.time() - start_time
        
        # 计算统计
        for name, client in self.clients.items():
            stats = client.calculate_stats(duration)
            if stats:
                self.results[name] = stats
        
        # 断开连接
        for client in self.clients.values():
            client.disconnect()
        
        return self.results
    
    def print_report(self):
        """打印报告"""
        print(f"\n{'='*80}")
        print("                        压测报告")
        print(f"{'='*80}\n")
        
        for name, stats in self.results.items():
            if stats is None:
                continue
            
            print(f"【{name}】")
            print(f"  总操作数: {stats.total_operations:,}")
            print(f"  成功: {stats.successful_operations:,} | 失败: {stats.failed_operations:,}")
            print(f"  成功率: {(stats.successful_operations/stats.total_operations*100):.2f}%")
            print(f"  延迟 (ms):")
            print(f"    - 最小: {stats.min_latency_ms:.2f}")
            print(f"    - 平均: {stats.avg_latency_ms:.2f}")
            print(f"    - 中位: {stats.p50_latency_ms:.2f}")
            print(f"    - P95:  {stats.p95_latency_ms:.2f}")
            print(f"    - P99:  {stats.p99_latency_ms:.2f}")
            print(f"    - 最大: {stats.max_latency_ms:.2f}")
            print(f"  吞吐量: {stats.throughput_ops_per_sec:.2f} ops/sec")
            print(f"  耗时: {stats.duration_seconds:.2f}s")
            print()
    
    def export_json(self, filename: str = "benchmark_results.json"):
        """导出 JSON 报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "num_workers": self.num_workers,
                "clients": list(self.clients.keys())
            },
            "results": {
                name: asdict(stats) 
                for name, stats in self.results.items() 
                if stats is not None
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 报告已导出: {filename}")
        return filename


def main():
    """主函数 - 示例使用"""
    
    # 创建压测套件
    suite = BenchmarkSuite(num_workers=20)
    
    # 配置各中间件
    configs = {
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "timeout": 5
        },
        "mysql": {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "root",
            "database": "test"
        },
        "mongodb": {
            "host": "localhost",
            "username": "admin",
            "password": "admin123",
            "port": 27017,
            "database": "benchmark_db"
        },
        "rabbitmq": {
            "host": "localhost",
            "port": 5672,
            "user": "guest",
            "password": "guest",
            "queue": "benchmark_queue"
        }
    }
    
    # 注册可用的客户端
    if redis:
        suite.register_client(RedisClient(configs["redis"]))
    else:
        print("⚠ redis 库未安装，跳过 Redis 压测")
    
    if mysql:
        suite.register_client(MySQLClient(configs["mysql"]))
    else:
        print("⚠ mysql.connector 库未安装，跳过 MySQL 压测")
    
    if pymongo:
        suite.register_client(MongoDBClient(configs["mongodb"]))
    else:
        print("⚠ pymongo 库未安装，跳过 MongoDB 压测")
    
    if pika:
        suite.register_client(RabbitMQClient(configs["rabbitmq"]))
    else:
        print("⚠ pika 库未安装，跳过 RabbitMQ 压测")
    
    # 运行压测 (100 次操作/客户端, 60 秒超时)
    try:
        suite.run_benchmark(operations_per_client=100, timeout=60)
        suite.print_report()
        suite.export_json()
    except Exception as e:
        print(f"✗ 压测失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
