# 后端日志集成指南

## 概述

本指南介绍如何将日志系统与各种后端组件集成，包括Web框架、数据库、缓存、消息队列等。正确的集成可以大大提高系统的可观察性和可维护性。

## Web框架集成

### FastAPI/Flask集成要点

#### 1. 请求跟踪中间件
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # 记录请求开始
    logger.info(f"请求开始: {request.method} {request.url}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录响应
        logger.info(f"请求完成: {request.method} {request.url} -> "
                   f"{response.status_code} ({process_time:.3f}s)")

        # 添加跟踪头部
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Process-Time'] = f"{process_time:.3f}"

        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"请求失败: {request.method} {request.url} -> "
                    f"异常: {type(e).__name__} ({process_time:.3f}s)",
                    exc_info=True)
        raise
```

#### 2. 异常处理器
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, 'request_id', 'unknown')

    if exc.status_code >= 500:
        logger.error(f"[{request_id}] 服务器错误 {exc.status_code}")
    elif exc.status_code >= 400:
        logger.warning(f"[{request_id}] 客户端错误 {exc.status_code}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "request_id": request_id}
    )
```

### Django集成要点

#### 1. 中间件配置
```python
class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django.request')

    def __call__(self, request):
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id

        start_time = time.time()
        self.logger.info(f"[{request_id}] {request.method} {request.path}")

        response = self.get_response(request)

        duration = time.time() - start_time
        self.logger.info(f"[{request_id}] {response.status_code} ({duration:.3f}s)")

        response['X-Request-ID'] = request_id
        return response
```

## 数据库集成

### 连接池日志

#### 1. 连接管理日志
```python
class DatabaseConnectionPool:
    def __init__(self, db_url, pool_size=10):
        self.logger = logging.getLogger('database.pool')
        self.pool_size = pool_size
        self.logger.info(f"初始化连接池: {db_url}, 大小={pool_size}")

    def get_connection(self):
        conn_id = id(conn)
        self.logger.debug(f"获取连接: id={conn_id}")
        self.logger.debug(f"可用连接: {self._available_count()}/{self.pool_size}")
        return conn

    def release_connection(self, conn):
        conn_id = id(conn)
        self.logger.debug(f"释放连接: id={conn_id}")
```

#### 2. SQL查询日志
```python
class LoggingCursor:
    def execute(self, sql, params=None):
        sql_logger = logging.getLogger('database.sql')

        # 记录SQL（脱敏敏感数据）
        safe_sql = self._sanitize_sql(sql, params)
        sql_logger.debug(f"执行SQL: {safe_sql}")

        start_time = time.time()
        try:
            result = super().execute(sql, params)
            duration = time.time() - start_time

            # 记录慢查询
            if duration > 1.0:  # 1秒阈值
                sql_logger.warning(f"慢查询: {safe_sql} ({duration:.3f}s)")
            else:
                sql_logger.debug(f"查询完成: {duration:.3f}s")

            return result
        except Exception as e:
            duration = time.time() - start_time
            sql_logger.error(f"查询失败: {safe_sql} ({duration:.3f}s)", exc_info=True)
            raise
```

### ORM集成（SQLAlchemy示例）

#### 1. 配置SQLAlchemy日志
```python
# 配置SQLAlchemy日志级别
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)

# 详细SQL日志
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### 2. 自定义事件处理器
```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    logger = logging.getLogger('sqlalchemy.query')
    logger.debug(f"开始执行: {statement}")

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    logger = logging.getLogger('sqlalchemy.query')

    if total > 0.5:  # 500ms阈值
        logger.warning(f"慢查询: {statement[:100]}... ({total:.3f}s)")
    else:
        logger.debug(f"查询完成: ({total:.3f}s)")
