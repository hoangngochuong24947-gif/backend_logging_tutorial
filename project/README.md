# LogMonitor - 企业级日志监控系统

## 项目概述

LogMonitor 是一个完整的企业级日志监控和分析系统，集成了日志收集、处理、存储、分析和可视化功能。采用微服务架构，支持云原生部署。

### 核心特性

- **多源日志收集**：支持文件、容器、应用、系统日志
- **实时处理管道**：日志过滤、丰富、转换
- **智能分析**：异常检测、模式识别、趋势分析
- **可视化仪表板**：实时监控、历史分析、告警管理
- **企业级特性**：多租户、安全审计、高可用

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                     LogMonitor System                    │
│                                                         │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐   │
│  │  数据采集层  │    │  数据处理层  │    │  数据存储层  │   │
│  │ • Filebeat │    │ • Logstash │    │ • ES集群   │   │
│  │ • Fluentd  │───►│ • 自定义处理 │───►│ • 对象存储  │   │
│  │ • SDK      │    │ • 规则引擎  │    │ • 缓存     │   │
│  └────────────┘    └────────────┘    └────────────┘   │
│           │                     │             │        │
│           ▼                     ▼             ▼        │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐   │
│  │   API网关   │    │  分析引擎   │    │  告警系统   │   │
│  │ • REST API │    │ • 实时分析 │    │ • 多通道   │   │
│  │ • GraphQL  │◄──►│ • 批处理   │◄──►│ • 智能路由 │   │
│  │ • WebSocket│    │ • 机器学习 │    │ • 去重抑制 │   │
│  └────────────┘    └────────────┘    └────────────┘   │
│           │                     │             │        │
│           └─────────────────────┼─────────────┘        │
│                                 ▼                      │
│                        ┌────────────┐                 │
│                        │  前端界面   │                 │
│                        │ • 仪表板   │                 │
│                        │ • 日志搜索 │                 │
│                        │ • 配置管理 │                 │
│                        └────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

### 技术栈

#### 后端服务
- **Python 3.10+**：主要开发语言
- **FastAPI**：REST API框架
- **SQLAlchemy**：ORM
- **Celery**：异步任务队列
- **Redis**：缓存和消息队列

#### 数据存储
- **PostgreSQL**：元数据存储
- **Elasticsearch**：日志存储和搜索
- **MinIO/S3**：对象存储
- **TimescaleDB**：时序数据（可选）

#### 日志处理
- **Vector**：高性能日志收集器
- **Logstash**：日志处理管道
- **自定义处理器**：业务逻辑处理

#### 前端
- **React 18**：前端框架
- **TypeScript**：类型安全
- **Ant Design**：UI组件库
- **ECharts**：数据可视化
- **WebSocket**：实时更新

#### 基础设施
- **Docker & Docker Compose**：容器化
- **Kubernetes**：生产部署
- **Helm**：Kubernetes包管理
- **GitHub Actions**：CI/CD
- **Prometheus & Grafana**：系统监控

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+（开发环境）
- Node.js 18+（前端开发）

### 使用Docker快速启动

1. 克隆项目
```bash
git clone https://github.com/yourusername/logmonitor.git
cd logmonitor
```

2. 复制环境变量文件
```bash
cp .env.example .env
# 编辑.env文件，配置必要的环境变量
```

3. 启动服务
```bash
docker-compose up -d
```

4. 访问系统
- 前端界面：http://localhost:3000
- API文档：http://localhost:8000/docs
- Kibana：http://localhost:5601
- Grafana：http://localhost:3001

### 开发环境设置

1. 创建Python虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖
```bash
pip install -r requirements/dev.txt
```

3. 初始化数据库
```bash
alembic upgrade head
python scripts/init_data.py
```

4. 启动开发服务器
```bash
# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端
cd frontend
npm install
npm start
```

## 项目结构

