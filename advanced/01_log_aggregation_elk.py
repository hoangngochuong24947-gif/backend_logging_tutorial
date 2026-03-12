"""
后端日志教学 - 高级层：日志聚合和ELK栈
文件名：01_log_aggregation_elk.py
功能：学习日志聚合、ELK栈集成和分布式日志系统

教学目标：
1. 掌握日志聚合的基本概念和架构
2. 学习ELK栈（Elasticsearch, Logstash, Kibana）的使用
3. 了解结构化日志和日志管道设计
4. 掌握分布式系统中的日志收集
"""

import logging
import logging.config
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, List
import threading
import queue
import socket
import struct
import gzip
import io

print("=" * 80)
print("日志聚合和ELK栈")
print("=" * 80)

# ============================================
# 第一部分：结构化日志生成器
# ============================================

print("\n" + "=" * 50)
print("第一部分：结构化日志生成器")
print("=" * 50)

class StructuredLogGenerator:
    """结构化日志生成器，模拟应用日志"""

    def __init__(self, app_name, environment="development"):
        self.app_name = app_name
        self.environment = environment
        self.logger = logging.getLogger(f'app.{app_name}')
        self.request_counter = 0

        print(f"初始化结构化日志生成器: app={app_name}, env={environment}")

    def generate_request_log(self, endpoint, method="GET", status_code=200,
                           user_id=None, duration_ms=None, **extra):
        """生成请求日志"""
        self.request_counter += 1

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "app": self.app_name,
            "environment": self.environment,
            "type": "request",
            "request_id": f"req_{self.request_counter:06d}",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms or random.randint(50, 500),
            "user_id": user_id or f"user_{random.randint(1, 1000)}",
            "source_ip": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "user_agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
            ])
        }

        # 添加额外字段
        log_entry.update(extra)

        # 根据状态码设置日志级别
        if status_code >= 500:
            log_entry["level"] = "ERROR"
        elif status_code >= 400:
            log_entry["level"] = "WARNING"

        # 记录日志
        if log_entry["level"] == "ERROR":
            self.logger.error(json.dumps(log_entry, ensure_ascii=False))
        elif log_entry["level"] == "WARNING":
            self.logger.warning(json.dumps(log_entry, ensure_ascii=False))
        else:
            self.logger.info(json.dumps(log_entry, ensure_ascii=False))

        return log_entry

    def generate_error_log(self, error_type, message, stack_trace=None, **extra):
        """生成错误日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "app": self.app_name,
            "environment": self.environment,
            "type": "error",
            "error_id": f"err_{int(time.time() * 1000)}",
            "error_type": error_type,
            "message": message,
            "stack_trace": stack_trace,
            "service": random.choice(["auth", "api", "database", "cache"])
        }

        # 添加额外字段
        log_entry.update(extra)

        self.logger.error(json.dumps(log_entry, ensure_ascii=False))
        return log_entry

    def generate_metric_log(self, metric_name, value, tags=None, **extra):
        """生成指标日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "app": self.app_name,
            "environment": self.environment,
            "type": "metric",
            "metric_name": metric_name,
            "value": value,
            "tags": tags or {},
            "unit": extra.get("unit", "count")
        }

        log_entry.update(extra)

        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        return log_entry

    def generate_business_log(self, action, entity, entity_id, details=None, **extra):
        """生成业务日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "app": self.app_name,
            "environment": self.environment,
            "type": "business",
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "details": details or {},
            "user_id": f"user_{random.randint(1, 1000)}",
            "session_id": f"session_{random.randint(1000, 9999)}"
        }

        log_entry.update(extra)

        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        return log_entry

# 配置结构化日志输出
print("\n配置结构化日志输出...")

STRUCTURED_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'logging.Formatter',
            'format': '%(message)s'  # 消息已经是JSON格式
        }
    },
    'handlers': {
        'json_file': {
            'class': 'logging.FileHandler',
            'filename': 'structured_app.log',
            'level': 'INFO',
            'formatter': 'json',
            'encoding': 'utf-8'
        },
        'json_console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'json',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'app': {
            'handlers': ['json_file', 'json_console'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

logging.config.dictConfig(STRUCTURED_LOGGING_CONFIG)

# 生成示例日志
print("\n生成结构化日志示例...")

log_generator = StructuredLogGenerator("ecommerce-api", "production")

# 生成各种类型的日志
for i in range(5):
    # 请求日志
    status = random.choice([200, 200, 200, 404, 500])
    log_generator.generate_request_log(
        endpoint=f"/api/products/{random.randint(1, 100)}",
        method=random.choice(["GET", "POST", "PUT", "DELETE"]),
        status_code=status,
        duration_ms=random.randint(100, 1000),
        product_id=random.randint(1, 1000),
        category=random.choice(["electronics", "clothing", "books"])
    )

    # 业务日志
    log_generator.generate_business_log(
        action=random.choice(["create", "update", "delete", "view"]),
        entity="order",
        entity_id=f"order_{random.randint(10000, 99999)}",
        details={
            "total_amount": random.randint(100, 10000),
            "items": random.randint(1, 10)
        }
    )

    # 指标日志
    log_generator.generate_metric_log(
        metric_name="request.latency",
        value=random.uniform(0.1, 2.0),
        tags={"endpoint": "/api/products", "method": "GET"},
        unit="seconds"
    )

    # 偶尔生成错误日志
    if random.random() < 0.2:
        log_generator.generate_error_log(
            error_type=random.choice(["DatabaseError", "TimeoutError", "ValidationError"]),
            message=random.choice([
                "数据库连接超时",
                "请求参数验证失败",
                "外部API调用失败"
            ]),
            stack_trace="Traceback (most recent call last):\n  ..."
        )

print("\n结构化日志已生成到 structured_app.log")

# ============================================
# 第二部分：日志收集器（Logstash模拟）
# ============================================

print("\n" + "=" * 50)
print("第二部分：日志收集器（Logstash模拟）")
print("=" * 50)

class LogCollector:
    """日志收集器，模拟Logstash功能"""

    def __init__(self, input_config, filter_config, output_config):
        """
        初始化日志收集器

        Args:
            input_config: 输入配置
            filter_config: 过滤器配置
            output_config: 输出配置
        """
        self.input_config = input_config
        self.filter_config = filter_config
        self.output_config = output_config
        self.log_queue = queue.Queue()
        self.running = False
        self.processed_count = 0

        print("初始化日志收集器...")
        print(f"  输入: {input_config['type']}")
        print(f"  过滤器: {len(filter_config)} 个")
        print(f"  输出: {output_config['type']}")

    def start(self):
        """启动收集器"""
        print("启动日志收集器...")
        self.running = True

        # 启动输入线程
        self.input_thread = threading.Thread(
            target=self._input_worker,
            name="InputWorker",
            daemon=True
        )
        self.input_thread.start()

        # 启动处理线程
        self.process_thread = threading.Thread(
            target=self._process_worker,
            name="ProcessWorker",
            daemon=True
        )
        self.process_thread.start()

        # 启动输出线程
        self.output_thread = threading.Thread(
            target=self._output_worker,
            name="OutputWorker",
            daemon=True
        )
        self.output_thread.start()

        print("日志收集器已启动")

    def stop(self):
        """停止收集器"""
        print("停止日志收集器...")
        self.running = False

        # 等待队列处理完成
        while not self.log_queue.empty():
            time.sleep(0.1)

        print(f"日志收集器已停止，共处理 {self.processed_count} 条日志")

    def _input_worker(self):
        """输入工作线程"""
        input_type = self.input_config['type']

        if input_type == 'file':
            self._file_input_worker()
        elif input_type == 'tcp':
            self._tcp_input_worker()
        elif input_type == 'udp':
            self._udp_input_worker()
        else:
            print(f"未知输入类型: {input_type}")

    def _file_input_worker(self):
        """文件输入工作线程"""
        filepath = self.input_config.get('path', 'structured_app.log')
        print(f"文件输入: 监控文件 {filepath}")

        try:
            # 模拟读取文件新增内容
            with open(filepath, 'r', encoding='utf-8') as f:
                # 读取现有内容
                lines = f.readlines()
                for line in lines:
                    if self.running:
                        self.log_queue.put({
                            'type': 'log_line',
                            'content': line.strip(),
                            'source': f'file:{filepath}',
                            'timestamp': time.time()
                        })
                    else:
                        break

                # 模拟持续监控（简化版本）
                while self.running and len(lines) < 20:
                    # 生成新日志行
                    fake_log = {
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'message': f'模拟日志行 {len(lines) + 1}',
                        'source': 'simulated'
                    }
                    self.log_queue.put({
                        'type': 'log_line',
                        'content': json.dumps(fake_log),
                        'source': f'file:{filepath}',
                        'timestamp': time.time()
                    })
                    lines.append(fake_log)
                    time.sleep(0.5)

        except Exception as e:
            print(f"文件输入错误: {e}")

    def _tcp_input_worker(self):
        """TCP输入工作线程"""
        host = self.input_config.get('host', '127.0.0.1')
        port = self.input_config.get('port', 5000)

        print(f"TCP输入: 监听 {host}:{port}")

        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((host, port))
            server.listen(5)
            server.settimeout(1)  # 1秒超时，便于检查运行状态

            while self.running:
                try:
                    client, addr = server.accept()
                    print(f"TCP连接: {addr}")

                    # 处理客户端连接
                    self._handle_tcp_client(client, addr)

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"TCP接受连接错误: {e}")

            server.close()
            print("TCP输入已关闭")

        except Exception as e:
            print(f"TCP服务器错误: {e}")

    def _handle_tcp_client(self, client, addr):
        """处理TCP客户端"""
        try:
            while self.running:
                # 读取数据
                data = client.recv(4096)
                if not data:
                    break

                # 解析数据
                try:
                    log_data = json.loads(data.decode('utf-8'))
                    self.log_queue.put({
                        'type': 'tcp_log',
                        'content': log_data,
                        'source': f'tcp:{addr[0]}:{addr[1]}',
                        'timestamp': time.time()
                    })
                except json.JSONDecodeError:
                    # 可能是普通文本
                    self.log_queue.put({
                        'type': 'tcp_log',
                        'content': {'raw': data.decode('utf-8')},
                        'source': f'tcp:{addr[0]}:{addr[1]}',
                        'timestamp': time.time()
                    })

        except Exception as e:
            print(f"处理TCP客户端错误: {e}")
        finally:
            client.close()

    def _udp_input_worker(self):
        """UDP输入工作线程"""
        host = self.input_config.get('host', '127.0.0.1')
        port = self.input_config.get('port', 5001)

        print(f"UDP输入: 监听 {host}:{port}")

        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server.bind((host, port))
            server.settimeout(1)

            while self.running:
                try:
                    data, addr = server.recvfrom(65535)

                    # 解析数据
                    try:
                        log_data = json.loads(data.decode('utf-8'))
                        self.log_queue.put({
                            'type': 'udp_log',
                            'content': log_data,
                            'source': f'udp:{addr[0]}:{addr[1]}',
                            'timestamp': time.time()
                        })
                    except json.JSONDecodeError:
                        # 可能是普通文本或GELF格式
                        self.log_queue.put({
                            'type': 'udp_log',
                            'content': {'raw': data.decode('utf-8')},
                            'source': f'udp:{addr[0]}:{addr[1]}',
                            'timestamp': time.time()
                        })

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"UDP接收错误: {e}")

            server.close()
            print("UDP输入已关闭")

        except Exception as e:
            print(f"UDP服务器错误: {e}")

    def _process_worker(self):
        """处理工作线程"""
        print("处理工作线程启动")

        while self.running or not self.log_queue.empty():
            try:
                # 从队列获取日志
                raw_event = self.log_queue.get(timeout=1)

                # 应用过滤器
                processed_event = self._apply_filters(raw_event)

                if processed_event:
                    # 标记为已处理
                    self.log_queue.task_done()
                    self.processed_count += 1

                    # 放入输出队列（简化处理，直接传递）
                    self._output_event(processed_event)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"处理日志错误: {e}")

        print("处理工作线程停止")

    def _apply_filters(self, event):
        """应用过滤器"""
        event_data = event.copy()

        for filter_config in self.filter_config:
            filter_type = filter_config['type']

            if filter_type == 'json_parse':
                event_data = self._filter_json_parse(event_data, filter_config)
            elif filter_type == 'grok':
                event_data = self._filter_grok(event_data, filter_config)
            elif filter_type == 'date':
                event_data = self._filter_date(event_data, filter_config)
            elif filter_type == 'mutate':
                event_data = self._filter_mutate(event_data, filter_config)
            elif filter_type == 'geoip':
                event_data = self._filter_geoip(event_data, filter_config)
            elif filter_type == 'user_agent':
                event_data = self._filter_user_agent(event_data, filter_config)

            if event_data is None:
                break

        return event_data

    def _filter_json_parse(self, event, config):
        """JSON解析过滤器"""
        content = event.get('content')

        if isinstance(content, str):
            try:
                parsed = json.loads(content)
                event['content'] = parsed
            except json.JSONDecodeError:
                # 不是JSON，保持原样
                pass

        return event

    def _filter_grok(self, event, config):
        """Grok模式匹配过滤器（简化版）"""
        # 在实际Logstash中，Grok使用正则表达式模式
        # 这里简化处理，只做基本解析
        content = event.get('content')

        if isinstance(content, dict):
            # 如果是结构化数据，不需要Grok
            return event

        if isinstance(content, str):
            # 简单解析常见日志格式
            import re

            # Apache日志格式示例
            apache_pattern = r'(\S+) (\S+) (\S+) \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\d+)'
            match = re.match(apache_pattern, content)

            if match:
                event['content'] = {
                    'client_ip': match.group(1),
                    'identity': match.group(2),
                    'user': match.group(3),
                    'timestamp': match.group(4),
                    'method': match.group(5),
                    'path': match.group(6),
                    'protocol': match.group(7),
                    'status': int(match.group(8)),
                    'size': int(match.group(9)),
                    'raw': content
                }

        return event

    def _filter_date(self, event, config):
        """日期过滤器"""
        content = event.get('content')

        if isinstance(content, dict):
            timestamp_fields = ['timestamp', '@timestamp', 'time', 'date']

            for field in timestamp_fields:
                if field in content:
                    try:
                        # 尝试解析ISO格式时间戳
                        from datetime import datetime
                        dt = datetime.fromisoformat(content[field].replace('Z', '+00:00'))
                        content['@timestamp'] = dt.isoformat()
                        break
                    except (ValueError, AttributeError):
                        continue

        # 添加处理时间戳
        event['processed_at'] = datetime.now().isoformat()

        return event

    def _filter_mutate(self, event, config):
        """字段操作过滤器"""
        content = event.get('content')

        if isinstance(content, dict):
            # 重命名字段
            rename = config.get('rename', {})
            for old_name, new_name in rename.items():
                if old_name in content:
                    content[new_name] = content.pop(old_name)

            # 删除字段
            remove_field = config.get('remove_field', [])
            for field in remove_field:
                content.pop(field, None)

            # 添加字段
            add_field = config.get('add_field', {})
            content.update(add_field)

        return event

    def _filter_geoip(self, event, config):
        """GEOIP过滤器（模拟）"""
        content = event.get('content')

        if isinstance(content, dict) and 'source_ip' in content:
            # 模拟GEOIP查询
            ip = content['source_ip']

            # 简单模拟：根据IP范围分配地理位置
            if ip.startswith('192.168.'):
                geo_data = {
                    'country': '本地网络',
                    'city': '内网',
                    'location': {'lat': 0, 'lon': 0}
                }
            else:
                # 随机分配一个地理位置用于演示
                countries = ['中国', '美国', '日本', '德国', '英国']
                cities = {
                    '中国': ['北京', '上海', '深圳', '杭州'],
                    '美国': ['纽约', '旧金山', '洛杉矶', '芝加哥'],
                    '日本': ['东京', '大阪', '京都', '名古屋'],
                    '德国': ['柏林', '慕尼黑', '汉堡', '法兰克福'],
                    '英国': ['伦敦', '曼彻斯特', '爱丁堡', '伯明翰']
                }

                country = random.choice(countries)
                city = random.choice(cities[country])

                geo_data = {
                    'country': country,
                    'city': city,
                    'location': {
                        'lat': random.uniform(-90, 90),
                        'lon': random.uniform(-180, 180)
                    }
                }

            content['geoip'] = geo_data

        return event

    def _filter_user_agent(self, event, config):
        """用户代理过滤器（模拟）"""
        content = event.get('content')

        if isinstance(content, dict) and 'user_agent' in content:
            ua = content['user_agent']

            # 简单解析用户代理
            ua_info = {
                'raw': ua,
                'device': 'Unknown',
                'os': 'Unknown',
                'browser': 'Unknown'
            }

            if 'Windows' in ua:
                ua_info['os'] = 'Windows'
                ua_info['device'] = 'Desktop'
            elif 'Macintosh' in ua:
                ua_info['os'] = 'macOS'
                ua_info['device'] = 'Desktop'
            elif 'iPhone' in ua:
                ua_info['os'] = 'iOS'
                ua_info['device'] = 'Mobile'
            elif 'Android' in ua:
                ua_info['os'] = 'Android'
                ua_info['device'] = 'Mobile'

            if 'Chrome' in ua:
                ua_info['browser'] = 'Chrome'
            elif 'Firefox' in ua:
                ua_info['browser'] = 'Firefox'
            elif 'Safari' in ua:
                ua_info['browser'] = 'Safari'

            content['user_agent_info'] = ua_info

        return event

    def _output_event(self, event):
        """输出事件"""
        output_type = self.output_config['type']

        if output_type == 'elasticsearch':
            self._output_to_elasticsearch(event)
        elif output_type == 'file':
            self._output_to_file(event)
        elif output_type == 'stdout':
            self._output_to_stdout(event)

    def _output_to_elasticsearch(self, event):
        """输出到Elasticsearch（模拟）"""
        # 在实际应用中，这里会连接到Elasticsearch集群
        # 这里只是模拟输出到文件
        es_doc = {
            '_index': self.output_config.get('index', 'logs'),
            '_type': '_doc',
            '_source': event['content'],
            '@timestamp': event['content'].get('@timestamp', datetime.now().isoformat())
        }

        # 写入模拟的ES输出文件
        with open('elasticsearch_output.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(es_doc, ensure_ascii=False) + '\n')

    def _output_to_file(self, event):
        """输出到文件"""
        filename = self.output_config.get('path', 'collected_logs.log')

        with open(filename, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

    def _output_to_stdout(self, event):
        """输出到标准输出"""
        print(f"[输出] {json.dumps(event, ensure_ascii=False)}")

    def _output_worker(self):
        """输出工作线程（简化版）"""
        # 在实际Logstash中，输出可能是异步的
        # 这里简化处理，在_process_worker中直接输出
        pass

# 演示日志收集器
print("\n演示日志收集器...")

# 配置收集器
collector_config = {
    'input': {
        'type': 'file',
        'path': 'structured_app.log'
    },
    'filters': [
        {
            'type': 'json_parse',
            'source_field': 'content'
        },
        {
            'type': 'date',
            'match': ['timestamp', '@timestamp']
        },
        {
            'type': 'mutate',
            'rename': {'level': 'log_level'},
            'add_field': {'collector': 'logstash_simulator'}
        },
        {
            'type': 'geoip',
            'source_field': 'source_ip'
        },
        {
            'type': 'user_agent',
            'source_field': 'user_agent'
        }
    ],
    'output': {
        'type': 'file',
        'path': 'collected_logs.json'
    }
}

# 创建并启动收集器
collector = LogCollector(
    input_config=collector_config['input'],
    filter_config=collector_config['filters'],
    output_config=collector_config['output']
)

collector.start()

print("\n收集器运行中，处理现有日志...")
time.sleep(2)  # 给收集器一些时间处理

collector.stop()

print("\n收集的日志已保存到 collected_logs.json")

# ============================================
# 第三部分：Elasticsearch客户端（模拟）
# ============================================

print("\n" + "=" * 50)
print("第三部分：Elasticsearch客户端（模拟）")
print("=" * 50)

class ElasticsearchSimulator:
    """Elasticsearch模拟器，用于演示"""

    def __init__(self, host='localhost', port=9200):
        self.host = host
        self.port = port
        self.indices = {}
        self.documents = {}

        print(f"初始化Elasticsearch模拟器: {host}:{port}")

    def create_index(self, index_name, mappings=None):
        """创建索引"""
        if index_name not in self.indices:
            self.indices[index_name] = {
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0
                },
                'mappings': mappings or {
                    'properties': {
                        '@timestamp': {'type': 'date'},
                        'message': {'type': 'text'},
                        'log_level': {'type': 'keyword'},
                        'app': {'type': 'keyword'}
                    }
                }
            }
            self.documents[index_name] = []

            print(f"创建索引: {index_name}")
            return {'acknowledged': True}
        else:
            print(f"索引已存在: {index_name}")
            return {'acknowledged': False, 'error': 'index_already_exists'}

    def index_document(self, index_name, document, doc_id=None):
        """索引文档"""
        if index_name not in self.indices:
            self.create_index(index_name)

        # 生成文档ID
        if doc_id is None:
            doc_id = f"doc_{len(self.documents[index_name]) + 1}"

        # 添加索引时间戳
        if '@timestamp' not in document:
            document['@timestamp'] = datetime.now().isoformat()

        document['_id'] = doc_id
        self.documents[index_name].append(document)

        print(f"索引文档: {index_name}/{doc_id}")
        return {
            '_index': index_name,
            '_type': '_doc',
            '_id': doc_id,
            '_version': 1,
            'result': 'created'
        }

    def bulk_index(self, index_name, documents):
        """批量索引文档"""
        results = []
        for doc in documents:
            result = self.index_document(index_name, doc)
            results.append(result)

        print(f"批量索引: {index_name}，共 {len(documents)} 个文档")
        return {'took': 100, 'errors': False, 'items': results}

    def search(self, index_name, query=None):
        """搜索文档"""
        if index_name not in self.documents:
            return {'hits': {'total': {'value': 0}, 'hits': []}}

        all_docs = self.documents[index_name]

        # 简单查询处理
        if query is None:
            matched_docs = all_docs
        else:
            # 简化查询处理
            matched_docs = []
            for doc in all_docs:
                # 检查是否匹配查询（简化版）
                match = True
                if 'query' in query and 'match' in query['query']:
                    for field, value in query['query']['match'].items():
                        if field in doc and str(doc[field]) != str(value):
                            match = False
                            break

                if match:
                    matched_docs.append(doc)

        # 构建返回结果
        hits = []
        for i, doc in enumerate(matched_docs[:10]):  # 限制10条
            hits.append({
                '_index': index_name,
                '_type': '_doc',
                '_id': doc.get('_id', f'doc_{i}'),
                '_score': 1.0,
                '_source': {k: v for k, v in doc.items() if k != '_id'}
            })

        return {
            'took': 50,
            'timed_out': False,
            '_shards': {'total': 1, 'successful': 1, 'failed': 0},
            'hits': {
                'total': {'value': len(matched_docs), 'relation': 'eq'},
                'max_score': 1.0,
                'hits': hits
            }
        }

    def get_index_stats(self, index_name):
        """获取索引统计"""
        if index_name not in self.documents:
            return {'error': 'index_not_found'}

        docs = self.documents[index_name]

        # 统计日志级别
        level_counts = {}
        for doc in docs:
            level = doc.get('log_level', doc.get('level', 'UNKNOWN'))
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            '_shards': {'total': 1, 'successful': 1, 'failed': 0},
            'indices': {
                index_name: {
                    'total': {
                        'docs': {'count': len(docs)},
                        'store': {'size_in_bytes': len(str(docs)) * 10}  # 估算大小
                    },
                    'primaries': {
                        'docs': {'count': len(docs)},
                        'indexing': {
                            'index_total': len(docs),
                            'index_time_in_millis': len(docs) * 10
                        }
                    }
                }
            },
            'aggregations': {
                'log_levels': level_counts
            }
        }

# 演示Elasticsearch模拟器
print("\n演示Elasticsearch模拟器...")

es = ElasticsearchSimulator()

# 1. 创建索引
print("\n1. 创建日志索引...")
es.create_index('app-logs-2024.01.01', mappings={
    'properties': {
        '@timestamp': {'type': 'date'},
        'log_level': {'type': 'keyword'},
        'app': {'type': 'keyword'},
        'message': {'type': 'text'},
        'endpoint': {'type': 'keyword'},
        'status_code': {'type': 'integer'},
        'duration_ms': {'type': 'float'},
        'user_id': {'type': 'keyword'},
        'geoip': {
            'properties': {
                'country': {'type': 'keyword'},
                'city': {'type': 'keyword'},
                'location': {'type': 'geo_point'}
            }
        }
    }
})

# 2. 索引文档
print("\n2. 索引日志文档...")

# 读取收集的日志
try:
    with open('collected_logs.json', 'r', encoding='utf-8') as f:
        logs = [json.loads(line) for line in f if line.strip()]

    # 提取和索引日志内容
    documents_to_index = []
    for log_entry in logs[:20]:  # 限制20条用于演示
        content = log_entry.get('content', {})
        if content:
            documents_to_index.append(content)

    # 批量索引
    if documents_to_index:
        result = es.bulk_index('app-logs-2024.01.01', documents_to_index)
        print(f"批量索引结果: {len(result['items'])} 个文档")
except FileNotFoundError:
    print("收集的日志文件不存在，使用模拟数据...")
    # 使用模拟数据
    mock_docs = []
    for i in range(10):
        mock_docs.append({
            '@timestamp': datetime.now().isoformat(),
            'log_level': random.choice(['INFO', 'WARNING', 'ERROR']),
            'app': 'ecommerce-api',
            'message': f'模拟日志消息 {i+1}',
            'endpoint': f'/api/{random.choice(["products", "orders", "users"])}',
            'status_code': random.choice([200, 200, 200, 404, 500]),
            'duration_ms': random.uniform(100, 1000),
            'user_id': f'user_{random.randint(1, 1000)}'
        })

    result = es.bulk_index('app-logs-2024.01.01', mock_docs)
    print(f"使用模拟数据: {len(result['items'])} 个文档")

# 3. 搜索文档
print("\n3. 搜索日志文档...")

# 搜索所有日志
all_logs = es.search('app-logs-2024.01.01')
print(f"总日志数: {all_logs['hits']['total']['value']}")
print(f"前 {len(all_logs['hits']['hits'])} 条日志:")

for hit in all_logs['hits']['hits'][:3]:  # 显示前3条
    source = hit['_source']
    print(f"  [{source.get('log_level', 'UNKNOWN')}] "
          f"{source.get('endpoint', 'N/A')} - "
          f"{source.get('message', '')[:50]}...")

# 搜索错误日志
error_query = {
    'query': {
        'match': {'log_level': 'ERROR'}
    }
}
error_logs = es.search('app-logs-2024.01.01', error_query)
print(f"\n错误日志数: {error_logs['hits']['total']['value']}")

# 4. 获取统计信息
print("\n4. 获取索引统计...")
stats = es.get_index_stats('app-logs-2024.01.01')
if 'aggregations' in stats:
    print("日志级别统计:")
    for level, count in stats['aggregations']['log_levels'].items():
        print(f"  {level}: {count}")

# ============================================
# 第四部分：Kibana仪表板配置（概念演示）
# ============================================

print("\n" + "=" * 50)
print("第四部分：Kibana仪表板配置（概念演示）")
print("=" * 50)

class KibanaConfigGenerator:
    """Kibana配置生成器"""

    def __init__(self, index_pattern):
        self.index_pattern = index_pattern
        print(f"初始化Kibana配置生成器，索引模式: {index_pattern}")

    def generate_index_pattern(self):
        """生成索引模式配置"""
        config = {
            'id': self.index_pattern.replace('*', 'star'),
            'title': self.index_pattern,
            'timeFieldName': '@timestamp',
            'fields': [
                {
                    'name': '@timestamp',
                    'type': 'date',
                    'count': 0,
                    'scripted': False,
                    'searchable': True,
                    'aggregatable': True,
                    'readFromDocValues': True
                },
                {
                    'name': 'log_level',
                    'type': 'string',
                    'count': 0,
                    'scripted': False,
                    'searchable': True,
                    'aggregatable': True,
                    'readFromDocValues': True
                },
                {
                    'name': 'app',
                    'type': 'string',
                    'count': 0,
                    'scripted': False,
                    'searchable': True,
                    'aggregatable': True,
                    'readFromDocValues': True
                },
                {
                    'name': 'message',
                    'type': 'string',
                    'count': 0,
                    'scripted': False,
                    'searchable': True,
                    'aggregatable': False,
                    'readFromDocValues': False
                },
                {
                    'name': 'endpoint',
                    'type': 'string',
                    'count': 0,
                    'scripted': False,
                    'searchable': True,
                    'aggregatable': True,
                    'readFromDocValues': True
                },
                {
                    'name': 'status_code',
                    'type': 'number',
                    'count': 0,
                    'scripted': False,
                    'searchable': True,
                    'aggregatable': True,
                    'readFromDocValues': True
                }
            ]
        }

        return config

    def generate_discover_view(self):
        """生成Discover视图配置"""
        config = {
            'columns': ['@timestamp', 'log_level', 'app', 'message'],
            'sort': [['@timestamp', 'desc']],
            'filters': [],
            'index': self.index_pattern
        }

        return config

    def generate_visualization_configs(self):
        """生成可视化配置"""

        visualizations = []

        # 1. 日志级别分布饼图
        level_pie = {
            'type': 'pie',
            'title': '日志级别分布',
            'params': {
                'type': 'pie',
                'addTooltip': True,
                'addLegend': True,
                'legendPosition': 'right'
            },
            'aggs': [
                {
                    'id': '1',
                    'type': 'count',
                    'schema': 'metric'
                },
                {
                    'id': '2',
                    'type': 'terms',
                    'schema': 'segment',
                    'params': {
                        'field': 'log_level',
                        'size': 10,
                        'order': 'desc',
                        'orderBy': '1'
                    }
                }
            ]
        }
        visualizations.append(('日志级别饼图', level_pie))

        # 2. 请求状态码分布柱状图
        status_bar = {
            'type': 'histogram',
            'title': 'HTTP状态码分布',
            'params': {
                'type': 'histogram',
                'grid': {'categoryLines': False},
                'categoryAxes': [{
                    'id': 'CategoryAxis-1',
                    'type': 'category',
                    'position': 'bottom',
                    'show': True,
                    'style': {},
                    'scale': {'type': 'linear'},
                    'labels': {'show': True, 'truncate': 100}
                }]
            },
            'aggs': [
                {
                    'id': '1',
                    'type': 'count',
                    'schema': 'metric'
                },
                {
                    'id': '2',
                    'type': 'terms',
                    'schema': 'segment',
                    'params': {
                        'field': 'status_code',
                        'size': 10,
                        'order': 'desc',
                        'orderBy': '1'
                    }
                }
            ]
        }
        visualizations.append(('状态码柱状图', status_bar))

        # 3. 时间序列图 - 日志量趋势
        time_series = {
            'type': 'line',
            'title': '日志量趋势',
            'params': {
                'type': 'line',
                'grid': {'categoryLines': False},
                'categoryAxes': [{
                    'id': 'CategoryAxis-1',
                    'type': 'category',
                    'position': 'bottom',
                    'show': True,
                    'style': {},
                    'scale': {'type': 'linear'},
                    'labels': {'show': True, 'truncate': 100}
                }]
            },
            'aggs': [
                {
                    'id': '1',
                    'type': 'count',
                    'schema': 'metric'
                },
                {
                    'id': '2',
                    'type': 'date_histogram',
                    'schema': 'segment',
                    'params': {
                        'field': '@timestamp',
                        'interval': 'hour',
                        'customInterval': '2h',
                        'min_doc_count': 0,
                        'extended_bounds': {}
                    }
                }
            ]
        }
        visualizations.append(('时间序列图', time_series))

        return visualizations

    def generate_dashboard(self):
        """生成仪表板配置"""
        visualizations = self.generate_visualization_configs()

        dashboard = {
            'title': '应用日志监控仪表板',
            'description': '监控应用日志级别、状态码和趋势',
            'panels': [],
            'options': {
                'darkTheme': False,
                'useMargins': True,
                'hidePanelTitles': False
            },
            'timeRestore': False,
            'kibanaSavedObjectMeta': {
                'searchSourceJSON': json.dumps({
                    'query': {'query': '', 'language': 'kuery'},
                    'filter': []
                })
            }
        }

        # 添加面板
        panel_positions = [
            {'x': 0, 'y': 0, 'w': 12, 'h': 8},
            {'x': 12, 'y': 0, 'w': 12, 'h': 8},
            {'x': 0, 'y': 8, 'w': 24, 'h': 10}
        ]

        for (title, viz_config), position in zip(visualizations, panel_positions):
            panel = {
                'panelIndex': str(len(dashboard['panels'])),
                'gridData': position,
                'version': '7.10.0',
                'panelRefName': f'panel_{len(dashboard["panels"])}',
                'embeddableConfig': viz_config,
                'title': title
            }
            dashboard['panels'].append(panel)

        return dashboard

    def save_configs(self, output_dir='kibana_configs'):
        """保存配置到文件"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 保存索引模式
        index_pattern = self.generate_index_pattern()
        with open(f'{output_dir}/index_pattern.json', 'w', encoding='utf-8') as f:
            json.dump(index_pattern, f, indent=2, ensure_ascii=False)

        # 保存Discover视图
        discover = self.generate_discover_view()
        with open(f'{output_dir}/discover.json', 'w', encoding='utf-8') as f:
            json.dump(discover, f, indent=2, ensure_ascii=False)

        # 保存可视化配置
        visualizations = self.generate_visualization_configs()
        for i, (title, config) in enumerate(visualizations):
            filename = f'visualization_{i+1}_{title.replace(" ", "_")}.json'
            with open(f'{output_dir}/{filename}', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        # 保存仪表板
        dashboard = self.generate_dashboard()
        with open(f'{output_dir}/dashboard.json', 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)

        print(f"Kibana配置已保存到 {output_dir}/ 目录")
        print(f"  索引模式: {output_dir}/index_pattern.json")
        print(f"  Discover视图: {output_dir}/discover.json")
        print(f"  可视化配置: {len(visualizations)} 个文件")
        print(f"  仪表板: {output_dir}/dashboard.json")

# 生成Kibana配置
print("\n生成Kibana配置...")

kibana_gen = KibanaConfigGenerator('app-logs-*')
kibana_gen.save_configs()

# ============================================
# 第五部分：分布式日志收集架构
# ============================================

print("\n" + "=" * 50)
print("第五部分：分布式日志收集架构")
print("=" * 50)

class DistributedLoggingArchitecture:
    """分布式日志收集架构说明"""

    @staticmethod
    def print_architecture():
        """打印架构图（文本版）"""
        print("\n分布式日志收集架构:")
        print("=" * 60)

        architecture = """
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   应用服务器 1   │    │   应用服务器 2   │    │   应用服务器 N   │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │   Filebeat │◄─┼────┼─►│   Filebeat │◄─┼────┼─►│   Filebeat │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│        │        │    │        │        │    │        │        │
└────────┼────────┘    └────────┼────────┘    └────────┼────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
                       ┌─────────────────┐
                       │    Logstash     │
                       │   (收集 + 处理)  │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Elasticsearch  │
                       │   (存储 + 索引)  │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Kibana      │
                       │   (可视化分析)   │
                       └─────────────────┘
        """

        print(architecture)

        print("\n组件说明:")
        print("1. 应用服务器:")
        print("   - 运行业务应用")
        print("   - 使用结构化日志格式（JSON）")
        print("   - 本地日志文件轮转")

        print("\n2. Filebeat (日志收集器):")
        print("   - 轻量级日志收集代理")
        print("   - 监控日志文件变化")
        print("   - 支持多行日志合并")
        print("   - 压缩和加密传输")

        print("\n3. Logstash (日志处理管道):")
        print("   - 接收来自Filebeat的日志")
        print("   - 解析、过滤、丰富日志数据")
        print("   - 支持Grok、GEOIP、用户代理解析")
        print("   - 输出到Elasticsearch")

        print("\n4. Elasticsearch (搜索引擎):")
        print("   - 分布式文档存储")
        print("   - 实时索引和搜索")
        print("   - 支持分片和副本")
        print("   - RESTful API")

        print("\n5. Kibana (可视化平台):")
        print("   - 日志搜索和发现")
        print("   - 创建仪表板和图表")
        print("   - 告警和监控")
        print("   - 机器学习分析")

        print("\n数据流:")
        print("  应用日志 → Filebeat → Logstash → Elasticsearch → Kibana")

    @staticmethod
    def generate_config_examples():
        """生成配置文件示例"""
        examples_dir = 'distributed_configs'
        import os
        os.makedirs(examples_dir, exist_ok=True)

        # 1. Filebeat配置
        filebeat_config = {
            'filebeat.inputs': [{
                'type': 'log',
                'enabled': true,
                'paths': ['/var/log/app/*.log'],
                'json.keys_under_root': true,
                'json.add_error_key': true,
                'fields': {
                    'app': 'ecommerce-api',
                    'environment': 'production'
                },
                'fields_under_root': true
            }],
            'output.logstash': {
                'hosts': ['logstash.example.com:5044'],
                'compression_level': 3
            },
            'processors': [{
                'add_fields': {
                    'target': '',
                    'fields': {
                        'host_ip': '${HOST_IP}'
                    }
                }
            }]
        }

        with open(f'{examples_dir}/filebeat.yml', 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(filebeat_config, f, default_flow_style=False)

        # 2. Logstash配置
        logstash_config = """
input {
  beats {
    port => 5044
    ssl => true
    ssl_certificate_authorities => ["/path/to/ca.crt"]
    ssl_certificate => "/path/to/server.crt"
    ssl_key => "/path/to/server.key"
  }
}

filter {
  # JSON解析
  json {
    source => "message"
    target => "parsed"
  }

  # 日期解析
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }

  # GEOIP
  geoip {
    source => "client_ip"
    target => "geoip"
  }

  # 用户代理解析
  useragent {
    source => "user_agent"
    target => "ua"
  }

  # 移除临时字段
  mutate {
    remove_field => ["message", "timestamp"]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch.example.com:9200"]
    index => "app-logs-%{+YYYY.MM.dd}"
    user => "elastic"
    password => "${ES_PASSWORD}"
    ssl => true
    cacert => "/path/to/ca.crt"
  }

  # 备份输出到文件
  file {
    path => "/var/log/logstash/backup/app-logs-%{+YYYY-MM-dd}.log"
    codec => line { format => "%{[@timestamp]} %{message}" }
  }
}
"""

        with open(f'{examples_dir}/logstash.conf', 'w', encoding='utf-8') as f:
            f.write(logstash_config)

        # 3. Elasticsearch索引模板
        index_template = {
            'index_patterns': ['app-logs-*'],
            'template': {
                'settings': {
                    'number_of_shards': 3,
                    'number_of_replicas': 1,
                    'refresh_interval': '30s'
                },
                'mappings': {
                    'dynamic': 'strict',
                    'properties': {
                        '@timestamp': {'type': 'date'},
                        'app': {'type': 'keyword'},
                        'environment': {'type': 'keyword'},
                        'log_level': {'type': 'keyword'},
                        'message': {'type': 'text'},
                        'endpoint': {'type': 'keyword'},
                        'method': {'type': 'keyword'},
                        'status_code': {'type': 'integer'},
                        'duration_ms': {'type': 'float'},
                        'user_id': {'type': 'keyword'},
                        'client_ip': {'type': 'ip'},
                        'geoip': {
                            'properties': {
                                'country_name': {'type': 'keyword'},
                                'city_name': {'type': 'keyword'},
                                'location': {'type': 'geo_point'}
                            }
                        },
                        'ua': {
                            'properties': {
                                'name': {'type': 'keyword'},
                                'os': {'type': 'keyword'},
                                'device': {'type': 'keyword'}
                            }
                        }
                    }
                }
            }
        }

        with open(f'{examples_dir}/index_template.json', 'w', encoding='utf-8') as f:
            json.dump(index_template, f, indent=2, ensure_ascii=False)

        print(f"\n配置文件示例已生成到 {examples_dir}/ 目录:")
        print(f"  - filebeat.yml: Filebeat配置")
        print(f"  - logstash.conf: Logstash配置")
        print(f"  - index_template.json: Elasticsearch索引模板")

# 展示分布式架构
DistributedLoggingArchitecture.print_architecture()
DistributedLoggingArchitecture.generate_config_examples()

# ============================================
# 第六部分：知识点总结
# ============================================

print("\n" + "=" * 50)
print("知识点总结")
print("=" * 50)

summary = """
必须背下来的知识点：
1. 结构化日志格式 - 使用JSON包含丰富上下文信息
2. ELK栈组件职责 - Elasticsearch存储、Logstash处理、Kibana可视化
3. 日志收集管道 - 输入→过滤→输出的数据处理流程
4. 索引模式设计 - 合理的字段映射和索引设置

需要熟悉掌握的知识点：
1. Filebeat配置 - 轻量级日志收集代理
2. Logstash过滤器 - Grok、GEOIP、用户代理解析
3. Elasticsearch查询DSL - 搜索、过滤、聚合查询
4. Kibana可视化 - 创建仪表板和图表

了解即可的知识点：
1. 分布式架构设计 - 高可用、可扩展的日志系统
2. 日志安全考虑 - 传输加密、访问控制、数据脱敏
3. 性能优化技巧 - 索引分片、查询优化、缓存策略
4. 备选方案 - Loki+Grafana、Splunk、Datadog等其他方案
"""

print(summary)

print("\n" + "=" * 50)
print("日志聚合和ELK栈学习完成！")
print("下一步：学习高级MCP集成和云原生日志")
print("=" * 50)