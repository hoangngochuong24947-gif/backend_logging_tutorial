"""
后端日志教学 - 高级层：MCP日志服务
文件名：02_mcp_logging_service.py
功能：学习如何创建和使用MCP（Model Context Protocol）日志服务

教学目标：
1. 理解MCP协议的基本概念
2. 学习创建MCP兼容的日志服务
3. 掌握MCP工具和资源的使用
4. 了解MCP在日志系统中的应用场景
"""

import logging
import logging.config
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import threading
import queue
import uuid
import asyncio
from contextlib import asynccontextmanager
import inspect

print("=" * 80)
print("MCP日志服务")
print("=" * 80)

# ============================================
# 第一部分：MCP基础概念
# ============================================

print("\n" + "=" * 50)
print("第一部分：MCP基础概念")
print("=" * 50)

print("""
MCP（Model Context Protocol）是什么？

MCP是一个开放协议，用于在AI模型和外部工具/服务之间建立标准化的通信。
它允许AI模型：
1. 发现可用的工具和资源
2. 调用工具执行操作
3. 访问结构化数据资源

在日志系统中的MCP应用：
1. 日志查询工具 - AI可以查询和分析日志
2. 日志监控工具 - AI可以监控日志并触发告警
3. 日志分析工具 - AI可以帮助分析日志模式和趋势
4. 日志配置工具 - AI可以帮助配置日志系统
""")

# ============================================
# 第二部分：MCP日志服务基础架构
# ============================================

print("\n" + "=" * 50)
print("第二部分：MCP日志服务基础架构")
print("=" * 50)

class MCPServerBase:
    """MCP服务器基类"""

    def __init__(self, server_name):
        self.server_name = server_name
        self.tools = {}
        self.resources = {}
        self.logger = logging.getLogger(f'mcp.server.{server_name}')

        print(f"初始化MCP服务器: {server_name}")

    def register_tool(self, tool_name, tool_func, description, input_schema=None):
        """注册工具"""
        self.tools[tool_name] = {
            'function': tool_func,
            'description': description,
            'input_schema': input_schema or {}
        }
        self.logger.info(f"注册工具: {tool_name}")

    def register_resource(self, resource_uri, resource_getter, description, mime_type="application/json"):
        """注册资源"""
        self.resources[resource_uri] = {
            'getter': resource_getter,
            'description': description,
            'mime_type': mime_type
        }
        self.logger.info(f"注册资源: {resource_uri}")

    async def list_tools(self):
        """列出所有可用工具"""
        tools_info = []
        for name, tool in self.tools.items():
            tools_info.append({
                'name': name,
                'description': tool['description'],
                'inputSchema': tool['input_schema']
            })
        return tools_info

    async def list_resources(self):
        """列出所有可用资源"""
        resources_info = []
        for uri, resource in self.resources.items():
            resources_info.append({
                'uri': uri,
                'description': resource['description'],
                'mimeType': resource['mime_type']
            })
        return resources_info

    async def call_tool(self, tool_name, arguments):
        """调用工具"""
        if tool_name not in self.tools:
            raise ValueError(f"未知工具: {tool_name}")

        tool = self.tools[tool_name]
        self.logger.info(f"调用工具: {tool_name}, 参数: {arguments}")

        try:
            # 检查是否为异步函数
            if inspect.iscoroutinefunction(tool['function']):
                result = await tool['function'](**arguments)
            else:
                result = tool['function'](**arguments)

            self.logger.debug(f"工具调用结果: {result}")
            return result

        except Exception as e:
            self.logger.error(f"工具调用失败: {tool_name}", exc_info=True)
            raise

    async def read_resource(self, resource_uri):
        """读取资源"""
        if resource_uri not in self.resources:
            raise ValueError(f"未知资源: {resource_uri}")

        resource = self.resources[resource_uri]
        self.logger.info(f"读取资源: {resource_uri}")

        try:
            result = resource['getter'](resource_uri)
            self.logger.debug(f"资源内容长度: {len(str(result))}")
            return result

        except Exception as e:
            self.logger.error(f"读取资源失败: {resource_uri}", exc_info=True)
            raise

# ============================================
# 第三部分：日志查询MCP服务实现
# ============================================

print("\n" + "=" * 50)
print("第三部分：日志查询MCP服务实现")
print("=" * 50)