```
logmonitor/
├── app/                            # 后端应用
│   ├── api/                        # API端点
│   │   ├── v1/                     # API版本1
│   │   │   ├── endpoints/          # 端点定义
│   │   │   │   ├── logs.py         # 日志相关API
│   │   │   │   ├── alerts.py       # 告警相关API
│   │   │   │   ├── dashboards.py   # 仪表板API
│   │   │   │   └── system.py       # 系统管理API
│   │   │   └── __init__.py
│   │   └── dependencies.py         # 依赖注入
│   ├── core/                       # 核心模块
│   │   ├── config.py               # 配置管理
│   │   ├── security.py             # 安全相关
│   │   ├── logging.py              # 日志配置
│   │   └── exceptions.py           # 异常处理
│   ├── models/                     # 数据模型
│   │   ├── sql/                    # SQL模型
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── log_source.py       # 日志源模型
│   │   │   ├── alert_rule.py       # 告警规则模型
│   │   │   └── dashboard.py        # 仪表板模型
│   │   └── schemas/                # Pydantic模式
│   ├── services/                   # 业务服务
│   │   ├── log/                    # 日志服务
│   │   │   ├── collector.py        # 日志收集器
│   │   │   ├── processor.py        # 日志处理器
│   │   │   ├── storage.py          # 日志存储
│   │   │   └── analyzer.py         # 日志分析器
│   │   ├── alert/                  # 告警服务
│   │   ├── monitor/                # 监控服务
│   │   └── report/                 # 报告服务
│   ├── tasks/                      # 异步任务
│   │   ├── log_tasks.py            # 日志相关任务
│   │   ├── alert_tasks.py          # 告警相关任务
│   │   └── maintenance_tasks.py    # 维护任务
│   ├── utils/                      # 工具函数
│   └── main.py                     # 应用入口
├── frontend/                       # 前端应用
│   ├── public/                     # 静态资源
│   ├── src/
│   │   ├── components/             # 可复用组件
│   │   ├── pages/                  # 页面组件
│   │   │   ├── Dashboard/          # 仪表板页面
│   │   │   ├── LogSearch/          # 日志搜索页面
│   │   │   ├── AlertCenter/        # 告警中心页面
│   │   │   ├── Configuration/      # 配置页面
│   │   │   └── SystemStatus/       # 系统状态页面
│   │   ├── services/               # API服务
│   │   ├── stores/                 # 状态管理
│   │   ├── types/                  # TypeScript类型定义
│   │   ├── utils/                  # 工具函数
│   │   └── App.tsx                 # 应用入口
│   └── package.json
├── configs/                        # 配置文件
│   ├── logstash/                   # Logstash配置
│   ├── vector/                     # Vector配置
│   ├── elasticsearch/              # ES配置
│   └── prometheus/                 # Prometheus配置
├── scripts/                        # 脚本文件
│   ├── deploy/                     # 部署脚本
│   ├── backup/                     # 备份脚本
│   └── monitoring/                 # 监控脚本
├── tests/                          # 测试文件
│   ├── unit/                       # 单元测试
│   ├── integration/                # 集成测试
│   └── e2e/                        # 端到端测试
├── docker/                         # Docker相关文件
│   ├── app/                        # 应用Dockerfile
│   ├── logstash/                   # Logstash Dockerfile
│   └── nginx/                      # Nginx配置
├── docs/                           # 文档
│   ├── api/                        # API文档
│   ├── architecture/               # 架构文档
│   ├── deployment/                 # 部署文档
│   └── development/                # 开发文档
├── docker-compose.yml              # Docker Compose配置
├── docker-compose.prod.yml         # 生产环境配置
├── .env.example                    # 环境变量示例
├── requirements.txt                # 生产依赖
├── requirements-dev.txt            # 开发依赖
├── pyproject.toml                  # Python项目配置
├── alembic.ini                     # 数据库迁移配置
├── README.md                       # 项目说明
└── LICENSE                         # 许可证
```

## 功能模块

### 1. 日志收集

支持多种日志源：
- **文件日志**：通过Filebeat或Vector收集
- **容器日志**：Kubernetes环境自动发现
- **应用日志**：通过SDK直接发送
- **系统日志**：Syslog、Journald
- **云服务日志**：AWS CloudWatch、GCP Logging

### 2. 日志处理

处理管道包括：
- **解析**：JSON、正则、Grok模式
- **过滤**：基于规则过滤无关日志
- **丰富**：添加元数据、地理位置、用户信息
- **转换**：格式转换、字段映射
- **脱敏**：敏感信息掩码

### 3. 存储管理

多级存储策略：
- **热存储**：Elasticsearch，实时查询
- **温存储**：压缩索引，成本优化
- **冷存储**：对象存储，长期归档
- **元数据**：PostgreSQL，配置和关系数据

### 4. 搜索和分析

强大的查询能力：
- **全文搜索**：基于Elasticsearch
- **字段过滤**：多条件组合查询
- **时间范围**：灵活的时间选择
- **聚合分析**：统计、分组、趋势
- **关联分析**：跨日志源关联

