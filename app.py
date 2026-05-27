#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 后端服务 - 为压测仪表板提供 API
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import threading
import queue
from datetime import datetime
from benchmark_tool import (
    BenchmarkSuite, RedisClient, MySQLClient, 
    MongoDBClient, RabbitMQClient
)

app = Flask(__name__)
CORS(app)

# 全局状态
benchmark_state = {
    "status": "idle",  # idle, running, completed, failed
    "progress": 0,
    "results": {},
    "start_time": None,
    "end_time": None,
    "current_operation": 0,
    "total_operations": 0
}

result_queue = queue.Queue()
benchmark_thread = None


def run_benchmark_async(config):
    """异步运行压测"""
    global benchmark_state
    
    try:
        benchmark_state["status"] = "running"
        benchmark_state["start_time"] = datetime.now().isoformat()
        benchmark_state["results"] = {}
        
        # 创建压测套件
        suite = BenchmarkSuite(num_workers=config.get("num_workers", 20))
        
        # 配置
        configs = {
            "redis": {
                "host": config.get("redis_host", "localhost"),
                "port": config.get("redis_port", 6379),
                "db": 0,
                "timeout": 5
            },
            "mysql": {
                "host": config.get("mysql_host", "localhost"),
                "port": config.get("mysql_port", 3306),
                "user": config.get("mysql_user", "root"),
                "password": config.get("mysql_password", ""),
                "database": config.get("mysql_database", "test")
            },
            "mongodb": {
                "host": config.get("mongodb_host", "localhost"),
                "port": config.get("mongodb_port", 27017),
                "database": config.get("mongodb_database", "benchmark_db")
            },
            "rabbitmq": {
                "host": config.get("rabbitmq_host", "localhost"),
                "port": config.get("rabbitmq_port", 5672),
                "user": config.get("rabbitmq_user", "guest"),
                "password": config.get("rabbitmq_password", "guest"),
                "queue": "benchmark_queue"
            }
        }
        
        # 注册客户端
        services = config.get("services", ["redis", "mysql", "mongodb", "rabbitmq"])
        
        if "redis" in services:
            try:
                suite.register_client(RedisClient(configs["redis"]))
            except Exception as e:
                print(f"Redis 注册失败: {e}")
        
        if "mysql" in services:
            try:
                suite.register_client(MySQLClient(configs["mysql"]))
            except Exception as e:
                print(f"MySQL 注册失败: {e}")
        
        if "mongodb" in services:
            try:
                suite.register_client(MongoDBClient(configs["mongodb"]))
            except Exception as e:
                print(f"MongoDB 注册失败: {e}")
        
        if "rabbitmq" in services:
            try:
                suite.register_client(RabbitMQClient(configs["rabbitmq"]))
            except Exception as e:
                print(f"RabbitMQ 注册失败: {e}")
        
        # 运行压测
        operations = config.get("operations_per_client", 100)
        timeout = config.get("timeout", 60)
        
        benchmark_state["total_operations"] = len(suite.clients) * operations
        
        results = suite.run_benchmark(operations, timeout)
        
        # 转换结果为可序列化格式
        benchmark_state["results"] = {
            name: {
                "total_operations": stats.total_operations,
                "successful_operations": stats.successful_operations,
                "failed_operations": stats.failed_operations,
                "min_latency_ms": round(stats.min_latency_ms, 2),
                "max_latency_ms": round(stats.max_latency_ms, 2),
                "avg_latency_ms": round(stats.avg_latency_ms, 2),
                "p50_latency_ms": round(stats.p50_latency_ms, 2),
                "p95_latency_ms": round(stats.p95_latency_ms, 2),
                "p99_latency_ms": round(stats.p99_latency_ms, 2),
                "throughput_ops_per_sec": round(stats.throughput_ops_per_sec, 2),
                "duration_seconds": round(stats.duration_seconds, 2),
                "success_rate": round(
                    (stats.successful_operations / stats.total_operations * 100), 2
                )
            }
            for name, stats in results.items() if stats is not None
        }
        
        benchmark_state["progress"] = 100
        benchmark_state["status"] = "completed"
        benchmark_state["end_time"] = datetime.now().isoformat()
        
    except Exception as e:
        print(f"压测失败: {e}")
        benchmark_state["status"] = "failed"
        benchmark_state["error"] = str(e)


# API 端点

@app.route("/api/status", methods=["GET"])
def get_status():
    """获取当前压测状态"""
    return jsonify(benchmark_state)


@app.route("/api/start", methods=["POST"])
def start_benchmark():
    """开始压测"""
    global benchmark_thread, benchmark_state
    
    if benchmark_state["status"] == "running":
        return jsonify({"error": "压测已在运行"}), 400
    
    config = request.json or {}
    
    # 重置状态
    benchmark_state = {
        "status": "idle",
        "progress": 0,
        "results": {},
        "start_time": None,
        "end_time": None,
        "current_operation": 0,
        "total_operations": 0
    }
    
    # 启动异步压测线程
    benchmark_thread = threading.Thread(target=run_benchmark_async, args=(config,))
    benchmark_thread.daemon = True
    benchmark_thread.start()
    
    return jsonify({"message": "压测已启动", "status": "running"})


@app.route("/api/stop", methods=["POST"])
def stop_benchmark():
    """停止压测"""
    global benchmark_state
    
    if benchmark_state["status"] != "running":
        return jsonify({"error": "没有正在运行的压测"}), 400
    
    benchmark_state["status"] = "stopped"
    return jsonify({"message": "压测已停止"})


@app.route("/api/results", methods=["GET"])
def get_results():
    """获取压测结果"""
    return jsonify({
        "status": benchmark_state["status"],
        "results": benchmark_state["results"],
        "duration": benchmark_state.get("duration_seconds", 0),
        "start_time": benchmark_state.get("start_time"),
        "end_time": benchmark_state.get("end_time")
    })


@app.route("/api/config", methods=["GET"])
def get_config():
    """获取默认配置"""
    return jsonify({
        "num_workers": 20,
        "operations_per_client": 100,
        "timeout": 60,
        "services": ["redis", "mysql", "mongodb", "rabbitmq"],
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0
        },
        "mysql": {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "database": "test"
        },
        "mongodb": {
            "host": "localhost",
            "port": 27017,
            "database": "benchmark_db"
        },
        "rabbitmq": {
            "host": "localhost",
            "port": 5672,
            "user": "guest"
        }
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/", methods=["GET"])
def serve_dashboard():
    """提供仪表板 HTML"""
    try:
        with open("dashboard.html", "r", encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
    except FileNotFoundError:
        return jsonify({"error": "仪表板文件未找到"}), 404


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║          中间件压测工具 - Flask 后端服务                     ║
    ║                                                             ║
    ║  📊 仪表板: http://localhost:5000                           ║
    ║  📡 API:    http://localhost:5000/api                       ║
    ║                                                             ║
    ║  支持的中间件:                                               ║
    ║    - Redis    (默认 localhost:6379)                        ║
    ║    - MySQL    (默认 localhost:3306)                        ║
    ║    - MongoDB  (默认 localhost:27017)                       ║
    ║    - RabbitMQ (默认 localhost:5672)                        ║
    ║                                                             ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False  # 防止两次加载
    )