class LogQueryMCPServer(MCPServerBase):
    """日志查询MCP服务器"""

    def __init__(self):
        super().__init__("log-query-service")
        self.log_store = LogStoreSimulator()
        self.setup_tools()
        self.setup_resources()

    def setup_tools(self):
        """设置工具"""
        # 1. 按时间范围查询日志
        self.register_tool(
            tool_name="query_logs_by_time",
            tool_func=self.query_logs_by_time,
            description="按时间范围查询日志",
            input_schema={
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "开始时间 (ISO格式)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "结束时间 (ISO格式)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数限制",
                        "default": 100
                    }
                },
                "required": ["start_time", "end_time"]
            }
        )

        # 2. 按级别查询日志
        self.register_tool(
            tool_name="query_logs_by_level",
            tool_func=self.query_logs_by_level,
            description="按日志级别查询",
            input_schema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "日志级别 (ERROR, WARNING, INFO, DEBUG)",
                        "enum": ["ERROR", "WARNING", "INFO", "DEBUG"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数限制",
                        "default": 50
                    }
                },
                "required": ["level"]
            }
        )

        # 3. 搜索日志内容
        self.register_tool(
            tool_name="search_logs",
            tool_func=self.search_logs,
            description="搜索日志内容",
            input_schema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "搜索字段 (message, app, user_id等)",
                        "default": ["message"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数限制",
                        "default": 50
                    }
                },
                "required": ["keyword"]
            }
        )

        # 4. 统计日志级别分布
        self.register_tool(
            tool_name="analyze_log_levels",
            tool_func=self.analyze_log_levels,
            description="分析日志级别分布",
            input_schema={
                "type": "object",
                "properties": {
                    "time_range": {
                        "type": "string",
                        "description": "时间范围 (1h, 24h, 7d, 30d)",
                        "default": "24h"
                    }
                }
            }
        )

        # 5. 检测异常模式
        self.register_tool(
            tool_name="detect_anomalies",
            tool_func=self.detect_anomalies,
            description="检测日志异常模式",
            input_schema={
                "type": "object",
                "properties": {
                    "time_window": {
                        "type": "string",
                        "description": "时间窗口 (例如: 1h)",
                        "default": "1h"
                    },
                    "sensitivity": {
                        "type": "number",
                        "description": "敏感度 (0.1-1.0)",
                        "default": 0.7
                    }
                }
            }
        )

        # 6. 生成日志报告
        self.register_tool(
            tool_name="generate_log_report",
            tool_func=self.generate_log_report,
            description="生成日志分析报告",
            input_schema={
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "description": "报告类型 (daily, weekly, error_summary)",
                        "enum": ["daily", "weekly", "error_summary"]
                    },
                    "date": {
                        "type": "string",
                        "description": "报告日期 (YYYY-MM-DD)"
                    }
                },
                "required": ["report_type", "date"]
            }
        )

    def setup_resources(self):
        """设置资源"""
        # 1. 日志系统状态
        self.register_resource(
            resource_uri="mcp://logs/system/status",
            resource_getter=self.get_system_status,
            description="日志系统状态信息"
        )

        # 2. 最近错误日志
        self.register_resource(
            resource_uri="mcp://logs/recent/errors",
            resource_getter=self.get_recent_errors,
            description="最近发生的错误日志"
        )

        # 3. 日志统计摘要
        self.register_resource(
            resource_uri="mcp://logs/stats/summary",
            resource_getter=self.get_stats_summary,
            description="日志统计摘要"
        )

        # 4. 活跃监控告警
        self.register_resource(
            resource_uri="mcp://logs/alerts/active",
            resource_getter=self.get_active_alerts,
            description="活跃的监控告警"
        )

    # 工具实现
    def query_logs_by_time(self, start_time, end_time, limit=100):
        """按时间范围查询日志"""
        self.logger.info(f"查询日志: {start_time} 到 {end_time}, 限制: {limit}")
        return self.log_store.query_by_time_range(start_time, end_time, limit)

    def query_logs_by_level(self, level, limit=50):
        """按日志级别查询"""
        self.logger.info(f"查询{level}级别日志, 限制: {limit}")
        return self.log_store.query_by_level(level, limit)

    def search_logs(self, keyword, fields=None, limit=50):
        """搜索日志内容"""
        fields = fields or ["message"]
        self.logger.info(f"搜索日志: 关键词='{keyword}', 字段={fields}, 限制: {limit}")
        return self.log_store.search(keyword, fields, limit)

    def analyze_log_levels(self, time_range="24h"):
        """分析日志级别分布"""
        self.logger.info(f"分析日志级别分布: 时间范围={time_range}")
        return self.log_store.analyze_level_distribution(time_range)

    def detect_anomalies(self, time_window="1h", sensitivity=0.7):
        """检测异常模式"""
        self.logger.info(f"检测异常: 时间窗口={time_window}, 敏感度={sensitivity}")
        return self.log_store.detect_anomalies(time_window, sensitivity)

    def generate_log_report(self, report_type, date):
        """生成日志报告"""
        self.logger.info(f"生成报告: 类型={report_type}, 日期={date}")
        return self.log_store.generate_report(report_type, date)

    # 资源实现
    def get_system_status(self, uri):
        """获取系统状态"""
        return {
            "status": "healthy",
            "uptime": "7 days",
            "total_logs": self.log_store.get_total_count(),
            "storage_used": "2.3 GB",
            "last_updated": datetime.now().isoformat()
        }

    def get_recent_errors(self, uri):
        """获取最近错误"""
        return self.log_store.get_recent_errors(20)

    def get_stats_summary(self, uri):
        """获取统计摘要"""
        return self.log_store.get_stats_summary()

    def get_active_alerts(self, uri):
        """获取活跃告警"""
        return self.log_store.get_active_alerts()

