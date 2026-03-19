# Axios 基础速查（面向“读懂项目”）

## 高频结构

```js
axios.get(url, { params, headers, timeout })
axios.post(url, data, { headers, timeout })
const client = axios.create({ baseURL, timeout })
client.interceptors.request.use(fn)
client.interceptors.response.use(successFn, errorFn)
```

## 你必须背下来的

1. `params` 是查询参数，`data` 是请求体。
2. 大多数项目会用 `axios.create()` 做统一实例。
3. token、日志、统一报错通常都在拦截器里。

## 你要熟练掌握的

1. `error.response / error.request / error.message` 的区别。
2. `baseURL + 相对路径` 的拼接方式。
3. `timeout`、`headers`、`params` 在配置对象里的位置。

## 了解即可

1. 请求取消（AbortController）。
2. token 自动刷新（401 后重试）。
3. 更复杂的并发控制（请求队列、限流）。

