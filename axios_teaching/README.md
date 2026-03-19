# Axios 四层教学包（以“看懂项目代码”为目标）

## 你的学习目标

你现在不追求从零写大型项目，而是先做到：

1. 看懂大多数项目里的 `axios` 请求代码。
2. 能定位请求配置、拦截器、错误处理、鉴权逻辑。
3. 能在已有项目里做小修改（加请求、改参数、改超时、加日志）。

## 学习路径（建议 5-7 天）

1. `foundation/`：先看懂语法和常见配置。
2. `integration/`：理解 axios 在项目中的组合方式。
3. `advanced/`：理解团队项目常见的高级写法。
4. `project/`：看一个“小型真实结构”并照着改。

## 目录

```text
axios_teaching/
├─ foundation/
│  ├─ 01_basic_get_post.js
│  ├─ 02_params_headers.js
│  ├─ 03_instance_and_interceptor.js
│  ├─ 04_error_timeout_retry.js
│  └─ foundation_cheatsheet.md
├─ integration/
│  ├─ 01_service_layer_pattern.js
│  ├─ 02_parallel_and_sequential_requests.js
│  └─ integration_guide.md
├─ advanced/
│  ├─ 01_token_refresh_pattern.js
│  ├─ 02_request_cancel_pattern.js
│  └─ advanced_features.md
├─ project/
│  └─ project_api_client_demo/
│     ├─ README.md
│     └─ src/
│        ├─ http/client.js
│        └─ services/userService.js
└─ USAGE_GUIDE.md
```