# 日志存储模拟器
class LogStoreSimulator:
    """日志存储模拟器，用于演示"""

    def __init__(self):
        self.logs = []
        self._generate_sample_logs()

    def _generate_sample_logs(self):
        """生成示例日志"""
        apps = ["auth-service", "api-gateway", "payment-service", "user-service", "inventory-service"]
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        endpoints = ["/api/login", "/api/products", "/api/orders", "/api/users", "/api/payments"]

        # 生成1000条示例日志
        for i in range(1000):
            timestamp = datetime.now().isoformat()
            # 模拟时间分布
            if i > 0:
                # 每条日志比前一条晚1-10秒
                pass

            log = {
                "id": f"log_{i:06d}",
                "timestamp": timestamp,
                "level": random.choice(levels),
                "app": random.choice(apps),
                "message": f"示例日志消息 {i}",
                "endpoint": random.choice(endpoints),
                "status_code": random.choice([200, 200, 200, 404, 500]),
                "user_id": f"user_{random.randint(1, 100)}",
                "duration_ms": random.randint(50, 2000)
            }

            # 添加一些特定模式的日志
            if i % 100 == 0:
                log["level"] = "ERROR"
                log["message"] = "数据库连接失败"
            elif i % 50 == 0:
                log["level"] = "WARNING"
                log["message"] = "API响应时间超过阈值"

            self.logs.append(log)

    def query_by_time_range(self, start_time, end_time, limit=100):
        """按时间范围查询"""
        # 简化实现：返回模拟数据
        results = []
        for i, log in enumerate(self.logs[:limit]):
            # 模拟时间过滤
            if i % 3 == 0:  # 每3条返回1条，模拟过滤
                results.append(log)
        return {"count": len(results), "logs": results}

    def query_by_level(self, level, limit=50):
        """按级别查询"""
        filtered = [log for log in self.logs if log["level"] == level][:limit]
        return {"count": len(filtered), "logs": filtered}

    def search(self, keyword, fields, limit=50):
        """搜索日志"""
        results = []
        for log in self.logs[:200]:  # 只搜索前200条
            for field in fields:
                if field in log and keyword.lower() in str(log[field]).lower():
                    results.append(log)
                    break
            if len(results) >= limit:
                break
        return {"count": len(results), "logs": results}

    def analyze_level_distribution(self, time_range):
        """分析级别分布"""
        # 模拟分析
        distribution = {"DEBUG": 150, "INFO": 600, "WARNING": 200, "ERROR": 50}
        return {
            "time_range": time_range,
            "total": sum(distribution.values()),
            "distribution": distribution,
            "percentage": {k: v/sum(distribution.values())*100 for k, v in distribution.items()}
        }

    def detect_anomalies(self, time_window, sensitivity):
        """检测异常"""
        # 模拟异常检测
        anomalies = []
        if random.random() > 0.5:
            anomalies.append({
                "type": "error_spike",
                "description": f"检测到错误日志突增 (窗口: {time_window})",
                "severity": "high",
                "timestamp": datetime.now().isoformat()
            })
        if random.random() > 0.7:
            anomalies.append({
                "type": "slow_response",
                "description": "检测到API响应时间异常",
                "severity": "medium",
                "timestamp": datetime.now().isoformat()
            })

        return {
            "time_window": time_window,
            "sensitivity": sensitivity,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies
        }

    def generate_report(self, report_type, date):
        """生成报告"""
        # 模拟报告生成
        return {
            "report_type": report_type,
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_logs": 1000,
                "error_count": 50,
                "warning_count": 200,
                "top_error": "数据库连接失败",
                "busiest_service": "api-gateway"
            },
            "recommendations": [
                "建议检查数据库连接池配置",
                "API网关响应时间需要优化",
                "考虑增加错误告警阈值"
            ]
        }

    def get_total_count(self):
        """获取总日志数"""
        return len(self.logs)

    def get_recent_errors(self, limit=20):
        """获取最近错误"""
        errors = [log for log in self.logs if log["level"] == "ERROR"][:limit]
        return {"count": len(errors), "errors": errors}

    def get_stats_summary(self):
        """获取统计摘要"""
        return {
            "total_logs": len(self.logs),
            "by_level": {"DEBUG": 150, "INFO": 600, "WARNING": 200, "ERROR": 50},
            "by_app": {"auth-service": 200, "api-gateway": 300, "payment-service": 250, "user-service": 150, "inventory-service": 100},
            "avg_response_time": "345ms",
            "error_rate": "5%"
        }

    def get_active_alerts(self):
        """获取活跃告警"""
        return [
            {
                "id": "alert_001",
                "type": "error_rate",
                "description": "错误率超过阈值(5%)",
                "severity": "warning",
                "triggered_at": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "id": "alert_002",
                "type": "slow_api",
                "description": "/api/products 响应时间超过2秒",
                "severity": "info",
                "triggered_at": datetime.now().isoformat(),
                "status": "active"
            }
        ]