```

## 缓存集成

### Redis日志集成

#### 1. Redis客户端包装
```python
class LoggingRedisClient:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.logger = logging.getLogger('cache.redis')
        self.slow_threshold = 0.1  # 100ms

    def get(self, key):
        start_time = time.time()
        self.logger.debug(f"GET {key}")

        try:
            value = self.redis.get(key)
            duration = time.time() - start_time

            if duration > self.slow_threshold:
                self.logger.warning(f"慢GET: {key} ({duration:.3f}s)")
            else:
                self.logger.debug(f"GET完成: {duration:.3f}s")

            return value
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"GET失败: {key} ({duration:.3f}s)", exc_info=True)
            raise

    def set(self, key, value, ex=None):
        start_time = time.time()
        self.logger.debug(f"SET {key} (ex={ex})")

        try:
            result = self.redis.set(key, value, ex=ex)
            duration = time.time() - start_time

            self.logger.debug(f"SET完成: {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"SET失败: {key} ({duration:.3f}s)", exc_info=True)
            raise
```

#### 2. 缓存命中率统计
```python
class CacheStatsLogger:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.logger = logging.getLogger('cache.stats')

    def record_hit(self, key):
        self.hits += 1
        self.logger.debug(f"缓存命中: {key}")
        self._log_stats()

    def record_miss(self, key):
        self.misses += 1
        self.logger.debug(f"缓存未命中: {key}")
        self._log_stats()

    def _log_stats(self):
        total = self.hits + self.misses
        if total > 0 and total % 100 == 0:  # 每100次记录一次统计
            hit_rate = self.hits / total * 100
            self.logger.info(f"缓存统计: 命中率={hit_rate:.1f}% "
                           f"({self.hits}/{total})")
```

## 消息队列集成

### RabbitMQ/Celery集成

#### 1. Celery任务日志
```python
from celery import current_task
import logging

@app.task(bind=True)
def process_data_task(self, data):
    # 获取任务特定的logger
    task_logger = logging.getLogger(f'celery.{self.name}')

    # 添加任务ID到日志记录
    task_id = self.request.id
    task_logger.info(f"任务开始: {task_id}")
    task_logger.debug(f"任务数据: {data}")

    try:
        # 处理数据
        result = process_data(data)

        task_logger.info(f"任务完成: {task_id}")
        return result
    except Exception as e:
        task_logger.error(f"任务失败: {task_id}", exc_info=True)
        raise
```

#### 2. 消息消费者日志
```python
class LoggingMessageConsumer:
    def __init__(self, queue_name):
        self.queue_name = queue_name
        self.logger = logging.getLogger(f'mq.consumer.{queue_name}')

    def consume(self, message):
        message_id = message.get('id', 'unknown')
        self.logger.info(f"收到消息: {message_id}")
        self.logger.debug(f"消息内容: {message}")

        start_time = time.time()

        try:
            result = self.process_message(message)
            duration = time.time() - start_time

            self.logger.info(f"消息处理完成: {message_id} ({duration:.3f}s)")
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"消息处理失败: {message_id} ({duration:.3f}s)",
                            exc_info=True)
            raise

    def process_message(self, message):
        # 实际处理逻辑
        pass
```

## 外部API集成

### HTTP客户端日志

#### 1. 请求/响应日志
```python
class LoggingHTTPClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.logger = logging.getLogger('http.client')
        self.session = requests.Session()

    def request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        request_id = str(uuid.uuid4())[:8]

        # 记录请求
        self.logger.info(f"[{request_id}] {method} {url}")
        if kwargs.get('json'):
            self.logger.debug(f"[{request_id}] 请求体: {kwargs['json']}")

        start_time = time.time()

        try:
            response = self.session.request(method, url, **kwargs)
            duration = time.time() - start_time

            # 记录响应
            self.logger.info(f"[{request_id}] {response.status_code} ({duration:.3f}s)")

            if duration > 2.0:  # 2秒阈值
                self.logger.warning(f"[{request_id}] 慢响应: {duration:.3f}s")

            # 记录错误响应
            if not response.ok:
                self.logger.error(f"[{request_id}] 错误响应: {response.status_code}")
                self.logger.debug(f"[{request_id}] 响应体: {response.text[:500]}")

            return response

        except requests.RequestException as e:
            duration = time.time() - start_time
            self.logger.error(f"[{request_id}] 请求失败: {e} ({duration:.3f}s)")
            raise
```

#### 2. 重试机制日志
```python
class RetryingClient(LoggingHTTPClient):
    def __init__(self, base_url, max_retries=3):
        super().__init__(base_url)
        self.max_retries = max_retries

    def request_with_retry(self, method, endpoint, **kwargs):
        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.debug(f"尝试 {attempt}/{self.max_retries}")
                return self.request(method, endpoint, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt < self.max_retries:
                    wait_time = attempt * 2  # 退避策略
                    self.logger.warning(f"连接失败，{wait_time}秒后重试: {e}")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"所有重试均失败")
                    raise