### 5. 可视化

丰富的可视化组件：
- **实时仪表板**：关键指标监控
- **日志查看器**：语法高亮、JSON格式化
- **图表分析**：折线图、柱状图、饼图
- **地理分布**：IP地理位置可视化
- **拓扑图**：服务依赖关系

### 6. 告警系统

智能告警功能：
- **规则引擎**：灵活的告警条件
- **多通道通知**：邮件、Slack、Webhook、短信
- **去重抑制**：防止告警风暴
- **升级策略**：告警升级和认领
- **历史管理**：告警记录和分析

### 7. 系统管理

企业级管理功能：
- **多租户**：组织、项目、用户隔离
- **权限控制**：基于角色的访问控制
- **审计日志**：所有操作记录
- **配置管理**：动态配置更新
- **系统监控**：健康检查和指标收集

## API文档

### 主要端点

#### 日志相关
- `GET /api/v1/logs` - 查询日志
- `GET /api/v1/logs/{log_id}` - 获取单个日志
- `POST /api/v1/logs/search` - 高级搜索
- `GET /api/v1/logs/statistics` - 统计信息

#### 告警相关
- `GET /api/v1/alerts` - 获取告警列表
- `POST /api/v1/alerts` - 创建告警规则
- `PUT /api/v1/alerts/{rule_id}` - 更新告警规则
- `DELETE /api/v1/alerts/{rule_id}` - 删除告警规则

#### 仪表板相关
- `GET /api/v1/dashboards` - 获取仪表板列表
- `POST /api/v1/dashboards` - 创建仪表板
- `GET /api/v1/dashboards/{dashboard_id}` - 获取仪表板详情
- `PUT /api/v1/dashboards/{dashboard_id}` - 更新仪表板

#### 系统管理
- `GET /api/v1/system/health` - 系统健康检查
- `GET /api/v1/system/metrics` - 系统指标
- `GET /api/v1/system/config` - 系统配置
- `POST /api/v1/system/backup` - 系统备份

### WebSocket接口

实时数据推送：
- `ws://localhost:8000/ws/logs` - 实时日志流
- `ws://localhost:8000/ws/alerts` - 实时告警通知
- `ws://localhost:8000/ws/metrics` - 实时指标数据

## 配置指南

### 日志源配置

#### 文件日志收集
```yaml
# configs/vector/file_logs.yaml
sources:
  app_logs:
    type: file
    include:
      - "/var/log/app/*.log"
    read_from: beginning

transforms:
  parse_json:
    type: remap
    inputs: ["app_logs"]
    source: |
      . = parse_json!(.message)
      .source_type = "file"
      .host = get_hostname!()

sinks:
  to_logstash:
    type: elasticsearch
    inputs: ["parse_json"]
    endpoint: "http://logstash:5044"
    compression: gzip
```

#### 应用SDK集成
```python
from logmonitor_sdk import LogMonitorClient

# 初始化SDK
client = LogMonitorClient(
    endpoint="http://localhost:8000",
    api_key="your_api_key",
    app_name="myapp",
    environment="production"
)

# 发送日志
client.log(
    level="INFO",
    message="用户登录成功",
    user_id="user_123",
    extra={
        "endpoint": "/api/login",
        "duration_ms": 150,
        "ip_address": "192.168.1.1"
    }
)
```

### 告警规则配置

```yaml
# 告警规则示例
alert_rules:
  - name: "high_error_rate"
    description: "错误率超过5%"
    enabled: true
    condition:
      type: "threshold"
      metric: "error_count"
      window: "5m"
      threshold: 5
      operator: "gt"
    actions:
      - type: "email"
        recipients: ["team@example.com"]
        subject: "错误率告警"
      - type: "slack"
        webhook: "https://hooks.slack.com/services/..."
        channel: "#alerts"
    severity: "high"
```

### 仪表板配置

```json
{
  "name": "应用概览",
  "description": "应用关键指标监控",
  "layout": "grid",
  "panels": [
    {
      "title": "请求量趋势",
      "type": "line_chart",
      "query": {
        "metric": "request_count",
        "aggregation": "sum",
        "interval": "1m",
        "time_range": "1h"
      },
      "position": {"x": 0, "y": 0, "w": 12, "h": 6}
    },
    {
      "title": "错误分布",
      "type": "pie_chart",
      "query": {
        "metric": "error_count",
        "group_by": ["error_type"],
        "time_range": "1h"
      },
      "position": {"x": 12, "y": 0, "w": 6, "h": 6}
    }
  ]
}
```