# ============================================
# 第四部分：MCP客户端实现
# ============================================

print("\n" + "=" * 50)
print("第四部分：MCP客户端实现")
print("=" * 50)

class MCPClient:
    """MCP客户端，用于与MCP服务器通信"""

    def __init__(self, server_url):
        self.server_url = server_url
        self.logger = logging.getLogger('mcp.client')
        print(f"初始化MCP客户端，连接: {server_url}")

    async def connect(self):
        """连接到MCP服务器"""
        self.logger.info(f"连接到MCP服务器: {self.server_url}")
        # 模拟连接
        await asyncio.sleep(0.1)
        self.logger.info("连接成功")
        return True

    async def discover_tools(self):
        """发现可用工具"""
        self.logger.info("发现可用工具...")
        # 模拟从服务器获取工具列表
        await asyncio.sleep(0.1)

        # 模拟返回的工具列表
        tools = [
            {
                "name": "query_logs_by_time",
                "description": "按时间范围查询日志",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                        "limit": {"type": "integer", "default": 100}
                    },
                    "required": ["start_time", "end_time"]
                }
            },
            {
                "name": "query_logs_by_level",
                "description": "按日志级别查询",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["ERROR", "WARNING", "INFO", "DEBUG"]},
                        "limit": {"type": "integer", "default": 50}
                    },
                    "required": ["level"]
                }
            },
            {
                "name": "search_logs",
                "description": "搜索日志内容",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string"},
                        "fields": {"type": "array", "items": {"type": "string"}, "default": ["message"]},
                        "limit": {"type": "integer", "default": 50}
                    },
                    "required": ["keyword"]
                }
            }
        ]

        self.logger.info(f"发现 {len(tools)} 个工具")
        return tools

    async def discover_resources(self):
        """发现可用资源"""
        self.logger.info("发现可用资源...")
        await asyncio.sleep(0.1)

        # 模拟返回的资源列表
        resources = [
            {
                "uri": "mcp://logs/system/status",
                "description": "日志系统状态信息",
                "mimeType": "application/json"
            },
            {
                "uri": "mcp://logs/recent/errors",
                "description": "最近发生的错误日志",
                "mimeType": "application/json"
            }
        ]

        self.logger.info(f"发现 {len(resources)} 个资源")
        return resources

    async def call_tool(self, tool_name, arguments):
        """调用工具"""
        self.logger.info(f"调用工具: {tool_name}, 参数: {arguments}")

        # 模拟调用
        await asyncio.sleep(0.2)

        # 模拟不同工具的结果
        if tool_name == "query_logs_by_time":
            result = {
                "count": 42,
                "logs": [
                    {
                        "id": "log_000001",
                        "timestamp": "2024-01-01T10:00:00Z",
                        "level": "INFO",
                        "app": "auth-service",
                        "message": "用户登录成功",
                        "user_id": "user_123"
                    },
                    {
                        "id": "log_000002",
                        "timestamp": "2024-01-01T10:01:00Z",
                        "level": "ERROR",
                        "app": "payment-service",
                        "message": "支付处理失败",
                        "error_code": "PAYMENT_001"
                    }
                ]
            }
        elif tool_name == "query_logs_by_level":
            result = {
                "count": 15,
                "logs": [
                    {
                        "id": "log_000003",
                        "timestamp": "2024-01-01T09:30:00Z",
                        "level": "ERROR",
                        "app": "api-gateway",
                        "message": "API调用超时",
                        "duration_ms": 5000
                    }
                ]
            }
        elif tool_name == "search_logs":
            result = {
                "count": 8,
                "logs": [
                    {
                        "id": "log_000004",
                        "timestamp": "2024-01-01T11:00:00Z",
                        "level": "WARNING",
                        "app": "inventory-service",
                        "message": "库存不足警告",
                        "product_id": "prod_456"
                    }
                ]
            }
        else:
            result = {"error": f"未知工具: {tool_name}"}

        self.logger.info(f"工具调用完成: {tool_name}")
        return result

    async def read_resource(self, resource_uri):
        """读取资源"""
        self.logger.info(f"读取资源: {resource_uri}")

        await asyncio.sleep(0.1)

        # 模拟资源内容
        if resource_uri == "mcp://logs/system/status":
            result = {
                "status": "healthy",
                "uptime": "7 days",
                "total_logs": 1000,
                "storage_used": "2.3 GB"
            }
        elif resource_uri == "mcp://logs/recent/errors":
            result = {
                "count": 3,
                "errors": [
                    {
                        "timestamp": "2024-01-01T10:01:00Z",
                        "app": "payment-service",
                        "message": "支付处理失败",
                        "error_code": "PAYMENT_001"
                    },
                    {
                        "timestamp": "2024-01-01T09:30:00Z",
                        "app": "api-gateway",
                        "message": "API调用超时"
                    }
                ]
            }
        else:
            result = {"error": f"未知资源: {resource_uri}"}

        return result