```

## 性能监控集成

### 指标收集和日志

#### 1. 性能指标日志
```python
class PerformanceMonitor:
    def __init__(self):
        self.logger = logging.getLogger('performance')
        self.metrics = {}

    def start_operation(self, operation_name):
        op_id = f"{operation_name}_{int(time.time() * 1000)}"
        self.metrics[op_id] = {
            'name': operation_name,
            'start_time': time.time(),
            'end_time': None,
            'success': False
        }
        self.logger.debug(f"开始操作: {operation_name} [{op_id}]")
        return op_id

    def end_operation(self, op_id, success=True, extra_metrics=None):
        if op_id in self.metrics:
            metric = self.metrics[op_id]
            metric['end_time'] = time.time()
            metric['success'] = success

            duration = metric['end_time'] - metric['start_time']

            # 记录性能指标
            if success:
                self.logger.info(f"操作完成: {metric['name']} "
                               f"({duration:.3f}s) [{op_id}]")
            else:
                self.logger.error(f"操作失败: {metric['name']} "
                                f"({duration:.3f}s) [{op_id}]")

            # 记录额外指标
            if extra_metrics:
                self.logger.debug(f"操作指标: {extra_metrics}")

            # 记录慢操作
            if duration > 1.0:  # 1秒阈值
                self.logger.warning(f"慢操作: {metric['name']} ({duration:.3f}s)")

    def record_metric(self, name, value, tags=None):
        metric_log = {
            'metric': name,
            'value': value,
            'timestamp': time.time(),
            'tags': tags or {}
        }
        self.logger.debug(f"指标记录: {json.dumps(metric_log)}")
```

## 安全审计集成

### 审计日志

#### 1. 用户操作审计
```python
class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger('audit')

    def log_user_action(self, user_id, action, resource, details=None,
                       success=True, ip_address=None):
        audit_record = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'success': success,
            'ip_address': ip_address,
            'details': details or {}
        }

        # 使用JSON格式记录审计日志
        self.logger.info(
            f"用户操作审计: {json.dumps(audit_record)}",
            extra={'audit_record': audit_record}
        )

    def log_security_event(self, event_type, severity, description, details=None):
        security_record = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'severity': severity,  # LOW, MEDIUM, HIGH, CRITICAL
            'description': description,
            'details': details or {}
        }

        # 根据严重程度使用不同日志级别
        if severity in ['HIGH', 'CRITICAL']:
            self.logger.error(
                f"安全事件: {json.dumps(security_record)}",
                extra={'security_record': security_record}
            )
        else:
            self.logger.warning(
                f"安全事件: {json.dumps(security_record)}",
                extra={'security_record': security_record}
            )
```

## 集成最佳实践

### 1. 上下文传播
- 使用请求ID在所有组件间传递
- 在日志中包括相关上下文（用户ID、会话ID等）
- 使用MDC（Mapped Diagnostic Context）或类似机制

### 2. 日志级别管理
- 生产环境：WARNING及以上
- 开发环境：DEBUG及以上
- 根据组件调整级别（数据库SQL日志使用DEBUG，错误日志使用ERROR）

### 3. 性能考虑
- 异步日志记录避免阻塞主线程
- 批量写入减少I/O操作
- 结构化日志便于后续分析

### 4. 安全性考虑
- 脱敏敏感信息（密码、令牌、个人身份信息）
- 审计日志单独存储和保护
- 访问控制日志记录

### 5. 监控和告警
- 错误率监控和告警
- 慢查询/慢操作监控
- 日志量异常监控

## 故障排除指南

### 常见问题

#### 1. 日志丢失
- 检查日志级别设置
- 验证handler配置
- 检查磁盘空间和权限

#### 2. 日志性能问题
- 使用异步日志
- 减少不必要的DEBUG日志
- 实施日志采样

#### 3. 日志混乱
- 确保线程/进程安全
- 使用请求ID跟踪
- 统一日志格式

#### 4. 存储问题
- 实施日志轮转
- 使用压缩减少空间
- 考虑日志分级存储

## 工具推荐

### 日志收集和分析
1. **ELK Stack** (Elasticsearch, Logstash, Kibana)
2. **Loki** + **Grafana** (云原生方案)
3. **Splunk** (企业级)
4. **Datadog** (SaaS方案)

### 性能监控
1. **Prometheus** + **Grafana**
2. **New Relic**
3. **AppDynamics**

### 分布式追踪
1. **Jaeger**
2. **Zipkin**
3. **OpenTelemetry**

## 下一步

1. **实现基础集成** - 从Web框架和数据库开始
2. **添加性能监控** - 集成关键指标收集
3. **实施安全审计** - 添加审计日志
4. **配置日志收集** - 设置集中式日志管理
5. **建立告警机制** - 配置关键错误告警

记住：好的日志集成是系统可观察性的基础，值得投入时间精心设计。