# 使用指南（按你的目标定制）

## 你先学这 5 个文件

1. `foundation/01_basic_get_post.js`
2. `foundation/03_instance_and_interceptor.js`
3. `foundation/04_error_timeout_retry.js`
4. `integration/01_service_layer_pattern.js`
5. `project/project_api_client_demo/src/http/client.js`

只要看懂这 5 个，你已经能看懂大多数项目里的 axios 代码。

## 运行方式

在 `axios_teaching` 目录下执行：

```bash
npm init -y
npm install axios
node foundation/01_basic_get_post.js
node foundation/03_instance_and_interceptor.js
node integration/01_service_layer_pattern.js
```

## 你读真实项目时的“定位口诀”

1. 先找 axios 实例（`axios.create`）。
2. 再看拦截器（请求前做什么，响应后做什么）。
3. 再看 service 函数（接口路径、参数、返回结构）。
4. 最后看页面如何处理 loading / error / 数据渲染。

## 一周复盘标准

1. 你能解释 `params` 和 `data` 的区别。
2. 你能说清楚拦截器在项目里的作用。
3. 你能在现有项目里加一个新 API 函数并被页面调用。