# ============================================
# 第五部分：AI代理集成示例
# ============================================

print("\n" + "=" * 50)
print("第五部分：AI代理集成示例")
print("=" * 50)

class AILogAnalyst:
    """AI日志分析代理"""

    def __init__(self, mcp_client):
        self.client = mcp_client
        self.logger = logging.getLogger('ai.log_analyst')
        print("初始化AI日志分析代理")

    async def analyze_system_health(self):
        """分析系统健康状态"""
        self.logger.info("开始分析系统健康状态...")

        try:
            # 1. 获取系统状态
            status = await self.client.read_resource("mcp://logs/system/status")
            self.logger.debug(f"系统状态: {status}")

            # 2. 获取最近错误
            errors = await self.client.read_resource("mcp://logs/recent/errors")
            self.logger.debug(f"最近错误: {errors['count']} 个")

            # 3. 分析错误趋势
            error_analysis = await self.analyze_error_trends()

            # 4. 生成健康报告
            report = {
                "timestamp": datetime.now().isoformat(),
                "overall_health": self._calculate_health_score(status, errors, error_analysis),
                "system_status": status,
                "recent_errors": errors,
                "error_trends": error_analysis,
                "recommendations": self._generate_recommendations(status, errors, error_analysis)
            }

            self.logger.info("系统健康分析完成")
            return report

        except Exception as e:
            self.logger.error("分析系统健康状态失败", exc_info=True)
            raise

    async def analyze_error_trends(self):
        """分析错误趋势"""
        self.logger.info("分析错误趋势...")

        # 查询最近24小时的错误日志
        end_time = datetime.now().isoformat()
        # 模拟24小时前
        start_time = datetime.now().isoformat()  # 简化处理

        try:
            result = await self.client.call_tool("query_logs_by_time", {
                "start_time": start_time,
                "end_time": end_time,
                "limit": 1000
            })

            # 分析错误分布
            errors_by_app = {}
            errors_by_type = {}

            for log in result.get("logs", []):
                if log.get("level") == "ERROR":
                    app = log.get("app", "unknown")
                    errors_by_app[app] = errors_by_app.get(app, 0) + 1

                    # 简单错误分类
                    message = log.get("message", "").lower()
                    if "timeout" in message:
                        errors_by_type["timeout"] = errors_by_type.get("timeout", 0) + 1
                    elif "database" in message:
                        errors_by_type["database"] = errors_by_type.get("database", 0) + 1
                    elif "connection" in message:
                        errors_by_type["connection"] = errors_by_type.get("connection", 0) + 1
                    else:
                        errors_by_type["other"] = errors_by_type.get("other", 0) + 1

            analysis = {
                "total_errors": sum(errors_by_app.values()),
                "errors_by_application": errors_by_app,
                "errors_by_type": errors_by_type,
                "top_error_app": max(errors_by_app.items(), key=lambda x: x[1])[0] if errors_by_app else "none",
                "most_common_error_type": max(errors_by_type.items(), key=lambda x: x[1])[0] if errors_by_type else "none"
            }

            self.logger.info(f"错误趋势分析完成: 共{analysis['total_errors']}个错误")
            return analysis

        except Exception as e:
            self.logger.error("分析错误趋势失败", exc_info=True)
            return {"error": str(e)}

    async def investigate_issue(self, issue_description):
        """调查特定问题"""
        self.logger.info(f"调查问题: {issue_description}")

        try:
            # 1. 搜索相关日志
            search_result = await self.client.call_tool("search_logs", {
                "keyword": self._extract_keywords(issue_description),
                "fields": ["message", "app"],
                "limit": 50
            })

            # 2. 分析错误日志
            errors = await self.client.call_tool("query_logs_by_level", {
                "level": "ERROR",
                "limit": 30
            })

            # 3. 检测异常模式
            anomalies = await self.client.call_tool("detect_anomalies", {
                "time_window": "1h",
                "sensitivity": 0.7
            })

            # 4. 生成调查报告
            investigation = {
                "issue": issue_description,
                "timestamp": datetime.now().isoformat(),
                "related_logs_found": search_result["count"],
                "recent_errors": errors["count"],
                "anomalies_detected": anomalies["anomalies_detected"],
                "key_findings": self._analyze_findings(search_result, errors, anomalies),
                "next_steps": self._suggest_next_steps(search_result, errors, anomalies)
            }

            self.logger.info(f"问题调查完成: 发现{search_result['count']}条相关日志")
            return investigation

        except Exception as e:
            self.logger.error("问题调查失败", exc_info=True)
            raise

    def _extract_keywords(self, description):
        """从描述中提取关键词"""
        # 简化实现
        keywords = []
        words = description.lower().split()
        for word in words:
            if len(word) > 3 and word not in ["this", "that", "with", "from", "have", "been"]:
                keywords.append(word)
        return " ".join(keywords[:3])  # 返回前3个关键词

    def _calculate_health_score(self, status, errors, error_analysis):
        """计算健康分数"""
        # 简化实现
        score = 100

        # 根据错误数量扣分
        if errors.get("count", 0) > 10:
            score -= 20
        elif errors.get("count", 0) > 5:
            score -= 10

        # 根据错误趋势扣分
        if error_analysis.get("total_errors", 0) > 50:
            score -= 30
        elif error_analysis.get("total_errors", 0) > 20:
            score -= 15

        # 确保分数在0-100之间
        return max(0, min(100, score))

    def _generate_recommendations(self, status, errors, error_analysis):
        """生成建议"""
        recommendations = []

        if errors.get("count", 0) > 10:
            recommendations.append("错误数量较多，建议立即检查系统状态")

        if error_analysis.get("total_errors", 0) > 50:
            recommendations.append("24小时内错误数量超过50个，需要紧急处理")

        top_error_app = error_analysis.get("top_error_app")
        if top_error_app and top_error_app != "none":
            recommendations.append(f"应用 '{top_error_app}' 错误最多，建议优先检查")

        if not recommendations:
            recommendations.append("系统运行正常，保持当前监控配置")

        return recommendations

    def _analyze_findings(self, search_result, errors, anomalies):
        """分析调查结果"""
        findings = []

        if search_result["count"] > 0:
            findings.append(f"找到 {search_result['count']} 条相关日志")

        if errors["count"] > 0:
            findings.append(f"发现 {errors['count']} 个错误")

        if anomalies["anomalies_detected"] > 0:
            findings.append(f"检测到 {anomalies['anomalies_detected']} 个异常模式")

        if not findings:
            findings.append("未发现明显问题")

        return findings

    def _suggest_next_steps(self, search_result, errors, anomalies):
        """建议下一步"""
        steps = []

        if errors["count"] > 0:
            steps.append("1. 查看错误详情，确定根本原因")
            steps.append("2. 检查相关服务的健康状态")

        if anomalies["anomalies_detected"] > 0:
            steps.append("3. 调查检测到的异常模式")
            steps.append("4. 考虑调整告警阈值")

        if search_result["count"] > 0:
            steps.append("5. 分析相关日志的时间序列")

        if not steps:
            steps.append("1. 继续监控系统状态")
            steps.append("2. 定期运行健康检查")

        return steps