## 部署指南

### 开发环境

使用Docker Compose：
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 测试环境

使用Docker Compose with Overrides：
```bash
# 使用测试配置
docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d
```

### 生产环境

#### Kubernetes部署
```bash
# 使用Helm部署
helm install logmonitor ./charts/logmonitor \
  --namespace logging \
  --set elasticsearch.replicas=3 \
  --set redis.cluster.enabled=true

# 验证部署
kubectl get pods -n logging
kubectl get services -n logging
```

#### 高可用配置
```yaml
# values-prod.yaml
elasticsearch:
  replicas: 3
  resources:
    requests:
      memory: "4Gi"
      cpu: "2"
    limits:
      memory: "8Gi"
      cpu: "4"

redis:
  cluster:
    enabled: true
    nodes: 6

postgresql:
  architecture: "replication"
  readReplicas: 2
```

## 监控和维护

### 系统监控

内置监控指标：
- **应用指标**：请求量、错误率、延迟
- **系统指标**：CPU、内存、磁盘、网络
- **业务指标**：日志量、告警数、用户数
- **服务质量**：SLA、可用性、性能

### 健康检查

```bash
# 手动健康检查
curl http://localhost:8000/api/v1/system/health

# 响应示例
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "services": {
    "database": "healthy",
    "elasticsearch": "healthy",
    "redis": "healthy",
    "logstash": "healthy"
  }
}
```

### 备份和恢复

#### 自动备份
```bash
# 执行备份
python scripts/backup/backup.py --type=full --destination=s3://backup-bucket

# 备份计划（crontab）
0 2 * * * cd /app && python scripts/backup/backup.py --type=daily
```

#### 数据恢复
```bash
# 恢复数据库
python scripts/backup/restore.py --backup=20240101_full.tar.gz

# 验证恢复
python scripts/backup/verify.py --backup=20240101_full.tar.gz
```

## 性能优化

### 优化建议

#### 1. 存储优化
- 使用SSD存储Elasticsearch数据
- 配置合适的分片和副本数
- 定期force merge减少碎片
- 使用索引生命周期管理

#### 2. 查询优化
- 为常用查询字段建立索引
- 使用日期范围限制查询
- 避免全字段搜索
- 缓存常用查询结果

#### 3. 网络优化
- 启用HTTP压缩
- 使用连接池
- 配置合适的超时时间
- 使用CDN缓存静态资源

### 性能测试

```bash
# 使用Locust进行性能测试
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m
```

## 安全指南

### 安全特性

1. **身份验证**：JWT令牌，支持OAuth2
2. **授权**：基于角色的访问控制(RBAC)
3. **数据加密**：传输加密(TLS)，存储加密
4. **审计日志**：所有操作记录
5. **输入验证**：防止注入攻击
6. **速率限制**：防止滥用

### 安全配置

```yaml
# 安全配置示例
security:
  jwt:
    secret_key: "${JWT_SECRET_KEY}"
    algorithm: "HS256"
    access_token_expire_minutes: 30
    refresh_token_expire_days: 7

  cors:
    allow_origins: ["https://example.com"]
    allow_methods: ["GET", "POST", "PUT", "DELETE"]
    allow_headers: ["*"]

  rate_limit:
    enabled: true
    default: "100/minute"
    strategies:
      ip: "50/minute"
      user: "200/minute"
```

## 贡献指南

### 开发流程

1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 运行测试
5. 创建Pull Request

### 代码规范

- 遵循PEP 8（Python）和ESLint（TypeScript）
- 编写单元测试，覆盖率>80%
- 更新相关文档
- 添加适当的注释

### 测试要求

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_log_service.py

# 生成测试覆盖率报告
pytest --cov=app --cov-report=html
```

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

- 文档：查看 [docs](docs/) 目录
- 问题：使用 [GitHub Issues](https://github.com/yourusername/logmonitor/issues)
- 讨论：加入 [Discord 频道](https://discord.gg/...)
- 邮件：support@logmonitor.example.com

## 致谢

感谢所有贡献者和用户的支持。特别感谢以下开源项目：
- FastAPI、Elasticsearch、React等核心依赖
- CNCF云原生生态系统
- 开源社区的支持和贡献

---

**注意**：本项目处于活跃开发阶段，API和功能可能会有变更。生产环境使用时请仔细测试。