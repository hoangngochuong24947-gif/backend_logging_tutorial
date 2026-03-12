"""
后端日志教学 - 高级层：云原生日志
文件名：03_cloud_native_logging.py
功能：学习云原生环境下的日志最佳实践和工具

教学目标：
1. 掌握容器化环境中的日志收集
2. 学习Kubernetes日志架构
3. 了解无服务器(Serverless)日志
4. 掌握云原生监控和告警
"""

import logging
import logging.config
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import threading
import queue
import random
import socket
import struct
import gzip
import io

print("=" * 80)
print("云原生日志")
print("=" * 80)

# ============================================
# 第一部分：容器日志基础
# ============================================

print("\n" + "=" * 50)
print("第一部分：容器日志基础")
print("=" * 50)

class ContainerLogSimulator:
    """容器日志模拟器"""

    def __init__(self, container_id, image_name, namespace="default"):
        self.container_id = container_id
        self.image_name = image_name
        self.namespace = namespace
        self.pod_name = f"pod-{container_id[:8]}"
        self.node_name = f"node-{random.randint(1, 5)}"
        self.logger = logging.getLogger(f'container.{container_id}')

        print(f"初始化容器日志模拟器: {container_id} ({image_name})")

    def generate_stdout_log(self, message, stream="stdout"):
        """生成标准输出日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "container_id": self.container_id,
            "pod": self.pod_name,
            "namespace": self.namespace,
            "node": self.node_name,
            "image": self.image_name,
            "stream": stream,
            "log": message,
            "labels": {
                "app": self.image_name.split("/")[-1].split(":")[0],
                "environment": self.namespace
            }
        }

        # 不同stream使用不同级别
        if stream == "stderr":
            self.logger.error(json.dumps(log_entry, ensure_ascii=False))
        else:
            self.logger.info(json.dumps(log_entry, ensure_ascii=False))

        return log_entry

    def generate_application_log(self, level, message, **extra):
        """生成应用日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "container_id": self.container_id,
            "pod": self.pod_name,
            "namespace": self.namespace,
            "level": level,
            "message": message,
            "service": self.image_name,
            "kubernetes": {
                "container_name": self.image_name.split("/")[-1],
                "namespace_name": self.namespace,
                "pod_name": self.pod_name,
                "pod_id": f"pod-{self.container_id}",
                "labels": {
                    "app": self.image_name.split("/")[-1].split(":")[0],
                    "version": "v1.0"
                }
            }
        }

        log_entry.update(extra)

        # 记录到相应级别
        if level == "ERROR":
            self.logger.error(json.dumps(log_entry, ensure_ascii=False))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_entry, ensure_ascii=False))
        else:
            self.logger.info(json.dumps(log_entry, ensure_ascii=False))

        return log_entry

    def generate_lifecycle_event(self, event_type, reason, message):
        """生成生命周期事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": "lifecycle",
            "event": event_type,
            "reason": reason,
            "message": message,
            "container_id": self.container_id,
            "pod": self.pod_name,
            "namespace": self.namespace,
            "source": {
                "component": "kubelet",
                "host": self.node_name
            },
            "count": 1,
            "first_timestamp": datetime.now().isoformat(),
            "last_timestamp": datetime.now().isoformat()
        }

        self.logger.info(json.dumps(event, ensure_ascii=False))
        return event

# 配置容器日志
print("\n配置容器日志输出...")

CONTAINER_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'logging.Formatter',
            'format': '%(message)s'
        }
    },
    'handlers': {
        'container_file': {
            'class': 'logging.FileHandler',
            'filename': 'container_logs.json',
            'level': 'INFO',
            'formatter': 'json',
            'encoding': 'utf-8'
        },
        'stdout': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'json',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'container': {
            'handlers': ['container_file', 'stdout'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

logging.config.dictConfig(CONTAINER_LOGGING_CONFIG)

# 模拟多个容器
print("\n模拟容器日志生成...")

containers = [
    ContainerLogSimulator(f"c{i:08x}", f"app-service:v1.{i}", "production")
    for i in range(1, 4)
]

containers.append(ContainerLogSimulator("db001234", "postgres:14", "production"))
containers.append(ContainerLogSimulator("redis5678", "redis:7", "production"))

# 生成各种日志
for i in range(10):
    container = random.choice(containers)

    # 生成不同类型的日志
    log_type = random.choice(['stdout', 'stderr', 'app', 'event'])

    if log_type == 'stdout':
        container.generate_stdout_log(
            f"处理请求 {i}, 耗时 {random.randint(50, 500)}ms",
            stream="stdout"
        )
    elif log_type == 'stderr':
        if random.random() < 0.3:
            container.generate_stdout_log(
                f"错误: 资源不足, 内存使用率 {random.randint(85, 99)}%",
                stream="stderr"
            )
    elif log_type == 'app':
        level = random.choice(['INFO', 'WARNING', 'ERROR'])
        container.generate_application_log(
            level,
            f"业务操作 {i}: {'成功' if level != 'ERROR' else '失败'}",
            user_id=f"user_{random.randint(1, 1000)}",
            endpoint=f"/api/{random.choice(['users', 'products', 'orders'])}",
            response_time=random.randint(100, 2000)
        )
    else:  # event
        if random.random() < 0.2:
            container.generate_lifecycle_event(
                event_type=random.choice(['Normal', 'Warning']),
                reason=random.choice(['Started', 'Killing', 'Pulling', 'Created']),
                message=random.choice([
                    "容器启动成功",
                    "容器终止请求",
                    "拉取镜像成功",
                    "容器创建完成"
                ])
            )

print("\n容器日志已生成到 container_logs.json")

# ============================================
# 第二部分：Kubernetes日志架构
# ============================================

print("\n" + "=" * 50)
print("第二部分：Kubernetes日志架构")
print("=" * 50)

class KubernetesLoggingArchitecture:
    """Kubernetes日志架构说明"""

    @staticmethod
    def print_architecture():
        """打印架构图"""
        print("\nKubernetes日志收集架构:")
        print("=" * 60)

        architecture = """
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │    Pod 1    │  │    Pod 2    │  │    Pod N    │       │
│  │  ┌────────┐ │  │  ┌────────┐ │  │  ┌────────┐ │       │
│  │  │Container│ │  │  │Container│ │  │  │Container│ │       │
│  │  │  STDOUT │─┼──┼─►│  STDOUT │─┼──┼─►│  STDOUT │ │       │
│  │  │  STDERR │ │  │  │  STDERR │ │  │  │  STDERR │ │       │
│  │  └────────┘ │  │  └────────┘ │  │  └────────┘ │       │
│  └────────────┘  └────────────┘  └────────────┘       │
│            │               │               │           │
│            └───────────────┼───────────────┘           │
│                            ▼                           │
│                   ┌─────────────────┐                 │
│                   │  Node Level     │                 │
│                   │  Logging Agent  │                 │
│                   │  (Fluentd/      │                 │
│                   │   Fluent Bit)   │                 │
│                   └─────────────────┘                 │
│                            │                           │
│                            ▼                           │
│                   ┌─────────────────┐                 │
│                   │  Log Aggregator │                 │
│                   │  (Logstash/     │                 │
│                   │   Vector)       │                 │
│                   └─────────────────┘                 │
│                            │                           │
│                            ▼                           │
│                 ┌─────────────────────┐               │
│                 │  Storage & Analysis │               │
│                 │  • Elasticsearch    │               │
│                 │  • Loki             │               │
│                 │  • Cloud Storage    │               │
│                 └─────────────────────┘               │
│                            │                           │
│                            ▼                           │
│                 ┌─────────────────────┐               │
│                 │  Visualization      │               │
│                 │  • Kibana           │               │
│                 │  • Grafana          │               │
│                 │  • Cloud Console    │               │
│                 └─────────────────────┘               │
└─────────────────────────────────────────────────────────┘
        """

        print(architecture)

        print("\n组件说明:")
        print("1. 容器层面:")
        print("   - 应用写入STDOUT/STDERR")
        print("   - 使用结构化日志格式(JSON)")
        print("   - 避免直接写入文件")

        print("\n2. 节点层面(Node Level):")
        print("   - DaemonSet部署日志代理")
        print("   - 收集/var/log/containers/日志")
        print("   - 添加Kubernetes元数据")
        print("   - 支持日志轮转和缓冲")

        print("\n3. 日志聚合(Log Aggregator):")
        print("   - 集中处理来自所有节点的日志")
        print("   - 解析、过滤、丰富日志")
        print("   - 路由到不同的存储后端")

        print("\n4. 存储和分析(Storage & Analysis):")
        print("   - Elasticsearch: 全文搜索和分析")
        print("   - Loki: 轻量级日志聚合(Grafana Labs)")
        print("   - 云存储: S3, GCS, Blob Storage")

        print("\n5. 可视化(Visualization):")
        print("   - Kibana: Elasticsearch的可视化")
        print("   - Grafana: 多数据源仪表板")
        print("   - 云控制台: AWS CloudWatch, GCP Logging")

    @staticmethod
    def generate_kubernetes_manifests():
        """生成Kubernetes配置文件"""
        import yaml
        import os

        manifests_dir = 'kubernetes_manifests'
        os.makedirs(manifests_dir, exist_ok=True)

        # 1. Fluent Bit DaemonSet
        fluentbit_daemonset = {
            'apiVersion': 'apps/v1',
            'kind': 'DaemonSet',
            'metadata': {
                'name': 'fluent-bit',
                'namespace': 'logging',
                'labels': {
                    'app': 'fluent-bit',
                    'version': 'v2.2'
                }
            },
            'spec': {
                'selector': {
                    'matchLabels': {
                        'app': 'fluent-bit'
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': 'fluent-bit'
                        }
                    },
                    'spec': {
                        'serviceAccountName': 'fluent-bit',
                        'containers': [{
                            'name': 'fluent-bit',
                            'image': 'fluent/fluent-bit:2.2',
                            'resources': {
                                'limits': {
                                    'memory': '200Mi',
                                    'cpu': '200m'
                                },
                                'requests': {
                                    'memory': '100Mi',
                                    'cpu': '100m'
                                }
                            },
                            'volumeMounts': [
                                {
                                    'name': 'varlog',
                                    'mountPath': '/var/log'
                                },
                                {
                                    'name': 'varlibdockercontainers',
                                    'mountPath': '/var/lib/docker/containers',
                                    'readOnly': True
                                },
                                {
                                    'name': 'fluent-bit-config',
                                    'mountPath': '/fluent-bit/etc/'
                                }
                            ]
                        }],
                        'volumes': [
                            {
                                'name': 'varlog',
                                'hostPath': {
                                    'path': '/var/log'
                                }
                            },
                            {
                                'name': 'varlibdockercontainers',
                                'hostPath': {
                                    'path': '/var/lib/docker/containers'
                                }
                            },
                            {
                                'name': 'fluent-bit-config',
                                'configMap': {
                                    'name': 'fluent-bit-config'
                                }
                            }
                        ],
                        'tolerations': [{
                            'key': 'node-role.kubernetes.io/master',
                            'effect': 'NoSchedule'
                        }]
                    }
                }
            }
        }

        with open(f'{manifests_dir}/fluentbit-daemonset.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(fluentbit_daemonset, f, default_flow_style=False)

        # 2. Fluent Bit ConfigMap
        fluentbit_config = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'fluent-bit-config',
                'namespace': 'logging',
                'labels': {
                    'app': 'fluent-bit'
                }
            },
            'data': {
                'fluent-bit.conf': """