# ============================================
# 第六部分：演示MCP日志服务
# ============================================

print("\n" + "=" * 50)
print("第六部分：演示MCP日志服务")
print("=" * 50)

async def demonstrate_mcp_logging():
    """演示MCP日志服务"""

    print("\n开始演示MCP日志服务...")

    # 1. 创建MCP客户端
    print("\n1. 创建MCP客户端...")
    client = MCPClient("http://localhost:8080/mcp")
    await client.connect()

    # 2. 发现可用工具和资源
    print("\n2. 发现可用工具和资源...")
    tools = await client.discover_tools()
    resources = await client.discover_resources()

    print(f"   发现工具: {len(tools)} 个")
    for tool in tools[:3]:  # 显示前3个
        print(f"     - {tool['name']}: {tool['description']}")

    print(f"   发现资源: {len(resources)} 个")
    for resource in resources:
        print(f"     - {resource['uri']}: {resource['description']}")

    # 3. 调用工具示例
    print("\n3. 调用工具示例...")

    # 查询最近错误
    print("   调用 query_logs_by_level...")
    error_logs = await client.call_tool("query_logs_by_level", {
        "level": "ERROR",
        "limit": 5
    })
    print(f"   找到 {error_logs['count']} 个错误日志")

    # 搜索日志
    print("   调用 search_logs...")
    search_results = await client.call_tool("search_logs", {
        "keyword": "timeout",
        "fields": ["message"],
        "limit": 5
    })
    print(f"   搜索到 {search_results['count']} 条相关日志")

    # 4. 读取资源示例
    print("\n4. 读取资源示例...")

    # 读取系统状态
    print("   读取系统状态资源...")
    system_status = await client.read_resource("mcp://logs/system/status")
    print(f"   系统状态: {system_status['status']}, "
          f"运行时间: {system_status['uptime']}")

    # 5. AI代理分析演示
    print("\n5. AI代理分析演示...")
    ai_analyst = AILogAnalyst(client)

    # 分析系统健康
    print("   分析系统健康状态...")
    health_report = await ai_analyst.analyze_system_health()
    print(f"   健康分数: {health_report['overall_health']}/100")

    # 调查问题
    print("   调查问题: '用户反映登录缓慢'...")
    investigation = await ai_analyst.investigate_issue("用户反映登录缓慢")
    print(f"   调查结果: {len(investigation['key_findings'])} 个发现")
    for finding in investigation['key_findings'][:2]:
        print(f"     - {finding}")

    print("\nMCP日志服务演示完成!")

# 运行演示
print("\n运行MCP演示（模拟）...")

# 由于这是演示代码，我们直接运行模拟逻辑
try:
    # 创建事件循环并运行演示
    import asyncio
    asyncio.run(demonstrate_mcp_logging())
except RuntimeError:
    # 如果已经有事件循环，使用不同的方式
    print("(注: 在交互式环境中，需要手动运行演示代码)")

# ============================================
# 第七部分：MCP服务部署和配置
# ============================================

print("\n" + "=" * 50)
print("第七部分：MCP服务部署和配置")
print("=" * 50)

class MCPDeploymentGuide:
    """MCP服务部署指南"""

    @staticmethod
    def print_deployment_guide():
        """打印部署指南"""

        print("\nMCP日志服务部署指南")
        print("=" * 60)

        print("""
1. 环境准备
   - Python 3.8+
   - 安装依赖: pip install mcp fastapi uvicorn
   - 配置日志存储（Elasticsearch、文件系统等）

2. 服务实现步骤
   a. 创建MCP服务器类
   b. 注册日志查询工具
   c. 注册监控资源
   d. 实现工具逻辑
   e. 配置HTTP端点

3. 配置示例 (server.py)
""")

        server_code = """
from fastapi import FastAPI
from mcp.server import MCPServer
from mcp.server.fastapi import FastAPIServer
import uvicorn

# 创建MCP服务器
server = MCPServer("log-service")

# 注册工具
@server.tool()
async def query_logs(start_time: str, end_time: str, level: str = None):
    \"\"\"查询日志\"\"\"
    # 实现查询逻辑
    return {"logs": [], "count": 0}

# 注册资源
@server.resource("logs://system/status")
async def get_system_status():
    \"\"\"获取系统状态\"\"\"
    return {"status": "healthy"}

# 创建FastAPI应用
app = FastAPI()
mcp_app = FastAPIServer(server)

# 挂载MCP端点
app.mount("/mcp", mcp_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""

        print(server_code)

        print("""