[SERVICE]
    Flush        5
    Daemon       Off
    Log_Level    info
    Parsers_File parsers.conf
    HTTP_Server  On
    HTTP_Listen  0.0.0.0
    HTTP_Port    2020

[INPUT]
    Name              tail
    Tag               kube.*
    Path              /var/log/containers/*.log
    Parser            docker
    DB                /var/log/flb_kube.db
    Mem_Buf_Limit     5MB
    Skip_Long_Lines   On
    Refresh_Interval  10

[FILTER]
    Name                kubernetes
    Match               kube.*
    Kube_URL            https://kubernetes.default.svc:443
    Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
    Kube_Tag_Prefix     kube.var.log.containers.
    Merge_Log           On
    Merge_Log_Key       log_processed
    Keep_Log            Off
    K8S-Logging.Parser  On
    K8S-Logging.Exclude Off

[OUTPUT]
    Name            es
    Match           *
    Host            elasticsearch.logging.svc
    Port            9200
    Logstash_Format On
    Logstash_Prefix fluent-bit
    Replace_Dots    On
    Retry_Limit     False
"""
            }
        }

        with open(f'{manifests_dir}/fluentbit-config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(fluentbit_config, f, default_flow_style=False)

        # 3. ServiceAccount和ClusterRole
        rbac_manifest = {
            'apiVersion': 'v1',
            'kind': 'ServiceAccount',
            'metadata': {
                'name': 'fluent-bit',
                'namespace': 'logging'
            }
        }

        with open(f'{manifests_dir}/serviceaccount.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(rbac_manifest, f, default_flow_style=False)

        print(f"\nKubernetes配置文件已生成到 {manifests_dir}/ 目录:")
        print(f"  - fluentbit-daemonset.yaml: Fluent Bit DaemonSet")
        print(f"  - fluentbit-config.yaml: Fluent Bit配置")
        print(f"  - serviceaccount.yaml: ServiceAccount")

# 展示Kubernetes日志架构
KubernetesLoggingArchitecture.print_architecture()
KubernetesLoggingArchitecture.generate_kubernetes_manifests()

# ============================================
# 第三部分：无服务器(Serverless)日志
# ============================================

print("\n" + "=" * 50)
print("第三部分：无服务器(Serverless)日志")
print("=" * 50)

class ServerlessLogging:
    """无服务器函数日志处理"""

    def __init__(self, platform="aws"):
        self.platform = platform
        self.logger = logging.getLogger('serverless')
        print(f"初始化无服务器日志: {platform}")

    def generate_lambda_log(self, function_name, request_id, message, level="INFO", **extra):
        """生成AWS Lambda日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "platform": "aws",
            "service": "lambda",
            "function_name": function_name,
            "function_version": "$LATEST",
            "request_id": request_id,
            "message": message,
            "memory_size": "1024",
            "memory_used": str(random.randint(100, 900)),
            "init_duration": random.randint(100, 500),
            "duration": random.randint(10, 5000)
        }

        log_entry.update(extra)

        # 添加平台特定字段
        if self.platform == "aws":
            log_entry["log_stream_name"] = f"2024/01/01/[$LATEST]{request_id[:8]}"
            log_entry["log_group_name"] = f"/aws/lambda/{function_name}"
        elif self.platform == "azure":
            log_entry["invocation_id"] = request_id
            log_entry["function_invocation_id"] = request_id

        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        return log_entry

    def generate_cold_start_log(self, function_name):
        """生成冷启动日志"""
        return self.generate_lambda_log(
            function_name=function_name,
            request_id=str(uuid.uuid4()),
            message="Cold Start",
            level="INFO",
            cold_start=True,
            init_duration=random.randint(500, 2000)
        )

    def generate_error_log(self, function_name, error_type, error_message):
        """生成错误日志"""
        return self.generate_lambda_log(
            function_name=function_name,
            request_id=str(uuid.uuid4()),
            message=f"{error_type}: {error_message}",
            level="ERROR",
            error_type=error_type,
            error_message=error_message,
            stack_trace="Traceback (most recent call last):\n  ..."
        )

    def generate_performance_log(self, function_name, duration, memory_used):
        """生成性能日志"""
        return self.generate_lambda_log(
            function_name=function_name,
            request_id=str(uuid.uuid4()),
            message=f"Function execution completed",
            level="INFO",
            duration=duration,
            memory_used=memory_used,
            billed_duration=max(100, duration // 100 * 100),
            billed_memory=max(128, memory_used // 64 * 64)
        )

    @staticmethod
    def print_best_practices():
        """打印最佳实践"""
        print("\n无服务器日志最佳实践:")
        print("=" * 60)

        print("""
1. 结构化日志输出
   - 始终使用JSON格式
   - 包含请求ID和函数上下文
   - 添加自定义业务字段

2. 控制日志级别
   - 生产环境: INFO及以上
   - 开发环境: DEBUG及以上
   - 使用环境变量控制级别

3. 性能考虑
   - 避免同步日志I/O
   - 使用批量写入
   - 控制日志量，避免成本激增

4. 错误处理
   - 记录完整错误信息
   - 包含堆栈跟踪
   - 添加错误分类和代码

5. 监控和告警
   - 设置错误率监控
   - 监控冷启动频率
   - 配置内存和超时告警

6. 成本优化
   - 采样DEBUG日志
   - 定期清理旧日志
   - 使用云原生日志服务
""")

# 演示无服务器日志
print("\n演示无服务器日志...")

# 配置无服务器日志
serverless_logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'logging.Formatter',
            'format': '%(message)s'
        }
    },
    'handlers': {
        'serverless_file': {
            'class': 'logging.FileHandler',
            'filename': 'serverless_logs.json',
            'level': 'INFO',
            'formatter': 'json',
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'serverless': {
            'handlers': ['serverless_file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

logging.config.dictConfig(serverless_logging_config)

# 生成示例日志
serverless = ServerlessLogging("aws")

functions = ["order-processor", "user-authenticator", "payment-handler", "email-sender"]

for i in range(20):
    func = random.choice(functions)
    request_id = str(uuid.uuid4())

    # 不同类型的日志
    if i % 10 == 0:
        # 冷启动
        serverless.generate_cold_start_log(func)
    elif random.random() < 0.1:
        # 错误
        error_type = random.choice(["ValidationError", "TimeoutError", "DatabaseError"])
        serverless.generate_error_log(func, error_type, "处理请求时发生错误")
    else:
        # 正常执行
        duration = random.randint(50, 1000)
        memory_used = random.randint(200, 800)
        serverless.generate_performance_log(func, duration, memory_used)

print("无服务器日志已生成到 serverless_logs.json")

# 显示最佳实践
ServerlessLogging.print_best_practices()

# ============================================
# 第四部分：云原生监控和告警
# ============================================

print("\n" + "=" * 50)
print("第四部分：云原生监控和告警")
print("=" * 50)

class CloudNativeMonitoring:
    """云原生监控系统"""

    def __init__(self):
        self.metrics = {}
        self.alerts = {}
        self.logger = logging.getLogger('cloud.monitoring')
        print("初始化云原生监控系统")

    def record_metric(self, metric_name, value, labels=None, timestamp=None):
        """记录指标"""
        timestamp = timestamp or datetime.now().isoformat()
        labels = labels or {}

        metric_key = f"{metric_name}_{hash(frozenset(labels.items()))}"

        if metric_key not in self.metrics:
            self.metrics[metric_key] = {
                'name': metric_name,
                'labels': labels,
                'values': [],
                'summary': {
                    'count': 0,
                    'sum': 0,
                    'min': float('inf'),
                    'max': float('-inf'),
                    'avg': 0
                }
            }

        metric = self.metrics[metric_key]
        metric['values'].append({
            'timestamp': timestamp,
            'value': value
        })

        # 更新统计
        metric['summary']['count'] += 1
        metric['summary']['sum'] += value
        metric['summary']['min'] = min(metric['summary']['min'], value)
        metric['summary']['max'] = max(metric['summary']['max'], value)
        metric['summary']['avg'] = metric['summary']['sum'] / metric['summary']['count']

        # 记录指标日志
        self.logger.info(json.dumps({
            'type': 'metric',
            'timestamp': timestamp,
            'metric': metric_name,
            'value': value,
            'labels': labels
        }, ensure_ascii=False))

        return metric_key

    def check_alert_rules(self, rule_name, metric_name, condition, threshold, labels=None):
        """检查告警规则"""
        labels = labels or {}
        metric_key = f"{metric_name}_{hash(frozenset(labels.items()))}"

        if metric_key not in self.metrics:
            return None

        metric = self.metrics[metric_key]
        current_value = metric['values'][-1]['value'] if metric['values'] else 0

        # 检查条件
        triggered = False
        if condition == 'gt' and current_value > threshold:
            triggered = True
        elif condition == 'gte' and current_value >= threshold:
            triggered = True
        elif condition == 'lt' and current_value < threshold:
            triggered = True
        elif condition == 'lte' and current_value <= threshold:
            triggered = True
        elif condition == 'eq' and current_value == threshold:
            triggered = True

        if triggered:
            alert_id = f"alert_{rule_name}_{int(time.time() * 1000)}"
            alert = {
                'id': alert_id,
                'rule': rule_name,
                'metric': metric_name,
                'condition': condition,
                'threshold': threshold,
                'current_value': current_value,
                'labels': labels,
                'triggered_at': datetime.now().isoformat(),
                'status': 'firing'
            }

            if alert_id not in self.alerts:
                self.alerts[alert_id] = alert

                # 记录告警日志
                self.logger.error(json.dumps({
                    'type': 'alert',
                    'timestamp': datetime.now().isoformat(),
                    'alert': alert
                }, ensure_ascii=False))

                # 模拟发送通知
                self._send_alert_notification(alert)

            return alert

        return None

    def _send_alert_notification(self, alert):
        """发送告警通知（模拟）"""
        print(f"🔔 告警触发: {alert['rule']}")
        print(f"   指标: {alert['metric']} {alert['condition']} {alert['threshold']}")
        print(f"   当前值: {alert['current_value']}")
        print(f"   时间: {alert['triggered_at']}")
        print()

    def get_metrics_summary(self):
        """获取指标摘要"""
        summary = {}
        for metric_key, metric in self.metrics.items():
            summary[metric['name']] = {
                'count': metric['summary']['count'],
                'avg': metric['summary']['avg'],
                'min': metric['summary']['min'],
                'max': metric['summary']['max'],
                'last_value': metric['values'][-1]['value'] if metric['values'] else None
            }
        return summary

    def get_active_alerts(self):
        """获取活跃告警"""
        return [alert for alert in self.alerts.values() if alert['status'] == 'firing']

# 演示云原生监控
print("\n演示云原生监控系统...")

monitoring = CloudNativeMonitoring()

# 定义监控指标
metrics_to_monitor = [
    ("request_latency_ms", {"endpoint": "/api/users", "method": "GET"}),
    ("error_rate_percent", {"service": "auth-service"}),
    ("memory_usage_percent", {"pod": "auth-service-abc123"}),
    ("cpu_usage_percent", {"node": "node-1"}),
    ("disk_usage_percent", {"volume": "data-volume"})
]

# 定义告警规则
alert_rules = [
    {"name": "high_latency", "metric": "request_latency_ms", "condition": "gt", "threshold": 1000},
    {"name": "high_error_rate", "metric": "error_rate_percent", "condition": "gt", "threshold": 5},
    {"name": "high_memory_usage", "metric": "memory_usage_percent", "condition": "gt", "threshold": 90},
    {"name": "high_cpu_usage", "metric": "cpu_usage_percent", "condition": "gt", "threshold": 80}
]

print("模拟监控数据收集（30秒）...")

# 模拟数据收集
for i in range(30):
    timestamp = datetime.now().isoformat()

    for metric_name, labels in metrics_to_monitor:
        # 生成模拟值
        if metric_name == "request_latency_ms":
            value = random.randint(100, 1500)  # 100-1500ms
        elif metric_name == "error_rate_percent":
            value = random.uniform(0.1, 10.0)  # 0.1-10%
        elif metric_name == "memory_usage_percent":
            value = random.randint(60, 95)  # 60-95%
        elif metric_name == "cpu_usage_percent":
            value = random.randint(50, 85)  # 50-85%
        else:
            value = random.randint(70, 98)  # 70-98%

        # 记录指标
        monitoring.record_metric(metric_name, value, labels, timestamp)

    # 检查告警规则
    for rule in alert_rules:
        monitoring.check_alert_rules(
            rule_name=rule["name"],
            metric_name=rule["metric"],
            condition=rule["condition"],
            threshold=rule["threshold"]
        )

    # 每秒一次
    time.sleep(1)

print("\n监控数据收集完成")

# 显示监控结果
print("\n指标摘要:")
summary = monitoring.get_metrics_summary()
for metric_name, stats in summary.items():
    print(f"  {metric_name}:")
    print(f"    计数: {stats['count']}, 平均: {stats['avg']:.2f}, "
          f"最小: {stats['min']:.2f}, 最大: {stats['max']:.2f}")

print("\n活跃告警:")
active_alerts = monitoring.get_active_alerts()
if active_alerts:
    for alert in active_alerts:
        print(f"  [{alert['rule']}] {alert['metric']} = {alert['current_value']} "
              f"{alert['condition']} {alert['threshold']}")
else:
    print("  无活跃告警")

# ============================================
# 第五部分：云服务商日志服务比较
# ============================================

print("\n" + "=" * 50)
print("第五部分：云服务商日志服务比较")
print("=" * 50)

class CloudLoggingServices:
    """云服务商日志服务比较"""

    @staticmethod
    def print_comparison():
        """打印比较表"""
        print("\n云服务商日志服务比较:")
        print("=" * 80)

        comparison = """
+------------------+------------------+------------------+------------------+
|     特性         |    AWS CloudWatch |  GCP Cloud Logging | Azure Monitor   |
+------------------+------------------+------------------+------------------+
| 日志收集         | CloudWatch Agent | Logging Agent    | Azure Monitor   |
|                  | Fluent Bit       | Fluentd          | Agent           |
+------------------+------------------+------------------+------------------+
| 日志查询         | CloudWatch       | Cloud Logging    | Log Analytics   |
|                  | Insights         | UI               | (KQL)           |
+------------------+------------------+------------------+------------------+
| 日志分析         | Logs Insights    | Log Analytics    | Log Analytics   |
|                  |                  | BigQuery集成     |                 |
+------------------+------------------+------------------+------------------+
| 指标监控         | CloudWatch       | Cloud Monitoring | Azure Monitor   |
|                  | Metrics          |                  | Metrics         |
+------------------+------------------+------------------+------------------+
| 告警             | CloudWatch       | Cloud Monitoring | Azure Monitor   |
|                  | Alarms           | Alerts           | Alerts          |
+------------------+------------------+------------------+------------------+
| 仪表板           | CloudWatch       | Cloud Monitoring | Azure Monitor   |
|                  | Dashboards       | Dashboards       | Dashboards      |
+------------------+------------------+------------------+------------------+
| 成本模型         | 按日志量+API调用   | 按日志量+扫描数据  | 按数据量+查询    |
+------------------+------------------+------------------+------------------+
| 数据保留         | 可配置(1天-10年)  | 可配置(1天-10年)  | 可配置(1天-2年)  |
+------------------+------------------+------------------+------------------+
| 第三方集成       | 支持多种集成      | 支持多种集成      | 支持多种集成     |
+------------------+------------------+------------------+------------------+
"""

        print(comparison)

        print("\n选择建议:")
        print("1. AWS环境: CloudWatch + CloudWatch Logs Insights")
        print("2. GCP环境: Cloud Logging + BigQuery + Cloud Monitoring")
        print("3. Azure环境: Azure Monitor + Log Analytics")
        print("4. 多云环境: 使用开源方案(ELK/Loki)或第三方服务(Datadog, Splunk)")

    @staticmethod
    def generate_cloud_configs():
        """生成云服务商配置示例"""
        import os
        configs_dir = 'cloud_configs'
        os.makedirs(configs_dir, exist_ok=True)

        # 1. AWS CloudWatch配置
        aws_config = {
            "logs": {
                "logs_collected": {
                    "files": {
                        "collect_list": [
                            {
                                "file_path": "/var/log/app/app.log",
                                "log_group_name": "/aws/ec2/app",
                                "log_stream_name": "{instance_id}",
                                "timezone": "UTC"
                            },
                            {
                                "file_path": "/var/log/app/error.log",
                                "log_group_name": "/aws/ec2/app/errors",
                                "log_stream_name": "{instance_id}"
                            }
                        ]
                    }
                },
                "log_stream_name": "application_logs",
                "force_flush_interval": 15
            },
            "metrics": {
                "metrics_collected": {
                    "statsd": {}
                },
                "append_dimensions": {
                    "InstanceId": "${aws:InstanceId}"
                }
            }
        }

        with open(f'{configs_dir}/aws_cloudwatch_config.json', 'w', encoding='utf-8') as f:
            json.dump(aws_config, f, indent=2, ensure_ascii=False)

        # 2. GCP Cloud Logging配置
        gcp_config = {
            "version": 1,
            "formatters": {
                "gcp": {
                    "()": "google.cloud.logging.handlers.CloudLoggingFormatter"
                }
            },
            "handlers": {
                "cloud_logging": {
                    "class": "google.cloud.logging.handlers.CloudLoggingHandler",
                    "client": {
                        "project": "my-project-id"
                    },
                    "formatter": "gcp",
                    "labels": {
                        "application": "my-app",
                        "environment": "production"
                    }
                }
            },
            "loggers": {
                "": {
                    "handlers": ["cloud_logging"],
                    "level": "INFO"
                }
            }
        }

        with open(f'{configs_dir}/gcp_logging_config.json', 'w', encoding='utf-8') as f:
            json.dump(gcp_config, f, indent=2, ensure_ascii=False)

        # 3. Azure Monitor配置
        azure_config = {
            "version": 1,
            "formatters": {
                "json": {
                    "()": "logging.Formatter",
                    "format": "%(message)s"
                }
            },
            "handlers": {
                "azure_monitor": {
                    "class": "opencensus.ext.azure.log_exporter.AzureLogHandler",
                    "connection_string": "InstrumentationKey=YOUR_INSTRUMENTATION_KEY",
                    "formatter": "json",
                    "export_interval": 15.0
                }
            },
            "loggers": {
                "": {
                    "handlers": ["azure_monitor"],
                    "level": "INFO"
                }
            }
        }

        with open(f'{configs_dir}/azure_monitor_config.json', 'w', encoding='utf-8') as f:
            json.dump(azure_config, f, indent=2, ensure_ascii=False)

        print(f"\n云服务商配置文件已生成到 {configs_dir}/ 目录:")
        print(f"  - aws_cloudwatch_config.json: AWS CloudWatch配置")
        print(f"  - gcp_logging_config.json: GCP Cloud Logging配置")
        print(f"  - azure_monitor_config.json: Azure Monitor配置")

# 显示云服务商比较
CloudLoggingServices.print_comparison()
CloudLoggingServices.generate_cloud_configs()

# ============================================
# 第六部分：知识点总结
# ============================================

print("\n" + "=" * 50)
print("知识点总结")
print("=" * 50)

summary = """
必须背下来的知识点：
1. 容器日志标准 - STDOUT/STDERR输出，避免文件日志
2. Kubernetes日志架构 - 节点代理→聚合器→存储→可视化
3. 无服务器日志特点 - 请求ID跟踪，冷启动记录，成本意识
4. 云原生监控四要素 - 指标(metrics)、日志(logs)、追踪(traces)、告警(alerts)

需要熟悉掌握的知识点：
1. Fluentd/Fluent Bit配置 - 容器日志收集和转发
2. 结构化日志格式 - 包含云原生元数据(Kubernetes标签等)
3. 多云日志策略 - 不同云服务商的日志服务比较
4. 成本优化技巧 - 日志采样、保留策略、存储分层

了解即可的知识点：
1. eBPF日志收集 - 内核级别的可观测性
2. 服务网格(Service Mesh)日志 - Istio、Linkerd的访问日志
3. GitOps日志管理 - 使用Git管理日志配置
4. 安全信息和事件管理(SIEM)集成
"""

print(summary)

print("\n" + "=" * 50)
print("云原生日志学习完成！")
print("下一步：进入项目层，创建完整的日志监控系统")
print("=" * 50)