4. Claude Desktop 配置 (.claude_desktop_config.json)
""")

        claude_config = """
{
  "mcpServers": {
    "log-service": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "LOG_STORAGE_URL": "http://localhost:9200"
      }
    }
  }
}
"""

        print(claude_config)

        print("""
5. 测试服务
   - 启动服务: python server.py
   - 测试工具调用
   - 验证资源访问
   - 集成到Claude Desktop

6. 生产部署考虑
   - 使用gunicorn/uwsgi部署
   - 配置反向代理（Nginx）
   - 设置SSL/TLS加密
   - 实施身份验证
   - 监控服务健康
""")

    @staticmethod
    def generate_docker_compose():
        """生成Docker Compose配置"""

        print("\nDocker Compose 配置示例 (docker-compose.yml):")

        docker_compose = """
version: '3.8'

services:
  # MCP日志服务
  mcp-log-service:
    build: .
    ports:
      - "8080:8080"
    environment:
      - LOG_STORAGE_URL=http://elasticsearch:9200
      - LOG_LEVEL=INFO
    depends_on:
      - elasticsearch
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  # Elasticsearch
  elasticsearch:
    image: elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    restart: unless-stopped

  # Kibana (可选)
  kibana:
    image: kibana:8.12.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    restart: unless-stopped

volumes:
  es_data:
"""

        print(docker_compose)

# 显示部署指南
MCPDeploymentGuide.print_deployment_guide()
MCPDeploymentGuide.generate_docker_compose()

# ============================================
# 第八部分：知识点总结
# ============================================

print("\n" + "=" * 50)
print("知识点总结")
print("=" * 50)

summary = """
必须背下来的知识点：
1. MCP协议基础 - 工具、资源、服务器的概念
2. MCP服务器实现 - 注册工具和资源的方法
3. MCP客户端使用 - 发现和调用工具的流程
4. AI代理集成模式 - 如何使用MCP增强AI能力

需要熟悉掌握的知识点：
1. 日志查询工具设计 - 时间范围、级别、关键词搜索
2. 系统监控资源设计 - 状态、统计、告警信息
3. 异步MCP服务器实现 - 支持异步工具调用
4. 错误处理和日志记录 - MCP服务中的异常管理

了解即可的知识点：
1. MCP协议扩展 - 自定义工具和资源类型
2. 性能优化技巧 - 缓存、批处理、连接池
3. 安全考虑 - 身份验证、授权、数据保护
4. 多服务集成 - 多个MCP服务的协同工作
"""

print(summary)

print("\n" + "=" * 50)
print("MCP日志服务学习完成！")
print("下一步：学习云原生日志和高级监控")
print("=" * 50)